# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Snippets of code for use by the internal C++ layer.

History: originally I would dynamically compile/eval bits of Python text
from within C++ code, but the major downside there was that none of that was
type-checked so if names or arguments changed I would never catch code breakage
until the code was next run.  By defining all snippets I use here and then
capturing references to them all at launch I can immediately verify everything
I'm looking for exists and pylint/mypy can do their magic on this file.
"""
# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import List, Sequence, Optional, Dict, Any
    import ba


def reset_to_main_menu() -> None:
    """Reset the game to the main menu gracefully."""
    _ba.app.return_to_main_menu_session_gracefully()


def set_config_fullscreen_on() -> None:
    """The app has set fullscreen on its own and we should note it."""
    _ba.app.config['Fullscreen'] = True
    _ba.app.config.commit()


def set_config_fullscreen_off() -> None:
    """The app has set fullscreen on its own and we should note it."""
    _ba.app.config['Fullscreen'] = False
    _ba.app.config.commit()


def not_signed_in_screen_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(Lstr(resource='notSignedInErrorText'))


def connecting_to_party_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(Lstr(resource='internal.connectingToPartyText'),
                      color=(1, 1, 1))


def rejecting_invite_already_in_party_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(
        Lstr(resource='internal.rejectingInviteAlreadyInPartyText'),
        color=(1, 0.5, 0))


def connection_failed_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(Lstr(resource='internal.connectionFailedText'),
                      color=(1, 0.5, 0))


def temporarily_unavailable_message() -> None:
    from ba._lang import Lstr
    _ba.playsound(_ba.getsound('error'))
    _ba.screenmessage(
        Lstr(resource='getTicketsWindow.unavailableTemporarilyText'),
        color=(1, 0, 0))


def in_progress_message() -> None:
    from ba._lang import Lstr
    _ba.playsound(_ba.getsound('error'))
    _ba.screenmessage(Lstr(resource='getTicketsWindow.inProgressText'),
                      color=(1, 0, 0))


def error_message() -> None:
    from ba._lang import Lstr
    _ba.playsound(_ba.getsound('error'))
    _ba.screenmessage(Lstr(resource='errorText'), color=(1, 0, 0))


def purchase_not_valid_error() -> None:
    from ba._lang import Lstr
    _ba.playsound(_ba.getsound('error'))
    _ba.screenmessage(Lstr(resource='store.purchaseNotValidError',
                           subs=[('${EMAIL}', 'support@froemling.net')]),
                      color=(1, 0, 0))


def purchase_already_in_progress_error() -> None:
    from ba._lang import Lstr
    _ba.playsound(_ba.getsound('error'))
    _ba.screenmessage(Lstr(resource='store.purchaseAlreadyInProgressText'),
                      color=(1, 0, 0))


def gear_vr_controller_warning() -> None:
    from ba._lang import Lstr
    _ba.playsound(_ba.getsound('error'))
    _ba.screenmessage(Lstr(resource='usesExternalControllerText'),
                      color=(1, 0, 0))


def orientation_reset_cb_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(
        Lstr(resource='internal.vrOrientationResetCardboardText'),
        color=(0, 1, 0))


def orientation_reset_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(Lstr(resource='internal.vrOrientationResetText'),
                      color=(0, 1, 0))


def on_app_pause() -> None:
    _ba.app.on_app_pause()


def on_app_resume() -> None:
    _ba.app.on_app_resume()


def launch_main_menu_session() -> None:
    from bastd.mainmenu import MainMenuSession
    _ba.new_host_session(MainMenuSession)


def language_test_toggle() -> None:
    from ba._lang import setlanguage
    setlanguage('Gibberish' if _ba.app.language == 'English' else 'English')


def award_in_control_achievement() -> None:
    from ba._achievement import award_local_achievement
    award_local_achievement('In Control')


def award_dual_wielding_achievement() -> None:
    from ba._achievement import award_local_achievement
    award_local_achievement('Dual Wielding')


def play_gong_sound() -> None:
    _ba.playsound(_ba.getsound('gong'))


def launch_coop_game(name: str) -> None:
    _ba.app.launch_coop_game(name)


def purchases_restored_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(Lstr(resource='getTicketsWindow.purchasesRestoredText'),
                      color=(0, 1, 0))


def dismiss_wii_remotes_window() -> None:
    call = _ba.app.ui.dismiss_wii_remotes_window_call
    if call is not None:
        call()


def unavailable_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(Lstr(resource='getTicketsWindow.unavailableText'),
                      color=(1, 0, 0))


def submit_analytics_counts(sval: str) -> None:
    _ba.add_transaction({'type': 'ANALYTICS_COUNTS', 'values': sval})
    _ba.run_transactions()


def set_last_ad_network(sval: str) -> None:
    import time
    _ba.app.last_ad_network = sval
    _ba.app.last_ad_network_set_time = time.time()


def no_game_circle_message() -> None:
    from ba._lang import Lstr
    _ba.screenmessage(Lstr(resource='noGameCircleText'), color=(1, 0, 0))


def empty_call() -> None:
    pass


def level_icon_press() -> None:
    print('LEVEL ICON PRESSED')


def trophy_icon_press() -> None:
    print('TROPHY ICON PRESSED')


def coin_icon_press() -> None:
    print('COIN ICON PRESSED')


def ticket_icon_press() -> None:
    from bastd.ui.resourcetypeinfo import ResourceTypeInfoWindow
    ResourceTypeInfoWindow(
        origin_widget=_ba.get_special_widget('tickets_info_button'))


def back_button_press() -> None:
    _ba.back_press()


def friends_button_press() -> None:
    print('FRIEND BUTTON PRESSED!')


def print_trace() -> None:
    import traceback
    print('Python Traceback (most recent call last):')
    traceback.print_stack()


def toggle_fullscreen() -> None:
    cfg = _ba.app.config
    cfg['Fullscreen'] = not cfg.resolve('Fullscreen')
    cfg.apply_and_commit()


def party_icon_activate(origin: Sequence[float]) -> None:
    import weakref
    from bastd.ui.party import PartyWindow
    app = _ba.app
    _ba.playsound(_ba.getsound('swish'))

    # If it exists, dismiss it; otherwise make a new one.
    if app.ui.party_window is not None and app.ui.party_window() is not None:
        app.ui.party_window().close()
    else:
        app.ui.party_window = weakref.ref(PartyWindow(origin=origin))


def read_config() -> None:
    _ba.app.read_config()


def ui_remote_press() -> None:
    """Handle a press by a remote device that is only usable for nav."""
    from ba._lang import Lstr

    # Can be called without a context; need a context for getsound.
    with _ba.Context('ui'):
        _ba.screenmessage(Lstr(resource='internal.controllerForMenusOnlyText'),
                          color=(1, 0, 0))
        _ba.playsound(_ba.getsound('error'))


def quit_window() -> None:
    from bastd.ui.confirm import QuitWindow
    QuitWindow()


def remove_in_game_ads_message() -> None:
    _ba.app.do_remove_in_game_ads_message()


def telnet_access_request() -> None:
    from bastd.ui.telnet import TelnetAccessRequestWindow
    TelnetAccessRequestWindow()


def do_quit() -> None:
    _ba.quit()


def shutdown() -> None:
    _ba.app.on_app_shutdown()


def gc_disable() -> None:
    import gc
    gc.disable()


def device_menu_press(device: ba.InputDevice) -> None:
    from bastd.ui.mainmenu import MainMenuWindow
    in_main_menu = _ba.app.ui.has_main_menu_window()
    if not in_main_menu:
        _ba.set_ui_input_device(device)
        _ba.playsound(_ba.getsound('swish'))
        _ba.app.ui.set_main_menu_window(MainMenuWindow().get_root_widget())


def show_url_window(address: str) -> None:
    from bastd.ui.url import ShowURLWindow
    ShowURLWindow(address)


def party_invite_revoke(invite_id: str) -> None:
    # If there's a confirm window up for joining this particular
    # invite, kill it.
    for winref in _ba.app.invite_confirm_windows:
        win = winref()
        if win is not None and win.ew_party_invite_id == invite_id:
            _ba.containerwidget(edit=win.get_root_widget(),
                                transition='out_right')


def filter_chat_message(msg: str, client_id: int) -> Optional[str]:
    """Intercept/filter chat messages.

    Called for all chat messages while hosting.
    Messages originating from the host will have clientID -1.
    Should filter and return the string to be displayed, or return None
    to ignore the message.
    """
    del client_id  # Unused by default.
    return msg


def local_chat_message(msg: str) -> None:
    if (_ba.app.ui.party_window is not None
            and _ba.app.ui.party_window() is not None):
        _ba.app.ui.party_window().on_chat_message(msg)


def handle_remote_achievement_list(completed_achievements: List[str]) -> None:
    from ba import _achievement
    _achievement.set_completed_achievements(completed_achievements)


def get_player_icon(sessionplayer: ba.SessionPlayer) -> Dict[str, Any]:
    info = sessionplayer.get_icon_info()
    return {
        'texture': _ba.gettexture(info['texture']),
        'tint_texture': _ba.gettexture(info['tint_texture']),
        'tint_color': info['tint_color'],
        'tint2_color': info['tint2_color']
    }
