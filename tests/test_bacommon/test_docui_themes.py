# Released under the MIT License. See LICENSE for details.
#
"""Tests for doc-ui page looks (flat page and link look values)."""

from efro.dataclassio import dataclass_to_dict, dataclass_from_dict

import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue
from bacommon.docui.routes import validate_route_page

# Note: importing as a module since pytest tries to collect 'Test*'
# classes it finds in test module namespaces.
import bacommon.docui.routes.docuitest as rt


def _page(**kwargs: float | tuple[float, float, float] | None) -> dui2.Page:
    page = dui2.Page(
        title=LangStrSpecValue.literal('x'),
        rows=[],
        state=rt.ThemesState().encode(),
    )
    for key, val in kwargs.items():
        setattr(page, key, val)
    return page


def test_page_look_wire_form() -> None:
    """Page look values encode compactly, and old meanings stay put."""
    page = _page(default_button_color=(1.0, 0.0, 0.0), h_inset=12.0)
    out = dataclass_to_dict(page)
    assert out['dbc'] == [1.0, 0.0, 0.0]
    assert out['hi'] == 12.0
    assert 'bc' not in out
    assert 'vi' not in out
    assert dataclass_from_dict(dui2.Page, out) == page

    # A vertical inset of 0 is a real value, not "unset".
    out = dataclass_to_dict(_page(v_inset=0.0))
    assert out['vi'] == 0.0

    # An unset row spacing is left off the wire, which builds before
    # PAGE_LOOK_BUILD read as their old default of 10.
    assert 's' not in dataclass_to_dict(_page())

    # Pages carrying look values validate like any other.
    validate_route_page(rt.Themes(), _page(button_color=(1.0, 1.0, 1.0)))
    validate_route_page(rt.ThemesPopup(), _page(h_inset=20.0))


def test_frame_colors_ride_links() -> None:
    """Frame colors go on the links that open windows and popups."""
    browse = rt.Themes().browse()
    assert browse.background_color is None
    assert browse.cancel_button_color is None
    assert 'bg' not in dataclass_to_dict(browse)

    browse = rt.Themes().browse(
        background_color=(0.1, 0.2, 0.3), cancel_button_color=(0.4, 0.5, 0.6)
    )
    out = dataclass_to_dict(browse)
    assert out['bg'] == [0.1, 0.2, 0.3]
    assert out['cbc'] == [0.4, 0.5, 0.6]

    popup = rt.ThemesPopup().popup(background_color=(0.1, 0.2, 0.3))
    assert popup.background_color == (0.1, 0.2, 0.3)
    assert popup.cancel_button_color is None
    # (Left unset, a popup's frame is the client's popup green.)
    assert rt.ThemesPopup().popup().background_color is None
