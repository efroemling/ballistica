# Released under the MIT License. See LICENSE for details.
#
"""Types used in prepping a doc-ui page for display.

Prepping involves doing as much math and layout work as possible in a
pre-pass (generally run in a background thread) so that the actual calls
made to instantiate the ui are as fast and minimal as possible.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable

    import bacommon.docui.v2
    import bauiv1

    from bauiv1lib.docui._window import DocUIWindow


@dataclass
class DecorationPrep:
    """Prep for a decoration in a doc-ui."""

    call: Callable[..., bauiv1.Widget]
    textures: dict[str, str]
    meshes: dict[str, str]
    highlight: bool


@dataclass
class ButtonPrep:
    """Prep for a button in a doc-ui."""

    buttoncall: Callable[..., bauiv1.Widget]
    buttoneditcall: Callable | None
    decorations: list[DecorationPrep]
    textures: dict[str, str]
    widgetid: str
    action: bacommon.docui.v2.Action | None


@dataclass
class RowPrep:
    """Prep for a row in a doc-ui."""

    width: float
    height: float
    titlecalls: list[Callable[..., bauiv1.Widget]]
    hscrollcall: Callable[..., bauiv1.Widget] | None
    hscrolleditcall: Callable | None
    hsubcall: Callable[..., bauiv1.Widget] | None
    buttons: list[ButtonPrep]
    simple_culling_h: float
    decorations: list[DecorationPrep]


@dataclass
class PagePrep:
    """Prep for a page in a doc-ui."""

    rootcall: Callable[..., bauiv1.Widget] | None
    rows: list[RowPrep]
    width: float
    height: float
    simple_culling_v: float
    center_vertically: bool
    #: Native language-string title handle.
    title: bauiv1.LangStr
    root_post_calls: list[Callable[[bauiv1.Widget], None]]
