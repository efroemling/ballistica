# Released under the MIT License. See LICENSE for details.
#
"""Analytics functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bacommon.cloud
import _babase

from babase._logging import balog

if TYPE_CHECKING:
    from bacommon.analytics import AnalyticsEvent


class AnalyticsSubsystem:
    """Subsystem for wrangling analytics.

    Access the single shared instance of this class via the
    :attr:`~babase.App.analytics` attr on the :class:`~babase.App`
    class.
    """

    def __init__(self) -> None:
        self.enabled: bool = True

    def submit_event(self, event: AnalyticsEvent) -> None:
        """Submit an event.

        Should only be called from the logic thread.
        """

        if not _babase.in_logic_thread():
            balog.error(
                'submit_event() called outside logic thread.', stack_info=True
            )
            return

        # No-op if analytics are disabled or we don't have plus.
        if not self.enabled:
            return

        plus = _babase.app.plus
        if plus is None:
            return

        # Currently just no-op if it seems we're not connected. Perhaps
        # in the future we'd want to save these and submit later when we
        # are.
        if not plus.cloud.is_connected():
            return

        # Just kick off an immediate send in the bg with or without
        # account info.
        account = plus.accounts.primary
        if account is None:
            plus.cloud.send_message_cb(
                bacommon.cloud.AnalyticsEventMessage(event),
                on_response=self._on_analytics_message_response,
            )
        else:
            with account:
                plus.cloud.send_message_cb(
                    bacommon.cloud.AnalyticsEventMessage(event),
                    on_response=self._on_analytics_message_response,
                )

    def _on_analytics_message_response(
        self, response: Exception | None
    ) -> None:
        pass
