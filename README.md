<div align="center">

<img src="icon.jpg" alt="PewDiePie_nx" width="160">

# PewDiePie_nx

**PewDiePie: Legend of Brofist on Nintendo Switch**

An unofficial Nintendo Switch port of the Android version of  
**PewDiePie: Legend of Brofist — 1.4.6**

**By xFlippy**

[![Switch](https://img.shields.io/badge/Nintendo_Switch-Homebrew-E60012?style=for-the-badge&logo=nintendoswitch&logoColor=white)](#)
[![Ko-fi](https://img.shields.io/badge/Support_on_Ko--fi-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/flippyy)

</div>

---

## About

# PewDiePie: Legend of the Brofist — Nintendo Switch

Isolated ARM64 Android compatibility port for **PewDiePie 1.4.6**, maintained by
xFlippy. The source and NRO run independently of APK64 and the Earn to Die port.
The original APK is required and is not bundled in distributable archives.

## Install

Use application/title takeover mode (hold R while opening an installed game to
enter hbmenu). Put only these two files on the SD card:

```
switch/pewdiepie_nx/pewdiepie_nx.nro
switch/pewdiepie_nx/pewdiepie.apk
```

Use your own ARM64 PewDiePie 1.4.6 APK, renamed to `pewdiepie.apk`. Do not extract
or patch its native libraries. The port creates one `data/` directory beside
these files for saves and cached runtime files. Keep `data/` when updating the
NRO. It does not read or migrate APK64 saves or another standalone port's files.
Existing APK64 saves remain in their original location.

## Controls

* Cursor hidden: the game's native controller and touchscreen input.
* **Minus**: show/hide cursor; hidden on startup.
* Cursor shown: left stick or D-pad moves; **A** clicks/drags. These inputs are
  reserved for the cursor while shown; other gamepad buttons remain available.
* **Plus**: exit.

Logging, crash-file output and the sampling profiler are disabled at compile
time. There is no log/config folder, installation launcher or external APK64
dependency. Startup failures show the first failed check on screen; press B to
return. This does not create log files or capture gameplay crashes.

## Build and verify

Requires devkitPro devkitA64/libnx and Switch portlibs (Mesa/nouveau, FreeType,
curl/Mbed TLS, Vorbis/Ogg and zlib), Linux/WSL, Python 3.11+, make, patch and a host
C compiler. Pinned Mesa and curl inputs are checked by their build scripts.

```
export DEVKITPRO=/opt/devkitpro
export DEVKITA64=$DEVKITPRO/devkitA64
export PATH=$DEVKITA64/bin:$DEVKITPRO/tools/bin:$PATH
make -j4
make check
python3 tools/audit.py --output .cache/verification.json
make package
```

To validate/import an APK without modifying it:

```
python3 tools/import_apk.py /path/to/original.apk --inspect
python3 tools/import_apk.py /path/to/original.apk
```

Build uses `-Oz`, LTO and linker section removal. Framework fonts come from the
Switch system service; no font package is shipped. The icon is decoded from the
APK's manifest launcher resource. No game assets are embedded in the NRO.


This is an unofficial port, not endorsed by Outerminds or PewDiePie. Game content,
trademarks and icon remain their owners' property. See [LICENSES.md](LICENSES.md)
for inherited code and third-party notices.
