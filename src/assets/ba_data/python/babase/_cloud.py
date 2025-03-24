# Released under the MIT License. See LICENSE for details.
#
"""Cloud related functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    pass


class CloudSubscription:
    """User handle to a subscription to some cloud data.

    Do not instantiate these directly; use the subscribe methods in
    :class:`~baplus.CloudSubsystem` to create them.
    """

    def __init__(self, subscription_id: int) -> None:
        self._subscription_id = subscription_id

    def __del__(self) -> None:
        if _babase.app.plus is not None:
            _babase.app.plus.cloud.unsubscribe(self._subscription_id)
