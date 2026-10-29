# Released under the MIT License. See LICENSE for details.
#
"""Host-defined menu buttons (see :mod:`baclassic._hostui`)."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

import bacommon.hostui as hui

from baclassic._hostuiparts import host_ui_text

if TYPE_CHECKING:
    from typing import Literal

    import bacommon.docui.v2
    from bacommon.langstr import LangStrSpec

    import babase


@dataclass
class HostUIButton:
    """A button a host puts on its clients' (and its own) ui.

    Pressing it opens a page in a doc-ui window, as :attr:`browse` says,
    which the host's :class:`HostUIHandler` serves. Make one with a
    route's :meth:`~bacommon.docui.routes.DocUIRoute.browse`, as for a
    page's own links::

        HostUIButton(
            label='Rules',
            browse=Rules().browse(
                layout=bacommon.docui.v2.WindowLayout.WIDE,
                background_color=(0.3, 0.2, 0.4),
            ),
        )
    """

    #: The label. Plain text is shown as-is; a language-string must
    #: come from one of the host's own asset-packages (clients refuse
    #: anything else).
    label: str | babase.LangStr | LangStrSpec

    #: How the button opens its page, as made by a route's ``browse()``.
    #: It carries the route's request, any state to send with it, and
    #: the window's look (layout, scroll edge style, frame colors). Its
    #: ``sets``, ``add_to_history`` and ``default_sound`` don't apply to
    #: menu buttons. Clients before
    #: build 23075 use only its request, state and layout.
    browse: bacommon.docui.v2.Browse

    #: Where the button goes.
    placement: Literal['in_game_menu', 'party_menu'] = 'in_game_menu'


def button_to_wire(button: HostUIButton) -> hui.Button:
    """A host button as sent to clients.

    :meta private:
    """
    placement: hui.ButtonPlacement
    match button.placement:
        case 'in_game_menu':
            placement = hui.ButtonPlacement.IN_GAME_MENU
        case 'party_menu':
            placement = hui.ButtonPlacement.PARTY_MENU
        case _:
            assert_never(button.placement)
    return hui.Button.for_browse(
        label=host_ui_text(button.label),
        placement=placement,
        browse=button.browse,
    )
