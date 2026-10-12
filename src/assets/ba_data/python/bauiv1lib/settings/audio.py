# Released under the MIT License. See LICENSE for details.
#
"""Audio settings, as a doc-ui page.

A client-local doc-ui domain: the page is authored here, its volume
sliders keep their values in typed page state, and everything that
must happen *live* -- the volume being set as a slider is dragged,
the test blip -- is a typed local action reading that state. No
requests leave the device.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.docui.v2 as dui2
from bacommon.docui.presets import section_button, SectionButtonSize
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

    from bauiv1lib.docui import DocUILocalAction

_audstrs = _classicassets.strings.settings.audio

#: The blips a sound-volume drag plays: how often, and how long a
#: drag waits before its first (a flick shorter than this is heard
#: only where it lands). See the legacy ConfigSlider notes for the
#: tuning; these are the same numbers.
_SWISH_INTERVAL = 0.5
_SWISH_DELAY = 0.5

#: Nothing audible accompanies a music-volume apply, so it tracks a
#: drag more closely.
_MUSIC_APPLY_INTERVAL = 0.25


class AudioRoute(DocUIRoute):
    """Family class for the audio settings routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyAudioRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # A few short rows; a large window leaves them stranded.
        return dui2.WindowLayout.SMALL


@ioprepped
@dataclass
class Root(AudioRoute, path='/'):
    """The audio settings page."""


AnyAudioRoute = Root


@ioprepped
@dataclass
class AudioState(DocUIState, state_id='settings.audio'):
    """The page's volumes, mirroring the config values."""

    sound_volume: Annotated[float, IOAttrs('sv')] = 1.0
    music_volume: Annotated[float, IOAttrs('mv')] = 1.0


class AudioLocalAction(DocUILocalActionBase):
    """Family class for the audio settings local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyAudioLocalAction)


@ioprepped
@dataclass
class ApplyVolume(AudioLocalAction, name='apply_volume'):
    """Apply a slider's volume live (its on_drag): the running app
    hears it, plus whatever accompanies an apply -- the sound slider's
    blip, the music player's level."""


@ioprepped
@dataclass
class CommitVolume(AudioLocalAction, name='commit_volume'):
    """Save a settled volume (its on_change)."""


@ioprepped
@dataclass
class OpenSoundtracks(AudioLocalAction, name='soundtracks'):
    """Open the soundtrack browser."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH


AnyAudioLocalAction = ApplyVolume | CommitVolume | OpenSoundtracks

_SOUND_KEY = 'Sound Volume'
_MUSIC_KEY = 'Music Volume'


class AudioSettingsController(
    TypedDocUIController[AnyAudioRoute, AnyAudioLocalAction]
):
    """Doc-ui controller for the audio settings page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[AudioRoute]:
        return AudioRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[AudioLocalAction]:
        return AudioLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        # As the other settings windows: minimal mid-game.
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def fulfill_route(self, route: AnyAudioRoute) -> DocUIResponse:
        match route:
            case Root():
                return _page()
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyAudioLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case ApplyVolume():
                _apply_volume(context, commit=False)
            case CommitVolume():
                _apply_volume(context, commit=True)
            case OpenSoundtracks():
                _open_soundtracks(context)
            case _:
                assert_never(action)


def _page() -> dui2.Response:
    """Build the page (called in a background thread)."""
    assert bui.app.classic is not None
    config = bui.app.config
    astate = AudioState

    state = AudioState(
        sound_volume=float(config.resolve(_SOUND_KEY)),
        music_volume=float(config.resolve(_MUSIC_KEY)),
    )

    rows: list[dui2.Row] = [
        astate.slider_row(
            lambda s: s.sound_volume,
            min_value=0.0,
            max_value=1.0,
            increment=0.05,
            as_percent=True,
            label=_audstrs.sound_volume.spec,
            on_drag=ApplyVolume().local(default_sound=False),
            drag_interval=_SWISH_INTERVAL,
            drag_delay=_SWISH_DELAY,
            on_change=CommitVolume().local(default_sound=False),
        ),
        astate.slider_row(
            lambda s: s.music_volume,
            min_value=0.0,
            max_value=1.0,
            increment=0.05,
            as_percent=True,
            label=_audstrs.music_volume.spec,
            on_drag=ApplyVolume().local(default_sound=False),
            drag_interval=_MUSIC_APPLY_INTERVAL,
            on_change=CommitVolume().local(default_sound=False),
        ),
    ]

    # Soundtracks need a music player, which only some platforms have.
    if bui.app.classic.music.have_music_player():
        rows.append(
            dui2.ButtonRow(
                center_content=True,
                spacing_top=20,
                # The description sits under the button as the row's
                # footnote, centered like the button.
                footnote=_audstrs.soundtrack_description.spec,
                title_align=dui2.HAlign.CENTER,
                buttons=[
                    section_button(
                        _audstrs.soundtracks.spec,
                        OpenSoundtracks().local(),
                        size=SectionButtonSize.MEDIUM,
                    )
                ],
            )
        )

    return dui2.Response(
        page=dui2.Page(
            title=_audstrs.title.spec,
            rows=rows,
            state=state.encode(),
            center_vertically=True,
        )
    )


def _apply_volume(context: DocUILocalAction, *, commit: bool) -> None:
    """Push the slider that fired us into the app (and to disk if commit).

    Mirrors the legacy ConfigSlider: a drag apply is heard right away
    and carries its accompaniment (the blip; the music level); the
    settled value is what gets written.
    """
    assert bui.app.classic is not None
    state = context.state(AudioState)
    if state is None:
        return
    config = bui.app.config
    if context.trigger == AudioState.key(lambda s: s.sound_volume):
        config[_SOUND_KEY] = state.sound_volume
        if commit:
            config.apply_and_commit()
        else:
            config.apply()
            bui.play_swish()
    elif context.trigger == AudioState.key(lambda s: s.music_volume):
        config[_MUSIC_KEY] = state.music_volume
        if commit:
            config.apply_and_commit()
        else:
            config.apply()
            bui.app.classic.music.music_volume_changed(state.music_volume)


def _open_soundtracks(context: DocUILocalAction) -> None:
    # pylint: disable=cyclic-import
    from bauiv1lib.soundtrack.browser import SoundtrackBrowserWindow

    window = context.window

    # No-op if we're not in control.
    if not window.main_window_has_control():
        return

    # We require disk access for soundtracks; request it if we don't
    # have it.
    if not bui.have_permission(bui.Permission.STORAGE):
        _builtinassets.audio.ding.get().play()
        bui.screenmessage(
            _commonassets.strings.status.storage_permission_needed,
            color=(0.5, 1, 0.5),
        )
        bui.apptimer(
            1.0,
            bui.CallStrict(bui.request_permission, bui.Permission.STORAGE),
        )
        return

    window.main_window_replace(
        lambda: SoundtrackBrowserWindow(origin_widget=context.widget)
    )
