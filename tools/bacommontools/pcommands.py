# Released under the MIT License. See LICENSE for details.
#
"""Pcommands for bacommontools."""


def bacurl() -> None:
    """Run curl with the Ballistica API key injected.

    Usage: bacurl [curl-args...] <url>

    Reads ``ballistica_api_key`` from ``pconfig/localconfig.json`` and
    passes it as a Bearer token in the Authorization header. All
    arguments are forwarded to curl. The ``-s`` (silent) flag is added
    automatically.

    Examples::

        bacurl https://dev.ballistica.net/api/v1/admin/stats/catalog
        bacurl -X POST -H 'Content-Type: application/json' \\
            -d '{"dry_run":true}' \\
            https://dev.ballistica.net/api/v1/admin/stats/flush
    """
    import json
    import subprocess

    from efro.error import CleanError
    from efrotools import pcommand

    args = pcommand.get_args()
    if not args:
        raise CleanError('Usage: bacurl [curl-args...] <url>')

    try:
        with open('pconfig/localconfig.json', encoding='utf-8') as f:
            cfg = json.load(f)
    except FileNotFoundError as exc:
        raise CleanError('pconfig/localconfig.json not found.') from exc

    api_key = cfg.get('ballistica_api_key')
    if not api_key:
        raise CleanError('No ballistica_api_key in pconfig/localconfig.json.')

    cmd = [
        'curl',
        '-s',
        '-H',
        f'Authorization: Bearer {api_key}',
        *args,
    ]
    result = subprocess.run(cmd, check=False)
    raise SystemExit(result.returncode)


def require_ballistica_api_key() -> None:
    """Verify a Ballistica API key is available; error if not."""
    import os
    from pathlib import Path

    from efro.error import CleanError
    from efrotools.project import getlocalconfig

    if os.environ.get('BALLISTICA_API_KEY'):
        return
    val = getlocalconfig(Path('.')).get('ballistica_api_key')
    if val:
        return
    raise CleanError(
        'No Ballistica API key found.\n'
        'Set the BALLISTICA_API_KEY env var or add'
        ' ballistica_api_key to pconfig/localconfig.json.'
    )


def compile_mesh() -> None:
    """Compile a display mesh from .obj to our binary .bob format.

    Usage: compile_mesh <src.obj> <dst.bob>
    """
    import os

    from efro.error import CleanError
    from efrotools import pcommand

    from bacommontools import meshcompile

    args = pcommand.get_args()
    if len(args) != 2:
        raise CleanError('Expected 2 args (src and dst paths).')

    src, dst = args

    # Show project-relative paths when possible.
    relpath = os.path.abspath(dst).removeprefix(f'{pcommand.PROJROOT}/')
    pcommand.clientprint(f'Compiling mesh: {relpath}')

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        meshcompile.compile_mesh(src, dst)
    except ValueError as exc:
        raise CleanError(f'Mesh compile failed: {exc}') from exc

    assert os.path.exists(dst)


def compile_collision_mesh() -> None:
    """Compile a collision mesh from .obj to our binary .cob format.

    Usage: compile_collision_mesh <src.obj> <dst.cob>
    """
    import os

    from efro.error import CleanError
    from efrotools import pcommand

    from bacommontools import meshcompile

    args = pcommand.get_args()
    if len(args) != 2:
        raise CleanError('Expected 2 args (src and dst paths).')

    src, dst = args

    # Show project-relative paths when possible.
    relpath = os.path.abspath(dst).removeprefix(f'{pcommand.PROJROOT}/')
    pcommand.clientprint(f'Compiling collision mesh: {relpath}')

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        meshcompile.compile_collision_mesh(src, dst)
    except ValueError as exc:
        raise CleanError(f'Collision-mesh compile failed: {exc}') from exc

    assert os.path.exists(dst)
