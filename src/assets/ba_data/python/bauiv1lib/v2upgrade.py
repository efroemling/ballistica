# Released under the MIT License. See LICENSE for details.
#
"""UI for upgrading V1 accounts to V2."""

from __future__ import annotations

import bauiv1 as bui


class V2UpgradeWindow(bui.Window):
    """A window presenting a URL to the user visually."""

    def __init__(self, login_name: str, code: str):

        app = bui.app
        assert app.classic is not None
        uiscale = app.ui_v1.uiscale

        self._code = code

        self._width = 700
        self._height = 270
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + 40),
                transition='in_right',
                scale=(
                    1.25
                    if uiscale is bui.UIScale.SMALL
                    else 1.25 if uiscale is bui.UIScale.MEDIUM else 1.25
                ),
            )
        )
        bui.getsound('error').play()

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 46),
            size=(0, 0),
            color=app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            text=bui.Lstr(
                resource='deviceAccountUpgradeText',
                subs=[('${NAME}', login_name)],
            ),
            maxwidth=self._width * 0.95,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, 125),
            size=(0, 0),
            scale=0.8,
            color=(0.7, 0.8, 0.7),
            h_align='center',
            v_align='center',
            text=(
                bui.charstr(bui.SpecialChar.LOCAL_ACCOUNT)
                + login_name
                + '    ---->    '
                + bui.charstr(bui.SpecialChar.V2_LOGO)
                + login_name
            ),
            maxwidth=self._width * 0.95,
        )
        button_width = 200

        cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(20, 25),
            size=(button_width, 65),
            autoselect=True,
            label=bui.Lstr(resource='notNowText'),
            on_activate_call=self._done,
        )

        _what_is_this_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.5 - button_width * 0.5, 25),
            size=(button_width, 65),
            autoselect=True,
            label=bui.Lstr(resource='whatIsThisText'),
            color=(0.55, 0.5, 0.6),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=show_what_is_v2_page,
        )

        upgrade_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - button_width - 20, 25),
            size=(button_width, 65),
            autoselect=True,
            label=bui.Lstr(resource='upgradeText'),
            on_activate_call=self._upgrade_press,
        )

        bui.containerwidget(
            edit=self._root_widget,
            selected_child=upgrade_button,
            cancel_button=cancel_button,
        )

    def _upgrade_press(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # Get rid of the window and sign out before kicking the
        # user over to a browser to do the upgrade. This hopefully
        # makes it more clear when they come back that they need to
        # sign in with the 'BombSquad account' option.
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        plus.sign_out_v1()
        bamasteraddr = plus.get_master_server_address(version=2)
        bui.open_url(f'{bamasteraddr}/v2uda/{self._code}')

    def _done(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_left')


def show_what_is_v2_page() -> None:
    """Show the webpage describing V2 accounts."""
    plus = bui.app.plus
    assert plus is not None

    bamasteraddr = plus.get_master_server_address(version=2)
    bui.open_url(f'{bamasteraddr}/whatisv2')
