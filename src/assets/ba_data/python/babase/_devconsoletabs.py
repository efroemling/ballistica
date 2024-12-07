# Released under the MIT License. See LICENSE for details.
#
"""Predefined tabs for the dev console."""
from __future__ import annotations

import math
import random
import logging
from functools import partial
from typing import TYPE_CHECKING, override, TypeVar, Generic

import _babase

from babase._devconsole import DevConsoleTab

if TYPE_CHECKING:
    from typing import Callable, Literal

    from bacommon.loggercontrol import LoggerControlConfig
    from babase import AppMode

T = TypeVar('T')


class DevConsoleTabPython(DevConsoleTab):
    """The Python dev-console tab."""

    @override
    def refresh(self) -> None:
        self.python_terminal()


class DevConsoleTabAppModes(DevConsoleTab):
    """Tab to switch app modes."""

    def __init__(self) -> None:
        self._app_modes: list[type[AppMode]] | None = None
        self._app_modes_loading = False

    def _on_app_modes_loaded(self, modes: list[type[AppMode]]) -> None:
        from babase._appintent import AppIntentDefault

        intent = AppIntentDefault()

        # Limit to modes that can handle default intents since that's
        # what we use.
        self._app_modes = [
            mode for mode in modes if mode.can_handle_intent(intent)
        ]
        self.request_refresh()

    @override
    def refresh(self) -> None:
        from babase import AppMode

        # Kick off a load if applicable.
        if self._app_modes is None and not self._app_modes_loading:
            _babase.app.meta.load_exported_classes(
                AppMode, self._on_app_modes_loaded
            )

        # Just say 'loading' if we don't have app-modes yet.
        if self._app_modes is None:
            self.text(
                'Loading...', pos=(0, 30), h_anchor='center', h_align='center'
            )
            return

        bwidth = 260
        bpadding = 5

        xoffs = -0.5 * bwidth * len(self._app_modes)

        self.text(
            'Available AppModes:',
            scale=0.8,
            pos=(0, 75),
            h_align='center',
            v_align='center',
        )
        # pylint: disable=protected-access
        for i, mode in enumerate(self._app_modes):
            self.button(
                f'{mode.__module__}.{mode.__qualname__}',
                pos=(xoffs + i * bwidth + bpadding, 10),
                size=(bwidth - 2.0 * bpadding, 40),
                label_scale=0.6,
                call=partial(self._set_app_mode, mode),
                style=(
                    'bright'
                    if isinstance(_babase.app._mode, mode)
                    else 'normal'
                ),
            )

    def _set_app_mode(self, mode: type[AppMode]) -> None:
        from babase._appintent import AppIntentDefault

        intent = AppIntentDefault()

        # Use private functionality to force a specific app-mode to
        # handle this intent. Note that this should never be done
        # outside of this explicit testing case. It is the app's job to
        # determine which app-mode should be used to handle a given
        # intent.
        setattr(intent, '_force_app_mode_handler', mode)

        _babase.app.set_intent(intent)

        # Slight hackish: need to wait a moment before refreshing to
        # pick up the newly current mode, as mode switches are
        # asynchronous.
        _babase.apptimer(0.1, self.request_refresh)


class DevConsoleTabUI(DevConsoleTab):
    """Tab to debug/test UI stuff."""

    @override
    def refresh(self) -> None:
        from babase._mgen.enums import UIScale

        xoffs = -375

        self.text(
            'Make sure all interactive UI fits in the'
            ' virtual bounds at all UI-scales (not counting things'
            ' that follow screen edges).\n'
            'Note that some elements may not reflect UI-scale changes'
            ' until recreated.',
            scale=0.6,
            pos=(xoffs + 15, 70),
            # h_anchor='left',
            h_align='left',
            v_align='center',
        )

        ui_overlay = _babase.get_draw_ui_bounds()
        self.button(
            'Virtual Bounds ON' if ui_overlay else 'Virtual Bounds OFF',
            pos=(xoffs + 10, 10),
            size=(200, 30),
            # h_anchor='left',
            label_scale=0.6,
            call=self.toggle_ui_overlay,
            style='bright' if ui_overlay else 'normal',
        )
        x = 300
        self.text(
            'UI-Scale',
            pos=(xoffs + x - 5, 15),
            # h_anchor='left',
            h_align='right',
            v_align='none',
            scale=0.6,
        )

        bwidth = 100
        for scale in UIScale:
            self.button(
                scale.name.capitalize(),
                pos=(xoffs + x, 10),
                size=(bwidth, 30),
                # h_anchor='left',
                label_scale=0.6,
                call=partial(_babase.app.set_ui_scale, scale),
                style=(
                    'bright'
                    if scale.name.lower() == _babase.get_ui_scale()
                    else 'normal'
                ),
            )
            x += bwidth + 2

    def toggle_ui_overlay(self) -> None:
        """Toggle UI overlay drawing."""
        _babase.set_draw_ui_bounds(not _babase.get_draw_ui_bounds())
        self.request_refresh()


class Table(Generic[T]):
    """Used to show controls for arbitrarily large data in a grid form."""

    def __init__(
        self,
        title: str,
        entries: list[T],
        draw_entry_call: Callable[
            [int, T, DevConsoleTab, float, float, float, float], None
        ],
        *,
        entry_width: float = 300.0,
        entry_height: float = 40.0,
        margin_left_right: float = 60.0,
        debug_bounds: bool = False,
        max_columns: int | None = None,
    ) -> None:
        self._title = title
        self._entry_width = entry_width
        self._entry_height = entry_height
        self._margin_left_right = margin_left_right
        self._focus_entry_index = 0
        self._entries_per_page = 1
        self._debug_bounds = debug_bounds
        self._entries = entries
        self._draw_entry_call = draw_entry_call
        self._max_columns = max_columns

        # Values updated on refresh (for aligning other custom
        # widgets/etc.)
        self.top_left: tuple[float, float] = (0.0, 0.0)
        self.top_right: tuple[float, float] = (0.0, 0.0)

    def set_entries(self, entries: list[T]) -> None:
        """Update table entries."""
        self._entries = entries

        # Clamp focus to new entries.
        self._focus_entry_index = max(
            0, min(len(self._entries) - 1, self._focus_entry_index)
        )

    def set_focus_entry_index(self, index: int) -> None:
        """Explicitly set the focused entry.

        This affects which page is shown at the next refresh.
        """
        self._focus_entry_index = max(0, min(len(self._entries) - 1, index))

    def refresh(self, tab: DevConsoleTab) -> None:
        """Call to refresh the data."""
        # pylint: disable=too-many-locals

        margin_top = 50.0
        margin_bottom = 10.0

        # Update how much we can fit on a page based on our current size.
        max_entry_area_width = tab.width - (self._margin_left_right * 2.0)
        max_entry_area_height = tab.height - (margin_top + margin_bottom)
        columns = max(1, int(max_entry_area_width / self._entry_width))
        if self._max_columns is not None:
            columns = min(columns, self._max_columns)
        rows = max(1, int(max_entry_area_height / self._entry_height))
        self._entries_per_page = rows * columns

        # See which page our focus index falls in.
        pagemax = math.ceil(len(self._entries) / self._entries_per_page)

        page = self._focus_entry_index // self._entries_per_page
        entry_offset = page * self._entries_per_page

        entries_on_this_page = min(
            self._entries_per_page, len(self._entries) - entry_offset
        )
        columns_on_this_page = math.ceil(entries_on_this_page / rows)
        rows_on_this_page = min(entries_on_this_page, rows)

        # We attach things to the center so resizes are smooth but we do
        # some math in a left-centric way.
        center_to_left = tab.width * -0.5

        # Center our columns.
        xoffs = 0.5 * (
            max_entry_area_width - columns_on_this_page * self._entry_width
        )

        # Align everything to the bottom of the dev-console.
        #
        # UPDATE: Nevermind; top feels better. Keeping this code around
        # in case we ever want to make it an option though.
        if bool(False):
            yoffs = -1.0 * (
                tab.height
                - (
                    rows_on_this_page * self._entry_height
                    + margin_top
                    + margin_bottom
                )
            )
        else:
            yoffs = 0

        # Keep our corners up to date for user use.
        self.top_left = (center_to_left + xoffs, tab.height + yoffs)
        self.top_right = (
            self.top_left[0]
            + self._margin_left_right * 2.0
            + columns_on_this_page * self._entry_width,
            self.top_left[1],
        )

        # Page left/right buttons.
        tab.button(
            '<',
            pos=(
                center_to_left + xoffs,
                yoffs + tab.height - margin_top - rows * self._entry_height,
            ),
            size=(
                self._margin_left_right,
                rows * self._entry_height,
            ),
            call=partial(self._page_left, tab),
            disabled=entry_offset == 0,
        )
        tab.button(
            '>',
            pos=(
                center_to_left
                + xoffs
                + self._margin_left_right
                + columns_on_this_page * self._entry_width,
                yoffs + tab.height - margin_top - rows * self._entry_height,
            ),
            size=(
                self._margin_left_right,
                rows * self._entry_height,
            ),
            call=partial(self._page_right, tab),
            disabled=(
                entry_offset + entries_on_this_page >= len(self._entries)
            ),
        )

        for column in range(columns):
            for row in range(rows):
                entry_index = entry_offset + column * rows + row
                if entry_index >= len(self._entries):
                    break

                xpos = (
                    xoffs + self._margin_left_right + self._entry_width * column
                )
                ypos = (
                    yoffs
                    + tab.height
                    - margin_top
                    - self._entry_height * (row + 1.0)
                )
                # Draw debug bounds.
                if self._debug_bounds:
                    tab.button(
                        str(entry_index),
                        pos=(
                            center_to_left + xpos,
                            ypos,
                        ),
                        size=(self._entry_width, self._entry_height),
                        # h_anchor='left',
                    )
                # Run user drawing.
                self._draw_entry_call(
                    entry_index,
                    self._entries[entry_index],
                    tab,
                    center_to_left + xpos,
                    ypos,
                    self._entry_width,
                    self._entry_height,
                )

            if entry_index >= len(self._entries):
                break

        tab.text(
            f'{self._title} ({page + 1}/{pagemax})',
            scale=0.8,
            pos=(0, yoffs + tab.height - margin_top * 0.5),
            h_align='center',
            v_align='center',
        )

    def _page_right(self, tab: DevConsoleTab) -> None:
        # Set focus on the first entry in the page before the current.
        page = self._focus_entry_index // self._entries_per_page
        page += 1
        self.set_focus_entry_index(page * self._entries_per_page)
        tab.request_refresh()

    def _page_left(self, tab: DevConsoleTab) -> None:
        # Set focus on the first entry in the page after the current.
        page = self._focus_entry_index // self._entries_per_page
        page -= 1
        self.set_focus_entry_index(page * self._entries_per_page)
        tab.request_refresh()


class DevConsoleTabLogging(DevConsoleTab):
    """Tab to wrangle logging levels."""

    def __init__(self) -> None:

        self._table = Table(
            title='Logging Levels',
            entry_width=800,
            entry_height=42,
            debug_bounds=False,
            entries=list[str](),
            draw_entry_call=self._draw_entry,
            max_columns=1,
        )

    @override
    def refresh(self) -> None:
        assert self._table is not None

        # Update table entries with the latest set of loggers (this can
        # change over time).
        self._table.set_entries(
            ['root'] + sorted(logging.root.manager.loggerDict)
        )

        # Draw the table.
        self._table.refresh(self)

        # Draw our control buttons in the corners.
        tl = self._table.top_left
        tr = self._table.top_right
        bwidth = 140.0
        bheight = 30.0
        bvpad = 10.0
        self.button(
            'Reset',
            pos=(tl[0], tl[1] - bheight - bvpad),
            size=(bwidth, bheight),
            label_scale=0.6,
            call=self._reset,
            disabled=(
                not self._get_reset_logger_control_config().would_make_changes()
            ),
        )
        self.button(
            'Cloud Control OFF',
            pos=(tr[0] - bwidth, tl[1] - bheight - bvpad),
            size=(bwidth, bheight),
            label_scale=0.6,
            disabled=True,
        )

    def _get_reset_logger_control_config(self) -> LoggerControlConfig:
        from bacommon.logging import get_base_logger_control_config_client

        return get_base_logger_control_config_client()

    def _reset(self) -> None:

        self._get_reset_logger_control_config().apply()

        # Let the native layer know that levels changed.
        _babase.update_internal_logger_levels()

        # Blow away any existing values in app-config.
        appconfig = _babase.app.config
        if 'Log Levels' in appconfig:
            del appconfig['Log Levels']
            appconfig.commit()

        self.request_refresh()

    def _set_entry_val(self, entry_index: int, entry: str, val: int) -> None:

        from bacommon.logging import get_base_logger_control_config_client
        from bacommon.loggercontrol import LoggerControlConfig

        # Focus on this entry with any interaction, so if we get resized
        # it'll still be visible.
        self._table.set_focus_entry_index(entry_index)

        logging.getLogger(entry).setLevel(val)

        # Let the native layer know that levels changed.
        _babase.update_internal_logger_levels()

        # Store only changes compared to the base config.
        baseconfig = get_base_logger_control_config_client()
        config = LoggerControlConfig.from_current_loggers().diff(baseconfig)

        appconfig = _babase.app.config
        appconfig['Log Levels'] = config.levels
        appconfig.commit()

        self.request_refresh()

    def _draw_entry(
        self,
        entry_index: int,
        entry: str,
        tab: DevConsoleTab,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=too-many-locals

        xoffs = -15.0
        bwidth = 80.0
        btextscale = 0.5
        tab.text(
            entry,
            (
                x + width - bwidth * 6.5 - 10.0 + xoffs,
                y + height * 0.5,
            ),
            h_align='right',
            scale=0.7,
        )

        logger = logging.getLogger(entry)
        level = logger.level
        index = 0
        effectivelevel = logger.getEffectiveLevel()
        # if entry != 'root' and level == logging.NOTSET:
        #     # Show the level being inherited in NOTSET cases.
        #     notsetlevelname = logging.getLevelName(logger.getEffectiveLevel())
        #     if notsetlevelname == 'NOTSET':
        #         notsetname = 'Not Set'
        #     else:
        #         notsetname = f'Not Set ({notsetlevelname.capitalize()})'
        # else:
        notsetname = 'Not Set'
        tab.button(
            notsetname,
            pos=(x + width - bwidth * 6.5 + xoffs + 1.0, y + 5.0),
            size=(bwidth * 1.0 - 2.0, height - 10),
            label_scale=btextscale,
            style='white_bright' if level == logging.NOTSET else 'black',
            call=partial(
                self._set_entry_val, entry_index, entry, logging.NOTSET
            ),
        )
        index += 1
        tab.button(
            'Debug',
            pos=(x + width - bwidth * 5 + xoffs + 1.0, y + 5.0),
            size=(bwidth - 2.0, height - 10),
            label_scale=btextscale,
            style=(
                'white_bright'
                if level == logging.DEBUG
                else 'blue' if effectivelevel <= logging.DEBUG else 'black'
            ),
            # style='bright' if level == logging.DEBUG else 'normal',
            call=partial(
                self._set_entry_val, entry_index, entry, logging.DEBUG
            ),
        )
        index += 1
        tab.button(
            'Info',
            pos=(x + width - bwidth * 4 + xoffs + 1.0, y + 5.0),
            size=(bwidth - 2.0, height - 10),
            label_scale=btextscale,
            style=(
                'white_bright'
                if level == logging.INFO
                else 'white' if effectivelevel <= logging.INFO else 'black'
            ),
            # style='bright' if level == logging.INFO else 'normal',
            call=partial(self._set_entry_val, entry_index, entry, logging.INFO),
        )
        index += 1
        tab.button(
            'Warning',
            pos=(x + width - bwidth * 3 + xoffs + 1.0, y + 5.0),
            size=(bwidth - 2.0, height - 10),
            label_scale=btextscale,
            style=(
                'white_bright'
                if level == logging.WARNING
                else 'yellow' if effectivelevel <= logging.WARNING else 'black'
            ),
            call=partial(
                self._set_entry_val, entry_index, entry, logging.WARNING
            ),
        )
        index += 1
        tab.button(
            'Error',
            pos=(x + width - bwidth * 2 + xoffs + 1.0, y + 5.0),
            size=(bwidth - 2.0, height - 10),
            label_scale=btextscale,
            style=(
                'white_bright'
                if level == logging.ERROR
                else 'red' if effectivelevel <= logging.ERROR else 'black'
            ),
            call=partial(
                self._set_entry_val, entry_index, entry, logging.ERROR
            ),
        )
        index += 1
        tab.button(
            'Critical',
            pos=(x + width - bwidth * 1 + xoffs + 1.0, y + 5.0),
            size=(bwidth - 2.0, height - 10),
            label_scale=btextscale,
            style=(
                'white_bright'
                if level == logging.CRITICAL
                else (
                    'purple' if effectivelevel <= logging.CRITICAL else 'black'
                )
            ),
            call=partial(
                self._set_entry_val, entry_index, entry, logging.CRITICAL
            ),
        )


class DevConsoleTabTest(DevConsoleTab):
    """Test dev-console tab."""

    @override
    def refresh(self) -> None:

        self.button(
            f'FLOOP-{random.randrange(200)}',
            pos=(10, 10),
            size=(100, 30),
            h_anchor='left',
            label_scale=0.6,
            call=self.request_refresh,
        )
        self.button(
            f'FLOOP2-{random.randrange(200)}',
            pos=(120, 10),
            size=(100, 30),
            h_anchor='left',
            label_scale=0.6,
            style='bright',
        )
        self.text(
            'TestText',
            scale=0.8,
            pos=(15, 50),
            h_anchor='left',
            h_align='left',
            v_align='none',
        )

        # Throw little bits of text in the corners to make sure
        # widths/heights are correct.
        self.text(
            'BL',
            scale=0.25,
            pos=(0, 0),
            h_anchor='left',
            h_align='left',
            v_align='bottom',
        )
        self.text(
            'BR',
            scale=0.25,
            pos=(self.width, 0),
            h_anchor='left',
            h_align='right',
            v_align='bottom',
        )
        self.text(
            'TL',
            scale=0.25,
            pos=(0, self.height),
            h_anchor='left',
            h_align='left',
            v_align='top',
        )
        self.text(
            'TR',
            scale=0.25,
            pos=(self.width, self.height),
            h_anchor='left',
            h_align='right',
            v_align='top',
        )
