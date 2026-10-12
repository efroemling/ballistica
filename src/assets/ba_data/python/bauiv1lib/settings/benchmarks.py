# Released under the MIT License. See LICENSE for details.
#
"""Benchmarks and stress tests, as a doc-ui page.

A client-local doc-ui domain like the other settings pages: the page
is authored here, the stress-test options live in typed page state,
and each button is a typed local action.
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.docui.v2 as dui2
from bacommon.docui.presets import section_button, button_stack
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
    from typing import Literal

    from bacommon.docui import DocUIResponse
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui import DocUILocalAction

_bmstrs = _classicassets.strings.settings.benchmarks


class StressPlaylistType(Enum):
    """Kinds of playlist a stress test can run (run_stress_test's values)."""

    RANDOM = 'Random'
    TEAMS = 'Teams'
    FREE_FOR_ALL = 'Free-For-All'


class BenchmarksRoute(DocUIRoute):
    """Family class for the benchmarks routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyBenchmarksRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # Two benchmark buttons plus the stress-test options; too many
        # rows for the shorter small layouts.
        return dui2.WindowLayout.SMALL_TALLER


@ioprepped
@dataclass
class Root(BenchmarksRoute, path='/'):
    """The benchmarks page."""


AnyBenchmarksRoute = Root


@ioprepped
@dataclass
class BenchmarksState(DocUIState, state_id='settings.benchmarks'):
    """The stress-test options."""

    playlist_type: Annotated[StressPlaylistType, IOAttrs('pt')] = (
        StressPlaylistType.RANDOM
    )
    playlist_name: Annotated[str, IOAttrs('pn')] = '__default__'
    player_count: Annotated[float, IOAttrs('pc')] = 8.0

    #: Seconds.
    round_duration: Annotated[float, IOAttrs('rd')] = 30.0


class BenchmarksLocalAction(DocUILocalActionBase):
    """Family class for the benchmarks local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyBenchmarksLocalAction)


@ioprepped
@dataclass
class RunCpuBenchmark(BenchmarksLocalAction, name='cpu'):
    """Run the cpu benchmark."""


@ioprepped
@dataclass
class RunMediaReloadBenchmark(BenchmarksLocalAction, name='media_reload'):
    """Run the media-reload benchmark."""


@ioprepped
@dataclass
class RunStressTest(BenchmarksLocalAction, name='stress_test'):
    """Run a stress test with the options in page state."""


AnyBenchmarksLocalAction = (
    RunCpuBenchmark | RunMediaReloadBenchmark | RunStressTest
)


class BenchmarksController(
    TypedDocUIController[AnyBenchmarksRoute, AnyBenchmarksLocalAction]
):
    """Doc-ui controller for the benchmarks page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[BenchmarksRoute]:
        return BenchmarksRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[BenchmarksLocalAction]:
        return BenchmarksLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        # As the other settings windows: minimal mid-game.
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'

    @override
    def fulfill_route(self, route: AnyBenchmarksRoute) -> DocUIResponse:
        match route:
            case Root():
                _preload_modules()
                return _page()
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyBenchmarksLocalAction, context: DocUILocalAction
    ) -> None:
        classic = bui.app.classic
        if classic is None:
            logging.warning('%s requires classic.', type(action).__name__)
            return
        match action:
            case RunCpuBenchmark():
                classic.run_cpu_benchmark()
            case RunMediaReloadBenchmark():
                classic.run_media_reload_benchmark()
            case RunStressTest():
                _run_stress_test(context)
            case _:
                assert_never(action)


def _preload_modules() -> None:
    """Import what our actions use here, off the logic thread."""
    # pylint: disable=cyclic-import
    import bascenev1 as _unused1
    from bascenev1lib import mainmenu as _unused2


def _playlist_type_label(ptype: StressPlaylistType) -> LangStrSpec:
    match ptype:
        case StressPlaylistType.RANDOM:
            return _commonassets.strings.values.random.spec
        case StressPlaylistType.TEAMS:
            return _classicassets.strings.play_modes.teams.spec
        case StressPlaylistType.FREE_FOR_ALL:
            return _classicassets.strings.play_modes.free_for_all.spec
        case _:
            assert_never(ptype)


def _page() -> dui2.Response:
    """Build the page (called in a background thread)."""
    bstate = BenchmarksState
    rows: list[dui2.Row] = button_stack(
        [
            [
                section_button(
                    _bmstrs.run_cpu_benchmark.spec, RunCpuBenchmark().local()
                ),
                section_button(
                    _bmstrs.run_media_reload_benchmark.spec,
                    RunMediaReloadBenchmark().local(),
                ),
            ]
        ],
        first_group_spacing=0.0,
    )
    stress_rows: list[dui2.Row] = [
        bstate.choice_row(
            lambda s: s.playlist_type,
            choice_label=_playlist_type_label,
            label=_bmstrs.playlist_type.spec,
        ),
        bstate.text_input_row(
            lambda s: s.playlist_name,
            label=_bmstrs.playlist_name.spec,
            description=_bmstrs.playlist_description.spec,
        ),
        bstate.number_row(
            lambda s: s.player_count,
            min_value=1.0,
            max_value=64.0,
            increment=1.0,
            label=_bmstrs.player_count.spec,
        ),
        bstate.number_row(
            lambda s: s.round_duration,
            min_value=10.0,
            max_value=600.0,
            increment=10.0,
            label=_bmstrs.round_duration.spec,
        ),
    ]
    stress_rows += button_stack(
        [
            [
                section_button(
                    _bmstrs.run_stress_test.spec, RunStressTest().local()
                )
            ]
        ]
    )
    rows.append(
        dui2.Section(
            title=_bmstrs.stress_test.spec,
            title_align=dui2.HAlign.CENTER,
            rows=stress_rows,
        )
    )
    return dui2.Response(
        page=dui2.Page(
            title=_bmstrs.title.spec,
            rows=rows,
            # Its content is shorter than the window at larger
            # ui-scales, where top-aligned it looks top-heavy.
            center_vertically=True,
            state=BenchmarksState().encode(),
        )
    )


def _run_stress_test(context: DocUILocalAction) -> None:
    import bascenev1 as bs
    from bascenev1lib.mainmenu import MainMenuActivity

    classic = bui.app.classic
    assert classic is not None
    state = context.state(BenchmarksState)
    if state is None:
        return

    # Only from the main menu; not on top of some other activity.
    if not isinstance(bs.get_foreground_host_activity(), MainMenuActivity):
        bui.screenmessage(_bmstrs.already_running_in_activity)
        return

    classic.run_stress_test(
        playlist_type=state.playlist_type.value,
        playlist_name=state.playlist_name,
        player_count=round(state.player_count),
        round_duration=round(state.round_duration),
    )
    context.window.main_window_close(transition='out_right')
