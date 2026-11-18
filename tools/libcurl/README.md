# Private HTTP backend

`bash tools/libcurl/build_switch.sh` builds a workspace-local static curl archive
for Switch. `build.sh switch` runs it automatically. It requires devkitA64,
libnx and the installed Switch Mbed TLS 2.28 and zlib libraries.

Source: [official curl 7.69.1](https://curl.se/download/curl-7.69.1.tar.xz),
SHA-256 `03c7d5e6697f7b7e40ada1b2256e565a555657398e6c1fcfa4cb251ccd819d4f`.
The source retains curl's COPYING license. Sources, configure/build logs and the
archive live under `.cache/curl-switch`; installed port libraries are untouched.
The configuration version `7.69.1-mbedtls-v2` invalidates older cached builds.

Only HTTP/HTTPS protocols are enabled. Mbed TLS uses PDP's platform root store
and mandatory peer/name verification. The installed curl port's Horizon SSL
backend unconditionally parses peer certificate metadata; the parser abort
reported in [devkitPro issue 436](https://github.com/devkitPro/pacman-packages/issues/436)
motivates using the existing tested Mbed TLS backend instead. Certificate
verification is never disabled to avoid that parser. Winbind authentication
helpers are disabled because Horizon does not supply execl/waitpid. PF_INET,
PF_INET6 and PF_UNSPEC are mapped to the corresponding AF constants missing
from libnx's POSIX aliases. The synchronous resolver is retained.

For host comparisons build the same source with `--without-ssl --with-mbedtls
--with-zlib --without-ca-bundle --without-ca-path`; expose matching headers and
archives through CPATH/LIBRARY_PATH. See tests/dex_host/README.md for the local
HTTP/HTTPS regression. Tests never contact captured game/cloud endpoints.

Uploads are buffered. Explicit Java connect/output-stream establishment uses
a real connection probe and a separate response transfer, adding a handshake.
Java proxy/cookie/cache hooks, authentication challenge handling, custom HTTPS
trust/verifier adapters and date headers remain unimplemented. Host environment
proxies are disabled so they cannot silently change Android policy. Curl's
multi interface drives response headers and incremental body reads; the native
handles do not enter PDP's guest descriptor table.
