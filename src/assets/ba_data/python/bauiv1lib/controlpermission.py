# Released under the MIT License. See LICENSE for details.
#
"""Asking whether an outside party may control this app."""

from typing import TYPE_CHECKING

import bauiv1 as bui
from bauiv1 import _commonassets

if TYPE_CHECKING:
    from typing import Callable


class ControlPermissionWindow:
    """Puts a request to control this app in front of the user.

    Answers exactly once, whatever happens to the window: dismissing
    it counts as a refusal, because 'they walked away' and 'they said
    no' should not lead to different amounts of access.
    """

    def __init__(
        self,
        *,
        on_result: Callable[[bool, bool], None],
        allow_remember: bool,
    ):
        """Ask, and report back ``(allowed, remember)``.

        ``allow_remember`` says whether we can recognize this
        requester again; without that, offering to remember them
        would be a promise we can't keep, so the button is left off.
        """
        self._on_result = on_result
        self._answered = False

        # We deliberately don't name the requester, even though the
        # request carries a vouched-for account tag. Reaching a device
        # requires owning it, so that tag is always the viewer's own --
        # showing it says nothing, and implying there is a choice of
        # who might be asking is worse than saying nothing.
        strings = _commonassets.strings
        text = strings.control.requesting_control_anonymous

        width = 620.0
        height = 210.0

        uiscale = bui.app.ui_v1.uiscale
        self.root_widget = bui.containerwidget(
            size=(width, height),
            transition='in_scale',
            toolbar_visibility='menu_minimal_no_back',
            parent=bui.get_special_widget('overlay_stack'),
            scale=(
                1.7
                if uiscale is bui.UIScale.SMALL
                else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
            ),
            darken_behind=True,
        )

        bui.textwidget(
            parent=self.root_widget,
            position=(width * 0.5, height - 55),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=text,
            scale=1.1,
            maxwidth=width * 0.9,
            # Height cap as well as width: a long translation (or a
            # long account tag substituted into it) wraps rather than
            # running off the side, and wrapping is what would push it
            # down into the explanation and the buttons.
            max_height=55,
        )
        bui.textwidget(
            parent=self.root_widget,
            position=(width * 0.5, height - 100),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=strings.control.control_means,
            scale=0.75,
            color=(0.7, 0.7, 0.75),
            maxwidth=width * 0.9,
            max_height=34,
        )

        # Deny sits apart from the two allowing buttons, and is what
        # a back/cancel press hits -- the safe answer should be the
        # one you land on by accident.
        denybtn = bui.buttonwidget(
            parent=self.root_widget,
            autoselect=True,
            position=(25, 25),
            size=(160, 55),
            label=strings.actions.deny,
            on_activate_call=lambda: self._finish(
                allowed=False, remember=False
            ),
        )
        bui.containerwidget(edit=self.root_widget, cancel_button=denybtn)

        allowbtn = bui.buttonwidget(
            parent=self.root_widget,
            autoselect=True,
            position=(width - 185, 25),
            size=(160, 55),
            label=strings.actions.allow,
            on_activate_call=lambda: self._finish(allowed=True, remember=False),
        )

        if allow_remember:
            bui.buttonwidget(
                parent=self.root_widget,
                autoselect=True,
                position=(width * 0.5 - 105, 25),
                size=(210, 55),
                label=strings.actions.always_allow,
                on_activate_call=lambda: self._finish(
                    allowed=True, remember=True
                ),
            )

        bui.containerwidget(
            edit=self.root_widget,
            selected_child=denybtn,
            start_button=allowbtn,
        )

    def _finish(self, *, allowed: bool, remember: bool) -> None:
        """Report the answer and close, once."""
        if self._answered:
            return
        self._answered = True
        if self.root_widget:
            bui.containerwidget(edit=self.root_widget, transition='out_scale')
        self._on_result(allowed, remember)
