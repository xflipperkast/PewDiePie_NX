These are host platform inputs, not game assets:

- `android_api.txt`: complete API 30 declarations, compressed at build time;
  the reference driving game's reduced type profile is not reused for Unity.
- `framework.arsc`: default, English and Russian Android API 30 resources with
  original resource IDs and retained values; string indices are compacted.
- `*_dex.dex`: Java boot libraries with the standalone bridge namespace.
- `runtime_profile.json`: selected ABI/declaration inventory.

`tools/embed_data.py` creates aligned build inputs. `tools/compact_resources.py`
compacts a supplied Android framework table without changing retained values.
Android framework source: API 30 SDK r3, resource table SHA-256
`6590d7072cd3938ad0574f3d2ecf337b578e9cca92dca634046dc76663a5c8cb`.
See LICENSES.md for notices and outstanding source/provenance obligations.
