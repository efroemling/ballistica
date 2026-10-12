# Released under the MIT License. See LICENSE for details.
#
"""The text popups doc-ui buttons can show."""

from typing import TYPE_CHECKING, override

import bauiv1 as bui
from bauiv1 import _commonassets

from bauiv1lib.popup import PopupWindow
from bauiv1lib.docui._layout import popup_scale
from bauiv1lib.docui.prep._calls2 import POPUP_TEXT_SCALE

if TYPE_CHECKING:
    from bauiv1lib.docui.prep import PopupTextPrep

# Space around the text, and the ok button under it.
_MARGIN_X = 40.0
_MARGIN_TOP = 35.0
_MARGIN_BOTTOM = 25.0
_TEXT_BUTTON_SPACING = 25.0
_BUTTON_SIZE = (140.0, 50.0)

_BG_COLOR = (0.45, 0.4, 0.6)


class DocUIPopupTextWindow(PopupWindow):
    """The popup shown by a doc-ui button with a popup-text action.

    Sized to fit its text, with an ok button below it; the ok button,
    a press outside the popup, or a back/escape closes it.
    """

    def __init__(self, button: bui.Widget, popup: PopupTextPrep) -> None:
        self._transitioning_out = False
        width = max(popup.width, _BUTTON_SIZE[0]) + _MARGIN_X * 2.0
        height = (
            _MARGIN_TOP
            + popup.height
            + _TEXT_BUTTON_SPACING
            + _BUTTON_SIZE[1]
            + _MARGIN_BOTTOM
        )
        super().__init__(
            position=button.get_screen_space_center(),
            size=(width, height),
            scale=popup_scale(),
            bg_color=_BG_COLOR,
            toolbar_visibility='inherit',
        )
        bui.textwidget(
            parent=self.root_widget,
            size=(0, 0),
            position=(width * 0.5, height - _MARGIN_TOP),
            h_align='center',
            v_align='top',
            scale=POPUP_TEXT_SCALE,
            # (Wrapped and measured in prep to fit exactly; width is
            # just a safety net, but height squishes text taller than
            # prep's cap.)
            maxwidth=width - _MARGIN_X,
            max_height=popup.height,
            text=popup.text,
        )
        okbutton = bui.buttonwidget(
            parent=self.root_widget,
            id=f'{self._idprefix}|ok',
            position=(
                width * 0.5 - _BUTTON_SIZE[0] * 0.5,
                _MARGIN_BOTTOM,
            ),
            size=_BUTTON_SIZE,
            color=_BG_COLOR,
            textcolor=(0.9, 0.9, 0.9),
            label=_commonassets.strings.actions.ok,
            autoselect=True,
            on_activate_call=self._on_ok_press,
        )
        bui.containerwidget(
            edit=self.root_widget,
            selected_child=okbutton,
            start_button=okbutton,
        )

    def _on_ok_press(self) -> None:
        bui.play_swish()
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        bui.play_swish()
        self._transition_out()
