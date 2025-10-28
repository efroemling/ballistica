# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import bauiv1 as bui

from bauiv1lib.utils import scroll_fade_bottom, scroll_fade_top
from bauiv1lib.cloudui._prep import CloudUIPagePrep

if TYPE_CHECKING:
    from typing import Callable

    import bacommon.cloudui.v1 as clui
    from bauiv1lib.cloudui._controller import CloudUIController


class CloudUIWindow(bui.MainWindow):
    """UI provided by the cloud."""

    @dataclass
    class State:
        """Final state window can be set to show."""

        controller: CloudUIController
        page: clui.Page

    def __init__(
        self,
        state: State | None,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
    ):
        ui = bui.app.ui_v1

        self._state: CloudUIWindow.State | None = None

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
        self._width = (
            1400
            if uiscale is bui.UIScale.SMALL
            else 1100 if uiscale is bui.UIScale.MEDIUM else 1200
        )
        self._height = (
            1200
            if uiscale is bui.UIScale.SMALL
            else 700 if uiscale is bui.UIScale.MEDIUM else 800
        )
        self._root_scale = (
            1.5
            if uiscale is bui.UIScale.SMALL
            else 0.9 if uiscale is bui.UIScale.MEDIUM else 0.8
        )

        # Do some fancy math to calculate our visible area; this will be
        # limited by the screen size in small mode and our backing size
        # otherwise.
        screensize = bui.get_virtual_screen_size()
        self._vis_width = min(
            self._width - 150, screensize[0] / self._root_scale
        )
        self._vis_height = min(
            self._height - 80, screensize[1] / self._root_scale
        )
        self._vis_top = 0.5 * self._height + 0.5 * self._vis_height
        self._vis_left = 0.5 * self._width - 0.5 * self._vis_width

        self._scroll_width = self._vis_width
        self._scroll_left = self._vis_left + 0.5 * (
            self._vis_width - self._scroll_width
        )
        # Go with full-screen scrollable aread in small ui.
        self._scroll_height = self._vis_height - (
            -1 if uiscale is bui.UIScale.SMALL else 43
        )
        self._scroll_bottom = (
            self._vis_top
            - (-1 if uiscale is bui.UIScale.SMALL else 32)
            - self._scroll_height
        )

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
                scale=self._root_scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We respond to screen size changes only at small ui-scale;
            # in other cases we assume our window remains fully visible
            # always (flip to windowed mode and resize the app window to
            # confirm this).
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
        # Avoid complaints if nothing is selected under us.
        bui.widget(edit=self._root_widget, allow_preserve_selection=False)

        self._subcontainer: bui.Widget | None = None

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=True,  # Will turn off once we have UI.
            size=(self._scroll_width, self._scroll_height),
            position=(self._scroll_left, self._scroll_bottom),
            border_opacity=0.4,
            center_small_content_horizontally=True,
            claims_left_right=True,
        )
        # Avoid having to deal with selecting this while its empty.
        # bui.containerwidget(edit=self._scrollwidget, selectable=False)
        bui.widget(edit=self._scrollwidget, autoselect=True)

        # With full-screen scrolling, fade content as it approaches
        # toolbars.
        if uiscale is bui.UIScale.SMALL and bool(True):
            scroll_fade_top(
                self._root_widget,
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
            )
            scroll_fade_bottom(
                self._root_widget,
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
            )

        # Title.
        self._title = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._vis_top - 20),
            size=(0, 0),
            text='',
            color=ui.title_color,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 1.0,
            # Make sure we avoid overlapping meters in small mode.
            maxwidth=(130 if uiscale is bui.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )
        # Needed to display properly over scrolled content.
        bui.widget(edit=self._title, depth_range=(0.9, 1.0))

        # For small UI-scale we use the system back/close button;
        # otherwise we make our own.
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button: bui.Widget | None = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|close',
                scale=0.8,
                position=(self._vis_left + 2, self._vis_top - 35),
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
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        # Show our vis-area bounds (for debugging).
        if bool(False):
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

        self._spinner: bui.Widget | None = bui.spinnerwidget(
            parent=self._root_widget,
            position=(
                self._vis_left + self._vis_width * 0.5,
                self._vis_top - self._vis_height * 0.5,
            ),
            size=48,
            style='bomb',
        )

        if state is not None:
            self.set_state(state, immediate=True)

    def set_state(self, state: State, immediate: bool = False) -> None:
        """Set a final state (error or page contents).

        This state may be instantly restored if the window is recreated
        (depending on cache lifespan/etc.)
        """
        assert bui.in_logic_thread()

        assert self._state is None
        self._state = state

        ui = bui.app.ui_v1
        uiscale = ui.uiscale

        if self._spinner:
            self._spinner.delete()
            self._spinner = None

        # Ok; we've got content.
        bui.textwidget(
            edit=self._title,
            literal=not state.page.title_is_lstr,
            text=state.page.title,
        )

        # Make sure there's at least one row and that all rows contain
        # at least one button. Otherwise show a 'nothing here' message.
        if not state.page.rows or not all(
            row.buttons for row in state.page.rows
        ):
            bui.uilog.exception(
                'Got invalid cloud-ui state;'
                ' must contain at least one row'
                ' and all rows must contain buttons.'
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._vis_left + 0.5 * self._vis_width,
                    self._vis_top - 0.5 * self._vis_height,
                ),
                size=(0, 0),
                scale=0.6,
                text=bui.Lstr(
                    translate=('serverResponses', 'There is nothing here.')
                ),
                h_align='center',
                v_align='center',
            )
            return

        pageprep = CloudUIPagePrep(
            state.page,
            uiscale,
            self._scroll_width,
            immediate=immediate,
            idprefix=self.main_window_id_prefix,
        )

        # We left highlighting on so the user could see something if
        # selecting our empty window, but let's kill it now that we're
        # no longer empty.
        bui.scrollwidget(edit=self._scrollwidget, highlight=False)

        bui.scrollwidget(
            edit=self._scrollwidget,
            simple_culling_v=pageprep.simple_culling_v,
            center_small_content=state.page.center_vertically,
        )

        self._subcontainer = pageprep.instantiate(
            self._scrollwidget,
            backbutton=(
                bui.get_special_widget('back_button')
                if self._back_button is None
                else self._back_button
            ),
            windowbackbutton=self._back_button,
        )

        # Most of our UI won't exist until this point so we need to
        # explicitly restore state for selection restore to work.
        #
        # Note to self: perhaps we should *not* do this if significant
        # time has passed since the window was made or if input commands
        # have happened.
        self.main_window_restore_shared_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # IMPORTANT - Pull values from self HERE; if we do it in the
        # lambda below it'll keep self alive which will lead to
        # 'ui-not-getting-cleaned-up' warnings and memory leaks.
        auxiliary_style = self._auxiliary_style
        state = self._state

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                state=state,
                transition=transition,
                origin_widget=origin_widget,
                auxiliary_style=auxiliary_style,
            ),
        )

    @override
    def main_window_should_preserve_selection(self) -> bool:
        return True

    @override
    def get_main_window_shared_state_id(self) -> str | None:
        return 'cloudui'
