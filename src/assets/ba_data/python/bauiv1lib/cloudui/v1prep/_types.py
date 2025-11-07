# Released under the MIT License. See LICENSE for details.
#
"""Prep functionality for our UI.

We do all layout math and bake out partial ui calls in a background
thread so there's as little work to do in the ui thread as possible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Callable

    import bacommon.cloudui.v1
    import bauiv1 as bui

    from bauiv1lib.cloudui._window import CloudUIWindow


@dataclass
class DecorationPrep:
    """Prep for a decoration in a v1 cloud-ui"""

    call: Callable[..., bui.Widget]
    textures: dict[str, str]
    meshes: dict[str, str]
    highlight: bool


@dataclass
class ButtonPrep:
    """Prep for a button in a v1 cloud-ui"""

    buttoncall: Callable[..., bui.Widget]
    buttoneditcall: Callable | None
    decorations: list[DecorationPrep]
    textures: dict[str, str]
    widgetid: str
    action: bacommon.cloudui.v1.Action | None


@dataclass
class RowPrep:
    """Prep for a row in a v1 cloud-ui"""

    width: float
    height: float
    titlecalls: list[Callable[..., bui.Widget]]
    hscrollcall: Callable[..., bui.Widget] | None
    hscrolleditcall: Callable | None
    hsubcall: Callable[..., bui.Widget] | None
    buttons: list[ButtonPrep]
    simple_culling_h: float
    decorations: list[DecorationPrep]


@dataclass
class PagePrep:
    """Prep for a page in a v1 cloud-ui"""

    rootcall: Callable[..., bui.Widget] | None
    rows: list[RowPrep]
    width: float
    height: float
    simple_culling_v: float
    center_vertically: bool
    title: str
    title_is_lstr: bool
    root_post_calls: list[Callable[[bui.Widget], None]]
