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
    """Adapts a platform-implicit login so it can be used explicitly.

    For login types like Google Play Game Services and Game Center, the
    user is silently/implicitly signed in at the platform level and
    typically has no in-app way to sign out. This adapter tracks the
    current implicit state, lets the app 'attach to' or 'detach from' it,
    and exposes an explicit :meth:`sign_in` call that produces V2
    credentials.

    Login types with no implicit platform state (e.g. Discord, email)
    don't use this class — they run their own explicit flows.
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

        too_soon = _check_sign_in_rate_limit(
            f'LoginAdapter: {self.login_type.name} adapter',
            self._last_sign_in_time,
            self._last_sign_in_desc,
            description,
        )
        if too_soon is not None:
            _babase.pushcall(partial(result_cb, self, too_soon))
            return

        self._last_sign_in_desc = description
        self._last_sign_in_time = time.monotonic()

        loginadapterlog.debug(
            '%s adapter sign_in() called; fetching sign-in-token...',
            self.login_type.name,
        )

        def _on_credentials(credentials: str | Exception) -> None:
            if isinstance(credentials, Exception):
                result: LoginAdapter.SignInResult | Exception = credentials
            else:
                result = self.SignInResult(credentials=credentials)
            _babase.pushcall(partial(result_cb, self, result))

        def _on_token(token: str | None) -> None:
            if token is None:
                loginadapterlog.debug(
                    '%s adapter sign-in-token fetch failed;'
                    ' aborting sign-in.',
                    self.login_type.name,
                )
                _on_credentials(RuntimeError('fetch-sign-in-token failed.'))
                return
            loginadapterlog.debug(
                '%s adapter sign-in-token fetch succeeded;'
                ' passing to cloud for verification...',
                self.login_type.name,
            )
            exchange_sign_in_token(
                login_type=self.login_type,
                token=token,
                description=description,
                on_result=_on_credentials,
            )

        # Kick off the sign-in process by fetching a sign-in token.
        self.get_sign_in_token(completion_cb=_on_token)

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


# -- Shared explicit-sign-in helpers -----------------------------------

# Rate-limit state for explicit flows (Discord, email-proxy, etc.)
# that don't have their own adapter instance. Keyed on a caller-supplied
# bucket string.
_last_explicit_sign_in_time: dict[str, float] = {}
_last_explicit_sign_in_desc: dict[str, str] = {}


def _check_sign_in_rate_limit(
    subject: str,
    last_time: float | None,
    last_desc: str | None,
    description: str,
) -> RuntimeError | None:
    """Return an exception if a sign-in is happening too soon; else None.

    Multiple sign-in attempts within a short window can be problematic
    server-side, so both :class:`LoginAdapter` and the free
    :func:`discord_sign_in` flow gate on this.
    """
    if last_time is None:
        return None
    now = time.monotonic()
    since_last = now - last_time
    if since_last >= 1.0:
        return None
    logging.warning(
        '%s sign_in() called too soon (%.2fs) after last;'
        ' this-desc="%s", last-desc="%s", ba-app-time=%.2f.',
        subject,
        since_last,
        description,
        last_desc,
        _babase.apptime(),
    )
    return RuntimeError('sign_in called too soon after last.')


def exchange_sign_in_token(
    login_type: LoginType,
    token: str,
    description: str,
    on_result: Callable[[str | Exception], None],
) -> None:
    """Exchange a platform-specific sign-in token for V2 credentials.

    Sends a ``SignInMessage`` to the cloud and invokes ``on_result`` on
    the logic thread with the returned credentials string, or with an
    ``Exception`` if the cloud rejects the token or can't be reached.

    Shared by :class:`LoginAdapter` and by explicit flows that don't
    have an adapter (Discord).
    """
    import bacommon.cloud

    assert _babase.in_logic_thread()

    def _on_response(
        response: bacommon.cloud.SignInResponse | Exception,
    ) -> None:
        if isinstance(response, Exception):
            loginadapterlog.debug(
                '%s got error sign-in response: %s',
                login_type.name,
                response,
            )
            _babase.pushcall(partial(on_result, response))
        elif response.credentials is None:
            _babase.pushcall(
                partial(on_result, RuntimeError('Sign-in-token was rejected.'))
            )
        else:
            loginadapterlog.debug(
                '%s got successful sign-in response',
                login_type.name,
            )
            _babase.pushcall(partial(on_result, response.credentials))

    assert _babase.app.plus is not None
    _babase.app.plus.cloud.send_message_cb(
        bacommon.cloud.SignInMessage(
            login_type,
            token,
            description=description,
            apptime=_babase.apptime(),
        ),
        on_response=_on_response,
    )


# -- Discord explicit-sign-in flow -------------------------------------

# Pending sign-in attempts keyed on attempt_id. Native layer sends
# attempt_id back with the OAuth token via the
# discord_sign_in_token_response hook.
_discord_sign_in_attempts: dict[int, Callable[[str | None], None]] = {}
_g_discord_sign_in_attempt_num = 1


def discord_sign_in(
    result_cb: Callable[[str | Exception], None],
    description: str,
) -> None:
    """Run the Discord OAuth sign-in flow and return V2 credentials.

    Kicks off the native OAuth flow (browser-based), exchanges the
    resulting token with the cloud for V2 credentials, and invokes
    ``result_cb`` on the logic thread with a credentials string on
    success or with an ``Exception`` on any failure.

    Discord has no implicit/background sign-in on any platform, so it
    doesn't use :class:`LoginAdapter`. This mirrors the email/V2-proxy
    flow in structure: an explicit credential-producing flow that drops
    directly into ``set_primary_credentials``.
    """
    global _g_discord_sign_in_attempt_num  # pylint: disable=global-statement

    assert _babase.in_logic_thread()

    too_soon = _check_sign_in_rate_limit(
        'discord_sign_in',
        _last_explicit_sign_in_time.get('discord'),
        _last_explicit_sign_in_desc.get('discord'),
        description,
    )
    if too_soon is not None:
        _babase.pushcall(partial(result_cb, too_soon))
        return

    _last_explicit_sign_in_time['discord'] = time.monotonic()
    _last_explicit_sign_in_desc['discord'] = description

    loginadapterlog.debug('discord_sign_in() called; fetching sign-in-token...')

    def _on_token(token: str | None) -> None:
        if token is None:
            loginadapterlog.debug(
                'discord sign-in-token fetch failed; aborting sign-in.'
            )
            _babase.pushcall(
                partial(result_cb, RuntimeError('fetch-sign-in-token failed.'))
            )
            return
        loginadapterlog.debug(
            'discord sign-in-token fetch succeeded;'
            ' passing to cloud for verification...'
        )
        exchange_sign_in_token(
            login_type=LoginType.DISCORD,
            token=token,
            description=description,
            on_result=result_cb,
        )

    attempt_id = _g_discord_sign_in_attempt_num
    _g_discord_sign_in_attempt_num += 1
    _discord_sign_in_attempts[attempt_id] = _on_token
    _babase.discord_request_sign_in_token(attempt_id)


def on_discord_sign_in_token_response(
    attempt_id: int, result: str | None
) -> None:
    """Called by the native layer when a Discord sign-in attempt finishes.

    :meta private:
    """
    assert _babase.in_logic_thread()
    callback = _discord_sign_in_attempts.pop(attempt_id, None)
    if callback is None:
        logging.exception('discord sign-in attempt_id %d not found', attempt_id)
        return
    callback(result)
