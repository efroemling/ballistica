# Released under the MIT License. See LICENSE for details.
#
"""Provides popup windows for choosing colors."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Sequence

REQUIRE_PRO = False


class ColorPicker(PopupWindow):
    """A popup UI to select from a set of colors.

    Passes the color to the delegate's color_picker_selected_color() method.
    """

    def __init__(
        self,
        parent: bui.Widget,
        position: tuple[float, float],
        *,
        initial_color: Sequence[float] = (1.0, 1.0, 1.0),
        delegate: Any = None,
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        tag: Any = '',
    ):
        # pylint: disable=too-many-locals
        assert bui.app.classic is not None

        c_raw = bui.app.classic.get_player_colors()
        assert len(c_raw) == 16
        self.colors = [c_raw[0:4], c_raw[4:8], c_raw[8:12], c_raw[12:16]]

        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            )
        self._parent = parent
        self._position = position
        self._scale = scale
        self._offset = offset
        self._delegate = delegate
        self._transitioning_out = False
        self._tag = tag
        self._initial_color = initial_color

        # Create our _root_widget.
        super().__init__(
            position=position,
            size=(210, 240),
            scale=scale,
            focus_position=(10, 10),
            focus_size=(190, 220),
            bg_color=(0.5, 0.5, 0.5),
            offset=offset,
        )
        rows: list[list[bui.Widget]] = []
        closest_dist = 9999.0
        closest = (0, 0)
        for y in range(4):
            row: list[bui.Widget] = []
            rows.append(row)
            for x in range(4):
                color = self.colors[y][x]
                dist = (
                    abs(color[0] - initial_color[0])
                    + abs(color[1] - initial_color[1])
                    + abs(color[2] - initial_color[2])
                )
                if dist < closest_dist:
                    closest = (x, y)
                    closest_dist = dist
                btn = bui.buttonwidget(
                    parent=self.root_widget,
                    position=(22 + 45 * x, 185 - 45 * y),
                    size=(35, 40),
                    label='',
                    button_type='square',
                    on_activate_call=bui.WeakCall(self._select, x, y),
                    autoselect=True,
                    color=color,
                    extra_touch_border_scale=0.0,
                )
                row.append(btn)
        other_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(105 - 60, 13),
            color=(0.7, 0.7, 0.7),
            text_scale=0.5,
            textcolor=(0.8, 0.8, 0.8),
            size=(120, 30),
            label=bui.Lstr(
                resource='otherText',
                fallback_resource='coopSelectWindow.customText',
            ),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._select_other),
        )

        assert bui.app.classic is not None
        if REQUIRE_PRO and not bui.app.classic.accounts.have_pro():
            bui.imagewidget(
                parent=self.root_widget,
                position=(50, 12),
                size=(30, 30),
                texture=bui.gettexture('lock'),
                draw_controller=other_button,
            )

        # If their color is close to one of our swatches, select it.
        # Otherwise select 'other'.
        if closest_dist < 0.03:
            bui.containerwidget(
                edit=self.root_widget,
                selected_child=rows[closest[1]][closest[0]],
            )
        else:
            bui.containerwidget(
                edit=self.root_widget, selected_child=other_button
            )

    def get_tag(self) -> Any:
        """Return this popup's tag."""
        return self._tag

    def _select_other(self) -> None:
        from bauiv1lib import purchase

        # Requires pro.
        assert bui.app.classic is not None
        if REQUIRE_PRO and not bui.app.classic.accounts.have_pro():
            purchase.PurchaseWindow(items=['pro'])
            self._transition_out()
            return
        ColorPickerExact(
            parent=self._parent,
            position=self._position,
            initial_color=self._initial_color,
            delegate=self._delegate,
            scale=self._scale,
            offset=self._offset,
            tag=self._tag,
        )

        # New picker now 'owns' the delegate; we shouldn't send it any
        # more messages.
        self._delegate = None
        self._transition_out()

    def _select(self, x: int, y: int) -> None:
        if self._delegate:
            self._delegate.color_picker_selected_color(self, self.colors[y][x])
        bui.apptimer(0.05, self._transition_out)

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            if self._delegate is not None:
                self._delegate.color_picker_closing(self)
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        if not self._transitioning_out:
            bui.getsound('swish').play()
        self._transition_out()


class ColorPickerExact(PopupWindow):
    """pops up a ui to select from a set of colors.
    passes the color to the delegate's color_picker_selected_color() method"""

    def __init__(
        self,
        parent: bui.Widget,
        position: tuple[float, float],
        *,
        initial_color: Sequence[float] = (1.0, 1.0, 1.0),
        delegate: Any = None,
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        tag: Any = '',
    ):
        # pylint: disable=too-many-locals
        del parent  # Unused var.
        assert bui.app.classic is not None

        c_raw = bui.app.classic.get_player_colors()
        assert len(c_raw) == 16
        self.colors = [c_raw[0:4], c_raw[4:8], c_raw[8:12], c_raw[12:16]]

        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            )
        self._delegate = delegate
        self._transitioning_out = False
        self._tag = tag
        self._color = list(initial_color)
        self._last_press_time = bui.apptime()
        self._last_press_color_name: str | None = None
        self._last_press_increasing: bool | None = None
        self._hex_timer: bui.AppTimer | None = None
        self._hex_prev_text: str = '#FFFFFF'
        self._change_speed = 1.0
        width = 180.0
        height = 240.0

        # Creates our _root_widget.
        super().__init__(
            position=position,
            size=(width, height),
            scale=scale,
            focus_position=(10, 10),
            focus_size=(width - 20, height - 20),
            bg_color=(0.5, 0.5, 0.5),
            offset=offset,
        )
        self._swatch = bui.imagewidget(
            parent=self.root_widget,
            position=(width * 0.5 - 65 + 5, height - 95),
            size=(130, 115),
            texture=bui.gettexture('clayStroke'),
            color=(1, 0, 0),
        )
        self._hex_textbox = bui.textwidget(
            parent=self.root_widget,
            position=(width * 0.5 - 37.5 + 3, height - 51),
            max_chars=9,
            text='#FFFFFF',
            autoselect=True,
            size=(75, 30),
            v_align='center',
            editable=True,
            maxwidth=70,
            allow_clear_button=False,
            glow_type='uniform',
        )

        x = 50
        y = height - 90
        self._label_r: bui.Widget
        self._label_g: bui.Widget
        self._label_b: bui.Widget
        for color_name, color_val in [
            ('r', (1, 0.15, 0.15)),
            ('g', (0.15, 1, 0.15)),
            ('b', (0.15, 0.15, 1)),
        ]:
            txt = bui.textwidget(
                parent=self.root_widget,
                position=(x - 10, y),
                size=(0, 0),
                h_align='center',
                color=color_val,
                v_align='center',
                text='0.12',
            )
            setattr(self, '_label_' + color_name, txt)
            for b_label, bhval, binc in [('-', 30, False), ('+', 75, True)]:
                bui.buttonwidget(
                    parent=self.root_widget,
                    position=(x + bhval, y - 15),
                    scale=0.8,
                    repeat=True,
                    text_scale=1.3,
                    size=(40, 40),
                    label=b_label,
                    autoselect=True,
                    enable_sound=False,
                    on_activate_call=bui.WeakCall(
                        self._color_change_press, color_name, binc
                    ),
                )
            y -= 42

        btn = bui.buttonwidget(
            parent=self.root_widget,
            position=(width * 0.5 - 40, 10),
            size=(80, 30),
            text_scale=0.6,
            color=(0.6, 0.6, 0.6),
            textcolor=(0.7, 0.7, 0.7),
            label=bui.Lstr(resource='doneText'),
            on_activate_call=bui.WeakCall(self._transition_out),
            autoselect=True,
        )
        bui.containerwidget(edit=self.root_widget, start_button=btn)

        # Unlike the swatch picker, we stay open and constantly push our
        # color to the delegate, so start doing that.
        self._update_for_color()

        # Update our HEX stuff!
        self._update_for_hex()
        self._hex_timer = bui.AppTimer(0.025, self._update_for_hex, repeat=True)

    def _update_for_hex(self) -> None:
        """Update for any HEX or color change."""
        from typing import cast

        hextext = cast(str, bui.textwidget(query=self._hex_textbox))
        hexcolor: tuple
        # Check if our current hex text doesn't match with our old one.
        # Convert our current hex text into a color if possible.
        if hextext != self._hex_prev_text:
            try:
                hexcolor = hex_to_color(hextext)
                if len(hexcolor) == 4:
                    r, g, b, a = hexcolor
                    del a  # unused
                else:
                    r, g, b = hexcolor
                # Replace the color!
                for i, ch in enumerate((r, g, b)):
                    self._color[i] = max(0.0, min(1.0, ch))
                self._update_for_color()
            # Usually, a ValueError will occur if the provided hex
            # is incomplete, which occurs when in the midst of typing it.
            except ValueError:
                pass
        # Store the current text for our next comparison.
        self._hex_prev_text = hextext

    # noinspection PyUnresolvedReferences
    def _update_for_color(self) -> None:
        if not self.root_widget:
            return
        bui.imagewidget(edit=self._swatch, color=self._color)

        # We generate these procedurally, so pylint misses them.
        # FIXME: create static attrs instead.
        # pylint: disable=consider-using-f-string
        bui.textwidget(edit=self._label_r, text='%.2f' % self._color[0])
        bui.textwidget(edit=self._label_g, text='%.2f' % self._color[1])
        bui.textwidget(edit=self._label_b, text='%.2f' % self._color[2])
        if self._delegate is not None:
            self._delegate.color_picker_selected_color(self, self._color)

        # Show the HEX code of this color.
        r, g, b = self._color
        hexcode = color_to_hex(r, g, b, None)
        self._hex_prev_text = hexcode
        bui.textwidget(
            edit=self._hex_textbox,
            text=hexcode,
            color=color_overlay_func(r, g, b),
        )

    def _color_change_press(self, color_name: str, increasing: bool) -> None:
        # If we get rapid-fire presses, eventually start moving faster.
        current_time = bui.apptime()
        since_last = current_time - self._last_press_time
        if (
            since_last < 0.2
            and self._last_press_color_name == color_name
            and self._last_press_increasing == increasing
        ):
            self._change_speed += 0.25
        else:
            self._change_speed = 1.0
        self._last_press_time = current_time
        self._last_press_color_name = color_name
        self._last_press_increasing = increasing

        color_index = ('r', 'g', 'b').index(color_name)
        offs = int(self._change_speed) * (0.01 if increasing else -0.01)
        self._color[color_index] = max(
            0.0, min(1.0, self._color[color_index] + offs)
        )
        self._update_for_color()

    def get_tag(self) -> Any:
        """Return this popup's tag value."""
        return self._tag

    def _transition_out(self) -> None:
        # Kill our timer
        self._hex_timer = None
        if not self._transitioning_out:
            self._transitioning_out = True
            if self._delegate is not None:
                self._delegate.color_picker_closing(self)
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        if not self._transitioning_out:
            bui.getsound('swish').play()
        self._transition_out()


def hex_to_color(hex_color: str) -> tuple:
    """Transforms an RGB / RGBA hex code into an rgb1/rgba1 tuple.

    Args:
        hex_color (str): The HEX color.
    Raises:
        ValueError: If the provided HEX color isn't 6 or 8 characters long.
    Returns:
        tuple: The color tuple divided by 255.
    """
    # Remove the '#' from the string if provided.
    if hex_color.startswith('#'):
        hex_color = hex_color.lstrip('#')
    # Check if this has a valid length.
    hexlength = len(hex_color)
    if not hexlength in [6, 8]:
        raise ValueError(f'Invalid HEX color provided: "{hex_color}"')

    # Convert the hex bytes to their true byte form.
    ar, ag, ab, aa = (
        (int.from_bytes(bytes.fromhex(hex_color[0:2]))),
        (int.from_bytes(bytes.fromhex(hex_color[2:4]))),
        (int.from_bytes(bytes.fromhex(hex_color[4:6]))),
        (
            (int.from_bytes(bytes.fromhex(hex_color[6:8])))
            if hexlength == 8
            else None
        ),
    )
    # Divide all numbers by 255 and return.
    nr, ng, nb, na = (
        x / 255 if x is not None else None for x in (ar, ag, ab, aa)
    )
    return (nr, ng, nb, na) if aa is not None else (nr, ng, nb)


def color_to_hex(r: float, g: float, b: float, a: float | None = 1.0) -> str:
    """Converts an rgb1 tuple to a HEX color code.

    Args:
        r: Red.
        g: Green.
        b: Blue.
        a: Alpha. Defaults to 1.0.

    Returns:
        str: The hexified rgba values.
    """
    # Turn our rgb1 to rgb255
    nr, ng, nb, na = [
        int(min(255, x * 255)) if x is not None else x for x in [r, g, b, a]
    ]
    # Merge all values into their HEX representation.
    hex_code = (
        f'#{nr:02x}{ng:02x}{nb:02x}{na:02x}'
        if na is not None
        else f'#{nr:02x}{ng:02x}{nb:02x}'
    )
    return hex_code


def color_overlay_func(
    r: float, g: float, b: float, a: float | None = None
) -> tuple[float, ...]:
    """I could NOT come up with a better function name.

    Args:
        r: Red.
        g: Green.
        b: Blue.
        a: Alpha. Defaults to None.

    Returns:
        tuple: A brighter color if the provided one is dark,
               and a darker one if it's darker.
    """

    # Calculate the relative luminance using the formula for sRGB
    # https://www.w3.org/TR/WCAG20/#relativeluminancedef
    def relative_luminance(color: float) -> Any:
        if color <= 0.03928:
            return color / 12.92
        return ((color + 0.055) / 1.055) ** 2.4

    luminance = (
        0.2126 * relative_luminance(r)
        + 0.7152 * relative_luminance(g)
        + 0.0722 * relative_luminance(b)
    )
    # Set our color multiplier depending on the provided color's luminance.
    luminant = 1.65 if luminance < 0.33 else 0.2
    # Multiply our given numbers, making sure
    # they don't blend in the original bg.
    avg = (0.7 - (r + g + b / 3)) + 0.15
    r, g, b = [max(avg, x * luminant) for x in (r, g, b)]
    # Include our alpha and ship it!
    return (r, g, b, a) if a is not None else (r, g, b)
