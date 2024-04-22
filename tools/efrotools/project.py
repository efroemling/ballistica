# Released under the MIT License. See LICENSE for details.
#
"""Project related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal


def get_public_legal_notice(
    style: Literal['python', 'c++', 'makefile', 'raw']
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
