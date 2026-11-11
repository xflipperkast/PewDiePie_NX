# License notices and distribution status

This document grants no new rights and does not relicense inherited code.
Publication has not been cleared: an overall license grant for the inherited
compatibility implementation and complete provenance/preferred source for its
legacy Java boot library still need to be established. Exact correspondence
between the embedded Java inputs and their original preferred source also
needs review. The standalone namespace does not change these obligations.

Retain source copyright headers and these included third-party notices:

| Component | Notice / terms |
|---|---|
| Android framework resources and declarations | AOSP Apache-2.0; complete losslessly compressed SDK notice in `romfs/system/licenses/ANDROID_FRAMEWORK_SDK_NOTICE.txt.gz` (read with `gzip -dc`) |
| Android/OpenJDK Java boot code | Mixed Android/Harmony/OpenJDK terms, including GPLv2 with Classpath Exception for designated files; `licenses/AOSP_LIBCORE_LICENSE`, `AOSP_LIBCORE_NOTICE`, `OPENJDK_NOTICE` |
| Unicode tables | `romfs/system/licenses/UNICODE.txt` and `licenses/UNICODE_FRAMEWORK.txt` |
| SQLite | Public-domain dedication in `source/sqlite3.inc` |
| minimp3 | Public-domain/CC0 dedication in `source/minimp3.h` |
| Launcher icon | `icon.jpg` is decoded from the supplied PewDiePie APK's manifest launcher resource `res/mipmap-anydpi-v26/app_icon.xml`; original game artwork remains its rightsholders' property and is not covered by the code licenses |
| Mesa | Pinned source and generic local EGL patch in `tools/mesa`; `licenses/MESA_LICENSE.html` |
| curl | `licenses/CURL_COPYING`; pinned source/build in `tools/libcurl` |
| Mbed TLS | `licenses/MBEDTLS_LICENSE`; verify against the installed linked version |
| FreeType, libogg/libvorbis, zlib, libdrm_nouveau | Preserve the applicable notices for the recorded devkitPro portlib versions |
| libnx and toolchain runtimes | Review the recorded versions' notices, source obligations and runtime exceptions before binary distribution |

The embedded platform data has been compacted for the shipped runtime profile;
the selected configurations preserve their resource IDs and values. Java
bridge identifiers have been renamed, with DEX integrity headers regenerated.
These modifications do not remove license or corresponding-source obligations.

The game's XAPK, APK components, native libraries, assets and trademarks belong
to their rightsholders. No redistribution grant was supplied. The complete game
package, native libraries and gameplay data are excluded from both source and
NRO archives. The extracted launcher artwork is included as `icon.jpg` and in
the NRO's menu metadata; its publication rights also need review before public
distribution. Users must provide a game copy they are entitled to use;
importing leaves that archive unchanged. There are no payment, entitlement,
signer or game-native patches.

Full provenance records are kept separately from this source candidate. Do not
publish until the outstanding grants and corresponding-source obligations are
resolved and the final archive's notices are complete.
