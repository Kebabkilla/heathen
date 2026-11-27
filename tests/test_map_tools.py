"""Stdlib-only checks; real compiler/TrenchBroom checks are separate."""

import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_test_map
import generate_blockout


class AssetTests(unittest.TestCase):
    def test_pcx_header_rle_and_palette(self):
        data = generate_blockout.palette_pcx()
        self.assertEqual(data[:4], bytes((10, 5, 1, 8)))
        self.assertEqual(struct.unpack_from("<6H", data, 4), (0, 0, 15, 15, 16, 16))
        self.assertEqual(data[65], 1)
        self.assertEqual(struct.unpack_from("<H", data, 66)[0], 16)
        self.assertEqual(data[-769], 12)
        expected_palette = bytes(c for i in range(256) for c in (i, i, i))
        self.assertEqual(data[-768:], expected_palette)
        decoded = bytearray()
        position = 128
        while position < len(data) - 769:
            value = data[position]
            position += 1
            if value & 0xC0 == 0xC0:
                count = value & 0x3F
                decoded.extend([data[position]] * count)
                position += 1
            else:
                decoded.append(value)
        self.assertEqual(decoded, bytes(range(256)))

    def test_wal_header_mips_and_transparency(self):
        data = generate_blockout.blockout_wal()
        header = struct.unpack_from("<32s6I32s3I", data)
        self.assertEqual(header[0].rstrip(b"\0"), b"heathen/blockout")
        self.assertEqual(header[1:3], (64, 64))
        offset = 100
        for level, actual in enumerate(header[3:7]):
            self.assertEqual(actual, offset)
            offset += (64 >> level) ** 2
        self.assertEqual(len(data), offset)
        self.assertEqual(header[7:], (bytes(32), 0, 1, 0))
        self.assertNotIn(255, data[100:])
        self.assertEqual(set(data[100:]), {48, 64, 112})

    def test_generation_is_deterministic_and_preserves_other_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / "keep.txt"
            sentinel.write_text("untouched")
            paths = generate_blockout.generate_assets(root)
            first = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
            self.assertEqual(generate_blockout.generate_assets(root), paths)
            self.assertEqual(first, [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths])
            self.assertEqual(sentinel.read_text(), "untouched")
            self.assertEqual(set(p.relative_to(root).as_posix() for p in paths),
                             {"pics/colormap.pcx", "textures/heathen/blockout.wal"})


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="heathen map tests ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project with spaces"
        self.source = self.root / "mygame/maps/tpp_test.map"
        self.source.parent.mkdir(parents=True)
        self.source.write_text('// Local editor settings must be preserved.\n')
        self.tools = Path(self.temporary.name) / "tools with spaces"
        self.tools.mkdir()
        suffix = ".exe" if os.name == "nt" else ""
        for name in ("qbsp", "vis", "light"):
            (self.tools / (name + suffix)).touch()
        self.bsp = self.root / "build-maps/tpp_test/tpp_test.bsp"

    def compiler_success(self, command, **kwargs):
        self.assertIsInstance(command, list)
        self.assertNotIn("shell", kwargs)
        self.assertEqual(kwargs["cwd"], self.bsp.parent)
        self.assertEqual(kwargs["stderr"], subprocess.STDOUT)
        self.assertFalse(kwargs["check"])
        kwargs["stdout"].write(b"mock compiler output\n")
        self.bsp.write_bytes(struct.pack("<4si", b"IBSP", 38) + bytes(152))
        return subprocess.CompletedProcess(command, 0)

    def test_success_stages_paths_source_and_logs(self):
        before = self.source.read_bytes()
        # A previous result must be removed before invoking qbsp.
        self.bsp.parent.mkdir(parents=True)
        self.bsp.write_bytes(b"stale")
        def run(command, **kwargs):
            if Path(command[0]).stem == "qbsp":
                self.assertFalse(self.bsp.exists())
            return self.compiler_success(command, **kwargs)
        with patch.object(build_test_map.subprocess, "run", side_effect=run) as mocked:
            self.assertEqual(build_test_map.build_map(self.tools, self.root), self.bsp)
        self.assertEqual(mocked.call_count, 3)
        commands = [call.args[0] for call in mocked.call_args_list]
        self.assertEqual([Path(c[0]).stem for c in commands], ["qbsp", "vis", "light"])
        self.assertIn("-q2bsp", commands[0])
        self.assertIn("-leaktest", commands[0])
        for command in (commands[0], commands[2]):
            self.assertIn("-nodefaultpaths", command)
            self.assertEqual(command[command.index("-path") + 1], str(self.root / "mygame"))
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(self.bsp.with_suffix(".map").read_bytes(), before)
        for name in ("qbsp", "vis", "light"):
            self.assertEqual((self.bsp.parent / (name + ".log")).read_bytes(),
                             b"mock compiler output\n")

    def test_failure_at_each_stage_stops_the_pipeline(self):
        for stage in range(3):
            with self.subTest(stage=stage):
                calls = []
                def run(command, **kwargs):
                    calls.append(command)
                    if len(calls) == stage + 1:
                        kwargs["stdout"].write(b"compile failure\n")
                        return subprocess.CompletedProcess(command, 7)
                    return self.compiler_success(command, **kwargs)
                with patch.object(build_test_map.subprocess, "run", side_effect=run):
                    with self.assertRaisesRegex(RuntimeError, "exit 7"):
                        build_test_map.build_map(self.tools, self.root)
                self.assertEqual(len(calls), stage + 1)

    def test_success_exit_without_output_is_rejected(self):
        with patch.object(build_test_map.subprocess, "run",
                          return_value=subprocess.CompletedProcess([], 0)) as mocked:
            with self.assertRaisesRegex(RuntimeError, "complete BSP header"):
                build_test_map.build_map(self.tools, self.root)
        self.assertEqual(mocked.call_count, 1)

    def test_non_q2_output_is_rejected(self):
        self.bsp.parent.mkdir(parents=True)
        self.bsp.write_bytes(bytes(160))
        with self.assertRaisesRegex(RuntimeError, "IBSP version 38"):
            build_test_map.check_bsp(self.bsp)

    def test_missing_tools_fail_before_generating_assets(self):
        with self.assertRaisesRegex(RuntimeError, "Required compiler not found"):
            build_test_map.build_map(self.tools / "missing", self.root)
        self.assertFalse((self.root / "mygame/pics").exists())


if __name__ == "__main__":
    unittest.main()
