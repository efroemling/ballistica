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
"""UI functionality related to inviting people to try the game."""

from __future__ import annotations

import copy
import time
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Optional, Dict, Union


class AppInviteWindow(ba.Window):
    """Window for showing different ways to invite people to try the game."""

    def __init__(self) -> None:
        ba.set_analytics_screen('AppInviteWindow')
        self._data: Optional[Dict[str, Any]] = None
        self._width = 650
        self._height = 400

        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            scale=(1.8 if uiscale is ba.UIScale.SMALL else
                   1.35 if uiscale is ba.UIScale.MEDIUM else 1.0)))

        self._cancel_button = ba.buttonwidget(parent=self._root_widget,
                                              scale=0.8,
                                              position=(60, self._height - 50),
                                              size=(50, 50),
                                              label='',
                                              on_activate_call=self.close,
                                              autoselect=True,
                                              color=(0.4, 0.4, 0.6),
                                              icon=ba.gettexture('crossOut'),
                                              iconscale=1.2)

        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button)

        ba.textwidget(
            parent=self._root_widget,
            size=(0, 0),
            position=(self._width * 0.5, self._height * 0.5 + 110),
            autoselect=True,
            scale=0.8,
            maxwidth=self._width * 0.9,
            h_align='center',
            v_align='center',
            color=(0.3, 0.8, 0.3),
            flatness=1.0,
            text=ba.Lstr(
                resource='gatherWindow.earnTicketsForRecommendingAmountText',
                fallback_resource=(
                    'gatherWindow.earnTicketsForRecommendingText'),
                subs=[
                    ('${COUNT}',
                     str(_ba.get_account_misc_read_val('friendTryTickets',
                                                       300))),
                    ('${YOU_COUNT}',
                     str(
                         _ba.get_account_misc_read_val('friendTryAwardTickets',
                                                       100)))
                ]))

        or_text = ba.Lstr(resource='orText',
                          subs=[('${A}', ''),
                                ('${B}', '')]).evaluate().strip()
        ba.buttonwidget(
            parent=self._root_widget,
            size=(250, 150),
            position=(self._width * 0.5 - 125, self._height * 0.5 - 80),
            autoselect=True,
            button_type='square',
            label=ba.Lstr(resource='gatherWindow.inviteFriendsText'),
            on_activate_call=ba.WeakCall(self._google_invites))

        ba.textwidget(parent=self._root_widget,
                      size=(0, 0),
                      position=(self._width * 0.5, self._height * 0.5 - 94),
                      autoselect=True,
                      scale=0.9,
                      h_align='center',
                      v_align='center',
                      color=(0.5, 0.5, 0.5),
                      flatness=1.0,
                      text=or_text)

        ba.buttonwidget(
            parent=self._root_widget,
            size=(180, 50),
            position=(self._width * 0.5 - 90, self._height * 0.5 - 170),
            autoselect=True,
            color=(0.5, 0.5, 0.6),
            textcolor=(0.7, 0.7, 0.8),
            text_scale=0.8,
            label=ba.Lstr(resource='gatherWindow.appInviteSendACodeText'),
            on_activate_call=ba.WeakCall(self._send_code))

        # kick off a transaction to get our code
        _ba.add_transaction(
            {
                'type': 'FRIEND_PROMO_CODE_REQUEST',
                'ali': False,
                'expire_time': time.time() + 20
            },
            callback=ba.WeakCall(self._on_code_result))
        _ba.run_transactions()

    def _on_code_result(self, result: Optional[Dict[str, Any]]) -> None:
        if result is not None:
            self._data = result

    def _send_code(self) -> None:
        handle_app_invites_press(force_code=True)

    def _google_invites(self) -> None:
        if self._data is None:
            ba.screenmessage(ba.Lstr(
                resource='getTicketsWindow.unavailableTemporarilyText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        if _ba.get_account_state() == 'signed_in':
            ba.set_analytics_screen('App Invite UI')
            _ba.show_app_invite(
                ba.Lstr(resource='gatherWindow.appInviteTitleText',
                        subs=[('${APP_NAME}', ba.Lstr(resource='titleText'))
                              ]).evaluate(),
                ba.Lstr(resource='gatherWindow.appInviteMessageText',
                        subs=[('${COUNT}', str(self._data['tickets'])),
                              ('${NAME}', _ba.get_account_name().split()[0]),
                              ('${APP_NAME}', ba.Lstr(resource='titleText'))
                              ]).evaluate(), self._data['code'])
        else:
            ba.playsound(ba.getsound('error'))

    def close(self) -> None:
        """Close the window."""
        ba.containerwidget(edit=self._root_widget, transition='out_scale')


class ShowFriendCodeWindow(ba.Window):
    """Window showing a code for sharing with friends."""

    def __init__(self, data: Dict[str, Any]):
        from ba.internal import is_browser_likely_available
        ba.set_analytics_screen('Friend Promo Code')
        self._width = 650
        self._height = 400
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            color=(0.45, 0.63, 0.15),
            transition='in_scale',
            scale=(1.7 if uiscale is ba.UIScale.SMALL else
                   1.35 if uiscale is ba.UIScale.MEDIUM else 1.0)))
        self._data = copy.deepcopy(data)
        ba.playsound(ba.getsound('cashRegister'))
        ba.playsound(ba.getsound('swish'))

        self._cancel_button = ba.buttonwidget(parent=self._root_widget,
                                              scale=0.7,
                                              position=(50, self._height - 50),
                                              size=(60, 60),
                                              label='',
                                              on_activate_call=self.close,
                                              autoselect=True,
                                              color=(0.45, 0.63, 0.15),
                                              icon=ba.gettexture('crossOut'),
                                              iconscale=1.2)
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button)

        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.8),
            size=(0, 0),
            color=ba.app.ui.infotextcolor,
            scale=1.0,
            flatness=1.0,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='gatherWindow.shareThisCodeWithFriendsText'),
            maxwidth=self._width * 0.85)

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height * 0.645),
                      size=(0, 0),
                      color=(1.0, 3.0, 1.0),
                      scale=2.0,
                      h_align='center',
                      v_align='center',
                      text=data['code'],
                      maxwidth=self._width * 0.85)

        award_str: Optional[Union[str, ba.Lstr]]
        if self._data['awardTickets'] != 0:
            award_str = ba.Lstr(
                resource='gatherWindow.friendPromoCodeAwardText',
                subs=[('${COUNT}', str(self._data['awardTickets']))])
        else:
            award_str = ''
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.37),
            size=(0, 0),
            color=ba.app.ui.infotextcolor,
            scale=1.0,
            flatness=1.0,
            h_align='center',
            v_align='center',
            text=ba.Lstr(
                value='${A}\n${B}\n${C}\n${D}',
                subs=[
                    ('${A}',
                     ba.Lstr(
                         resource='gatherWindow.friendPromoCodeRedeemLongText',
                         subs=[('${COUNT}', str(self._data['tickets'])),
                               ('${MAX_USES}',
                                str(self._data['usesRemaining']))])),
                    ('${B}',
                     ba.Lstr(resource=(
                         'gatherWindow.friendPromoCodeWhereToEnterText'))),
                    ('${C}', award_str),
                    ('${D}',
                     ba.Lstr(resource='gatherWindow.friendPromoCodeExpireText',
                             subs=[('${EXPIRE_HOURS}',
                                    str(self._data['expireHours']))]))
                ]),
            maxwidth=self._width * 0.9,
            max_height=self._height * 0.35)

        if is_browser_likely_available():
            xoffs = 0
            ba.buttonwidget(parent=self._root_widget,
                            size=(200, 40),
                            position=(self._width * 0.5 - 100 + xoffs, 39),
                            autoselect=True,
                            label=ba.Lstr(resource='gatherWindow.emailItText'),
                            on_activate_call=ba.WeakCall(self._email))

    def _google_invites(self) -> None:
        ba.set_analytics_screen('App Invite UI')
        _ba.show_app_invite(
            ba.Lstr(resource='gatherWindow.appInviteTitleText',
                    subs=[('${APP_NAME}', ba.Lstr(resource='titleText'))
                          ]).evaluate(),
            ba.Lstr(resource='gatherWindow.appInviteMessageText',
                    subs=[('${COUNT}', str(self._data['tickets'])),
                          ('${NAME}', _ba.get_account_name().split()[0]),
                          ('${APP_NAME}', ba.Lstr(resource='titleText'))
                          ]).evaluate(), self._data['code'])

    def _email(self) -> None:
        import urllib.parse

        # If somehow we got signed out.
        if _ba.get_account_state() != 'signed_in':
            ba.screenmessage(ba.Lstr(resource='notSignedInText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        ba.set_analytics_screen('Email Friend Code')
        subject = (ba.Lstr(resource='gatherWindow.friendHasSentPromoCodeText').
                   evaluate().replace(
                       '${NAME}', _ba.get_account_name()).replace(
                           '${APP_NAME}',
                           ba.Lstr(resource='titleText').evaluate()).replace(
                               '${COUNT}', str(self._data['tickets'])))
        body = (ba.Lstr(resource='gatherWindow.youHaveBeenSentAPromoCodeText').
                evaluate().replace('${APP_NAME}',
                                   ba.Lstr(resource='titleText').evaluate()) +
                '\n\n' + str(self._data['code']) + '\n\n')
        body += (
            (ba.Lstr(resource='gatherWindow.friendPromoCodeRedeemShortText').
             evaluate().replace('${COUNT}', str(self._data['tickets']))) +
            '\n\n' +
            ba.Lstr(resource='gatherWindow.friendPromoCodeInstructionsText').
            evaluate().replace('${APP_NAME}',
                               ba.Lstr(resource='titleText').evaluate()) +
            '\n' + ba.Lstr(resource='gatherWindow.friendPromoCodeExpireText').
            evaluate().replace('${EXPIRE_HOURS}', str(
                self._data['expireHours'])) + '\n' +
            ba.Lstr(resource='enjoyText').evaluate())
        ba.open_url('mailto:?subject=' + urllib.parse.quote(subject) +
                    '&body=' + urllib.parse.quote(body))

    def close(self) -> None:
        """Close the window."""
        ba.containerwidget(edit=self._root_widget, transition='out_scale')


def handle_app_invites_press(force_code: bool = False) -> None:
    """(internal)"""
    app = ba.app
    do_app_invites = (app.platform == 'android' and app.subplatform == 'google'
                      and _ba.get_account_misc_read_val(
                          'enableAppInvites', False) and not app.on_tv)
    if force_code:
        do_app_invites = False

    # FIXME: Should update this to grab a code before showing the invite UI.
    if do_app_invites:
        AppInviteWindow()
    else:
        ba.screenmessage(
            ba.Lstr(resource='gatherWindow.requestingAPromoCodeText'),
            color=(0, 1, 0))

        def handle_result(result: Optional[Dict[str, Any]]) -> None:
            with ba.Context('ui'):
                if result is None:
                    ba.screenmessage(ba.Lstr(resource='errorText'),
                                     color=(1, 0, 0))
                    ba.playsound(ba.getsound('error'))
                else:
                    ShowFriendCodeWindow(result)

        _ba.add_transaction(
            {
                'type': 'FRIEND_PROMO_CODE_REQUEST',
                'ali': False,
                'expire_time': time.time() + 10
            },
            callback=handle_result)
        _ba.run_transactions()
