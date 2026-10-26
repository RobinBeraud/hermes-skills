#!/usr/bin/env python3
"""Valide les skills (frontmatter, sections, secrets) et génère INDEX.md. Bibliothèque standard uniquement.
Usage : validate_skills.py [--root DIR] [--write-index]"""
import os, re, sys

ROOT = sys.argv[sys.argv.index('--root') + 1] if '--root' in sys.argv else '.'
REQUIRED = ['name', 'description']
SECTIONS = ['Objectif', 'Prérequis', 'Tester', 'Limites', 'Risques', 'Désinstallation']
SECRET = re.compile(r'(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?i:api[_-]?key|token|secret|password)\s*[=:]\s*[\'"]?[A-Za-z0-9_\-/+]{20,})')
SKIP = {'.git', 'node_modules', '06-templates'}


def frontmatter(text):
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k = re.match(r'^(\s*)([A-Za-z_]+):\s*(.*?)\s*(#.*)?$', line)
        if k and k.group(3):
            fm[k.group(2)] = k.group(3).strip('"\'')
    return fm


def main():
    errors, rows = [], []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            p = os.path.join(dp, f)
            if f.endswith(('.md', '.py', '.sh', '.json', '.yml', '.yaml', '.txt', '.example')) and f != 'validate_skills.py':
                try:
                    for i, l in enumerate(open(p, encoding='utf-8').read().splitlines(), 1):
                        if SECRET.search(l):
                            errors.append(f'{p}:{i}: secret potentiel')
                except UnicodeDecodeError:
                    pass
            if f == '.env':
                errors.append(f'{p}: fichier .env versionné')
            if f == 'SKILL.md':
                t = open(p, encoding='utf-8').read()
                fm = frontmatter(t)
                if not fm:
                    errors.append(f'{p}: frontmatter manquant'); continue
                for k in REQUIRED:
                    if not fm.get(k):
                        errors.append(f'{p}: champ « {k} » manquant')
                if fm.get('name') and fm['name'] != os.path.basename(dp):
                    errors.append(f'{p}: name « {fm["name"]} » != nom du dossier')
                # sections vérifiées seulement pour les skills Academy (metadata.academy)
                if 'academy:' in t:
                    for s in SECTIONS:
                        if not re.search(r'^#+\s.*' + s, t, re.M | re.I):
                            errors.append(f'{p}: section « {s} » manquante')
                rows.append((fm.get('name', ''), fm.get('description', ''), os.path.relpath(dp, ROOT), fm.get('version', ''), fm.get('status', 'non renseigné'), fm.get('tested_on', '')))
    if '--write-index' in sys.argv:
        out = ['# Index des skills', '', '_Généré automatiquement par `tools/validate_skills.py`. Ne pas modifier à la main._', '', '| Skill | Description | Dossier | Version | Statut | Testé sur |', '|---|---|---|---|---|---|']
        out += [f'| {n} | {d[:90]} | `{r}` | {v} | {s} | {t} |' for n, d, r, v, s, t in sorted(rows)]
        open(os.path.join(ROOT, 'INDEX.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f'{len(rows)} skill(s) analysé(s), {len(errors)} problème(s)')
    for e in errors:
        print(' -', e)
    sys.exit(1 if errors else 0)


main()
