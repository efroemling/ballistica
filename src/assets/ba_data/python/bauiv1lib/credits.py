# Released under the MIT License. See LICENSE for details.
#
"""Provides a window to display game credits."""

from functools import partial
from typing import TYPE_CHECKING, override

from efro.util import strip_exception_tracebacks

import bauiv1 as bui
from bauiv1 import classicassets

if TYPE_CHECKING:
    from typing import Sequence, TypeAlias

    #: One display row: either a plain text line, or a row of names as
    #: (inset, [(column-slot, name), ...]) drawn as individual widgets
    #: at absolute column positions.
    CreditsRow: TypeAlias = str | tuple[float, list[tuple[int, str]]]

#: Horizontal distance between name columns (text units).
_NAME_COLUMN_SPACING = 330.0

#: Name columns per row.
_NAME_COLUMN_COUNT = 3

#: Font scale for the credits body text.
_TEXT_SCALE = 0.55

#: Vertical distance between rows, in container units. This is
#: text-mesh row height (32) at our text scale — rows within a
#: multi-line widget land exactly this far apart, which is what lets
#: us batch many rows into one widget with per-row positions intact.
_ROW_HEIGHT = 32.0 * _TEXT_SCALE

#: Widget-creates performed per frame when populating content.
#: Each create costs ~1ms all-in on a midrange phone (creation plus
#: its first-draw mesh build), so this keeps per-frame logic-thread
#: cost in the single-digit-ms range while the full page still lands
#: within a fraction of a second. Content fills top-down, so the
#: initially-visible portion appears in the first batch or two.
_CREATES_PER_FRAME = 6

#: Max rows batched into a single textwidget. Batching is what keeps
#: logic-thread build cost low (widget-creation overhead dominates on
#: mobile; a phone spent ~165ms creating one widget per row/name).
#: Capped well below text-mesh vertex limits (a 50-row chunk of even
#: very long lines stays under ~20k of the 65535 max verts).
_CHUNK_ROWS = 50


def _layout_names(
    names2: Sequence[str], inset: float
) -> list[tuple[float, list[tuple[int, str]]]]:
    """Assign names to (row, column-slot) positions.

    Each name later becomes its own widget at an absolute column x, so
    columns line up exactly regardless of font metrics; measurement
    (via the OS text backend for non-Latin names, hence
    background-thread-only) is needed only to skip slots for names too
    wide for their column.
    """
    rows: list[tuple[float, list[tuple[int, str]]]] = []
    row: list[tuple[int, str]] = []
    slot = 0
    for name in names2:
        if slot >= _NAME_COLUMN_COUNT:
            rows.append((inset, row))
            row = []
            slot = 0
        row.append((slot, name))
        width = bui.get_string_width(name, suppress_warning=True)
        # Advance past however many slots this name's width covers.
        end = slot * _NAME_COLUMN_SPACING + width
        slot = max(slot + 1, int(end // _NAME_COLUMN_SPACING) + 1)
    if row:
        rows.append((inset, row))
    return rows


def _bake_widget_specs(
    rows: Sequence[CreditsRow],
) -> tuple[int, list[tuple[float, float, str]]]:
    """Bake display rows into a minimal set of widget-create specs.

    Returns ``(row_count, [(x, y_down, text), ...])`` where each spec
    is one multi-line textwidget: x in container units, y_down the
    distance of its first row below the content top, text with rows
    joined by newlines (drawn ``_ROW_HEIGHT`` apart). Consecutive
    plain rows batch into chunks; name rows batch into one spec per
    column (same y, fixed column x) so column alignment survives
    batching exactly. All layout math happens here (on the background
    compose thread) so the logic thread's job is reduced to a few
    dozen bare widget-create calls.
    """
    specs: list[tuple[float, float, str]] = []
    row_idx = 0
    total = len(rows)
    while row_idx < total:
        row = rows[row_idx]
        chunk_top = row_idx
        if isinstance(row, str):
            # A run of plain rows.
            lines: list[str] = []
            while (
                row_idx < total
                and isinstance(rows[row_idx], str)
                and len(lines) < _CHUNK_ROWS
            ):
                nrow = rows[row_idx]
                assert isinstance(nrow, str)
                lines.append(nrow)
                row_idx += 1
            specs.append((0.0, chunk_top * _ROW_HEIGHT, '\n'.join(lines)))
        else:
            # A run of name rows (all sharing one inset; the sections
            # are separated by plain rows so runs never mix insets).
            inset = row[0]
            cols: list[list[str]] = [[] for _ in range(_NAME_COLUMN_COUNT)]
            count = 0
            while (
                row_idx < total
                and not isinstance(rows[row_idx], str)
                and count < _CHUNK_ROWS
            ):
                nrow = rows[row_idx]
                assert not isinstance(nrow, str)
                present: dict[int, str] = dict(nrow[1])
                for slot in range(_NAME_COLUMN_COUNT):
                    cols[slot].append(present.get(slot, ''))
                count += 1
                row_idx += 1
            for slot in range(_NAME_COLUMN_COUNT):
                text = '\n'.join(cols[slot])
                if not text.strip():
                    continue
                specs.append(
                    (
                        (inset + slot * _NAME_COLUMN_SPACING) * _TEXT_SCALE,
                        chunk_top * _ROW_HEIGHT,
                        text,
                    )
                )
    return (total, specs)


def _compose_credits_rows(
    translation_contributors: Sequence[str],
) -> list[CreditsRow]:
    """Build the full credits body as a list of display rows.

    Involves lots of string measuring (see ``_layout_names``), so this
    must run on a background thread, not the logic thread.
    """
    # Flat text on purpose: the credits body is assembled as
    # pre-laid-out plain text (name rows get positioned-widget
    # treatment instead so their columns line up exactly), so Lstr
    # values get evaluated at the boundary.
    sound_and_music = classicassets.strings.credits.song_credit(
        title="'William Tell (Trumpet Entry)'",
        performer='The Apollo Symphony Orchestra',
        composer='Gioacchino Rossini',
        arranger='Chris Worth',
        publisher='BMI',
        source='www.AudioSparx.com',
    ).evaluate()
    spc = '     '
    sound_and_music = spc + sound_and_music.replace('\n', '\n' + spc)
    names = [
        'HubOfTheUniverseProd',
        'Jovica',
        'LG',
        'Leady',
        'Percy Duke',
        'PhreaKsAccount',
        'Pogotron',
        'Rock Savage',
        'anamorphosis',
        'benboncan',
        'cdrk',
        'chipfork',
        'guitarguy1985',
        'jascha',
        'joedeshon',
        'loofa',
        'm_O_m',
        'mich3d',
        'sandyrb',
        'shakaharu',
        'sirplus',
        'stickman',
        'thanvannispen',
        'virotic',
        'zimbot',
    ]
    names.sort(key=lambda x: x.lower())

    part_before_freesound = (
        '  '
        + classicassets.strings.credits.coding_graphics_audio(
            name='Eric Froemling'
        ).evaluate()
        + '\n'
        '\n'
        '  '
        + classicassets.strings.credits.additional_audio_art_ideas(
            name='Raphael Suter'
        ).evaluate()
        + '\n'
        '\n'
        '  ' + classicassets.strings.credits.sound_and_music.evaluate() + '\n'
        '\n' + sound_and_music + '\n'
        '\n'
        '     '
        + classicassets.strings.credits.public_domain_music_via(
            name='Musopen.com'
        ).evaluate()
        + '\n'
        '        '
        + classicassets.strings.credits.thanks_especially_to(
            name='the US Army, Navy, and Marine Bands'
        ).evaluate()
        + '\n'
        '\n'
        '     '
        + classicassets.strings.credits.additional_music_from(
            name='The YouTube Audio Library'
        ).evaluate()
        + '\n'
        '\n'
        '     '
        + classicassets.strings.credits.sounds_source(
            source='Freesound.org'
        ).evaluate()
        + '\n\n'
    )

    part_before_translators = (
        '\n\n  '
        + classicassets.strings.credits.language_translations.evaluate()
        + '\n\n'
    )

    part_after_translators = (
        '\n'
        '  Shout Out to Awesome Mods / Modders / Contributors:\n\n'
        '     BombDash ModPack\n'
        '     TheMikirog & SoK - BombSquad Joyride Modpack\n'
        '     Mrmaxmeier - BombSquad-Community-Mod-Manager\n'
        '     Ritiek Malhotra \n'
        '     Dliwk\n'
        '     vishal332008\n'
        '     itsre3\n'
        '     Drooopyyy\n'
        '     Loup\n'
        '\n'
        '  Holiday theme vector art designed by Freepik\n'
        '\n'
        '  ' + classicassets.strings.credits.special_thanks.evaluate() + '\n'
        '\n'
        '     Todd, Laura, and Robert Froemling\n'
        '     '
        + classicassets.strings.credits.all_my_family.evaluate().replace(
            '\n', '\n     '
        )
        + '\n'
        '     '
        + classicassets.strings.credits.whoever_invented_coffee.evaluate()
        + '\n'
        '\n'
        '  ' + classicassets.strings.credits.legal.evaluate() + '\n'
        '\n'
        '     '
        + classicassets.strings.credits.software_based_on(
            name='the Khronos Group'
        ).evaluate()
        + '\n'
        '\n'
        '                                       '
        '                      www.ballistica.net\n'
    )

    rows: list[CreditsRow] = []
    rows += part_before_freesound.splitlines()
    rows += _layout_names(names, 90)
    rows += part_before_translators.splitlines()
    rows += _layout_names(translation_contributors, 60)
    rows += part_after_translators.splitlines()
    return rows


class CreditsWindow(bui.MainWindow):
    """Window for displaying game credits."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        bui.set_analytics_screen('Credits Window')

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 990 if uiscale is bui.UIScale.SMALL else 670
        height = 750 if uiscale is bui.UIScale.SMALL else 500

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.2 if uiscale is bui.UIScale.MEDIUM else 1.0
        )

        # Scale down if necessary so the full width of our UI is
        # visible.
        min_width = 800
        if screensize[0] / scale < min_width:
            scale *= (screensize[0] / scale) / min_width

        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(width - 80, screensize[0] / scale)
        target_height = min(height - 80, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height

        scroll_width = target_width

        # Use the full screen area in small mode (we'll include our
        # title in the scrollable content).
        if uiscale is bui.UIScale.SMALL:
            scroll_height = target_height
            scroll_y = yoffs - scroll_height
        else:
            yoffs += 30
            scroll_height = target_height - 29
            scroll_y = yoffs - 58 - scroll_height

        self._r = 'creditsWindow'
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
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

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|back',
                position=(40, yoffs - 46),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
                autoselect=True,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        scroll = self._scroll = bui.scrollwidget(
            parent=self._root_widget,
            size=(scroll_width, scroll_height),
            position=(width * 0.5 - scroll_width * 0.5, scroll_y),
            capture_arrows=True,
            border_opacity=0.4,
            center_small_content_horizontally=True,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=scroll,
                left_widget=bui.get_special_widget('back_button'),
            )
        bui.widget(
            edit=scroll,
            right_widget=bui.get_special_widget('squad_button'),
        )
        bui.containerwidget(edit=self._root_widget, selected_child=scroll)

        # Layout values our deferred content build will need.
        self._uiscale = uiscale
        self._width = width
        self._yoffs = yoffs
        self._scroll_width = scroll_width
        self._sub_width = min(700, width - 80)
        self._sub_height: float | None = None
        self._subcontainer: bui.Widget | None = None
        self._specs: list[tuple[float, float, str]] | None = None
        self._spec_index = 0
        self._content_top = 0.0
        self._build_timer: bui.DisplayTimer | None = None

        # Composing the credits body involves measuring lots of
        # multi-script text, which can stall on lazy OS font loads — so
        # it happens on a background thread and the resulting content
        # gets built here once ready (this is also why we grab the
        # contributor list here rather than there; its underlying
        # asset-registry lookups keep a simple logic-thread-only
        # contract). Measurement itself is thread-safe.
        translation_contributors: Sequence[str] = bui.get_legacy_langdata().get(
            'translation_contributors', []
        )
        bui.app.threadpool.submit_no_wait(
            partial(self._compose_in_bg, translation_contributors)
        )

    def _compose_in_bg(self, translation_contributors: Sequence[str]) -> None:
        """Compose the credits body (on a background thread)."""
        try:
            assert not bui.in_logic_thread()
            rows = _compose_credits_rows(translation_contributors)
            # Bake rows into a minimal set of fully-positioned widget
            # specs (all layout math done here, off the logic thread).
            row_count, specs = _bake_widget_specs(rows)
            # Pre-measure the exact spec strings: this populates the
            # engine's span-measure cache with the spans the logic
            # thread will need when building these widgets' text
            # meshes, keeping that step off the OS text backend.
            for _x, _y, spec_text in specs:
                bui.get_string_width(spec_text, suppress_warning=True)
            bui.pushcall(
                bui.WeakCallStrict(self._build_content, row_count, specs),
                from_other_thread=True,
            )
        except Exception as exc:
            bui.uilog.exception('Error composing credits content.')
            strip_exception_tracebacks(exc)

    def _build_content(
        self, row_count: int, specs: list[tuple[float, float, str]]
    ) -> None:
        """Populate our scroll content (back on the logic thread).

        Everything here was baked on the background compose thread;
        this just runs the (few dozen) widget creates.
        """
        # No-op if our ui is already gone.
        if not self._root_widget:
            return

        sub_height = float(_ROW_HEIGHT * row_count + 40)

        inline_title_height = 50

        # Make space for our title when we're stuffing it inline.
        if self._uiscale is bui.UIScale.SMALL:
            sub_height += inline_title_height
        self._sub_height = sub_height

        self._subcontainer = bui.containerwidget(
            parent=self._scroll,
            id=f'{self.main_window_id_prefix}|sub',
            size=(self._sub_width, sub_height),
            background=False,
            claims_left_right=False,
        )

        # Stick our title on the scrollable content in small ui mode so
        # we can use the full screen area for said content.
        bui.textwidget(
            parent=(
                self._subcontainer
                if self._uiscale is bui.UIScale.SMALL
                else self._root_widget
            ),
            position=(
                (self._sub_width * 0.5, sub_height - 20)
                if self._uiscale is bui.UIScale.SMALL
                else (self._width * 0.5, self._yoffs - 28)
            ),
            size=(0, 0),
            scale=0.8 if self._uiscale is bui.UIScale.SMALL else 1.0,
            text=classicassets.strings.credits.title(
                app_name=classicassets.strings.ui.app_name
            ),
            h_align='center',
            v_align='center',
            color=bui.app.ui_v1.title_color,
            maxwidth=self._scroll_width * 0.7,
        )

        voffs = (
            -inline_title_height if self._uiscale is bui.UIScale.SMALL else 0
        )

        # Create content widgets a few per frame: each costs ~1ms
        # all-in on a midrange phone, so doing all of them in one
        # frame is a visible hitch while this way stays well within
        # frame budget. Specs are ordered top-down so visible content
        # lands first; the rest fills in below over the next fraction
        # of a second.
        self._content_top = sub_height - 20 + voffs
        self._specs = specs
        self._spec_index = 0
        self._build_timer = bui.DisplayTimer(
            0.0001, bui.WeakCallStrict(self._build_batch), repeat=True
        )
        self._build_batch()

    def _build_batch(self) -> None:
        """Create the next batch of content widgets (logic thread)."""
        container = self._subcontainer
        if not container:
            # Our ui died; stop.
            self._build_timer = None
            return
        assert self._specs is not None
        batch_end = min(len(self._specs), self._spec_index + _CREATES_PER_FRAME)
        textwidget = bui.textwidget
        for i in range(self._spec_index, batch_end):
            xoffs, y_down, text = self._specs[i]
            textwidget(
                parent=container,
                padding=4,
                color=(0.7, 0.9, 0.7, 1.0),
                scale=_TEXT_SCALE,
                flatness=1.0,
                size=(0, 0),
                position=(xoffs, self._content_top - y_down),
                h_align='left',
                v_align='top',
                text=text,
            )
        self._spec_index = batch_end
        if batch_end >= len(self._specs):
            self._build_timer = None
            self._specs = None

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
