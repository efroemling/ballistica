# Released under the MIT License. See LICENSE for details.
#
"""Prepping doc-ui decorations and turning them into widgets."""

from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable, Sequence

    from bacommon.assetpackage import ApverNum
    import bacommon.docui.v2 as dui2

    from bauiv1lib.docui.prep._types import DecorationPrep


def prep_decorations_for_container(
    decorations: Sequence[dui2.Decoration],
    *,
    packages: list[ApverNum],
    allow_logic_thread: bool = False,
) -> Callable[..., None]:
    """Prep decorations for drawing into a plain container widget.

    This is how non-doc-ui windows draw doc-ui content (display-items
    in the inbox and chest windows, say). Does every bit of layout math
    up front and returns a single call that instantiates the whole
    batch at once; run that on the logic thread with
    ``parent=<container widget>``. Decoration positions are in the
    container's own coordinates.

    Prep is meant to run off the logic thread; doing otherwise
    reintroduces exactly the stutter the prep/instantiate split exists
    to prevent, so it logs a warning. Pass ``allow_logic_thread`` only
    if a caller genuinely has no other option. (Note this is unrelated
    to ``prep_page``'s ``immediate``, which concerns transition delays.)
    """
    if not allow_logic_thread and bui.in_logic_thread():
        bui.uilog.warning(
            'prep_decorations_for_container() called on the logic'
            ' thread; this blocks the ui while it runs. Prep from a'
            ' background thread, or pass allow_logic_thread=True if'
            ' there is genuinely no option.'
        )

    # pylint: disable=cyclic-import
    # Safe up-call: the prep package (which imports _calls2) is loaded
    # by the time anything gets prepped.
    import bauiv1lib.docui.prep._calls2 as prepcalls2

    decoration_preps: list[DecorationPrep] = []
    prepcalls2.prep_decorations(
        list(decorations),
        0.0,
        0.0,
        1.0,
        None,
        packages=packages,
        highlight=False,
        out_decoration_preps=decoration_preps,
    )

    def _instantiate(parent: bui.Widget) -> None:
        instantiate_decorations(decoration_preps, parent=parent)

    return _instantiate


def instantiate_decorations(
    decorations: list[DecorationPrep],
    *,
    parent: bui.Widget,
    draw_controller: bui.Widget | None = None,
) -> None:
    """Instantiate prepped decorations under a parent widget.

    The one place prepped decorations turn into live widgets. Asset
    refs are resolved here rather than at prep time because prep
    generally runs off the logic thread.

    Decorations carry no knowledge of where they live, so ``parent``
    fully determines that; this is what lets the same prepped
    decorations be drawn into a doc-ui page or into any plain
    container widget.

    ``draw_controller``, when passed, is applied to decorations whose
    ``highlight`` is set, tying their draw state to that widget (used
    for decorations layered over a button). Decorations drawn outside
    of a button context simply pass nothing here.
    """
    for decoration in decorations:
        kwds: dict = {'parent': parent}
        if draw_controller is not None and decoration.highlight:
            kwds['draw_controller'] = draw_controller
        for texarg, texname in decoration.textures.items():
            kwds[texarg] = bui.texture_from_ref(texname)
        for mesharg, meshname in decoration.meshes.items():
            kwds[mesharg] = bui.mesh_from_ref(meshname)
        decoration.call(**kwds)
