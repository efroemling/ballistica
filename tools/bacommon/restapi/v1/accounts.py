# Released under the MIT License. See LICENSE for details.
#
# See CLAUDE.md in this directory for contributor conventions.
"""Account response types for REST API v1."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Annotated

from efro.dataclassio import ioprepped, IOAttrs


@ioprepped
@dataclass
class AccountResponse:
    """Public info for a single account.

    Returned by :attr:`~bacommon.restapi.v1.Endpoint.ACCOUNT` and
    :attr:`~bacommon.restapi.v1.Endpoint.ACCOUNT_BY_TAG`.
    """

    #: Unique account ID (e.g. ``'a-12345'``).
    id: Annotated[str, IOAttrs('id')]
    #: Globally unique display name for the account.
    tag: Annotated[str, IOAttrs('tag')]
    #: When the account was created.
    create_time: Annotated[
        datetime.datetime, IOAttrs('create_time', time_format='iso')
    ]
    #: The most recent day the account was active, or ``None`` if unknown.
    last_active_day: Annotated[datetime.date | None, IOAttrs('last_active_day')]
    #: Number of distinct days the account has been active.
    total_active_days: Annotated[int, IOAttrs('total_active_days')]
