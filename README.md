# heathen
code for the heretic 2 game inpsired in id tech engine - with more rpg elements

## Development baseline

Q2PRO engine and bundled game sources are now included. See [UPSTREAM.md](UPSTREAM.md)
for the pinned source revision, Windows build steps, verification limits, and
camera architecture notes. The original upstream README is preserved in
[README.q2pro.md](README.q2pro.md); upstream build prerequisites are in
[BUILDING.md](BUILDING.md).

This is currently an unmodified engine/game baseline, not yet an asset-independent
standalone game. No Quake II retail assets are included. See [LICENSE](LICENSE)
for the engine/game license.

## Level editor

Start with the [Windows TrenchBroom guide](doc/trenchbroom.md). The repository
includes a minimal [game.fgd](game.fgd) and an original
[test-room source](mygame/maps/tpp_test.map). Then follow the
[original blockout assets and map compilation guide](doc/map-compilation.md)
to generate the texture/palette and build the room with ericw-tools. Generated
assets and compiler output are ignored; only their source tools are tracked.
For the next diagnostic step, see [First standalone Windows launch](doc/first-launch.md):
original font/player placeholders and a fresh ignored runtime staging folder.
Actual Windows startup and movement require manual verification; this is not
a production-ready runtime asset set or a verified third-person/co-op feature.
