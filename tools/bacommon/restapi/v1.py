# Released under the MIT License. See LICENSE for details.
#
"""REST API v1 public schema.

Convention: all fields carry explicit IOAttrs storage keys even when the key
matches the field name. This guards against automated renaming breaking the
public wire format and allows variable names to diverge from wire names later.
Use full descriptive names (no short keys) for readability.

This module must remain standalone (no baserver/bamaster imports). Define
any needed enums locally, mirroring internal values where necessary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from efro.dataclassio import ioprepped, IOAttrs


@ioprepped
@dataclass
class ErrorResponse:
    """Returned on error; HTTP status code conveys success/failure."""

    # machine-readable code, e.g. 'not_found'
    error: Annotated[str, IOAttrs('error')]
    # human-readable detail
    message: Annotated[str, IOAttrs('message')]
