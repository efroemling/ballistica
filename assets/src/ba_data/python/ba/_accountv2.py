# Released under the MIT License. See LICENSE for details.
#
"""Account related functionality."""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING

from efro.call import tpartial
from efro.error import CommunicationError
from bacommon.login import LoginType
import _ba

if TYPE_CHECKING:
    from typing import Any

    from ba._login import LoginAdapter


DEBUG_LOG = False


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

        self.login_adapters: dict[LoginType, LoginAdapter] = {}

        self._implicit_signed_in_adapter: LoginAdapter | None = None
        self._implicit_state_changed = False
        self._can_do_auto_sign_in = True

        if _ba.app.platform == 'android' and _ba.app.subplatform == 'google':
            from ba._login import LoginAdapterGPGS

            self.login_adapters[LoginType.GPGS] = LoginAdapterGPGS()

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

    def on_implicit_sign_in(
        self, login_type: LoginType, login_id: str, display_name: str
    ) -> None:
        """An implicit sign-in happened (called by native layer)."""
        from ba._login import LoginAdapter

        with _ba.Context('ui'):
            self.login_adapters[login_type].set_implicit_login_state(
                LoginAdapter.ImplicitLoginState(
                    login_id=login_id, display_name=display_name
                )
            )

    def on_implicit_sign_out(self, login_type: LoginType) -> None:
        """An implicit sign-out happened (called by native layer)."""
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

    @staticmethod
    def _hashstr(val: str) -> str:
        md5 = hashlib.md5()
        md5.update(val.encode())
        return md5.hexdigest()

    def on_implicit_login_state_changed(
        self,
        login_type: LoginType,
        state: LoginAdapter.ImplicitLoginState | None,
    ) -> None:
        """Called when implicit login state changes.

        Login systems that tend to sign themselves in/out in the
        background are considered implicit. We may choose to honor or
        ignore their states, allowing the user to opt for other login
        types even if the default implicit one can't be explicitly
        logged out or otherwise controlled.
        """
        from ba._language import Lstr

        assert _ba.in_logic_thread()

        cfg = _ba.app.config
        cfgkey = 'ImplicitLoginStates'
        cfgdict = _ba.app.config.setdefault(cfgkey, {})

        # Store which (if any) adapter is currently implicitly signed in.
        # Making the assumption there will only ever be one implicit
        # adapter at a time; may need to update this if that changes.
        prev_state = cfgdict.get(login_type.value)
        if state is None:
            self._implicit_signed_in_adapter = None
            new_state = cfgdict[login_type.value] = None
        else:
            self._implicit_signed_in_adapter = self.login_adapters[login_type]
            new_state = cfgdict[login_type.value] = self._hashstr(
                state.login_id
            )

            # Special case: if the user is already signed in but not with
            # this implicit login, we may want to let them know that the
            # 'Welcome back FOO' they likely just saw is not actually
            # accurate.
            if (
                self.primary is not None
                and not self.login_adapters[login_type].is_back_end_active()
            ):
                if login_type is LoginType.GPGS:
                    service_str = Lstr(resource='googlePlayText')
                else:
                    service_str = None
                if service_str is not None:
                    _ba.timer(
                        2.0,
                        tpartial(
                            _ba.screenmessage,
                            Lstr(
                                resource='notUsingAccountText',
                                subs=[
                                    ('${ACCOUNT}', state.display_name),
                                    ('${SERVICE}', service_str),
                                ],
                            ),
                            (1, 0.5, 0),
                        ),
                    )

        cfg.commit()

        # We want to respond any time the implicit state changes;
        # generally this means the user has explicitly signed in/out or
        # switched accounts within that back-end.
        if prev_state != new_state:
            if DEBUG_LOG:
                logging.debug(
                    'AccountV2: Implicit state changed (%s -> %s);'
                    ' will update app sign-in state accordingly.',
                    prev_state,
                    new_state,
                )
            self._implicit_state_changed = True

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

        # If implicit state has changed, try to respond.
        if self._implicit_state_changed:
            if self._implicit_signed_in_adapter is None:
                # If implicit back-end is signed out, follow suit
                # immediately; no need to wait for network connectivity.
                if DEBUG_LOG:
                    logging.debug(
                        'AccountV2: Signing out as result'
                        ' of implicit state change...',
                    )
                _ba.app.accounts_v2.set_primary_credentials(None)
                self._implicit_state_changed = False

                # Once we've made a move here we don't want to
                # do any more automatic ones.
                self._can_do_auto_sign_in = False

            else:
                # Ok; we've got a new implicit state. If we've got
                # connectivity, let's attempt to sign in with it.
                # Consider this an 'explicit' sign in because the
                # implicit-login state change presumably was triggered
                # by some user action (signing in, signing out, or
                # switching accounts via the back-end).
                # NOTE: should test case where we don't have
                # connectivity here.
                if _ba.app.cloud.is_connected():
                    if DEBUG_LOG:
                        logging.debug(
                            'AccountV2: Signing in as result'
                            ' of implicit state change...',
                        )
                    self._implicit_signed_in_adapter.sign_in(
                        self._on_explicit_sign_in_completed
                    )
                    self._implicit_state_changed = False

                    # Once we've made a move here we don't want to
                    # do any more automatic ones.
                    self._can_do_auto_sign_in = False

        if not self._can_do_auto_sign_in:
            return

        # If we're not currently signed in, we have connectivity, and
        # we have an available implicit login, auto-sign-in with it.
        # The implicit-state-change logic above should keep things
        # mostly in-sync, but due to connectivity or other issues that
        # might not always be the case. We prefer to keep people signed
        # in as a rule, even if there are corner cases where this might
        # not be what they want (A user signing out and then restarting
        # may be auto-signed back in).
        connected = _ba.app.cloud.is_connected()
        signed_in_v1 = get_v1_account_state() == 'signed_in'
        signed_in_v2 = _ba.app.accounts_v2.have_primary_credentials()
        if (
            connected
            and not signed_in_v1
            and not signed_in_v2
            and self._implicit_signed_in_adapter is not None
        ):
            if DEBUG_LOG:
                logging.debug(
                    'AccountV2: Signing in due to on-launch-auto-sign-in...',
                )
            self._can_do_auto_sign_in = False  # Only ATTEMPT once
            self._implicit_signed_in_adapter.sign_in(
                self._on_implicit_sign_in_completed
            )

    def _on_explicit_sign_in_completed(
        self,
        adapter: LoginAdapter,
        result: LoginAdapter.SignInResult | Exception,
    ) -> None:
        """A sign-in has completed that the user asked for explicitly."""
        from ba._language import Lstr

        del adapter  # Unused.

        # Make some noise on errors since the user knows
        # a sign-in attempt is happening in this case.
        if isinstance(result, Exception):
            # We expect the occasional communication errors;
            # Log a full exception for anything else though.
            if not isinstance(result, CommunicationError):
                logging.warning(
                    'Error on explicit accountv2 sign in attempt.',
                    exc_info=result,
                )
            with _ba.Context('ui'):
                _ba.screenmessage(
                    Lstr(resource='internal.signInErrorText'),
                    color=(1, 0, 0),
                )
                _ba.playsound(_ba.getsound('error'))

            # Also I suppose we should sign them out in this case since
            # it could be misleading to be still signed in with the old
            # account.
            _ba.app.accounts_v2.set_primary_credentials(None)
            return

        _ba.app.accounts_v2.set_primary_credentials(result.credentials)

    def _on_implicit_sign_in_completed(
        self,
        adapter: LoginAdapter,
        result: LoginAdapter.SignInResult | Exception,
    ) -> None:
        """A sign-in has completed that the user didn't ask for explicitly."""
        from ba._internal import get_v1_account_state

        del adapter  # Unused.

        # Log errors but don't inform the user; they're not aware of this
        # attempt and ignorance is bliss.
        if isinstance(result, Exception):
            # We expect the occasional communication errors;
            # Log a full exception for anything else though.
            if not isinstance(result, CommunicationError):
                logging.warning(
                    'Error on implicit accountv2 sign in attempt.',
                    exc_info=result,
                )
            return

        # If we're still connected and still not signed in,
        # plug in the credentials we got. We want to be extra cautious
        # in case the user has since explicitly signed in since we
        # kicked off.
        connected = _ba.app.cloud.is_connected()
        signed_in_v1 = get_v1_account_state() == 'signed_in'
        signed_in_v2 = _ba.app.accounts_v2.have_primary_credentials()
        if connected and not signed_in_v1 and not signed_in_v2:
            _ba.app.accounts_v2.set_primary_credentials(result.credentials)

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
