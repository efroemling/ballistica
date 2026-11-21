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
    :attr:`LAYOUT` is windows' and popups' own (no page asks for it):
    the rects a page is laid out against -- where its scroll area
    reaches out to, the content rect its layout gives it, and where its
    content starts within that by its insets -- plus where the scroll
    area's edge fades end, and any viewer pane.
    :attr:`SHOW_AREAS` shows, for whichever row is selected, what
    selecting it must bring into view: its titles and footnote, plus
    any section heading or note attached to it. Selection brings that
    to the page's inset rect at least, and nudges it further toward the
    middle (unless the "DocUI No Selection Centering" toggle is on).
    """

    ROWS = 'rows'
    SECTIONS = 'sections'
    BUTTONS = 'buttons'
    DECORATIONS = 'decorations'
    LAYOUT = 'layout'
    SHOW_AREAS = 'show_areas'


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
        case DebugDrawKind.LAYOUT:
            return 'DocUI Layout'
        case DebugDrawKind.SHOW_AREAS:
            return 'DocUI Show Areas'
        case _:
            assert_never(kind)


_g_no_selection_centering = False


def selection_centering_disabled() -> bool:
    """Whether selecting a row should scroll it only just into view.

    Normally selection nudges what it brings into view toward the
    middle of the scroll area; with this on (a debugging aid) it
    scrolls only far enough to bring a row's must-show area to the
    page's inset rect. Safe from any thread (page prep runs in the
    background).
    """
    return _g_no_selection_centering


def set_selection_centering_disabled(disabled: bool) -> None:
    """Turn selection centering off (or back on); see above.

    Rebuilds the main window in place to apply it. Not saved; off at
    launch.
    """
    global _g_no_selection_centering  # pylint: disable=global-statement
    if disabled == _g_no_selection_centering:
        return
    _g_no_selection_centering = disabled
    bui.app.ui_v1.request_main_window_recreate()


def get_debug_draw_toggles() -> list[bui.DevConsoleToggleDef]:
    """Dev-console toggles for our kinds, for an app-mode to offer.

    Plus one that turns off selection centering, so show areas land
    exactly on their target. See
    :meth:`babase.AppMode.get_dev_console_ui_debug_draw_toggles`.
    """
    return [
        *(
            bui.DevConsoleToggleDef(
                _toggle_label(kind),
                partial(debug_draw_enabled, kind),
                partial(set_debug_draw_enabled, kind),
            )
            for kind in DebugDrawKind
        ),
        bui.DevConsoleToggleDef(
            'DocUI No Selection Centering',
            selection_centering_disabled,
            set_selection_centering_disabled,
        ),
    ]
