# Released under the MIT License. See LICENSE for details.
#
"""Project related functionality."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal, Any

# Cache these since we may repeatedly fetch these in batch mode.
_g_project_configs: dict[str, dict[str, Any]] = {}
_g_local_configs: dict[str, dict[str, Any]] = {}


def get_public_legal_notice(
    style: Literal['python', 'c++', 'makefile', 'raw'],
) -> str:
    """Return the license notice as used for our public facing stuff.

    'style' arg can be 'python', 'c++', or 'makefile, or 'raw'.
    """
    # FIXME: Probably don't need style here for the minimal amount we're
    # doing with it now.
    if style == 'raw':
        return 'Released under the MIT License. See LICENSE for details.'
    if style == 'python':
        return '# Released under the MIT License. See LICENSE for details.'
    if style == 'makefile':
        return '# Released under the MIT License. See LICENSE for details.'
    if style == 'c++':
        return '// Released under the MIT License. See LICENSE for details.'
    raise RuntimeError(f'Invalid style: {style}')


def get_non_public_legal_notice() -> str:
    """Return the one line legal notice we expect private repo files to have."""
    # TODO: Move this to project config or somewhere not hard-coded.
    return 'Copyright (c) 2011-2024 Eric Froemling'


def get_non_public_legal_notice_prev() -> str:
    """Allows us to auto-update."""
    # TODO: Move this to project config or somewhere not hard-coded.
    return 'Copyright (c) 2011-2023 Eric Froemling'


def getlocalconfig(projroot: Path | str) -> dict[str, Any]:
    """Return a project's localconfig contents (or default if missing)."""
    projrootstr = str(projroot)
    if projrootstr not in _g_local_configs:
        localconfig: dict[str, Any]

        # Allow overriding path via env var.
        path = os.environ.get('EFRO_LOCALCONFIG_PATH')
        if path is None:
            path = 'config/localconfig.json'

        try:
            with open(Path(projroot, path), encoding='utf-8') as infile:
                localconfig = json.loads(infile.read())
        except FileNotFoundError:
            localconfig = {}
        _g_local_configs[projrootstr] = localconfig

    return _g_local_configs[projrootstr]


def getprojectconfig(projroot: Path | str) -> dict[str, Any]:
    """Return a project's projectconfig contents (or default if missing)."""
    projrootstr = str(projroot)
    if projrootstr not in _g_project_configs:
        config: dict[str, Any]
        try:
            with open(
                Path(projroot, 'config/projectconfig.json'), encoding='utf-8'
            ) as infile:
                config = json.loads(infile.read())
        except FileNotFoundError:
            config = {}
        _g_project_configs[projrootstr] = config
    return _g_project_configs[projrootstr]


def setprojectconfig(projroot: Path | str, config: dict[str, Any]) -> None:
    """Set the project config contents."""
    projrootstr = str(projroot)
    _g_project_configs[projrootstr] = config
    os.makedirs(Path(projroot, 'config'), exist_ok=True)
    with Path(projroot, 'config/projectconfig.json').open(
        'w', encoding='utf-8'
    ) as outfile:
        outfile.write(json.dumps(config, indent=2))
