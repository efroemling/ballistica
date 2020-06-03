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
"""Functionality related to individual levels in a campaign."""
from __future__ import annotations

import copy
import weakref
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import Type, Any, Dict, Optional
    import ba


class Level:
    """An entry in a ba.Campaign consisting of a name, game type, and settings.

    category: Gameplay Classes
    """

    def __init__(self,
                 name: str,
                 gametype: Type[ba.GameActivity],
                 settings: dict,
                 preview_texture_name: str,
                 displayname: str = None):
        self._name = name
        self._gametype = gametype
        self._settings = settings
        self._preview_texture_name = preview_texture_name
        self._displayname = displayname
        self._campaign: Optional[ReferenceType[ba.Campaign]] = None
        self._index: Optional[int] = None
        self._score_version_string: Optional[str] = None

    @property
    def name(self) -> str:
        """The unique name for this Level."""
        return self._name

    def get_settings(self) -> Dict[str, Any]:
        """Returns the settings for this Level."""
        settings = copy.deepcopy(self._settings)

        # So the game knows what the level is called.
        # Hmm; seems hacky; I think we should take this out.
        settings['name'] = self._name
        return settings

    @property
    def preview_texture_name(self) -> str:
        """The preview texture name for this Level."""
        return self._preview_texture_name

    def get_preview_texture(self) -> ba.Texture:
        """Load/return the preview Texture for this Level."""
        return _ba.gettexture(self._preview_texture_name)

    @property
    def displayname(self) -> ba.Lstr:
        """The localized name for this Level."""
        from ba import _lang
        return _lang.Lstr(
            translate=('coopLevelNames', self._displayname
                       if self._displayname is not None else self._name),
            subs=[('${GAME}',
                   self._gametype.get_display_string(self._settings))])

    @property
    def gametype(self) -> Type[ba.GameActivity]:
        """The type of game used for this Level."""
        return self._gametype

    @property
    def campaign(self) -> Optional[ba.Campaign]:
        """The ba.Campaign this Level is associated with, or None."""
        return None if self._campaign is None else self._campaign()

    @property
    def index(self) -> int:
        """The zero-based index of this Level in its ba.Campaign.

        Access results in a RuntimeError if the Level is  not assigned to a
        Campaign.
        """
        if self._index is None:
            raise RuntimeError('Level is not part of a Campaign')
        return self._index

    @property
    def complete(self) -> bool:
        """Whether this Level has been completed."""
        config = self._get_config_dict()
        return config.get('Complete', False)

    def set_complete(self, val: bool) -> None:
        """Set whether or not this level is complete."""
        old_val = self.complete
        assert isinstance(old_val, bool)
        assert isinstance(val, bool)
        if val != old_val:
            config = self._get_config_dict()
            config['Complete'] = val

    def get_high_scores(self) -> dict:
        """Return the current high scores for this Level."""
        config = self._get_config_dict()
        high_scores_key = 'High Scores' + self.get_score_version_string()
        if high_scores_key not in config:
            return {}
        return copy.deepcopy(config[high_scores_key])

    def set_high_scores(self, high_scores: Dict) -> None:
        """Set high scores for this level."""
        config = self._get_config_dict()
        high_scores_key = 'High Scores' + self.get_score_version_string()
        config[high_scores_key] = high_scores

    def get_score_version_string(self) -> str:
        """Return the score version string for this Level.

        If a Level's gameplay changes significantly, its version string
        can be changed to separate its new high score lists/etc. from the old.
        """
        if self._score_version_string is None:
            scorever = self._gametype.getscoreconfig().version
            if scorever != '':
                scorever = ' ' + scorever
            self._score_version_string = scorever
        assert self._score_version_string is not None
        return self._score_version_string

    @property
    def rating(self) -> float:
        """The current rating for this Level."""
        return self._get_config_dict().get('Rating', 0.0)

    def set_rating(self, rating: float) -> None:
        """Set a rating for this Level, replacing the old ONLY IF higher."""
        old_rating = self.rating
        config = self._get_config_dict()
        config['Rating'] = max(old_rating, rating)

    def _get_config_dict(self) -> Dict[str, Any]:
        """Return/create the persistent state dict for this level.

        The referenced dict exists under the game's config dict and
        can be modified in place."""
        campaign = self.campaign
        if campaign is None:
            raise RuntimeError('Level is not in a campaign.')
        configdict = campaign.configdict
        val: Dict[str, Any] = configdict.setdefault(self._name, {
            'Rating': 0.0,
            'Complete': False
        })
        assert isinstance(val, dict)
        return val

    def set_campaign(self, campaign: ba.Campaign, index: int) -> None:
        """For use by ba.Campaign when adding levels to itself.

        (internal)"""
        self._campaign = weakref.ref(campaign)
        self._index = index
