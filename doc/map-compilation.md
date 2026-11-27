# Original blockout assets and first map compilation

This checkpoint generates an original grayscale palette and grid texture, then
runs ericw-tools on a copy of the test room. It does **not** yet make the game
playable: fonts, player models, other startup assets, and runtime staging are
still separate tasks. There are no engine C or Meson changes.

## Prerequisites

- The Heathen checkout, e.g. `C:\game projects\heathen`.
- Python 3.8 or newer (`python --version`). Python is already part of the Meson
  build toolchain, but its command may differ on your machine. If `python` is
  not recognized, stop and check the installed Python command before continuing.
- The complete **ericw-tools 2.0.0-alpha11 win64** archive extracted together.
  For this setup its location is `C:\game projects\ericw-tools`, with `qbsp.exe`,
  `vis.exe`, `light.exe`, DLLs, and `plugins` kept together.

Pinned release: https://github.com/ericwa/ericw-tools/releases/tag/2.0.0-alpha11

## 1. Update without discarding the saved editor settings

Close the map in TrenchBroom after saving it. From a command prompt:

```bat
cd /d "C:\game projects\heathen" && git pull --ff-only
```

This update does not change `tpp_test.map`, so your local saved FGD/mod settings
should remain intact. If Git reports a conflict or refuses to update, stop and
send the message. Do not reset or overwrite the saved map.

## 2. Generate original assets

From the repository root:

```bat
python tools\generate_blockout.py
```

This writes exactly two reproducible, ignored files:

```text
mygame\pics\colormap.pcx
mygame\textures\heathen\blockout.wal
```

The PCX has a valid 8-bit grayscale palette and a small swatch image. It is a
palette carrier for these editor/compiler tests, **not** a software renderer's
full lighting colormap. The 64x64 WAL includes all four mip levels. The texture
uses no transparent pixels. Both assets are authored procedurally for this
project, without retail data, and use the project's GPL-2.0-or-later license.
The source script is tracked; generated binary assets are not. Regenerating
will replace these two files if they differ: do not hand-edit their output.

Reopen the map in TrenchBroom, check **Map > Mods > mygame** is enabled, and use
**File > Reload Assets**. In **Face**, the material browser should now find the
`heathen` collection and `heathen/blockout` texture. The room already references
that texture; there is no need to repaint every face. The intended result is
a dark gray grid/checker texture, not colorful retail textures.

If the texture is still missing, check the generated file paths and enabled
mod. Send the editor console messages rather than installing Quake II PAKs.

## 3. Compile from the command prompt first

Save any map edits before building: this script compiles the file on disk, not
the editor's unsaved buffer. In the Heathen source root, run:

```bat
python tools\build_test_map.py --tools "C:\game projects\ericw-tools"
```

The script:

1. Checks for all three compilers before generating assets.
2. Generates the same two original assets (safe to repeat).
3. Copies the saved map into `build-maps\tpp_test`, leaving the original intact.
4. Removes stale BSP/portal/leak files in that output folder.
5. Runs `qbsp -q2bsp -leaktest`, then `vis`, then `light`.
6. Uses an explicit `mygame` asset path and disables automatic game-path search
   for QBSP and LIGHT, so installed retail asset directories are not needed.
7. Stops on the first nonzero compiler exit and checks for a Quake II
   `IBSP` version 38 header after each stage.

The full logical compiler commands are equivalent to:

```text
qbsp -q2bsp -leaktest -nodefaultpaths -path <repo>/mygame <output>/tpp_test.map
vis <output>/tpp_test.bsp
light -nodefaultpaths -path <repo>/mygame <output>/tpp_test.bsp
```

All paths are passed as individual subprocess arguments; spaces in directory
names are supported. The tools run with the output directory as their working
directory. `-leaktest` makes a detected leak a compilation error.

On success, the final output is:

```text
C:\game projects\heathen\build-maps\tpp_test\tpp_test.bsp
```

Separate captured logs are in the same folder: `qbsp.log`, `vis.log`, and
`light.log`. Other compiler diagnostics also stay in that folder. Treat the
result as successful **only if the script prints SUCCESS and returns zero**.
After a failed VIS or LIGHT stage, a partial BSP can still exist; it is not a
completed level. If a stage fails, send its log and do not proceed to launch.

No game files are deployed by the script. Do not copy the BSP into `build` or
create a launch profile yet: standalone runtime staging and remaining assets
are not ready. A successful compile verifies map processing, not in-game
collision, camera behavior, or co-op.

## TrenchBroom integration comes after the first successful compile

For now, use the single build-script command rather than manually configuring
three compiler tasks in TrenchBroom. This keeps quoting and generated output
locations consistent while we verify the pipeline. A native editor compile
profile can be added once the command-line build is confirmed.

## Developer checks and verification limits

Run stdlib-only tests from the repository root:

```bat
python -m unittest discover -s tests -v
```

The tests independently decode PCX RLE and check its palette, WAL header/mip
layout, deterministic generation, preservation of source files, argument/path
handling, compiler ordering, missing/invalid output rejection, and fail-fast
behavior. Compiler execution is mocked in unit tests; it is not an actual
QBSP/VIS/LIGHT run.

The agent sandbox could not retrieve the Linux compiler release because its
release-asset download host was inaccessible. The real compiler run and editor
palette/texture reload therefore require verification on Windows. No successful
map compile or GUI test is claimed by these scripts/tests alone.
