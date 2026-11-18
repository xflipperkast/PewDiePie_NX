# Switch EGL surface backend

`bash tools/mesa/build_switch.sh` builds PDP's generic EGL surface driver.
`build.sh switch` invokes it automatically. The SDK installation stays intact:
PDP links `.cache/mesa-switch/lib/libEGL.a` before the portlib directory.
Changes to that archive trigger relinking.

The source is [devkitPro Mesa](https://github.com/devkitPro/mesa/tree/05fc4b1d449b8fe12cf1a47b46c4a1c1f4e4e3a6),
whose Switch driver matches the installed `switch-mesa 20.1.0-5` package.
The source archive and original driver object are checked against pinned
SHA-256 hashes. Only the Switch EGL driver object is replaced; Mesa's EGL core,
GLES state tracker, nouveau and other archive objects remain the installed
versions. Unsupported SDK upgrades fail the hash/layout checks and need an
explicit rebase. No game identity, guest offset or AIR adapter is involved.

The driver adds the following real capabilities:

- Enumerate multisample configs only when Gallium supports both the color
  format and the selected depth/stencil format at that sample count. Existing
  single-sample configurations keep their order and IDs.
- Allocate multisample color and depth/stencil storage for a window. Resolve
  its color into the single-sample native presentation buffer after pending GL
  vertices reach Gallium and before the frame is submitted. The presentation
  fence belongs to the resolved native buffer.
- Allocate independent pbuffer render targets, including matching multisample
  depth/stencil attachments. Pbuffers use single-buffer visuals, do not own an
  NWindow and do not count as display presents. The frontend uses native
  pbuffers whenever the host config advertises support.
- Forward EGL's requested share context to Gallium, so worker contexts can
  share their resources. Allocation failures release partial allocations and
  references; window cleanup cancels an outstanding dequeued buffer.

The installed Mesa binary predates the current devkitA64/newlib C11 mutex
layout. Its `_EGLDisplay` contains a 16-byte mutex; the new toolchain's mutex
is 12 bytes. The compile-local display header retains the pinned archive's
opaque mutex storage. The replacement driver never operates that mutex.
Compile-time checks verify display, config, context, surface and Gallium
offsets against the installed object. Rebuilding a driver with the current
mutex type would corrupt the private display ABI.

Contracts: [EGL config matching and sample attributes](https://registry.khronos.org/EGL/sdk/docs/man/html/eglChooseConfig.xhtml),
[pbuffer creation](https://registry.khronos.org/EGL/sdk/docs/man/html/eglCreatePbufferSurface.xhtml),
[swap semantics](https://registry.khronos.org/EGL/sdk/docs/man/html/eglSwapBuffers.xhtml).
Gallium's format checks, resources, blit interface and the state tracker's
pre-flush callback are implemented by the pinned Mesa source.

Run `bash tests/mesa/run_host_tests.sh` after building the driver. It compiles
the actual patched source with Mesa's headers and a CPU pipe/window backend,
under UBSan. Tests cover capability rejection, config stability, multisample
attachments, resolve ordering, resolved pixels and fences across successive
frames, single-sample windows, pbuffer isolation, sharing and allocation
failure cleanup. `tests/stage9/run_host_tests.sh` also tests native pbuffer
forwarding and the existing EGL/GLES/presentation paths.

These host tests establish driver control flow and ownership, not nouveau GPU
rendering or Switch gameplay. Preserved-swap support, pixmaps, pbuffer texture
binding and native-window resizing remain unavailable in this backend.
Portrait presentation still uses PDP's existing single-sample offscreen
compositor; multisampling of that guest framebuffer remains a separate gap.
