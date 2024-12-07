# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to individual levels in a campaign."""
from __future__ import annotations

import copy
import weakref
from typing import TYPE_CHECKING, override

import babase

if TYPE_CHECKING:
    from typing import Any

    import bascenev1


class Level:
    """An entry in a bascenev1.Campaign.

    Category: **Gameplay Classes**
    """

    def __init__(
        self,
        name: str,
        gametype: type[bascenev1.GameActivity],
        settings: dict,
        preview_texture_name: str,
        *,
        displayname: str | None = None,
    ):
        self._name = name
        self._gametype = gametype
        self._settings = settings
        self._preview_texture_name = preview_texture_name
        self._displayname = displayname
        self._campaign: weakref.ref[bascenev1.Campaign] | None = None
        self._index: int | None = None
        self._score_version_string: str | None = None

    @override
    def __repr__(self) -> str:
        cls = type(self)
        return f"<{cls.__module__}.{cls.__name__} '{self._name}'>"

    @property
    def name(self) -> str:
        """The unique name for this Level."""
        return self._name

    def get_settings(self) -> dict[str, Any]:
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

    # def get_preview_texture(self) -> bauiv1.Texture:
    #     """Load/return the preview Texture for this Level."""
    #     return _bauiv1.gettexture(self._preview_texture_name)

    @property
    def displayname(self) -> bascenev1.Lstr:
        """The localized name for this Level."""
        return babase.Lstr(
            translate=(
                'coopLevelNames',
                (
                    self._displayname
                    if self._displayname is not None
                    else self._name
                ),
            ),
            subs=[
                ('${GAME}', self._gametype.get_display_string(self._settings))
            ],
        )

    @property
    def gametype(self) -> type[bascenev1.GameActivity]:
        """The type of game used for this Level."""
        return self._gametype

    @property
    def campaign(self) -> bascenev1.Campaign | None:
        """The baclassic.Campaign this Level is associated with, or None."""
        return None if self._campaign is None else self._campaign()

    @property
    def index(self) -> int:
        """The zero-based index of this Level in its baclassic.Campaign.

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
        val = config.get('Complete', False)
        assert isinstance(val, bool)
        return val

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

    def set_high_scores(self, high_scores: dict) -> None:
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
        val = self._get_config_dict().get('Rating', 0.0)
        assert isinstance(val, float)
        return val

    def set_rating(self, rating: float) -> None:
        """Set a rating for this Level, replacing the old ONLY IF higher."""
        old_rating = self.rating
        config = self._get_config_dict()
        config['Rating'] = max(old_rating, rating)

    def _get_config_dict(self) -> dict[str, Any]:
        """Return/create the persistent state dict for this level.

        The referenced dict exists under the game's config dict and
        can be modified in place."""
        campaign = self.campaign
        if campaign is None:
            raise RuntimeError('Level is not in a campaign.')
        configdict = campaign.configdict
        val: dict[str, Any] = configdict.setdefault(
            self._name, {'Rating': 0.0, 'Complete': False}
        )
        assert isinstance(val, dict)
        return val

    def set_campaign(self, campaign: bascenev1.Campaign, index: int) -> None:
        """For use by baclassic.Campaign when adding levels to itself.

        (internal)"""
        self._campaign = weakref.ref(campaign)
        self._index = index
