"""Stage a fresh Windows x64 first-launch test, without modifying source/builds.

No downloads, no recursive asset copying, no overwrite/delete of existing test
runtimes. Use --name build-runtime-02 to stage a subsequent snapshot. DLLs come
only from the local engine build directory, never from installed Quake II.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile

from build_test_map import check_bsp
from generate_blockout import generate_assets
from generate_runtime import generate_runtime_assets

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ('@echo off\r\n'
            'cd /d "%~dp0"\r\n'
            'q2pro.exe +set basedir "." +set libdir "." +set homedir "" '
            '+set sys_forcegamelib "" +set game mygame +set fs_autoexec 0 '
            '+set s_enable 0 +set net_ip "127.0.0.1" +set net_enable_ipv6 0 '
            '+set logfile 1 +set logfile_flush 1 +exec heathen-test.cfg\r\n')


def check_pe64(path, dll=False):
    """Catch missing, wrong-platform or wrong-architecture build inputs early."""
    path = Path(path)
    size = path.stat().st_size
    with path.open('rb') as stream:
        dos = stream.read(64)
        if len(dos) != 64 or dos[:2] != b'MZ':
            raise RuntimeError('Not a Windows PE binary: ' + str(path))
        offset = struct.unpack_from('<I', dos, 60)[0]
        if offset < 64 or offset > size - 26:
            raise RuntimeError('Invalid PE header offset: ' + str(path))
        stream.seek(offset)
        pe = stream.read(26)
    if (pe[:4] != b'PE\0\0' or struct.unpack_from('<H', pe, 4)[0] != 0x8664
            or struct.unpack_from('<H', pe, 24)[0] != 0x20B):
        raise RuntimeError('Expected Windows x64 PE32+ binary: ' + str(path))
    is_dll = bool(struct.unpack_from('<H', pe, 22)[0] & 0x2000)
    if is_dll != dll:
        raise RuntimeError('Wrong executable/DLL type: ' + str(path))


def stage_runtime(root=ROOT, name='build-runtime'):
    root = Path(root).resolve()
    if not re.fullmatch(r'build-runtime(?:-[A-Za-z0-9_-]+)?', name):
        raise RuntimeError('Runtime name must be build-runtime or build-runtime-<letters/digits/dashes>')
    destination = root / name
    if destination.exists() or destination.is_symlink():
        raise RuntimeError('Runtime already exists; nothing overwritten. Use --name build-runtime-02: '
                           + str(destination))
    build = root / 'build'
    executable = build / 'q2pro.exe'
    library = build / 'gamex86_64.dll'
    bsp = root / 'build-maps/tpp_test/tpp_test.bsp'
    config = root / 'mygame/heathen-test.cfg'
    for path in (executable, library, bsp, config):
        if not path.is_file():
            raise RuntimeError('Required input not found: ' + str(path))
    check_pe64(executable)
    check_pe64(library, dll=True)
    check_bsp(bsp)
    source_map = root / 'mygame/maps/tpp_test.map'
    receipt_path = bsp.parent / 'build-success.json'
    if not receipt_path.is_file() or not source_map.is_file():
        raise RuntimeError('Missing successful map-build receipt/source. Re-run build_test_map.py.')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if (not isinstance(receipt, dict) or receipt.get('schema') != 1
            or receipt.get('bsp_sha256') != hashlib.sha256(bsp.read_bytes()).hexdigest()
            or receipt.get('map_sha256') != hashlib.sha256(source_map.read_bytes()).hexdigest()):
        raise RuntimeError('Map/BSP differs from successful build receipt. Re-run build_test_map.py.')
    # Only immediate build-directory DLLs are eligible, not subproject trees.
    dependencies = sorted(p for p in build.iterdir()
                          if p.is_file() and p.suffix.lower() == '.dll'
                          and p.name.lower() != 'gamex86_64.dll')
    for path in dependencies:
        check_pe64(path, dll=True)
    dedicated = build / 'q2proded.exe'
    if dedicated.is_file():
        check_pe64(dedicated)

    # Construct in a temporary sibling. Do not expose a partial runtime after
    # an input/copy/generation failure. TemporaryDirectory removes only its own
    # generated contents; never remove the source root or an existing runtime.
    with tempfile.TemporaryDirectory(prefix='build-runtime-stage-', dir=root) as temporary:
        stage = Path(temporary) / 'payload'
        game = stage / 'mygame'
        base = stage / 'baseq2'
        game.mkdir(parents=True)
        base.mkdir()
        shutil.copy2(executable, stage / executable.name)
        shutil.copy2(library, game / library.name)
        for dependency in dependencies:
            shutil.copy2(dependency, stage / dependency.name)
        if dedicated.is_file():
            shutil.copy2(dedicated, stage / dedicated.name)
        (game / 'maps').mkdir()
        shutil.copy2(bsp, game / 'maps/tpp_test.bsp')
        shutil.copy2(config, game / 'heathen-test.cfg')
        generate_assets(game)
        generate_runtime_assets(game)
        # Make early startup rendering work even before the mod search path is
        # selected. These are identical generated originals, not retail data.
        (base / 'pics').mkdir()
        for filename in ('colormap.pcx', 'conchars.pcx', 'conback.pcx'):
            shutil.copy2(game / 'pics' / filename, base / 'pics' / filename)
        (base / 'default.cfg').write_text('// Heathen isolated test bootstrap.\n', encoding='ascii')
        (base / 'q2pro.menu').write_text('// No retail-art menus in first-launch test.\n', encoding='ascii')
        (stage / 'launch-test.cmd').write_bytes(LAUNCHER.encode('ascii'))
        # Asset provenance and exact staged-file hashes help diagnose accidental
        # runtime changes. This is not a security signature or a release bill of materials.
        files = {p.relative_to(stage).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(stage.rglob('*')) if p.is_file()}
        if any(Path(path).suffix.lower() in ('.pak', '.pkz', '.zip') for path in files):
            raise RuntimeError('Unexpected asset archive in runtime')
        manifest = {'schema': 1, 'purpose': 'Heathen first-launch diagnostic',
                    'asset_source': 'Original generated placeholders; GPL-2.0-or-later',
                    'files': files}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        if destination.exists() or destination.is_symlink():
            raise RuntimeError('Runtime appeared during staging; nothing overwritten')
        stage.rename(destination)
    print('STAGED:', destination)
    print('Launch on Windows:', destination / 'launch-test.cmd')
    print('Not yet verified in-game; no existing runtime or map source was changed.')
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='build-runtime', help='New ignored runtime folder name')
    args = parser.parse_args()
    try:
        stage_runtime(name=args.name)
    except (OSError, RuntimeError, ValueError) as error:
        print('ERROR:', error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
