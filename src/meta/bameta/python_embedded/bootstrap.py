# Released under the MIT License. See LICENSE for details.
#
"""Ballistica bootstrapping."""

# This code runs in the logic thread to bootstrap ballistica.

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    pass

# All we do here is make our script files accessible and then hand it off
# to them.

# Let's lookup mods first (so users can do whatever they want).
# and then our bundled scripts last (don't want bundled site-package
# stuff overwriting system versions)
sys.path.insert(0, _ba.env()['python_directory_user'])
sys.path.append(_ba.env()['python_directory_app'])
sys.path.append(_ba.env()['python_directory_app_site'])

# The import is down here since it won't work until we muck with paths.
# noinspection PyProtectedMember
# pylint: disable=wrong-import-position
from ba._bootstrap import bootstrap

bootstrap()
