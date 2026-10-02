# Released under the MIT License. See LICENSE for details.
#
"""Graphics settings, as a doc-ui page.

A client-local doc-ui domain like the audio and advanced settings: the
page is authored here, its controls keep their values in typed page
state mirroring the config, and each change is a typed local action
that writes the config.

Fullscreen is the odd one out: it can change behind the page's back (a
hotkey, the OS window controls), so the controller polls it (see
:meth:`GraphicsSettingsController.poll_page_state`). Its native calls
are logic-thread-only while pages are built in the background, so the
controller keeps what the page build needs cached.
"""

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    DocUIState,
    family_members,
)
from bacommon.langstr import LangStrSpecValue
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets
from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Literal

    from bacommon.docui import DocUIResponse
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui import DocUILocalAction, DocUIWindow

_gfxstrs = _classicassets.strings.settings.graphics

#: How often (seconds) to re-check values that change behind our back.
_POLL_INTERVAL = 0.5


class Quality(Enum):
    """Graphics quality settings (their config values)."""

    AUTO = 'Auto'
    HIGHER = 'Higher'
    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'


class AssetQuality(Enum):
    """Asset quality tiers.

    Display-only for now: the popup shows what's coming, with ultra
    disabled, and writes nothing to the config.
    """

    REGULAR = 'Regular'
    ULTRA = 'Ultra'


class VSync(Enum):
    """Vertical-sync settings (their config values)."""

    AUTO = 'Auto'
    ALWAYS = 'Always'
    NEVER = 'Never'


class ScreenInsets(Enum):
    """Screen-insets settings (their config values)."""

    AUTO = 'Auto'
    CUSTOM = 'Custom'


class ResolutionMode(Enum):
    """What the resolution control sets on this platform."""

    #: Sets ``Resolution (Android)`` to Auto, Native, or an HD standard.
    ANDROID = 'android'

    #: Sets ``GVR Render Target Scale`` (cardboard VR) on a slider.
    CARDBOARD = 'cardboard'

    #: Sets ``Screen Pixel Scale`` on a slider (for systems that can't
    #: set a resolution directly).
    PIXEL_SCALE = 'pixel_scale'


#: Step size for the resolution-scale slider.
_RESOLUTION_SCALE_INCREMENT = 0.05

#: How often a resolution-scale drag applies at most (each apply
#: reallocates render targets).
_RESOLUTION_DRAG_INTERVAL = 0.25

#: Step size for the custom screen-insets slider.
_SCREEN_INSETS_INCREMENT = 0.05


class GraphicsRoute(DocUIRoute):
    """Family class for the graphics settings routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyGraphicsRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # A list of options; tall rather than wide.
        return dui2.WindowLayout.SMALL_TALL


@ioprepped
@dataclass
class Root(GraphicsRoute, path='/'):
    """The graphics settings page."""


AnyGraphicsRoute = Root


@ioprepped
@dataclass
class GraphicsState(DocUIState, state_id='settings.graphics'):
    """The page's values, mirroring the config."""

    fullscreen: Annotated[bool, IOAttrs('fs')] = False
    visuals: Annotated[Quality, IOAttrs('v')] = Quality.AUTO
    asset_quality: Annotated[AssetQuality, IOAttrs('aq')] = AssetQuality.REGULAR

    #: One of the Android resolution popup's choice values (see
    #: _resolution_choices()).
    resolution: Annotated[str, IOAttrs('r')] = ''

    #: The resolution slider's scale, for the scale-based modes (see
    #: _scale_range()).
    resolution_scale: Annotated[float, IOAttrs('rs')] = 1.0
    vsync: Annotated[VSync, IOAttrs('vs')] = VSync.AUTO

    #: As typed; cleaned up and written by ApplyMaxFps.
    max_fps: Annotated[str, IOAttrs('mf')] = ''
    show_fps: Annotated[bool, IOAttrs('sf')] = False
    screen_insets: Annotated[ScreenInsets, IOAttrs('si')] = ScreenInsets.AUTO

    #: 0-1; see ApplyScreenInsets for how it relates to screen_insets.
    custom_screen_insets: Annotated[float, IOAttrs('csi')] = 0.0


#: Config key for each state field that is a plain config mirror (its
#: wire value is its config value). Built from typed field lookups so a
#: renamed field fails here, not at runtime.
_CONFIG_KEYS: dict[str, str] = {
    GraphicsState.key(lambda s: s.visuals): 'Graphics Quality',
    GraphicsState.key(lambda s: s.vsync): 'Vertical Sync',
    GraphicsState.key(lambda s: s.show_fps): 'Show FPS',
}


class GraphicsLocalAction(DocUILocalActionBase):
    """Family class for the graphics settings local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyGraphicsLocalAction)


@ioprepped
@dataclass
class ApplySetting(GraphicsLocalAction, name='apply_setting'):
    """Write the setting that changed (the trigger) to the config."""


@ioprepped
@dataclass
class ApplyFullscreen(GraphicsLocalAction, name='apply_fullscreen'):
    """Set fullscreen to what the page's state holds."""


@ioprepped
@dataclass
class ApplyResolution(GraphicsLocalAction, name='apply_resolution'):
    """Write the resolution setting in its platform's form."""


@ioprepped
@dataclass
class ApplyMaxFps(GraphicsLocalAction, name='apply_max_fps'):
    """Clean up and write the typed max-fps value."""


@ioprepped
@dataclass
class ApplyScreenInsets(GraphicsLocalAction, name='apply_screen_insets'):
    """Write the screen-insets settings (mode and custom amount).

    Switching modes either way resets the custom amount to what
    automatic uses, so switching to custom doesn't jump and switching
    to automatic shows its amount. The custom-amount slider is disabled
    under automatic, so the page rebuilds on each mode switch.
    """


AnyGraphicsLocalAction = (
    ApplySetting
    | ApplyFullscreen
    | ApplyResolution
    | ApplyMaxFps
    | ApplyScreenInsets
)


class GraphicsSettingsController(
    TypedDocUIController[AnyGraphicsRoute, AnyGraphicsLocalAction]
):
    """Doc-ui controller for the graphics settings page."""

    def __init__(self) -> None:
        assert bui.in_logic_thread()
        # The fullscreen calls are logic-thread-only; grab what page
        # builds (in the background) need now, and keep the value itself
        # current from our poll and our own changes.
        self._fullscreen_available = bui.fullscreen_control_available()
        self._fullscreen_shortcut = (
            bui.fullscreen_control_key_shortcut()
            if self._fullscreen_available
            else None
        )
        self._fullscreen = (
            bui.fullscreen_control_get()
            if self._fullscreen_available
            else False
        )

    @override
    @classmethod
    def get_route_type(cls) -> type[GraphicsRoute]:
        return GraphicsRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[GraphicsLocalAction]:
        return GraphicsLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        # As the other settings windows: minimal mid-game.
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def get_page_state_poll_interval(self) -> float | None:
        return _POLL_INTERVAL if self._fullscreen_available else None

    @override
    def poll_page_state(self, window: DocUIWindow) -> dict:
        del window  # Unused.
        self._fullscreen = bui.fullscreen_control_get()
        return {GraphicsState.key(lambda s: s.fullscreen): self._fullscreen}

    @override
    def fulfill_route(self, route: AnyGraphicsRoute) -> DocUIResponse:
        match route:
            case Root():
                return self._page()
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyGraphicsLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case ApplySetting():
                _apply_setting(context)
            case ApplyFullscreen():
                self._apply_fullscreen(context)
            case ApplyResolution():
                _apply_resolution(context)
            case ApplyMaxFps():
                _apply_max_fps(context)
            case ApplyScreenInsets():
                if _apply_screen_insets(context):
                    # The mode changed, which is what the custom slider's
                    # disabled-ness hangs off; rebuild to show it. (A
                    # switch that also changes the insets reflows the
                    # window, which refreshes too; that's harmless.)
                    self.replace(
                        context.window, Root().request(), is_refresh=True
                    )
            case _:
                assert_never(action)

    def _apply_fullscreen(self, context: DocUILocalAction) -> None:
        state = context.state(GraphicsState)
        if state is None or not self._fullscreen_available:
            return
        self._fullscreen = state.fullscreen
        bui.fullscreen_control_set(state.fullscreen)

    def _page(self) -> dui2.Response:
        """Build the page (called in a background thread)."""
        config = bui.app.config
        gstate = GraphicsState
        apply = ApplySetting().local(default_sound=False)

        # A device capped at medium quality shows anything higher
        # greyed out; a stored higher setting shows as the medium it
        # gets.
        visuals_disabled: list[Quality] = (
            [Quality.HIGHER, Quality.HIGH]
            if bui.get_max_graphics_quality() == 'Medium'
            else []
        )
        visuals = _enum_from_config(Quality, 'Graphics Quality', Quality.AUTO)
        if visuals in visuals_disabled:
            visuals = Quality.MEDIUM

        # Android picks among discrete resolutions (a popup); other
        # modes set a scale (a slider).
        resmode = _resolution_mode()
        reschoices = (
            _resolution_choices() if resmode is ResolutionMode.ANDROID else []
        )
        resolution = ''
        if reschoices:
            resolution = str(config.resolve('Resolution (Android)'))
            if resolution not in {c[0] for c in reschoices}:
                resolution = reschoices[0][0]
        scalerange = None if resmode is None else _scale_range(resmode)
        resolution_scale = 1.0
        if resmode is not None and scalerange is not None:
            key = _scale_config_key(resmode)
            assert key is not None
            resolution_scale = bui.snap_slider_value(
                float(config.resolve(key)),
                min_value=scalerange[0],
                max_value=scalerange[1],
                increment=_RESOLUTION_SCALE_INCREMENT,
            )

        state = GraphicsState(
            fullscreen=self._fullscreen,
            visuals=visuals,
            resolution=resolution,
            resolution_scale=resolution_scale,
            vsync=_enum_from_config(VSync, 'Vertical Sync', VSync.AUTO),
            max_fps=str(config.resolve('Max FPS')),
            show_fps=bool(config.resolve('Show FPS')),
            screen_insets=_enum_from_config(
                ScreenInsets, 'Screen Insets', ScreenInsets.AUTO
            ),
            custom_screen_insets=_snap_screen_insets(
                float(config.resolve('Custom Screen Insets'))
            ),
        )

        rows: list[dui2.Row] = []
        if self._fullscreen_available:
            label: LangStrSpec = _gfxstrs.fullscreen.spec
            if self._fullscreen_shortcut is not None:
                label = _gfxstrs.fullscreen_shortcut_format(
                    name=_gfxstrs.fullscreen,
                    shortcut=self._fullscreen_shortcut,
                ).spec
            rows.append(
                gstate.checkbox_row(
                    lambda s: s.fullscreen,
                    label=label,
                    on_change=ApplyFullscreen().local(default_sound=False),
                )
            )
        rows += [
            gstate.choice_row(
                lambda s: s.visuals,
                choice_label=_quality_label,
                disabled_choices=visuals_disabled,
                label=_gfxstrs.visuals.spec,
                on_change=apply,
            ),
            # Not wired up yet; shows players what's coming (ultra stays
            # disabled until it is).
            gstate.choice_row(
                lambda s: s.asset_quality,
                choice_label=_asset_quality_label,
                disabled_choices=[AssetQuality.ULTRA],
                # NEEDS_TRANSLATION
                label=LangStrSpecValue.literal('Asset Quality'),
            ),
        ]
        if reschoices:
            rows.append(
                gstate.choice_row(
                    lambda s: s.resolution,
                    choices=reschoices,
                    label=_gfxstrs.resolution.spec,
                    on_change=ApplyResolution().local(default_sound=False),
                )
            )
        elif scalerange is not None:
            # Applied live while dragging, so the effect shows as it
            # changes; 5% steps and the drag throttle keep render-target
            # reallocations infrequent.
            apply_res = ApplyResolution().local(default_sound=False)
            rows.append(
                gstate.slider_row(
                    lambda s: s.resolution_scale,
                    min_value=scalerange[0],
                    max_value=scalerange[1],
                    increment=_RESOLUTION_SCALE_INCREMENT,
                    as_percent=True,
                    label=_gfxstrs.resolution.spec,
                    on_drag=apply_res,
                    drag_interval=_RESOLUTION_DRAG_INTERVAL,
                    on_change=apply_res,
                )
            )
        if bui.supports_vsync():
            rows.append(
                gstate.choice_row(
                    lambda s: s.vsync,
                    choice_label=_vsync_label,
                    label=_gfxstrs.vertical_sync.spec,
                    on_change=apply,
                )
            )
        if bui.supports_max_fps():
            rows.append(
                gstate.text_input_row(
                    lambda s: s.max_fps,
                    label=_gfxstrs.max_fps.spec,
                    max_chars=5,
                    on_change=ApplyMaxFps().local(default_sound=False),
                )
            )
        rows.append(
            gstate.checkbox_row(
                lambda s: s.show_fps,
                label=_gfxstrs.show_fps.spec,
                on_change=apply,
            )
        )
        # Virtual bounds don't apply in VR (the UI lives on an overlay).
        if not bui.app.env.vr:
            apply_insets = ApplyScreenInsets().local(default_sound=False)
            rows += [
                gstate.choice_row(
                    lambda s: s.screen_insets,
                    choice_label=_screen_insets_label,
                    # NEEDS_TRANSLATION
                    label=LangStrSpecValue.literal('Screen Insets'),
                    on_change=apply_insets,
                ),
                # Applied only once settled (no on_drag): changing insets
                # reflows the UI, which would pull the slider out from
                # under an in-progress drag. Disabled under automatic,
                # which doesn't use it.
                gstate.slider_row(
                    lambda s: s.custom_screen_insets,
                    min_value=0.0,
                    max_value=1.0,
                    increment=_SCREEN_INSETS_INCREMENT,
                    as_percent=True,
                    # NEEDS_TRANSLATION
                    label=LangStrSpecValue.literal('Custom Screen Insets'),
                    on_change=apply_insets,
                    disabled=state.screen_insets is ScreenInsets.AUTO,
                ),
            ]

        return dui2.Response(
            page=dui2.Page(
                title=_gfxstrs.title.spec,
                rows=rows,
                state=state.encode(),
                center_vertically=True,
            )
        )


def _enum_from_config[E: Enum](enumtype: type[E], key: str, fallback: E) -> E:
    """A config string value as its enum; the fallback if unrecognized."""
    try:
        return enumtype(bui.app.config.resolve(key))
    except ValueError:
        return fallback


def _quality_label(quality: Quality) -> LangStrSpec:
    valstrs = _commonassets.strings.values
    match quality:
        case Quality.AUTO:
            return valstrs.auto.spec
        case Quality.HIGHER:
            return valstrs.higher.spec
        case Quality.HIGH:
            return valstrs.high.spec
        case Quality.MEDIUM:
            return valstrs.medium.spec
        case Quality.LOW:
            return valstrs.low.spec
        case _:
            assert_never(quality)


def _asset_quality_label(quality: AssetQuality) -> LangStrSpec:
    match quality:
        case AssetQuality.REGULAR:
            # NEEDS_TRANSLATION
            return LangStrSpecValue.literal('Regular')
        case AssetQuality.ULTRA:
            # NEEDS_TRANSLATION
            return LangStrSpecValue.literal('Ultra')
        case _:
            assert_never(quality)


def _vsync_label(vsync: VSync) -> LangStrSpec:
    valstrs = _commonassets.strings.values
    match vsync:
        case VSync.AUTO:
            return valstrs.auto.spec
        case VSync.ALWAYS:
            return valstrs.always.spec
        case VSync.NEVER:
            return valstrs.never.spec
        case _:
            assert_never(vsync)


def _screen_insets_label(insets: ScreenInsets) -> LangStrSpec:
    match insets:
        case ScreenInsets.AUTO:
            # NEEDS_TRANSLATION
            return LangStrSpecValue.literal('Automatic')
        case ScreenInsets.CUSTOM:
            # NEEDS_TRANSLATION
            return LangStrSpecValue.literal('Custom')
        case _:
            assert_never(insets)


def _snap_screen_insets(value: float) -> float:
    """A screen-insets amount as the slider can show it."""
    return bui.snap_slider_value(
        value, min_value=0.0, max_value=1.0, increment=_SCREEN_INSETS_INCREMENT
    )


def _resolution_mode() -> ResolutionMode | None:
    """What the resolution control sets here (None: no control)."""
    app = bui.app
    assert app.classic is not None
    cardboard = (
        app.classic.platform == 'android'
        and app.classic.subplatform == 'cardboard'
    )
    if app.env.vr and not cardboard:
        return None
    if app.classic.platform == 'android':
        return ResolutionMode.CARDBOARD if cardboard else ResolutionMode.ANDROID
    # Only systems that can't set a resolution directly get a control
    # (a pixel-scale one); discrete resolutions are no longer supported.
    if bui.get_display_resolution() is None:
        return ResolutionMode.PIXEL_SCALE
    return None


def _scale_range(mode: ResolutionMode) -> tuple[float, float] | None:
    """A scale-based mode's slider (min, max); None for other modes.

    The same limits the old percentage popups offered.
    """
    match mode:
        case ResolutionMode.CARDBOARD:
            return 0.35, 1.0
        case ResolutionMode.PIXEL_SCALE:
            return 0.5, 1.0
        case ResolutionMode.ANDROID:
            return None
        case _:
            assert_never(mode)


def _scale_config_key(mode: ResolutionMode) -> str | None:
    """The float config key a scale-based mode sets."""
    match mode:
        case ResolutionMode.CARDBOARD:
            return 'GVR Render Target Scale'
        case ResolutionMode.PIXEL_SCALE:
            return 'Screen Pixel Scale'
        case ResolutionMode.ANDROID:
            return None
        case _:
            assert_never(mode)


def _resolution_choices() -> list[tuple[str, LangStrSpec]]:
    """The Android resolution popup's choices."""
    native_res = bui.get_display_resolution()
    assert native_res is not None
    choices: list[tuple[str, LangStrSpec]] = [
        ('Auto', _commonassets.strings.values.auto.spec),
        ('Native', _gfxstrs.native.spec),
    ]
    for res in [1440, 1080, 960, 720, 480]:
        if native_res[1] >= res:
            choices.append((f'{res}p', LangStrSpecValue.literal(f'{res}p')))
    return choices


def _apply_setting(context: DocUILocalAction) -> None:
    """Write the changed setting to the config, as ConfigCheckBox would."""
    state = context.state(GraphicsState)
    if context.trigger is None or state is None:
        return
    key = _CONFIG_KEYS.get(context.trigger)
    if key is None:
        return
    # The wire form of the value is exactly the config form (bools; the
    # enums' string values).
    cfg = bui.app.config
    cfg[key] = state.encode()[context.trigger]
    cfg.apply_and_commit()


def _apply_resolution(context: DocUILocalAction) -> None:
    state = context.state(GraphicsState)
    mode = _resolution_mode()
    if state is None or mode is None:
        return
    cfg = bui.app.config
    key = _scale_config_key(mode)
    if key is None:
        cfg['Resolution (Android)'] = state.resolution
    else:
        cfg[key] = state.resolution_scale
    cfg.apply_and_commit()


def _apply_screen_insets(context: DocUILocalAction) -> bool:
    """Write the screen-insets settings; return whether the mode changed."""
    state = context.state(GraphicsState)
    if context.trigger is None or state is None:
        return False
    mode_key = GraphicsState.key(lambda s: s.screen_insets)
    amount_key = GraphicsState.key(lambda s: s.custom_screen_insets)
    amount = state.custom_screen_insets
    mode_changed = context.trigger == mode_key
    if mode_changed:
        # The slider follows automatic's amount across mode flips:
        # picking custom starts from what automatic was using (so
        # nothing jumps), and picking automatic shows what it is using.
        # (Snapped so the slider can show it exactly.)
        amount = _snap_screen_insets(bui.get_auto_screen_inset_amount())
        context.window.set_page_state_values({amount_key: amount})
    elif context.trigger != amount_key:
        return False
    cfg = bui.app.config
    cfg['Screen Insets'] = state.screen_insets.value
    cfg['Custom Screen Insets'] = amount
    cfg.apply_and_commit()
    return mode_changed


def _apply_max_fps(context: DocUILocalAction) -> None:
    """Clean up the typed max-fps value, write it, and show the result."""
    state = context.state(GraphicsState)
    if state is None:
        return
    cfg = bui.app.config
    try:
        ival = int(state.max_fps)
    except ValueError:
        # A broken value gets the default.
        ival = int(cfg.default_value('Max FPS'))

    # Clamp to reasonable limits (-1 means no max).
    if ival != -1:
        ival = min(99999, max(10, ival))
    cfg['Max FPS'] = ival
    cfg.apply_and_commit()

    # Show what was actually applied if that isn't what was typed.
    if str(ival) != state.max_fps:
        context.window.set_page_state_values(
            {GraphicsState.key(lambda s: s.max_fps): str(ival)}
        )
