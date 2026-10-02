# Released under the MIT License. See LICENSE for details.
#
"""Advanced settings, as a doc-ui page.

A client-local doc-ui domain like the audio settings: the page is
authored here, its controls keep their values in typed page state
mirroring the config, and each change is a typed local action that
writes the config. Buttons leading elsewhere are local actions too,
opening the existing (non-doc-ui) windows.
"""

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, override, assert_never
import weakref

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
from bacommon.langstr import LangStrSpecValue
from bacommon.locale import LocaleResolved, Locale, language_picker_label
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets
from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Literal

    from bacommon.docui import DocUIResponse
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui import DocUILocalAction

_advstrs = _classicassets.strings.settings.advanced

#: The 'follow the OS locale' language choice.
_LANGUAGE_AUTO = 'Auto'


class InsecureConnections(Enum):
    """The tri-state ``Insecure Connections`` setting (its config values)."""

    ALWAYS = 'always'
    AUTO = 'auto'
    NEVER = 'never'


class Target(Enum):
    """Windows the page's buttons lead to."""

    MODDING_GUIDE = 'modding_guide'
    DEV_TOOLS = 'dev_tools'
    MODS_FOLDER = 'mods_folder'
    PLUGINS = 'plugins'
    VR_TEST = 'vr_test'
    NET_TEST = 'net_test'
    BENCHMARKS = 'benchmarks'
    SEND_INFO = 'send_info'


class AdvancedRoute(DocUIRoute):
    """Family class for the advanced settings routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyAdvancedRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # A long list of options; tall rather than wide.
        return dui2.WindowLayout.SMALL_TALLER


@ioprepped
@dataclass
class Root(AdvancedRoute, path='/'):
    """The advanced settings page."""


AnyAdvancedRoute = Root


@ioprepped
@dataclass
class AdvancedState(DocUIState, state_id='settings.advanced'):
    """The page's values, mirroring the config."""

    #: A locale long-value, or ``_LANGUAGE_AUTO``.
    language: Annotated[str, IOAttrs('lang')] = _LANGUAGE_AUTO
    kick_idle_players: Annotated[bool, IOAttrs('kip')] = False
    show_ping: Annotated[bool, IOAttrs('sp')] = False
    show_demos_when_idle: Annotated[bool, IOAttrs('sd')] = False
    disable_camera_shake: Annotated[bool, IOAttrs('dcs')] = False
    disable_camera_gyro: Annotated[bool, IOAttrs('dcg')] = False
    insecure_connections: Annotated[InsecureConnections, IOAttrs('ic')] = (
        InsecureConnections.AUTO
    )
    always_use_internal_keyboard: Annotated[bool, IOAttrs('kb')] = False
    allow_extreme_aspect_ratios: Annotated[bool, IOAttrs('ar')] = False


#: Config key for each state field that is a plain config mirror. Built
#: from typed field lookups so a renamed field fails here, not at
#: runtime; the language is not here since switching it is its own
#: (asynchronous) affair.
_CONFIG_KEYS: dict[str, str] = {
    AdvancedState.key(lambda s: s.kick_idle_players): 'Kick Idle Players',
    AdvancedState.key(lambda s: s.show_ping): 'Show Ping',
    AdvancedState.key(lambda s: s.show_demos_when_idle): 'Show Demos When Idle',
    AdvancedState.key(lambda s: s.disable_camera_shake): 'Disable Camera Shake',
    AdvancedState.key(lambda s: s.disable_camera_gyro): 'Disable Camera Gyro',
    AdvancedState.key(lambda s: s.insecure_connections): 'Insecure Connections',
    AdvancedState.key(
        lambda s: s.always_use_internal_keyboard
    ): 'Always Use Internal Keyboard',
    AdvancedState.key(
        lambda s: s.allow_extreme_aspect_ratios
    ): 'Allow Extreme Aspect Ratios',
}


class AdvancedLocalAction(DocUILocalActionBase):
    """Family class for the advanced settings local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyAdvancedLocalAction)


@ioprepped
@dataclass
class SetLanguage(AdvancedLocalAction, name='set_language'):
    """Switch to the language the page's state holds."""


@ioprepped
@dataclass
class ApplySetting(AdvancedLocalAction, name='apply_setting'):
    """Write the setting that changed (the trigger) to the config."""


@ioprepped
@dataclass
class Open(AdvancedLocalAction, name='open'):
    """Go somewhere."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH

    target: Annotated[Target, IOAttrs('t')]


@ioprepped
@dataclass
class SendTranslationFeedback(
    AdvancedLocalAction, name='send_translation_feedback'
):
    """Report a translation that could be improved."""


AnyAdvancedLocalAction = (
    SetLanguage | ApplySetting | Open | SendTranslationFeedback
)


class AdvancedSettingsController(
    TypedDocUIController[AnyAdvancedRoute, AnyAdvancedLocalAction]
):
    """Doc-ui controller for the advanced settings page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[AdvancedRoute]:
        return AdvancedRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[AdvancedLocalAction]:
        return AdvancedLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        # As the other settings windows: minimal mid-game.
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def fulfill_route(self, route: AnyAdvancedRoute) -> DocUIResponse:
        match route:
            case Root():
                _preload_modules()
                return _page()
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyAdvancedLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case SetLanguage():
                self._set_language(context)
            case ApplySetting():
                _apply_setting(context)
            case Open():
                _open(action.target, context)
            case SendTranslationFeedback():
                bui.open_url('https://www.ballistica.net/feedback')
            case _:
                assert_never(action)

    def _set_language(self, context: DocUILocalAction) -> None:
        state = context.state(AdvancedState)
        if state is None:
            return
        locale_ss = bui.app.locale

        # Re-render once the switch is done with, whether or not it went
        # through: on success the page comes back in the new language
        # with the picker matching; on a cancelled or failed download the
        # picker snaps back to the language we are actually still in.
        winref = weakref.ref(context.window)

        def _on_complete(success: bool) -> None:
            del success  # Either way, show what is actually current.
            window = winref()
            if window is not None and not window.locked:
                self.replace(window, Root().request(), is_refresh=True)

        # Switching is an elective asset-resolve (the target locale's
        # language flavor is downloaded if not already local) that
        # commits only on success and writes/clears the 'Lang' config
        # itself. Auto = no override (follow the OS-default locale).
        if state.language == _LANGUAGE_AUTO:
            locale_ss.set_locale(
                locale_ss.default_locale,
                store_to_config=False,
                on_complete=_on_complete,
            )
        else:
            locale_ss.set_locale(
                Locale.from_long_value(state.language),
                store_to_config=True,
                on_complete=_on_complete,
            )


def _preload_modules() -> None:
    """Import what the buttons lead to here, off the logic thread."""
    # pylint: disable=cyclic-import
    from babase import modutils as _unused2
    from bauiv1lib.settings import vrtesting as _unused3
    from bauiv1lib.settings import nettesting as _unused4
    from bauiv1lib import sendinfo as _unused7
    from bauiv1lib.settings import benchmarks as _unused8
    from bauiv1lib.settings import plugins as _unused9
    from bauiv1lib.settings import devtools as _unused10


def _language_choices() -> list[tuple[str, LangStrSpec]]:
    """The language picker's options: Auto, then every displayable locale.

    Ordered by endonym -- the half of each label the user actually
    scans; label shape lives in
    :func:`bacommon.locale.language_picker_label`, shared with the
    master server's account-settings picker so the two can't drift.
    """
    locale_ss = bui.app.locale
    locale_strs = _commonassets.strings.locales
    choices: list[tuple[str, LangStrSpec]] = [
        (
            _LANGUAGE_AUTO,
            _commonassets.strings.compose.paren_suffix(
                main=_commonassets.strings.values.auto,
                note=getattr(
                    locale_strs, locale_ss.default_locale.resolved.value
                ),
            ).spec,
        )
    ]
    for lresolved in sorted(
        (
            lr
            for lr in LocaleResolved
            if locale_ss.can_display_locale(lr.locale)
        ),
        key=lambda lr: lr.endonym_sort_key,
    ):
        choices.append(
            (
                lresolved.locale.long_value,
                LangStrSpecValue.literal(
                    language_picker_label(
                        lresolved,
                        getattr(locale_strs, lresolved.value).evaluate(),
                    )
                ),
            )
        )
    return choices


def _page() -> dui2.Response:
    """Build the page (called in a background thread)."""
    app = bui.app
    assert app.classic is not None
    config = app.config
    astate = AdvancedState
    setstrs = _classicassets.strings.settings

    def _bool(key: str) -> bool:
        return bool(config.resolve(key))

    insecure = config.resolve('Insecure Connections')
    try:
        insecure_mode = InsecureConnections(insecure)
    except ValueError:
        insecure_mode = InsecureConnections.AUTO

    show_gyro = bui.hasgyro()
    show_internal_keyboard = not app.env.vr
    show_vr_test = app.env.vr

    state = AdvancedState(
        language=config.get('Lang', _LANGUAGE_AUTO),
        kick_idle_players=_bool('Kick Idle Players'),
        show_ping=_bool('Show Ping'),
        show_demos_when_idle=_bool('Show Demos When Idle'),
        disable_camera_shake=_bool('Disable Camera Shake'),
        disable_camera_gyro=_bool('Disable Camera Gyro'),
        insecure_connections=insecure_mode,
        always_use_internal_keyboard=_bool('Always Use Internal Keyboard'),
        allow_extreme_aspect_ratios=_bool('Allow Extreme Aspect Ratios'),
    )
    # A stored language we can no longer show reads as Auto.
    if state.language not in {c[0] for c in _language_choices()}:
        state.language = _LANGUAGE_AUTO

    apply = ApplySetting().local(default_sound=False)

    rows: list[dui2.Row] = [
        astate.choice_row(
            lambda s: s.language,
            choices=_language_choices(),
            label=_advstrs.language.spec,
            on_change=SetLanguage().local(default_sound=False),
        ),
        dui2.ButtonControlRow(
            label=_advstrs.improve_translations.spec,
            button=dui2.Button(
                label=_advstrs.translation_feedback.spec,
                style=dui2.ButtonStyle.MEDIUM,
                size=(150.0, 45.0),
                action=SendTranslationFeedback().local(),
            ),
            # (Wrapped at display time by its max-chars-per-line wrap
            # params, so each language gets however many lines it needs;
            # the row grows to fit.)
            footnote=_advstrs.improve_translations_description(
                app_name=_classicassets.strings.ui.app_name
            ).spec,
        ),
        astate.checkbox_row(
            lambda s: s.kick_idle_players,
            label=_advstrs.kick_idle_players.spec,
            on_change=apply,
        ),
        astate.checkbox_row(
            lambda s: s.show_ping,
            label=_advstrs.show_in_game_ping.spec,
            on_change=apply,
        ),
        astate.checkbox_row(
            lambda s: s.show_demos_when_idle,
            label=_advstrs.show_demos_when_idle.spec,
            on_change=apply,
        ),
        astate.checkbox_row(
            lambda s: s.disable_camera_shake,
            label=_advstrs.disable_camera_shake.spec,
            on_change=apply,
        ),
    ]
    if show_gyro:
        rows.append(
            astate.checkbox_row(
                lambda s: s.disable_camera_gyro,
                label=_advstrs.disable_camera_gyro.spec,
                on_change=apply,
            )
        )
    rows.append(
        astate.choice_row(
            lambda s: s.insecure_connections,
            choice_label=_insecure_label,
            label=_advstrs.insecure_connections.spec,
            footnote=_advstrs.insecure_connections_description.spec,
            on_change=apply,
        )
    )
    if show_internal_keyboard:
        rows.append(
            astate.checkbox_row(
                lambda s: s.always_use_internal_keyboard,
                label=_advstrs.always_use_internal_keyboard.spec,
                footnote=_advstrs.always_use_internal_keyboard_description.spec,
                on_change=apply,
            )
        )
    rows.append(
        astate.checkbox_row(
            lambda s: s.allow_extreme_aspect_ratios,
            # NEEDS_TRANSLATION
            label=LangStrSpecValue.literal('Allow Extreme Aspect Ratios'),
            footnote=LangStrSpecValue.literal(
                # NEEDS_TRANSLATION
                'Some things will look janky. But you do you.'
            ),
            on_change=apply,
        )
    )

    def _button(label: LangStrSpec, target: Target) -> dui2.Button:
        return section_button(label, Open(target=target).local())

    # One button per row, like the old window, grouped (modding,
    # testing, reporting).
    testing = [
        _button(setstrs.net_testing.title.spec, Target.NET_TEST),
        _button(setstrs.benchmarks.title.spec, Target.BENCHMARKS),
    ]
    if show_vr_test:
        testing.insert(
            0, _button(setstrs.vr_testing.title.spec, Target.VR_TEST)
        )
    rows += button_stack(
        [
            [
                _button(_advstrs.modding_guide.spec, Target.MODDING_GUIDE),
                _button(setstrs.dev_tools.title.spec, Target.DEV_TOOLS),
                _button(_advstrs.show_mods_folder.spec, Target.MODS_FOLDER),
                _button(setstrs.plugins.title.spec, Target.PLUGINS),
            ],
            testing,
            [_button(_advstrs.send_info.spec, Target.SEND_INFO)],
        ]
    )

    return dui2.Response(
        page=dui2.Page(
            title=_advstrs.title.spec, rows=rows, state=state.encode()
        )
    )


def _insecure_label(mode: InsecureConnections) -> LangStrSpec:
    valstrs = _commonassets.strings.values
    match mode:
        case InsecureConnections.ALWAYS:
            return valstrs.always.spec
        case InsecureConnections.AUTO:
            return valstrs.auto.spec
        case InsecureConnections.NEVER:
            return valstrs.never.spec
        case _:
            assert_never(mode)


def _apply_setting(context: DocUILocalAction) -> None:
    """Write the changed setting to the config, as ConfigCheckBox would."""
    state = context.state(AdvancedState)
    if context.trigger is None or state is None:
        return
    key = _CONFIG_KEYS.get(context.trigger)
    if key is None:
        return
    # The wire form of the value is exactly the config form (bools;
    # the tri-state's string values).
    value = state.encode()[context.trigger]
    cfg = bui.app.config
    cfg[key] = value
    cfg.apply_and_commit()


def _open(target: Target, context: DocUILocalAction) -> None:
    # pylint: disable=cyclic-import
    window = context.window
    match target:
        case Target.MODDING_GUIDE:
            bui.open_url('https://ballistica.net/wiki/modding-guide')
            return
        case Target.MODS_FOLDER:
            from babase.modutils import show_user_scripts

            show_user_scripts()
            return
        case (
            Target.DEV_TOOLS
            | Target.PLUGINS
            | Target.VR_TEST
            | Target.NET_TEST
            | Target.BENCHMARKS
            | Target.SEND_INFO
        ):
            pass
        case _:
            assert_never(target)

    # The rest replace us with another window; no-op if we're not in
    # control.
    if not window.main_window_has_control():
        return
    origin = context.widget
    match target:
        case Target.DEV_TOOLS:
            from bauiv1lib.settings import devtools

            window.main_window_replace(
                lambda: devtools.DevToolsController().create_window(
                    devtools.Root(),
                    origin_widget=origin,
                    auxiliary_style=False,
                ),
                extra_type_id=(
                    devtools.DevToolsController.get_window_extra_type_id()
                ),
            )
        case Target.PLUGINS:
            from bauiv1lib.settings.plugins import PluginWindow

            window.main_window_replace(
                lambda: PluginWindow(origin_widget=origin)
            )
        case Target.VR_TEST:
            from bauiv1lib.settings.vrtesting import VRTestingWindow

            window.main_window_replace(
                lambda: VRTestingWindow(transition='in_right')
            )
        case Target.NET_TEST:
            from bauiv1lib.settings.nettesting import NetTestingWindow

            window.main_window_replace(
                lambda: NetTestingWindow(transition='in_right')
            )
        case Target.BENCHMARKS:
            from bauiv1lib.settings import benchmarks

            window.main_window_replace(
                lambda: benchmarks.BenchmarksController().create_window(
                    benchmarks.Root(),
                    origin_widget=origin,
                    auxiliary_style=False,
                ),
                extra_type_id=(
                    benchmarks.BenchmarksController.get_window_extra_type_id()
                ),
            )
        case Target.SEND_INFO:
            from bauiv1lib import sendinfo

            window.main_window_replace(
                lambda: sendinfo.SendInfoController().create_window(
                    sendinfo.Root(),
                    origin_widget=origin,
                    auxiliary_style=False,
                ),
                extra_type_id=(
                    sendinfo.SendInfoController.get_window_extra_type_id()
                ),
            )
        case _:
            assert_never(target)
