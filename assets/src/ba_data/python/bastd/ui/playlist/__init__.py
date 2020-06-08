# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
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

        if issubclass(sessiontype, ba.DualTeamSession):
            play_mode_name = ba.Lstr(resource='playModes.teamsText',
                                     fallback_resource='teamsText')
            self.get_default_list_call = get_default_teams_playlist
            self.session_type_name = 'ba.DualTeamSession'
            self.config_name = 'Team Tournament'
            self.window_title_name = ba.Lstr(resource='playModes.teamsText',
                                             fallback_resource='teamsText')
            self.sessiontype = ba.DualTeamSession

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
            raise RuntimeError(
                f'Playlist type vars undefined for sessiontype: {sessiontype}')
        self.default_list_name = ba.Lstr(resource='defaultGameListNameText',
                                         subs=[('${PLAYMODE}', play_mode_name)
                                               ])
        self.default_new_list_name = ba.Lstr(
            resource='defaultNewGameListNameText',
            subs=[('${PLAYMODE}', play_mode_name)])
