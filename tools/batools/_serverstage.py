# Released under the MIT License. See LICENSE for details.
#
"""Staging of server-package files (wrapper script, README, config).

Split out of :mod:`batools.staging` to keep it under the module-size
limit.
"""

import os
import subprocess

from efrotools.pyver import PYVER


def write_if_changed(
    path: str, contents: str, make_executable: bool = False
) -> None:
    """Write a file only if its contents differ (keeps mtimes stable)."""
    changed: bool
    try:
        with open(path, encoding='utf-8') as infile:
            existing = infile.read()
        changed = contents != existing
    except FileNotFoundError:
        changed = True
    if changed:
        with open(path, 'w', encoding='utf-8') as outfile:
            outfile.write(contents)
        if make_executable:
            subprocess.run(['chmod', '+x', path], check=True)


def stage_server_file(
    projroot: str, mode: str, infilename: str, outfilename: str
) -> None:
    """Stage files for the server environment with some filtering."""
    import batools.build
    from efrotools.util import replace_exact

    if mode not in ('debug', 'release'):
        raise RuntimeError(
            f"Invalid server-file-staging mode '{mode}';"
            f" expected 'debug' or 'release'."
        )

    print(f'Building server file: {os.path.basename(outfilename)}')

    os.makedirs(os.path.dirname(outfilename), exist_ok=True)

    basename = os.path.basename(infilename)
    if basename == 'config_template.toml':
        # Inject all available config values into the config file.
        write_if_changed(
            outfilename,
            batools.build.filter_server_config_toml(str(projroot), infilename),
        )

    elif basename == 'ballisticakit_server.py':
        # Run Python in opt mode for release builds.
        with open(infilename, encoding='utf-8') as infile:
            lines = infile.read().splitlines()
            if mode == 'release':
                lines[0] = replace_exact(
                    lines[0],
                    f'#!/usr/bin/env -S python{PYVER} -B',
                    f'#!/usr/bin/env -S python{PYVER} -OB',
                )
        write_if_changed(
            outfilename, '\n'.join(lines) + '\n', make_executable=True
        )
    elif basename == 'README.txt':
        with open(infilename, encoding='utf-8') as infile:
            readme = infile.read()
        write_if_changed(outfilename, readme)
    elif basename == 'launch_ballisticakit_server.bat':
        # Run Python in opt mode for release builds.
        with open(infilename, encoding='utf-8') as infile:
            lines = infile.read().splitlines()
        if mode == 'release':
            lines[1] = replace_exact(
                lines[1],
                ':: Python interpreter.',
                ':: Python interpreter. (in opt mode)',
            )
            lines[2] = replace_exact(
                lines[2],
                'dist\\\\python.exe -B ballisticakit_server.py',
                'dist\\\\python.exe -OB ballisticakit_server.py',
            )
        else:
            # In debug mode we use the bundled debug interpreter.
            lines[2] = replace_exact(
                lines[2],
                'dist\\\\python.exe -B ballisticakit_server.py',
                'dist\\\\python_d.exe -B ballisticakit_server.py',
            )

        write_if_changed(outfilename, '\n'.join(lines) + '\n')
    else:
        raise RuntimeError(f"Unknown server file for staging: '{basename}'.")
