# Released under the MIT License. See LICENSE for details.
#
"""UI related to reporting bad behavior/etc."""

from __future__ import annotations

import bauiv1 as bui


class ReportPlayerWindow(bui.Window):
    """Player for reporting naughty players."""

    def __init__(self, account_id: str, origin_widget: bui.Widget):
        self._width = 550
        self._height = 220
        self._account_id = account_id
        self._transition_out = 'out_scale'
        scale_origin = origin_widget.get_screen_space_center()

        overlay_stack = bui.get_special_widget('overlay_stack')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                parent=overlay_stack,
                transition='in_scale',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    1.8
                    if uiscale is bui.UIScale.SMALL
                    else 1.35 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
            )
        )
        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(40, self._height - 50),
            size=(50, 50),
            label='',
            on_activate_call=self.close,
            autoselect=True,
            color=(0.4, 0.4, 0.5),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )
        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.64),
            size=(0, 0),
            color=(1, 1, 1, 0.8),
            scale=1.2,
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='reportThisPlayerReasonText'),
            maxwidth=self._width * 0.85,
        )
        bui.buttonwidget(
            parent=self._root_widget,
            size=(235, 60),
            position=(20, 30),
            label=bui.Lstr(resource='reportThisPlayerLanguageText'),
            on_activate_call=self._on_language_press,
            autoselect=True,
        )
        bui.buttonwidget(
            parent=self._root_widget,
            size=(235, 60),
            position=(self._width - 255, 30),
            label=bui.Lstr(resource='reportThisPlayerCheatingText'),
            on_activate_call=self._on_cheating_press,
            autoselect=True,
        )

    def _on_language_press(self) -> None:
        from urllib import parse

        plus = bui.app.plus
        assert plus is not None

        plus.add_v1_account_transaction(
            {
                'type': 'REPORT_ACCOUNT',
                'reason': 'language',
                'account': self._account_id,
            }
        )
        body = bui.Lstr(resource='reportPlayerExplanationText').evaluate()
        bui.open_url(
            'mailto:support@froemling.net'
            f'?subject={bui.appnameupper()} Player Report: '
            + self._account_id
            + '&body='
            + parse.quote(body)
        )
        self.close()

    def _on_cheating_press(self) -> None:
        from urllib import parse

        plus = bui.app.plus
        assert plus is not None

        plus.add_v1_account_transaction(
            {
                'type': 'REPORT_ACCOUNT',
                'reason': 'cheating',
                'account': self._account_id,
            }
        )
        body = bui.Lstr(resource='reportPlayerExplanationText').evaluate()
        bui.open_url(
            'mailto:support@froemling.net'
            f'?subject={bui.appnameupper()} Player Report: '
            + self._account_id
            + '&body='
            + parse.quote(body)
        )
        self.close()

    def close(self) -> None:
        """Close the window."""
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
