# Released under the MIT License. See LICENSE for details.
#
"""Account related functionality."""

from __future__ import annotations

import hashlib
import logging
from functools import partial
from typing import TYPE_CHECKING, assert_never

from efro.error import CommunicationError
from efro.call import CallbackSet
from bacommon.login import LoginType
import _babase

if TYPE_CHECKING:
    from typing import Any, Callable

    from babase._login import LoginAdapter, LoginInfo

logger = logging.getLogger('ba.accountv2')


class AccountV2Subsystem:
    """Subsystem for modern account handling in the app.

    Category: **App Classes**

    Access the single shared instance of this class at 'ba.app.plus.accounts'.
    """

    def __init__(self) -> None:
        assert _babase.in_logic_thread()

        from babase._login import LoginAdapterGPGS, LoginAdapterGameCenter

        # Register to be informed when connectivity changes.
        plus = _babase.app.plus
        self._connectivity_changed_cb = (
            None
            if plus is None
            else plus.cloud.on_connectivity_changed_callbacks.register(
                self._on_cloud_connectivity_changed
            )
        )

        # Whether or not everything related to an initial sign in (or
        # lack thereof) has completed. This includes things like
        # workspace syncing. Completion of this is what flips the app
        # into 'running' state.
        self._initial_sign_in_completed = False

        self._kicked_off_workspace_load = False

        self.login_adapters: dict[LoginType, LoginAdapter] = {}

        self._implicit_signed_in_adapter: LoginAdapter | None = None
        self._implicit_state_changed = False
        self._can_do_auto_sign_in = True
        self.on_primary_account_changed_callbacks: CallbackSet[
            Callable[[AccountV2Handle | None], None]
        ] = CallbackSet()

        adapter: LoginAdapter
        if _babase.using_google_play_game_services():
            adapter = LoginAdapterGPGS()
            self.login_adapters[adapter.login_type] = adapter
        if _babase.using_game_center():
            adapter = LoginAdapterGameCenter()
            self.login_adapters[adapter.login_type] = adapter

    def on_app_loading(self) -> None:
        """Should be called at standard on_app_loading time."""

        for adapter in self.login_adapters.values():
            adapter.on_app_loading()

    def have_primary_credentials(self) -> bool:
        """Are credentials currently set for the primary app account?

        Note that this does not mean these credentials have been checked
        for validity; only that they exist. If/when credentials are
        validated, the 'primary' account handle will be set.
        """
        raise NotImplementedError()

    @property
    def primary(self) -> AccountV2Handle | None:
        """The primary account for the app, or None if not logged in."""
        return self.do_get_primary()

    def on_primary_account_changed(
        self, account: AccountV2Handle | None
    ) -> None:
        """Callback run after the primary account changes.

        Will be called with None on log-outs and when new credentials
        are set but have not yet been verified.
        """
        assert _babase.in_logic_thread()

        # Fire any registered callbacks.
        for call in self.on_primary_account_changed_callbacks.getcalls():
            try:
                call(account)
            except Exception:
                logging.exception('Error in primary-account-changed callback.')

        # Currently don't do anything special on sign-outs.
        if account is None:
            return

        # If this new account has a workspace, update it and ask to be
        # informed when that process completes.
        if account.workspaceid is not None:
            assert account.workspacename is not None
            if (
                not self._initial_sign_in_completed
                and not self._kicked_off_workspace_load
            ):
                self._kicked_off_workspace_load = True
                _babase.app.workspaces.set_active_workspace(
                    account=account,
                    workspaceid=account.workspaceid,
                    workspacename=account.workspacename,
                    on_completed=self._on_set_active_workspace_completed,
                )
            else:
                # Don't activate workspaces if we've already told the
                # game that initial-log-in is done or if we've already
                # kicked off a workspace load.
                _babase.screenmessage(
                    f'\'{account.workspacename}\''
                    f' will be activated at next app launch.',
                    color=(1, 1, 0),
                )
                _babase.getsimplesound('error').play()
            return

        # Ok; no workspace to worry about; carry on.
        if not self._initial_sign_in_completed:
            self._initial_sign_in_completed = True
            _babase.app.on_initial_sign_in_complete()

    def on_active_logins_changed(self, logins: dict[LoginType, str]) -> None:
        """Should be called when logins for the active account change."""

        for adapter in self.login_adapters.values():
            adapter.set_active_logins(logins)

    def on_implicit_sign_in(
        self, login_type: LoginType, login_id: str, display_name: str
    ) -> None:
        """An implicit sign-in happened (called by native layer)."""
        from babase._login import LoginAdapter

        assert _babase.in_logic_thread()

        with _babase.ContextRef.empty():
            self.login_adapters[login_type].set_implicit_login_state(
                LoginAdapter.ImplicitLoginState(
                    login_id=login_id, display_name=display_name
                )
            )

    def on_implicit_sign_out(self, login_type: LoginType) -> None:
        """An implicit sign-out happened (called by native layer)."""
        assert _babase.in_logic_thread()
        with _babase.ContextRef.empty():
            self.login_adapters[login_type].set_implicit_login_state(None)

    def on_no_initial_primary_account(self) -> None:
        """Callback run if the app has no primary account after launch.

        Either this callback or on_primary_account_changed will be called
        within a few seconds of app launch; the app can move forward
        with the startup sequence at that point.
        """
        if not self._initial_sign_in_completed:
            self._initial_sign_in_completed = True
            _babase.app.on_initial_sign_in_complete()

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
        from babase._language import Lstr

        assert _babase.in_logic_thread()

        cfg = _babase.app.config
        cfgkey = 'ImplicitLoginStates'
        cfgdict = _babase.app.config.setdefault(cfgkey, {})

        # Store which (if any) adapter is currently implicitly signed
        # in. Making the assumption there will only ever be one implicit
        # adapter at a time; may need to revisit this logic if that
        # changes.
        prev_state = cfgdict.get(login_type.value)
        if state is None:
            self._implicit_signed_in_adapter = None
            new_state = cfgdict[login_type.value] = None
        else:
            self._implicit_signed_in_adapter = self.login_adapters[login_type]
            new_state = cfgdict[login_type.value] = self._hashstr(
                state.login_id
            )

            # Special case: if the user is already signed in but not
            # with this implicit login, let them know that the 'Welcome
            # back FOO' they likely just saw is not actually accurate.
            if (
                self.primary is not None
                and not self.login_adapters[login_type].is_back_end_active()
            ):
                service_str: Lstr | None
                if login_type is LoginType.GPGS:
                    service_str = Lstr(resource='googlePlayText')
                elif login_type is LoginType.GAME_CENTER:
                    # Note: Apparently Game Center is just called 'Game
                    # Center' in all languages. Can revisit if not true.
                    # https://developer.apple.com/forums/thread/725779
                    service_str = Lstr(value='Game Center')
                elif login_type is LoginType.EMAIL:
                    # Not possible; just here for exhaustive coverage.
                    service_str = None
                else:
                    assert_never(login_type)
                if service_str is not None:
                    _babase.apptimer(
                        2.0,
                        partial(
                            _babase.screenmessage,
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
            logger.debug(
                'Implicit state changed (%s -> %s);'
                ' will update app sign-in state accordingly.',
                prev_state,
                new_state,
            )
            self._implicit_state_changed = True

        # We may want to auto-sign-in based on this new state.
        self._update_auto_sign_in()

    def _on_cloud_connectivity_changed(self, connected: bool) -> None:
        """Should be called with cloud connectivity changes."""
        del connected  # Unused.
        assert _babase.in_logic_thread()

        # We may want to auto-sign-in based on this new state.
        self._update_auto_sign_in()

    def do_get_primary(self) -> AccountV2Handle | None:
        """Internal - should be overridden by subclass."""
        raise NotImplementedError()

    def set_primary_credentials(self, credentials: str | None) -> None:
        """Set credentials for the primary app account."""
        raise NotImplementedError()

    def _update_auto_sign_in(self) -> None:
        plus = _babase.app.plus
        assert plus is not None

        # If implicit state has changed, try to respond.
        if self._implicit_state_changed:
            if self._implicit_signed_in_adapter is None:
                # If implicit back-end has signed out, we follow suit
                # immediately; no need to wait for network connectivity.
                logger.debug(
                    'Signing out as result of implicit state change...',
                )
                plus.accounts.set_primary_credentials(None)
                self._implicit_state_changed = False

                # Once we've made a move here we don't want to
                # do any more automatic stuff.
                self._can_do_auto_sign_in = False

            else:
                # Ok; we've got a new implicit state. If we've got
                # connectivity, let's attempt to sign in with it.
                # Consider this an 'explicit' sign in because the
                # implicit-login state change presumably was triggered
                # by some user action (signing in, signing out, or
                # switching accounts via the back-end). NOTE: should
                # test case where we don't have connectivity here.
                if plus.cloud.is_connected():
                    logger.debug(
                        'Signing in as result of implicit state change...',
                    )
                    self._implicit_signed_in_adapter.sign_in(
                        self._on_explicit_sign_in_completed,
                        description='implicit state change',
                    )
                    self._implicit_state_changed = False

                    # Once we've made a move here we don't want to
                    # do any more automatic stuff.
                    self._can_do_auto_sign_in = False

        if not self._can_do_auto_sign_in:
            return

        # If we're not currently signed in, we have connectivity, and
        # we have an available implicit login, auto-sign-in with it once.
        # The implicit-state-change logic above should keep things
        # mostly in-sync, but that might not always be the case due to
        # connectivity or other issues. We prefer to keep people signed
        # in as a rule, even if there are corner cases where this might
        # not be what they want (A user signing out and then restarting
        # may be auto-signed back in).
        connected = plus.cloud.is_connected()
        signed_in_v1 = plus.get_v1_account_state() == 'signed_in'
        signed_in_v2 = plus.accounts.have_primary_credentials()
        if (
            connected
            and not signed_in_v1
            and not signed_in_v2
            and self._implicit_signed_in_adapter is not None
        ):
            logger.debug(
                'Signing in due to on-launch-auto-sign-in...',
            )
            self._can_do_auto_sign_in = False  # Only ATTEMPT once
            self._implicit_signed_in_adapter.sign_in(
                self._on_implicit_sign_in_completed, description='auto-sign-in'
            )

    def _on_explicit_sign_in_completed(
        self,
        adapter: LoginAdapter,
        result: LoginAdapter.SignInResult | Exception,
    ) -> None:
        """A sign-in has completed that the user asked for explicitly."""
        from babase._language import Lstr

        del adapter  # Unused.

        plus = _babase.app.plus
        assert plus is not None

        # Make some noise on errors since the user knows a
        # sign-in attempt is happening in this case (the 'explicit' part).
        if isinstance(result, Exception):
            # We expect the occasional communication errors;
            # Log a full exception for anything else though.
            if not isinstance(result, CommunicationError):
                logging.warning(
                    'Error on explicit accountv2 sign in attempt.',
                    exc_info=result,
                )

            # For now just show 'error'. Should do better than this.
            _babase.screenmessage(
                Lstr(resource='internal.signInErrorText'),
                color=(1, 0, 0),
            )
            _babase.getsimplesound('error').play()

            # Also I suppose we should sign them out in this case since
            # it could be misleading to be still signed in with the old
            # account.
            plus.accounts.set_primary_credentials(None)
            return

        plus.accounts.set_primary_credentials(result.credentials)

    def _on_implicit_sign_in_completed(
        self,
        adapter: LoginAdapter,
        result: LoginAdapter.SignInResult | Exception,
    ) -> None:
        """A sign-in has completed that the user didn't ask for explicitly."""
        plus = _babase.app.plus
        assert plus is not None

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
        connected = plus.cloud.is_connected()
        signed_in_v1 = plus.get_v1_account_state() == 'signed_in'
        signed_in_v2 = plus.accounts.have_primary_credentials()
        if connected and not signed_in_v1 and not signed_in_v2:
            plus.accounts.set_primary_credentials(result.credentials)

    def _on_set_active_workspace_completed(self) -> None:
        if not self._initial_sign_in_completed:
            self._initial_sign_in_completed = True
            _babase.app.on_initial_sign_in_complete()


class AccountV2Handle:
    """Handle for interacting with a V2 account.

    This class supports the 'with' statement, which is how it is
    used with some operations such as cloud messaging.
    """

    accountid: str
    tag: str
    workspacename: str | None
    workspaceid: str | None
    logins: dict[LoginType, LoginInfo]

    def __enter__(self) -> None:
        """Support for "with" statement.

        This allows cloud messages to be sent on our behalf.
        """

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Any:
        """Support for "with" statement.

        This allows cloud messages to be sent on our behalf.
        """
