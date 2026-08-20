# Released under the MIT License. See LICENSE for details.
#
"""Fetch debug symbols for prefab binaries on demand.

Prefab binaries ship without debug-symbol files to keep downloads
small, but symbols for recent builds are archived server-side and can
be fetched for any binary by its content hash. With a symbols file
sitting next to its binary, native stack traces in fatal-error output
come out fully symbolicated (file and line numbers included), which
makes crash reports vastly more useful.

Currently this covers the Windows prefab binaries (.pdb files); other
platforms either embed their debug info in the binary itself (Linux)
or are not yet covered (macOS).
"""

import hashlib
import json
import os
import urllib.error
import urllib.request

from efro.error import CleanError
from efro.terminal import Clr

# Master-server host per fleet; mirrors the scheme used by bacloud
# (BA_FLEET env var, 'prod' default). Only meaningful for developer
# setups; public users always talk to prod.
_FLEET_HOSTS = {
    'prod': 'www.ballistica.net',
    'test': 'test.ballistica.net',
    'dev': 'dev.ballistica.net',
}

# Windows prefab binaries that can have .pdb symbol sidecars.
_EXE_PATHS = [
    'build/prefab/full/windows_x86_64_gui/debug/BallisticaKit.exe',
    'build/prefab/full/windows_x86_64_gui/release/BallisticaKit.exe',
    'build/prefab/full/windows_x86_64_server/debug/dist'
    '/BallisticaKitHeadless.exe',
    'build/prefab/full/windows_x86_64_server/release/dist'
    '/BallisticaKitHeadless.exe',
]


def _sha256_file(path: str) -> str:
    sha = hashlib.sha256()
    with open(path, 'rb') as infile:
        while True:
            chunk = infile.read(1024 * 1024)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _fetch_symbols_for_exe(exe_path: str, host: str) -> bool:
    """Fetch symbols for one binary; return True if fetched."""
    exe_sha = _sha256_file(exe_path)
    url = f'https://{host}/api/v1/prefab-symbols/{exe_sha}'
    try:
        with urllib.request.urlopen(url) as response:
            info = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(
                f'{Clr.YLW}No symbols available for'
                f' {Clr.BLD}{exe_path}{Clr.RST}{Clr.YLW} (symbols are'
                f' kept for recent builds only).{Clr.RST}'
            )
            return False
        raise CleanError(
            f'Symbols lookup failed for {exe_path}:'
            f' HTTP {exc.code} from {url}.'
        ) from exc

    pdb_path = os.path.join(os.path.dirname(exe_path), info['file_name'])
    size_mb = info['size'] / (1024 * 1024)
    print(
        f'Downloading symbols for {Clr.BLD}{exe_path}{Clr.RST}'
        f' ({size_mb:.1f} MB)...',
        flush=True,
    )
    pdb_path_tmp = f'{pdb_path}.download'
    with urllib.request.urlopen(info['download_url']) as response:
        with open(pdb_path_tmp, 'wb') as outfile:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                outfile.write(chunk)
    os.replace(pdb_path_tmp, pdb_path)
    print(f'{Clr.GRN}Wrote {Clr.BLD}{pdb_path}{Clr.RST}{Clr.GRN}.{Clr.RST}')
    return True


def fetch_prefab_symbols() -> None:
    """Fetch symbol files for all present Windows prefab binaries."""
    fleet = os.environ.get('BA_FLEET', 'prod').lower()
    host = _FLEET_HOSTS.get(fleet)
    if host is None:
        raise CleanError(f"Invalid BA_FLEET value '{fleet}'.")

    exe_paths = [p for p in _EXE_PATHS if os.path.isfile(p)]
    if not exe_paths:
        raise CleanError(
            'No Windows prefab binaries found under build/prefab; run a'
            " prefab build first (e.g. 'make prefab-gui-debug-build')."
        )

    fetched = sum(
        1 for exe_path in exe_paths if _fetch_symbols_for_exe(exe_path, host)
    )
    print(
        f'Fetched symbols for {fetched} of {len(exe_paths)}'
        f' prefab binaries.'
    )
