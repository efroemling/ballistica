# Released under the MIT License. See LICENSE for details.
#
"""Account related functionality."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any

    from bacommon.login import LoginType
    from ba._login import LoginAdapter


class AccountV2Subsystem:
    """Subsystem for modern account handling in the app.

    Category: **App Classes**

    Access the single shared instance of this class at 'ba.app.accounts_v2'.
    """

    def __init__(self) -> None:
        from bacommon.login import LoginType

        # Whether or not everything related to an initial login
        # (or lack thereof) has completed. This includes things like
        # workspace syncing. Completion of this is what flips the app
        # into 'running' state.
        self._initial_login_completed = False

        self._kicked_off_workspace_load = False

        self.login_adapters: dict[LoginType, LoginAdapter] = {}

        self._implicit_signed_in_adapter: LoginAdapter | None = None
        self._auto_signed_in = False

        if _ba.app.platform == 'android' and _ba.app.subplatform == 'google':
            from ba._login import LoginAdapterGPGS

            self.login_adapters[LoginType.GPGS] = LoginAdapterGPGS(
                LoginType.GPGS
            )

    def on_app_launch(self) -> None:
        """Should be called at standard on_app_launch time."""

        for adapter in self.login_adapters.values():
            adapter.on_app_launch()

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
        return self.do_get_primary()

    def do_get_primary(self) -> AccountV2Handle | None:
        """Internal - should be overridden by subclass."""
        return None

    def on_primary_account_changed(
        self, account: AccountV2Handle | None
    ) -> None:
        """Callback run after the primary account changes.

        Will be called with None on log-outs and when new credentials
        are set but have not yet been verified.
        """
        assert _ba.in_logic_thread()

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

    def on_active_logins_changed(self, logins: dict[LoginType, str]) -> None:
        """Should be called when logins for the active account change."""

        for adapter in self.login_adapters.values():
            adapter.set_active_logins(logins)

    def on_implicit_login(
        self, login_type: LoginType, login_id: str, display_name: str
    ) -> None:
        """An implicit login happened."""
        from ba._login import LoginAdapter

        with _ba.Context('ui'):
            self.login_adapters[login_type].set_implicit_login_state(
                LoginAdapter.ImplicitLoginState(
                    login_id=login_id, display_name=display_name
                )
            )

    def on_implicit_logout(self, login_type: LoginType) -> None:
        """An implicit logout happened."""
        with _ba.Context('ui'):
            self.login_adapters[login_type].set_implicit_login_state(None)

    def on_no_initial_primary_account(self) -> None:
        """Callback run if the app has no primary account after launch.

        Either this callback or on_primary_account_changed will be called
        within a few seconds of app launch; the app can move forward
        with the startup sequence at that point.
        """
        if not self._initial_login_completed:
            self._initial_login_completed = True
            _ba.app.on_initial_login_completed()

    def on_implicit_login_state_changed(
        self,
        login_type: LoginType,
        state: LoginAdapter.ImplicitLoginState | None,
    ) -> None:
        """Called when implicit login state changes.

        Logins that tend to sign themselves in/out in the background are
        considered implicit. We may choose to honor or ignore their states,
        allowing the user to opt for other login types even if the default
        implicit one can't be explicitly logged out or otherwise controlled.
        """
        assert _ba.in_logic_thread()

        # Store which (if any) adapter is currently implicitly signed in.
        if state is None:
            self._implicit_signed_in_adapter = None
        else:
            self._implicit_signed_in_adapter = self.login_adapters[login_type]

        # We may want to auto-sign-in based on this new state.
        self._update_auto_sign_in()

    def on_cloud_connectivity_changed(self, connected: bool) -> None:
        """Should be called with cloud connectivity changes."""
        del connected  # Unused.
        assert _ba.in_logic_thread()

        # We may want to auto-sign-in based on this new state.
        self._update_auto_sign_in()

    def _update_auto_sign_in(self) -> None:
        from ba._internal import get_v1_account_state

        # We attempt auto-sign-in only once.
        if self._auto_signed_in:
            return

        # If we're not currently signed in, we have connectivity, and
        # we have an available implicit adapter, do an auto-sign-in.
        connected = _ba.app.cloud.is_connected()
        signed_in_v1 = get_v1_account_state() == 'signed_in'
        signed_in_v2 = _ba.app.accounts_v2.have_primary_credentials()
        if (
            connected
            and not signed_in_v1
            and not signed_in_v2
            and self._implicit_signed_in_adapter is not None
        ):
            self._auto_signed_in = True
            self._implicit_signed_in_adapter.sign_in(self._on_sign_in_completed)

    def _on_sign_in_completed(
        self, result: LoginAdapter.SignInResult | Exception
    ) -> None:
        logging.debug('GOT SIGN-IN COMPLETED WITH %s', result)

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

        # Login types and their display-names associated with this account.
        self.logins: dict[LoginType, str] = {}

    def __enter__(self) -> None:
        """Support for "with" statement.

        This allows cloud messages to be sent on our behalf.
        """

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Any:
        """Support for "with" statement.

        This allows cloud messages to be sent on our behalf.
        """
