# Released under the MIT License. See LICENSE for details.
#
"""The top level controls settings, as a doc-ui page.

A client-local doc-ui domain like the other settings pages: a stack
of buttons leading to the per-kind controller settings (which are still
legacy windows), plus a Windows-only XInput toggle in typed page
state.
"""

from enum import Enum
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.docui.v2 as dui2
from bacommon.docui.presets import section_button, button_stack
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    DocUIState,
    PressSound,
    family_members,
)
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets, _builtinassets
from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Literal

    from bacommon.docui import DocUIResponse
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui import DocUILocalAction

_ctlstrs = _classicassets.strings.settings.controllers

_XINPUT_KEY = 'Disable XInput'


class Target(Enum):
    """Windows the page's buttons lead to."""

    TOUCHSCREEN = 'touchscreen'
    GAMEPADS = 'gamepads'
    KEYBOARD = 'keyboard'
    KEYBOARD_P2 = 'keyboard_p2'
    MOBILE = 'mobile'


class ControlsRoute(DocUIRoute):
    """Family class for the controls settings routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyControlsRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # A stack of up to five buttons (plus a checkbox on Windows);
        # a bit much for a small layout.
        return dui2.WindowLayout.SMALL_TALL


@ioprepped
@dataclass
class Root(ControlsRoute, path='/'):
    """The controls settings page."""


AnyControlsRoute = Root


@ioprepped
@dataclass
class ControlsState(DocUIState, state_id='settings.controls'):
    """The page's values, mirroring the config."""

    disable_xinput: Annotated[bool, IOAttrs('dx')] = False


class ControlsLocalAction(DocUILocalActionBase):
    """Family class for the controls settings local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyControlsLocalAction)


@ioprepped
@dataclass
class Open(ControlsLocalAction, name='open'):
    """Go somewhere."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH

    target: Annotated[Target, IOAttrs('t')]


@ioprepped
@dataclass
class ApplyXInput(ControlsLocalAction, name='apply_xinput'):
    """Write the disable-xinput setting to the config."""


AnyControlsLocalAction = Open | ApplyXInput


class ControlsSettingsController(
    TypedDocUIController[AnyControlsRoute, AnyControlsLocalAction]
):
    """Doc-ui controller for the controls settings page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[ControlsRoute]:
        return ControlsRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[ControlsLocalAction]:
        return ControlsLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        # As the other settings windows: minimal mid-game.
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def fulfill_route(self, route: AnyControlsRoute) -> DocUIResponse:
        match route:
            case Root():
                _preload_modules()
                return _page(_Availability.gather())
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyControlsLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case Open():
                _open(action.target, context)
            case ApplyXInput():
                _apply_xinput(context)
            case _:
                assert_never(action)


@dataclass
class _Availability:
    """Which of our controls apply here and now."""

    touchscreen: bool
    keyboard: bool
    keyboard_p2: bool
    xinput_toggle: bool

    @classmethod
    def gather(cls) -> _Availability:
        """Gather availability (from a background thread).

        The input-device queries it takes must run on the logic thread,
        so we hop over there and wait. Done per page build (rather than
        once) so a keyboard connected since last time shows up.
        """
        return bui.logic_thread_submit(cls._gather_in_logic_thread).result(
            timeout=10.0
        )

    @classmethod
    def _gather_in_logic_thread(cls) -> _Availability:
        # pylint: disable=cyclic-import
        import bascenev1 as bs

        app = bui.app
        assert app.classic is not None
        keyboard = (
            bs.getinputdevice('Keyboard', '#1', doraise=False) is not None
        )
        return cls(
            touchscreen=bs.have_touchscreen_input(),
            keyboard=keyboard,
            # Keyboard P2 only gets keys once enabled (in keyboard 1's
            # config window).
            keyboard_p2=(
                keyboard
                and not app.env.vr
                and bool(app.config.resolve('Keyboard P2 Enabled'))
            ),
            # On windows (outside of vr), an option to disable xinput.
            xinput_toggle=(
                app.classic.platform == 'windows' and not app.env.vr
            ),
        )


def _preload_modules() -> None:
    """Import what the buttons lead to here, off the logic thread."""
    # pylint: disable=cyclic-import
    from bauiv1lib.settings import keyboard as _unused1
    from bauiv1lib.settings import remoteapp as _unused2
    from bauiv1lib.settings import gamepadselect as _unused3
    from bauiv1lib.settings import touchscreen as _unused4


def _page(avail: _Availability) -> dui2.Response:
    """Build the page (called in a background thread)."""

    def _button(label: LangStrSpec, target: Target) -> dui2.Button:
        return section_button(label, Open(target=target).local())

    # One group; every platform we support has gamepads in some form,
    # and the remote app works everywhere, so those always show.
    buttons: list[dui2.Button] = []
    if avail.touchscreen:
        buttons.append(
            _button(_ctlstrs.touchscreen.title.spec, Target.TOUCHSCREEN)
        )
    buttons.append(
        _button(_ctlstrs.configure_controllers.spec, Target.GAMEPADS)
    )
    if avail.keyboard:
        buttons.append(
            _button(_ctlstrs.configure_keyboard.spec, Target.KEYBOARD)
        )
    if avail.keyboard_p2:
        buttons.append(
            _button(_ctlstrs.configure_keyboard_p2.spec, Target.KEYBOARD_P2)
        )
    buttons.append(_button(_ctlstrs.configure_mobile.spec, Target.MOBILE))
    rows: list[dui2.Row] = button_stack([buttons], first_group_spacing=0.0)

    state = ControlsState(
        disable_xinput=bool(bui.app.config.resolve(_XINPUT_KEY))
    )
    if avail.xinput_toggle:
        rows.append(
            replace(
                ControlsState.checkbox_row(
                    lambda s: s.disable_xinput,
                    label=_ctlstrs.disable_xinput.spec,
                    footnote=_ctlstrs.disable_xinput_description.spec,
                    on_change=ApplyXInput().local(default_sound=False),
                ),
                spacing_top=20.0,
            )
        )

    return dui2.Response(
        page=dui2.Page(
            title=_ctlstrs.title.spec,
            rows=rows,
            state=state.encode(),
            center_vertically=True,
        )
    )


def _apply_xinput(context: DocUILocalAction) -> None:
    state = context.state(ControlsState)
    if state is None:
        return
    bui.screenmessage(
        _commonassets.strings.status.must_restart, color=(1, 1, 0)
    )
    _builtinassets.audio.gun_cocking.get().play()
    cfg = bui.app.config
    cfg[_XINPUT_KEY] = state.disable_xinput
    cfg.apply_and_commit()


def _open(target: Target, context: DocUILocalAction) -> None:
    # pylint: disable=cyclic-import
    import bascenev1 as bs

    window = context.window

    # No-op if we're not in control.
    if not window.main_window_has_control():
        return
    match target:
        case Target.TOUCHSCREEN:
            from bauiv1lib.settings import touchscreen

            ctrl = touchscreen.TouchscreenSettingsController
            window.main_window_replace(
                lambda: ctrl().create_window(
                    touchscreen.Root(),
                    origin_widget=context.widget,
                    auxiliary_style=False,
                ),
                extra_type_id=ctrl.get_window_extra_type_id(),
            )
        case Target.GAMEPADS:
            from bauiv1lib.settings.gamepadselect import GamepadSelectWindow

            window.main_window_replace(GamepadSelectWindow)
        case Target.KEYBOARD | Target.KEYBOARD_P2:
            from bauiv1lib.settings.keyboard import ConfigKeyboardWindow

            name = '#1' if target is Target.KEYBOARD else '#2'
            window.main_window_replace(
                lambda: ConfigKeyboardWindow(
                    bs.getinputdevice('Keyboard', name)
                )
            )
        case Target.MOBILE:
            from bauiv1lib.settings.remoteapp import RemoteAppSettingsWindow

            window.main_window_replace(RemoteAppSettingsWindow)
        case _:
            assert_never(target)
