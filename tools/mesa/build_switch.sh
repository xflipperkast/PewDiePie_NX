#!/usr/bin/env bash
# Keep the installed Mesa/Gallium stack; replace only its pinned Switch EGL driver.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$ROOT/.cache/mesa-switch"
REV=05fc4b1d449b8fe12cf1a47b46c4a1c1f4e4e3a6
SOURCE_HASH=935a9aa82e4f0ac8a6352700849b48398f70954a97e908673d79c46fc9377f84
DRIVER_HASH=f06072f9174ebc530088d3d9a0f5a962890473509974ed382269aaf7284e5e84
export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
export PATH="$DEVKITPRO/devkitA64/bin:$PATH"
BASE="$DEVKITPRO/portlibs/switch/lib/libEGL.a"
PATCH="$ROOT/tools/mesa/switch-egl-surfaces.patch"
mkdir -p "$WORK/lib" "$WORK/original"
# Private Mesa structure layouts must match the archive we link against.
aarch64-none-elf-ar p "$BASE" drivers_switch_egl_switch.c.o > "$WORK/original/driver.o"
printf '%s  %s\n' "$DRIVER_HASH" "$WORK/original/driver.o" | sha256sum -c -
KEY="$(sha256sum "$BASE" "$PATCH" "${BASH_SOURCE[0]}" | cut -d' ' -f1 | sha256sum | cut -d' ' -f1)"
if [[ -f "$WORK/lib/libEGL.a" && -f "$WORK/version" && "$(cat "$WORK/version")" == "$KEY" ]]; then exit 0; fi
TARBALL="$WORK/source.tar.gz"
if [[ ! -f "$TARBALL" ]]; then
    if [[ -f "$ROOT/.cache/mesa-switch-source.tar.gz" ]]; then
        cp "$ROOT/.cache/mesa-switch-source.tar.gz" "$TARBALL"
    else
        curl -fsSL "https://codeload.github.com/devkitPro/mesa/tar.gz/$REV" -o "$TARBALL"
    fi
fi
printf '%s  %s\n' "$SOURCE_HASH" "$TARBALL" | sha256sum -c -
SRC="$WORK/mesa-$REV"
# Restore the pristine driver each time the patch changes; keep pinned headers.
if [[ ! -f "$WORK/source-ready" ]]; then
    tar -xf "$TARBALL" -C "$WORK"
    touch "$WORK/source-ready"
else
    tar -xf "$TARBALL" -C "$WORK" "mesa-$REV/src/egl/drivers/switch/egl_switch.c" "mesa-$REV/src/egl/main/egldisplay.h"
fi
patch -d "$SRC" -p1 < "$PATCH"
aarch64-none-elf-gcc -c "$SRC/src/egl/drivers/switch/egl_switch.c" \
    -o "$WORK/drivers_switch_egl_switch.c.o" \
    -std=c99 -Os -g -fPIC -ffunction-sections -fdata-sections \
    -ffile-prefix-map="$ROOT"=. -fmacro-prefix-map="$ROOT"=. \
    -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft \
    -D__SWITCH__ -D_ISOC11_SOURCE -DHAVE_TIMESPEC_GET -DNDEBUG -DHAVE_SWITCH_PLATFORM \
    -DPDP_MESA_PINNED_DISPLAY_ABI \
    -I"$SRC/include" -I"$SRC/src" -I"$SRC/src/egl" -I"$SRC/src/egl/main" \
    -I"$SRC/src/gallium/include" -I"$SRC/src/gallium/auxiliary" \
    -I"$SRC/src/gallium/winsys" -I"$SRC/src/mesa" \
    -I"$DEVKITPRO/libnx/include" -I"$DEVKITPRO/portlibs/switch/include"
cp "$BASE" "$WORK/lib/libEGL.a"
aarch64-none-elf-ar r "$WORK/lib/libEGL.a" "$WORK/drivers_switch_egl_switch.c.o"
printf '%s\n' "$KEY" > "$WORK/version"
