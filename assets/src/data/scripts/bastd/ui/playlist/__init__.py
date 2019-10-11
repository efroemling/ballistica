# Copyright (c) 2011-2019 Eric Froemling
"""Playlist ui functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Type


# FIXME: Could change this to be a classmethod of session types?
class PlaylistTypeVars:
    """Defines values for a playlist type (config names to use, etc)."""

    def __init__(self, sessiontype: Type[ba.Session]):
        from ba.internal import (get_default_teams_playlist,
                                 get_default_free_for_all_playlist)
        self.sessiontype: Type[ba.Session]
        if issubclass(sessiontype, ba.TeamsSession):
            play_mode_name = ba.Lstr(resource='playModes.teamsText',
                                     fallback_resource='teamsText')
            self.get_default_list_call = get_default_teams_playlist
            self.session_type_name = 'ba.TeamsSession'
            self.config_name = 'Team Tournament'
            self.window_title_name = ba.Lstr(resource='playModes.teamsText',
                                             fallback_resource='teamsText')
            self.sessiontype = ba.TeamsSession
        elif issubclass(sessiontype, ba.FreeForAllSession):
            play_mode_name = ba.Lstr(resource='playModes.freeForAllText',
                                     fallback_resource='freeForAllText')
            self.get_default_list_call = get_default_free_for_all_playlist
            self.session_type_name = 'ba.FreeForAllSession'
            self.config_name = 'Free-for-All'
            self.window_title_name = ba.Lstr(
                resource='playModes.freeForAllText',
                fallback_resource='freeForAllText')
            self.sessiontype = ba.FreeForAllSession
        else:
            raise Exception('playlist type vars undefined for session type: ' +
                            str(sessiontype))
        self.default_list_name = ba.Lstr(resource='defaultGameListNameText',
                                         subs=[('${PLAYMODE}', play_mode_name)
                                               ])
        self.default_new_list_name = ba.Lstr(
            resource='defaultNewGameListNameText',
            subs=[('${PLAYMODE}', play_mode_name)])
