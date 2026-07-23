# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to individual levels in a campaign."""

import copy
import weakref
from typing import TYPE_CHECKING, override

import babase

if TYPE_CHECKING:
    from typing import Any

    import bascenev1


def _get_level_display_name(key: str, game: babase.LangStr) -> babase.LangStr:
    """Return a displayable name for a campaign level.

    ``key`` is the level's displayname, or its name when it declares
    none. A bare ``${GAME}`` is simply the game's own name; the
    difficulty-prefixed forms are parameterized entries. Anything else
    -- a mod's campaign level -- shows its own text, with any
    ``${GAME}`` token substituted in flat.
    """
    # Safe up-call: bascenev1 is fully imported by the time this runs;
    # the cycle pylint sees is structural only.
    # pylint: disable-next=cyclic-import
    from bascenev1 import classicassets

    if key == '${GAME}':
        return game

    s = classicassets.strings.cooplevels
    if key == 'Pro ${GAME}':
        return s.pro_variant(game=game)
    if key == 'Uber ${GAME}':
        return s.uber_variant(game=game)

    entry = {
        'Infinite Onslaught': s.infinite_onslaught,
        'Infinite Runaround': s.infinite_runaround,
        'Onslaught Training': s.onslaught_training,
        'Pro Football': s.pro_football,
        'Pro Onslaught': s.pro_onslaught,
        'Pro Runaround': s.pro_runaround,
        'Rookie Football': s.rookie_football,
        'Rookie Onslaught': s.rookie_onslaught,
        'The Last Stand': s.the_last_stand,
        'Uber Football': s.uber_football,
        'Uber Onslaught': s.uber_onslaught,
        'Uber Runaround': s.uber_runaround,
    }.get(key)
    if entry is not None:
        return entry

    # A mod's level; show its own text.
    if '${GAME}' in key:
        key = key.replace('${GAME}', game.evaluate())
    return babase.LangStr.from_text(key)


class Level:
    """An entry in a :class:`~bascenev1.Campaign`."""

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
        """The unique name for this level."""
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
        """The preview texture name for this level."""
        return self._preview_texture_name

    @property
    def displayname(self) -> bascenev1.Lstr:
        """The localized name for this level.

        .. deprecated:: 1.8.0
           Use :attr:`displayname_langstr`. This property's type changes
           to :class:`~babase.LangStr` when api 9 support ends.
        """
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
    def displayname_langstr(self) -> babase.LangStr:
        """The localized name for this level.

        This is the :class:`~babase.LangStr` flavor of
        :attr:`displayname`. It exists only for the transition; once api
        9 support ends, :attr:`displayname` returns this and this
        property goes away with the removal of api 10.
        """
        return _get_level_display_name(
            (
                self._displayname
                if self._displayname is not None
                else self._name
            ),
            self._gametype.get_display_string(self._settings, langstr=True),
        )

    @property
    def gametype(self) -> type[bascenev1.GameActivity]:
        """The type of game used for this level."""
        return self._gametype

    @property
    def campaign(self) -> bascenev1.Campaign | None:
        """The campaign this level is associated with, or None."""
        return None if self._campaign is None else self._campaign()

    @property
    def index(self) -> int:
        """The zero-based index of this level in its campaign.

        Access results in a RuntimeError if the level is not assigned to
        a campaign.
        """
        if self._index is None:
            raise RuntimeError('Level is not part of a Campaign')
        return self._index

    @property
    def complete(self) -> bool:
        """Whether this level has been completed."""
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
        """Return the current high scores for this level."""
        config = self._get_config_dict()
        high_scores_key = f'High Scores{self.get_score_version_string()}'
        val = config.get(high_scores_key)
        if isinstance(val, dict):
            return copy.deepcopy(val)
        return {}

    def set_high_scores(self, high_scores: dict) -> None:
        """Set high scores for this level."""
        config = self._get_config_dict()
        high_scores_key = 'High Scores' + self.get_score_version_string()
        config[high_scores_key] = high_scores

    def get_score_version_string(self) -> str:
        """Return the score version string for this level.

        If a level's gameplay changes significantly, its version string
        can be changed to separate its new high score lists/etc. from
        the old.
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
        """The current rating for this level."""
        val = self._get_config_dict().get('Rating', 0.0)
        assert isinstance(val, float)
        return val

    def set_rating(self, rating: float) -> None:
        """Set a rating for this level, replacing the old ONLY IF higher."""
        old_rating = self.rating
        config = self._get_config_dict()
        config['Rating'] = max(old_rating, rating)

    def _get_config_dict(self) -> dict[str, Any]:
        """Return/create the persistent state dict for this level.

        The referenced dict exists under the game's config dict and can
        be modified in place.
        """
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
        """Internal: Used by campaign when adding levels to itself.

        :meta private:
        """
        self._campaign = weakref.ref(campaign)
        self._index = index
