"""Original first-launch placeholders, GPL-2.0-or-later (stdlib only).

No assets are extracted from Quake II or from installed system fonts. This is
an intentionally rigid block figure and a hand-specified uppercase pixel font,
not production animation/art. Asset names satisfy the unchanged game protocol.
"""

from pathlib import Path
import struct

from generate_blockout import palette_pcx


# Original 5x7 raster glyphs. Lowercase console characters use uppercase forms.
ROWS = {
    'A': '01110/10001/10001/11111/10001/10001/10001',
    'B': '11110/10001/10001/11110/10001/10001/11110',
    'C': '01111/10000/10000/10000/10000/10000/01111',
    'D': '11110/10001/10001/10001/10001/10001/11110',
    'E': '11111/10000/10000/11110/10000/10000/11111',
    'F': '11111/10000/10000/11110/10000/10000/10000',
    'G': '01111/10000/10000/10111/10001/10001/01111',
    'H': '10001/10001/10001/11111/10001/10001/10001',
    'I': '11111/00100/00100/00100/00100/00100/11111',
    'J': '00111/00010/00010/00010/10010/10010/01100',
    'K': '10001/10010/10100/11000/10100/10010/10001',
    'L': '10000/10000/10000/10000/10000/10000/11111',
    'M': '10001/11011/10101/10101/10001/10001/10001',
    'N': '10001/11001/10101/10011/10001/10001/10001',
    'O': '01110/10001/10001/10001/10001/10001/01110',
    'P': '11110/10001/10001/11110/10000/10000/10000',
    'Q': '01110/10001/10001/10001/10101/10010/01101',
    'R': '11110/10001/10001/11110/10100/10010/10001',
    'S': '01111/10000/10000/01110/00001/00001/11110',
    'T': '11111/00100/00100/00100/00100/00100/00100',
    'U': '10001/10001/10001/10001/10001/10001/01110',
    'V': '10001/10001/10001/10001/10001/01010/00100',
    'W': '10001/10001/10001/10101/10101/11011/10001',
    'X': '10001/01010/00100/00100/00100/01010/10001',
    'Y': '10001/01010/00100/00100/00100/00100/00100',
    'Z': '11111/00001/00010/00100/01000/10000/11111',
    '0': '01110/10001/10011/10101/11001/10001/01110',
    '1': '00100/01100/00100/00100/00100/00100/01110',
    '2': '01110/10001/00001/00010/00100/01000/11111',
    '3': '11110/00001/00001/01110/00001/00001/11110',
    '4': '00010/00110/01010/10010/11111/00010/00010',
    '5': '11111/10000/10000/11110/00001/00001/11110',
    '6': '01110/10000/10000/11110/10001/10001/01110',
    '7': '11111/00001/00010/00100/01000/01000/01000',
    '8': '01110/10001/10001/01110/10001/10001/01110',
    '9': '01110/10001/10001/01111/00001/00001/01110',
    '?': '01110/10001/00001/00010/00100/00000/00100',
    '!': '00100/00100/00100/00100/00100/00000/00100',
    '.': '00000/00000/00000/00000/00000/00110/00110',
    ',': '00000/00000/00000/00000/00110/00100/01000',
    ':': '00000/00110/00110/00000/00110/00110/00000',
    ';': '00000/00110/00110/00000/00110/00100/01000',
    '-': '00000/00000/00000/11111/00000/00000/00000',
    '_': '00000/00000/00000/00000/00000/00000/11111',
    '+': '00000/00100/00100/11111/00100/00100/00000',
    '=': '00000/00000/11111/00000/11111/00000/00000',
    '/': '00001/00001/00010/00100/01000/10000/10000',
    '\\': '10000/10000/01000/00100/00010/00001/00001',
    '(': '00010/00100/01000/01000/01000/00100/00010',
    ')': '01000/00100/00010/00010/00010/00100/01000',
    '[': '01110/01000/01000/01000/01000/01000/01110',
    ']': '01110/00010/00010/00010/00010/00010/01110',
    '<': '00010/00100/01000/10000/01000/00100/00010',
    '>': '01000/00100/00010/00001/00010/00100/01000',
    '"': '01010/01010/01010/00000/00000/00000/00000',
    "'": '00100/00100/01000/00000/00000/00000/00000',
    '|': '00100/00100/00100/00100/00100/00100/00100',
    '#': '01010/01010/11111/01010/11111/01010/01010',
    '%': '11001/11010/00100/00100/01000/10110/00110',
    '*': '00000/10101/01110/11111/01110/10101/00000',
    '~': '00000/00000/01001/10110/00000/00000/00000',
    '^': '00100/01010/10001/00000/00000/00000/00000',
    '`': '01000/00100/00010/00000/00000/00000/00000',
    '@': '01110/10001/10111/10101/10111/10000/01110',
    '&': '01100/10010/10100/01000/10101/10010/01101',
    '$': '00100/01111/10100/01110/00101/11110/00100',
    '{': '00010/00100/00100/01000/00100/00100/00010',
    '}': '01000/00100/00100/00010/00100/00100/01000',
}


def pcx(width, height, pixels):
    """8-bit PCX, even padded scanlines, simple per-byte RLE escaping."""
    if width < 1 or height < 1 or len(pixels) != width * height:
        raise ValueError("Invalid PCX dimensions/pixel count")
    stride = (width + 1) & ~1
    header = struct.pack('<4B6H48sBB4H54s', 10, 5, 1, 8,
                         0, 0, width - 1, height - 1, width, height,
                         bytes(48), 0, 1, stride, 1, width, height, bytes(54))
    data = bytearray(header)
    for y in range(height):
        row = bytes(pixels[y * width:(y + 1) * width]) + bytes(stride - width)
        for value in row:
            if value >= 192:
                data.extend((193, value))
            else:
                data.append(value)
    return bytes(data) + b'\x0c' + palette_pcx()[-768:]


def console_font():
    pixels = bytearray([255] * (128 * 128))
    for code in range(256):
        ch = chr(code & 127).upper()
        # Control glyphs fall back to a visible marker, except empty NUL/space.
        if (code & 127) in (0, 32):
            continue
        rows = ROWS.get(ch, ROWS['?']).split('/')
        x0, y0 = (code % 16) * 8 + 1, (code // 16) * 8
        for y, row in enumerate(rows):
            for x, bit in enumerate(row):
                if bit == '1':
                    pixels[(y0 + y) * 128 + x0 + x] = 254
    return pcx(128, 128, pixels)


def block_model(boxes, frames):
    """Build MD2 v8 with original cuboid geometry and valid strip commands.

    All frames intentionally have identical geometry. Stock player frame IDs
    0..197 remain in range without copying any Quake II animation data.
    """
    vertices, triangles = [], []
    for x0, y0, z0, x1, y1, z1 in boxes:
        offset = len(vertices)
        vertices.extend(((x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0),
                         (x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1)))
        for face in ((0,3,2,1), (4,5,6,7), (0,4,7,3),
                     (1,2,6,5), (0,1,5,4), (3,7,6,2)):
            # MD2 front faces use clockwise winding in this renderer.
            for tri in ((0,2,1), (0,3,2)):
                triangles.append((tuple(offset + face[i] for i in tri), tri))
    origin = tuple(min(v[i] for v in vertices) for i in range(3))
    skin = b'players/male/grunt.pcx'.ljust(64, b'\0')
    st = ((0,0), (63,0), (63,63), (0,63))
    texcoords = b''.join(struct.pack('<2h', *uv) for uv in st)
    tris = b''.join(struct.pack('<6H', *(xyz + uv)) for xyz, uv in triangles)
    frame_size = 40 + len(vertices) * 4
    frame_data = bytearray()
    for index in range(frames):
        frame_data.extend(struct.pack('<6f16s', 1, 1, 1, *origin,
                                      ('test%03d' % index).encode('ascii')))
        for vertex in vertices:
            frame_data.extend(struct.pack('<4B', *(vertex[i] - origin[i] for i in range(3)), 5))
    commands = bytearray()
    for xyz, uv in triangles:
        commands.extend(struct.pack('<i', 3))
        for vi, ti in zip(xyz, uv):
            commands.extend(struct.pack('<ffi', (st[ti][0] + .5) / 64,
                                        (st[ti][1] + .5) / 64, vi))
    commands.extend(struct.pack('<i', 0))
    ofs_skin = 68
    ofs_st = ofs_skin + len(skin)
    ofs_tris = ofs_st + len(texcoords)
    ofs_frames = ofs_tris + len(tris)
    ofs_commands = ofs_frames + len(frame_data)
    end = ofs_commands + len(commands)
    header = struct.pack('<17I', int.from_bytes(b'IDP2', 'little'), 8,
                         64, 64, frame_size, 1, len(vertices), 4, len(triangles),
                         len(commands) // 4, frames, ofs_skin, ofs_st,
                         ofs_tris, ofs_frames, ofs_commands, end)
    return header + skin + texcoords + tris + frame_data + commands


def generate_runtime_assets(game_dir):
    game_dir = Path(game_dir)
    # Full-height figure bounds: (-15,-7,-24) to (15,7,32).
    figure = [(-10,-7,-10,10,7,20), (-6,-6,20,6,6,32),
              (-9,-6,-24,-1,6,-10), (1,-6,-24,9,6,-10),
              (-15,-5,-8,-10,5,18), (10,-5,-8,15,5,18)]
    skin = bytes(160 if (x // 8 + y // 8) % 2 else 208
                 for y in range(64) for x in range(64))
    icon = bytes(208 if 8 <= x < 24 and 4 <= y < 28 else 48
                 for y in range(32) for x in range(32))
    files = {
        'pics/conchars.pcx': console_font(),
        'pics/conback.pcx': pcx(64, 64, bytes([24]) * 4096),
        'pics/ch1.pcx': pcx(8, 8, bytes(254 if x == 3 or y == 3 else 255
                                      for y in range(8) for x in range(8))),
        'players/male/tris.md2': block_model(figure, 198),
        'players/male/weapon.md2': block_model([(-3,-4,0,3,4,8)], 1),
        'players/male/grunt.pcx': pcx(64, 64, skin),
        'players/male/grunt_i.pcx': pcx(32, 32, icon),
    }
    for relative, data in files.items():
        path = game_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return sorted(files)
