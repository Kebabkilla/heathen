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
[test-room source](mygame/maps/tpp_test.map). This is an editor-only blockout
checkpoint: textures, map compilation, and standalone runtime assets are not
configured yet.
