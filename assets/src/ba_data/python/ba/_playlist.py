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
"""Playlist related functionality."""

from __future__ import annotations

import copy
from typing import Any, TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from typing import Type, Sequence
    from ba import _session

PlaylistType = List[Dict[str, Any]]


def filter_playlist(playlist: PlaylistType,
                    sessiontype: Type[_session.Session],
                    add_resolved_type: bool = False,
                    remove_unowned: bool = True,
                    mark_unowned: bool = False) -> PlaylistType:
    """Return a filtered version of a playlist.

    Strips out or replaces invalid or unowned game types, makes sure all
    settings are present, and adds in a 'resolved_type' which is the actual
    type.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    from ba import _meta
    from ba import _map
    from ba import _general
    from ba import _gameactivity
    goodlist: List[Dict] = []
    unowned_maps: Sequence[str]
    if remove_unowned or mark_unowned:
        unowned_maps = _map.get_unowned_maps()
        unowned_game_types = _meta.get_unowned_game_types()
    else:
        unowned_maps = []
        unowned_game_types = set()

    for entry in copy.deepcopy(playlist):
        # 'map' used to be called 'level' here.
        if 'level' in entry:
            entry['map'] = entry['level']
            del entry['level']

        # We now stuff map into settings instead of it being its own thing.
        if 'map' in entry:
            entry['settings']['map'] = entry['map']
            del entry['map']

        # Update old map names to new ones.
        entry['settings']['map'] = _map.get_filtered_map_name(
            entry['settings']['map'])
        if remove_unowned and entry['settings']['map'] in unowned_maps:
            continue

        # Ok, for each game in our list, try to import the module and grab
        # the actual game class. add successful ones to our initial list
        # to present to the user.
        if not isinstance(entry['type'], str):
            raise TypeError('invalid entry format')
        try:
            # Do some type filters for backwards compat.
            if entry['type'] in ('Assault.AssaultGame',
                                 'Happy_Thoughts.HappyThoughtsGame',
                                 'bsAssault.AssaultGame',
                                 'bs_assault.AssaultGame'):
                entry['type'] = 'bastd.game.assault.AssaultGame'
            if entry['type'] in ('King_of_the_Hill.KingOfTheHillGame',
                                 'bsKingOfTheHill.KingOfTheHillGame',
                                 'bs_king_of_the_hill.KingOfTheHillGame'):
                entry['type'] = 'bastd.game.kingofthehill.KingOfTheHillGame'
            if entry['type'] in ('Capture_the_Flag.CTFGame',
                                 'bsCaptureTheFlag.CTFGame',
                                 'bs_capture_the_flag.CTFGame'):
                entry['type'] = (
                    'bastd.game.capturetheflag.CaptureTheFlagGame')
            if entry['type'] in ('Death_Match.DeathMatchGame',
                                 'bsDeathMatch.DeathMatchGame',
                                 'bs_death_match.DeathMatchGame'):
                entry['type'] = 'bastd.game.deathmatch.DeathMatchGame'
            if entry['type'] in ('ChosenOne.ChosenOneGame',
                                 'bsChosenOne.ChosenOneGame',
                                 'bs_chosen_one.ChosenOneGame'):
                entry['type'] = 'bastd.game.chosenone.ChosenOneGame'
            if entry['type'] in ('Conquest.Conquest', 'Conquest.ConquestGame',
                                 'bsConquest.ConquestGame',
                                 'bs_conquest.ConquestGame'):
                entry['type'] = 'bastd.game.conquest.ConquestGame'
            if entry['type'] in ('Elimination.EliminationGame',
                                 'bsElimination.EliminationGame',
                                 'bs_elimination.EliminationGame'):
                entry['type'] = 'bastd.game.elimination.EliminationGame'
            if entry['type'] in ('Football.FootballGame',
                                 'bsFootball.FootballTeamGame',
                                 'bs_football.FootballTeamGame'):
                entry['type'] = 'bastd.game.football.FootballTeamGame'
            if entry['type'] in ('Hockey.HockeyGame', 'bsHockey.HockeyGame',
                                 'bs_hockey.HockeyGame'):
                entry['type'] = 'bastd.game.hockey.HockeyGame'
            if entry['type'] in ('Keep_Away.KeepAwayGame',
                                 'bsKeepAway.KeepAwayGame',
                                 'bs_keep_away.KeepAwayGame'):
                entry['type'] = 'bastd.game.keepaway.KeepAwayGame'
            if entry['type'] in ('Race.RaceGame', 'bsRace.RaceGame',
                                 'bs_race.RaceGame'):
                entry['type'] = 'bastd.game.race.RaceGame'
            if entry['type'] in ('bsEasterEggHunt.EasterEggHuntGame',
                                 'bs_easter_egg_hunt.EasterEggHuntGame'):
                entry['type'] = 'bastd.game.easteregghunt.EasterEggHuntGame'
            if entry['type'] in ('bsMeteorShower.MeteorShowerGame',
                                 'bs_meteor_shower.MeteorShowerGame'):
                entry['type'] = 'bastd.game.meteorshower.MeteorShowerGame'
            if entry['type'] in ('bsTargetPractice.TargetPracticeGame',
                                 'bs_target_practice.TargetPracticeGame'):
                entry['type'] = (
                    'bastd.game.targetpractice.TargetPracticeGame')

            gameclass = _general.getclass(entry['type'],
                                          _gameactivity.GameActivity)

            if remove_unowned and gameclass in unowned_game_types:
                continue
            if add_resolved_type:
                entry['resolved_type'] = gameclass
            if mark_unowned and entry['settings']['map'] in unowned_maps:
                entry['is_unowned_map'] = True
            if mark_unowned and gameclass in unowned_game_types:
                entry['is_unowned_game'] = True

            # Make sure all settings the game defines are present.
            neededsettings = gameclass.get_available_settings(sessiontype)
            for setting in neededsettings:
                if setting.name not in entry['settings']:
                    entry['settings'][setting.name] = setting.default
            goodlist.append(entry)
        except ImportError as exc:
            print(f'Import failed while scanning playlist: {exc}')
        except Exception:
            from ba import _error
            _error.print_exception()
    return goodlist


def get_default_free_for_all_playlist() -> PlaylistType:
    """Return a default playlist for free-for-all mode."""

    # NOTE: these are currently using old type/map names,
    # but filtering translates them properly to the new ones.
    # (is kinda a handy way to ensure filtering is working).
    # Eventually should update these though.
    return [{
        'settings': {
            'Epic Mode': False,
            'Kills to Win Per Player': 10,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Doom Shroom'
        },
        'type': 'bs_death_match.DeathMatchGame'
    }, {
        'settings': {
            'Chosen One Gets Gloves': True,
            'Chosen One Gets Shield': False,
            'Chosen One Time': 30,
            'Epic Mode': 0,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Monkey Face'
        },
        'type': 'bs_chosen_one.ChosenOneGame'
    }, {
        'settings': {
            'Hold Time': 30,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Zigzag'
        },
        'type': 'bs_king_of_the_hill.KingOfTheHillGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'map': 'Rampage'
        },
        'type': 'bs_meteor_shower.MeteorShowerGame'
    }, {
        'settings': {
            'Epic Mode': 1,
            'Lives Per Player': 1,
            'Respawn Times': 1.0,
            'Time Limit': 120,
            'map': 'Tip Top'
        },
        'type': 'bs_elimination.EliminationGame'
    }, {
        'settings': {
            'Hold Time': 30,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'The Pad'
        },
        'type': 'bs_keep_away.KeepAwayGame'
    }, {
        'settings': {
            'Epic Mode': True,
            'Kills to Win Per Player': 10,
            'Respawn Times': 0.25,
            'Time Limit': 120,
            'map': 'Rampage'
        },
        'type': 'bs_death_match.DeathMatchGame'
    }, {
        'settings': {
            'Bomb Spawning': 1000,
            'Epic Mode': False,
            'Laps': 3,
            'Mine Spawn Interval': 4000,
            'Mine Spawning': 4000,
            'Time Limit': 300,
            'map': 'Big G'
        },
        'type': 'bs_race.RaceGame'
    }, {
        'settings': {
            'Hold Time': 30,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Happy Thoughts'
        },
        'type': 'bs_king_of_the_hill.KingOfTheHillGame'
    }, {
        'settings': {
            'Enable Impact Bombs': 1,
            'Enable Triple Bombs': False,
            'Target Count': 2,
            'map': 'Doom Shroom'
        },
        'type': 'bs_target_practice.TargetPracticeGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Lives Per Player': 5,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Step Right Up'
        },
        'type': 'bs_elimination.EliminationGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Kills to Win Per Player': 10,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Crag Castle'
        },
        'type': 'bs_death_match.DeathMatchGame'
    }, {
        'map': 'Lake Frigid',
        'settings': {
            'Bomb Spawning': 0,
            'Epic Mode': False,
            'Laps': 6,
            'Mine Spawning': 2000,
            'Time Limit': 300,
            'map': 'Lake Frigid'
        },
        'type': 'bs_race.RaceGame'
    }]


def get_default_teams_playlist() -> PlaylistType:
    """Return a default playlist for teams mode."""

    # NOTE: these are currently using old type/map names,
    # but filtering translates them properly to the new ones.
    # (is kinda a handy way to ensure filtering is working).
    # Eventually should update these though.
    return [{
        'settings': {
            'Epic Mode': False,
            'Flag Idle Return Time': 30,
            'Flag Touch Return Time': 0,
            'Respawn Times': 1.0,
            'Score to Win': 3,
            'Time Limit': 600,
            'map': 'Bridgit'
        },
        'type': 'bs_capture_the_flag.CTFGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Respawn Times': 1.0,
            'Score to Win': 3,
            'Time Limit': 600,
            'map': 'Step Right Up'
        },
        'type': 'bs_assault.AssaultGame'
    }, {
        'settings': {
            'Balance Total Lives': False,
            'Epic Mode': False,
            'Lives Per Player': 3,
            'Respawn Times': 1.0,
            'Solo Mode': True,
            'Time Limit': 600,
            'map': 'Rampage'
        },
        'type': 'bs_elimination.EliminationGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Kills to Win Per Player': 5,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Roundabout'
        },
        'type': 'bs_death_match.DeathMatchGame'
    }, {
        'settings': {
            'Respawn Times': 1.0,
            'Score to Win': 1,
            'Time Limit': 600,
            'map': 'Hockey Stadium'
        },
        'type': 'bs_hockey.HockeyGame'
    }, {
        'settings': {
            'Hold Time': 30,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Monkey Face'
        },
        'type': 'bs_keep_away.KeepAwayGame'
    }, {
        'settings': {
            'Balance Total Lives': False,
            'Epic Mode': True,
            'Lives Per Player': 1,
            'Respawn Times': 1.0,
            'Solo Mode': False,
            'Time Limit': 120,
            'map': 'Tip Top'
        },
        'type': 'bs_elimination.EliminationGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Respawn Times': 1.0,
            'Score to Win': 3,
            'Time Limit': 300,
            'map': 'Crag Castle'
        },
        'type': 'bs_assault.AssaultGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Kills to Win Per Player': 5,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Doom Shroom'
        },
        'type': 'bs_death_match.DeathMatchGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'map': 'Rampage'
        },
        'type': 'bs_meteor_shower.MeteorShowerGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Flag Idle Return Time': 30,
            'Flag Touch Return Time': 0,
            'Respawn Times': 1.0,
            'Score to Win': 2,
            'Time Limit': 600,
            'map': 'Roundabout'
        },
        'type': 'bs_capture_the_flag.CTFGame'
    }, {
        'settings': {
            'Respawn Times': 1.0,
            'Score to Win': 21,
            'Time Limit': 600,
            'map': 'Football Stadium'
        },
        'type': 'bs_football.FootballTeamGame'
    }, {
        'settings': {
            'Epic Mode': True,
            'Respawn Times': 0.25,
            'Score to Win': 3,
            'Time Limit': 120,
            'map': 'Bridgit'
        },
        'type': 'bs_assault.AssaultGame'
    }, {
        'map': 'Doom Shroom',
        'settings': {
            'Enable Impact Bombs': 1,
            'Enable Triple Bombs': False,
            'Target Count': 2,
            'map': 'Doom Shroom'
        },
        'type': 'bs_target_practice.TargetPracticeGame'
    }, {
        'settings': {
            'Hold Time': 30,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Tip Top'
        },
        'type': 'bs_king_of_the_hill.KingOfTheHillGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Respawn Times': 1.0,
            'Score to Win': 2,
            'Time Limit': 300,
            'map': 'Zigzag'
        },
        'type': 'bs_assault.AssaultGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Flag Idle Return Time': 30,
            'Flag Touch Return Time': 0,
            'Respawn Times': 1.0,
            'Score to Win': 3,
            'Time Limit': 300,
            'map': 'Happy Thoughts'
        },
        'type': 'bs_capture_the_flag.CTFGame'
    }, {
        'settings': {
            'Bomb Spawning': 1000,
            'Epic Mode': True,
            'Laps': 1,
            'Mine Spawning': 2000,
            'Time Limit': 300,
            'map': 'Big G'
        },
        'type': 'bs_race.RaceGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Kills to Win Per Player': 5,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Monkey Face'
        },
        'type': 'bs_death_match.DeathMatchGame'
    }, {
        'settings': {
            'Hold Time': 30,
            'Respawn Times': 1.0,
            'Time Limit': 300,
            'map': 'Lake Frigid'
        },
        'type': 'bs_keep_away.KeepAwayGame'
    }, {
        'settings': {
            'Epic Mode': False,
            'Flag Idle Return Time': 30,
            'Flag Touch Return Time': 3,
            'Respawn Times': 1.0,
            'Score to Win': 2,
            'Time Limit': 300,
            'map': 'Tip Top'
        },
        'type': 'bs_capture_the_flag.CTFGame'
    }, {
        'settings': {
            'Balance Total Lives': False,
            'Epic Mode': False,
            'Lives Per Player': 3,
            'Respawn Times': 1.0,
            'Solo Mode': False,
            'Time Limit': 300,
            'map': 'Crag Castle'
        },
        'type': 'bs_elimination.EliminationGame'
    }, {
        'settings': {
            'Epic Mode': True,
            'Respawn Times': 0.25,
            'Time Limit': 120,
            'map': 'Zigzag'
        },
        'type': 'bs_conquest.ConquestGame'
    }]
