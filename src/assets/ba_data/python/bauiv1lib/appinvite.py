# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to inviting people to try the game."""

from __future__ import annotations

import copy
import time
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class ShowFriendCodeWindow(bui.Window):
    """Window showing a code for sharing with friends."""

    def __init__(self, data: dict[str, Any]):
        bui.set_analytics_screen('Friend Promo Code')
        self._width = 650
        self._height = 400
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                color=(0.45, 0.63, 0.15),
                transition='in_scale',
                scale=(
                    1.5
                    if uiscale is bui.UIScale.SMALL
                    else 1.35 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
            )
        )
        self._data = copy.deepcopy(data)
        bui.getsound('cashRegister').play()
        bui.getsound('swish').play()

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(50, self._height - 50),
            size=(60, 60),
            label='',
            on_activate_call=self.close,
            autoselect=True,
            color=(0.45, 0.63, 0.15),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )
        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.8),
            size=(0, 0),
            color=bui.app.ui_v1.infotextcolor,
            scale=1.0,
            flatness=1.0,
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='gatherWindow.shareThisCodeWithFriendsText'),
            maxwidth=self._width * 0.85,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.645),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=2.0,
            h_align='center',
            v_align='center',
            text=data['code'],
            maxwidth=self._width * 0.85,
        )

        award_str: str | bui.Lstr | None
        if self._data['awardTickets'] != 0:
            award_str = bui.Lstr(
                resource='gatherWindow.friendPromoCodeAwardText',
                subs=[('${COUNT}', str(self._data['awardTickets']))],
            )
        else:
            award_str = ''
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.37),
            size=(0, 0),
            color=bui.app.ui_v1.infotextcolor,
            scale=1.0,
            flatness=1.0,
            h_align='center',
            v_align='center',
            text=bui.Lstr(
                value='${A}\n${B}\n${C}\n${D}',
                subs=[
                    (
                        '${A}',
                        bui.Lstr(
                            resource=(
                                'gatherWindow.friendPromoCodeRedeemLongText'
                            ),
                            subs=[
                                ('${COUNT}', str(self._data['tickets'])),
                                (
                                    '${MAX_USES}',
                                    str(self._data['usesRemaining']),
                                ),
                            ],
                        ),
                    ),
                    (
                        '${B}',
                        bui.Lstr(
                            resource=(
                                'gatherWindow.friendPromoCodeWhereToEnterText'
                            )
                        ),
                    ),
                    ('${C}', award_str),
                    (
                        '${D}',
                        bui.Lstr(
                            resource='gatherWindow.friendPromoCodeExpireText',
                            subs=[
                                (
                                    '${EXPIRE_HOURS}',
                                    str(self._data['expireHours']),
                                )
                            ],
                        ),
                    ),
                ],
            ),
            maxwidth=self._width * 0.9,
            max_height=self._height * 0.35,
        )

        if bui.is_browser_likely_available():
            xoffs = 0
            bui.buttonwidget(
                parent=self._root_widget,
                size=(200, 40),
                position=(self._width * 0.5 - 100 + xoffs, 39),
                autoselect=True,
                label=bui.Lstr(resource='gatherWindow.emailItText'),
                on_activate_call=bui.WeakCall(self._email),
            )

    def _email(self) -> None:
        import urllib.parse

        plus = bui.app.plus
        assert plus is not None

        # If somehow we got signed out.
        if plus.get_v1_account_state() != 'signed_in':
            bui.screenmessage(
                bui.Lstr(resource='notSignedInText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        bui.set_analytics_screen('Email Friend Code')
        subject = (
            bui.Lstr(resource='gatherWindow.friendHasSentPromoCodeText')
            .evaluate()
            .replace('${NAME}', plus.get_v1_account_name())
            .replace('${APP_NAME}', bui.Lstr(resource='titleText').evaluate())
            .replace('${COUNT}', str(self._data['tickets']))
        )
        body = (
            bui.Lstr(resource='gatherWindow.youHaveBeenSentAPromoCodeText')
            .evaluate()
            .replace('${APP_NAME}', bui.Lstr(resource='titleText').evaluate())
            + '\n\n'
            + str(self._data['code'])
            + '\n\n'
        )
        body += (
            (
                bui.Lstr(resource='gatherWindow.friendPromoCodeRedeemShortText')
                .evaluate()
                .replace('${COUNT}', str(self._data['tickets']))
            )
            + '\n\n'
            + bui.Lstr(resource='gatherWindow.friendPromoCodeInstructionsText')
            .evaluate()
            .replace('${APP_NAME}', bui.Lstr(resource='titleText').evaluate())
            + '\n'
            + bui.Lstr(resource='gatherWindow.friendPromoCodeExpireText')
            .evaluate()
            .replace('${EXPIRE_HOURS}', str(self._data['expireHours']))
            + '\n'
            + bui.Lstr(resource='enjoyText').evaluate()
        )
        bui.open_url(
            'mailto:?subject='
            + urllib.parse.quote(subject)
            + '&body='
            + urllib.parse.quote(body)
        )

    def close(self) -> None:
        """Close the window."""
        bui.containerwidget(edit=self._root_widget, transition='out_scale')


def handle_app_invites_press() -> None:
    """(internal)"""
    app = bui.app
    plus = app.plus
    assert plus is not None

    bui.screenmessage(
        bui.Lstr(resource='gatherWindow.requestingAPromoCodeText'),
        color=(0, 1, 0),
    )

    def handle_result(result: dict[str, Any] | None) -> None:
        if result is None:
            bui.screenmessage(bui.Lstr(resource='errorText'), color=(1, 0, 0))
            bui.getsound('error').play()
        else:
            ShowFriendCodeWindow(result)

    plus.add_v1_account_transaction(
        {
            'type': 'FRIEND_PROMO_CODE_REQUEST',
            'ali': False,
            'expire_time': time.time() + 10,
        },
        callback=handle_result,
    )
    plus.run_v1_account_transactions()
