# Released under the MIT License. See LICENSE for details.
#
"""Provides ConstructAppMode."""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import TYPE_CHECKING, override

import _babase
from bacommon.app import ExitCode
from babase._appmode import AppMode
from babase._logging import assetmanagerlog as logger
from babase._assetsubsystem import (
    AssetAuthRequiredError,
    AssetAccessDeniedError,
)

if TYPE_CHECKING:
    from babase import AppIntent
    from babase._assetsubsystem import AssetSubsystem


#: How long to wait for auto-sign-in to establish a primary account
#: before giving up (after a resolve reports authentication is needed).
_SIGN_IN_WAIT_SECONDS = 15.0

#: After sign-in, how long to keep retrying a resolve that still reports
#: AUTH_REQUIRED — i.e. wait for the account's session channel to finish
#: registering + verifying on the connected node (a round-trip that lags
#: the local primary-account establishment).
_ACCOUNT_CHANNEL_WAIT_SECONDS = 10.0


class _ResolveOutcome(Enum):
    """Result of one construct-mode resolve attempt."""

    SUCCESS = 'success'
    #: Server needs an authenticated account (recoverable: sign in + retry).
    AUTH_REQUIRED = 'auth_required'
    #: Failed; a user-facing message was already shown.
    FAILED = 'failed'


def _primary_signed_in() -> bool:
    """Is a primary (v2) account currently established?

    A function (re-evaluated on each call) rather than an inline
    ``accounts.primary is not None`` so a polling loop can re-check it —
    inline checks let the type-checker assume the value never changes.
    """
    plus = _babase.app.plus
    return plus is not None and plus.accounts.primary is not None


class ConstructAppMode(AppMode):
    """The app's asset-bring-up mode (``app.assets``-driven).

    Construct-mode is the machinery that gets the app from native
    bootstrapping to a real, intent-handling app-mode (classic, etc.). It
    *constructs* the running app out of its asset packages: it makes the
    required asset-package set available — pulling any not-yet-local
    packages from the connected node — and only then releases control to
    the app-mode that actually handles the launch intent.

    It is **not** an intent handler and is never returned by the
    :class:`~babase.AppModeSelector`. The app enters it directly at boot
    (see ``App._enter_construct_mode``), and it hands off by dispatching
    the deferred initial intent through the normal selector once bring-up
    succeeds.

    :meta private:
    """

    def __init__(self, deferred_intent: AppIntent | None = None) -> None:
        super().__init__()

        # The launch intent we captured at boot and will release to the
        # real app-mode once bring-up completes.
        self._deferred_intent = deferred_intent

        # Whether we've faded the screen up from the boot black-out. We
        # only do this when bring-up actually has work to show (downloads
        # / an error); a clean no-download boot passes straight through
        # and lets the real app-mode drive the fade-in.
        self._faded_in = False

    @override
    @classmethod
    def can_handle_intent(cls, intent: AppIntent) -> bool:
        # We are never selected to handle intents; we're entered directly
        # as the boot-time bring-up gate.
        return False

    @override
    def handle_intent(self, intent: AppIntent) -> None:
        # Should be unreachable: we're not in the mode-selector, so the
        # intent machinery never routes anything to us.
        raise RuntimeError('ConstructAppMode does not handle intents.')

    @override
    def on_activate(self) -> None:
        # Bring-up runs as an async task on the logic thread's event loop;
        # the hand-off to the real app-mode happens once it completes.
        # (Server-mode start and other stdin commands wait safely until the
        # real app-mode activates — construct-mode does not trip the
        # initial-app-mode signal that starts the stdin console; see
        # App._note_app_mode_activated.)
        _babase.app.create_async_task(
            self._bring_up(), name='construct-mode bring-up'
        )

    async def _bring_up(self) -> None:
        """Make required assets available, then hand off to the real mode.

        Resolves the full set of asset-packages the meta-scan discovered
        across all scripts (``# ba_meta require asset-package`` directives,
        surfaced as ``app.meta.scanresults.asset_packages``) — pulling any
        not-yet-local packages from the connected node — and only hands off
        to the real app-mode if every one succeeds. On failure we stay in
        construct-mode (the gate) rather than enter a mode whose assets
        aren't ready.

        The builtin/projectconfig package is already registered before this
        mode (so our own UI assets exist); re-resolving it here is a cheap
        no-op (bundled → offline) that keeps this loop uniform.

        Flow (per the asset-packages design):

        * Attempt the resolve immediately (without waiting for sign-in, so
          the public-package path isn't gated on it). A fully-local set
          (the common bundled-assets boot) resolves in one off-thread pass
          with the screen left untouched — the real app-mode drives the
          fade-in.
        * If a real download is needed, :meth:`_on_download_starting` fires
          (fade in + ``Loading assets…``). If the server then reports
          authentication is needed, show ``Authenticating…``, wait for
          auto-sign-in, then retry. Failures surface a screenmessage and we
          stay put.
        """
        scanresults = _babase.app.meta.scanresults
        required = (
            list(scanresults.asset_packages) if scanresults is not None else []
        )
        assets = _babase.app.assets

        if not required:
            logger.debug('Construct-mode: no asset-packages required.')
            self._hand_off()
            return

        logger.info(
            'Construct-mode resolving %d asset-package(s): %s',
            len(required),
            ', '.join(required),
        )

        # Attempt the resolve immediately, with whatever account state
        # exists this early (typically none — we don't pre-wait for sign-in,
        # so the public-package path isn't gated on it). A fully-local set
        # passes straight through; a real download triggers
        # _on_download_starting (fade + 'Loading assets…').
        outcome = await self._attempt(assets, required, auth_recoverable=True)

        if outcome is _ResolveOutcome.AUTH_REQUIRED:
            # Wait for auto-sign-in to settle, then retry.
            logger.info(
                'Construct-mode: resolve needs authentication;'
                ' waiting for sign-in.'
            )
            self._screenmessage('Authenticating…')
            if not await self._wait_for_sign_in():
                self._fail(
                    'You must sign in to load these assets. Remove these'
                    ' mods/changes so you can sign in and then try again.'
                )
                return
            outcome = await self._resolve_signed_in(assets, required)

        if outcome is _ResolveOutcome.SUCCESS:
            self._hand_off()
        # Else: _attempt already surfaced the failure message; stay put.

    async def _resolve_signed_in(
        self, assets: AssetSubsystem, required: list[str]
    ) -> _ResolveOutcome:
        """Resolve now that we're signed in, tolerating account-channel lag.

        Signing in establishes a primary account locally, but the account
        becomes usable for the resolve only once its session channel is
        registered + verified on the connected node — a separate async
        round-trip that can still be in flight here. So a fresh
        ``AUTH_REQUIRED`` right after sign-in usually means "the channel
        isn't up yet", not "no account": retry briefly until the resolve
        sees our account (success / access-denied) rather than treating
        that transient state as terminal. Persistent ``AUTH_REQUIRED`` past
        the window is surfaced as an error (we're signed in, so it isn't a
        "please sign in" situation).
        """
        end = _babase.apptime() + _ACCOUNT_CHANNEL_WAIT_SECONDS
        while True:
            outcome = await self._attempt(
                assets, required, auth_recoverable=True
            )
            if outcome is not _ResolveOutcome.AUTH_REQUIRED:
                # SUCCESS, or FAILED (access-denied/other) already messaged.
                return outcome
            if _babase.apptime() >= end:
                logger.warning(
                    'Construct-mode: signed in but the asset server still'
                    ' reports no account after %.0fs (account-session'
                    ' channel never came up).',
                    _ACCOUNT_CHANNEL_WAIT_SECONDS,
                )
                self._fail(
                    'Could not authenticate with the asset server;'
                    ' see log for details.'
                )
                return _ResolveOutcome.FAILED
            await asyncio.sleep(0.3)

    async def _attempt(
        self,
        assets: AssetSubsystem,
        required: list[str],
        *,
        auth_recoverable: bool,
    ) -> _ResolveOutcome:
        """Run one resolve, classifying the outcome.

        On failure a user-facing message is shown here (so callers just
        branch on the returned outcome). ``auth_recoverable`` controls
        whether an authentication-required result is returned for the
        caller to recover from (sign in + retry) or treated as a terminal
        failure (we already tried signing in).
        """
        try:
            await assets.resolve(
                required,
                allow_downloads=True,
                on_download_starting=self._on_download_starting,
            )
            return _ResolveOutcome.SUCCESS
        except AssetAuthRequiredError:
            if auth_recoverable:
                return _ResolveOutcome.AUTH_REQUIRED
            # Already signed in (or tried to) yet auth still failed.
            logger.exception(
                'Construct-mode asset bring-up failed; staying put.'
            )
            self._fail('An error occurred loading assets; see log for details.')
            return _ResolveOutcome.FAILED
        except AssetAccessDeniedError as exc:
            # Surface the server's own message — it names the account
            # (by tag, resolved server-side) and the version, so it both
            # reads clearly and sanity-checks that the server resolved the
            # request to the account we expect. Append the modder guidance.
            logger.warning('Construct-mode: asset access denied: %s', exc)
            detail = (
                exc.server_message
                or 'You do not have permission to load these assets.'
            )
            self._fail(f'{detail} Remove these mods/changes and try again.')
            return _ResolveOutcome.FAILED
        except Exception:
            logger.exception(
                'Construct-mode asset bring-up failed; staying put.'
            )
            self._fail('An error occurred loading assets; see log for details.')
            return _ResolveOutcome.FAILED

    @staticmethod
    async def _wait_for_sign_in() -> bool:
        """Wait for auto-sign-in to establish a primary account.

        Returns True if a primary account is (or becomes) available, False
        if no sign-in is pending or it doesn't complete within the timeout.
        We only wait when credentials are actually in play (validation in
        flight); with no credentials there's nothing to wait for, so we
        fail fast rather than hang on a doomed boot.
        """
        plus = _babase.app.plus
        if plus is None:
            return False
        accounts = plus.accounts

        if _primary_signed_in():
            return True
        if not accounts.have_primary_credentials():
            # No sign-in pending; waiting would just stall.
            return False

        # Credentials are set but not yet validated → poll for the primary
        # account to settle. (A one-time boot path; polling keeps it simple
        # and avoids callback-lifetime juggling.)
        end = _babase.apptime() + _SIGN_IN_WAIT_SECONDS
        while _babase.apptime() < end:
            await asyncio.sleep(0.2)
            if _primary_signed_in():
                return True
        return _primary_signed_in()

    def _on_download_starting(self) -> None:
        """Resolve callback: a real asset download is about to begin.

        Surface progress — fade in and show ``Loading assets…``. A
        fully-local (warm/bundled) resolve never calls this, so that boot
        passes straight through with the screen untouched (the real
        app-mode drives the fade-in). May fire on each retry; idempotent.
        """
        self._begin_visible()
        self._screenmessage('Loading assets…')

    def _begin_visible(self) -> None:
        """Fade the screen up from the boot black-out (idempotent, gui).

        Construct-mode otherwise never fades in (it hands off to the real
        app-mode, which does). When we need to show progress or an error we
        must do it ourselves, or the screen sits black until the stuck-fade
        watchdog force-ends it ~15 s later.
        """
        if self._faded_in or not _babase.app.env.gui:
            return
        self._faded_in = True
        _babase.fade_screen(True, time=0.5)

    @staticmethod
    def _screenmessage(message: str, *, error: bool = False) -> None:
        """Post a screenmessage (red for errors), mirrored to the log.

        Logging every message here keeps the log in lock-step with what's
        shown on screen — and surfaces the bring-up flow on headless (which
        has no screen) and behind the "see log for details" message. Errors
        log at WARNING, progress at INFO.

        IMPORTANT: the screenmessage presentation is provisional — it'll be
        replaced by progress dialogs / a dead-in-the-water UI later. The
        *logging* half must survive that migration (it's the headless +
        diagnostic record), so keep it whatever the presentation becomes.
        """
        if error:
            logger.warning('Construct-mode: %s', message)
        else:
            logger.info('Construct-mode: %s', message)
        try:
            # pylint: disable=cyclic-import
            import babase

            babase.screenmessage(
                message, color=(1.0, 0.0, 0.0) if error else (1.0, 1.0, 1.0)
            )
        except Exception:
            logger.exception('Error showing construct-mode message.')

    def _fail(self, message: str) -> None:
        """Surface a terminal bring-up failure.

        Ensures the screen is up (so the message is visible) and posts it
        in red (also logged at WARNING via :meth:`_screenmessage`).

        On gui we stay put with the message on screen and wait for the
        user to quit (a proper babase-level dead-in-the-water dialog
        replaces this later; the builtin package's fonts are already up,
        so this renders even when resolve fails). On headless there's no
        one to read a dialog, and sitting here forever just looks like a
        hang (and wedges supervisors/tests), so we exit cleanly with a
        specific failure code (:class:`~bacommon.app.ExitCode`). Under the
        server wrapper's default auto-restart this is simply retried (so
        a transient fleet-side condition, e.g. a mid-rollout node, can
        self-heal); ``--no-auto-restart``, direct-binary runs, and BASN
        task orchestration can read the code to treat it as a definitive
        failure.
        """
        self._begin_visible()
        self._screenmessage(message, error=True)

        if not _babase.app.env.gui:
            _babase.set_app_exit_code(ExitCode.ASSET_BRINGUP_FAILED.value)
            _babase.quit()

    def _hand_off(self) -> None:
        """Release the deferred launch intent to the normal app-mode."""
        intent = self._deferred_intent
        if intent is None:
            # Nothing to release (e.g. a plugin already drove an intent).
            return
        self._deferred_intent = None
        logger.debug('Construct-mode handing off to real app-mode.')
        _babase.app.set_intent(intent)
