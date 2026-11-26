# Q2PRO baseline

## Source provenance

- Repository: https://github.com/q2pro/q2pro
- Upstream branch: `master`
- Imported commit: `601a8df8433b0c50dbbe37c0716c3793fff140a7`
- Commit date (UTC): 2025-12-11 14:31:00
- Commit subject: Fix 'zero extending DWORD to size_t of greater size' MSVC warning
- Selection: latest commit on upstream master before 2026-11-24 23:59:59 UTC,
  matching the latest commit subject visible in the user's download screenshot.
  The original ZIP was unavailable for a byte-for-byte comparison.
- Retrieval: GitHub source archive for the full commit ID above.

Upstream `README.md` is preserved as `README.q2pro.md`. All other upstream
files were imported in place; only `.gitignore` was extended. No engine or
gameplay code was modified in this baseline import. New project documentation
is separate from upstream documentation.

The engine and bundled game code are GPL-2.0-or-later; retain `LICENSE` and
source copyright notices. Commercial distribution must satisfy the applicable
licenses. Quake II retail assets are not included or licensed by this import.

## Build and verification

### Windows x64 (required before accepting the Windows baseline)

Keep the existing `C:\game projects\q2pro-master` download and its working build
as a backup. Use a separate checkout of Heathen; do not copy or reuse that
folder's configured `build/` directory.

From an **x64 Native Tools Command Prompt for VS**, in the Heathen source root:

```bat
meson setup build --wrap-mode=forcefallback
ninja -C build
```

Initial setup downloads and builds dependencies and requires network access.
See `BUILDING.md` for upstream prerequisites. Expected Windows x64 targets
include `build\q2pro.exe`, `build\q2proded.exe`, and `build\gamex86_64.dll`.
This import does not change upstream Meson target definitions or dependencies.

For subsequent source-only changes, run `ninja -C build`. If Meson options or
build definitions change, explicitly reconfigure as appropriate:

```bat
meson setup build --reconfigure
ninja -C build
```

The existing upstream GitHub Actions workflows target upstream branch names
and have not been adapted to Heathen's main branch or n8n deployment.

### Agent sandbox verification

On 2026-11-26, Linux x86_64 / GCC 12.2 successfully compiled and linked
`q2proded` and `gamex86_64.so` (92 Ninja steps, no compile/link errors), using:

```sh
meson setup build --auto-features=disabled --wrap-mode=nofallback -Dsystem-wide=false
ninja -C build
```

This is a **limited server/game compilation check**, not a recommended shipping
configuration. Optional dependencies, including zlib, were disabled. Meson
reported expected configuration warnings about missing protocol compression,
video, and audio support. The client target was not built because the sandbox
lacked video development dependencies. Windows/MSVC compilation, graphical
runtime behavior, two-client co-op, and asset-independent startup remain
unverified. Do not use this reduced configuration as the Windows build recipe.

`version.py` derives the build version from the Heathen checkout's Git history;
it is not an upstream revision identifier after import. Use the full commit ID
in this document to identify the upstream baseline.

## Architecture orientation and next milestone

- `src/client/entities.c`: `CL_CalcViewValues` derives the view from predicted
  movement state, with interpolation fallbacks. `CL_SetupThirdPersionView`
  (upstream spelling) already constructs a chase camera. `CL_LerpedTrace`
  sweeps a small box against world geometry and interpolated solid brush models.
  Local-player model visibility and fading are also handled in this file.
- `src/client/main.c`: registers `cl_thirdperson` (default `0`, `CVAR_CHEAT`),
  `cl_thirdperson_angle` (default `0`), and `cl_thirdperson_range` (default `60`).
- `src/client/predict.c`: existing client movement prediction and collision;
  preserve this path while changing camera presentation.
- `src/client/view.c`: render-scene assembly and submission; the chase-camera
  implementation itself is in `entities.c`, not here.
- `src/game/`: bundled authoritative game module, including `p_client.c`,
  `p_view.c`, `g_spawn.c`, and `g_combat.c`.
- `src/game/g_chase.c`: server-side spectator chase logic, not the local
  player's third-person action camera.
- `src/refresh/`: renderer. This baseline uses OpenGL; the desired software-era
  aesthetic should not be confused with an included software renderer.
- `src/server/`: engine-side server hosting and networking, distinct from the
  authoritative game module.

Next steps, kept separate from the baseline import:

1. Verify the full Windows build of this repository.
2. Audit minimum startup/rendering/game-precaching asset requirements, then
   build an original/licensed-data-only sealed test room. Track its `.map`
   source and a `game.fgd` matching supported test entities; do not track BSPs.
   The current upstream game is not yet a standalone, pak-free runtime.
3. Refine the existing camera rather than adding another implementation:
   normal co-op availability, bounded configuration, eye-anchor collision,
   start-solid fallback, and local-model visibility. Keep changes client-side
   and leave authoritative movement and damage untouched.
4. Test corners, ceilings, moving brush models, respawn, map reload, and two
   clients under latency. Review aiming separately: camera displacement alone
   does not reconcile crosshair rays with server weapon traces.

No custom entities were added or modified in this baseline import. There is
not yet a project `game.fgd`, test map, or standalone asset set. Body/leg turning,
independent aiming, melee, and RPG persistence are later milestones.
