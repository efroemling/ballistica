# Released under the MIT License. See LICENSE for details.
#
"""Account related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any


class AccountV2Subsystem:
    """Subsystem for modern account handling in the app.

    Category: **App Classes**

    Access the single shared instance of this class at 'ba.app.accounts_v2'.
    """

    def __init__(self) -> None:

        # Whether or not everything related to an initial login
        # (or lack thereof) has completed. This includes things like
        # workspace syncing. Completion of this is what flips the app
        # into 'running' state.
        self._initial_login_completed = False

        self._kicked_off_workspace_load = False

    def on_app_launch(self) -> None:
        """Should be called at standard on_app_launch time."""

    def set_primary_credentials(self, credentials: str | None) -> None:
        """Set credentials for the primary app account."""
        raise RuntimeError('This should be overridden.')

    def have_primary_credentials(self) -> bool:
        """Are credentials currently set for the primary app account?

        Note that this does not mean these credentials are currently valid;
        only that they exist. If/when credentials are validated, the 'primary'
        account handle will be set.
        """
        raise RuntimeError('This should be overridden.')

    @property
    def primary(self) -> AccountV2Handle | None:
        """The primary account for the app, or None if not logged in."""
        return None

    def do_get_primary(self) -> AccountV2Handle | None:
        """Internal - should be overridden by subclass."""
        return None

    def on_primary_account_changed(
        self, account: AccountV2Handle | None
    ) -> None:
        """Callback run after the primary account changes.

        Will be called with None on log-outs or when new credentials
        are set but have not yet been verified.
        """
        # Currently don't do anything special on sign-outs.
        if account is None:
            return

        # If this new account has a workspace, update it and ask to be
        # informed when that process completes.
        if account.workspaceid is not None:
            assert account.workspacename is not None
            if (
                not self._initial_login_completed
                and not self._kicked_off_workspace_load
            ):
                self._kicked_off_workspace_load = True
                _ba.app.workspaces.set_active_workspace(
                    account=account,
                    workspaceid=account.workspaceid,
                    workspacename=account.workspacename,
                    on_completed=self._on_set_active_workspace_completed,
                )
            else:
                # Don't activate workspaces if we've already told the game
                # that initial-log-in is done or if we've already kicked
                # off a workspace load.
                _ba.screenmessage(
                    f'\'{account.workspacename}\''
                    f' will be activated at next app launch.',
                    color=(1, 1, 0),
                )
                _ba.playsound(_ba.getsound('error'))
            return

        # Ok; no workspace to worry about; carry on.
        if not self._initial_login_completed:
            self._initial_login_completed = True
            _ba.app.on_initial_login_completed()

    def on_no_initial_primary_account(self) -> None:
        """Callback run if the app has no primary account after launch.

        Either this callback or on_primary_account_changed will be called
        within a few seconds of app launch; the app can move forward
        with the startup sequence at that point.
        """
        if not self._initial_login_completed:
            self._initial_login_completed = True
            _ba.app.on_initial_login_completed()

    def _on_set_active_workspace_completed(self) -> None:
        if not self._initial_login_completed:
            self._initial_login_completed = True
            _ba.app.on_initial_login_completed()


class AccountV2Handle:
    """Handle for interacting with a V2 account.

    This class supports the 'with' statement, which is how it is
    used with some operations such as cloud messaging.
    """

    def __init__(self) -> None:
        self.tag = '?'

        self.workspacename: str | None = None
        self.workspaceid: str | None = None

    def __enter__(self) -> None:
        """Support for "with" statement."""

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Any:
        """Support for "with" statement."""
