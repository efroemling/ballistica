# Released under the MIT License. See LICENSE for details.
#
"""Provides ConstructAppMode."""

import asyncio
from enum import Enum
from typing import TYPE_CHECKING, override

from efro.util import strip_exception_tracebacks
from efro.error import CommunicationError

import _babase
import bacommon.cloud
from bacommon.app import ExitCode
from babase._appmode import AppMode
from babase._apputils import is_browser_likely_available
from babase._logging import applog, assetmanagerlog as logger
from babase._simpledialog import SimpleDialog
from babase._assetsubsystem import (
    AssetAuthRequiredError,
    AssetAccessDeniedError,
    AssetClientTooOldError,
    AssetContentError,
    AssetResolveAbortedError,
    make_progress_reporter,
)

if TYPE_CHECKING:
    from babase import AppIntent, LangStr
    from babase._assetsubsystem import AssetSubsystem


#: How long to wait for auto-sign-in to establish a primary account
#: before giving up (after a resolve reports authentication is needed).
_SIGN_IN_WAIT_SECONDS = 15.0

#: After sign-in, how long to keep retrying a resolve that still reports
#: AUTH_REQUIRED — i.e. wait for the account's session channel to finish
#: registering + verifying on the connected node (a round-trip that lags
#: the local primary-account establishment).
_ACCOUNT_CHANNEL_WAIT_SECONDS = 10.0

#: How long to wait for the user to complete a browser-based sign-in
#: before giving up. The server expires login-proxies after ~5 minutes,
#: so polling longer than that is pointless; stay just under it.
_BROWSER_SIGN_IN_WAIT_SECONDS = 290.0

#: How often to ask the server whether a browser-based sign-in has
#: completed (mirrors the account-settings sign-in window's cadence).
_BROWSER_SIGN_IN_POLL_SECONDS = 2.0


class _ResolveOutcome(Enum):
    """Result of one construct-mode resolve attempt."""

    SUCCESS = 'success'
    #: Server needs an authenticated account (recoverable: sign in + retry).
    AUTH_REQUIRED = 'auth_required'
    #: Failed; a user-facing message was already shown.
    FAILED = 'failed'
    #: Abandoned because the app is shutting down. Benign -- no message
    #: shown, no failure exit-code set; the caller just stops quietly.
    ABORTED = 'aborted'


def _logtext(message: str | LangStr) -> str:
    """Flatten a possibly-:class:`~babase.LangStr` message for a log record.

    Dialog-bound messages are localized ``LangStr`` values; the log
    record wants flat text (evaluated in the current locale).
    """
    return message if isinstance(message, str) else message.evaluate()


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

        # The progress/error dialog (gui only). Created lazily the first
        # time we have something to show (a download/build, or an error);
        # a clean no-download boot never creates one.
        self._dialog: SimpleDialog | None = None

        # Stashed resolve inputs so the dialog's Retry button can re-run.
        self._assets: AssetSubsystem | None = None
        self._required: list[str] = []

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
        * If a real download/build is needed, a progress :class:`SimpleDialog`
          appears (gui). If the server then reports authentication is needed,
          we wait for auto-sign-in — or, when no sign-in is coming (no stored
          credentials), offer an interactive browser-based one (gui) — then
          retry. A failure leaves an error
          dialog with a **Retry** button (gui) — pressing it re-runs the
          resolve via :meth:`_run`; on headless we exit with a failure code
          for the wrapper to restart. We stay in construct-mode until success.
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

        # Stash inputs so the Retry button can re-run, then go.
        self._assets = assets
        self._required = required
        await self._run()

    async def _run(self) -> None:
        """Run one resolve cycle; on failure leave an error dialog + Retry.

        Re-entered by the dialog's Retry button (which clears its own button
        first, so it can't double-fire). Wrapped so an unexpected error can't
        leave a stuck modal progress dialog with no way out.
        """
        assert self._assets is not None
        try:
            # Attempt immediately, with whatever account state exists this
            # early (typically none — we don't pre-wait for sign-in, so the
            # public-package path isn't gated on it). A fully-local set passes
            # straight through; a real download/build shows the dialog.
            outcome = await self._attempt(
                self._assets, self._required, auth_recoverable=True
            )

            if outcome is _ResolveOutcome.AUTH_REQUIRED:
                # Wait for auto-sign-in to settle, then retry.
                from babase import builtinassets

                logger.info(
                    'Construct-mode: resolve needs authentication;'
                    ' waiting for sign-in.'
                )
                self._set_status(builtinassets.strings.assets.authenticating)
                signed_in = await self._wait_for_sign_in()
                if not signed_in:
                    # No sign-in is coming on its own (typically no
                    # stored credentials); offer an interactive
                    # browser-based one (gui only).
                    signed_in = await self._sign_in_via_browser()
                if not signed_in:
                    self._fail(builtinassets.strings.assets.sign_in_failed)
                    return
                outcome = await self._resolve_signed_in(
                    self._assets, self._required
                )

            if outcome is _ResolveOutcome.SUCCESS:
                # Hand off to app-mode (fading out first if we showed
                # progress). The post-resolve ideal-flavor media reload happens
                # inside the hand-off -- after the fade-out -- so its visual
                # churn stays hidden behind the black screen.
                self._finish_success()
            elif outcome is _ResolveOutcome.ABORTED:
                # App is shutting down mid-resolve; bow out quietly.
                self._dismiss_dialog()
            # Else FAILED: _attempt / _resolve_signed_in already called _fail,
            # which left an error dialog + Retry (gui) or exited (headless).
        except Exception as exc:
            # Safety net: an unexpected orchestration error must not leave a
            # stuck modal progress dialog. Surface it as a failure (Retry on
            # gui / exit on headless).
            from babase import builtinassets

            logger.exception('Construct-mode bring-up crashed.')
            self._fail(builtinassets.strings.assets.load_error)
            strip_exception_tracebacks(exc)

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
        from babase import builtinassets

        strs = builtinassets.strings.assets
        try:
            await assets.resolve(
                required,
                allow_downloads=True,
                on_download_starting=self._on_download_starting,
                on_progress=make_progress_reporter(self._on_resolve_progress),
            )
            return _ResolveOutcome.SUCCESS
        except AssetAuthRequiredError as exc:
            if auth_recoverable:
                strip_exception_tracebacks(exc)
                return _ResolveOutcome.AUTH_REQUIRED
            # Already signed in (or tried to) yet auth still failed.
            logger.exception(
                'Construct-mode asset bring-up failed; staying put.'
            )
            self._fail(strs.load_error)
            strip_exception_tracebacks(exc)
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
            self._fail(strs.access_denied_guidance(detail=detail))
            strip_exception_tracebacks(exc)
        except AssetClientTooOldError as exc:
            # This build can't address the server's current asset
            # manifests; updating is the only fix (Retry won't help, but
            # it's harmless). Prefer the server's own wording.
            logger.warning('Construct-mode: client too old for assets: %s', exc)
            self._fail(exc.server_message or strs.client_too_old)
            strip_exception_tracebacks(exc)
        except AssetContentError as exc:
            # A source asset in the package failed to build — something
            # its author can fix. Surface the server's message verbatim;
            # it names the offending source file(s). This audience is
            # nearly always the author (dev/test versions only resolve
            # for the owner/dev-team), so speak to them directly.
            logger.warning('Construct-mode: asset content error: %s', exc)
            detail = exc.server_message or 'An asset failed to build.'
            self._fail(strs.content_error_guidance(detail=detail))
            strip_exception_tracebacks(exc)
        except AssetResolveAbortedError as exc:
            # The app started shutting down mid-resolve (e.g. the user
            # quit while a download/cloud-build was still in flight).
            # That's not a real failure -- bow out quietly without an error
            # dialog or failure exit-code.
            logger.debug(
                'Construct-mode asset bring-up aborted; app is shutting'
                ' down.'
            )
            strip_exception_tracebacks(exc)
            return _ResolveOutcome.ABORTED
        except Exception as exc:
            logger.exception(
                'Construct-mode asset bring-up failed; staying put.'
            )
            self._fail(strs.load_error)
            strip_exception_tracebacks(exc)
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

    async def _sign_in_via_browser(self) -> bool:
        """Run an interactive browser-based sign-in.

        Used when a resolve needs an account but no sign-in is coming
        on its own (fresh install / signed out). Without this, an app
        bundling mods that pin restricted asset-packages (dev/test
        versions) would soft-lock here — the account UI for signing in
        lives *behind* the resolve gate we're stuck at.

        Drives the same master-server login-proxy flow the
        account-settings V2 sign-in window uses: request a proxy,
        surface its URL, and poll until the user completes the sign-in
        in their browser, it fails, or the proxy expires. On success,
        primary credentials are set and we wait for the local account
        to finish validating.

        Works on **headless** too (a server bundling restricted assets
        must be signable-in): the URL is always logged at ``ba.app``
        INFO so a server operator can open it and approve, then this
        poll picks the sign-in up. On gui we additionally surface the
        URL in the dialog (with a Sign In button when a browser is
        likely present).

        Returns whether a primary account is now established.
        """
        from babase import builtinassets

        plus = _babase.app.plus
        if plus is None:
            return False

        try:
            proxy = await plus.cloud.send_message_async(
                bacommon.cloud.LoginProxyRequestMessage()
            )
        except Exception as exc:
            # Covers CommunicationError (offline/flaky) and builds
            # without cloud support; either way we can't offer this.
            logger.warning(
                'Construct-mode: login-proxy request failed (%s).',
                type(exc).__name__,
            )
            strip_exception_tracebacks(exc)
            return False

        address = plus.get_master_server_address() + proxy.url
        address_pretty = address.removeprefix('https://')

        # The URL is the actionable operator instruction (the only one a
        # headless server gets), so log it at ba.app INFO — visible by
        # default and the logger server operators watch.
        applog.info(
            'Sign-in required to load bundled assets;'
            ' visit %s in a browser to sign in.',
            address,
        )

        # On gui, also surface the URL in the dialog. Headless has no
        # dialog (ensure returns None); the log line above is its record.
        dialog = self._ensure_dialog()
        if dialog is not None:
            if is_browser_likely_available():
                dialog.update(
                    title=builtinassets.strings.ui.sign_in,
                    message=(
                        builtinassets.strings.assets.sign_in_needed_browser(
                            address=address_pretty
                        )
                    ),
                    progress=None,
                    button_label=builtinassets.strings.ui.sign_in,
                    on_button=lambda: _babase.open_url(address),
                )
            else:
                # No browser on this device (vr/tv/etc.); show the
                # address to visit from another device. (A QR code would
                # be ideal here; that's a planned follow-up.)
                strs = builtinassets.strings
                dialog.update(
                    title=strs.ui.sign_in,
                    message=strs.assets.sign_in_needed_other_device(
                        address=address_pretty
                    ),
                    progress=None,
                    button_label=None,
                    on_button=None,
                )

        deadline = _babase.apptime() + _BROWSER_SIGN_IN_WAIT_SECONDS
        while True:
            await asyncio.sleep(_BROWSER_SIGN_IN_POLL_SECONDS)
            if _babase.apptime() >= deadline:
                logger.warning(
                    'Construct-mode: browser sign-in not completed'
                    ' after %.0f seconds; giving up.',
                    _BROWSER_SIGN_IN_WAIT_SECONDS,
                )
                return False
            try:
                status = await plus.cloud.send_message_async(
                    bacommon.cloud.LoginProxyStateQueryMessage(
                        proxyid=proxy.proxyid, proxykey=proxy.proxykey
                    )
                )
            except CommunicationError as exc:
                # Transient connectivity blip; keep polling.
                strip_exception_tracebacks(exc)
                continue
            except Exception as exc:
                logger.warning(
                    'Construct-mode: login-proxy status check failed (%s).',
                    type(exc).__name__,
                )
                strip_exception_tracebacks(exc)
                return False
            if status.state is status.State.FAIL:
                logger.warning('Construct-mode: browser sign-in failed.')
                return False
            if status.state is status.State.SUCCESS:
                break
            # WAITING; keep polling.

        assert status.credentials is not None
        plus.accounts.set_primary_credentials(status.credentials)

        # Courtesy: tell the server we're done with the proxy (best
        # effort; it expires on its own regardless).
        try:
            await plus.cloud.send_message_async(
                bacommon.cloud.LoginProxyCompleteMessage(proxyid=proxy.proxyid)
            )
        except Exception as exc:
            strip_exception_tracebacks(exc)

        # Back to progress-style dialog state while the account
        # validates and the resolve re-runs (gui only).
        if dialog is not None:
            dialog.update(
                title=builtinassets.strings.ui.updating,
                message=builtinassets.strings.assets.signing_in,
                progress=None,
                button_label=None,
                on_button=None,
            )
        return await self._wait_for_sign_in()

    def _on_download_starting(self) -> None:
        """Resolve callback: a real asset download is about to begin.

        Ensures the progress dialog is up (gui). A fully-local (warm/bundled)
        resolve never calls this, so that boot passes straight through with
        the screen untouched (the real app-mode drives the fade-in). May fire
        on each retry; idempotent.
        """
        self._ensure_dialog()

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

    def _ensure_dialog(self) -> SimpleDialog | None:
        """Return the progress dialog, creating + fading in on first need.

        Returns ``None`` on headless (no dialogs there). The dialog starts
        with the generic 'updating' title and a zeroed bar; callers set the
        message / progress / button.
        """
        from babase import builtinassets

        if not _babase.app.env.gui:
            return None
        self._begin_visible()
        if self._dialog is None:
            self._dialog = SimpleDialog(
                title=builtinassets.strings.ui.updating, progress=0.0
            )
        return self._dialog

    def _dismiss_dialog(self) -> None:
        """Tear down the dialog if present (idempotent)."""
        if self._dialog is not None:
            self._dialog.dismiss()
            self._dialog = None

    def _on_resolve_progress(
        self, message: str | LangStr, progress: float | None
    ) -> None:
        """Progress-reporter sink: log + drive the dialog.

        The INFO log is the headless + diagnostic record — it must survive
        (it's the only bring-up trace on headless, which has no dialog).
        """
        logger.info('Construct-mode: %s', _logtext(message))
        dialog = self._ensure_dialog()
        if dialog is not None:
            dialog.update(message=message, progress=progress)

    def _set_status(self, message: str | LangStr) -> None:
        """Log an interim lifecycle status; reflect it in the dialog if up.

        Unlike :meth:`_on_resolve_progress` this does NOT create a dialog --
        it's for states (e.g. 'Authenticating…') that may occur before any
        download dialog exists; on headless / pre-dialog it just logs.
        """
        logger.info('Construct-mode: %s', _logtext(message))
        if self._dialog is not None:
            self._dialog.update(message=message)

    def _finish_success(self) -> None:
        """Hand off to app-mode after a successful resolve.

        If we faded in to show progress, fade back out to black first so the
        post-resolve media reload (a visible hitch) and the dialog teardown
        happen behind black rather than flashing, and don't hard-cut into
        app-mode's UI -- the fade's end-command does that work, and app-mode
        fades back in from black on its own (it expects to start from black).
        A purely-local (warm/bundled) boot never faded in -- nor does headless
        -- so there (and when there's no intent to release) we do it
        immediately (the reload is a no-op on those paths).
        """
        if self._dialog is not None:
            logger.info('Construct-mode: assets updated.')
        if self._faded_in and self._deferred_intent is not None:
            _babase.fade_screen(
                False, time=0.25, endcall=self._reload_and_hand_off
            )
        else:
            self._reload_and_hand_off()

    def _reload_and_hand_off(self) -> None:
        """Reload ideal-flavor media, tear down the dialog, then hand off.

        Runs behind the faded-out black screen (or immediately on the
        warm/headless path). The resolve may have fetched ideal flavors of
        assets that came up earlier on fallbacks (e.g. builtin textures loaded
        at boot, before their ideal versions were cached); reloading them here
        -- after the fade-out -- keeps the reload's hitch hidden so app-mode
        renders at the ideal flavor on fade-in. Cheap no-op when nothing
        changed (the warm path).
        """
        _babase.reload_changed_media()
        self._dismiss_dialog()
        self._hand_off()

    def _fail(self, message: str | LangStr) -> None:
        """Surface a terminal bring-up failure.

        On gui, leave an error dialog up with a **Retry** button (pressing it
        re-runs :meth:`_run`); the message is logged at WARNING (the surviving
        record). The builtin package's fonts/assets are already up, so this
        renders even when the resolve failed.

        On headless there's no one to read a dialog, and sitting here forever
        just looks like a hang (and wedges supervisors/tests), so we exit
        cleanly with a specific failure code (:class:`~bacommon.app.ExitCode`).
        Under the server wrapper's default auto-restart this is simply retried
        (so a transient fleet-side condition, e.g. a mid-rollout node, can
        self-heal); ``--no-auto-restart``, direct-binary runs, and BASN task
        orchestration can read the code to treat it as a definitive failure.
        """
        from babase import builtinassets

        logger.warning('Construct-mode: %s', _logtext(message))

        if not _babase.app.env.gui:
            _babase.set_app_exit_code(ExitCode.ASSET_BRINGUP_FAILED.value)
            _babase.quit()
            return

        dialog = self._ensure_dialog()
        assert dialog is not None
        dialog.update(
            title=builtinassets.strings.ui.error,
            message=message,
            progress=None,
            button_label=builtinassets.strings.ui.retry,
            on_button=self._on_retry,
        )

    def _on_retry(self) -> None:
        """Dialog Retry-button handler: re-run the resolve.

        Resets the dialog to a progress state first -- restores the 'updating'
        title, removes the Retry button (so a second press can't fire while we
        re-resolve), and shows that work has resumed.
        """
        from babase import builtinassets

        if self._dialog is not None:
            self._dialog.update(
                title=builtinassets.strings.ui.updating,
                message='',
                progress=0.0,
                button_label=None,
                on_button=None,
            )
        _babase.app.create_async_task(self._run(), name='construct-mode retry')

    def _hand_off(self) -> None:
        """Release the deferred launch intent to the normal app-mode."""
        intent = self._deferred_intent
        if intent is None:
            # Nothing to release (e.g. a plugin already drove an intent).
            return
        self._deferred_intent = None
        logger.debug('Construct-mode handing off to real app-mode.')
        _babase.app.set_intent(intent)
