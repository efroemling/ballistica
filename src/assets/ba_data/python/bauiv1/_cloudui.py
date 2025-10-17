# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, override, Annotated

from efro.dataclassio import ioprepped, IOAttrs
import babase
from bauiv1._window import MainWindow, BasicMainWindowState
import _bauiv1


if TYPE_CHECKING:
    from bauiv1._window import MainWindowState


def show_cloud_ui_window() -> None:
    """Bust out a cloud-ui window."""

    # Pop up an auxiliary window wherever we are in the nav stack.
    babase.app.ui_v1.auxiliary_window_activate(
        win_type=CloudUIWindow,
        win_create_call=lambda: CloudUIWindow(state=None),
    )


@ioprepped
@dataclass
class CloudUIButton:
    """Represents a button in a cloud-ui."""


@ioprepped
@dataclass
class CloudUIRow:
    """Represents a row in a cloud-ui."""

    buttons: Annotated[list[CloudUIButton], IOAttrs('b')]


@ioprepped
@dataclass
class CloudUIRoot:
    """Represents an entire cloud-ui."""

    title: Annotated[str, IOAttrs('t')]
    rows: Annotated[list[CloudUIRow], IOAttrs('r')]


class CloudUIWindow(MainWindow):
    """An example of a well-behaved main-window."""

    @dataclass
    class _State:
        root: CloudUIRoot | None

    def __init__(
        self,
        state: _State | None,
        *,
        transition: str | None = 'in_right',
        origin_widget: _bauiv1.Widget | None = None,
        auxiliary_style: bool = True,
    ):
        ui = babase.app.ui_v1

        self._state: CloudUIWindow._State | None = None

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
        self._width = 1400 if uiscale is babase.UIScale.SMALL else 750
        self._height = 1200 if uiscale is babase.UIScale.SMALL else 500
        scale = (
            1.5
            if uiscale is babase.UIScale.SMALL
            else 1.2 if uiscale is babase.UIScale.MEDIUM else 1.0
        )

        # Do some fancy math to calculate our visible area; this will be
        # limited by the screen size in small mode and our backing size
        # otherwise.
        screensize = babase.get_virtual_screen_size()
        self._vis_width = min(self._width - 100, screensize[0] / scale)
        self._vis_height = min(self._height - 100, screensize[1] / scale)
        self._vis_top = 0.5 * self._height + 0.5 * self._vis_height
        self._vis_left = 0.5 * self._width - 0.5 * self._vis_width

        # Nudge our vis area up a bit when we can see the full backing
        # (visual fudge factor).
        if uiscale is not babase.UIScale.SMALL:
            self._vis_top += 12.0

        super().__init__(
            root_widget=_bauiv1.containerwidget(
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
            refresh_on_screen_size_changes=uiscale is babase.UIScale.SMALL,
        )
        # Avoid complaints if nothing is selected under us.
        _bauiv1.widget(edit=self._root_widget, allow_preserve_selection=False)

        # Title.
        self._title = _bauiv1.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._vis_top - 20),
            size=(0, 0),
            text='',
            color=ui.title_color,
            scale=0.9 if uiscale is babase.UIScale.SMALL else 1.0,
            # Make sure we avoid overlapping meters in small mode.
            maxwidth=(130 if uiscale is babase.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )

        # For small UI-scale we use the system back/close button;
        # otherwise we make our own.
        if uiscale is babase.UIScale.SMALL:
            _bauiv1.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = _bauiv1.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|close',
                scale=0.8,
                position=(self._vis_left - 15, self._vis_top - 30),
                size=(50, 50) if auxiliary_style else (60, 55),
                extra_touch_border_scale=2.0,
                button_type=None if auxiliary_style else 'backSmall',
                on_activate_call=self.main_window_back,
                autoselect=True,
                label=babase.charstr(
                    babase.SpecialChar.CLOSE
                    if auxiliary_style
                    else babase.SpecialChar.BACK
                ),
            )
            _bauiv1.containerwidget(edit=self._root_widget, cancel_button=btn)

        # Show our vis-area bounds (for debugging).
        if bool(True):
            # Skip top-left since its always overlapping back/close
            # buttons.
            if bool(False):
                _bauiv1.textwidget(
                    parent=self._root_widget,
                    position=(self._vis_left, self._vis_top),
                    size=(0, 0),
                    color=(1, 1, 1, 0.5),
                    scale=0.5,
                    text='TL',
                    h_align='left',
                    v_align='top',
                )
            _bauiv1.textwidget(
                parent=self._root_widget,
                position=(self._vis_left + self._vis_width, self._vis_top),
                size=(0, 0),
                color=(1, 1, 1, 0.5),
                scale=0.5,
                text='TR',
                h_align='right',
                v_align='top',
            )
            _bauiv1.textwidget(
                parent=self._root_widget,
                position=(self._vis_left, self._vis_top - self._vis_height),
                size=(0, 0),
                color=(1, 1, 1, 0.5),
                scale=0.5,
                text='BL',
                h_align='left',
                v_align='bottom',
            )
            _bauiv1.textwidget(
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

        self._spinner: _bauiv1.Widget | None = _bauiv1.spinnerwidget(
            parent=self._root_widget,
            position=(
                self._vis_left + self._vis_width * 0.5,
                self._vis_top - self._vis_height * 0.5,
            ),
            size=48,
            style='bomb',
        )

        if state is not None:
            self._set_state(state)
        else:
            if random.random() < 0.3:
                babase.apptimer(1.0, babase.WeakCall(self._on_error_response))
            else:
                babase.apptimer(1.0, babase.WeakCall(self._on_response))

    def _on_error_response(self) -> None:
        self._set_state(self._State(None))

    def _on_response(self) -> None:
        self._set_state(self._State(CloudUIRoot(title='Testing', rows=[])))

    def _set_state(self, state: _State) -> None:
        """Set a final state (error or page contents).

        This state may be instantly restored if the window is recreated
        (depending on cache lifespan/etc.)
        """

        assert self._state is None
        self._state = state

        if self._spinner:
            self._spinner.delete()
            self._spinner = None

        if self._state.root is None:
            _bauiv1.textwidget(
                edit=self._title,
                literal=False,  # Allow Lstr.
                text=babase.Lstr(resource='errorText'),
            )
            _bauiv1.textwidget(
                parent=self._root_widget,
                position=(
                    self._vis_left + 0.5 * self._vis_width,
                    self._vis_top - 0.5 * self._vis_height,
                ),
                size=(0, 0),
                scale=0.6,
                text=babase.Lstr(resource='store.loadErrorText'),
                h_align='center',
                v_align='center',
            )
        else:
            _bauiv1.textwidget(
                edit=self._title,
                literal=True,  # Never interpret as Lstr.
                text=self._state.root.title,
            )

    @override
    def get_main_window_state(self) -> MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # IMPORTANT - Pull values from self HERE; if we do it in the
        # lambda below it'll keep self alive which will lead to
        # 'ui-not-getting-cleaned-up' warnings and memory leaks.
        auxiliary_style = self._auxiliary_style
        state = self._state

        return BasicMainWindowState(
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
