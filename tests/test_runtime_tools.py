"""File-format and staging checks; not a substitute for Windows gameplay tests."""

import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import generate_runtime
import stage_runtime


def decode_pcx(data):
    width = struct.unpack_from('<H', data, 8)[0] + 1
    height = struct.unpack_from('<H', data, 10)[0] + 1
    stride = struct.unpack_from('<H', data, 66)[0]
    pixels = bytearray()
    pos = 128
    for _ in range(height):
        row = bytearray()
        while len(row) < stride:
            value = data[pos]
            pos += 1
            if value & 192 == 192:
                row.extend([data[pos]] * (value & 63))
                pos += 1
            else:
                row.append(value)
        if len(row) != stride:
            raise AssertionError('RLE crosses scanline')
        pixels.extend(row[:width])
    assert pos == len(data) - 769
    assert data[-769] == 12
    return width, height, pixels


def fake_pe(dll=False):
    data = bytearray(90)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 64)
    data[64:68] = b'PE\0\0'
    struct.pack_into('<H', data, 68, 0x8664)
    struct.pack_into('<H', data, 84, 2)
    struct.pack_into('<H', data, 86, 0x2000 if dll else 0)
    struct.pack_into('<H', data, 88, 0x20B)
    return data


class RuntimeAssetTests(unittest.TestCase):
    def test_glyph_definitions_cover_printable_ascii(self):
        for code in range(33, 127):
            rows = generate_runtime.ROWS[chr(code).upper()].split('/')
            self.assertEqual(len(rows), 7)
            self.assertTrue(all(len(row) == 5 and set(row) <= {'0', '1'} for row in rows))

    def test_font_layout_and_transparency(self):
        width, height, pixels = decode_pcx(generate_runtime.console_font())
        self.assertEqual((width, height), (128, 128))
        self.assertEqual(set(pixels), {254, 255})
        for code in range(33, 127):
            x, y = (code % 16) * 8, (code // 16) * 8
            glyph = [pixels[(y + row) * 128 + x + col] for row in range(8) for col in range(8)]
            alternate = [pixels[(y + 64 + row) * 128 + x + col] for row in range(8) for col in range(8)]
            self.assertIn(254, glyph)
            self.assertEqual(glyph, alternate)

    def test_pcx_odd_scanline_padding_and_dimension_validation(self):
        self.assertEqual(decode_pcx(generate_runtime.pcx(3, 2, bytes([255, 192, 0, 1, 2, 3]))),
                         (3, 2, bytes([255, 192, 0, 1, 2, 3])))
        with self.assertRaises(ValueError):
            generate_runtime.pcx(3, 2, bytes(5))

    def test_md2_all_offsets_indices_frames_and_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            files = generate_runtime.generate_runtime_assets(directory)
            self.assertEqual(len(files), 7)
            for filename, frames in [('tris.md2', 198), ('weapon.md2', 1)]:
                data = (Path(directory) / 'players/male' / filename).read_bytes()
                h = struct.unpack_from('<17I', data)
                self.assertEqual((data[:4], h[1], h[2], h[3], h[5], h[10]),
                                 (b'IDP2', 8, 64, 64, 1, frames))
                self.assertEqual(h[4], 40 + h[6] * 4)
                self.assertEqual(h[11], 68)
                self.assertEqual(h[12], h[11] + 64)
                self.assertEqual(h[13], h[12] + h[7] * 4)
                self.assertEqual(h[14], h[13] + h[8] * 12)
                self.assertEqual(h[15], h[14] + h[4] * frames)
                self.assertEqual(h[16], h[15] + h[9] * 4)
                self.assertEqual(len(data), h[16])
                self.assertEqual(h[14] % 4, 0)
                skin = data[h[11]:h[11] + 64].split(b'\0')[0].decode('ascii')
                self.assertTrue((Path(directory) / skin).is_file())
                for offset in range(h[13], h[14], 12):
                    tri = struct.unpack_from('<6H', data, offset)
                    self.assertTrue(all(i < h[6] for i in tri[:3]))
                    self.assertTrue(all(i < h[7] for i in tri[3:]))
                first_vertices = data[h[14] + 40:h[14] + h[4]]
                for frame in range(frames):
                    offset = h[14] + frame * h[4]
                    scale_translate = struct.unpack_from('<6f', data, offset)
                    self.assertEqual(scale_translate[:3], (1, 1, 1))
                    self.assertEqual(data[offset + 40:offset + h[4]], first_vertices)
                    for vi in range(h[6]):
                        vertex = struct.unpack_from('<4B', data, offset + 40 + vi * 4)
                        self.assertLess(vertex[3], 162)
                        if filename == 'tris.md2':
                            pos = [vertex[i] + scale_translate[i + 3] for i in range(3)]
                            self.assertTrue(-15 <= pos[0] <= 15 and -7 <= pos[1] <= 7 and -24 <= pos[2] <= 32)
                offset = h[15]
                for _ in range(h[8]):
                    self.assertEqual(struct.unpack_from('<i', data, offset)[0], 3)
                    offset += 4
                    for _ in range(3):
                        s, t, vi = struct.unpack_from('<ffi', data, offset)
                        self.assertTrue(0 <= s <= 1 and 0 <= t <= 1 and 0 <= vi < h[6])
                        offset += 12
                self.assertEqual(struct.unpack_from('<i', data, offset)[0], 0)
                self.assertEqual(offset + 4, len(data))
            # All generated PCXs use the same original palette.
            palette = generate_runtime.palette_pcx()[-768:]
            for path in Path(directory).rglob('*.pcx'):
                decode_pcx(path.read_bytes())
                self.assertEqual(path.read_bytes()[-768:], palette)


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='heathen runtime tests ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'build').mkdir()
        for name, dll in [('q2pro.exe', False), ('gamex86_64.dll', True),
                          ('q2proded.exe', False), ('dependency.dll', True)]:
            (self.root / 'build' / name).write_bytes(fake_pe(dll))
        (self.root / 'build' / 'do-not-copy.pak').write_bytes(b'unrelated')
        game = self.root / 'mygame'
        (game / 'maps').mkdir(parents=True)
        (game / 'maps/tpp_test.map').write_text('// saved local editor settings\n')
        real_config = Path(__file__).resolve().parents[1] / 'mygame/heathen-test.cfg'
        shutil.copyfile(real_config, game / 'heathen-test.cfg')
        self.bsp = self.root / 'build-maps/tpp_test/tpp_test.bsp'
        self.bsp.parent.mkdir(parents=True)
        self.bsp.write_bytes(b'IBSP' + struct.pack('<i', 38) + bytes(152))
        self.receipt = self.bsp.parent / 'build-success.json'
        self.receipt.write_text(json.dumps({
            'schema': 1,
            'bsp_sha256': hashlib.sha256(self.bsp.read_bytes()).hexdigest(),
            'map_sha256': hashlib.sha256((game / 'maps/tpp_test.map').read_bytes()).hexdigest(),
        }))

    def test_staging_manifest_isolation_and_original_inputs(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        output = stage_runtime.stage_runtime(self.root)
        for relative, content in before.items():
            self.assertEqual((self.root / relative).read_bytes(), content)
        self.assertFalse((self.root / 'mygame/pics').exists())
        self.assertTrue((output / 'mygame/gamex86_64.dll').is_file())
        self.assertFalse((output / 'gamex86_64.dll').exists())
        self.assertTrue((output / 'dependency.dll').is_file())
        self.assertTrue((output / 'q2proded.exe').is_file())
        self.assertFalse(list(output.rglob('*.pak')))
        self.assertFalse(list(output.rglob('*.map')))
        manifest = json.loads((output / 'manifest.json').read_text())
        paths = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
        self.assertEqual(set(manifest['files']), paths - {'manifest.json'})
        for path, digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((output / path).read_bytes()).hexdigest(), digest)
        command = (output / 'launch-test.cmd').read_bytes()
        self.assertIn(b'+set libdir "."', command)
        self.assertIn(b'+set homedir ""', command)
        self.assertIn(b'+set net_ip "127.0.0.1"', command)
        self.assertIn(b'+set net_enable_ipv6 0', command)
        self.assertIn(b'\r\n', command)
        self.assertFalse(list(self.root.glob('build-runtime-stage-*')))

    def test_existing_runtime_is_never_overwritten(self):
        output = stage_runtime.stage_runtime(self.root)
        (output / 'keep.txt').write_text('user data')
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            stage_runtime.stage_runtime(self.root)
        self.assertEqual((output / 'keep.txt').read_text(), 'user data')
        other = stage_runtime.stage_runtime(self.root, 'build-runtime-02')
        self.assertNotEqual(output, other)

    def test_bad_names_missing_inputs_and_wrong_architecture(self):
        for name in ('../build-runtime', 'build', '/tmp/build-runtime', 'build-runtime/subdir'):
            with self.assertRaises(RuntimeError):
                stage_runtime.stage_runtime(self.root, name)
        executable = self.root / 'build/q2pro.exe'
        data = fake_pe()
        struct.pack_into('<H', data, 68, 0x14C)
        executable.write_bytes(data)
        with self.assertRaisesRegex(RuntimeError, 'Windows x64'):
            stage_runtime.stage_runtime(self.root)
        executable.unlink()
        with self.assertRaisesRegex(RuntimeError, 'Required input'):
            stage_runtime.stage_runtime(self.root)
        self.assertFalse((self.root / 'build-runtime').exists())

    def test_missing_or_changed_receipt_map_or_bsp_is_rejected(self):
        original = self.receipt.read_bytes()
        self.receipt.unlink()
        with self.assertRaisesRegex(RuntimeError, 'receipt'):
            stage_runtime.stage_runtime(self.root)
        self.receipt.write_bytes(original)
        for path in (self.bsp, self.root / 'mygame/maps/tpp_test.map'):
            old = path.read_bytes()
            path.write_bytes(old + b'changed')
            with self.assertRaisesRegex(RuntimeError, 'receipt'):
                stage_runtime.stage_runtime(self.root)
            path.write_bytes(old)
        self.assertFalse((self.root / 'build-runtime').exists())

    def test_generation_failure_cleans_partial_stage_only(self):
        with patch.object(stage_runtime, 'generate_runtime_assets', side_effect=OSError('test failure')):
            with self.assertRaises(OSError):
                stage_runtime.stage_runtime(self.root)
        self.assertFalse((self.root / 'build-runtime').exists())
        self.assertFalse(list(self.root.glob('build-runtime-stage-*')))
        self.assertTrue((self.root / 'mygame/maps/tpp_test.map').exists())


if __name__ == '__main__':
    unittest.main()
