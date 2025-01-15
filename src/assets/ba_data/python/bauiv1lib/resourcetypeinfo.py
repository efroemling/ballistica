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
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        self._transitioning_out = False
        self._width = 570
        self._height = 400
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

        if resource_type == 'tickets':
            yoffs -= 20
            rdesc = (
                'Tickets can be used to unlock characters,\n'
                'maps, minigames, and more in the store.\n'
                '\n'
                'Tickets can be found in chests won through\n'
                'campaigns, tournaments, and achievements.'
            )
            texname = 'tickets'
        elif resource_type == 'tokens':
            rdesc = (
                'Tokens are used to speed up chest unlocks\n'
                'and for other game and account features.\n'
                '\n'
                'You can win tokens in the game or buy them\n'
                'in packs. Or buy a Gold Pass for infinite\n'
                'tokens and never hear about them again.'
            )
            texname = 'coin'
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
            position=(self._width * 0.5, yoffs - 5.0),
            text=rdesc,
            scale=0.8,
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
