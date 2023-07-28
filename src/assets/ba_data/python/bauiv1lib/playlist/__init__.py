# Released under the MIT License. See LICENSE for details.
#
"""Playlist ui functionality."""

from __future__ import annotations

import bascenev1 as bs


# FIXME: Could change this to be a classmethod of session types?
class PlaylistTypeVars:
    """Defines values for a playlist type (config names to use, etc)."""

    def __init__(self, sessiontype: type[bs.Session]):
        from bascenev1 import (
            get_default_teams_playlist,
            get_default_free_for_all_playlist,
        )

        self.sessiontype: type[bs.Session]

        if issubclass(sessiontype, bs.DualTeamSession):
            play_mode_name = bs.Lstr(
                resource='playModes.teamsText', fallback_resource='teamsText'
            )
            self.get_default_list_call = get_default_teams_playlist
            self.session_type_name = 'bascenev1.DualTeamSession'
            self.config_name = 'Team Tournament'
            self.window_title_name = bs.Lstr(
                resource='playModes.teamsText', fallback_resource='teamsText'
            )
            self.sessiontype = bs.DualTeamSession

        elif issubclass(sessiontype, bs.FreeForAllSession):
            play_mode_name = bs.Lstr(
                resource='playModes.freeForAllText',
                fallback_resource='freeForAllText',
            )
            self.get_default_list_call = get_default_free_for_all_playlist
            self.session_type_name = 'bascenev1.FreeForAllSession'
            self.config_name = 'Free-for-All'
            self.window_title_name = bs.Lstr(
                resource='playModes.freeForAllText',
                fallback_resource='freeForAllText',
            )
            self.sessiontype = bs.FreeForAllSession

        else:
            raise RuntimeError(
                f'Playlist type vars undefined for sessiontype: {sessiontype}'
            )
        self.default_list_name = bs.Lstr(
            resource='defaultGameListNameText',
            subs=[('${PLAYMODE}', play_mode_name)],
        )
        self.default_new_list_name = bs.Lstr(
            resource='defaultNewGameListNameText',
            subs=[('${PLAYMODE}', play_mode_name)],
        )
