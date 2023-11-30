# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for entering promo codes."""

from __future__ import annotations

import time

import bauiv1 as bui


class PromoCodeWindow(bui.Window):
    """Window for entering promo codes."""

    def __init__(
        self, modal: bool = False, origin_widget: bui.Widget | None = None
    ):
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
            transition = 'in_right'

        width = 450
        height = 330

        self._modal = modal
        self._r = 'promoCodeWindow'

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition=transition,
                toolbar_visibility='menu_minimal_no_back',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    2.0
                    if uiscale is bui.UIScale.SMALL
                    else 1.5
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
            )
        )

        btn = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.5,
            position=(40, height - 40),
            size=(60, 60),
            label='',
            on_activate_call=self._do_back,
            autoselect=True,
            color=(0.55, 0.5, 0.6),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        v = height - 74
        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource='codesExplainText'),
            maxwidth=width * 0.9,
            position=(width * 0.5, v),
            color=(0.7, 0.7, 0.7, 1.0),
            size=(0, 0),
            scale=0.8,
            h_align='center',
            v_align='center',
        )
        v -= 60

        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(
                resource='supportEmailText',
                subs=[('${EMAIL}', 'support@froemling.net')],
            ),
            maxwidth=width * 0.9,
            position=(width * 0.5, v),
            color=(0.7, 0.7, 0.7, 1.0),
            size=(0, 0),
            scale=0.65,
            h_align='center',
            v_align='center',
        )

        v -= 80

        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource=self._r + '.codeText'),
            position=(22, v),
            color=(0.8, 0.8, 0.8, 1.0),
            size=(90, 30),
            h_align='right',
        )
        v -= 8

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(125, v),
            size=(280, 46),
            text='',
            h_align='left',
            v_align='center',
            max_chars=64,
            color=(0.9, 0.9, 0.9, 1.0),
            description=bui.Lstr(resource=self._r + '.codeText'),
            editable=True,
            padding=4,
            on_return_press_call=self._activate_enter_button,
        )
        bui.widget(edit=btn, down_widget=self._text_field)

        v -= 79
        b_width = 200
        self._enter_button = btn2 = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.5 - b_width * 0.5, v),
            size=(b_width, 60),
            scale=1.0,
            label=bui.Lstr(
                resource='submitText', fallback_resource=self._r + '.enterText'
            ),
            on_activate_call=self._do_enter,
        )
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=btn,
            start_button=btn2,
            selected_child=self._text_field,
        )

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        if not self._modal:
            assert bui.app.classic is not None
            bui.app.ui_v1.set_main_menu_window(
                AdvancedSettingsWindow(transition='in_left').get_root_widget(),
                from_window=self._root_widget,
            )

    def _activate_enter_button(self) -> None:
        self._enter_button.activate()

    def _do_enter(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        plus = bui.app.plus
        assert plus is not None

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        if not self._modal:
            assert bui.app.classic is not None
            bui.app.ui_v1.set_main_menu_window(
                AdvancedSettingsWindow(transition='in_left').get_root_widget(),
                from_window=self._root_widget,
            )
        plus.add_v1_account_transaction(
            {
                'type': 'PROMO_CODE',
                'expire_time': time.time() + 5,
                'code': bui.textwidget(query=self._text_field),
            }
        )
        plus.run_v1_account_transactions()
