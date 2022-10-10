# Released under the MIT License. See LICENSE for details.
#
"""UI related to reporting bad behavior/etc."""

from __future__ import annotations

import ba
import ba.internal


class ReportPlayerWindow(ba.Window):
    """Player for reporting naughty players."""

    def __init__(self, account_id: str, origin_widget: ba.Widget):
        self._width = 550
        self._height = 220
        self._account_id = account_id
        self._transition_out = 'out_scale'
        scale_origin = origin_widget.get_screen_space_center()

        overlay_stack = ba.internal.get_special_widget('overlay_stack')
        uiscale = ba.app.ui.uiscale
        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height),
                parent=overlay_stack,
                transition='in_scale',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    1.8
                    if uiscale is ba.UIScale.SMALL
                    else 1.35
                    if uiscale is ba.UIScale.MEDIUM
                    else 1.0
                ),
            )
        )
        self._cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(40, self._height - 50),
            size=(50, 50),
            label='',
            on_activate_call=self.close,
            autoselect=True,
            color=(0.4, 0.4, 0.5),
            icon=ba.gettexture('crossOut'),
            iconscale=1.2,
        )
        ba.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.64),
            size=(0, 0),
            color=(1, 1, 1, 0.8),
            scale=1.2,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='reportThisPlayerReasonText'),
            maxwidth=self._width * 0.85,
        )
        ba.buttonwidget(
            parent=self._root_widget,
            size=(235, 60),
            position=(20, 30),
            label=ba.Lstr(resource='reportThisPlayerLanguageText'),
            on_activate_call=self._on_language_press,
            autoselect=True,
        )
        ba.buttonwidget(
            parent=self._root_widget,
            size=(235, 60),
            position=(self._width - 255, 30),
            label=ba.Lstr(resource='reportThisPlayerCheatingText'),
            on_activate_call=self._on_cheating_press,
            autoselect=True,
        )

    def _on_language_press(self) -> None:
        from urllib import parse

        ba.internal.add_transaction(
            {
                'type': 'REPORT_ACCOUNT',
                'reason': 'language',
                'account': self._account_id,
            }
        )
        body = ba.Lstr(resource='reportPlayerExplanationText').evaluate()
        ba.open_url(
            'mailto:support@froemling.net'
            f'?subject={ba.internal.appnameupper()} Player Report: '
            + self._account_id
            + '&body='
            + parse.quote(body)
        )
        self.close()

    def _on_cheating_press(self) -> None:
        from urllib import parse

        ba.internal.add_transaction(
            {
                'type': 'REPORT_ACCOUNT',
                'reason': 'cheating',
                'account': self._account_id,
            }
        )
        body = ba.Lstr(resource='reportPlayerExplanationText').evaluate()
        ba.open_url(
            'mailto:support@froemling.net'
            f'?subject={ba.internal.appnameupper()} Player Report: '
            + self._account_id
            + '&body='
            + parse.quote(body)
        )
        self.close()

    def close(self) -> None:
        """Close the window."""
        ba.containerwidget(edit=self._root_widget, transition='out_scale')
