# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for Modding Tools."""

from typing import override

# Note: import the submodule explicitly — attribute access on bare
# `babase` only works if something else happened to import it first.
import babase.modutils
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets

from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.config import ConfigCheckBox
from bauiv1lib.utils import get_screen_margins, scroll_fade_top

_devstrs = _classicassets.strings.settings.dev_tools


class DevToolsWindow(bui.MainWindow):
    """Window for accessing modding tools."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        app = bui.app
        assert app.classic is not None

        uiscale = app.ui_v1.uiscale
        self._width = 1200.0 if uiscale is bui.UIScale.SMALL else 670.0
        self._height = (
            800
            if uiscale is bui.UIScale.SMALL
            else 540.0 if uiscale is bui.UIScale.MEDIUM else 624.0
        )
        self._spacing = 32

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        # Slightly reduced scale in small ui so our short list of
        # content requires minimal scrolling on phone-ish aspects.
        scale = (
            1.52
            if uiscale is bui.UIScale.SMALL
            else 1.12 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 80, screensize[0] / scale)
        target_height = min(self._height - 90, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        self._scroll_width = target_width
        self._scroll_height = target_height - 35
        self._scroll_bottom = yoffs - 64 - self._scroll_height

        # In small ui we extend our scrollable area out into the screen
        # margins (space between the virtual bounds and the actual
        # screen edges) while keeping content laid out within the
        # virtual bounds.
        margin_left, margin_right, margin_bottom, margin_top = (
            get_screen_margins(scale)
            if uiscale is bui.UIScale.SMALL
            else (0.0, 0.0, 0.0, 0.0)
        )

        # In small ui we also extend the scroll's top edge all the way
        # up to the top of the screen; soft blobs then keep our title
        # legible over any content scrolled up there. Content gets
        # padded to stay exactly where it would be with the top edge
        # in its standard spot below the title.
        top_extend = (
            (0.5 * self._height + 0.5 * (screensize[1] / scale))
            - (self._scroll_bottom + self._scroll_height)
            + margin_top
            if uiscale is bui.UIScale.SMALL
            else 0.0
        )

        # A bit of extra padding above our content so the soft blobs
        # fading things out under the title don't eat into our top
        # checkbox when scrolled to the top.
        top_pad = 15.0

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 390.0 + margin_bottom + top_extend + top_pad

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        self._r = 'settingsDevTools'

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|back',
                position=(53, yoffs - 50),
                size=(140, 60),
                scale=0.8,
                autoselect=True,
                label=_commonassets.strings.actions.back,
                button_type='back',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        if self._back_button is not None:
            bui.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 - self._scroll_width * 0.5 - margin_left,
                self._scroll_bottom - margin_bottom,
            ),
            simple_culling_v=20.0,
            highlight=False,
            size=(
                self._scroll_width + margin_left + margin_right,
                self._scroll_height + margin_bottom + top_extend,
            ),
            selection_loops_to_parent=True,
            center_small_content_horizontally=True,
            border_opacity=0.4,
        )
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)

        # Our scroll area extends up past our title; these soft blobs
        # (plus the title being drawn after the scroll area) keep the
        # title legible over content scrolled up there. Note that we
        # intentionally use the original un-margin-extended scroll
        # geometry here so the blobs coincide with the title, which
        # doesn't move when we extend out into screen margins.
        if uiscale is bui.UIScale.SMALL:
            scroll_fade_top(
                self._root_widget,
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
                # Nudge the blobs up so their most-opaque core sits
                # just above our title instead of below it.
                yoffs_extra=20.0,
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (60 if uiscale is bui.UIScale.SMALL else 42),
            ),
            size=(0, 25),
            scale=(0.8 if uiscale is bui.UIScale.SMALL else 1.0),
            maxwidth=self._width - 200,
            text=_devstrs.title,
            color=app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            selection_loops_to_parent=True,
        )

        # (start below the top-edge extension plus padding so content
        # sits just below where the soft blobs fade things out).
        v = self._sub_height - top_extend - top_pad - 35
        this_button_width = 410

        v -= self._spacing * 1.9
        # Keep our left edge aligned with the buttons below us no matter
        # how wide the window gets (our sub-width tracks window width at
        # small ui-scale). The extra 10 units visually lines the check
        # box up with the button contents.
        self._show_dev_console_button_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            check_box_id=f'{self.main_window_id_prefix}|showdevsonsole',
            position=(self._sub_width / 2 - this_button_width / 2 + 10, v + 40),
            size=(this_button_width, 30),
            configkey='Show Dev Console Button',
            displayname=_devstrs.show_dev_console_button,
            scale=1.0,
            maxwidth=350,
        )
        if self._back_button is not None:
            bui.widget(
                edit=self._show_dev_console_button_check_box.widget,
                up_widget=self._back_button,
            )

        v -= self._spacing * 1.2
        self._reset_dev_console_button_position_button = bui.buttonwidget(
            parent=self._subcontainer,
            id=f'{self.main_window_id_prefix}|resetdevconsolebuttonposition',
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=_devstrs.reset_button_position,
            text_scale=1.0,
            on_activate_call=self._reset_dev_console_button_position,
        )

        # Extra gap here so the position-reset button above reads as
        # grouped with the dev-console-button checkbox.
        v -= self._spacing * 3.4
        self._create_user_system_scripts_button = bui.buttonwidget(
            parent=self._subcontainer,
            id=f'{self.main_window_id_prefix}|createusersystemscripts',
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=_devstrs.create_user_system_scripts,
            text_scale=1.0,
            on_activate_call=babase.modutils.create_user_system_scripts,
        )

        v -= self._spacing * 2.5
        self._delete_user_system_scripts_button = bui.buttonwidget(
            parent=self._subcontainer,
            id=f'{self.main_window_id_prefix}|deleteusersystemscripts',
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=_devstrs.delete_user_system_scripts,
            text_scale=1.0,
            on_activate_call=lambda: ConfirmWindow(
                action=babase.modutils.delete_user_system_scripts,
            ),
        )

    def _reset_dev_console_button_position(self) -> None:
        # Drop our stored custom position; applying then reverts the
        # button to its default docked spot.
        cfg = bui.app.config
        cfg.pop('Dev Console Button Pos X', None)
        cfg.pop('Dev Console Button Pos Y', None)
        cfg.apply_and_commit()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def main_window_should_preserve_selection(self) -> bool:
        return True

    def _set_uiscale(self, val: str) -> None:
        cfg = bui.app.config
        cfg['UI Scale'] = val
        cfg.apply_and_commit()
        if bui.app.ui_v1.uiscale.name != val.upper():
            bui.screenmessage(
                _commonassets.strings.status.must_restart,
                color=(1.0, 0.5, 0.0),
            )
