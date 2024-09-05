# Released under the MIT License. See LICENSE for details.
#
"""Dev-Console functionality."""
from __future__ import annotations

import os
import logging
from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import _babase

if TYPE_CHECKING:
    from typing import Callable, Any, Literal

    from babase import AppMode, UIScale


class DevConsoleTab:
    """Defines behavior for a tab in the dev-console."""

    def refresh(self) -> None:
        """Called when the tab should refresh itself."""

    def request_refresh(self) -> None:
        """The tab can call this to request that it be refreshed."""
        _babase.dev_console_request_refresh()

    def button(
        self,
        label: str,
        pos: tuple[float, float],
        size: tuple[float, float],
        call: Callable[[], Any] | None = None,
        h_anchor: Literal['left', 'center', 'right'] = 'center',
        label_scale: float = 1.0,
        corner_radius: float = 8.0,
        style: Literal['normal', 'light'] = 'normal',
    ) -> None:
        """Add a button to the tab being refreshed."""
        assert _babase.app.devconsole.is_refreshing
        _babase.dev_console_add_button(
            label,
            pos[0],
            pos[1],
            size[0],
            size[1],
            call,
            h_anchor,
            label_scale,
            corner_radius,
            style,
        )

    def text(
        self,
        text: str,
        pos: tuple[float, float],
        h_anchor: Literal['left', 'center', 'right'] = 'center',
        h_align: Literal['left', 'center', 'right'] = 'center',
        v_align: Literal['top', 'center', 'bottom', 'none'] = 'center',
        scale: float = 1.0,
    ) -> None:
        """Add a button to the tab being refreshed."""
        assert _babase.app.devconsole.is_refreshing
        _babase.dev_console_add_text(
            text, pos[0], pos[1], h_anchor, h_align, v_align, scale
        )

    def python_terminal(self) -> None:
        """Add a Python Terminal to the tab being refreshed."""
        assert _babase.app.devconsole.is_refreshing
        _babase.dev_console_add_python_terminal()

    @property
    def width(self) -> float:
        """Return the current tab width. Only call during refreshes."""
        assert _babase.app.devconsole.is_refreshing
        return _babase.dev_console_tab_width()

    @property
    def height(self) -> float:
        """Return the current tab height. Only call during refreshes."""
        assert _babase.app.devconsole.is_refreshing
        return _babase.dev_console_tab_height()

    @property
    def base_scale(self) -> float:
        """A scale value set depending on the app's UI scale.

        Dev-console tabs can incorporate this into their UI sizes and
        positions if they desire. This must be done manually however.
        """
        assert _babase.app.devconsole.is_refreshing
        return _babase.dev_console_base_scale()


class DevConsoleTabPython(DevConsoleTab):
    """The Python dev-console tab."""

    @override
    def refresh(self) -> None:
        self.python_terminal()


class DevConsoleTabAppModes(DevConsoleTab):
    """Tab to switch app modes."""

    @override
    def refresh(self) -> None:

        modes = _babase.app.mode_selector.testable_app_modes()
        self.text(
            'Available AppModes:',
            scale=0.8,
            pos=(15, 55),
            h_anchor='left',
            h_align='left',
            v_align='none',
        )
        for i, mode in enumerate(modes):
            self.button(
                f'{mode.__module__}.{mode.__qualname__}',
                pos=(10 + i * 260, 10),
                size=(250, 40),
                h_anchor='left',
                label_scale=0.6,
                call=partial(self._set_app_mode, mode),
            )

    @staticmethod
    def _set_app_mode(mode: type[AppMode]) -> None:
        from babase._appintent import AppIntentDefault

        intent = AppIntentDefault()

        # Use private functionality to force a specific app-mode to
        # handle this intent. Note that this should never be done
        # outside of this explicit testing case. It is the app's job to
        # determine which app-mode should be used to handle a given
        # intent.
        setattr(intent, '_force_app_mode_handler', mode)

        _babase.app.set_intent(intent)


class DevConsoleTabUI(DevConsoleTab):
    """Tab to debug/test UI stuff."""

    @override
    def refresh(self) -> None:
        from babase._mgen.enums import UIScale

        # self.text(
        #     'UI Testing',
        #     scale=0.8,
        #     pos=(15, 77),
        #     h_anchor='left',
        #     h_align='left',
        #     v_align='center',
        # )
        self.text(
            'Make sure all static UI fits in the'
            ' virtual screen at all UI scales (not counting things'
            ' that follow screen edges).\n'
            'Note that some UI elements'
            ' may not reflect scale changes until recreated.',
            scale=0.6,
            pos=(15, 70),
            h_anchor='left',
            h_align='left',
            v_align='center',
        )

        ui_overlay = _babase.get_draw_ui_bounds()
        self.button(
            'Virtual Bounds ON' if ui_overlay else 'Virtual Bounds OFF',
            pos=(10, 10),
            size=(200, 30),
            h_anchor='left',
            label_scale=0.6,
            call=self.toggle_ui_overlay,
            style='light' if ui_overlay else 'normal',
        )
        x = 300
        self.text(
            'UI Scale',
            pos=(x - 5, 15),
            h_anchor='left',
            h_align='right',
            v_align='none',
            scale=0.6,
        )

        bwidth = 100
        for scale in UIScale:
            self.button(
                scale.name.lower(),
                pos=(x, 10),
                size=(bwidth, 30),
                h_anchor='left',
                label_scale=0.6,
                call=partial(_babase.app.set_ui_scale, scale),
                style=(
                    'light' if scale is _babase.app.ui_v1.uiscale else 'normal'
                ),
            )
            x += bwidth + 2

    def toggle_ui_overlay(self) -> None:
        """Toggle UI overlay drawing."""
        _babase.set_draw_ui_bounds(not _babase.get_draw_ui_bounds())
        self.request_refresh()


class DevConsoleTabTest(DevConsoleTab):
    """Test dev-console tab."""

    @override
    def refresh(self) -> None:
        import random

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
            style='light',
        )
        self.text(
            'TestText',
            scale=0.8,
            pos=(15, 50),
            h_anchor='left',
            h_align='left',
            v_align='none',
        )


@dataclass
class DevConsoleTabEntry:
    """Represents a distinct tab in the dev-console."""

    name: str
    factory: Callable[[], DevConsoleTab]


class DevConsoleSubsystem:
    """Subsystem for wrangling the dev console.

    The single instance of this class can be found at
    babase.app.devconsole. The dev-console is a simple always-available
    UI intended for use by developers; not end users. Traditionally it
    is available by typing a backtick (`) key on a keyboard, but now can
    be accessed via an on-screen button (see settings/advanced to enable
    said button).
    """

    def __init__(self) -> None:
        # All tabs in the dev-console. Add your own stuff here via
        # plugins or whatnot.
        self.tabs: list[DevConsoleTabEntry] = [
            DevConsoleTabEntry('Python', DevConsoleTabPython),
            DevConsoleTabEntry('AppModes', DevConsoleTabAppModes),
            DevConsoleTabEntry('UI', DevConsoleTabUI),
        ]
        if os.environ.get('BA_DEV_CONSOLE_TEST_TAB', '0') == '1':
            self.tabs.append(DevConsoleTabEntry('Test', DevConsoleTabTest))
        self.is_refreshing = False

    def do_refresh_tab(self, tabname: str) -> None:
        """Called by the C++ layer when a tab should be filled out."""
        assert _babase.in_logic_thread()

        # FIXME: We currently won't handle multiple tabs with the same
        # name. We should give a clean error or something in that case.
        tab: DevConsoleTab | None = None
        for tabentry in self.tabs:
            if tabentry.name == tabname:
                tab = tabentry.factory()
                break

        if tab is None:
            logging.error(
                'DevConsole got refresh request for tab'
                " '%s' which does not exist.",
                tabname,
            )
            return

        self.is_refreshing = True
        try:
            tab.refresh()
        finally:
            self.is_refreshing = False
