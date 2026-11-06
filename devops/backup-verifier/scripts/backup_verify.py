#!/usr/bin/env python3
"""Verify that backups exist, are recent, are not suspiciously small, and can be read.

Standard library only. Exit codes: 0 = all OK, 1 = warnings, 2 = failures.
"""
import argparse
import glob
import gzip
import bz2
import lzma
import hashlib
import json
import os
import sys
import tarfile
import tempfile
import time
import zipfile
import shutil

OK, WARN, FAIL = "OK", "WARN", "FAIL"


def find_candidates(pattern):
    """Return files matching a file path, a directory, or a glob, newest first."""
    if os.path.isdir(pattern):
        paths = [os.path.join(pattern, n) for n in os.listdir(pattern)]
    else:
        paths = glob.glob(pattern)
    files = [p for p in paths if os.path.isfile(p) and not p.endswith(".sha256")]
    return sorted(files, key=os.path.getmtime, reverse=True)


def read_all(fobj, chunk=1 << 20):
    total = 0
    while True:
        data = fobj.read(chunk)
        if not data:
            return total
        total += len(data)


def check_integrity(path):
    """Fully read the archive. Returns (status, message)."""
    low = path.lower()
    try:
        if low.endswith((".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".tar")):
            with tarfile.open(path, "r:*") as tf:
                count = 0
                for member in tf:
                    count += 1
                    if member.isfile():
                        f = tf.extractfile(member)
                        if f is not None:
                            read_all(f)
            if count == 0:
                return FAIL, "tar archive is empty"
            return OK, "tar readable, %d entries" % count
        if low.endswith(".zip"):
            with zipfile.ZipFile(path) as zf:
                bad = zf.testzip()
                if bad:
                    return FAIL, "corrupt member: %s" % bad
                n = len(zf.namelist())
            if n == 0:
                return FAIL, "zip archive is empty"
            return OK, "zip readable, %d entries" % n
        for ext, opener in ((".gz", gzip.open), (".bz2", bz2.open), (".xz", lzma.open)):
            if low.endswith(ext):
                with opener(path, "rb") as f:
                    size = read_all(f)
                if size == 0:
                    return FAIL, "decompresses to 0 bytes"
                return OK, "stream decompresses, %d bytes" % size
    except Exception as exc:  # corrupt or truncated archives raise many types
        return FAIL, "cannot read archive: %s: %s" % (type(exc).__name__, exc)
    return WARN, "unknown format, integrity not checked (only size and age)"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_checksum(path):
    side = path + ".sha256"
    if not os.path.exists(side):
        return None
    with open(side) as f:
        parts = f.read().split()
    expected = parts[0].lower() if parts else ""
    actual = sha256_of(path)
    if expected == actual:
        return OK, "sha256 matches sidecar file"
    return FAIL, "sha256 differs from sidecar file"


def verify(pattern, max_age_hours, min_size, shrink_ratio):
    results = []

    def add(name, status, msg):
        results.append({"check": name, "status": status, "message": msg})

    files = find_candidates(pattern)
    if not files:
        add("exists", FAIL, "no backup file found for %r" % pattern)
        return None, results
    newest = files[0]
    add("exists", OK, "%d file(s) found, newest: %s" % (len(files), os.path.basename(newest)))

    age_h = (time.time() - os.path.getmtime(newest)) / 3600.0
    if age_h > max_age_hours:
        add("freshness", FAIL, "newest backup is %.1f h old (limit %.1f h)" % (age_h, max_age_hours))
    else:
        add("freshness", OK, "newest backup is %.1f h old (limit %.1f h)" % (age_h, max_age_hours))

    size = os.path.getsize(newest)
    if size < min_size:
        add("size", FAIL, "size %d bytes is below minimum %d" % (size, min_size))
    elif len(files) > 1:
        prev = os.path.getsize(files[1])
        if prev > 0 and size < prev * shrink_ratio:
            add("size", WARN, "size %d is under %.0f%% of previous backup (%d)" % (size, shrink_ratio * 100, prev))
        else:
            add("size", OK, "size %d bytes, previous %d" % (size, prev))
    else:
        add("size", OK, "size %d bytes (no previous backup to compare)" % size)

    status, msg = check_integrity(newest)
    add("integrity", status, msg)
    cs = check_checksum(newest)
    if cs:
        add("checksum", cs[0], cs[1])
    return newest, results


def render(newest, results):
    lines = []
    if newest:
        lines.append("Backup: %s" % newest)
    for r in results:
        lines.append("[%-4s] %-9s %s" % (r["status"], r["check"], r["message"]))
    worst = max((r["status"] for r in results), key=[OK, WARN, FAIL].index)
    lines.append("Result: %s" % worst)
    return "\n".join(lines), worst


def selftest():
    tmp = tempfile.mkdtemp(prefix="backup_verify_")
    try:
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        for i in range(3):
            with open(os.path.join(src, "f%d.txt" % i), "w") as f:
                f.write(("data %d\n" % i) * 2000)
        good = os.path.join(tmp, "db-2026-01-02.tar.gz")
        with tarfile.open(good, "w:gz") as tf:
            tf.add(src, arcname="src")
        with open(good + ".sha256", "w") as f:
            f.write(sha256_of(good) + "  " + os.path.basename(good) + "\n")
        _, res = verify(good, 24, 100, 0.5)
        assert all(r["status"] == OK for r in res), res
        # truncated archive
        bad = os.path.join(tmp, "db-bad.tar.gz")
        with open(good, "rb") as f:
            blob = f.read()
        with open(bad, "wb") as f:
            f.write(blob[: len(blob) // 2])
        _, res = verify(bad, 24, 100, 0.5)
        assert any(r["check"] == "integrity" and r["status"] == FAIL for r in res), res
        # stale archive
        old = time.time() - 72 * 3600
        os.utime(good, (old, old))
        _, res = verify(good, 24, 100, 0.5)
        assert any(r["check"] == "freshness" and r["status"] == FAIL for r in res), res
        # missing
        _, res = verify(os.path.join(tmp, "nothing-*.zip"), 24, 100, 0.5)
        assert res[0]["status"] == FAIL
        # zip ok + shrink warning
        z1 = os.path.join(tmp, "b-1.zip")
        z2 = os.path.join(tmp, "b-2.zip")
        with zipfile.ZipFile(z1, "w") as zf:
            zf.writestr("a.bin", os.urandom(50000))
        with zipfile.ZipFile(z2, "w") as zf:
            zf.writestr("a.txt", "x")
        os.utime(z1, (time.time() - 100, time.time() - 100))
        _, res = verify(os.path.join(tmp, "b-*.zip"), 24, 10, 0.5)
        assert any(r["check"] == "size" and r["status"] == WARN for r in res), res
        print("selftest passed (6 scenarios)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description="Verify a backup exists, is fresh, sane in size, and readable.")
    p.add_argument("target", nargs="?", help="file, directory or glob (e.g. '/backups/db-*.tar.gz')")
    p.add_argument("--max-age-hours", type=float, default=26.0)
    p.add_argument("--min-size", type=int, default=1024, help="minimum size in bytes")
    p.add_argument("--shrink-ratio", type=float, default=0.5, help="warn if newest < ratio * previous")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if not a.target:
        p.error("target is required unless --selftest")
    newest, results = verify(a.target, a.max_age_hours, a.min_size, a.shrink_ratio)
    text, worst = render(newest, results)
    if a.json:
        print(json.dumps({"backup": newest, "result": worst, "checks": results}, indent=2))
    else:
        print(text)
    return {OK: 0, WARN: 1, FAIL: 2}[worst]


if __name__ == "__main__":
    sys.exit(main())
