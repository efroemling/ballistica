# Released under the MIT License. See LICENSE for details.
#
"""Dev-Console functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
import logging

import _babase

if TYPE_CHECKING:
    from typing import Callable, Any, Literal


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

    def refresh(self) -> None:
        self.python_terminal()


class DevConsoleTabTest(DevConsoleTab):
    """Test dev-console tab."""

    def refresh(self) -> None:
        import random

        self.button(
            f'FLOOP-{random.randrange(200)}',
            pos=(10, 10),
            size=(100, 30),
            h_anchor='left',
            call=self.request_refresh,
        )


@dataclass
class DevConsoleTabEntry:
    """Represents a distinct tab in the dev-console."""

    name: str
    factory: Callable[[], DevConsoleTab]


class DevConsoleSubsystem:
    """Wrangles the dev console."""

    def __init__(self) -> None:
        # All tabs in the dev-console. Add your own stuff here via
        # plugins or whatnot.
        self.tabs: list[DevConsoleTabEntry] = [
            DevConsoleTabEntry('Python', DevConsoleTabPython),
            DevConsoleTabEntry('Test', DevConsoleTabTest),
        ]
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
