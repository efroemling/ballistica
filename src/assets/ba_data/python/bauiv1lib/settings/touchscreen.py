# Released under the MIT License. See LICENSE for details.
#
"""Touchscreen control settings, as a doc-ui page.

A client-local doc-ui domain like the other settings pages: the
settings live in typed page state mirroring the config, and each
change is a typed local action writing it. While a window showing the
page is up, the touch controls themselves are in editing mode, so they
can be dragged around behind it.
"""

import weakref
from enum import Enum
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.docui.v2 as dui2
from bacommon.docui.presets import SectionButtonSize, section_button
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    DocUIState,
    family_members,
)
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets
from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Literal, Callable

    import bacommon.docui
    from bacommon.docui import DocUIRequest, DocUIResponse
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui import DocUILocalAction, DocUIWindow

_tsstrs = _classicassets.strings.settings.controllers.touchscreen

_MOVEMENT_KEY = 'Touch Movement Control Type'
_ACTIONS_KEY = 'Touch Action Control Type'
_MOVEMENT_SCALE_KEY = 'Touch Controls Scale Movement'
_ACTIONS_SCALE_KEY = 'Touch Controls Scale Actions'
_SWIPE_HIDDEN_KEY = 'Touch Controls Swipe Hidden'

#: Everything Reset clears (the drag positions included).
_RESET_KEYS = (
    _MOVEMENT_KEY,
    _ACTIONS_KEY,
    'Touch Controls Scale',
    _MOVEMENT_SCALE_KEY,
    _ACTIONS_SCALE_KEY,
    _SWIPE_HIDDEN_KEY,
    'Touch DPad X',
    'Touch DPad Y',
    'Touch Buttons X',
    'Touch Buttons Y',
)

#: How often a scale-slider drag applies at most. Nothing audible
#: accompanies an apply and the effect is visible on screen, so it
#: tracks a drag closely.
_SCALE_DRAG_INTERVAL = 0.1


class MovementType(Enum):
    """How movement is controlled (the config's values)."""

    JOYSTICK = 'joystick'
    SWIPE = 'swipe'


class ActionType(Enum):
    """How actions are triggered (the config's values)."""

    BUTTONS = 'buttons'
    SWIPE = 'swipe'


class TouchscreenRoute(DocUIRoute):
    """Family class for the touchscreen settings routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyTouchscreenRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # Two explanatory lines, five rows and a button; a small-tall
        # layout cuts off the button at medium ui-scale. (Still narrow,
        # leaving the touch controls at the screen edges uncovered.)
        return dui2.WindowLayout.SMALL_TALLER


@ioprepped
@dataclass
class Root(TouchscreenRoute, path='/'):
    """The touchscreen settings page."""


AnyTouchscreenRoute = Root


@ioprepped
@dataclass
class TouchscreenState(DocUIState, state_id='settings.touchscreen'):
    """The page's values, mirroring the config."""

    movement: Annotated[MovementType, IOAttrs('m')] = MovementType.SWIPE
    movement_scale: Annotated[float, IOAttrs('ms')] = 1.0
    actions: Annotated[ActionType, IOAttrs('a')] = ActionType.BUTTONS
    actions_scale: Annotated[float, IOAttrs('as')] = 1.0
    swipe_hidden: Annotated[bool, IOAttrs('sh')] = False


#: Config key for each state field (the state's wire values are the
#: config's). Built from typed field lookups so a renamed field fails
#: here, not at runtime.
_CONFIG_KEYS: dict[str, str] = {
    TouchscreenState.key(lambda s: s.movement): _MOVEMENT_KEY,
    TouchscreenState.key(lambda s: s.movement_scale): _MOVEMENT_SCALE_KEY,
    TouchscreenState.key(lambda s: s.actions): _ACTIONS_KEY,
    TouchscreenState.key(lambda s: s.actions_scale): _ACTIONS_SCALE_KEY,
    TouchscreenState.key(lambda s: s.swipe_hidden): _SWIPE_HIDDEN_KEY,
}


class TouchscreenLocalAction(DocUILocalActionBase):
    """Family class for the touchscreen settings local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyTouchscreenLocalAction)


@ioprepped
@dataclass
class ApplySetting(TouchscreenLocalAction, name='apply_setting'):
    """Write the setting that changed (the trigger) to the config."""

    #: Save to disk too (a settled value), or just apply (mid-drag).
    commit: Annotated[bool, IOAttrs('c')] = True


@ioprepped
@dataclass
class Reset(TouchscreenLocalAction, name='reset'):
    """Put every touch control setting (and position) back to default."""


AnyTouchscreenLocalAction = ApplySetting | Reset


class TouchscreenSettingsController(
    TypedDocUIController[AnyTouchscreenRoute, AnyTouchscreenLocalAction]
):
    """Doc-ui controller for the touchscreen settings page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[TouchscreenRoute]:
        return TouchscreenRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[TouchscreenLocalAction]:
        return TouchscreenLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        # As the other settings windows: minimal mid-game.
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def create_window(
        self,
        request: DocUIRequest | DocUIRoute,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
        uiopenstateid: str | None = None,
        suppress_win_extra_type_warning: bool = False,
        layout: bacommon.docui.v2.WindowLayout | None = None,
    ) -> DocUIWindow:
        win = super().create_window(
            request,
            transition=transition,
            origin_widget=origin_widget,
            auxiliary_style=auxiliary_style,
            uiopenstateid=uiopenstateid,
            suppress_win_extra_type_warning=suppress_win_extra_type_warning,
            layout=layout,
        )
        _TouchEditing.hold_for(win)
        return win

    @override
    def restore(
        self,
        win: DocUIWindow,
        *,
        last_response: DocUIResponse | None,
        has_had_response: bool,
    ) -> DocUIWindow:
        win = super().restore(
            win, last_response=last_response, has_had_response=has_had_response
        )
        _TouchEditing.hold_for(win)
        return win

    @override
    def fulfill_route(self, route: AnyTouchscreenRoute) -> DocUIResponse:
        match route:
            case Root():
                return _page()
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyTouchscreenLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case ApplySetting():
                _apply_setting(context, commit=action.commit)
            case Reset():
                self._reset(context)
            case _:
                assert_never(action)

    def _reset(self, context: DocUILocalAction) -> None:
        cfg = bui.app.config
        for key in _RESET_KEYS:
            cfg.pop(key, None)
        cfg.apply_and_commit()

        # Re-render so the page shows the defaults we just went back to.
        window = context.window
        if not window.locked:
            self.replace(window, Root().request(), is_refresh=True)


class _TouchEditing:
    """Keeps the touch controls in editing mode while our windows live.

    Counted rather than a plain on/off: during navigation a new window
    can be created before the one it replaces has died, and the old
    one's cleanup must not turn editing off under the new one.
    """

    _holders = 0

    @classmethod
    def hold_for(cls, win: DocUIWindow) -> None:
        """Keep editing on for as long as ``win`` lives."""
        # pylint: disable=cyclic-import
        import bascenev1 as bs

        cls._holders += 1
        if cls._holders == 1:
            bs.set_touchscreen_editing(True)
        weakref.finalize(win, cls._release)

    @classmethod
    def _release(cls) -> None:
        # pylint: disable=cyclic-import
        import bascenev1 as bs

        cls._holders = max(0, cls._holders - 1)
        if cls._holders == 0:
            bs.set_touchscreen_editing(False)


def _band_text(
    text: LangStrSpec,
    y: float,
    *,
    scale: float,
    color: tuple[float, float, float, float],
    flatness: float | None = None,
) -> dui2.Text:
    return dui2.Text(
        text=text,
        position=(0, y),
        size=(560, 34),
        scale=scale,
        color=color,
        flatness=flatness,
    )


def _page() -> dui2.Response:
    """Build the page (called in a background thread)."""
    config = bui.app.config
    tstate = TouchscreenState

    def _enum_from_config[E: Enum](etype: type[E], key: str, default: E) -> E:
        try:
            return etype(config.get(key, default.value))
        except ValueError:
            return default

    state = TouchscreenState(
        movement=_enum_from_config(
            MovementType, _MOVEMENT_KEY, MovementType.SWIPE
        ),
        movement_scale=float(config.resolve(_MOVEMENT_SCALE_KEY)),
        actions=_enum_from_config(ActionType, _ACTIONS_KEY, ActionType.BUTTONS),
        actions_scale=float(config.resolve(_ACTIONS_SCALE_KEY)),
        swipe_hidden=bool(config.resolve(_SWIPE_HIDDEN_KEY)),
    )
    apply = ApplySetting().local(default_sound=False)
    apply_drag = ApplySetting(commit=False).local(default_sound=False)

    def _scale_row(
        field: Callable[[TouchscreenState], float], label: LangStrSpec
    ) -> bacommon.docui.v2.SliderRow:
        return tstate.slider_row(
            field,
            min_value=0.1,
            max_value=4.0,
            increment=0.1,
            decimals=1,
            label=label,
            on_drag=apply_drag,
            drag_interval=_SCALE_DRAG_INTERVAL,
            on_change=apply,
        )

    rows: list[dui2.Row] = [
        replace(
            tstate.choice_row(
                lambda s: s.movement,
                choice_label=_movement_label,
                label=_tsstrs.movement.spec,
                on_change=apply,
            ),
            # How to reposition the controls (which are live behind
            # us), and a word of encouragement for swipe controls.
            header_height=80.0,
            header_decorations_center=[
                _band_text(
                    _tsstrs.drag_controls.spec,
                    22.0,
                    scale=0.65,
                    color=(1.0, 1.0, 1.0, 0.4),
                ),
                _band_text(
                    _tsstrs.swipe_info.spec,
                    -12.0,
                    scale=0.55,
                    color=(0.0, 0.9, 0.1, 0.7),
                    flatness=1.0,
                ),
            ],
        ),
        _scale_row(
            lambda s: s.movement_scale, _tsstrs.movement_control_scale.spec
        ),
        tstate.choice_row(
            lambda s: s.actions,
            choice_label=_actions_label,
            label=_tsstrs.actions.spec,
            on_change=apply,
        ),
        _scale_row(
            lambda s: s.actions_scale, _tsstrs.action_control_scale.spec
        ),
        tstate.checkbox_row(
            lambda s: s.swipe_hidden,
            label=_tsstrs.swipe_controls_hidden.spec,
            on_change=apply,
        ),
    ]
    # A lone, deliberately narrow button centered under the controls
    # (a fill row would stretch it across the column).
    rows.append(
        dui2.ButtonRow(
            center_content=True,
            spacing_top=15.0,
            padding_top=8.0,
            padding_bottom=6.0,
            buttons=[
                section_button(
                    _commonassets.strings.actions.reset.spec,
                    Reset().local(),
                    size=SectionButtonSize.MEDIUM,
                )
            ],
        )
    )
    return dui2.Response(
        page=dui2.Page(
            title=_tsstrs.title.spec,
            rows=rows,
            state=state.encode(),
            center_vertically=True,
        )
    )


def _movement_label(value: MovementType) -> LangStrSpec:
    match value:
        case MovementType.JOYSTICK:
            return _tsstrs.joystick.spec
        case MovementType.SWIPE:
            return _tsstrs.swipe.spec
        case _:
            assert_never(value)


def _actions_label(value: ActionType) -> LangStrSpec:
    match value:
        case ActionType.BUTTONS:
            return _tsstrs.buttons.spec
        case ActionType.SWIPE:
            return _tsstrs.swipe.spec
        case _:
            assert_never(value)


def _apply_setting(context: DocUILocalAction, *, commit: bool) -> None:
    """Write the changed setting to the config."""
    state = context.state(TouchscreenState)
    if context.trigger is None or state is None:
        return
    key = _CONFIG_KEYS.get(context.trigger)
    if key is None:
        return
    # The wire form of the value is exactly the config form.
    cfg = bui.app.config
    cfg[key] = state.encode()[context.trigger]
    if commit:
        cfg.apply_and_commit()
    else:
        cfg.apply()
