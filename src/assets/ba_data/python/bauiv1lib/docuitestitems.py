# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui display-items test page.

A display-item stays what it always was -- *show this thing in this
style*. What changes is what that turns into: the depiction now comes
as a :class:`~bacommon.docui.v2.Frame` rather than being derived
client-side from the item type.

This page began as an A/B of the two, which is how their equivalence
was established. The client no longer draws the legacy decoration at
all, so what is left is a renderer regression check -- every item type
and style, drawable with no server and no account.

See ``docs/initiatives/docui-frames.md``.
"""

from typing import TYPE_CHECKING

from bacommon.langstr import LangStrSpecValue
import bacommon.legacydisplayitem as lditm
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.v2


#: Each (style, bounds, x-offset) slot on a test button, paired with the
#: y-offsets below. The left of each pair shows the item normally; the
#: right shows it with its type stripped, exercising the display-item
#: path's baked-description fallback.
_SLOTS: list[tuple[dui2.DisplayItemStyle, tuple[float, float], float]] = [
    (dui2.DisplayItemStyle.FULL, (120, 120), 62),
    (dui2.DisplayItemStyle.COMPACT, (80, 80), 55),
    (dui2.DisplayItemStyle.ICON, (100, 80), 55),
]
_SLOT_YS = [100.0, -20.0, -120.0]


def test_page_display_items(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """Testing display-items (v2 mirror of '/displayitems')."""
    import copy

    from bacommon.classic import ClassicChestAppearance, ClassicChestDisplayItem

    # pylint: disable=cyclic-import
    # Safe up-call: baclassic is fully imported by the time a doc-ui
    # page is being authored.
    from baclassic import display_item_frame

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    def _make_test_button(
        scale: float,
        wrapper: lditm.Wrapper,
    ) -> bacommon.docui.v2.Button:

        # See how this looks when unrecognized (relying on wrapper info
        # only).
        uwrapper = copy.deepcopy(wrapper)
        uwrapper.item = lditm.Unknown()

        decorations: list[dui2.Decoration] = []
        for (style, size, xoffs), yoffs in zip(_SLOTS, _SLOT_YS):
            for wrp, xsign in ((wrapper, -1.0), (uwrapper, 1.0)):
                if wrp is uwrapper:
                    # Skip the fallback copy: it is the *same* item with
                    # its type stripped, and a frame depicts an
                    # unrecognized item exactly as it depicts a known
                    # one, so it would just render twice.
                    continue
                decorations.append(
                    display_item_frame(
                        wrp,
                        position=(xoffs * xsign, yoffs),
                        size=size,
                        style=style,
                        debug=debug,
                    )
                )

        return dui2.Button(
            size=(300, 400),
            scale=scale,
            decorations=decorations,
        )

    return dui2.Response(
        page=dui2.Page(
            padding_left=20,
            padding_right=20,
            title=strs.items.display_items.spec,
            rows=[
                dui2.ButtonRow(
                    debug=debug,
                    padding_left=-10,
                    title=strs.items.display_item_tests.spec,
                    subtitle=LangStrSpecValue.literal(
                        'top=FULL, center=COMPACT, bottom=ICON'
                    ),
                    buttons=[
                        _make_test_button(
                            1.0,
                            lditm.Wrapper.for_item(lditm.Tickets(count=213)),
                        ),
                        _make_test_button(
                            0.47,
                            lditm.Wrapper.for_item(lditm.Tickets(count=213)),
                        ),
                        _make_test_button(
                            1.0,
                            lditm.Wrapper.for_item(
                                ClassicChestDisplayItem(
                                    appearance=ClassicChestAppearance.L3
                                )
                            ),
                        ),
                        _make_test_button(
                            1.0,
                            lditm.Wrapper.for_item(lditm.Tokens(count=3)),
                        ),
                        _make_test_button(
                            1.0,
                            lditm.Wrapper.for_item(lditm.Tokens(count=1414287)),
                        ),
                        _make_test_button(
                            1.0,
                            lditm.Wrapper.for_item(lditm.Test()),
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=(
                                strs.common.hide_debug.spec
                                if debug
                                else strs.common.show_debug.spec
                            ),
                            style=dui2.ButtonStyle.MEDIUM,
                            size=(240, 60),
                            color=(0.6, 0.4, 0.8, 1.0),
                            action=dui2.Replace(
                                dui2.Request(
                                    request.path,
                                    args={'debug': not debug},
                                )
                            ),
                        ),
                    ],
                ),
            ],
        )
    )
