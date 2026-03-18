# Released under the MIT License. See LICENSE for details.
#
"""Pcommands for bacommontools."""

from __future__ import annotations


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
        ' ballistica_api_key to config/localconfig.json.'
    )
