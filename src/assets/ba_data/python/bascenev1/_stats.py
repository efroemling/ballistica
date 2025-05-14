# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to scores and statistics."""
from __future__ import annotations

import random
import weakref
import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass

import babase

import _bascenev1


if TYPE_CHECKING:
    from typing import Any, Sequence

    import bascenev1


@dataclass
class PlayerScoredMessage:
    """Informs something that a bascenev1.Player scored."""

    score: int
    """The score value."""


class PlayerRecord:
    """Stats for an individual player in a bascenev1.Stats object.

    This does not necessarily correspond to a bascenev1.Player that is
    still present (stats may be retained for players that leave
    mid-game)
    """

    character: str

    def __init__(
        self,
        name: str,
        name_full: str,
        sessionplayer: bascenev1.SessionPlayer,
        stats: bascenev1.Stats,
    ):
        self.name = name
        self.name_full = name_full
        self.score = 0
        self.accumscore = 0
        self.kill_count = 0
        self.accum_kill_count = 0
        self.killed_count = 0
        self.accum_killed_count = 0
        self._multi_kill_timer: bascenev1.Timer | None = None
        self._multi_kill_count = 0
        self._stats = weakref.ref(stats)
        self._last_sessionplayer: bascenev1.SessionPlayer | None = None
        self._sessionplayer: bascenev1.SessionPlayer | None = None
        self._sessionteam: weakref.ref[bascenev1.SessionTeam] | None = None
        self.streak = 0
        self.associate_with_sessionplayer(sessionplayer)

    @property
    def team(self) -> bascenev1.SessionTeam:
        """The bascenev1.SessionTeam the last associated player was last on.

        This can still return a valid result even if the player is gone.
        Raises a bascenev1.SessionTeamNotFoundError if the team no longer
        exists.
        """
        assert self._sessionteam is not None
        team = self._sessionteam()
        if team is None:
            raise babase.SessionTeamNotFoundError()
        return team

    @property
    def player(self) -> bascenev1.SessionPlayer:
        """Return the instance's associated bascenev1.SessionPlayer.

        Raises a bascenev1.SessionPlayerNotFoundError if the player
        no longer exists.
        """
        if not self._sessionplayer:
            raise babase.SessionPlayerNotFoundError()
        return self._sessionplayer

    def getname(self, full: bool = False) -> str:
        """Return the player entry's name."""
        return self.name_full if full else self.name

    def get_icon(self) -> dict[str, Any]:
        """Get the icon for this instance's player."""
        player = self._last_sessionplayer
        assert player is not None
        return player.get_icon()

    def cancel_multi_kill_timer(self) -> None:
        """Cancel any multi-kill timer for this player entry."""
        self._multi_kill_timer = None

    def getactivity(self) -> bascenev1.Activity | None:
        """Return the bascenev1.Activity this instance is associated with.

        Returns None if the activity no longer exists."""
        stats = self._stats()
        if stats is not None:
            return stats.getactivity()
        return None

    def associate_with_sessionplayer(
        self, sessionplayer: bascenev1.SessionPlayer
    ) -> None:
        """Associate this entry with a bascenev1.SessionPlayer."""
        self._sessionteam = weakref.ref(sessionplayer.sessionteam)
        self.character = sessionplayer.character
        self._last_sessionplayer = sessionplayer
        self._sessionplayer = sessionplayer
        self.streak = 0

    def _end_multi_kill(self) -> None:
        self._multi_kill_timer = None
        self._multi_kill_count = 0

    def get_last_sessionplayer(self) -> bascenev1.SessionPlayer:
        """Return the last bascenev1.Player we were associated with."""
        assert self._last_sessionplayer is not None
        return self._last_sessionplayer

    def submit_kill(self, showpoints: bool = True) -> None:
        """Submit a kill for this player entry."""
        # FIXME Clean this up.
        # pylint: disable=too-many-statements

        self._multi_kill_count += 1
        stats = self._stats()
        assert stats
        if self._multi_kill_count == 1:
            score = 0
            name = None
            delay = 0.0
            color = (0.0, 0.0, 0.0, 1.0)
            scale = 1.0
            sound = None
        elif self._multi_kill_count == 2:
            score = 20
            name = babase.Lstr(resource='twoKillText')
            color = (0.1, 1.0, 0.0, 1)
            scale = 1.0
            delay = 0.0
            sound = stats.orchestrahitsound1
        elif self._multi_kill_count == 3:
            score = 40
            name = babase.Lstr(resource='threeKillText')
            color = (1.0, 0.7, 0.0, 1)
            scale = 1.1
            delay = 0.3
            sound = stats.orchestrahitsound2
        elif self._multi_kill_count == 4:
            score = 60
            name = babase.Lstr(resource='fourKillText')
            color = (1.0, 1.0, 0.0, 1)
            scale = 1.2
            delay = 0.6
            sound = stats.orchestrahitsound3
        elif self._multi_kill_count == 5:
            score = 80
            name = babase.Lstr(resource='fiveKillText')
            color = (1.0, 0.5, 0.0, 1)
            scale = 1.3
            delay = 0.9
            sound = stats.orchestrahitsound4
        else:
            score = 100
            name = babase.Lstr(
                resource='multiKillText',
                subs=[('${COUNT}', str(self._multi_kill_count))],
            )
            color = (1.0, 0.5, 0.0, 1)
            scale = 1.3
            delay = 1.0
            sound = stats.orchestrahitsound4

        def _apply(
            name2: babase.Lstr,
            score2: int,
            showpoints2: bool,
            color2: tuple[float, float, float, float],
            scale2: float,
            sound2: bascenev1.Sound | None,
        ) -> None:
            # pylint: disable=too-many-positional-arguments
            from bascenev1lib.actor.popuptext import PopupText

            # Only award this if they're still alive and we can get
            # a current position for them.
            our_pos: babase.Vec3 | None = None
            if self._sessionplayer:
                if self._sessionplayer.activityplayer is not None:
                    try:
                        our_pos = self._sessionplayer.activityplayer.position
                    except babase.NotFoundError:
                        pass
            if our_pos is None:
                return

            # Jitter position a bit since these often come in clusters.
            our_pos = babase.Vec3(
                our_pos[0] + (random.random() - 0.5) * 2.0,
                our_pos[1] + (random.random() - 0.5) * 2.0,
                our_pos[2] + (random.random() - 0.5) * 2.0,
            )
            activity = self.getactivity()
            if activity is not None:
                PopupText(
                    babase.Lstr(
                        value=(('+' + str(score2) + ' ') if showpoints2 else '')
                        + '${N}',
                        subs=[('${N}', name2)],
                    ),
                    color=color2,
                    scale=scale2,
                    position=our_pos,
                ).autoretain()
            if sound2:
                sound2.play()

            self.score += score2
            self.accumscore += score2

            # Inform a running game of the score.
            if score2 != 0 and activity is not None:
                activity.handlemessage(PlayerScoredMessage(score=score2))

        if name is not None:
            _bascenev1.timer(
                0.3 + delay,
                babase.Call(
                    _apply, name, score, showpoints, color, scale, sound
                ),
            )

        # Keep the tally rollin'...
        # set a timer for a bit in the future.
        self._multi_kill_timer = _bascenev1.Timer(1.0, self._end_multi_kill)


class Stats:
    """Manages scores and statistics for a bascenev1.Session."""

    def __init__(self) -> None:
        self._activity: weakref.ref[bascenev1.Activity] | None = None
        self._player_records: dict[str, PlayerRecord] = {}
        self.orchestrahitsound1: bascenev1.Sound | None = None
        self.orchestrahitsound2: bascenev1.Sound | None = None
        self.orchestrahitsound3: bascenev1.Sound | None = None
        self.orchestrahitsound4: bascenev1.Sound | None = None

    def setactivity(self, activity: bascenev1.Activity | None) -> None:
        """Set the current activity for this instance."""

        self._activity = None if activity is None else weakref.ref(activity)

        # Load our media into this activity's context.
        if activity is not None:
            if activity.expired:
                logging.exception('Unexpected finalized activity.')
            else:
                with activity.context:
                    self._load_activity_media()

    def getactivity(self) -> bascenev1.Activity | None:
        """Get the activity associated with this instance.

        May return None.
        """
        if self._activity is None:
            return None
        return self._activity()

    def _load_activity_media(self) -> None:
        self.orchestrahitsound1 = _bascenev1.getsound('orchestraHit')
        self.orchestrahitsound2 = _bascenev1.getsound('orchestraHit2')
        self.orchestrahitsound3 = _bascenev1.getsound('orchestraHit3')
        self.orchestrahitsound4 = _bascenev1.getsound('orchestraHit4')

    def reset(self) -> None:
        """Reset the stats instance completely."""

        # Just to be safe, lets make sure no multi-kill timers are gonna go off
        # for no-longer-on-the-list players.
        for p_entry in list(self._player_records.values()):
            p_entry.cancel_multi_kill_timer()
        self._player_records = {}

    def reset_accum(self) -> None:
        """Reset per-sound sub-scores."""
        for s_player in list(self._player_records.values()):
            s_player.cancel_multi_kill_timer()
            s_player.accumscore = 0
            s_player.accum_kill_count = 0
            s_player.accum_killed_count = 0
            s_player.streak = 0

    def register_sessionplayer(self, player: bascenev1.SessionPlayer) -> None:
        """Register a bascenev1.SessionPlayer with this score-set."""
        assert player.exists()  # Invalid refs should never be passed to funcs.
        name = player.getname()
        if name in self._player_records:
            # If the player already exists, update his character and such as
            # it may have changed.
            self._player_records[name].associate_with_sessionplayer(player)
        else:
            name_full = player.getname(full=True)
            self._player_records[name] = PlayerRecord(
                name, name_full, player, self
            )

    def get_records(self) -> dict[str, bascenev1.PlayerRecord]:
        """Get PlayerRecord corresponding to still-existing players."""
        records = {}

        # Go through our player records and return ones whose player id still
        # corresponds to a player with that name.
        for record_id, record in self._player_records.items():
            lastplayer = record.get_last_sessionplayer()
            if lastplayer and lastplayer.getname() == record_id:
                records[record_id] = record
        return records

    def player_scored(
        self,
        player: bascenev1.Player,
        base_points: int = 1,
        *,
        target: Sequence[float] | None = None,
        kill: bool = False,
        victim_player: bascenev1.Player | None = None,
        scale: float = 1.0,
        color: Sequence[float] | None = None,
        title: str | babase.Lstr | None = None,
        screenmessage: bool = True,
        display: bool = True,
        importance: int = 1,
        showpoints: bool = True,
        big_message: bool = False,
    ) -> int:
        """Register a score for the player.

        Return value is actual score with multipliers and such factored in.
        """
        # FIXME: Tidy this up.
        # pylint: disable=cyclic-import
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        from bascenev1lib.actor.popuptext import PopupText

        from bascenev1._gameactivity import GameActivity

        del victim_player  # Currently unused.
        name = player.getname()
        s_player = self._player_records[name]

        if kill:
            s_player.submit_kill(showpoints=showpoints)

        display_color: Sequence[float] = (1.0, 1.0, 1.0, 1.0)

        if color is not None:
            display_color = color
        elif importance != 1:
            display_color = (1.0, 1.0, 0.4, 1.0)
        points = base_points

        # If they want a big announcement, throw a zoom-text up there.
        if display and big_message:
            try:
                assert self._activity is not None
                activity = self._activity()
                if isinstance(activity, GameActivity):
                    name_full = player.getname(full=True, icon=False)
                    activity.show_zoom_message(
                        babase.Lstr(
                            resource='nameScoresText',
                            subs=[('${NAME}', name_full)],
                        ),
                        color=babase.normalized_color(player.team.color),
                    )
            except Exception:
                logging.exception('Error showing big_message.')

        # If we currently have a actor, pop up a score over it.
        if display and showpoints:
            our_pos = player.node.position if player.node else None
            if our_pos is not None:
                if target is None:
                    target = our_pos

                # If display-pos is *way* lower than us, raise it up
                # (so we can still see scores from dudes that fell off cliffs).
                display_pos = (
                    target[0],
                    max(target[1], our_pos[1] - 2.0),
                    min(target[2], our_pos[2] + 2.0),
                )
                activity = self.getactivity()
                if activity is not None:
                    if title is not None:
                        sval = babase.Lstr(
                            value='+${A} ${B}',
                            subs=[('${A}', str(points)), ('${B}', title)],
                        )
                    else:
                        sval = babase.Lstr(
                            value='+${A}', subs=[('${A}', str(points))]
                        )
                    PopupText(
                        sval,
                        color=display_color,
                        scale=1.2 * scale,
                        position=display_pos,
                    ).autoretain()

        # Tally kills.
        if kill:
            s_player.accum_kill_count += 1
            s_player.kill_count += 1

        # Report non-kill scorings.
        try:
            if screenmessage and not kill:
                _bascenev1.broadcastmessage(
                    babase.Lstr(
                        resource='nameScoresText', subs=[('${NAME}', name)]
                    ),
                    top=True,
                    color=player.color,
                    image=player.get_icon(),
                )
        except Exception:
            logging.exception('Error announcing score.')

        s_player.score += points
        s_player.accumscore += points

        # Inform a running game of the score.
        if points != 0:
            activity = self._activity() if self._activity is not None else None
            if activity is not None:
                activity.handlemessage(PlayerScoredMessage(score=points))

        return points

    def player_was_killed(
        self,
        player: bascenev1.Player,
        killed: bool = False,
        killer: bascenev1.Player | None = None,
    ) -> None:
        """Should be called when a player is killed."""
        name = player.getname()
        prec = self._player_records[name]
        prec.streak = 0
        if killed:
            prec.accum_killed_count += 1
            prec.killed_count += 1
        try:
            if killed and _bascenev1.getactivity().announce_player_deaths:
                if killer is player:
                    _bascenev1.broadcastmessage(
                        babase.Lstr(
                            resource='nameSuicideText', subs=[('${NAME}', name)]
                        ),
                        top=True,
                        color=player.color,
                        image=player.get_icon(),
                    )
                elif killer is not None:
                    if killer.team is player.team:
                        _bascenev1.broadcastmessage(
                            babase.Lstr(
                                resource='nameBetrayedText',
                                subs=[
                                    ('${NAME}', killer.getname()),
                                    ('${VICTIM}', name),
                                ],
                            ),
                            top=True,
                            color=killer.color,
                            image=killer.get_icon(),
                        )
                    else:
                        _bascenev1.broadcastmessage(
                            babase.Lstr(
                                resource='nameKilledText',
                                subs=[
                                    ('${NAME}', killer.getname()),
                                    ('${VICTIM}', name),
                                ],
                            ),
                            top=True,
                            color=killer.color,
                            image=killer.get_icon(),
                        )
                else:
                    _bascenev1.broadcastmessage(
                        babase.Lstr(
                            resource='nameDiedText', subs=[('${NAME}', name)]
                        ),
                        top=True,
                        color=player.color,
                        image=player.get_icon(),
                    )
        except Exception:
            logging.exception('Error announcing kill.')
