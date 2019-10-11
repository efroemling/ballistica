# Copyright (c) 2011-2019 Eric Froemling
"""Functionality related to co-op campaigns."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any, List, Dict
    import ba


def register_campaign(campaign: ba.Campaign) -> None:
    """Register a new campaign."""
    _ba.app.campaigns[campaign.name] = campaign


def get_campaign(name: str) -> ba.Campaign:
    """Return a campaign by name."""
    return _ba.app.campaigns[name]


class Campaign:
    """Represents a unique set or series of ba.Levels."""

    def __init__(self, name: str, sequential: bool = True):
        self._name = name
        self._levels: List[ba.Level] = []
        self._sequential = sequential

    @property
    def name(self) -> str:
        """The name of the Campaign."""
        return self._name

    @property
    def sequential(self) -> bool:
        """Whether this Campaign's levels must be played in sequence."""
        return self._sequential

    def add_level(self, level: ba.Level) -> None:
        """Adds a ba.Level to the Campaign."""
        if level.get_campaign() is not None:
            raise Exception("level already belongs to a campaign")
        level.set_campaign(self, len(self._levels))
        self._levels.append(level)

    def get_levels(self) -> List[ba.Level]:
        """Return the set of ba.Levels in the Campaign."""
        return self._levels

    def get_level(self, name: str) -> ba.Level:
        """Return a contained ba.Level by name."""
        for level in self._levels:
            if level.name == name:
                return level
        raise Exception("Level '" + name + "' not found in campaign '" +
                        self.name + "'")

    def reset(self) -> None:
        """Reset state for the Campaign."""
        _ba.app.config.setdefault('Campaigns', {})[self._name] = {}

    # FIXME should these give/take ba.Level instances instead of level names?..
    def set_selected_level(self, levelname: str) -> None:
        """Set the Level currently selected in the UI (by name)."""
        self.get_config_dict()['Selection'] = levelname
        _ba.app.config.commit()

    def get_selected_level(self) -> str:
        """Return the name of the Level currently selected in the UI."""
        return self.get_config_dict().get('Selection', self._levels[0].name)

    def get_config_dict(self) -> Dict[str, Any]:
        """Return the live config dict for this campaign."""
        val: Dict[str, Any] = (_ba.app.config.setdefault('Campaigns',
                                                         {}).setdefault(
                                                             self._name, {}))
        assert isinstance(val, dict)
        return val


def init_campaigns() -> None:
    """Fill out initial default Campaigns."""
    # pylint: disable=too-many-statements
    # pylint: disable=cyclic-import
    from ba import _level
    from bastd.game.onslaught import OnslaughtGame
    from bastd.game.football import FootballCoopGame
    from bastd.game.runaround import RunaroundGame
    from bastd.game.thelaststand import TheLastStandGame
    from bastd.game.race import RaceGame
    from bastd.game.targetpractice import TargetPracticeGame
    from bastd.game.meteorshower import MeteorShowerGame
    from bastd.game.easteregghunt import EasterEggHuntGame
    from bastd.game.ninjafight import NinjaFightGame

    # FIXME: Once translations catch up, we can convert these to use the
    #  generic display-name '${GAME} Training' type stuff.
    campaign = Campaign('Easy')
    campaign.add_level(
        _level.Level('Onslaught Training',
                     gametype=OnslaughtGame,
                     settings={'preset': 'training_easy'},
                     preview_texture_name='doomShroomPreview'))
    campaign.add_level(
        _level.Level('Rookie Onslaught',
                     gametype=OnslaughtGame,
                     settings={'preset': 'rookie_easy'},
                     preview_texture_name='courtyardPreview'))
    campaign.add_level(
        _level.Level('Rookie Football',
                     gametype=FootballCoopGame,
                     settings={'preset': 'rookie_easy'},
                     preview_texture_name='footballStadiumPreview'))
    campaign.add_level(
        _level.Level('Pro Onslaught',
                     gametype=OnslaughtGame,
                     settings={'preset': 'pro_easy'},
                     preview_texture_name='doomShroomPreview'))
    campaign.add_level(
        _level.Level('Pro Football',
                     gametype=FootballCoopGame,
                     settings={'preset': 'pro_easy'},
                     preview_texture_name='footballStadiumPreview'))
    campaign.add_level(
        _level.Level('Pro Runaround',
                     gametype=RunaroundGame,
                     settings={'preset': 'pro_easy'},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level('Uber Onslaught',
                     gametype=OnslaughtGame,
                     settings={'preset': 'uber_easy'},
                     preview_texture_name='courtyardPreview'))
    campaign.add_level(
        _level.Level('Uber Football',
                     gametype=FootballCoopGame,
                     settings={'preset': 'uber_easy'},
                     preview_texture_name='footballStadiumPreview'))
    campaign.add_level(
        _level.Level('Uber Runaround',
                     gametype=RunaroundGame,
                     settings={'preset': 'uber_easy'},
                     preview_texture_name='towerDPreview'))
    register_campaign(campaign)

    # "hard" mode
    campaign = Campaign('Default')
    campaign.add_level(
        _level.Level('Onslaught Training',
                     gametype=OnslaughtGame,
                     settings={'preset': 'training'},
                     preview_texture_name='doomShroomPreview'))
    campaign.add_level(
        _level.Level('Rookie Onslaught',
                     gametype=OnslaughtGame,
                     settings={'preset': 'rookie'},
                     preview_texture_name='courtyardPreview'))
    campaign.add_level(
        _level.Level('Rookie Football',
                     gametype=FootballCoopGame,
                     settings={'preset': 'rookie'},
                     preview_texture_name='footballStadiumPreview'))
    campaign.add_level(
        _level.Level('Pro Onslaught',
                     gametype=OnslaughtGame,
                     settings={'preset': 'pro'},
                     preview_texture_name='doomShroomPreview'))
    campaign.add_level(
        _level.Level('Pro Football',
                     gametype=FootballCoopGame,
                     settings={'preset': 'pro'},
                     preview_texture_name='footballStadiumPreview'))
    campaign.add_level(
        _level.Level('Pro Runaround',
                     gametype=RunaroundGame,
                     settings={'preset': 'pro'},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level('Uber Onslaught',
                     gametype=OnslaughtGame,
                     settings={'preset': 'uber'},
                     preview_texture_name='courtyardPreview'))
    campaign.add_level(
        _level.Level('Uber Football',
                     gametype=FootballCoopGame,
                     settings={'preset': 'uber'},
                     preview_texture_name='footballStadiumPreview'))
    campaign.add_level(
        _level.Level('Uber Runaround',
                     gametype=RunaroundGame,
                     settings={'preset': 'uber'},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level('The Last Stand',
                     gametype=TheLastStandGame,
                     settings={},
                     preview_texture_name='rampagePreview'))
    register_campaign(campaign)

    # challenges: our 'official' random extra co-op levels
    campaign = Campaign('Challenges', sequential=False)
    campaign.add_level(
        _level.Level('Infinite Onslaught',
                     gametype=OnslaughtGame,
                     settings={'preset': 'endless'},
                     preview_texture_name='doomShroomPreview'))
    campaign.add_level(
        _level.Level('Infinite Runaround',
                     gametype=RunaroundGame,
                     settings={'preset': 'endless'},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level('Race',
                     displayname='${GAME}',
                     gametype=RaceGame,
                     settings={
                         'map': 'Big G',
                         'Laps': 3,
                         'Bomb Spawning': 0
                     },
                     preview_texture_name='bigGPreview'))
    campaign.add_level(
        _level.Level('Pro Race',
                     displayname='Pro ${GAME}',
                     gametype=RaceGame,
                     settings={
                         'map': 'Big G',
                         'Laps': 3,
                         'Bomb Spawning': 1000
                     },
                     preview_texture_name='bigGPreview'))
    campaign.add_level(
        _level.Level('Lake Frigid Race',
                     displayname='${GAME}',
                     gametype=RaceGame,
                     settings={
                         'map': 'Lake Frigid',
                         'Laps': 6,
                         'Mine Spawning': 2000,
                         'Bomb Spawning': 0
                     },
                     preview_texture_name='lakeFrigidPreview'))
    campaign.add_level(
        _level.Level('Football',
                     displayname='${GAME}',
                     gametype=FootballCoopGame,
                     settings={'preset': 'tournament'},
                     preview_texture_name='footballStadiumPreview'))
    campaign.add_level(
        _level.Level('Pro Football',
                     displayname='Pro ${GAME}',
                     gametype=FootballCoopGame,
                     settings={'preset': 'tournament_pro'},
                     preview_texture_name='footballStadiumPreview'))
    campaign.add_level(
        _level.Level('Runaround',
                     displayname='${GAME}',
                     gametype=RunaroundGame,
                     settings={'preset': 'tournament'},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level('Uber Runaround',
                     displayname='Uber ${GAME}',
                     gametype=RunaroundGame,
                     settings={'preset': 'tournament_uber'},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level('The Last Stand',
                     displayname='${GAME}',
                     gametype=TheLastStandGame,
                     settings={'preset': 'tournament'},
                     preview_texture_name='rampagePreview'))
    campaign.add_level(
        _level.Level('Tournament Infinite Onslaught',
                     displayname='Infinite Onslaught',
                     gametype=OnslaughtGame,
                     settings={'preset': 'endless_tournament'},
                     preview_texture_name='doomShroomPreview'))
    campaign.add_level(
        _level.Level('Tournament Infinite Runaround',
                     displayname='Infinite Runaround',
                     gametype=RunaroundGame,
                     settings={'preset': 'endless_tournament'},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level('Target Practice',
                     displayname='Pro ${GAME}',
                     gametype=TargetPracticeGame,
                     settings={},
                     preview_texture_name='doomShroomPreview'))
    campaign.add_level(
        _level.Level('Target Practice B',
                     displayname='${GAME}',
                     gametype=TargetPracticeGame,
                     settings={
                         'Target Count': 2,
                         'Enable Impact Bombs': False,
                         'Enable Triple Bombs': False
                     },
                     preview_texture_name='doomShroomPreview'))
    campaign.add_level(
        _level.Level('Meteor Shower',
                     displayname='${GAME}',
                     gametype=MeteorShowerGame,
                     settings={},
                     preview_texture_name='rampagePreview'))
    campaign.add_level(
        _level.Level('Epic Meteor Shower',
                     displayname='${GAME}',
                     gametype=MeteorShowerGame,
                     settings={'Epic Mode': True},
                     preview_texture_name='rampagePreview'))
    campaign.add_level(
        _level.Level('Easter Egg Hunt',
                     displayname='${GAME}',
                     gametype=EasterEggHuntGame,
                     settings={},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level('Pro Easter Egg Hunt',
                     displayname='Pro ${GAME}',
                     gametype=EasterEggHuntGame,
                     settings={'Pro Mode': True},
                     preview_texture_name='towerDPreview'))
    campaign.add_level(
        _level.Level(
            name='Ninja Fight',  # (unique id not seen by player)
            displayname='${GAME}',  # (readable name seen by player)
            gametype=NinjaFightGame,
            settings={'preset': 'regular'},
            preview_texture_name='courtyardPreview'))
    campaign.add_level(
        _level.Level(name='Pro Ninja Fight',
                     displayname='Pro ${GAME}',
                     gametype=NinjaFightGame,
                     settings={'preset': 'pro'},
                     preview_texture_name='courtyardPreview'))
    register_campaign(campaign)
