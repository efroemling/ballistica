# Released under the MIT License. See LICENSE for details.
#
"""Public schema for the Ballistica master-server REST API v1.

All endpoints require an ``Authorization: Bearer <key>`` header. Responses
are JSON; any non-200 response has an :class:`ErrorResponse` body regardless
of which endpoint was called.

See :class:`Endpoint` for the full list of available endpoints and
their usage.

Example — fetch info for the authenticated account:

.. code-block:: bash

    curl -H 'Authorization: Bearer <your-api-key>' \
https://www.ballistica.net/api/v1/accounts/me

The dataclasses here (e.g. :class:`AccountResponse`) serve as schema
documentation and can also be used directly with
:mod:`efro.dataclassio` to parse or construct values::

    from efro.dataclassio import dataclass_from_json
    from bacommon.restapi.v1 import AccountResponse

    account = dataclass_from_json(AccountResponse, response_json_str)
"""

# Module conventions (for contributors, not consumers):
# - All fields carry explicit IOAttrs storage keys even when the key matches
#   the field name. This guards against automated renaming breaking the public
#   wire format and allows variable names to diverge from wire names later.
#   Use full descriptive names (no short keys) for readability.
# - This module must remain standalone (no baserver/bamaster imports). Define
#   any needed enums locally, mirroring internal values where necessary.
# - Response dataclasses should include a 'Returned by' line in their
#   docstring with a ``:attr:`Endpoint.XXX``` reference to the associated
#   endpoint(s) where applicable.

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from efro.dataclassio import ioprepped, IOAttrs


# Convention for adding entries to Endpoint:
# - Each member's ``#:`` comment must fully document the endpoint: HTTP method,
#   auth requirements, path parameters, query parameters, and a
#   ``:class:`XxxResponse``` cross-reference to its response dataclass.
# - Run ``make docs`` after editing to verify RST formatting and that all
#   cross-references resolve correctly.
class Endpoint(StrEnum):
    """Public REST API v1 endpoint paths.

    Each value is the URL path for an endpoint; see its description for the
    HTTP method, parameters, and response type.

    Tip: use :meth:`str.format` to fill in path parameters::

        url = Endpoint.ACCOUNT.format(account_id='a-1')
    """

    #: ``GET`` — fetch public info for a single account.
    #: Returns :class:`AccountResponse`.
    #: Pass ``'me'`` as ``account_id`` to refer to the authenticated account.
    ACCOUNT = '/api/v1/accounts/{account_id}'


@ioprepped
@dataclass
class ErrorResponse:
    """Returned by all :class:`Endpoint` members on any non-200 response.

    The HTTP status code conveys the specific failure type.
    """

    #: Machine-readable error code (e.g. ``'not_found'``, ``'unauthorized'``).
    error: Annotated[str, IOAttrs('error')]
    #: Human-readable description of the error.
    message: Annotated[str, IOAttrs('message')]


@ioprepped
@dataclass
class AccountResponse:
    """Public info for a single account.

    Returned by :attr:`Endpoint.ACCOUNT`.
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
