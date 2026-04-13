# Released under the MIT License. See LICENSE for details.
#
"""Login related functionality."""

from __future__ import annotations

import time
import logging
from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, final, override

from bacommon.login import LoginType

from babase._logging import loginadapterlog
import _babase

if TYPE_CHECKING:
    from typing import Callable


@dataclass
class LoginInfo:
    """Info for a login used by :class:`~babase.AccountV2Handle`."""

    name: str


class LoginAdapter:
    """Allows using implicit login types in an explicit way.

    Some login types such as Google Play Game Services or Game Center
    are basically always present and often do not provide a way to log
    out from within a running app, so this adapter exists to use them in
    a flexible manner by 'attaching to' and 'detaching from' an
    always-present login, allowing for its use alongside other login
    types. It also provides common functionality for server-side account
    verification and other handy bits.
    """

    @dataclass
    class SignInResult:
        """Describes the final result of a sign-in attempt."""

        credentials: str

    @dataclass
    class ImplicitLoginState:
        """Describes the current state of an implicit login."""

        login_id: str
        display_name: str

    def __init__(self, login_type: LoginType):
        assert _babase.in_logic_thread()
        self.login_type = login_type
        self._implicit_login_state: LoginAdapter.ImplicitLoginState | None = (
            None
        )
        self._on_app_loading_called = False
        self._implicit_login_state_dirty = False
        self._back_end_active = False

        # Which login of our type (if any) is associated with the
        # current active primary account.
        self._active_login_id: str | None = None

        self._last_sign_in_time: float | None = None
        self._last_sign_in_desc: str | None = None

    def on_app_loading(self) -> None:
        """Should be called for each adapter in on_app_loading.

        :meta private:
        """

        assert not self._on_app_loading_called
        self._on_app_loading_called = True

        # Any implicit state we received up until now needs to be pushed
        # to the app account subsystem.
        self._update_implicit_login_state()

    def set_implicit_login_state(
        self, state: ImplicitLoginState | None
    ) -> None:
        """Keep the adapter informed of implicit login states.

        This should be called by the adapter back-end when an account
        of their associated type gets logged in or out.
        """
        assert _babase.in_logic_thread()

        # Ignore redundant sets.
        if state == self._implicit_login_state:
            return

        if state is None:
            loginadapterlog.debug(
                '%s implicit state changed; now signed out.',
                self.login_type.name,
            )
        else:
            loginadapterlog.debug(
                '%s implicit state changed; now signed in as %s.',
                self.login_type.name,
                state.display_name,
            )

        self._implicit_login_state = state
        self._implicit_login_state_dirty = True

        # (possibly) push it to the app for handling.
        self._update_implicit_login_state()

        # This might affect whether we consider that back-end as 'active'.
        self._update_back_end_active()

    def set_active_logins(self, logins: dict[LoginType, str]) -> None:
        """Keep the adapter informed of actively used logins.

        This should be called by the app's account subsystem to
        keep adapters up to date on the full set of logins attached
        to the currently-in-use account.
        Note that the logins dict passed in should be immutable as
        only a reference to it is stored, not a copy.

        :meta private:
        """
        assert _babase.in_logic_thread()
        loginadapterlog.debug(
            '%s adapter got active logins %s.',
            self.login_type.name,
            {k: v[:4] + '...' + v[-4:] for k, v in logins.items()},
        )

        self._active_login_id = logins.get(self.login_type)
        self._update_back_end_active()

    def on_back_end_active_change(self, active: bool) -> None:
        """Called when active state for the back-end is (possibly) changing.

        Meant to be overridden by subclasses. Being active means that
        the implicit login provided by the back-end is actually being
        used by the app. It should therefore register unlocked
        achievements, leaderboard scores, allow viewing native UIs, etc.
        When not active it should ignore everything and behave as if
        signed out, even if it technically is still signed in.
        """
        assert _babase.in_logic_thread()
        del active  # Unused.

    @final
    def sign_in(
        self,
        result_cb: Callable[[LoginAdapter, SignInResult | Exception], None],
        description: str,
    ) -> None:
        """Attempt to sign in via this adapter.

        This can be called even if the back-end is not implicitly signed in;
        the adapter will attempt to sign in if possible. An exception will
        be passed to the callback if the sign-in attempt fails.
        """

        assert _babase.in_logic_thread()

        # Have been seeing multiple sign-in attempts come through
        # nearly simultaneously which can be problematic server-side.
        # Let's error if a sign-in attempt is made within a few seconds
        # of the last one to try and address this.
        now = time.monotonic()
        appnow = _babase.apptime()
        if self._last_sign_in_time is not None:
            since_last = now - self._last_sign_in_time
            if since_last < 1.0:
                logging.warning(
                    'LoginAdapter: %s adapter sign_in() called too soon'
                    ' (%.2fs) after last; this-desc="%s", last-desc="%s",'
                    ' ba-app-time=%.2f.',
                    self.login_type.name,
                    since_last,
                    description,
                    self._last_sign_in_desc,
                    appnow,
                )
                _babase.pushcall(
                    partial(
                        result_cb,
                        self,
                        RuntimeError('sign_in called too soon after last.'),
                    )
                )
                return

        self._last_sign_in_desc = description
        self._last_sign_in_time = now

        loginadapterlog.debug(
            '%s adapter sign_in() called; fetching sign-in-token...',
            self.login_type.name,
        )

        def _got_sign_in_token_result(result: str | None) -> None:
            import bacommon.cloud

            # Failed to get a sign-in-token.
            if result is None:
                loginadapterlog.debug(
                    '%s adapter sign-in-token fetch failed;'
                    ' aborting sign-in.',
                    self.login_type.name,
                )
                _babase.pushcall(
                    partial(
                        result_cb,
                        self,
                        RuntimeError('fetch-sign-in-token failed.'),
                    )
                )
                return

            # Got a sign-in token! Now pass it to the cloud which will use
            # it to verify our identity and give us app credentials on
            # success.
            loginadapterlog.debug(
                '%s adapter sign-in-token fetch succeeded;'
                ' passing to cloud for verification...',
                self.login_type.name,
            )

            def _got_sign_in_response(
                response: bacommon.cloud.SignInResponse | Exception,
            ) -> None:
                # This likely means we couldn't communicate with the server.
                if isinstance(response, Exception):
                    loginadapterlog.debug(
                        '%s adapter got error sign-in response: %s',
                        self.login_type.name,
                        response,
                    )
                    _babase.pushcall(partial(result_cb, self, response))
                else:
                    # This means our credentials were explicitly rejected.
                    if response.credentials is None:
                        result2: LoginAdapter.SignInResult | Exception = (
                            RuntimeError('Sign-in-token was rejected.')
                        )
                    else:
                        loginadapterlog.debug(
                            '%s adapter got successful sign-in response',
                            self.login_type.name,
                        )
                        result2 = self.SignInResult(
                            credentials=response.credentials
                        )
                    _babase.pushcall(partial(result_cb, self, result2))

            assert _babase.app.plus is not None
            _babase.app.plus.cloud.send_message_cb(
                bacommon.cloud.SignInMessage(
                    self.login_type,
                    result,
                    description=description,
                    apptime=appnow,
                ),
                on_response=_got_sign_in_response,
            )

        # Kick off the sign-in process by fetching a sign-in token.
        self.get_sign_in_token(completion_cb=_got_sign_in_token_result)

    def is_back_end_active(self) -> bool:
        """Is this adapter's back-end currently active?"""
        return self._back_end_active

    def get_sign_in_token(
        self, completion_cb: Callable[[str | None], None]
    ) -> None:
        """Get a sign-in token from the adapter back end.

        This token is then passed to the cloud to complete the sign-in
        process. The adapter can use this opportunity to bring up
        account creation UI, call its internal sign-in function, etc. as
        needed. The provided ``completion_cb`` should then be called
        with either a token or with ``None`` if sign in failed or was
        cancelled.
        """

        # Default implementation simply fails immediately.
        _babase.pushcall(partial(completion_cb, None))

    def _update_implicit_login_state(self) -> None:
        # If we've received an implicit login state, schedule it to be
        # sent along to the app. We wait until on-app-loading has been
        # called so that account-client-v2 has had a chance to load
        # any existing state so it can properly respond to this.
        if self._implicit_login_state_dirty and self._on_app_loading_called:

            loginadapterlog.debug(
                '%s adapter sending implicit-state-changed to app.',
                self.login_type.name,
            )

            assert _babase.app.plus is not None
            _babase.pushcall(
                partial(
                    _babase.app.plus.accounts.on_implicit_login_state_changed,
                    self.login_type,
                    self._implicit_login_state,
                )
            )
            self._implicit_login_state_dirty = False

    def _update_back_end_active(self) -> None:
        was_active = self._back_end_active
        if self._implicit_login_state is None:
            is_active = False
        else:
            is_active = (
                self._implicit_login_state.login_id == self._active_login_id
            )
        if was_active != is_active:
            loginadapterlog.debug(
                '%s adapter back-end-active is now %s.',
                self.login_type.name,
                is_active,
            )
            self.on_back_end_active_change(is_active)
            self._back_end_active = is_active


class LoginAdapterNative(LoginAdapter):
    """A login adapter that does its work in the native layer."""

    def __init__(self, login_type: LoginType) -> None:
        super().__init__(login_type)

        # Store int ids for in-flight attempts since they may go through
        # various platform layers and back.
        self._sign_in_attempt_num = 123
        self._sign_in_attempts: dict[int, Callable[[str | None], None]] = {}

    @override
    def get_sign_in_token(
        self, completion_cb: Callable[[str | None], None]
    ) -> None:
        attempt_id = self._sign_in_attempt_num
        self._sign_in_attempts[attempt_id] = completion_cb
        self._sign_in_attempt_num += 1
        _babase.login_adapter_get_sign_in_token(
            self.login_type.value, attempt_id
        )

    @override
    def on_back_end_active_change(self, active: bool) -> None:
        _babase.login_adapter_back_end_active_change(
            self.login_type.value, active
        )

    def on_sign_in_complete(self, attempt_id: int, result: str | None) -> None:
        """Called by the native layer on a completed attempt."""
        assert _babase.in_logic_thread()
        if attempt_id not in self._sign_in_attempts:
            logging.exception('sign-in attempt_id %d not found', attempt_id)
            return
        callback = self._sign_in_attempts.pop(attempt_id)
        callback(result)


class LoginAdapterGPGS(LoginAdapterNative):
    """Google Play Game Services adapter."""

    def __init__(self) -> None:
        super().__init__(LoginType.GPGS)


class LoginAdapterGameCenter(LoginAdapterNative):
    """Apple Game Center adapter."""

    def __init__(self) -> None:
        super().__init__(LoginType.GAME_CENTER)
