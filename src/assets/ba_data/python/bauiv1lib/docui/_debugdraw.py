# Released under the MIT License. See LICENSE for details.
#
"""Debug drawing for whole kinds of doc-ui elements at once."""

from enum import Enum
from functools import partial
from typing import assert_never

import bauiv1 as bui


class DebugDrawKind(Enum):
    """Kinds of doc-ui element whose debug drawing can be forced on.

    Each element of a page can ask for its own debug drawing (its
    ``debug`` flag); switching a kind on here draws it for every such
    element on every page, whatever the page says.
    """

    ROWS = 'rows'
    SECTIONS = 'sections'
    BUTTONS = 'buttons'
    DECORATIONS = 'decorations'


_enabled: set[DebugDrawKind] = set()


def debug_draw_enabled(kind: DebugDrawKind) -> bool:
    """Whether debug drawing is forced on for a kind of element."""
    return kind in _enabled


def wants_debug_draw(own_flag: bool, kind: DebugDrawKind) -> bool:
    """Whether an element should draw its debug drawing.

    True if it asks for it itself (its ``debug`` flag) or its kind is
    forced on. Safe from any thread (page prep runs in the background).
    """
    return own_flag or kind in _enabled


def set_debug_draw_enabled(kind: DebugDrawKind, enabled: bool) -> None:
    """Force debug drawing on (or stop forcing it) for a kind of element.

    Pages draw these as they are laid out, so the main window is
    rebuilt in place to show the change; anything else showing doc-ui
    picks it up the next time it lays out. Not saved; off at launch.
    """
    if enabled == (kind in _enabled):
        return
    if enabled:
        _enabled.add(kind)
    else:
        _enabled.discard(kind)
    bui.app.ui_v1.request_main_window_recreate()


def _toggle_label(kind: DebugDrawKind) -> str:
    match kind:
        case DebugDrawKind.ROWS:
            return 'DocUI Rows'
        case DebugDrawKind.SECTIONS:
            return 'DocUI Sections'
        case DebugDrawKind.BUTTONS:
            return 'DocUI Buttons'
        case DebugDrawKind.DECORATIONS:
            return 'DocUI Decorations'
        case _:
            assert_never(kind)


def get_debug_draw_toggles() -> list[bui.DevConsoleToggleDef]:
    """Dev-console toggles for our kinds, for an app-mode to offer.

    See :meth:`babase.AppMode.get_dev_console_ui_debug_draw_toggles`.
    """
    return [
        bui.DevConsoleToggleDef(
            _toggle_label(kind),
            partial(debug_draw_enabled, kind),
            partial(set_debug_draw_enabled, kind),
        )
        for kind in DebugDrawKind
    ]
