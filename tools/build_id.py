#!/usr/bin/env python3
"""Content-derived ELF build ID; exclude debug paths and checkout locations."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sdk = Path(os.environ["DEVKITPRO"])
inputs = [("project/" + p.relative_to(ROOT).as_posix(), p)
          for folder in ("source", "romfs", "assets")
          for p in (ROOT / folder).rglob("*") if p.is_file()]
inputs += [("project/" + name, ROOT / name) for name in
           ("Makefile", "tools/build_id.py", "tools/mesa/build_switch.sh",
            "tools/mesa/switch-egl-surfaces.patch", "tools/libcurl/build_switch.sh")]
for dependency, archive in (("mesa-switch", "libEGL.a"), ("curl-switch", "libcurl.a")):
    inputs.append((dependency + "/" + archive, ROOT / ".cache" / dependency / "lib" / archive))
for name in ("GLESv2", "glapi", "drm_nouveau", "vorbisfile", "vorbis", "ogg", "freetype",
             "png16", "bz2", "mbedtls", "mbedx509", "mbedcrypto", "z"):
    path = sdk / "portlibs/switch/lib" / ("lib" + name + ".a")
    if path.is_file(): inputs.append(("portlib/" + path.name, path))
inputs += [("libnx/" + name, sdk / "libnx" / name) for name in ("lib/libnx.a", "switch.specs")]
compiler = str(sdk / "devkitA64/bin/aarch64-none-elf-gcc")
for name in ("libc.a", "libm.a", "libgcc.a", "libstdc++.a"):
    path = Path(subprocess.check_output([compiler, "-print-file-name=" + name], text=True).strip())
    inputs.append(("toolchain/" + name, path))
digest = hashlib.sha1()
digest.update(subprocess.check_output([compiler, "--version"]).splitlines()[0])
for label, path in sorted(inputs):
    digest.update(label.encode() + b"\0")
    if label in {"mesa-switch/libEGL.a", "curl-switch/libcurl.a"}:
        # Cached and fresh archives can differ only in debug info/member modes.
        with tempfile.TemporaryDirectory(prefix="etd2-build-id-") as temporary:
            normalized = Path(temporary) / path.name
            subprocess.run([str(sdk / "devkitA64/bin/aarch64-none-elf-objcopy"),
                            "--strip-debug", "--enable-deterministic-archives",
                            str(path), str(normalized)], check=True)
            with normalized.open("rb") as data:
                digest.update(hashlib.file_digest(data, "sha256").digest())
    else:
        with path.open("rb") as data:
            digest.update(hashlib.file_digest(data, "sha256").digest())
print(digest.hexdigest())
