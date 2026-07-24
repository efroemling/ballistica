# Released under the MIT License. See LICENSE for details.
#
"""Asset-package string accessors for the built-in achievements.

Binds each built-in achievement's name to its authored strings in
``baclassicassets``. Kept as functions rather than module-level tables
because achievements are registered during app-loading, before
construct-mode has resolved asset-packages -- so the wrapper must not be
touched until a lookup actually happens (mirrors
``bascenev1lib.actor.spazappearance._character_name_table``).

Names and full descriptions take the campaign level as a ``{level}``
parameter, so the accessors are callables taking that; the five
achievements with no associated level ignore it. Achievements absent
from these tables -- a mod's -- have no authored strings.
"""

from typing import TYPE_CHECKING

from bascenev1 import classicassets

if TYPE_CHECKING:
    from collections.abc import Callable

    import babase

    #: A string parameterized by the campaign level's display name.
    type _LevelStr = Callable[[babase.LangStr], babase.LangStr]


def name_table() -> 'dict[str, _LevelStr]':
    """Achievement name -> its display name, given the level's name."""
    a = classicassets.strings.achievements
    return {
        'Boom Goes the Dynamite': lambda v: (a.boom_goes_the_dynamite.name),
        'Boxer': lambda v: (a.boxer.name),
        'Dual Wielding': lambda v: (a.dual_wielding.name),
        'Flawless Victory': lambda v: (a.flawless_victory.name),
        'Free Loader': lambda v: (a.free_loader.name),
        'Gold Miner': lambda v: (a.gold_miner.name),
        'Got the Moves': lambda v: (a.got_the_moves.name),
        'In Control': lambda v: (a.in_control.name),
        'Last Stand God': lambda v: (a.last_stand_god.name(level=v)),
        'Last Stand Master': lambda v: (a.last_stand_master.name(level=v)),
        'Last Stand Wizard': lambda v: (a.last_stand_wizard.name(level=v)),
        'Mine Games': lambda v: (a.mine_games.name),
        'Off You Go Then': lambda v: (a.off_you_go_then.name),
        'Onslaught God': lambda v: (a.onslaught_god.name(level=v)),
        'Onslaught Master': lambda v: (a.onslaught_master.name(level=v)),
        'Onslaught Training Victory': lambda v: (
            a.onslaught_training_victory.name(level=v)
        ),
        'Onslaught Wizard': lambda v: (a.onslaught_wizard.name(level=v)),
        'Precision Bombing': lambda v: (a.precision_bombing.name),
        'Pro Boxer': lambda v: (a.pro_boxer.name),
        'Pro Football Shutout': lambda v: (
            a.pro_football_shutout.name(level=v)
        ),
        'Pro Football Victory': lambda v: (
            a.pro_football_victory.name(level=v)
        ),
        'Pro Onslaught Victory': lambda v: (
            a.pro_onslaught_victory.name(level=v)
        ),
        'Pro Runaround Victory': lambda v: (
            a.pro_runaround_victory.name(level=v)
        ),
        'Rookie Football Shutout': lambda v: (
            a.rookie_football_shutout.name(level=v)
        ),
        'Rookie Football Victory': lambda v: (
            a.rookie_football_victory.name(level=v)
        ),
        'Rookie Onslaught Victory': lambda v: (
            a.rookie_onslaught_victory.name(level=v)
        ),
        'Runaround God': lambda v: (a.runaround_god.name(level=v)),
        'Runaround Master': lambda v: (a.runaround_master.name(level=v)),
        'Runaround Wizard': lambda v: (a.runaround_wizard.name(level=v)),
        'Sharing is Caring': lambda v: (a.sharing_is_caring.name),
        'Stayin\' Alive': lambda v: (a.stayin_alive.name),
        'Super Mega Punch': lambda v: (a.super_mega_punch.name),
        'Super Punch': lambda v: (a.super_punch.name),
        'TNT Terror': lambda v: (a.tnt_terror.name),
        'Team Player': lambda v: (a.team_player.name),
        'The Great Wall': lambda v: (a.the_great_wall.name),
        'The Wall': lambda v: (a.the_wall.name),
        'Uber Football Shutout': lambda v: (
            a.uber_football_shutout.name(level=v)
        ),
        'Uber Football Victory': lambda v: (
            a.uber_football_victory.name(level=v)
        ),
        'Uber Onslaught Victory': lambda v: (
            a.uber_onslaught_victory.name(level=v)
        ),
        'Uber Runaround Victory': lambda v: (
            a.uber_runaround_victory.name(level=v)
        ),
    }


def short_description_table() -> (
    'dict[str, tuple[babase.LangStr, babase.LangStr]]'
):
    """Achievement name -> its (unearned, earned) short descriptions.

    Only the achievements tied to a campaign level have these; the rest
    show their full description in both spots.
    """
    a = classicassets.strings.achievements
    return {
        'Boom Goes the Dynamite': (
            a.boom_goes_the_dynamite.description,
            a.boom_goes_the_dynamite.description_complete,
        ),
        'Boxer': (
            a.boxer.description,
            a.boxer.description_complete,
        ),
        'Flawless Victory': (
            a.flawless_victory.description,
            a.flawless_victory.description_complete,
        ),
        'Gold Miner': (
            a.gold_miner.description,
            a.gold_miner.description_complete,
        ),
        'Got the Moves': (
            a.got_the_moves.description,
            a.got_the_moves.description_complete,
        ),
        'Last Stand God': (
            a.last_stand_god.description,
            a.last_stand_god.description_complete,
        ),
        'Last Stand Master': (
            a.last_stand_master.description,
            a.last_stand_master.description_complete,
        ),
        'Last Stand Wizard': (
            a.last_stand_wizard.description,
            a.last_stand_wizard.description_complete,
        ),
        'Mine Games': (
            a.mine_games.description,
            a.mine_games.description_complete,
        ),
        'Off You Go Then': (
            a.off_you_go_then.description,
            a.off_you_go_then.description_complete,
        ),
        'Onslaught God': (
            a.onslaught_god.description,
            a.onslaught_god.description_complete,
        ),
        'Onslaught Master': (
            a.onslaught_master.description,
            a.onslaught_master.description_complete,
        ),
        'Onslaught Training Victory': (
            a.onslaught_training_victory.description,
            a.onslaught_training_victory.description_complete,
        ),
        'Onslaught Wizard': (
            a.onslaught_wizard.description,
            a.onslaught_wizard.description_complete,
        ),
        'Precision Bombing': (
            a.precision_bombing.description,
            a.precision_bombing.description_complete,
        ),
        'Pro Boxer': (
            a.pro_boxer.description,
            a.pro_boxer.description_complete,
        ),
        'Pro Football Shutout': (
            a.pro_football_shutout.description,
            a.pro_football_shutout.description_complete,
        ),
        'Pro Football Victory': (
            a.pro_football_victory.description,
            a.pro_football_victory.description_complete,
        ),
        'Pro Onslaught Victory': (
            a.pro_onslaught_victory.description,
            a.pro_onslaught_victory.description_complete,
        ),
        'Pro Runaround Victory': (
            a.pro_runaround_victory.description,
            a.pro_runaround_victory.description_complete,
        ),
        'Rookie Football Shutout': (
            a.rookie_football_shutout.description,
            a.rookie_football_shutout.description_complete,
        ),
        'Rookie Football Victory': (
            a.rookie_football_victory.description,
            a.rookie_football_victory.description_complete,
        ),
        'Rookie Onslaught Victory': (
            a.rookie_onslaught_victory.description,
            a.rookie_onslaught_victory.description_complete,
        ),
        'Runaround God': (
            a.runaround_god.description,
            a.runaround_god.description_complete,
        ),
        'Runaround Master': (
            a.runaround_master.description,
            a.runaround_master.description_complete,
        ),
        'Runaround Wizard': (
            a.runaround_wizard.description,
            a.runaround_wizard.description_complete,
        ),
        'Stayin\' Alive': (
            a.stayin_alive.description,
            a.stayin_alive.description_complete,
        ),
        'Super Mega Punch': (
            a.super_mega_punch.description,
            a.super_mega_punch.description_complete,
        ),
        'Super Punch': (
            a.super_punch.description,
            a.super_punch.description_complete,
        ),
        'TNT Terror': (
            a.tnt_terror.description,
            a.tnt_terror.description_complete,
        ),
        'The Great Wall': (
            a.the_great_wall.description,
            a.the_great_wall.description_complete,
        ),
        'The Wall': (
            a.the_wall.description,
            a.the_wall.description_complete,
        ),
        'Uber Football Shutout': (
            a.uber_football_shutout.description,
            a.uber_football_shutout.description_complete,
        ),
        'Uber Football Victory': (
            a.uber_football_victory.description,
            a.uber_football_victory.description_complete,
        ),
        'Uber Onslaught Victory': (
            a.uber_onslaught_victory.description,
            a.uber_onslaught_victory.description_complete,
        ),
        'Uber Runaround Victory': (
            a.uber_runaround_victory.description,
            a.uber_runaround_victory.description_complete,
        ),
    }


def full_description_table() -> 'dict[str, tuple[_LevelStr, _LevelStr]]':
    """Achievement name -> its (unearned, earned) full descriptions."""
    a = classicassets.strings.achievements
    return {
        'Boom Goes the Dynamite': (
            lambda v: (a.boom_goes_the_dynamite.description_full(level=v)),
            lambda v: (
                a.boom_goes_the_dynamite.description_full_complete(level=v)
            ),
        ),
        'Boxer': (
            lambda v: (a.boxer.description_full(level=v)),
            lambda v: (a.boxer.description_full_complete(level=v)),
        ),
        'Dual Wielding': (
            lambda v: (a.dual_wielding.description_full),
            lambda v: (a.dual_wielding.description_full_complete),
        ),
        'Flawless Victory': (
            lambda v: (a.flawless_victory.description_full(level=v)),
            lambda v: (a.flawless_victory.description_full_complete(level=v)),
        ),
        'Free Loader': (
            lambda v: (a.free_loader.description_full),
            lambda v: (a.free_loader.description_full_complete),
        ),
        'Gold Miner': (
            lambda v: (a.gold_miner.description_full(level=v)),
            lambda v: (a.gold_miner.description_full_complete(level=v)),
        ),
        'Got the Moves': (
            lambda v: (a.got_the_moves.description_full(level=v)),
            lambda v: (a.got_the_moves.description_full_complete(level=v)),
        ),
        'In Control': (
            lambda v: (a.in_control.description_full),
            lambda v: (a.in_control.description_full_complete),
        ),
        'Last Stand God': (
            lambda v: (a.last_stand_god.description_full(level=v)),
            lambda v: (a.last_stand_god.description_full_complete(level=v)),
        ),
        'Last Stand Master': (
            lambda v: (a.last_stand_master.description_full(level=v)),
            lambda v: (a.last_stand_master.description_full_complete(level=v)),
        ),
        'Last Stand Wizard': (
            lambda v: (a.last_stand_wizard.description_full(level=v)),
            lambda v: (a.last_stand_wizard.description_full_complete(level=v)),
        ),
        'Mine Games': (
            lambda v: (a.mine_games.description_full(level=v)),
            lambda v: (a.mine_games.description_full_complete(level=v)),
        ),
        'Off You Go Then': (
            lambda v: (a.off_you_go_then.description_full(level=v)),
            lambda v: (a.off_you_go_then.description_full_complete(level=v)),
        ),
        'Onslaught God': (
            lambda v: (a.onslaught_god.description_full(level=v)),
            lambda v: (a.onslaught_god.description_full_complete(level=v)),
        ),
        'Onslaught Master': (
            lambda v: (a.onslaught_master.description_full(level=v)),
            lambda v: (a.onslaught_master.description_full_complete(level=v)),
        ),
        'Onslaught Training Victory': (
            lambda v: (a.onslaught_training_victory.description_full(level=v)),
            lambda v: (
                a.onslaught_training_victory.description_full_complete(level=v)
            ),
        ),
        'Onslaught Wizard': (
            lambda v: (a.onslaught_wizard.description_full(level=v)),
            lambda v: (a.onslaught_wizard.description_full_complete(level=v)),
        ),
        'Precision Bombing': (
            lambda v: (a.precision_bombing.description_full(level=v)),
            lambda v: (a.precision_bombing.description_full_complete(level=v)),
        ),
        'Pro Boxer': (
            lambda v: (a.pro_boxer.description_full(level=v)),
            lambda v: (a.pro_boxer.description_full_complete(level=v)),
        ),
        'Pro Football Shutout': (
            lambda v: (a.pro_football_shutout.description_full(level=v)),
            lambda v: (
                a.pro_football_shutout.description_full_complete(level=v)
            ),
        ),
        'Pro Football Victory': (
            lambda v: (a.pro_football_victory.description_full(level=v)),
            lambda v: (
                a.pro_football_victory.description_full_complete(level=v)
            ),
        ),
        'Pro Onslaught Victory': (
            lambda v: (a.pro_onslaught_victory.description_full(level=v)),
            lambda v: (
                a.pro_onslaught_victory.description_full_complete(level=v)
            ),
        ),
        'Pro Runaround Victory': (
            lambda v: (a.pro_runaround_victory.description_full(level=v)),
            lambda v: (
                a.pro_runaround_victory.description_full_complete(level=v)
            ),
        ),
        'Rookie Football Shutout': (
            lambda v: (a.rookie_football_shutout.description_full(level=v)),
            lambda v: (
                a.rookie_football_shutout.description_full_complete(level=v)
            ),
        ),
        'Rookie Football Victory': (
            lambda v: (a.rookie_football_victory.description_full(level=v)),
            lambda v: (
                a.rookie_football_victory.description_full_complete(level=v)
            ),
        ),
        'Rookie Onslaught Victory': (
            lambda v: (a.rookie_onslaught_victory.description_full(level=v)),
            lambda v: (
                a.rookie_onslaught_victory.description_full_complete(level=v)
            ),
        ),
        'Runaround God': (
            lambda v: (a.runaround_god.description_full(level=v)),
            lambda v: (a.runaround_god.description_full_complete(level=v)),
        ),
        'Runaround Master': (
            lambda v: (a.runaround_master.description_full(level=v)),
            lambda v: (a.runaround_master.description_full_complete(level=v)),
        ),
        'Runaround Wizard': (
            lambda v: (a.runaround_wizard.description_full(level=v)),
            lambda v: (a.runaround_wizard.description_full_complete(level=v)),
        ),
        'Sharing is Caring': (
            lambda v: (a.sharing_is_caring.description_full),
            lambda v: (a.sharing_is_caring.description_full_complete),
        ),
        'Stayin\' Alive': (
            lambda v: (a.stayin_alive.description_full(level=v)),
            lambda v: (a.stayin_alive.description_full_complete(level=v)),
        ),
        'Super Mega Punch': (
            lambda v: (a.super_mega_punch.description_full(level=v)),
            lambda v: (a.super_mega_punch.description_full_complete(level=v)),
        ),
        'Super Punch': (
            lambda v: (a.super_punch.description_full(level=v)),
            lambda v: (a.super_punch.description_full_complete(level=v)),
        ),
        'TNT Terror': (
            lambda v: (a.tnt_terror.description_full(level=v)),
            lambda v: (a.tnt_terror.description_full_complete(level=v)),
        ),
        'Team Player': (
            lambda v: (a.team_player.description_full),
            lambda v: (a.team_player.description_full_complete),
        ),
        'The Great Wall': (
            lambda v: (a.the_great_wall.description_full(level=v)),
            lambda v: (a.the_great_wall.description_full_complete(level=v)),
        ),
        'The Wall': (
            lambda v: (a.the_wall.description_full(level=v)),
            lambda v: (a.the_wall.description_full_complete(level=v)),
        ),
        'Uber Football Shutout': (
            lambda v: (a.uber_football_shutout.description_full(level=v)),
            lambda v: (
                a.uber_football_shutout.description_full_complete(level=v)
            ),
        ),
        'Uber Football Victory': (
            lambda v: (a.uber_football_victory.description_full(level=v)),
            lambda v: (
                a.uber_football_victory.description_full_complete(level=v)
            ),
        ),
        'Uber Onslaught Victory': (
            lambda v: (a.uber_onslaught_victory.description_full(level=v)),
            lambda v: (
                a.uber_onslaught_victory.description_full_complete(level=v)
            ),
        ),
        'Uber Runaround Victory': (
            lambda v: (a.uber_runaround_victory.description_full(level=v)),
            lambda v: (
                a.uber_runaround_victory.description_full_complete(level=v)
            ),
        ),
    }


def level_name_table() -> 'dict[str, babase.LangStr]':
    """Campaign level name -> its display name.

    The levels the built-in achievements are earned on; substituted into
    the parameterized names and full descriptions above.
    """
    c = classicassets.strings.cooplevels
    return {
        'Infinite Onslaught': c.infinite_onslaught,
        'Infinite Runaround': c.infinite_runaround,
        'Onslaught Training': c.onslaught_training,
        'Pro Football': c.pro_football,
        'Pro Onslaught': c.pro_onslaught,
        'Pro Runaround': c.pro_runaround,
        'Rookie Football': c.rookie_football,
        'Rookie Onslaught': c.rookie_onslaught,
        'The Last Stand': c.the_last_stand,
        'Uber Football': c.uber_football,
        'Uber Onslaught': c.uber_onslaught,
        'Uber Runaround': c.uber_runaround,
    }
