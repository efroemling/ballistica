# Released under the MIT License. See LICENSE for details.
#
"""The dev console's UI tab."""

from functools import partial
from typing import TYPE_CHECKING, override

from bacommon.text import SpecialChar
import _babase

from babase._devconsole import DevConsoleTab

if TYPE_CHECKING:
    from babase._devconsole import DevConsoleToggleDef

# Tabs taller than this are showing in the console's expanded view (the
# small view is 100 high).
_EXPANDED_MIN_HEIGHT = 150.0

# Kinds :func:`_babase.set_debug_bounds` takes, with their button labels.
_DEBUG_BOUNDS_KINDS = (
    ('name_depictions', 'Name Depictions'),
    ('image_depictions', 'Image Depictions'),
    ('character_icon_depictions', 'Character Icons'),
)


class DevConsoleTabUI(DevConsoleTab):
    """Tab to debug/test UI stuff."""

    @override
    def refresh(self) -> None:
        from babase._generated.enums import UIScale

        # Chosen so the row of fixed elements (toggles + UI-Scale; they
        # span x 10..861) sits centered; the custom-button adjustment
        # below keeps it that way when app-modes add buttons.
        xoffs = -435.0
        yoffs = 10.0

        custom_buttons = _babase.app.mode.get_dev_console_ui_tab_buttons()
        cboffs = 30
        cbwidth = 170
        cbspacing = 10

        # Every button on this tab shares a height and bottom edge so the
        # row reads as one strip. Button pos is the bottom-left corner,
        # so these two together are what line them up.
        bheight = 40.0
        by = yoffs + 5

        if custom_buttons:
            cbtotalwidth = (
                len(custom_buttons) * cbwidth
                + max(0, len(custom_buttons) - 1) * cbspacing
                + cboffs
            )
        else:
            cbtotalwidth = 0

        xoffs -= cbtotalwidth * 0.5

        self.text(
            'UI should respond dynamically to virtual bounds or fit in'
            ' virtual safe area if static, and should not look broken'
            ' with max margins on.',
            scale=0.6,
            pos=(xoffs + 8, yoffs + 65),
            h_align='left',
            v_align='center',
        )

        # The small view is out of room; more controls live in the
        # expanded one.
        if self.height < _EXPANDED_MIN_HEIGHT:
            self.text(
                f'{SpecialChar.UP_ARROW.value} expand for more',
                scale=0.5,
                pos=(-14, yoffs + 65),
                h_anchor='right',
                h_align='right',
                v_align='center',
                style='faded',
            )
        else:
            self._debug_drawing_row(xoffs, by + bheight + 55.0, bheight)

        # Bounds on the left, safe area in the middle: they nest that
        # way on screen (bounds is the outer rect), so the buttons read
        # in the same order as what they draw.
        bounds_overlay = _babase.get_draw_virtual_bounds()
        self.button(
            'Virtual Bounds ON' if bounds_overlay else 'Virtual Bounds OFF',
            pos=(xoffs + 10, by),
            size=(160, bheight),
            label_scale=0.5,
            call=self.toggle_bounds_overlay,
            style='bright' if bounds_overlay else 'normal',
        )
        ui_overlay = _babase.get_draw_virtual_safe_area_bounds()
        self.button(
            'Virtual Safe Area ON' if ui_overlay else 'Virtual Safe Area OFF',
            pos=(xoffs + 180, by),
            size=(160, bheight),
            label_scale=0.5,
            call=self.toggle_ui_overlay,
            style='bright' if ui_overlay else 'normal',
        )
        max_margins = _babase.get_force_max_virtual_bounds_margins()
        self.button(
            'Max Margins ON' if max_margins else 'Max Margins OFF',
            pos=(xoffs + 350, by),
            size=(160, bheight),
            label_scale=0.5,
            call=self.toggle_max_margins,
            style='bright' if max_margins else 'normal',
        )
        x = 585
        self.text(
            'UI-Scale',
            pos=(xoffs + x - 5, yoffs + 15),
            h_align='right',
            v_align='none',
            scale=0.55,
        )

        bwidth = 90
        for scale in UIScale:
            self.button(
                scale.name.capitalize(),
                pos=(xoffs + x, by),
                size=(bwidth, bheight),
                label_scale=0.6,
                call=partial(_babase.app.set_ui_scale, scale),
                style=(
                    'bright'
                    if scale.name.lower() == _babase.get_ui_scale()
                    else 'normal'
                ),
            )
            x += bwidth + 2

        if custom_buttons:
            x += cboffs
            for custom_button in custom_buttons:
                self.button(
                    custom_button.name,
                    pos=(xoffs + x, by),
                    size=(cbwidth, bheight),
                    label_scale=0.6,
                    call=custom_button.call,
                    corner_radius=10.0,
                    sound=custom_button.sound,
                )
                x += cbwidth + cbspacing

    def _debug_drawing_row(
        self, xoffs: float, y: float, bheight: float
    ) -> None:
        """A labeled row of toggles, one per kind of debug drawing."""
        self.text(
            'Debug Drawing',
            scale=0.6,
            pos=(xoffs + 8, y + bheight + 15.0),
            h_align='left',
            v_align='center',
        )
        x = xoffs + 10.0

        # Our own: kinds of thing whose bounds can be outlined.
        for kind, label in _DEBUG_BOUNDS_KINDS:
            enabled = _babase.get_debug_bounds(kind)
            self.button(
                f'{label} ON' if enabled else f'{label} OFF',
                pos=(x, y),
                size=(160, bheight),
                label_scale=0.5,
                call=partial(self.toggle_debug_bounds, kind),
                style='bright' if enabled else 'normal',
            )
            x += 170.0

        # Plus whatever the app-mode offers (for ui we can't know about
        # here).
        toggles = _babase.app.mode.get_dev_console_ui_debug_draw_toggles()
        for toggle in toggles:
            enabled = toggle.get_call()
            self.button(
                f'{toggle.name} ON' if enabled else f'{toggle.name} OFF',
                pos=(x, y),
                size=(160, bheight),
                label_scale=0.5,
                call=partial(self.toggle_custom_debug_draw, toggle),
                style='bright' if enabled else 'normal',
            )
            x += 170.0

    def toggle_ui_overlay(self) -> None:
        """Toggle UI overlay drawing."""
        _babase.set_draw_virtual_safe_area_bounds(
            not _babase.get_draw_virtual_safe_area_bounds()
        )
        self.request_refresh()

    def toggle_debug_bounds(self, kind: str) -> None:
        """Toggle outlining of one kind of thing's bounds."""
        _babase.set_debug_bounds(kind, not _babase.get_debug_bounds(kind))
        self.request_refresh()

    def toggle_custom_debug_draw(self, toggle: DevConsoleToggleDef) -> None:
        """Flip a debug-drawing toggle the app-mode offered."""
        toggle.set_call(not toggle.get_call())
        self.request_refresh()

    def toggle_bounds_overlay(self) -> None:
        """Toggle virtual-bounds guide drawing."""
        _babase.set_draw_virtual_bounds(not _babase.get_draw_virtual_bounds())
        self.request_refresh()

    def toggle_max_margins(self) -> None:
        """Toggle forced max virtual-bounds margins."""
        _babase.set_force_max_virtual_bounds_margins(
            not _babase.get_force_max_virtual_bounds_margins()
        )
        self.request_refresh()
