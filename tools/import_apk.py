#!/usr/bin/env python3
"""Validate a user-owned ARM64 APK and install it unchanged as pewdiepie.apk."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "com.outerminds.pewdiepie"


def build_probe():
    cache = ROOT / ".cache/import"
    cache.mkdir(parents=True, exist_ok=True)
    output = cache / "apk_probe"
    sources = ["tools/apk_probe.c", "source/runtime_assets.c", "source/runtime_diagnostics.c"]
    subprocess.run(shlex.split(os.environ.get("HOST_CC", "cc")) +
                   ["-std=gnu11", "-O1", "-ffunction-sections", "-fdata-sections", "-Isource"] +
                   sources + ["-Wl,--gc-sections", "-pthread", "-lz", "-o", str(output)],
                   cwd=ROOT, check=True)
    return output


def inspect_apk(source, probe):
    source = Path(source).resolve(strict=True)
    def validate_names(archive):
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Archive has duplicate ZIP entries")
        for name in names:
            parts = name.split("/")
            if name.startswith("/") or ".." in parts or "\\" in name:
                raise ValueError("Unsafe ZIP entry")
        return names
    libraries = []
    with zipfile.ZipFile(source) as outer:
        names = validate_names(outer)
        if 'AndroidManifest.xml' not in names:
            raise ValueError("Supply the original APK, not an XAPK or unpacked files")
        for entry in names:
            if entry.startswith('lib/arm64-v8a/') and entry.endswith('.so'):
                with outer.open(entry) as native:
                    header = native.read(20)
                if len(header) != 20 or header[:6] != b'\x7fELF\x02\x01' or header[18:20] != b'\xb7\0':
                    raise ValueError("Invalid ARM64 ELF header")
                libraries.append(entry)
    if not libraries:
        raise ValueError("An ARM64 APK is required; ARMv7-only packages cannot run")
    info = json.loads(subprocess.check_output([str(probe), str(source)], cwd=ROOT, text=True))
    if info["package"] != PACKAGE:
        raise ValueError(f"Expected {PACKAGE}, got {info['package']!r}")
    if info["result"] != 0:
        raise ValueError(f"Runtime cannot bootstrap this XAPK: {info}")
    with source.open("rb") as original:
        info["sha256"] = hashlib.file_digest(original, "sha256").hexdigest()
    info["native_libraries"] = libraries
    return info


def import_apk(source, destination, probe, replace=False):
    info = inspect_apk(source, probe)
    destination = Path(destination)
    if destination.is_symlink():
        raise ValueError("Destination must not be a symbolic link")
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / "pewdiepie.apk"
    if target.exists() and not replace:
        raise FileExistsError("pewdiepie.apk already exists; use --replace to update it (saves are preserved)")
    fd, temporary = tempfile.mkstemp(prefix=".import-", dir=destination)
    try:
        with os.fdopen(fd, "wb") as out, Path(source).open("rb") as original:
            shutil.copyfileobj(original, out)
            out.flush()
            os.fsync(out.fileno())
        with open(temporary, "rb") as copied:
            if hashlib.file_digest(copied, "sha256").hexdigest() != info["sha256"]:
                raise ValueError("APK changed during import; original destination preserved")
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--destination", type=Path, default=ROOT,
                        help="pewdiepie_nx directory, optionally directly on your SD card")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--inspect", action="store_true", help="read metadata without importing")
    args = parser.parse_args()
    try:
        probe = build_probe()
        info = inspect_apk(args.apk, probe) if args.inspect else import_apk(
            args.apk, args.destination, probe, args.replace)
        print(json.dumps(info, indent=2))
    except (ValueError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Import failed: {error}\n")


if __name__ == "__main__":
    main()
