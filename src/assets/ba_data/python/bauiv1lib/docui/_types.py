# Released under the MIT License. See LICENSE for details.
#
"""Shared public types for doc-ui."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bauiv1 as bui

    from bauiv1lib.docui._window import DocUIWindow


@dataclass
class DocUILocalAction:
    """Context for a local-action."""

    name: str
    args: dict
    widget: bui.Widget | None
    window: DocUIWindow
