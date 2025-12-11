# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

from __future__ import annotations

from typing import TYPE_CHECKING, override, assert_never

import bauiv1 as bui

from bacommon.docui import DocUIRequestTypeID, DocUIResponseTypeID
from bauiv1lib.utils import scroll_fade_bottom, scroll_fade_top

if TYPE_CHECKING:
    from typing import Callable

    from bacommon.docui import DocUIRequest, DocUIResponse
    import bacommon.docui.v1
    from bauiv1lib.docui._controller import DocUIController
    from bauiv1lib.docui import v1prep


class DocUIWindow(bui.MainWindow):
    """Window showing doc-ui content."""

    def __init__(
        self,
        controller: DocUIController,
        request: DocUIRequest,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
        restored: bool = False,
        uiopenstateid: str | None = None,
        suppress_win_extra_type_warning: bool = False,
        has_had_response: bool = False,
    ):
        # pylint: disable=too-many-statements
        ui = bui.app.ui_v1

        self._uiopenstate = (
            None if uiopenstateid is None else bui.UIOpenState(uiopenstateid)
        )

        self._locked = False

        self._restored = restored

        # Note: our windows and states both hold strong references to
        # the controller, so we need to make sure the opposite is not
        # true to avoid cycles.
        self.controller = controller

        self._suppress_win_extra_type_warning = suppress_win_extra_type_warning
        self._request = request
        self._request_state_id = self._default_state_id(request)

        self._last_response: DocUIResponse | None = None
        self._last_response_success: bool = False
        self._last_response_shared_state_id: str | None = None
        self._has_had_response: bool = has_had_response

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
            1.45
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

        self._spinner: bui.Widget | None = None

        if not suppress_win_extra_type_warning:
            bui.pushcall(bui.WeakCallStrict(self._sanity_check_win_extra_type))

    def _sanity_check_win_extra_type(self) -> None:
        # There will be lots of windows with this same type, so we really
        # need the user to provide extra-type-ids so our logic can tell
        # all of us apart for navigation purposes.
        if not self.main_window_extra_type_id:
            bui.uilog.warning(
                '%s created by %s was not assigned an extra-type-id.'
                ' Always pass a "win_extra_type_id" when calling'
                ' `auxiliary_window_activate()` with a DocUIWindow.',
                type(self).__name__,
                type(self.controller),
            )

    @property
    def request(self) -> DocUIRequest:
        """The current request.

        Should only be accessed from the logic thread while the ui is
        unlocked.
        """
        assert bui.in_logic_thread()
        if self._request is None:
            raise RuntimeError('No request is set.')
        return self._request

    @request.setter
    def request(self, request: DocUIRequest) -> None:
        assert bui.in_logic_thread()
        self._request = request
        self._request_state_id = self._default_state_id(request)

        # New requests immediately blow away existing responses.
        self._last_response = None
        self._last_response_success = False
        self._last_response_shared_state_id = None

    @classmethod
    def _default_state_id(cls, request: DocUIRequest) -> str:
        """Calc a default state id for a request."""
        requesttypeid = request.get_type_id()
        if requesttypeid is DocUIRequestTypeID.V1:
            import bacommon.docui.v1 as dui1

            # One state per path seems like a reasonable default.
            assert isinstance(request, dui1.Request)
            return request.path
        if requesttypeid is DocUIRequestTypeID.UNKNOWN:
            return 'unknown'
        assert_never(requesttypeid)

    def lock_ui(self, origin_widget: bui.Widget | None = None) -> None:
        """Stop UI interactions during some operation."""
        assert bui.in_logic_thread()
        assert not self._locked

        # If a spinner-position is provided, make the spinner in our
        # subcontainer at the provided spot and have it appear
        # immediately instead of fading (Makes button presses feel more
        # responsive).
        parent = None if origin_widget is None else origin_widget.parent
        if parent is not None:
            assert origin_widget is not None
            self._spinner = bui.spinnerwidget(
                parent=parent,
                position=origin_widget.center,
                size=48,
                fade=False,
            )
        else:
            # Otherwise do one at the center of our window (not in our
            # subcontainer).
            self._spinner = bui.spinnerwidget(
                parent=self._root_widget,
                position=(
                    self._vis_left + self._vis_width * 0.5,
                    self._vis_top - self._vis_height * 0.5,
                ),
                size=48,
                # With restored windows we're likely to have stuff under
                # the spinner. Bomb looks nicer but simple is more
                # readable in those cases.
                style='simple' if self._restored else 'bomb',
            )
        self._locked = True

    def unlock_ui(self) -> None:
        """Resume normal UI interactions."""
        assert bui.in_logic_thread()
        assert self._locked

        if self._spinner:
            self._spinner.delete()
        self._spinner = None
        self._locked = False

    @property
    def locked(self) -> bool:
        """Are we locked?"""
        assert bui.in_logic_thread()
        return self._locked

    @property
    def scroll_width(self) -> float:
        """Width of our scroll area."""
        return self._scroll_width

    @property
    def scroll_height(self) -> float:
        """Height of our scroll area."""
        return self._scroll_height

    def set_last_response(self, response: DocUIResponse, success: bool) -> None:
        """Set a response to a request."""
        assert bui.in_logic_thread()
        assert not self._locked
        self._last_response = response
        self._last_response_success = success
        self._has_had_response = True

        # Grab any custom shared-state-id included in this response.
        responsetypeid = response.get_type_id()
        if responsetypeid is DocUIResponseTypeID.V1:
            import bacommon.docui.v1 as dui1

            assert isinstance(response, dui1.Response)
            self._last_response_shared_state_id = response.shared_state_id
        elif responsetypeid is DocUIResponseTypeID.UNKNOWN:
            self._last_response_shared_state_id = None
        else:
            assert_never(responsetypeid)

    def instantiate_ui(self, pageprep: v1prep.PagePrep) -> None:
        """Replace any current ui with provided prepped one.

        :meta private:
        """
        from bauiv1lib.docui.v1prep._calls import (
            doc_ui_v1_instantiate_page_prep,
        )

        assert bui.in_logic_thread()

        # Set title.
        bui.textwidget(
            edit=self._title,
            literal=not pageprep.title_is_lstr,
            text=pageprep.title,
        )

        # Clear any existing children.
        for child in self._scrollwidget.get_children():
            child.delete()

        if pageprep.rows:
            # Stop showing scroll-widget highlights now that we've got
            # child stuff to be highlighted.
            bui.scrollwidget(
                edit=self._scrollwidget,
                highlight=False,
                simple_culling_v=pageprep.simple_culling_v,
                center_small_content=(pageprep.center_vertically),
            )
            self._subcontainer = doc_ui_v1_instantiate_page_prep(
                pageprep,
                rootwidget=self._root_widget,
                scrollwidget=self._scrollwidget,
                backbutton=(
                    bui.get_special_widget('back_button')
                    if self._back_button is None
                    else self._back_button
                ),
                windowbackbutton=self._back_button,
                window=self,
            )
        else:
            # No child stuff to show so let the scroll-widget highlight.
            bui.scrollwidget(
                edit=self._scrollwidget,
                highlight=True,
                simple_culling_v=0.0,
                center_small_content=True,
            )
            self._subcontainer = None

            bui.textwidget(
                parent=self._scrollwidget,
                h_align='center',
                v_align='center',
                text=bui.Lstr(
                    translate=('serverResponses', 'There is nothing here.')
                ),
                scale=0.75,
                color=(1, 1, 1, 0.5),
                size=(0, 0),
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

        assert bui.in_logic_thread()

        # IMPORTANT - Pull values from self HERE; if we do it in the
        # lambda below it'll keep self alive which will lead to
        # 'ui-not-getting-cleaned-up' warnings and memory leaks.
        auxiliary_style = self._auxiliary_style
        controller = self.controller
        request = self._request
        last_response = self._last_response
        has_had_response = self._has_had_response
        uiopenstateid = (
            None if self._uiopenstate is None else self._uiopenstate.stateid
        )
        suppress_win_extra_type_warning = self._suppress_win_extra_type_warning

        return bui.BasicMainWindowState(
            create_call=(
                lambda transition, origin_widget: controller.restore(
                    cls(
                        controller=controller,
                        request=request,
                        transition=transition,
                        origin_widget=origin_widget,
                        auxiliary_style=auxiliary_style,
                        uiopenstateid=uiopenstateid,
                        suppress_win_extra_type_warning=(
                            suppress_win_extra_type_warning
                        ),
                        restored=True,
                        has_had_response=has_had_response,
                    ),
                    last_response=last_response,
                    has_had_response=has_had_response,
                )
            ),
            uiopenstate=self._uiopenstate,
        )

    @override
    def main_window_do_save_shared_state(self, state: dict) -> None:
        # Give our controller a stab at this.
        self.controller.save_window_shared_state(self, state)

    @override
    def main_window_do_restore_shared_state(self, state: dict) -> None:
        # Give our controller a stab at this.
        self.controller.restore_window_shared_state(self, state)

    @override
    def main_window_should_preserve_selection(self) -> bool:
        return True

    @override
    def get_main_window_shared_state_id(self) -> str | None:
        base_id = (
            self._request_state_id
            if self._last_response_shared_state_id is None
            else self._last_response_shared_state_id
        )

        # Each controller has its own unique domain, so include that in
        # the id.
        ctp = type(self.controller)
        out = f'{ctp.__module__}.{ctp.__qualname__}:{base_id}'
        return out
