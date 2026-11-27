"""Compile the Heathen test room with ericw-tools 2.0.0-alpha11.

Run from any directory. Tool paths are passed as arguments, never through a
shell. The editable source and its TrenchBroom settings are never modified.
"""

import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from generate_blockout import generate_assets


ROOT = Path(__file__).resolve().parents[1]


def check_bsp(path):
    """Reject missing, truncated or non-Quake-II BSP output."""
    if not path.is_file() or path.stat().st_size < 160:
        raise RuntimeError("Compiler did not produce a complete BSP header: " + str(path))
    with path.open("rb") as stream:
        magic, version = struct.unpack("<4si", stream.read(8))
    if magic != b"IBSP" or version != 38:
        raise RuntimeError("Expected vanilla Quake II IBSP version 38: " + str(path))


def build_map(tools_dir, root=ROOT):
    tools_dir = Path(tools_dir).resolve()
    root = Path(root).resolve()
    suffix = ".exe" if os.name == "nt" else ""
    tools = [tools_dir / (name + suffix) for name in ("qbsp", "vis", "light")]
    for tool in tools:
        if not tool.is_file():
            raise RuntimeError("Required compiler not found: " + str(tool))

    source = root / "mygame" / "maps" / "tpp_test.map"
    if not source.is_file():
        raise RuntimeError("Map source not found: " + str(source))

    game_dir = root / "mygame"
    generate_assets(game_dir)
    work_dir = root / "build-maps" / "tpp_test"
    work_dir.mkdir(parents=True, exist_ok=True)
    work_map = work_dir / source.name
    shutil.copyfile(source, work_map)
    bsp = work_map.with_suffix(".bsp")
    # Do not accept output or portal/leak data from a previous compile.
    for extension in (".bsp", ".prt", ".pts", ".lin"):
        work_map.with_suffix(extension).unlink(missing_ok=True)

    search_args = ["-nodefaultpaths", "-path", str(game_dir)]
    commands = (
        [str(tools[0]), "-q2bsp", "-leaktest", *search_args, str(work_map)],
        [str(tools[1]), str(bsp)],
        [str(tools[2]), *search_args, str(bsp)],
    )
    for name, command in zip(("qbsp", "vis", "light"), commands):
        log = work_dir / (name + ".log")
        print("Running", name, "(log:", str(log) + ")", flush=True)
        # Inherit stdout/stderr together so tool diagnostics are retained even
        # when a compiler exits nonzero. Never proceed after a failed stage.
        with log.open("wb") as stream:
            result = subprocess.run(command, cwd=work_dir, stdout=stream,
                                    stderr=subprocess.STDOUT, check=False)
        if result.returncode:
            raise RuntimeError("{} failed (exit {}). Read {}".format(
                name, result.returncode, log))
        check_bsp(bsp)
    print("SUCCESS:", bsp)
    print("Map compilation only; standalone game startup is not configured yet.")
    return bsp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tools", required=True, type=Path,
                        help="Folder containing qbsp, vis and light (keep DLLs/plugins nearby)")
    args = parser.parse_args()
    try:
        build_map(args.tools)
    except (OSError, RuntimeError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
