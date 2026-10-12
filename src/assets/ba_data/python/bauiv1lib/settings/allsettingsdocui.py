# Released under the MIT License. See LICENSE for details.
#
"""The top level settings window, as a doc-ui page.

A client-local doc-ui domain: one centered row of big buttons leading
to the controls, graphics, audio and advanced settings pages; opened
by the toolbar's settings button. (Replaces the legacy
``AllSettingsWindow``.)
"""

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    PressSound,
    family_members,
)
import bauiv1 as bui
from bauiv1 import _classicassets
from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Literal

    from bacommon.docui import DocUIResponse
    from bacommon.langstr import LangStrSpec
    from bacommon.assetspec import TextureSpec

    from bauiv1lib.docui import DocUILocalAction

#: The buttons' unscaled size (the legacy window's), and their scale
#: and spacing: four just fill the wide layout's page width without
#: scrolling (the same total width as the play window's row).
_BW = 200.0
_BH = 230.0
_BUTTON_SCALE = 0.97
_BUTTON_SPACING = 20.0

#: How far below center the button row sits (space added above and
#: taken from below, so the page still fits without scrolling); reads
#: better under the title.
_ROW_DROP = 20.0

#: Labels sit a quarter of the way up the button and icons centered a
#: bit above middle, as in the legacy window. (Everything is centered
#: horizontally; the legacy window's small sideways icon nudges were
#: calibrated for its old, unevenly-fitting backing graphic.)
_LABEL_Y = _BH * 0.25 - _BH * 0.5
_ICON_Y = _BH * 0.56 - _BH * 0.5

_LABEL_COLOR = (0.7, 0.9, 0.7, 1.0)


class Target(Enum):
    """Where the page's buttons lead."""

    CONTROLLERS = 'controllers'
    GRAPHICS = 'graphics'
    AUDIO = 'audio'
    ADVANCED = 'advanced'


class SettingsRoute(DocUIRoute):
    """Family class for the settings routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnySettingsRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        return dui2.WindowLayout.WIDE


@ioprepped
@dataclass
class Root(SettingsRoute, path='/'):
    """The top level settings page."""


AnySettingsRoute = Root


class SettingsLocalAction(DocUILocalActionBase):
    """Family class for the settings local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnySettingsLocalAction)


@ioprepped
@dataclass
class Open(SettingsLocalAction, name='open'):
    """Go to a settings category."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH

    target: Annotated[Target, IOAttrs('t')]


AnySettingsLocalAction = Open


class AllSettingsController(
    TypedDocUIController[AnySettingsRoute, AnySettingsLocalAction]
):
    """Doc-ui controller for the top level settings page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[SettingsRoute]:
        return SettingsRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[SettingsLocalAction]:
        return SettingsLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def fulfill_route(self, route: AnySettingsRoute) -> DocUIResponse:
        match route:
            case Root():
                _preload_modules()
                return _page()
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnySettingsLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case Open():
                _open(action.target, context)
            case _:
                assert_never(action)


def _preload_modules() -> None:
    """Preload modules our buttons lead to (avoids hitches)."""
    # pylint: disable=cyclic-import
    import bauiv1lib.settings.controls as _unused1
    import bauiv1lib.settings.graphics as _unused2
    import bauiv1lib.settings.audio as _unused3
    import bauiv1lib.settings.advanced as _unused4


def _page() -> dui2.Response:
    """Build the page (called in a background thread)."""
    strs = _classicassets.strings.settings
    tex = _classicassets.textures
    return dui2.Response(
        page=dui2.Page(
            title=strs.title.spec,
            center_vertically=True,
            rows=[
                dui2.ButtonRow(
                    content_align=dui2.HAlign.CENTER,
                    button_spacing=_BUTTON_SPACING,
                    # Every bit of width goes to the buttons.
                    padding_left=0.0,
                    padding_right=0.0,
                    spacing_top=_ROW_DROP,
                    spacing_bottom=-_ROW_DROP,
                    buttons=[
                        _button(
                            Target.CONTROLLERS,
                            strs.controllers.title.spec,
                            tex.controller_icon,
                            icon_size=150.0,
                            icon_raise=2.0,
                            selected=True,
                        ),
                        _button(
                            Target.GRAPHICS,
                            strs.graphics.title.spec,
                            tex.graphics_icon,
                            icon_size=135.0,
                            icon_raise=4.0,
                        ),
                        _button(
                            Target.AUDIO,
                            strs.audio.title.spec,
                            tex.audio_icon,
                            icon_size=150.0,
                            icon_color=(1.0, 1.0, 0.0),
                        ),
                        _button(
                            Target.ADVANCED,
                            strs.advanced.title.spec,
                            tex.advanced_icon,
                            icon_size=150.0,
                            icon_raise=5.0,
                            icon_color=(0.8, 0.95, 1.0),
                        ),
                    ],
                )
            ],
        )
    )


def _button(
    target: Target,
    label: LangStrSpec,
    icon: TextureSpec,
    *,
    icon_size: float,
    icon_raise: float = 0.0,
    icon_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    selected: bool = False,
) -> dui2.Button:
    return dui2.Button(
        size=(_BW, _BH),
        scale=_BUTTON_SCALE,
        action=Open(target=target).local(),
        widget_id=target.value,
        selected=selected,
        decorations=[
            dui2.Image(
                texture=icon,
                position=(0.0, _ICON_Y + icon_raise),
                size=(icon_size, icon_size),
                color=(*icon_color, 1.0),
            ),
            dui2.Text(
                text=label,
                position=(0.0, _LABEL_Y),
                size=(_BW * 0.7, 40.0),
                color=_LABEL_COLOR,
            ),
        ],
    )


def _open(target: Target, context: DocUILocalAction) -> None:
    # pylint: disable=cyclic-import
    window = context.window

    # No-op if we're not in control.
    if not window.main_window_has_control():
        return
    match target:
        case Target.CONTROLLERS:
            from bauiv1lib.settings.controls import (
                ControlsSettingsController,
                Root as ControlsRoot,
            )

            window.main_window_replace(
                lambda: ControlsSettingsController().create_window(
                    ControlsRoot(),
                    origin_widget=context.widget,
                    auxiliary_style=False,
                ),
                extra_type_id=(
                    ControlsSettingsController.get_window_extra_type_id()
                ),
            )
        case Target.GRAPHICS:
            from bauiv1lib.settings.graphics import (
                GraphicsSettingsController,
                Root as GraphicsRoot,
            )

            window.main_window_replace(
                lambda: GraphicsSettingsController().create_window(
                    GraphicsRoot(),
                    origin_widget=context.widget,
                    auxiliary_style=False,
                ),
                extra_type_id=(
                    GraphicsSettingsController.get_window_extra_type_id()
                ),
            )
        case Target.AUDIO:
            from bauiv1lib.settings.audio import (
                AudioSettingsController,
                Root as AudioRoot,
            )

            window.main_window_replace(
                lambda: AudioSettingsController().create_window(
                    AudioRoot(),
                    origin_widget=context.widget,
                    auxiliary_style=False,
                ),
                extra_type_id=(
                    AudioSettingsController.get_window_extra_type_id()
                ),
            )
        case Target.ADVANCED:
            from bauiv1lib.settings.advanced import (
                AdvancedSettingsController,
                Root as AdvancedRoot,
            )

            window.main_window_replace(
                lambda: AdvancedSettingsController().create_window(
                    AdvancedRoot(),
                    origin_widget=context.widget,
                    auxiliary_style=False,
                ),
                extra_type_id=(
                    AdvancedSettingsController.get_window_extra_type_id()
                ),
            )
        case _:
            assert_never(target)
