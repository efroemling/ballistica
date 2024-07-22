# Released under the MIT License. See LICENSE for details.
#
"""Call related functionality shared between all efro components."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# TODO: should deprecate tpartial since it nowadays simply wraps
# functools.partial (mypy added support for functools.partial in 1.11 so
# there's no benefit to rolling our own type-safe version anymore).
# Perhaps we can use Python 13's @warnings.deprecated() stuff for this.
tpartial = functools.partial
