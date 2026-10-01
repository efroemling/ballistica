# Released under the MIT License. See LICENSE for details.
#
"""Dev tools settings, as a doc-ui page.

A client-local doc-ui domain like the other settings pages: the page
is authored here, its controls mirror the config in typed page state,
and every control is a typed local action.
"""

from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2
from bacommon.docui.presets import section_button
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    DocUIState,
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

    from bauiv1lib.docui import DocUILocalAction

_devstrs = _classicassets.strings.settings.dev_tools

_SHOW_BUTTON_KEY = 'Show Dev Console Button'
_BUTTON_SIZE_KEY = 'Dev Console Button Size'
_BUTTON_STYLE_KEY = 'Dev Console Button Style'
_BUTTON_POS_KEYS = ('Dev Console Button Pos X', 'Dev Console Button Pos Y')

# How often a size drag re-applies the config (the button resizes live).
_SIZE_DRAG_INTERVAL = 0.1


class DevConsoleButtonStyle(Enum):
    """Color scheme for the dev console button (config values)."""

    GREY = 'grey'
    GREEN = 'green'
    PURPLE = 'purple'
    HOWDY = 'howdy'


class DevToolsRoute(DocUIRoute):
    """Family class for the dev tools routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyDevToolsRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # Two sections of controls: enough to want the tall form.
        return dui2.WindowLayout.SMALL_TALLER


@ioprepped
@dataclass
class Root(DevToolsRoute, path='/'):
    """The dev tools page."""


AnyDevToolsRoute = Root


@ioprepped
@dataclass
class DevToolsState(DocUIState, state_id='settings.devtools'):
    """The page's values, mirroring the config."""

    show_dev_console_button: Annotated[bool, IOAttrs('sb')] = False
    dev_console_button_size: Annotated[float, IOAttrs('bs')] = 1.0
    dev_console_button_style: Annotated[
        DevConsoleButtonStyle, IOAttrs('bt')
    ] = DevConsoleButtonStyle.GREY


class DevToolsLocalAction(DocUILocalActionBase):
    """Family class for the dev tools local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyDevToolsLocalAction)


@ioprepped
@dataclass
class ApplyShowButton(DevToolsLocalAction, name='apply_show_button'):
    """Write the show-dev-console-button setting to the config."""


@ioprepped
@dataclass
class ApplyButtonSetting(DevToolsLocalAction, name='apply_button_setting'):
    """Write the dev-console-button setting that changed to the config."""

    #: Save to disk too (a settled value), or just apply (mid-drag).
    commit: Annotated[bool, IOAttrs('c')] = True


@ioprepped
@dataclass
class ResetButton(DevToolsLocalAction, name='reset_button'):
    """Put the dev console button back to its default look and spot."""


@ioprepped
@dataclass
class CreateUserSystemScripts(DevToolsLocalAction, name='create_scripts'):
    """Copy the system scripts out to the user dir for editing."""


@ioprepped
@dataclass
class DeleteUserSystemScripts(DevToolsLocalAction, name='delete_scripts'):
    """Remove the user copy of the system scripts (after confirming)."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH


AnyDevToolsLocalAction = (
    ApplyShowButton
    | ApplyButtonSetting
    | ResetButton
    | CreateUserSystemScripts
    | DeleteUserSystemScripts
)


class DevToolsController(
    TypedDocUIController[AnyDevToolsRoute, AnyDevToolsLocalAction]
):
    """Doc-ui controller for the dev tools page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[DevToolsRoute]:
        return DevToolsRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[DevToolsLocalAction]:
        return DevToolsLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        # As the other settings windows: minimal mid-game.
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def fulfill_route(self, route: AnyDevToolsRoute) -> DocUIResponse:
        match route:
            case Root():
                _preload_modules()
                return _page()
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyDevToolsLocalAction, context: DocUILocalAction
    ) -> None:
        # Note: import the submodule explicitly -- attribute access on
        # bare `babase` only works if something else happened to import
        # it first.
        import babase.modutils

        match action:
            case ApplyShowButton():
                _apply_show_button(context)
                # The rest of the section's controls hang their
                # disabled-ness off this; rebuild to show it.
                self.replace(context.window, Root().request(), is_refresh=True)
            case ApplyButtonSetting():
                _apply_button_setting(context, commit=action.commit)
            case ResetButton():
                _reset_button()
                self.replace(context.window, Root().request(), is_refresh=True)
            case CreateUserSystemScripts():
                babase.modutils.create_user_system_scripts()
            case DeleteUserSystemScripts():
                from bauiv1lib.confirm import ConfirmWindow

                ConfirmWindow(
                    action=babase.modutils.delete_user_system_scripts,
                    origin_widget=context.widget,
                )
            case _:
                assert_never(action)


def _preload_modules() -> None:
    """Import what our actions use here, off the logic thread."""
    # pylint: disable=cyclic-import
    import babase.modutils as _unused1
    from bauiv1lib import confirm as _unused2


def _style_from_config() -> DevConsoleButtonStyle:
    try:
        return DevConsoleButtonStyle(bui.app.config.resolve(_BUTTON_STYLE_KEY))
    except ValueError:
        return DevConsoleButtonStyle.GREY


def _style_label(style: DevConsoleButtonStyle) -> LangStrSpec:
    match style:
        case DevConsoleButtonStyle.GREY:
            # NEEDS_TRANSLATION
            return LangStrSpecValue.literal('Grey')
        case DevConsoleButtonStyle.GREEN:
            # NEEDS_TRANSLATION
            return LangStrSpecValue.literal('Green')
        case DevConsoleButtonStyle.PURPLE:
            # NEEDS_TRANSLATION
            return LangStrSpecValue.literal('Purple')
        case DevConsoleButtonStyle.HOWDY:
            # NEEDS_TRANSLATION
            return LangStrSpecValue.literal('Howdy')
        case _:
            assert_never(style)


def _page() -> dui2.Response:
    """Build the page (called in a background thread)."""
    config = bui.app.config
    state = DevToolsState(
        show_dev_console_button=bool(config.resolve(_SHOW_BUTTON_KEY)),
        dev_console_button_size=float(config.resolve(_BUTTON_SIZE_KEY)),
        dev_console_button_style=_style_from_config(),
    )
    enabled = state.show_dev_console_button
    apply = ApplyButtonSetting().local(default_sound=False)
    apply_drag = ApplyButtonSetting(commit=False).local(default_sound=False)
    button_rows: list[dui2.Row] = [
        DevToolsState.checkbox_row(
            lambda s: s.show_dev_console_button,
            # NEEDS_TRANSLATION
            label=LangStrSpecValue.literal('Enable'),
            on_change=ApplyShowButton().local(default_sound=False),
        ),
        DevToolsState.slider_row(
            lambda s: s.dev_console_button_size,
            min_value=0.5,
            max_value=4.0,
            increment=0.1,
            decimals=1,
            # NEEDS_TRANSLATION
            label=LangStrSpecValue.literal('Size'),
            on_drag=apply_drag,
            drag_interval=_SIZE_DRAG_INTERVAL,
            on_change=apply,
            disabled=not enabled,
        ),
        DevToolsState.choice_row(
            lambda s: s.dev_console_button_style,
            choice_label=_style_label,
            # NEEDS_TRANSLATION
            label=LangStrSpecValue.literal('Style'),
            on_change=apply,
            disabled=not enabled,
        ),
        # The reset hangs right under the controls it goes with. (Fill
        # rows span the column as the control rows above do. Paddings
        # reproduce the button stacks these replaced -- 8/6 there, but
        # a scrolling row lifts its content 6 units, so effectively
        # 2/12 -- leaving spacing unchanged.)
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[
                replace(
                    section_button(
                        # NEEDS_TRANSLATION
                        LangStrSpecValue.literal('Reset'),
                        ResetButton().local(),
                    ),
                    disabled=not enabled,
                )
            ],
            padding_top=2.0,
            padding_bottom=12.0,
        ),
    ]
    rows: list[dui2.Row] = [
        dui2.Section(
            # NEEDS_TRANSLATION
            title=LangStrSpecValue.literal('Dev Console Button'),
            # NEEDS_TRANSLATION
            subtitle=LangStrSpecValue.literal('<drag to reposition>'),
            title_align=dui2.HAlign.CENTER,
            rows=button_rows,
        ),
        dui2.Section(
            # NEEDS_TRANSLATION
            title=LangStrSpecValue.literal('User System Scripts'),
            title_align=dui2.HAlign.CENTER,
            rows=[
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    buttons=[
                        section_button(
                            # NEEDS_TRANSLATION
                            LangStrSpecValue.literal('Create Scripts'),
                            CreateUserSystemScripts().local(),
                        ),
                        section_button(
                            # NEEDS_TRANSLATION
                            LangStrSpecValue.literal('Delete Scripts'),
                            DeleteUserSystemScripts().local(),
                        ),
                    ],
                    padding_top=2.0,
                    padding_bottom=12.0,
                ),
            ],
        ),
    ]
    return dui2.Response(
        page=dui2.Page(
            title=_devstrs.title.spec,
            rows=rows,
            state=state.encode(),
            center_vertically=True,
        )
    )


def _apply_show_button(context: DocUILocalAction) -> None:
    state = context.state(DevToolsState)
    if state is None:
        return
    cfg = bui.app.config
    cfg[_SHOW_BUTTON_KEY] = state.show_dev_console_button
    cfg.apply_and_commit()


def _apply_button_setting(context: DocUILocalAction, *, commit: bool) -> None:
    """Write the changed size or style to the config."""
    state = context.state(DevToolsState)
    if state is None:
        return
    cfg = bui.app.config
    cfg[_BUTTON_SIZE_KEY] = state.dev_console_button_size
    cfg[_BUTTON_STYLE_KEY] = state.dev_console_button_style.value
    if commit:
        cfg.apply_and_commit()
    else:
        cfg.apply()


def _reset_button() -> None:
    # Drop our stored size, style, and custom position; applying then
    # reverts the button to its default look in its default docked spot.
    cfg = bui.app.config
    cfg.pop(_BUTTON_SIZE_KEY, None)
    cfg.pop(_BUTTON_STYLE_KEY, None)
    for key in _BUTTON_POS_KEYS:
        cfg.pop(key, None)
    cfg.apply_and_commit()
