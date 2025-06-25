# Released under the MIT License. See LICENSE for details.
#
"""Dev-Console functionality."""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from typing import Callable, Any, Literal


class DevConsoleTab:
    """Base class for a :class:`~babase.DevConsoleSubsystem` tab."""

    def refresh(self) -> None:
        """Called when the tab should refresh itself.

        Overridden by subclasses to implement tab behavior.
        """

    def request_refresh(self) -> None:
        """The tab can call this to request that it be refreshed."""
        _babase.dev_console_request_refresh()

    def button(
        self,
        label: str,
        pos: tuple[float, float],
        size: tuple[float, float],
        call: Callable[[], Any] | None = None,
        *,
        h_anchor: Literal['left', 'center', 'right'] = 'center',
        label_scale: float = 1.0,
        corner_radius: float = 8.0,
        style: Literal[
            'normal',
            'bright',
            'red',
            'red_bright',
            'purple',
            'purple_bright',
            'yellow',
            'yellow_bright',
            'blue',
            'blue_bright',
            'white',
            'white_bright',
            'black',
            'black_bright',
        ] = 'normal',
        disabled: bool = False,
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
            disabled,
        )

    def text(
        self,
        text: str,
        pos: tuple[float, float],
        *,
        h_anchor: Literal['left', 'center', 'right'] = 'center',
        h_align: Literal['left', 'center', 'right'] = 'center',
        v_align: Literal['top', 'center', 'bottom', 'none'] = 'center',
        scale: float = 1.0,
        style: Literal['normal', 'faded'] = 'normal',
    ) -> None:
        """Add a button to the tab being refreshed."""
        assert _babase.app.devconsole.is_refreshing
        _babase.dev_console_add_text(
            text, pos[0], pos[1], h_anchor, h_align, v_align, scale, style
        )

    def python_terminal(self) -> None:
        """Add a Python Terminal to the tab being refreshed."""
        assert _babase.app.devconsole.is_refreshing
        _babase.dev_console_add_python_terminal()

    @property
    def width(self) -> float:
        """The current tab width. Only valid during refreshes."""
        assert _babase.app.devconsole.is_refreshing
        return _babase.dev_console_tab_width()

    @property
    def height(self) -> float:
        """The current tab height. Only valid during refreshes."""
        assert _babase.app.devconsole.is_refreshing
        return _babase.dev_console_tab_height()

    @property
    def base_scale(self) -> float:
        """A scale value based on the app's current :class:`~babase.UIScale`.

        Dev-console tabs can manually incorporate this into their UI
        sizes and positions if they desire. By default, dev-console tabs
        are uniform across all ui-scales.
        """
        assert _babase.app.devconsole.is_refreshing
        return _babase.dev_console_base_scale()


@dataclass
class DevConsoleTabEntry:
    """Represents a distinct tab in the :class:`~babase.DevConsoleSubsystem`."""

    name: str
    factory: Callable[[], DevConsoleTab]


class DevConsoleSubsystem:
    """Subsystem for wrangling the dev-console.

    Access the single shared instance of this class via the
    :attr:`~babase.App.devconsole` attr on the :class:`~babase.App`
    class.

    The dev-console is a simple always-available UI intended for use by
    developers; not end users. Traditionally it is available by typing a
    backtick (`) key on a keyboard, but can also be accessed via an
    on-screen button (see settings/advanced/dev-tools to enable said
    button).
    """

    def __init__(self) -> None:
        # pylint: disable=cyclic-import
        from babase._devconsoletabs import (
            DevConsoleTabPython,
            DevConsoleTabAppModes,
            DevConsoleTabUI,
            DevConsoleTabLogging,
            DevConsoleTabTest,
        )

        #: All tabs in the dev-console. Add your own stuff here via
        #: plugins or whatnot to customize the console.
        self.tabs: list[DevConsoleTabEntry] = [
            DevConsoleTabEntry('Python', DevConsoleTabPython),
            DevConsoleTabEntry('AppModes', DevConsoleTabAppModes),
            DevConsoleTabEntry('UI', DevConsoleTabUI),
            DevConsoleTabEntry('Logging', DevConsoleTabLogging),
        ]
        if os.environ.get('BA_DEV_CONSOLE_TEST_TAB', '0') == '1':
            self.tabs.append(DevConsoleTabEntry('Test', DevConsoleTabTest))
        self.is_refreshing = False
        self._tab_instances: dict[str, DevConsoleTab] = {}

    def save_tab(self, tabname: str) -> None:
        """Called by the C++ layer when we should store tab to config."""
        cfg = _babase.app.config
        cfg['Dev Console Tab'] = tabname
        cfg.commit()

    def do_refresh_tab(self, tabname: str) -> None:
        """Called by the C++ layer when a tab should be filled out.

        :meta private:
        """
        assert _babase.in_logic_thread()

        # Make noise if we have repeating tab names, as that breaks our
        # logic.
        if __debug__:
            alltabnames = set[str](tabentry.name for tabentry in self.tabs)
            if len(alltabnames) != len(self.tabs):
                logging.error(
                    'Duplicate dev-console tab names found;'
                    ' tabs may behave unpredictably.'
                )

        tab: DevConsoleTab | None = self._tab_instances.get(tabname)

        # If we haven't instantiated this tab yet, do so.
        if tab is None:
            for tabentry in self.tabs:
                if tabentry.name == tabname:
                    tab = self._tab_instances[tabname] = tabentry.factory()
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
