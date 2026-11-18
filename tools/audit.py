#!/usr/bin/env python3
"""Check source isolation, package boundaries and the size of the linked port."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIRS = ('source', 'assets', 'romfs', 'tools', 'tests', 'licenses')
PUBLIC_FILES = ('Makefile', 'README.md', 'VERIFICATION.md', 'LICENSES.md', 'icon.jpg', '.gitignore', '.gitattributes')
def source_files():
    paths = [ROOT / name for name in PUBLIC_FILES]
    for name in PUBLIC_DIRS:
        paths.extend(p for p in (ROOT / name).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc')
    return sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix())
def audit(build=True):
    files = source_files()
    for path in files:
        assert path.is_file() and not path.is_symlink(), path
        relative = path.relative_to(ROOT)
        assert path.suffix.lower() not in {'.apk', '.xapk', '.obb', '.so', '.o', '.nro', '.elf'}, relative
        assert not set(relative.parts) & {'.git', '.cache', 'dist', 'build'}, relative
    removed = {'launcher.c', 'installer.c', 'air_adapter.c', 'il2cpp_diag.c', 'future_diag.c',
               'media_ndk.c', 'stage_labs.inc', 'entrypoint.inc', 'audio_test.c', 'input_test.c'}
    assert not [p for p in (ROOT / 'source').rglob('*') if p.name in removed]
    assert not (ROOT / 'romfs/system/fonts').exists()
    profile = json.loads((ROOT / 'assets/runtime_profile.json').read_text())
    bionic=(ROOT/'source/runtime_bionic.c').read_text()
    graphics=(ROOT/'source/runtime_graphics.c').read_text()
    fixed=set(re.findall(r'\{"([^"\n]+)",\s*PDP_(?:FUNC|DATA)_ADDR',bionic))
    egl=set(re.findall(r'\{"([^"\n]+)",\s*FADDR\(',graphics))
    assert not (set(profile['native_imports'])-fixed-egl-{'_ZTH15gDeferredAction'}), 'Native profile has missing bindings'
    result = {'source_files': len(files), 'platform_types': profile['platform_types_after'],
              'fixed_native_imports': len(profile['native_imports']), 'proprietary_archive_files': 0,
              'hardware_tested': False, 'publication_cleared': False}
    policy=(ROOT/'source/runtime_storage.c').read_text()
    assert '"/switch/pewdiepie_nx"' in policy
    for source in (ROOT/'source').glob('*'):
        if source.suffix not in {'.c','.h','.s'}: continue
        text=source.read_text()
        assert 'sdmc:/switch/apk64' not in text and 'sdmc:/switch/earntodie' not in text, source
        assert not re.search(r'#\s*include\s*["<](?:\.\./){2}',text), source
    if build:
        units = list((ROOT / '.cache/build').glob('*.d'))
        assert units, 'Build first'
        packaged = {p.resolve() for p in files}
        checked = 0
        dependencies = set()
        for dep in units:
            rule = dep.read_text().replace('\\\n', ' ').split('\n\n', 1)[0]
            for raw in re.findall(r'/[^\s:]+', rule):
                path = Path(raw).resolve()
                dependencies.add(path)
                assert path.is_relative_to(ROOT) or path.is_relative_to(Path('/opt/devkitpro')), (dep.name, raw)
                if path.is_relative_to(ROOT) and path.relative_to(ROOT).parts[0] in PUBLIC_DIRS:
                    assert path in packaged, ('Missing source-archive dependency', raw)
                checked += 1
        runtime_inputs = {p.resolve() for p in files
                          if p.relative_to(ROOT).parts[0] in {'source', 'include', 'third_party'}
                          and p.suffix in {'.c', '.h', '.s'}}
        project_runtime = {p for p in runtime_inputs if p.relative_to(ROOT).parts[0] != 'third_party'}
        assert len(project_runtime) == 23, 'Review runtime source inventory'
        assert len(units) == 18, 'Unexpected or stale compilation units; make clean'
        assert runtime_inputs <= dependencies, ('Unreferenced runtime files', sorted(str(p) for p in runtime_inputs - dependencies))
        linkmap = (ROOT / '.cache/build/pewdiepie_nx.map').read_text()
        for name in removed:
            assert not re.search(r'^LOAD ' + re.escape(Path(name).stem) + r'\.o$', linkmap, re.M), name
        data = (ROOT / 'pewdiepie_nx.nro').read_bytes()
        assert data[0x10:0x14] == b'NRO0'
        end = struct.unpack_from('<I', data, 0x18)[0]
        assert data[end:end + 4] == b'ASET'
        icon_offset, icon_size, nacp_offset, nacp_size = struct.unpack_from('<QQQQ', data, end + 8)
        assert data[end + icon_offset:end + icon_offset + icon_size] == (ROOT / 'icon.jpg').read_bytes()
        nacp = data[end + nacp_offset:end + nacp_offset + nacp_size]
        assert nacp[:512].split(b'\0', 1)[0] == b'PewDiePie: Legend of the Brofist'
        assert nacp[512:768].split(b'\0', 1)[0] == b'xFlippy'
        assert len(data) < 16 * 1024 * 1024, 'Size budget exceeded; review linked components'
        symbols=subprocess.check_output(['/opt/devkitpro/devkitA64/bin/aarch64-none-elf-nm',
                str(ROOT/'.cache/build/pewdiepie_nx.elf')],text=True)
        assert 'dex_prof_thread_main' not in symbols, 'Unexpected sampling profiler worker'
        result.update(compiled_units=len(units), runtime_files_read=len(runtime_inputs), project_runtime_files=len(project_runtime), dependency_paths_checked=checked,
                      external_project_dependencies=0, logging_enabled='log.flag', nro_bytes=len(data),
                      nro_sha256=hashlib.sha256(data).hexdigest())
    return result
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-only', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = json.dumps(audit(not args.source_only), indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(report)
    print(report, end='')
