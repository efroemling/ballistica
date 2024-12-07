# Released under the MIT License. See LICENSE for details.
#
"""Snippets of code for use by the internal layer.

History: originally the engine would dynamically compile/eval various Python
code from within C++ code, but the major downside there was that none of it
was type-checked so if names or arguments changed it would go unnoticed
until it broke at runtime. By instead defining such snippets here and then
capturing references to them all at launch it is possible to allow linting
and type-checking magic to happen and most issues will be caught immediately.
"""
# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring
from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from babase._stringedit import StringEditAdapter


def reset_to_main_menu() -> None:
    # Some high-level event wants us to return to the main menu.
    # an example of this is re-opening the game after we 'soft' quit it
    # on Android.
    if _babase.app.classic is not None:
        _babase.app.classic.return_to_main_menu_session_gracefully()
    else:
        logging.warning('reset_to_main_menu: no-op due to classic not present.')


def get_v2_account_id() -> str | None:
    """Return the current V2 account id if signed in, or None if not."""
    try:
        plus = _babase.app.plus
        if plus is not None:
            account = plus.accounts.primary
            if account is not None:
                accountid = account.accountid
                # (Avoids mypy complaints when plus is not present)
                assert isinstance(accountid, (str, type(None)))
                return accountid
        return None
    except Exception:
        logging.exception('Error fetching v2 account id.')
        return None


def store_config_fullscreen_on() -> None:
    """The OS has changed our fullscreen state and we should take note."""
    _babase.app.config['Fullscreen'] = True
    _babase.app.config.commit()


def store_config_fullscreen_off() -> None:
    """The OS has changed our fullscreen state and we should take note."""
    _babase.app.config['Fullscreen'] = False
    _babase.app.config.commit()


def set_config_fullscreen_on() -> None:
    """Set and store fullscreen state"""
    _babase.app.config['Fullscreen'] = True
    _babase.app.config.apply_and_commit()


def set_config_fullscreen_off() -> None:
    """The OS has changed our fullscreen state and we should take note."""
    _babase.app.config['Fullscreen'] = False
    _babase.app.config.apply_and_commit()


def not_signed_in_screen_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(Lstr(resource='notSignedInErrorText'))


def open_url_with_webbrowser_module(url: str) -> None:
    """Show a URL in the browser or print on-screen error if we can't."""
    import webbrowser
    from babase._language import Lstr

    assert _babase.in_logic_thread()
    try:
        webbrowser.open(url)
    except Exception:
        logging.exception("Error displaying url '%s'.", url)
        _babase.getsimplesound('error').play()
        _babase.screenmessage(Lstr(resource='errorText'), color=(1, 0, 0))


def rejecting_invite_already_in_party_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(
        Lstr(resource='internal.rejectingInviteAlreadyInPartyText'),
        color=(1, 0.5, 0),
    )


def connection_failed_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(
        Lstr(resource='internal.connectionFailedText'), color=(1, 0.5, 0)
    )


def temporarily_unavailable_message() -> None:
    from babase._language import Lstr

    if _babase.app.env.gui:
        _babase.getsimplesound('error').play()
        _babase.screenmessage(
            Lstr(resource='getTicketsWindow.unavailableTemporarilyText'),
            color=(1, 0, 0),
        )


def in_progress_message() -> None:
    from babase._language import Lstr

    if _babase.app.env.gui:
        _babase.getsimplesound('error').play()
        _babase.screenmessage(
            Lstr(resource='getTicketsWindow.inProgressText'),
            color=(1, 0, 0),
        )


def error_message() -> None:
    from babase._language import Lstr

    if _babase.app.env.gui:
        _babase.getsimplesound('error').play()
        _babase.screenmessage(Lstr(resource='errorText'), color=(1, 0, 0))


def success_message() -> None:
    from babase._language import Lstr

    if _babase.app.env.gui:
        _babase.getsimplesound('dingSmall').play()
        _babase.screenmessage(Lstr(resource='successText'), color=(0, 1, 0))


def purchase_not_valid_error() -> None:
    from babase._language import Lstr

    if _babase.app.env.gui:
        _babase.getsimplesound('error').play()
        _babase.screenmessage(
            Lstr(
                resource='store.purchaseNotValidError',
                subs=[('${EMAIL}', 'support@froemling.net')],
            ),
            color=(1, 0, 0),
        )


def purchase_already_in_progress_error() -> None:
    from babase._language import Lstr

    if _babase.app.env.gui:
        _babase.getsimplesound('error').play()
        _babase.screenmessage(
            Lstr(resource='store.purchaseAlreadyInProgressText'),
            color=(1, 0, 0),
        )


def uuid_str() -> str:
    import uuid

    return str(uuid.uuid4())


def orientation_reset_cb_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(
        Lstr(resource='internal.vrOrientationResetCardboardText'),
        color=(0, 1, 0),
    )


def orientation_reset_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(
        Lstr(resource='internal.vrOrientationResetText'), color=(0, 1, 0)
    )


def show_post_purchase_message() -> None:
    assert _babase.app.classic is not None
    _babase.app.classic.accounts.show_post_purchase_message()


def language_test_toggle() -> None:
    _babase.app.lang.setlanguage(
        'Gibberish' if _babase.app.lang.language == 'English' else 'English'
    )


def award_in_control_achievement() -> None:
    if _babase.app.classic is not None:
        _babase.app.classic.ach.award_local_achievement('In Control')
    else:
        logging.warning('award_in_control_achievement is no-op without classic')


def award_dual_wielding_achievement() -> None:
    if _babase.app.classic is not None:
        _babase.app.classic.ach.award_local_achievement('Dual Wielding')
    else:
        logging.warning(
            'award_dual_wielding_achievement is no-op without classic'
        )


def play_gong_sound() -> None:
    if _babase.app.env.gui:
        _babase.getsimplesound('gong').play()


def launch_coop_game(name: str) -> None:
    assert _babase.app.classic is not None
    _babase.app.classic.launch_coop_game(name)


def purchases_restored_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(
        Lstr(resource='getTicketsWindow.purchasesRestoredText'), color=(0, 1, 0)
    )


def unavailable_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(
        Lstr(resource='getTicketsWindow.unavailableText'), color=(1, 0, 0)
    )


def set_last_ad_network(sval: str) -> None:
    if _babase.app.classic is not None:
        _babase.app.classic.ads.last_ad_network = sval
        _babase.app.classic.ads.last_ad_network_set_time = time.time()


def google_play_purchases_not_available_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(
        Lstr(resource='googlePlayPurchasesNotAvailableText'), color=(1, 0, 0)
    )


def google_play_services_not_available_message() -> None:
    from babase._language import Lstr

    _babase.screenmessage(
        Lstr(resource='googlePlayServicesNotAvailableText'), color=(1, 0, 0)
    )


def empty_call() -> None:
    pass


def print_trace() -> None:
    import traceback

    print('Python Traceback (most recent call last):')
    traceback.print_stack()


def toggle_fullscreen() -> None:
    cfg = _babase.app.config
    cfg['Fullscreen'] = not cfg.resolve('Fullscreen')
    cfg.apply_and_commit()


def ui_remote_press() -> None:
    """Handle a press by a remote device that is only usable for nav."""
    from babase._language import Lstr

    if _babase.app.env.headless:
        return

    # Can be called without a context; need a context for getsound.
    _babase.screenmessage(
        Lstr(resource='internal.controllerForMenusOnlyText'),
        color=(1, 0, 0),
    )
    _babase.getsimplesound('error').play()


def remove_in_game_ads_message() -> None:
    if _babase.app.classic is not None:
        _babase.app.classic.ads.do_remove_in_game_ads_message()


def do_quit() -> None:
    _babase.quit()


def hash_strings(inputs: list[str]) -> str:
    """Hash provided strings into a short output string."""
    import hashlib

    sha = hashlib.sha1()
    for inp in inputs:
        sha.update(inp.encode())

    return sha.hexdigest()


def have_account_v2_credentials() -> bool:
    """Do we have primary account-v2 credentials set?"""
    assert _babase.app.plus is not None
    have: bool = _babase.app.plus.accounts.have_primary_credentials()
    return have


def implicit_sign_in(
    login_type_str: str, login_id: str, display_name: str
) -> None:
    """An implicit login happened."""
    from bacommon.login import LoginType

    assert _babase.app.plus is not None

    _babase.app.plus.accounts.on_implicit_sign_in(
        login_type=LoginType(login_type_str),
        login_id=login_id,
        display_name=display_name,
    )


def implicit_sign_out(login_type_str: str) -> None:
    """An implicit logout happened."""
    from bacommon.login import LoginType

    assert _babase.app.plus is not None
    _babase.app.plus.accounts.on_implicit_sign_out(
        login_type=LoginType(login_type_str)
    )


def login_adapter_get_sign_in_token_response(
    login_type_str: str, attempt_id_str: str, result_str: str
) -> None:
    """Login adapter do-sign-in completed."""
    from bacommon.login import LoginType
    from babase._login import LoginAdapterNative

    login_type = LoginType(login_type_str)
    attempt_id = int(attempt_id_str)
    result = None if result_str == '' else result_str

    assert _babase.app.plus is not None
    adapter = _babase.app.plus.accounts.login_adapters[login_type]
    assert isinstance(adapter, LoginAdapterNative)
    adapter.on_sign_in_complete(attempt_id=attempt_id, result=result)


def show_client_too_old_error() -> None:
    """Called at launch if the server tells us we're too old to talk to it."""
    from babase._language import Lstr

    # If you are using an old build of the app and would like to stop
    # seeing this error at launch, do:
    #  ba.app.config['SuppressClientTooOldErrorForBuild'] = ba.app.build_number
    #  ba.app.config.commit()
    # Note that you will have to do that again later if you update to
    # a newer build.
    if (
        _babase.app.config.get('SuppressClientTooOldErrorForBuild')
        == _babase.app.env.engine_build_number
    ):
        return

    if _babase.app.env.gui:
        _babase.getsimplesound('error').play()

    _babase.screenmessage(
        Lstr(
            translate=(
                'serverResponses',
                'Server functionality is no longer supported'
                ' in this version of the game;\n'
                'Please update to a newer version.',
            )
        ),
        color=(1, 0, 0),
    )


def string_edit_adapter_can_be_replaced(adapter: StringEditAdapter) -> bool:
    """Return whether a StringEditAdapter can be replaced."""
    from babase._stringedit import StringEditAdapter

    assert isinstance(adapter, StringEditAdapter)
    return adapter.can_be_replaced()


def get_dev_console_tab_names() -> list[str]:
    """Return the current set of dev-console tab names."""
    return [t.name for t in _babase.app.devconsole.tabs]


def unsupported_controller_message(name: str) -> None:
    """Print a message when an unsupported controller is connected."""
    from babase._language import Lstr

    # Ick; this can get called early in the bootstrapping process
    # before we're allowed to load assets. Guard against that.
    if _babase.asset_loads_allowed():
        _babase.getsimplesound('error').play()
    _babase.screenmessage(
        Lstr(resource='unsupportedControllerText', subs=[('${NAME}', name)]),
        color=(1, 0, 0),
    )


def copy_dev_console_history() -> None:
    """Copy log history from the dev console."""
    import baenv
    from babase._language import Lstr

    if not _babase.clipboard_is_supported():
        _babase.getsimplesound('error').play()
        _babase.screenmessage(
            'Clipboard not supported on this build.',
            color=(1, 0, 0),
        )
        return

    # This requires us to be running with a log-handler set up.
    envconfig = baenv.get_config()
    if envconfig.log_handler is None:
        _babase.getsimplesound('error').play()
        _babase.screenmessage(
            'Not available; standard engine logging is not enabled.',
            color=(1, 0, 0),
        )
        return

    # Just dump everything that's in the log-handler's cache.
    archive = envconfig.log_handler.get_cached()
    lines: list[str] = []
    stdnames = ('stdout', 'stderr')
    for entry in archive.entries:
        reltime = entry.time.timestamp() - envconfig.launch_time
        level_ex = '' if entry.name in stdnames else f' {entry.level.name}'
        lines.append(f'{reltime:.3f}{level_ex} {entry.name}: {entry.message}')

    _babase.clipboard_set_text('\n'.join(lines))
    _babase.screenmessage(Lstr(resource='copyConfirmText'), color=(0, 1, 0))
    _babase.getsimplesound('gunCocking').play()
