#!/usr/bin/env python3
"""Linux server health report: disk, inodes, memory, swap, load, uptime,
failed systemd units, pending package updates, reboot flag.
Standard library only. Read-only. Exit code: 0 ok, 1 warnings, 2 critical."""
import argparse, json, os, shutil, subprocess, sys

PSEUDO_FS = {"proc", "sysfs", "devpts", "tmpfs", "devtmpfs", "cgroup", "cgroup2", "overlay",
             "squashfs", "securityfs", "debugfs", "tracefs", "configfs", "fusectl", "mqueue",
             "hugetlbfs", "pstore", "bpf", "autofs", "binfmt_misc", "nsfs", "ramfs", "efivarfs",
             "fuse.lxcfs", "fuse.gvfsd-fuse"}
ORDER = {"ok": 0, "warn": 1, "crit": 2, "info": 0}


def level(value, warn, crit):
    return "crit" if value >= crit else "warn" if value >= warn else "ok"


def parse_meminfo(text):
    d = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            parts = v.split()
            if parts and parts[0].isdigit():
                d[k.strip()] = int(parts[0]) * 1024
    return d


def check_memory(meminfo, warn, crit):
    out = []
    total = meminfo.get("MemTotal", 0)
    avail = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
    if total:
        used = 100.0 * (total - avail) / total
        out.append({"check": "memory", "status": level(used, warn, crit),
                    "detail": f"{used:.0f}% used ({(total-avail)/2**20:.0f} MiB of {total/2**20:.0f} MiB, available counts cache)"})
    st = meminfo.get("SwapTotal", 0)
    if st:
        su = 100.0 * (st - meminfo.get("SwapFree", 0)) / st
        out.append({"check": "swap", "status": level(su, 50, 80), "detail": f"{su:.0f}% used of {st/2**20:.0f} MiB"})
    return out


def parse_mounts(text):
    seen, res = set(), []
    for line in text.splitlines():
        p = line.split()
        if len(p) < 3:
            continue
        dev, mp, fs = p[0], p[1].replace("\\040", " "), p[2]
        if fs in PSEUDO_FS or not dev.startswith("/") or dev in seen:
            continue
        seen.add(dev)
        res.append(mp)
    return res


def check_disks(mounts, warn, crit):
    out = []
    for mp in mounts:
        try:
            u = shutil.disk_usage(mp)
            s = os.statvfs(mp)
        except OSError as e:
            out.append({"check": f"disk {mp}", "status": "warn", "detail": f"unreadable: {e}"})
            continue
        if u.total == 0:
            continue
        pct = 100.0 * u.used / u.total
        out.append({"check": f"disk {mp}", "status": level(pct, warn, crit),
                    "detail": f"{pct:.0f}% used, {u.free/2**30:.1f} GiB free"})
        if s.f_files:
            ip = 100.0 * (s.f_files - s.f_ffree) / s.f_files
            out.append({"check": f"inodes {mp}", "status": level(ip, warn, crit), "detail": f"{ip:.0f}% used"})
    return out


def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return None, ""


def parse_failed_units(text):
    units = []
    for line in text.splitlines():
        p = line.replace("●", " ").split()
        if p and (p[0].endswith(".service") or p[0].endswith(".mount") or p[0].endswith(".timer")):
            units.append(p[0])
    return units


def parse_apt_upgradable(text):
    pk = [l for l in text.splitlines() if "/" in l and "upgradable" in l]
    sec = [l for l in pk if "security" in l.split("/", 1)[1].split()[0]]
    return len(pk), len(sec)


def check_system(skip_updates):
    out = []
    if shutil.which("systemctl"):
        rc, txt = run(["systemctl", "--failed", "--no-legend", "--plain"])
        if rc is None:
            out.append({"check": "systemd", "status": "info", "detail": "systemctl not usable here"})
        else:
            units = parse_failed_units(txt)
            out.append({"check": "failed units", "status": "crit" if units else "ok",
                        "detail": ", ".join(units) if units else "none"})
    else:
        out.append({"check": "systemd", "status": "info", "detail": "systemctl not found, skipped"})
    if os.path.exists("/var/run/reboot-required"):
        out.append({"check": "reboot", "status": "warn", "detail": "reboot required"})
    if not skip_updates and shutil.which("apt"):
        rc, txt = run(["apt", "list", "--upgradable"])
        if rc is not None:
            n, s = parse_apt_upgradable(txt)
            out.append({"check": "updates", "status": "warn" if s else "ok" if n == 0 else "info",
                        "detail": f"{n} upgradable ({s} flagged security); uses local apt cache, may be stale"})
    return out


def collect(a):
    res = []
    try:
        meminfo = parse_meminfo(open("/proc/meminfo").read())
        res += check_memory(meminfo, a.mem_warn, a.mem_crit)
    except OSError:
        res.append({"check": "memory", "status": "info", "detail": "/proc/meminfo unavailable"})
    try:
        mounts = parse_mounts(open("/proc/mounts").read())
    except OSError:
        mounts = ["/"]
    res += check_disks(mounts, a.disk_warn, a.disk_crit)
    try:
        l1, l5, l15 = os.getloadavg()
        cpus = os.cpu_count() or 1
        res.append({"check": "load", "status": level(l5 / cpus, 1.0, 2.0),
                    "detail": f"{l1:.2f} {l5:.2f} {l15:.2f} on {cpus} CPU(s)"})
    except OSError:
        pass
    try:
        up = float(open("/proc/uptime").read().split()[0])
        res.append({"check": "uptime", "status": "info", "detail": f"{up/86400:.1f} days"})
    except OSError:
        pass
    res += check_system(a.skip_updates)
    return res


def render(res, as_json):
    worst = max((ORDER[r["status"]] for r in res), default=0)
    if as_json:
        return json.dumps({"worst": ["ok", "warn", "crit"][worst], "checks": res}, indent=2), worst
    tag = {"ok": "OK  ", "warn": "WARN", "crit": "CRIT", "info": "INFO"}
    lines = [f"[{tag[r['status']]}] {r['check']}: {r['detail']}" for r in
             sorted(res, key=lambda r: -ORDER[r["status"]])]
    lines.append(f"Overall: {['OK', 'WARNINGS', 'CRITICAL'][worst]}")
    return "\n".join(lines), worst


def selftest():
    m = parse_meminfo("MemTotal: 1000 kB\nMemAvailable: 100 kB\nSwapTotal: 100 kB\nSwapFree: 10 kB\n")
    r = check_memory(m, 80, 90)
    assert r[0]["status"] == "crit" and r[1]["status"] == "crit", r
    assert level(50, 80, 90) == "ok" and level(85, 80, 90) == "warn"
    mt = "/dev/sda1 / ext4 rw 0 0\ntmpfs /run tmpfs rw 0 0\n/dev/sda1 /bind ext4 rw 0 0\n/dev/sdb1 /data xfs rw 0 0\n"
    assert parse_mounts(mt) == ["/", "/data"], parse_mounts(mt)
    assert parse_failed_units("● foo.service loaded failed failed Foo\n") == ["foo.service"]
    n, s = parse_apt_upgradable("Listing...\nbar/jammy-security 1.2 amd64 [upgradable from: 1.1]\nbaz/jammy-updates 2 amd64 [upgradable from: 1]\n")
    assert (n, s) == (2, 1), (n, s)
    txt, worst = render([{"check": "a", "status": "warn", "detail": "x"}], False)
    assert worst == 1 and "WARNINGS" in txt
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-updates", action="store_true", help="do not call apt")
    ap.add_argument("--disk-warn", type=float, default=80)
    ap.add_argument("--disk-crit", type=float, default=90)
    ap.add_argument("--mem-warn", type=float, default=85)
    ap.add_argument("--mem-crit", type=float, default=95)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    txt, worst = render(collect(a), a.json)
    print(txt)
    sys.exit(worst)


if __name__ == "__main__":
    main()
