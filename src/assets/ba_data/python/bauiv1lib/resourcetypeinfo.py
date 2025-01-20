# Released under the MIT License. See LICENSE for details.
#
"""Provides a window which shows info about resource types."""

from __future__ import annotations

from typing import override, TYPE_CHECKING, assert_never

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Literal


class ResourceTypeInfoWindow(PopupWindow):
    """Popup window providing info about resource types."""

    def __init__(
        self,
        resource_type: Literal['tickets', 'tokens', 'trophies', 'xp'],
        origin_widget: bui.Widget,
    ):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.4 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        self._transitioning_out = False
        self._width = 570
        self._height = 400
        self._get_tokens_button: bui.Widget | None = None
        bg_color = (0.5, 0.4, 0.6)
        super().__init__(
            size=(self._width, self._height),
            toolbar_visibility='inherit',
            scale=scale,
            bg_color=bg_color,
            position=origin_widget.get_screen_space_center(),
            edge_buffer_scale=4.0,
        )
        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(40, self._height - 40),
            size=(50, 50),
            scale=0.7,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        yoffs = self._height - 145

        max_rdesc_height = 160

        rdesc: bui.Lstr | str

        if resource_type == 'tickets':
            yoffs -= 20
            rdesc = bui.Lstr(resource='ticketsDescriptionText')
            texname = 'tickets'
        elif resource_type == 'tokens':
            rdesc = bui.Lstr(resource='tokens.tokensDescriptionText')
            texname = 'coin'
            bwidth = 200
            bheight = 50

            # Show 'Get Tokens' button if we don't have a gold pass
            # (in case a user doesn't notice the '+' button or we have
            # it disabled for some reason).
            if not bui.app.classic.gold_pass:
                self._get_tokens_button = bui.buttonwidget(
                    parent=self.root_widget,
                    position=(
                        self._width * 0.5 - bwidth * 0.5,
                        yoffs - 15.0 - bheight - max_rdesc_height,
                    ),
                    color=bg_color,
                    textcolor=(0.8, 0.8, 0.8),
                    label=bui.Lstr(resource='tokens.getTokensText'),
                    size=(bwidth, bheight),
                    autoselect=True,
                    on_activate_call=bui.WeakCall(self._on_get_tokens_press),
                )

        elif resource_type == 'trophies':
            rdesc = 'TODO: Will show trophies & league rankings.'
            texname = 'crossOut'
        elif resource_type == 'xp':
            rdesc = 'TODO: Will describe xp/levels.'
            texname = 'crossOut'
        else:
            assert_never(resource_type)

        imgsize = 100.0
        bui.imagewidget(
            parent=self.root_widget,
            position=(self._width * 0.5 - imgsize * 0.5, yoffs + 5.0),
            size=(imgsize, imgsize),
            texture=bui.gettexture(texname),
        )

        bui.textwidget(
            parent=self.root_widget,
            h_align='center',
            v_align='top',
            size=(0, 0),
            maxwidth=self._width * 0.8,
            max_height=max_rdesc_height,
            position=(self._width * 0.5, yoffs - 5.0),
            text=rdesc,
            scale=0.8,
        )

    def _on_get_tokens_press(self) -> None:
        from bauiv1lib.gettokens import show_get_tokens_window

        self._transition_out()
        show_get_tokens_window(
            origin_widget=bui.existing(self._get_tokens_button)
        )

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()
