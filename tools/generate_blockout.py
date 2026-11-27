"""Generate original, deterministic editor/compiler test assets (stdlib only).

These grayscale blockout assets are authored for Heathen, not extracted from
Quake II. They are distributed under the project's GPL-2.0-or-later license.
The PCX is a palette carrier, not a software renderer's lighting colormap.
"""

import argparse
from pathlib import Path
import struct


GAME_DIR = Path(__file__).resolve().parents[1] / "mygame"
TEXTURE_NAME = "heathen/blockout"


def palette_pcx():
    """Return a valid 16x16, 8-bit RLE PCX containing our grayscale palette."""
    header = struct.pack(
        "<4B6H48sBB4H54s",
        10, 5, 1, 8,                 # PCX v5, RLE, 8 bits per pixel
        0, 0, 15, 15, 16, 16,        # bounds and resolution
        bytes(48), 0, 1,             # legacy palette, reserved, one color plane
        16, 1, 16, 16, bytes(54),     # bytes/line, palette info, screen size, pad
    )
    pixels = bytearray()
    for index in range(256):
        if index >= 0xC0:
            pixels.extend((0xC1, index))
        else:
            pixels.append(index)
    # Entry 255 is reserved for transparency by Q2PRO. The WAL never uses it.
    palette = bytes(component for index in range(256) for component in (index,) * 3)
    return header + pixels + b"\x0c" + palette


def blockout_wal():
    """Return a 64x64 Quake II WAL, including all four mip levels."""
    mips = []
    for level in range(4):
        width = 64 >> level
        pixels = bytearray()
        for y in range(width):
            for x in range(width):
                # Keep a visible grid even at the smallest mip level.
                period = max(2, 16 >> level)
                if x % period == 0 or y % period == 0:
                    index = 112
                else:
                    index = 48 if ((x // period) + (y // period)) % 2 else 64
                pixels.append(index)
        mips.append(bytes(pixels))
    offsets = []
    offset = 100  # sizeof Quake II miptex_t
    for mip in mips:
        offsets.append(offset)
        offset += len(mip)
    header = struct.pack(
        "<32s6I32s3I", TEXTURE_NAME.encode("ascii"), 64, 64, *offsets,
        bytes(32), 0, 1, 0,  # no animation; no surface flags; CONTENTS_SOLID
    )
    return header + b"".join(mips)


def generate_assets(game_dir=GAME_DIR):
    """Write only the two named, generated assets; leave map sources untouched."""
    outputs = (
        (Path(game_dir) / "pics" / "colormap.pcx", palette_pcx()),
        (Path(game_dir) / "textures" / "heathen" / "blockout.wal", blockout_wal()),
    )
    for path, data in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != data:
            path.write_bytes(data)
    return [path for path, _ in outputs]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, default=GAME_DIR)
    args = parser.parse_args()
    for path in generate_assets(args.game_dir):
        print("Generated:", path)
    print("Editor/compiler assets only; this is not a complete playable asset set.")


if __name__ == "__main__":
    main()
