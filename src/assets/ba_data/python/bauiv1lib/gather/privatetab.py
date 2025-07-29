# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Defines the Private tab in the gather UI."""

from __future__ import annotations

import os
import copy
import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, override

from efro.error import CommunicationError
from efro.dataclassio import dataclass_from_dict, dataclass_to_dict
import bacommon.cloud
from bacommon.net import (
    PrivateHostingState,
    PrivateHostingConfig,
    PrivatePartyConnectResult,
)
from bauiv1lib.gather import GatherTab
from bauiv1lib.play import PlaylistSelectContext

from bauiv1lib.gettokens import show_get_tokens_prompt
import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any

    from bauiv1lib.gather import GatherWindow


# Print a bit of info about queries, etc.
DEBUG_SERVER_COMMUNICATION = os.environ.get('BA_DEBUG_PPTABCOM') == '1'


class SubTabType(Enum):
    """Available sub-tabs."""

    JOIN = 'join'
    HOST = 'host'


@dataclass
class State:
    """Our core state that persists while the app is running."""

    sub_tab: SubTabType = SubTabType.JOIN
    playlist_select_context: PlaylistSelectContext | None = None


class PrivateGatherTab(GatherTab):
    """The private tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._container: bui.Widget | None = None
        self._state: State = State()
        self._last_datacode_refresh_time: float | None = None
        self._hostingstate = PrivateHostingState()
        self._v2state: bacommon.bs.PrivatePartyResponse | None = None
        self._join_sub_tab_text: bui.Widget | None = None
        self._host_sub_tab_text: bui.Widget | None = None
        self._update_timer: bui.AppTimer | None = None
        self._join_party_code_text: bui.Widget | None = None
        self._c_width: float = 0.0
        self._c_height: float = 0.0
        self._last_hosting_state_query_time: float | None = None
        self._last_v2_state_query_time: float | None = None
        self._waiting_for_initial_state = True
        self._waiting_for_start_stop_response = True
        self._host_playlist_button: bui.Widget | None = None
        self._host_copy_button: bui.Widget | None = None
        self._host_connect_button: bui.Widget | None = None
        self._host_start_stop_button: bui.Widget | None = None
        self._get_tokens_button: bui.Widget | None = None
        self._token_count_text: bui.Widget | None = None
        self._showing_not_signed_in_screen = False
        self._create_time = time.time()
        self._last_action_send_time: float | None = None
        self._connect_press_time: float | None = None
        try:
            self._hostingconfig = self._build_hosting_config()
        except Exception:
            logging.exception('Error building hosting config.')
            self._hostingconfig = PrivateHostingConfig()

    @override
    def on_activate(
        self,
        parent_widget: bui.Widget,
        tab_button: bui.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> bui.Widget:
        # pylint: disable=too-many-positional-arguments
        self._c_width = region_width
        self._c_height = region_height - 20
        self._container = bui.containerwidget(
            parent=parent_widget,
            position=(
                region_left,
                region_bottom + (region_height - self._c_height) * 0.5,
            ),
            size=(self._c_width, self._c_height),
            background=False,
            selection_loops_to_parent=True,
        )
        v = self._c_height - 30.0
        self._join_sub_tab_text = bui.textwidget(
            parent=self._container,
            position=(self._c_width * 0.5 - 245, v - 13),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(200, 30),
            maxwidth=250,
            h_align='left',
            v_align='center',
            click_activate=True,
            selectable=True,
            autoselect=True,
            on_activate_call=lambda: self._set_sub_tab(
                SubTabType.JOIN,
                playsound=True,
            ),
            text=bui.Lstr(resource='gatherWindow.privatePartyJoinText'),
            glow_type='uniform',
        )
        self._host_sub_tab_text = bui.textwidget(
            parent=self._container,
            position=(self._c_width * 0.5 + 45, v - 13),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(200, 30),
            maxwidth=250,
            h_align='left',
            v_align='center',
            click_activate=True,
            selectable=True,
            autoselect=True,
            on_activate_call=lambda: self._set_sub_tab(
                SubTabType.HOST,
                playsound=True,
            ),
            text=bui.Lstr(resource='gatherWindow.privatePartyHostText'),
            glow_type='uniform',
        )
        bui.widget(edit=self._join_sub_tab_text, up_widget=tab_button)
        bui.widget(
            edit=self._host_sub_tab_text,
            left_widget=self._join_sub_tab_text,
            up_widget=tab_button,
        )
        bui.widget(
            edit=self._join_sub_tab_text, right_widget=self._host_sub_tab_text
        )

        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )

        # Prevent taking any action until we've updated our state.
        self._waiting_for_initial_state = True

        # Force some immediate refreshes.
        self._last_datacode_refresh_time = None
        self._last_v2_state_query_time = None
        self._last_action_send_time = None  # Ensure we don't ignore response.
        self._last_hosting_state_query_time = None
        self._update()

        self._set_sub_tab(self._state.sub_tab)

        return self._container

    def _build_hosting_config(self) -> PrivateHostingConfig:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        from bauiv1lib.playlist import PlaylistTypeVars
        from bascenev1 import filter_playlist

        hcfg = PrivateHostingConfig()
        cfg = bui.app.config
        sessiontypestr = cfg.get('Private Party Host Session Type', 'ffa')
        if not isinstance(sessiontypestr, str):
            raise RuntimeError(f'Invalid sessiontype {sessiontypestr}')
        hcfg.session_type = sessiontypestr

        sessiontype: type[bs.Session]
        if hcfg.session_type == 'ffa':
            sessiontype = bs.FreeForAllSession
        elif hcfg.session_type == 'teams':
            sessiontype = bs.DualTeamSession
        else:
            raise RuntimeError(f'Invalid sessiontype: {hcfg.session_type}')
        pvars = PlaylistTypeVars(sessiontype)

        playlist_name = bui.app.config.get(
            f'{pvars.config_name} Playlist Selection'
        )
        if not isinstance(playlist_name, str):
            playlist_name = '__default__'
        hcfg.playlist_name = (
            pvars.default_list_name.evaluate()
            if playlist_name == '__default__'
            else playlist_name
        )

        playlist: list[dict[str, Any]] | None = None
        if playlist_name != '__default__':
            playlist = cfg.get(f'{pvars.config_name} Playlists', {}).get(
                playlist_name
            )
        if playlist is None:
            playlist = pvars.get_default_list_call()

        hcfg.playlist = filter_playlist(
            playlist, sessiontype, name=playlist_name
        )

        randomize = cfg.get(f'{pvars.config_name} Playlist Randomize')
        if not isinstance(randomize, bool):
            randomize = False
        hcfg.randomize = randomize

        tutorial = cfg.get('Show Tutorial')
        if not isinstance(tutorial, bool):
            tutorial = True
        hcfg.tutorial = tutorial

        if hcfg.session_type == 'teams':
            ctn: list[str] | None = cfg.get('Custom Team Names')
            if ctn is not None:
                ctn_any: Any = ctn  # Actual value may not match type checker.
                if (
                    isinstance(ctn_any, (list, tuple))
                    and len(ctn) == 2
                    and all(isinstance(x, str) for x in ctn)
                ):
                    hcfg.custom_team_names = (ctn[0], ctn[1])
                else:
                    print(f'Found invalid custom-team-names data: {ctn}')

            ctc: list[list[float]] | None = cfg.get('Custom Team Colors')
            if ctc is not None:
                ctc_any: Any = ctc  # Actual value may not match type checker.
                if (
                    isinstance(ctc_any, (list, tuple))
                    and len(ctc) == 2
                    and all(isinstance(x, (list, tuple)) for x in ctc)
                    and all(len(x) == 3 for x in ctc)
                ):
                    hcfg.custom_team_colors = (
                        (ctc[0][0], ctc[0][1], ctc[0][2]),
                        (ctc[1][0], ctc[1][1], ctc[1][2]),
                    )
                else:
                    print(f'Found invalid custom-team-colors data: {ctc}')

        return hcfg

    @override
    def on_deactivate(self) -> None:
        self._update_timer = None

    def _update_currency_ui(self) -> None:
        # Keep currency count up to date if applicable.
        plus = bui.app.plus
        assert plus is not None

        if self._v2state is not None:
            t_str = str(self._v2state.tokens)
        else:
            t_str = '-'

        if self._get_tokens_button:
            bui.buttonwidget(
                edit=self._get_tokens_button,
                label=bui.charstr(bui.SpecialChar.TOKEN) + t_str,
            )
        if self._token_count_text:
            bui.textwidget(
                edit=self._token_count_text,
                text=bui.charstr(bui.SpecialChar.TOKEN) + t_str,
            )

    def _update(self) -> None:
        """Periodic updating."""

        plus = bui.app.plus
        assert plus is not None

        now = bui.apptime()

        self._update_currency_ui()

        if self._state.sub_tab is SubTabType.HOST:
            # If we're not signed in, just refresh to show that.
            if (
                plus.accounts.primary is None
            ) and not self._showing_not_signed_in_screen:
                self._refresh_sub_tab()
            else:
                # Query an updated v1 state periodically.
                if (
                    self._last_hosting_state_query_time is None
                    or now - self._last_hosting_state_query_time > 15.0
                ):
                    self._debug_server_comm('querying private party state')
                    if plus.get_v1_account_state() == 'signed_in':
                        plus.add_v1_account_transaction(
                            {
                                'type': 'PRIVATE_PARTY_QUERY',
                                'expire_time': time.time() + 20,
                            },
                            callback=bui.WeakCall(
                                self._idle_hosting_state_response
                            ),
                        )
                        plus.run_v1_account_transactions()
                    else:
                        self._idle_hosting_state_response(None)
                    self._last_hosting_state_query_time = now

                # Query an updated v2 state periodically.
                if (
                    self._last_v2_state_query_time is None
                    or now - self._last_v2_state_query_time > 12.0
                ):
                    self._debug_server_comm('querying pp v2 state')

                    if plus.accounts.primary is not None:
                        with plus.accounts.primary:
                            plus.cloud.send_message_cb(
                                bacommon.bs.PrivatePartyMessage(
                                    need_datacode=(
                                        self._last_datacode_refresh_time is None
                                        or time.monotonic()
                                        - self._last_datacode_refresh_time
                                        > 30.0
                                    )
                                ),
                                on_response=bui.WeakCall(
                                    self._on_private_party_query_response
                                ),
                            )

                    self._last_v2_state_query_time = now

    def _on_private_party_query_response(
        self, response: bacommon.bs.PrivatePartyResponse | Exception
    ) -> None:
        if isinstance(response, Exception):
            self._debug_server_comm('got pp v2 state response (err)')
            # We expect comm errors sometimes. Make noise on anything else.
            if not isinstance(response, CommunicationError):
                logging.exception('Error on private-party-query-response')
            return

        # Ignore if something went wrong server-side.
        if not response.success:
            self._debug_server_comm('got pp v2 state response (serverside err)')
            return

        self._debug_server_comm('got pp v2 state response')

        existing_datacode = (
            None if self._v2state is None else self._v2state.datacode
        )

        self._v2state = response
        if self._v2state.datacode is None:
            # We don't fetch datacode each time; preserve our existing
            # if we didn't.
            self._v2state.datacode = existing_datacode
        else:
            # If we *did* fetch it, note the time.
            self._last_datacode_refresh_time = time.monotonic()

    def _idle_hosting_state_response(
        self, result: dict[str, Any] | None
    ) -> None:
        # This simply passes through to our standard response handler.
        # The one exception is if we've recently sent an action to the
        # server (start/stop hosting/etc.) In that case we want to
        # ignore idle background updates and wait for the response to
        # our action. (this keeps the button showing 'one moment...'
        # until the change takes effect, etc.)
        if (
            self._last_action_send_time is not None
            and time.time() - self._last_action_send_time < 5.0
        ):
            self._debug_server_comm(
                'ignoring private party state response due to recent action'
            )
            return
        self._hosting_state_response(result)

    def _hosting_state_response(self, result: dict[str, Any] | None) -> None:
        # Its possible for this to come back to us after our UI is dead;
        # ignore in that case.
        if not self._container:
            return

        state: PrivateHostingState | None = None
        if result is not None:
            self._debug_server_comm('got private party state response')
            try:
                state = dataclass_from_dict(
                    PrivateHostingState, result, discard_unknown_attrs=True
                )
            except Exception:
                logging.exception('Got invalid PrivateHostingState data')
        else:
            self._debug_server_comm('private party state response errored')

        # Hmm I guess let's just ignore failed responses?... Or should
        # we show some sort of error state to the user?...
        if result is None or state is None:
            return

        self._waiting_for_initial_state = False
        self._waiting_for_start_stop_response = False
        self._hostingstate = state
        self._refresh_sub_tab()

    def _set_sub_tab(self, value: SubTabType, playsound: bool = False) -> None:
        assert self._container
        if playsound:
            bui.getsound('click01').play()

        # If switching from join to host, force some refreshes.
        if self._state.sub_tab is SubTabType.JOIN and value is SubTabType.HOST:
            # Prevent taking any action until we've gotten a fresh
            # state.
            self._waiting_for_initial_state = True

            # Get some refreshes going immediately.
            self._last_hosting_state_query_time = None
            self._last_action_send_time = None  # So we don't ignore response.
            self._last_datacode_refresh_time = None
            self._last_v2_state_query_time = None
            self._update()

        self._state.sub_tab = value
        active_color = (0.6, 1.0, 0.6)
        inactive_color = (0.5, 0.4, 0.5)
        bui.textwidget(
            edit=self._join_sub_tab_text,
            color=active_color if value is SubTabType.JOIN else inactive_color,
        )
        bui.textwidget(
            edit=self._host_sub_tab_text,
            color=active_color if value is SubTabType.HOST else inactive_color,
        )

        self._refresh_sub_tab()

        # Kick off an update to get any needed messages sent/etc.
        bui.pushcall(self._update)

    def _selwidgets(self) -> list[bui.Widget | None]:
        """An indexed list of widgets we can use for saving/restoring sel."""
        return [
            self._host_playlist_button,
            self._host_copy_button,
            self._host_connect_button,
            self._host_start_stop_button,
            self._get_tokens_button,
        ]

    def _refresh_sub_tab(self) -> None:
        assert self._container

        # Store an index for our current selection so we can reselect
        # the equivalent recreated widget if possible.
        selindex: int | None = None
        selchild = self._container.get_selected_child()
        if selchild is not None:
            try:
                selindex = self._selwidgets().index(selchild)
            except ValueError:
                pass

        # Clear anything existing in the old sub-tab.
        for widget in self._container.get_children():
            if widget and widget not in {
                self._host_sub_tab_text,
                self._join_sub_tab_text,
            }:
                widget.delete()

        if self._state.sub_tab is SubTabType.JOIN:
            self._build_join_tab()
        elif self._state.sub_tab is SubTabType.HOST:
            self._build_host_tab()
        else:
            raise RuntimeError('Invalid state.')

        # Select the new equivalent widget if there is one.
        if selindex is not None:
            selwidget = self._selwidgets()[selindex]
            if selwidget:
                bui.containerwidget(
                    edit=self._container, selected_child=selwidget
                )

    def _build_join_tab(self) -> None:
        bui.textwidget(
            parent=self._container,
            position=(self._c_width * 0.5, self._c_height - 140),
            color=(0.5, 0.46, 0.5),
            scale=1.5,
            size=(0, 0),
            maxwidth=250,
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='gatherWindow.partyCodeText'),
        )

        self._join_party_code_text = bui.textwidget(
            parent=self._container,
            position=(self._c_width * 0.5 - 150, self._c_height - 250),
            flatness=1.0,
            scale=1.5,
            size=(300, 50),
            editable=True,
            max_chars=20,
            description=bui.Lstr(resource='gatherWindow.partyCodeText'),
            autoselect=True,
            h_align='left',
            v_align='center',
            text='',
        )
        btn = bui.buttonwidget(
            parent=self._container,
            size=(300, 70),
            label=bui.Lstr(resource='gatherWindow.manualConnectText'),
            position=(self._c_width * 0.5 - 150, self._c_height - 350),
            on_activate_call=self._join_connect_press,
            autoselect=True,
        )
        bui.textwidget(
            edit=self._join_party_code_text, on_return_press_call=btn.activate
        )

    def _build_host_tab(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        classic = bui.app.classic
        assert classic is not None

        plus = bui.app.plus
        assert plus is not None

        hostingstate = self._hostingstate

        havegoldpass = self._v2state is not None and self._v2state.gold_pass

        # We use both v1 and v2 account functionality here (sigh). So
        # make sure we're signed in on both ends.

        # Make sure the V1 side is good to go.
        if plus.get_v1_account_state() != 'signed_in':
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=self._c_width * 0.8,
                scale=0.8,
                color=(0.6, 0.56, 0.6),
                position=(self._c_width * 0.5, self._c_height * 0.5),
                text=bui.Lstr(resource='notSignedInErrorText'),
            )
            self._showing_not_signed_in_screen = True
            return

        # Make sure the V2 side is good to go.
        if plus.accounts.primary is None:
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=self._c_width * 0.8,
                scale=0.8,
                color=(0.6, 0.56, 0.6),
                position=(self._c_width * 0.5, self._c_height * 0.5),
                text=bui.Lstr(resource='v2AccountRequiredText'),
            )
            self._showing_not_signed_in_screen = True
            return

        self._showing_not_signed_in_screen = False

        # At first we don't want to show anything until we've gotten a
        # state. Update: In this situation we now simply show our
        # existing state but give the start/stop button a loading
        # message and disallow its use. This keeps things a lot less
        # jumpy looking and allows selecting playlists/etc without
        # having to wait for the server each time back to the ui.
        if self._waiting_for_initial_state and bool(False):
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=200,
                scale=0.8,
                color=(0.6, 0.56, 0.6),
                position=(self._c_width * 0.5, self._c_height * 0.5),
                text=bui.Lstr(
                    value='${A}...',
                    subs=[('${A}', bui.Lstr(resource='store.loadingText'))],
                ),
            )
            return

        # If we're not currently hosting and hosting requires tokens,
        # Show our count (possibly with a link to purchase more).
        if (
            not self._waiting_for_initial_state
            and hostingstate.party_code is None
            and hostingstate.tickets_to_host_now != 0
            and not havegoldpass
        ):
            pass

        v = self._c_height - 90
        if hostingstate.party_code is None:
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=self._c_width * 0.9,
                scale=0.7,
                flatness=1.0,
                color=(0.5, 0.46, 0.5),
                position=(self._c_width * 0.5, v),
                text=bui.Lstr(
                    resource='gatherWindow.privatePartyCloudDescriptionText'
                ),
            )

        v -= 90
        if hostingstate.party_code is None:
            # We've got no current party running; show options to set
            # one up.
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='right',
                v_align='center',
                maxwidth=200,
                scale=0.8,
                color=(0.6, 0.56, 0.6),
                position=(self._c_width * 0.5 - 210, v),
                text=bui.Lstr(resource='playlistText'),
            )
            self._host_playlist_button = bui.buttonwidget(
                parent=self._container,
                size=(400, 70),
                color=(0.6, 0.5, 0.6),
                textcolor=(0.8, 0.75, 0.8),
                label=self._hostingconfig.playlist_name,
                on_activate_call=self._playlist_press,
                position=(self._c_width * 0.5 - 200, v - 35),
                up_widget=self._host_sub_tab_text,
                autoselect=True,
            )

            # If it appears we're coming back from playlist selection,
            # re-select our playlist button.
            if self._state.playlist_select_context is not None:
                self._state.playlist_select_context = None
                bui.containerwidget(
                    edit=self._container,
                    selected_child=self._host_playlist_button,
                )

        else:
            # We've got a current party; show its info.
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=600,
                scale=0.9,
                color=(0.7, 0.64, 0.7),
                position=(self._c_width * 0.5, v + 90),
                text=bui.Lstr(resource='gatherWindow.partyServerRunningText'),
            )
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=600,
                scale=0.7,
                color=(0.7, 0.64, 0.7),
                position=(self._c_width * 0.5, v + 50),
                text=bui.Lstr(resource='gatherWindow.partyCodeText'),
            )
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=2.0,
                color=(0.0, 1.0, 0.0),
                position=(self._c_width * 0.5, v + 10),
                text=hostingstate.party_code,
            )

            # Also action buttons to copy it and connect to it.
            if bui.clipboard_is_supported():
                cbtnoffs = 10
                self._host_copy_button = bui.buttonwidget(
                    parent=self._container,
                    size=(140, 40),
                    color=(0.6, 0.5, 0.6),
                    textcolor=(0.8, 0.75, 0.8),
                    label=bui.Lstr(resource='gatherWindow.copyCodeText'),
                    on_activate_call=self._host_copy_press,
                    position=(self._c_width * 0.5 - 150, v - 70),
                    autoselect=True,
                )
            else:
                cbtnoffs = -70
            self._host_connect_button = bui.buttonwidget(
                parent=self._container,
                size=(140, 40),
                color=(0.6, 0.5, 0.6),
                textcolor=(0.8, 0.75, 0.8),
                label=bui.Lstr(resource='gatherWindow.manualConnectText'),
                on_activate_call=self._host_connect_press,
                position=(self._c_width * 0.5 + cbtnoffs, v - 70),
                autoselect=True,
            )

        v -= 110

        # Line above the main action button:

        # If we don't want to show anything until we get a state:
        if self._waiting_for_initial_state:
            pass
        elif hostingstate.unavailable_error is not None:
            # If hosting is unavailable, show the associated reason.
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=self._c_width * 0.9,
                scale=0.7,
                flatness=1.0,
                color=(1.0, 0.0, 0.0),
                position=(self._c_width * 0.5, v),
                text=bui.Lstr(
                    translate=(
                        'serverResponses',
                        hostingstate.unavailable_error,
                    )
                ),
            )
        elif havegoldpass:
            # If we have a gold pass, none of the
            # timing/free-server-availability info below is relevant to
            # us.
            pass
        elif hostingstate.free_host_minutes_remaining is not None:
            # If we've been pre-approved to start/stop for free, show
            # that.
            bui.textwidget(
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=self._c_width * 0.9,
                scale=0.7,
                flatness=1.0,
                color=(
                    (0.7, 0.64, 0.7)
                    if hostingstate.party_code
                    else (0.0, 1.0, 0.0)
                ),
                position=(self._c_width * 0.5, v),
                text=bui.Lstr(
                    resource='gatherWindow.startStopHostingMinutesText',
                    subs=[
                        (
                            '${MINUTES}',
                            f'{hostingstate.free_host_minutes_remaining:.0f}',
                        )
                    ],
                ),
            )
        else:
            # Otherwise tell whether the free cloud server is available
            # or will be at some point.
            if hostingstate.party_code is None:
                if hostingstate.tickets_to_host_now == 0:
                    bui.textwidget(
                        parent=self._container,
                        size=(0, 0),
                        h_align='center',
                        v_align='center',
                        maxwidth=self._c_width * 0.9,
                        scale=0.7,
                        flatness=1.0,
                        color=(0.0, 1.0, 0.0),
                        position=(self._c_width * 0.5, v),
                        text=bui.Lstr(
                            resource=(
                                'gatherWindow.freeCloudServerAvailableNowText'
                            )
                        ),
                    )
                else:
                    if hostingstate.minutes_until_free_host is None:
                        bui.textwidget(
                            parent=self._container,
                            size=(0, 0),
                            h_align='center',
                            v_align='center',
                            maxwidth=self._c_width * 0.9,
                            scale=0.7,
                            flatness=1.0,
                            color=(1.0, 0.6, 0.0),
                            position=(self._c_width * 0.5, v),
                            text=bui.Lstr(
                                resource=(
                                    'gatherWindow'
                                    '.freeCloudServerNotAvailableText'
                                )
                            ),
                        )
                    else:
                        availmins = hostingstate.minutes_until_free_host
                        bui.textwidget(
                            parent=self._container,
                            size=(0, 0),
                            h_align='center',
                            v_align='center',
                            maxwidth=self._c_width * 0.9,
                            scale=0.7,
                            flatness=1.0,
                            color=(1.0, 0.6, 0.0),
                            position=(self._c_width * 0.5, v),
                            text=bui.Lstr(
                                resource='gatherWindow.'
                                'freeCloudServerAvailableMinutesText',
                                subs=[('${MINUTES}', f'{availmins:.0f}')],
                            ),
                        )

        v -= 100

        if (
            self._waiting_for_start_stop_response
            or self._waiting_for_initial_state
        ):
            btnlabel = bui.Lstr(resource='oneMomentText')
        else:
            if hostingstate.unavailable_error is not None:
                btnlabel = bui.Lstr(
                    resource='gatherWindow.hostingUnavailableText'
                )
            elif hostingstate.party_code is None:
                ticon = bui.charstr(bui.SpecialChar.TOKEN)
                nowtokens = hostingstate.tokens_to_host_now
                if nowtokens > 0 and not havegoldpass:
                    btnlabel = bui.Lstr(
                        resource='gatherWindow.startHostingPaidText',
                        subs=[('${COST}', f'{ticon}{nowtokens}')],
                    )
                else:
                    btnlabel = bui.Lstr(
                        resource='gatherWindow.startHostingText'
                    )
            else:
                btnlabel = bui.Lstr(resource='gatherWindow.stopHostingText')

        disabled = (
            hostingstate.unavailable_error is not None
            or self._waiting_for_initial_state
        )
        waiting = self._waiting_for_start_stop_response
        self._host_start_stop_button = bui.buttonwidget(
            parent=self._container,
            size=(400, 80),
            color=(
                (0.6, 0.6, 0.6)
                if disabled
                else (0.5, 1.0, 0.5) if waiting else None
            ),
            enable_sound=False,
            label=btnlabel,
            textcolor=((0.7, 0.7, 0.7) if disabled else None),
            position=(self._c_width * 0.5 - 200, v),
            on_activate_call=self._start_stop_button_press,
            autoselect=True,
        )

    def _playlist_press(self) -> None:
        assert self._host_playlist_button is not None

        self._state.playlist_select_context = PlaylistSelectContext()

        self.window.playlist_select(
            origin_widget=self._host_playlist_button,
            context=self._state.playlist_select_context,
        )

    def _host_copy_press(self) -> None:
        assert self._hostingstate.party_code is not None
        bui.clipboard_set_text(self._hostingstate.party_code)
        bui.screenmessage(bui.Lstr(resource='gatherWindow.copyCodeConfirmText'))

    def _host_connect_press(self) -> None:
        assert self._hostingstate.party_code is not None
        self._connect_to_party_code(self._hostingstate.party_code)

    def _debug_server_comm(self, msg: str) -> None:
        if DEBUG_SERVER_COMMUNICATION:
            print(
                f'PPTABCOM: {msg} at time '
                f'{time.time()-self._create_time:.2f}'
            )

    def _connect_to_party_code(self, code: str) -> None:
        # Ignore attempted followup sends for a few seconds (this will
        # reset if we get a response).
        plus = bui.app.plus
        assert plus is not None

        now = time.time()
        if (
            self._connect_press_time is not None
            and now - self._connect_press_time < 5.0
        ):
            self._debug_server_comm(
                'not sending private party connect (too soon)'
            )
            return
        self._connect_press_time = now

        self._debug_server_comm('sending private party connect')
        plus.add_v1_account_transaction(
            {
                'type': 'PRIVATE_PARTY_CONNECT',
                'expire_time': time.time() + 20,
                'code': code,
            },
            callback=bui.WeakCall(self._connect_response),
        )
        plus.run_v1_account_transactions()

    def _start_stop_button_press(self) -> None:
        plus = bui.app.plus
        assert plus is not None
        if (
            self._waiting_for_start_stop_response
            or self._waiting_for_initial_state
        ):
            return

        if plus.get_v1_account_state() != 'signed_in':
            bui.screenmessage(bui.Lstr(resource='notSignedInErrorText'))
            bui.getsound('error').play()
            self._refresh_sub_tab()
            return

        if self._hostingstate.unavailable_error is not None:
            bui.getsound('error').play()
            return

        bui.getsound('click01').play()

        # We need our v2 info for this.
        if self._v2state is None or self._v2state.datacode is None:
            bui.screenmessage(
                bui.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # If we're not hosting, start.
        if self._hostingstate.party_code is None:
            # If there's a token cost, make sure we have enough tokens
            # or a gold pass.
            if self._hostingstate.tokens_to_host_now > 0:

                if (
                    not self._v2state.gold_pass
                    and self._v2state.tokens
                    < self._hostingstate.tokens_to_host_now
                ):
                    show_get_tokens_prompt()
                    bui.getsound('error').play()
                    return

            self._last_action_send_time = time.time()
            plus.add_v1_account_transaction(
                {
                    'type': 'PRIVATE_PARTY_START',
                    'config': dataclass_to_dict(self._hostingconfig),
                    'region_pings': bui.app.net.zone_pings,
                    'expire_time': time.time() + 20,
                    'datacode': self._v2state.datacode,
                },
                callback=bui.WeakCall(self._hosting_state_response),
            )
            plus.run_v1_account_transactions()

        else:
            self._last_action_send_time = time.time()
            plus.add_v1_account_transaction(
                {
                    'type': 'PRIVATE_PARTY_STOP',
                    'expire_time': time.time() + 20,
                },
                callback=bui.WeakCall(self._hosting_state_response),
            )
            plus.run_v1_account_transactions()
        bui.getsound('click01').play()

        self._waiting_for_start_stop_response = True
        self._refresh_sub_tab()

    def _join_connect_press(self) -> None:
        # Error immediately if its an empty code.
        code: str | None = None
        if self._join_party_code_text:
            code = cast(str, bui.textwidget(query=self._join_party_code_text))
        if not code:
            bui.screenmessage(
                bui.Lstr(translate=('serverResponses', 'Invalid code.')),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        self._connect_to_party_code(code)

    def _connect_response(self, result: dict[str, Any] | None) -> None:
        try:
            self._connect_press_time = None
            if result is None:
                raise RuntimeError()
            cresult = dataclass_from_dict(
                PrivatePartyConnectResult, result, discard_unknown_attrs=True
            )
            if cresult.error is not None:
                self._debug_server_comm('got error connect response')
                bui.screenmessage(
                    bui.Lstr(translate=('serverResponses', cresult.error)),
                    (1, 0, 0),
                )
                bui.getsound('error').play()
                return
            self._debug_server_comm('got valid connect response')
            assert cresult.address4 is not None and cresult.port is not None

            # Store UI location to return to when done.
            if bs.app.classic is not None:
                bs.app.classic.save_ui_state()

            bs.connect_to_party(cresult.address4, port=cresult.port)
        except Exception:
            self._debug_server_comm('got connect response error')
            bui.getsound('error').play()

    @override
    def save_state(self) -> None:
        assert bui.app.classic is not None
        bui.app.ui_v1.window_states[type(self)] = copy.deepcopy(self._state)

    @override
    def restore_state(self) -> None:
        assert bui.app.classic is not None
        state = bui.app.ui_v1.window_states.get(type(self))
        if state is None:
            state = State()
        assert isinstance(state, State)
        self._state = state
