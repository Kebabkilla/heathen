# First standalone Windows launch (diagnostic checkpoint)

This is a **development smoke test**, not a release package or completed TPP
feature. The source audit and tests are complete; actual Windows startup,
rendering, and movement still need to be verified by running the steps below.
There are **no engine/game C or Meson changes** in this checkpoint.

## Startup audit and scope

| Resource / behavior | Source evidence | First-launch decision |
| --- | --- | --- |
| Global palette | `IMG_GetPalette`, `src/refresh/images.c`, calls `ERR_FATAL` if `pics/colormap.pcx` cannot load | Use the existing original grayscale generator |
| Console font | `scr_font_changed`, `src/client/screen.c`, and renderer font registration | Generate original 128x128 `conchars.pcx`, with 256 8x8 cells; lowercase uses uppercase glyphs |
| Client player appearance | `CL_LoadClientinfo`, `src/client/precache.c`, expects model, skin, icon and `weaponmodel[0]` for a valid player appearance | Generate original `players/male/tris.md2`, `grunt.pcx`, `grunt_i.pcx`, and `weapon.md2` |
| Player animation frame IDs | `src/game/m_player.h` defines stock frame numbers through 197 | Supply 198 identical rigid frames; no retail animation data is copied |
| Optional models | `R_RegisterModel`, `src/refresh/models.c`, returns a null handle after registration errors | Do not remove stock precaches; expect missing stock model diagnostics, and do not exercise combat/effects |
| Sounds | `CL_RegisterSounds`, `src/client/precache.c`, uses sound registration | Disable audio before client initialization for this diagnostic; sound/combat is not being validated |
| HUD / gun rendering | `scr_draw2d` and `cl_gun` client settings | Disable HUD and view gun in the test config, while leaving the console usable |
| Game library | `SV_InitGameProgs`, `src/server/game.c`, tries the selected game under libdir before base-game fallback | Stage the x64 DLL only under `mygame`; explicitly set libdir to the runtime root |
| Asset search roots | Windows `basedir`, `libdir`, `homedir` cvars and `src/common/files.c` search-path setup | Fresh root with generated base/mod assets, empty homedir, no external installation search path |
| Menus | UI initialization reads `q2pro.menu` | Supply an empty test menu script; Escape opens the console instead of a retail-art menu |

The legacy `male/grunt` filenames are compatibility paths used by unchanged
client defaults; the generated files contain original placeholder data. The
figure uses basic cuboids and is not a final player model. Both PCX palettes
and the WAL share the original grayscale palette. The generated PCX is not a
software-renderer lighting colormap.

The test leaves authoritative movement, damage, co-op state, prediction,
and game precache code unchanged. No custom map entities were added, so
`game.fgd` needs no changes. Third-person remains off and cheats remain off.
The server is configured for co-op with four slots, but binds IPv4 to
**127.0.0.1** with IPv6 disabled: this is not a public or LAN co-op test.

## 1. Save, update, check the engine build

Save the map in TrenchBroom, then use an **x64 Native Tools Command Prompt for
VS**:

```bat
cd /d "C:\game projects\heathen" && git pull --ff-only && ninja -C build
```

No Meson reconfiguration or new dependencies are needed. Keep all existing
source/build folders. If Git reports conflicts, stop; do not reset the saved
map. A local map edit is okay when it does not conflict with upstream changes.

## 2. Recompile the saved map once

```bat
python tools\build_test_map.py --tools "C:\game projects\ericw-tools"
```

Even if the map already compiled previously, run this updated script once.
It now writes `build-maps\tpp_test\build-success.json` **only after all three
compiler stages succeed**. A new compile invalidates the previous receipt.
Staging compares the current source-map and BSP hashes with that receipt,
rejecting stale or changed files. Save the map before compiling; saving it
again afterward may require another compile to refresh the receipt.

## 3. Stage a new isolated runtime

```bat
python tools\stage_runtime.py
```

This validates the engine/DLL as Windows x64 PE32+ files and the BSP as Quake II
IBSP v38, copies explicit inputs, generates original placeholders, and writes
SHA-256 hashes to `manifest.json`. It does **not** compile the engine or copy
assets recursively from an installed game. DLL dependencies are copied only
from the top level of your local `build` directory; full redistribution/installer
requirements remain a future task.

The default output is a fresh ignored folder:

```text
C:\game projects\heathen\build-runtime\
    q2pro.exe
    q2proded.exe                 (if present in build)
    launch-test.cmd
    manifest.json
    baseq2\                     (original early-startup resources only)
    mygame\
        gamex86_64.dll
        heathen-test.cfg
        maps\tpp_test.bsp
        pics\...
        textures\heathen\blockout.wal
        players\male\...
```

No PAKs/PKZs, source maps, or old config files are imported. A new folder is
constructed before publication; failed staging cleans only its temporary output.
Source code, the saved `.map`, and the original build outputs are not changed.
Generated art is created directly in the ignored runtime, not in tracked source.

**Existing runtime directories are never overwritten or deleted.** If one
already exists, stage a new snapshot:

```bat
python tools\stage_runtime.py --name build-runtime-02
```

Use the corresponding new folder when launching. Keep older runtime logs until
a problem is resolved; don't add downloaded PAKs or manually copy assets into
these test folders. Restaging is a snapshot, not an automatic live update.

## 4. Launch the staged test

For the default folder:

```bat
build-runtime\launch-test.cmd
```

The launcher first changes to its own directory. It explicitly selects
`basedir .`, `libdir .`, empty `homedir`, and `game mygame`, disables sound before
initialization, enables a flushed console log, and executes `heathen-test.cfg`.
Early palette/font copies are provided in `baseq2` as well as `mygame` so initial
rendering is not dependent on the timing of mod search-path selection.

The game should attempt to enter `tpp_test` in a window. This is deliberately
**first-person** for the initial spawn/movement test. Controls:

| Key | Action |
| --- | --- |
| W/A/S/D | Move |
| Mouse | Look |
| Space | Jump |
| Ctrl | Crouch |
| Escape or backtick | Toggle console |
| F12 | Screenshot |
| F10 | Quit |

Sound, HUD, crosshair, view weapon, attack bindings, and retail-art menus are
intentionally absent. The console font uses uppercase glyphs for lowercase
characters; actual command parsing still respects the text you type. Missing
stock sound/effect/sky/UI resource diagnostics may remain in the console. They
are not evidence that retail assets should be installed. Do not treat a fatal
error, a dropped map, an unreadable console, or failure to spawn as success.

## 5. Report the first-launch result

Check these **before calling this milestone verified**:

- [ ] The room loads and the console is readable.
- [ ] W/A/S/D and mouse look work.
- [ ] Floor, walls, ceiling and column block player movement as expected.
- [ ] Jump/crouch work without falling out of the room.
- [ ] In the console, `path` shows only this staged base/mod tree, not the old
  ZIP download, a retail install, or another user-data folder.
- [ ] `modellist` shows the original `players/male/tris.md2` and weapon model
  loaded (this first-person test does not visually validate their appearance).
- [ ] No fatal errors, game-DLL load failure, or map drop occurred.

Send an in-game screenshot. If startup fails, send the exact error and the end
of `build-runtime\mygame\logs\console.log`. Early startup diagnostics may instead
be in `build-runtime\baseq2\logs\console.log`. Use your actual numbered runtime
folder if different. If Windows reports a missing runtime DLL before the game
opens, report its filename; do not download arbitrary DLLs from third-party sites.

A successful Windows run is the **next PR/merge checkpoint**. The agent's stdlib
unit tests validate file structure and staging safeguards, not actual OpenGL
rendering, Windows DLL loading, player collision, or gameplay. PE fixtures in
unit tests are synthetic sanity-check data, not runnable executables. No actual
Windows runtime test is claimed until the user performs it.

After this checkpoint: verify original model rendering, refine the existing
client-side chase camera, and test two clients before adding RPG mechanics.
