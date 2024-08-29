# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for the Discord window."""

from __future__ import annotations

import bauiv1 as bui


class DiscordWindow(bui.Window):
    """Window for joining the Discord."""

    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        if bui.app.classic is None:
            raise RuntimeError('This requires classic support.')

        app = bui.app
        assert app.classic is not None

        # If they provided an origin-widget, scale up from that.
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        uiscale = bui.app.ui_v1.uiscale
        self._width = 800
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        self._height = 320
        top_extra = 10 if uiscale is bui.UIScale.SMALL else 0
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                transition=transition,
                toolbar_visibility='menu_minimal',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    1.6
                    if uiscale is bui.UIScale.SMALL
                    else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(0, 5) if uiscale is bui.UIScale.SMALL else (0, 0),
            )
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self._do_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(53 + x_inset, self._height - 60),
                size=(140, 60),
                scale=0.8,
                autoselect=True,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self._do_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        # Do we need to translate 'Discord'? Or is that always the name?
        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(0, self._height - 52),
            size=(self._width, 25),
            text='Discord',
            color=app.ui_v1.title_color,
            h_align='center',
            v_align='top',
        )

        min_size = min(self._width - 25, self._height - 25)
        bui.imagewidget(
            parent=self._root_widget,
            position=(40, -15),
            size=(min_size, min_size),
            texture=bui.gettexture('discordServer'),
        )

        # Hmm should we translate this? The discord server is mostly
        # English so being able to read this might be a good screening
        # process?..
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width / 2 - 60, self._height - 100),
            text='We have our own Discord server where you can:\n- Find new'
            ' friends and people to play with\n- Participate in Office'
            ' Hours/Coffee with Eric\n- Share mods, plugins, art, and'
            ' memes\n- Report bugs and make feature suggestions\n'
            '- Troubleshoot issues',
            maxwidth=(self._width - 10) / 2,
            color=(1, 1, 1, 1),
            h_align='left',
            v_align='top',
        )

        bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width / 2 - 30, 20),
            size=(self._width / 2 - 60, 60),
            autoselect=True,
            label=bui.Lstr(resource='discordJoinText'),
            text_scale=1.0,
            on_activate_call=bui.Call(
                bui.open_url, 'https://ballistica.net/discord'
            ),
        )

        if self._back_button is not None:
            bui.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

    def _do_back(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
