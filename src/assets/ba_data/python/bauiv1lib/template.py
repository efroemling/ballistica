# Released under the MIT License. See LICENSE for details.
#
"""Useful starting points for new classes and whatnot."""

from __future__ import annotations

import random
from typing import override

import bauiv1 as bui


def show_template_main_window() -> None:
    """Bust out a template-main-window."""

    # Pop up an auxiliary window wherever we are in the nav stack.
    bui.app.ui_v1.auxiliary_window_activate(
        win_type=TemplateMainWindow,
        win_create_call=lambda: TemplateMainWindow(
            dummy_data=random.randrange(100, 1000)
        ),
    )


class TemplateMainWindow(bui.MainWindow):
    """An example of a well-behaved main-window."""

    def __init__(
        self,
        dummy_data: int,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
    ):
        ui = bui.app.ui_v1

        # A simple number standing in for actual data (to show how we'd
        # save/restore actual data).
        self._dummy_data = dummy_data

        # We want to display differently whether we're an auxiliary
        # window or not, but unfortunately that value is not yet
        # available until we're added to the main-window-stack so it
        # must be explicitly passed in.
        self._auxiliary_style = auxiliary_style

        # Calc scale and size for our backing window. For medium & large
        # ui-scale we aim for a window small enough to always be fully
        # visible on-screen and for small mode we aim for a window big
        # enough that we never see the window edges; only the window
        # texture covering the whole screen.
        uiscale = ui.uiscale
        self._width = 1400 if uiscale is bui.UIScale.SMALL else 750
        self._height = 1200 if uiscale is bui.UIScale.SMALL else 500
        scale = (
            1.5
            if uiscale is bui.UIScale.SMALL
            else 1.2 if uiscale is bui.UIScale.MEDIUM else 1.0
        )

        # Do some fancy math to calculate our visible area; this will be
        # limited by the screen size in small mode and our backing size
        # otherwise.
        screensize = bui.get_virtual_screen_size()
        self._vis_width = min(self._width - 100, screensize[0] / scale)
        self._vis_height = min(self._height - 100, screensize[1] / scale)
        self._vis_top = 0.5 * self._height + 0.5 * self._vis_height
        self._vis_left = 0.5 * self._width - 0.5 * self._vis_width

        # Nudge our vis area up a bit when we can see the full backing
        # (visual fudge factor).
        if uiscale is not bui.UIScale.SMALL:
            self._vis_top += 12.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility='menu_full',
                toolbar_cancel_button_style=(
                    'close' if auxiliary_style else 'back'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We respond to screen size changes only at small ui-scale;
            # in other cases we assume our window remains fully visible
            # always (flip to windowed mode and resize the app window to
            # confirm this).
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        # Title.
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._vis_top - 20),
            size=(0, 0),
            text=f'Template{self._dummy_data}',
            color=ui.title_color,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 1.0,
            # Make sure we avoid overlapping meters in small mode/etc.
            maxwidth=(130 if uiscale is bui.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )

        # For small UI-scale we use the system back/close button;
        # otherwise we make our own.
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|close',
                scale=0.8,
                position=(self._vis_left - 15, self._vis_top - 30),
                size=(50, 50) if auxiliary_style else (60, 55),
                extra_touch_border_scale=2.0,
                button_type=None if auxiliary_style else 'backSmall',
                on_activate_call=self.main_window_back,
                autoselect=True,
                label=bui.charstr(
                    bui.SpecialChar.CLOSE
                    if auxiliary_style
                    else bui.SpecialChar.BACK
                ),
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        # Show our vis-area bounds (for debugging).
        if bool(True):
            # Skip top-left since its always overlapping back/close
            # buttons.
            if bool(False):
                bui.textwidget(
                    parent=self._root_widget,
                    position=(self._vis_left, self._vis_top),
                    size=(0, 0),
                    color=(1, 1, 1, 0.5),
                    scale=0.5,
                    text='TL',
                    h_align='left',
                    v_align='top',
                )
            bui.textwidget(
                parent=self._root_widget,
                position=(self._vis_left + self._vis_width, self._vis_top),
                size=(0, 0),
                color=(1, 1, 1, 0.5),
                scale=0.5,
                text='TR',
                h_align='right',
                v_align='top',
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(self._vis_left, self._vis_top - self._vis_height),
                size=(0, 0),
                color=(1, 1, 1, 0.5),
                scale=0.5,
                text='BL',
                h_align='left',
                v_align='bottom',
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._vis_left + self._vis_width,
                    self._vis_top - self._vis_height,
                ),
                size=(0, 0),
                scale=0.5,
                color=(1, 1, 1, 0.5),
                text='BR',
                h_align='right',
                v_align='bottom',
            )

        # Description.
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._vis_top - 100),
            size=(0, 0),
            scale=0.6,
            text=(
                f'Use this class as reference for making'
                f' a well-behaved MainWindow class or for\n'
                'navigating between MainWindows. It lives at'
                f' {self.__module__}.{type(self).__qualname__}.\n'
                f'vis-size=({round(self._vis_width)},'
                f' {round(self._vis_height)})'
            ),
            h_align='center',
            v_align='center',
        )

        # Make a few buttons to navigate to other MainWindows (simply
        # our same class with random different dummy values).
        button_width = 300
        for i in range(3):
            child_dummy_data = self._dummy_data + (i + 1) * 17
            self._player_profiles_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|button{i + 1}',
                position=(
                    self._width * 0.5 - button_width * 0.5,
                    self._vis_top - 230 - i * 80,
                ),
                autoselect=True,
                size=(button_width, 60),
                label=f'Template{child_dummy_data}',
                on_activate_call=bui.WeakCallStrict(
                    self._child_press, child_dummy_data
                ),
            )

    def _child_press(self, dummy_data: int) -> None:
        # Navigate to a new one of us.
        self.main_window_replace(
            lambda: TemplateMainWindow(
                auxiliary_style=False, dummy_data=dummy_data
            )
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # IMPORTANT - Pull values from self HERE; if we do it in the
        # lambda below then the state will keep self alive which will
        # lead to 'ui-not-getting-cleaned-up' warnings and memory leaks.
        dummy_data = self._dummy_data
        auxiliary_style = self._auxiliary_style

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                dummy_data=dummy_data,
                auxiliary_style=auxiliary_style,
            ),
        )

    @override
    def main_window_should_preserve_selection(self) -> bool:
        # If we return True here, the app will reselect the last
        # selected widget when creating a new one of our windows. We
        # just need to make sure all of our selectable widgets have
        # unique ids starting with `self.main_window_id_prefix`.
        return True

    @override
    def get_main_window_shared_state_id(self) -> str | None:
        # Here we return a unique id based on what we're displaying.
        # This means each level will remember its selected button. If we
        # remove this function override we get the default behavior
        # where this state is shared for all instances of our class
        # (thus selecting the second button will go to a new window with
        # the second button already selected).
        return f'template{self._dummy_data}'
