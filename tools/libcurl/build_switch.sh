#!/usr/bin/env bash
# Pin the installed curl API version, using the existing Mbed TLS backend.
# The portlib's libnx backend unconditionally parses peer certificate metadata
# (devkitPro/pacman-packages#436); private HTTP uses the tested Mbed TLS path.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$ROOT/.cache/curl-switch"
VERSION=7.69.1
HASH=03c7d5e6697f7b7e40ada1b2256e565a555657398e6c1fcfa4cb251ccd819d4f
CONFIG_VERSION="$VERSION-mbedtls-v3-relative-paths"
if [[ -f "$WORK/lib/libcurl.a" && -f "$WORK/version" && "$(cat "$WORK/version")" == "$CONFIG_VERSION" ]]; then exit 0; fi
export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
export DEVKITA64="${DEVKITA64:-$DEVKITPRO/devkitA64}"
export PATH="$DEVKITA64/bin:$PATH"
mkdir -p "$WORK"
TARBALL="$WORK/curl-$VERSION.tar.xz"
if [[ ! -f "$TARBALL" ]]; then
    if [[ -f "$ROOT/.cache/curl-host/source.tar.xz" ]]; then cp "$ROOT/.cache/curl-host/source.tar.xz" "$TARBALL";
    else curl -fsSL "https://curl.se/download/curl-$VERSION.tar.xz" -o "$TARBALL"; fi
fi
printf '%s  %s\n' "$HASH" "$TARBALL" | sha256sum -c -
if [[ ! -d "$WORK/curl-$VERSION" ]]; then tar -xf "$TARBALL" -C "$WORK"; fi
mkdir -p "$WORK/build" "$WORK/lib"
cd "$WORK/build"
export CPPFLAGS="-D__SWITCH__ -D_POSIX_C_SOURCE=200112L -DPF_INET=AF_INET -DPF_INET6=AF_INET6 -DPF_UNSPEC=AF_UNSPEC -I$DEVKITPRO/portlibs/switch/include -I$DEVKITPRO/libnx/include"
export CFLAGS="-Os -g -march=armv8-a+crc+crypto -mtune=cortex-a57 -mtp=soft -fPIC -ffunction-sections -fdata-sections -ffile-prefix-map=$ROOT=. -fmacro-prefix-map=$ROOT=."
export LDFLAGS="-specs=$DEVKITPRO/libnx/switch.specs -L$DEVKITPRO/portlibs/switch/lib -L$DEVKITPRO/libnx/lib"
export LIBS="-lnx"
if [[ ! -f lib/Makefile || ! -f lib/curl_config.h || ! -f "$WORK/config-version" || "$(cat "$WORK/config-version")" != "$CONFIG_VERSION" ]]; then
"$WORK/curl-$VERSION/configure" --host=aarch64-none-elf --disable-shared --enable-static --without-ssl \
    --with-mbedtls --with-zlib --without-ca-bundle --without-ca-path --without-libidn2 --without-libssh2 \
    --disable-threaded-resolver --disable-ntlm-wb --disable-ldap --disable-ldaps --disable-ftp --disable-file --disable-rtsp \
    --disable-dict --disable-telnet --disable-tftp --disable-pop3 --disable-imap --disable-smtp --disable-gopher --disable-smb \
    > "$WORK/configure.log" 2>&1
printf '%s\n' "$CONFIG_VERSION" > "$WORK/config-version"
fi
make -j4 -C lib CPPFLAGS="$CPPFLAGS" > "$WORK/build.log" 2>&1
cp lib/.libs/libcurl.a "$WORK/lib/libcurl.a"
printf '%s\n' "$CONFIG_VERSION" > "$WORK/version"
