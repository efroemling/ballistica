# Released under the MIT License. See LICENSE for details.
#
"""Fetch and cache xcode project build paths.

This saves the few seconds it normally would take to fire up xcodebuild
and filter its output.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Optional


def project_build_path(projroot: str, project_path: str,
                       configuration: str) -> str:
    """Main script entry point."""
    # pylint: disable=too-many-locals

    config_path = os.path.join(projroot, '.cache', 'xcode_build_path')
    out_path = None
    config: dict[str, dict[str, Any]] = {}

    build_dir: Optional[str] = None

    try:
        if os.path.exists(config_path):
            with open(config_path, encoding='utf-8') as infile:
                config = json.loads(infile.read())
            if (project_path in config
                    and configuration in config[project_path]):

                # Ok we've found a build-dir entry for this project; now if it
                # exists on disk and all timestamps within it are decently
                # close to the one we've got recorded, lets use it.
                # (Anything using this script should also be building
                # stuff there so mod times should be pretty recent; if not
                # then its worth re-caching to be sure.)
                build_dir = config[project_path][configuration]['build_dir']
                timestamp = config[project_path][configuration]['timestamp']
                assert build_dir is not None
                if os.path.isdir(build_dir):
                    use_cached = True

                    # if its been over a day since we cached this, renew it
                    now = time.time()
                    if abs(now - timestamp) > 60 * 60 * 24:
                        use_cached = False

                    if use_cached:
                        out_path = build_dir
    except Exception:
        import traceback
        print('EXCEPTION checking cached build path', file=sys.stderr)
        traceback.print_exc()
        out_path = None

    # If we don't have a path at this point we look it up and cache it.
    if out_path is None:
        print('Caching xcode build path...', file=sys.stderr)
        output = subprocess.check_output([
            'xcodebuild', '-project', project_path, '-showBuildSettings',
            '-configuration', configuration
        ]).decode('utf-8')
        prefix = 'TARGET_BUILD_DIR = '
        lines = [
            l for l in output.splitlines() if l.strip().startswith(prefix)
        ]
        if len(lines) != 1:
            raise Exception(
                'TARGET_BUILD_DIR not found in xcodebuild settings output')
        build_dir = lines[0].replace(prefix, '').strip()
        if project_path not in config:
            config[project_path] = {}
        config[project_path][configuration] = {
            'build_dir': build_dir,
            'timestamp': time.time()
        }
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as outfile:
            outfile.write(json.dumps(config))

    assert build_dir is not None
    return build_dir
