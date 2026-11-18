#!/usr/bin/env python3
"""Prepare source and NRO archives without bundling the game package."""
import hashlib
import json
import shutil
import zipfile
from audit import ROOT, audit, source_files
def archive(path, entries):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, data in entries:
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 15, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            output.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
def main():
    report = audit()
    dist = ROOT / '.cache/dist'; dist.mkdir(exist_ok=True)
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files()}
    (dist / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (dist / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    archive(dist / 'pewdiepie_nx-source.zip',
            [('pewdiepie_nx/' + p.relative_to(ROOT).as_posix(), p.read_bytes()) for p in source_files()])
    archive(dist / 'pewdiepie_nx-sd.zip',
            [('switch/pewdiepie_nx/pewdiepie_nx.nro', (ROOT / 'pewdiepie_nx.nro').read_bytes())])
    install = dist / 'sdmc/switch/pewdiepie_nx'; install.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'pewdiepie_nx.nro', install / 'pewdiepie_nx.nro')
    # Local user installation only. Both distributable ZIPs exclude this file.
    if (ROOT / 'pewdiepie.apk').is_file():
        shutil.copyfile(ROOT / 'pewdiepie.apk', install / 'pewdiepie.apk')
    print('Source and NRO ZIPs created; local SD folder contains the two installation files.')
if __name__ == '__main__': main()
