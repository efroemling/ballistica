# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to inviting people to try the game."""

import copy
import time
from typing import TYPE_CHECKING

import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets
from bauiv1 import _builtinassets
from bauiv1 import _uiv1assets

if TYPE_CHECKING:
    from typing import Any


def _lines(*parts: str | bui.LangStr) -> bui.LangStr:
    """Stack parts on separate lines via the join template.

    LangStr has no concatenation, so this folds the parts through
    ``ui.line_pair`` right-to-left.
    """
    assert parts
    out: str | bui.LangStr = parts[-1]
    for part in reversed(parts[:-1]):
        out = _commonassets.strings.compose.line_pair(first=part, second=out)
    assert isinstance(out, bui.LangStr)
    return out


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
                darken_behind=True,
            )
        )
        self._data = copy.deepcopy(data)
        _builtinassets.audio.cash_register.get().play()
        _uiv1assets.audio.swish.get().play()

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(50, self._height - 50),
            size=(60, 60),
            label=bui.charstr(bui.SpecialChar.CLOSE),
            textcolor=(1, 1, 1),
            on_activate_call=self.close,
            autoselect=True,
            color=(0.45, 0.63, 0.15),
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
            text=_classicassets.strings.app_invite.share_code,
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

        award_str: str | bui.LangStr
        if self._data['awardTickets'] != 0:
            award_str = _classicassets.strings.app_invite.friend_promo_award(
                count=self._data['awardTickets']
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
            # Four independently-varying lines (the award line is
            # empty when no award applies, matching the legacy blank
            # line), stacked via the newline join template.
            text=_lines(
                (_classicassets.strings.app_invite).friend_promo_redeem_long(
                    count=self._data['tickets'],
                    max_uses=str(self._data['usesRemaining']),
                ),
                _classicassets.strings.app_invite.where_to_enter,
                award_str,
                (_classicassets.strings.app_invite).friend_promo_expire(
                    expire_hours=self._data['expireHours']
                ),
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
                label=_classicassets.strings.app_invite.email_it,
                on_activate_call=bui.WeakCallStrict(self._email),
            )

    def _email(self) -> None:
        import urllib.parse

        plus = bui.app.plus
        assert plus is not None

        # If somehow we got signed out.
        if plus.get_v1_account_state() != 'signed_in':
            bui.screenmessage(
                _classicassets.strings.ui.not_signed_in_status, color=(1, 0, 0)
            )
            _builtinassets.audio.error.get().play()
            return

        bui.set_analytics_screen('Email Friend Code')
        appname = _classicassets.strings.ui.app_name
        subject = (
            (_classicassets.strings.app_invite)
            .friend_has_sent_promo(
                count=self._data['tickets'],
                app_name=appname,
                name=plus.get_v1_account_name(),
            )
            .evaluate()
        )

        # A mail body is genuinely a flat string, so evaluating here is
        # not a retained-surface flatten.
        body = (
            (_classicassets.strings.app_invite)
            .you_have_been_sent_promo(app_name=appname)
            .evaluate()
            + '\n\n'
            + str(self._data['code'])
            + '\n\n'
        )
        body += (
            (_classicassets.strings.app_invite)
            .friend_promo_redeem_short(count=self._data['tickets'])
            .evaluate()
            + '\n\n'
            + (_classicassets.strings.app_invite)
            .friend_promo_instructions(app_name=appname)
            .evaluate()
            + '\n'
            + (_classicassets.strings.app_invite)
            .friend_promo_expire(expire_hours=self._data['expireHours'])
            .evaluate()
            + '\n'
            + _classicassets.strings.app_invite.enjoy.evaluate()
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
        _classicassets.strings.app_invite.requesting_code,
        color=(0, 1, 0),
    )

    def handle_result(result: dict[str, Any] | None) -> None:
        if result is None:
            bui.screenmessage(
                _commonassets.strings.values.error, color=(1, 0, 0)
            )
            _builtinassets.audio.error.get().play()
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
