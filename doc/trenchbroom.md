# TrenchBroom: first editor checkpoint (Windows)

This step opens an original blockout in the editor. It does **not** yet produce
an asset-independent playable game. No Quake II PAKs are needed for this editor
checkpoint. No engine/game C code or Meson options change, so there is no need
to reconfigure or rebuild the engine just for these files.

## 1. Install / extract TrenchBroom

Use the normal stable Windows distribution. If it is an installer, use its
normal defaults. If it is a ZIP, extract the **whole archive**, for example to
`C:\Tools\TrenchBroom`, and run `TrenchBroom.exe` there. Do not run it from inside
the ZIP or copy only its EXE: it needs its bundled resources.

Keep the editor separate from the Heathen repository and its build folder.

## 2. Update the project

After these files have been pushed to the working branch, in a command prompt:

```bat
cd /d "C:\game projects\heathen" && git pull --ff-only
```

The editor files are:

- `game.fgd`: a deliberately small definition set for existing stock entities;
  uses colored boxes instead of retail model previews.
- `mygame\maps\tpp_test.map`: original Quake II-format room source.
- This guide.

## 3. Select Quake 2 support

Start TrenchBroom. In **File > Preferences > Games**, select **Quake 2** and set
its game path to:

```text
C:\game projects\heathen
```

This is the **editor authoring root**: `mygame` is a subdirectory of it. It is
not the `build` directory or the path to the EXE. We will establish a separate
runtime staging layout later; on Windows the engine normally uses its EXE
directory as its working directory.

Some versions offer an **Open preferences...** button in the game selection
dialog instead. The built-in Quake 2 configuration is sufficient for this
blockout; do not install another game's game configuration or edit files inside
TrenchBroom's installation.

The stock configuration searches `baseq2` by default, which is absent here.
Missing game assets/material warnings are expected at this stage. TrenchBroom
supports editing without an installed retail game.

## 4. Open the supplied map

Use **File > Open** and choose:

```text
C:\game projects\heathen\mygame\maps\tpp_test.map
```

If asked for the game/format, choose **Quake 2**, format **Quake2** (the standard
Quake II format, not Quake 1, Quake III, or the Valve variant).

In the **Map Inspector**, expand **Mods** and enable **mygame**. The game path
above must be set first for this directory to appear. `mygame` is the only
additional mod needed; do not enable `src`, `build`, or other source folders.

## 5. Load Heathen entity definitions

In the **Entity Inspector**, open the entity browser's **Settings** area.
Under external definitions, click **Browse** and select:

```text
C:\game projects\heathen\game.fgd
```

Switch back to **Browser**. The small set of point entities should include:

- `info_player_start`: first player's spawn, green box.
- `info_player_coop`: additional players' spawns, blue boxes.
- `light`: static point lights, yellow boxes.

`worldspawn` describes the room's world brushes. These are existing server
entities, not new RPG functionality. The light's brightness and `_color` are
for the map compiler. No retail model previews are referenced.

TrenchBroom may store the chosen definition path and mod selection in the map's
`_tb_def` and `_tb_mod` editor properties. If prompted, prefer relative paths
for portability. Do not commit machine-specific absolute paths.

## 6. Inspect, do not compile yet

The map contains seven world brushes: floor, ceiling, four outside walls, and
an interior column for future camera obstruction tests. The empty room is
512 x 512 units, 256 units high, with 32-unit-thick enclosing brushes. There
is one primary spawn, three additional co-op spawns, and four static lights.

The map references `heathen/blockout`, an **intentional missing texture
placeholder**. Expect missing-texture surfaces and no real material collection;
this does not mean your installation failed. Do not substitute retail assets.

If the 3D camera is outside the room, navigate inside. Its center is approximately
`0 0 128`, and the primary spawn is `0 -160 24`. Basic navigation: hold the right
mouse button to look, use the scroll wheel to move forward/backward, and hold
the middle mouse button to pan. Use 2D views to inspect the enclosing walls.

For your first session, leave the source unchanged or use **Save As** to create
`mygame\maps\tpp_sandbox.map` for experiments. Do not delete the ceiling or an
outer wall in the actual test room: that would introduce a leak.

**Success for this checkpoint:** the room loads with no brush/map parse errors,
and the spawn/light boxes are visible. Missing texture/asset warnings are
expected; malformed brushes, unknown FGD syntax, or missing `game.fgd` are not.

Send a screenshot of the editor or any unexpected error. This repository has
not yet been GUI-tested in your TrenchBroom version.

## Next checkpoint (not configured here)

1. Provide original/licensed WAL textures and a palette, shared consistently
   between the editor, map compiler, and engine.
2. Install an ericw-tools build with Quake II support; configure `qbsp -q2`,
   `vis`, and `light`, with generated output outside tracked sources.
3. Resolve original engine/game startup asset requirements (palette, font,
   player model, precaches, and other required resources).
4. Stage the compiled map, game DLL, configuration, and original assets in a
   defined runtime folder and test-launch it.

Do not set up a compile/run profile or try launching `tpp_test` in Q2PRO yet:
there is no BSP or complete standalone asset set. Compiled `.bsp`, `.prt`,
`.pts`, and diagnostic `.log` files stay ignored. The `.map` and `game.fgd`
remain source-controlled.
