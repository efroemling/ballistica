# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui widgets that client-effects can animate.

A page's decorations and buttons can carry an ``anim_id``; as a window
builds the page it records each such widget here along with its
as-laid-out geometry. Client-effects
(``bacommon.clienteffect.KeyframeAnimation``) then find targets by id
and set animation states relative to that geometry. Everything sharing
an id animates together (a button and its decorations, say). This is
the doc-ui implementation of the effects runner's ``EffectTargets``
protocol (see ``baclassic._clienteffect``); nothing here knows about
effects.
"""

from typing import TYPE_CHECKING, assert_never

import bauiv1 as bui

from bauiv1lib.docui.prep._types import AnimTargetKind

if TYPE_CHECKING:
    from bauiv1lib.docui.prep._types import AnimTargetPrep


class DocUIAnimTarget:
    """One animatable widget of a doc-ui page."""

    def __init__(self, prep: AnimTargetPrep, widget: bui.Widget) -> None:
        self._prep = prep
        self._widget = widget

    @property
    def widget(self) -> bui.Widget:
        """The widget this target drives."""
        return self._widget

    def set_animation_state(
        self,
        *,
        offset: tuple[float, float],
        scale: float,
        opacity: float | None,
    ) -> None:
        """Show the widget offset and scaled from its base state.

        ``offset`` is in the widget's own (page) units and ``scale`` is
        about the widget's center (text scales about its anchor).
        ``opacity`` is absolute; None for the widget's base opacity.
        """
        if not self._widget:
            return
        prep = self._prep
        opac = prep.opacity if opacity is None else opacity
        if prep.kind is AnimTargetKind.IMAGE:
            width = prep.size[0] * scale
            height = prep.size[1] * scale
            bui.imagewidget(
                edit=self._widget,
                position=(
                    prep.position[0] + offset[0] + (prep.size[0] - width) * 0.5,
                    prep.position[1]
                    + offset[1]
                    + (prep.size[1] - height) * 0.5,
                ),
                size=(width, height),
                opacity=opac,
            )
        elif prep.kind is AnimTargetKind.BUTTON:
            # Buttons scale about their bottom-left; keep them centered.
            grow = prep.scale * (1.0 - scale) * 0.5
            bui.buttonwidget(
                edit=self._widget,
                position=(
                    prep.position[0] + offset[0] + prep.size[0] * grow,
                    prep.position[1] + offset[1] + prep.size[1] * grow,
                ),
                scale=prep.scale * scale,
                opacity=opac,
            )
        elif prep.kind is AnimTargetKind.TEXT:
            rgb = (1.0, 1.0, 1.0) if prep.color is None else prep.color
            bui.textwidget(
                edit=self._widget,
                position=(
                    prep.position[0] + offset[0],
                    prep.position[1] + offset[1],
                ),
                scale=prep.scale * scale,
                color=(*rgb, opac),
            )
        else:
            assert_never(prep.kind)


class DocUIAnimGroup:
    """Every live widget of a page sharing one ``anim_id``."""

    def __init__(self, targets: list[DocUIAnimTarget]) -> None:
        self._targets = targets

    def set_animation_state(
        self,
        *,
        offset: tuple[float, float],
        scale: float,
        opacity: float | None,
    ) -> None:
        """Set all our targets' state; see DocUIAnimTarget."""
        for target in self._targets:
            target.set_animation_state(
                offset=offset, scale=scale, opacity=opacity
            )


class DocUIAnimTargets:
    """The animatable widgets of a doc-ui window's current page.

    Refilled every time the window builds a page, so lookups made by
    id always reach the current widgets (an animation running across
    a rebuild carries on with the new ones).
    """

    def __init__(self) -> None:
        self._targets: dict[str, list[DocUIAnimTarget]] = {}

    def clear(self) -> None:
        """Forget all targets (the page is being rebuilt)."""
        self._targets.clear()

    def register(self, prep: AnimTargetPrep, widget: bui.Widget) -> None:
        """Note a widget just built for something with an ``anim_id``."""
        self._targets.setdefault(prep.anim_id, []).append(
            DocUIAnimTarget(prep, widget)
        )

    def get_target(self, target_id: str) -> DocUIAnimGroup | None:
        """Return everything live with an id, if there is anything."""
        targets = [t for t in self._targets.get(target_id, []) if t.widget]
        if not targets:
            return None
        return DocUIAnimGroup(targets)
