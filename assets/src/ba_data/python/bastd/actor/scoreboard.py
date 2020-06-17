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
"""Defines ScoreBoard Actor and related functionality."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Optional, Sequence, Dict, Union


class _Entry:

    def __init__(self, scoreboard: Scoreboard, team: ba.Team, do_cover: bool,
                 scale: float, label: Optional[ba.Lstr], flash_length: float):
        # pylint: disable=too-many-statements
        self._scoreboard = weakref.ref(scoreboard)
        self._do_cover = do_cover
        self._scale = scale
        self._flash_length = flash_length
        self._width = 140.0 * self._scale
        self._height = 32.0 * self._scale
        self._bar_width = 2.0 * self._scale
        self._bar_height = 32.0 * self._scale
        self._bar_tex = self._backing_tex = ba.gettexture('bar')
        self._cover_tex = ba.gettexture('uiAtlas')
        self._model = ba.getmodel('meterTransparent')
        self._pos: Optional[Sequence[float]] = None
        self._flash_timer: Optional[ba.Timer] = None
        self._flash_counter: Optional[int] = None
        self._flash_colors: Optional[bool] = None
        self._score: Optional[float] = None

        safe_team_color = ba.safecolor(team.color, target_intensity=1.0)

        # FIXME: Should not do things conditionally for vr-mode, as there may
        #  be non-vr clients connected which will also get these value.
        vrmode = ba.app.vr_mode

        if self._do_cover:
            if vrmode:
                self._backing_color = [0.1 + c * 0.1 for c in safe_team_color]
            else:
                self._backing_color = [
                    0.05 + c * 0.17 for c in safe_team_color
                ]
        else:
            self._backing_color = [0.05 + c * 0.1 for c in safe_team_color]

        opacity = (0.8 if vrmode else 0.8) if self._do_cover else 0.5
        self._backing = ba.NodeActor(
            ba.newnode('image',
                       attrs={
                           'scale': (self._width, self._height),
                           'opacity': opacity,
                           'color': self._backing_color,
                           'vr_depth': -3,
                           'attach': 'topLeft',
                           'texture': self._backing_tex
                       }))

        self._barcolor = safe_team_color
        self._bar = ba.NodeActor(
            ba.newnode('image',
                       attrs={
                           'opacity': 0.7,
                           'color': self._barcolor,
                           'attach': 'topLeft',
                           'texture': self._bar_tex
                       }))

        self._bar_scale = ba.newnode('combine',
                                     owner=self._bar.node,
                                     attrs={
                                         'size': 2,
                                         'input0': self._bar_width,
                                         'input1': self._bar_height
                                     })
        assert self._bar.node
        self._bar_scale.connectattr('output', self._bar.node, 'scale')
        self._bar_position = ba.newnode('combine',
                                        owner=self._bar.node,
                                        attrs={
                                            'size': 2,
                                            'input0': 0,
                                            'input1': 0
                                        })
        self._bar_position.connectattr('output', self._bar.node, 'position')
        self._cover_color = safe_team_color
        if self._do_cover:
            self._cover = ba.NodeActor(
                ba.newnode('image',
                           attrs={
                               'scale':
                                   (self._width * 1.15, self._height * 1.6),
                               'opacity': 1.0,
                               'color': self._cover_color,
                               'vr_depth': 2,
                               'attach': 'topLeft',
                               'texture': self._cover_tex,
                               'model_transparent': self._model
                           }))

        clr = safe_team_color
        maxwidth = 130.0 * (1.0 - scoreboard.score_split)
        flatness = ((1.0 if vrmode else 0.5) if self._do_cover else 1.0)
        self._score_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'h_attach': 'left',
                           'v_attach': 'top',
                           'h_align': 'right',
                           'v_align': 'center',
                           'maxwidth': maxwidth,
                           'vr_depth': 2,
                           'scale': self._scale * 0.9,
                           'text': '',
                           'shadow': 1.0 if vrmode else 0.5,
                           'flatness': flatness,
                           'color': clr
                       }))

        clr = safe_team_color

        team_name_label: Union[str, ba.Lstr]
        if label is not None:
            team_name_label = label
        else:
            team_name_label = team.name

            # We do our own clipping here; should probably try to tap into some
            # existing functionality.
            if isinstance(team_name_label, ba.Lstr):

                # Hmmm; if the team-name is a non-translatable value lets go
                # ahead and clip it otherwise we leave it as-is so
                # translation can occur..
                if team_name_label.is_flat_value():
                    val = team_name_label.evaluate()
                    if len(val) > 10:
                        team_name_label = ba.Lstr(value=val[:10] + '...')
            else:
                if len(team_name_label) > 10:
                    team_name_label = team_name_label[:10] + '...'
                team_name_label = ba.Lstr(value=team_name_label)

        flatness = ((1.0 if vrmode else 0.5) if self._do_cover else 1.0)
        self._name_text = ba.NodeActor(
            ba.newnode('text',
                       attrs={
                           'h_attach': 'left',
                           'v_attach': 'top',
                           'h_align': 'left',
                           'v_align': 'center',
                           'vr_depth': 2,
                           'scale': self._scale * 0.9,
                           'shadow': 1.0 if vrmode else 0.5,
                           'flatness': flatness,
                           'maxwidth': 130 * scoreboard.score_split,
                           'text': team_name_label,
                           'color': clr + (1.0, )
                       }))

    def flash(self, countdown: bool, extra_flash: bool) -> None:
        """Flash momentarily."""
        self._flash_timer = ba.Timer(0.1,
                                     ba.WeakCall(self._do_flash),
                                     repeat=True)
        if countdown:
            self._flash_counter = 10
        else:
            self._flash_counter = int(20.0 * self._flash_length)
        if extra_flash:
            self._flash_counter *= 4
        self._set_flash_colors(True)

    def set_position(self, position: Sequence[float]) -> None:
        """Set the entry's position."""

        # Abort if we've been killed
        if not self._backing.node:
            return

        self._pos = tuple(position)
        self._backing.node.position = (position[0] + self._width / 2,
                                       position[1] - self._height / 2)
        if self._do_cover:
            assert self._cover.node
            self._cover.node.position = (position[0] + self._width / 2,
                                         position[1] - self._height / 2)
        self._bar_position.input0 = self._pos[0] + self._bar_width / 2
        self._bar_position.input1 = self._pos[1] - self._bar_height / 2
        assert self._score_text.node
        self._score_text.node.position = (self._pos[0] + self._width -
                                          7.0 * self._scale,
                                          self._pos[1] - self._bar_height +
                                          16.0 * self._scale)
        assert self._name_text.node
        self._name_text.node.position = (self._pos[0] + 7.0 * self._scale,
                                         self._pos[1] - self._bar_height +
                                         16.0 * self._scale)

    def _set_flash_colors(self, flash: bool) -> None:
        self._flash_colors = flash

        def _safesetcolor(node: Optional[ba.Node], val: Any) -> None:
            if node:
                node.color = val

        if flash:
            scale = 2.0
            _safesetcolor(
                self._backing.node,
                (self._backing_color[0] * scale, self._backing_color[1] *
                 scale, self._backing_color[2] * scale))
            _safesetcolor(self._bar.node,
                          (self._barcolor[0] * scale, self._barcolor[1] *
                           scale, self._barcolor[2] * scale))
            if self._do_cover:
                _safesetcolor(
                    self._cover.node,
                    (self._cover_color[0] * scale, self._cover_color[1] *
                     scale, self._cover_color[2] * scale))
        else:
            _safesetcolor(self._backing.node, self._backing_color)
            _safesetcolor(self._bar.node, self._barcolor)
            if self._do_cover:
                _safesetcolor(self._cover.node, self._cover_color)

    def _do_flash(self) -> None:
        assert self._flash_counter is not None
        if self._flash_counter <= 0:
            self._set_flash_colors(False)
        else:
            self._flash_counter -= 1
            self._set_flash_colors(not self._flash_colors)

    def set_value(self,
                  score: float,
                  max_score: float = None,
                  countdown: bool = False,
                  flash: bool = True,
                  show_value: bool = True) -> None:
        """Set the value for the scoreboard entry."""

        # If we have no score yet, just set it.. otherwise compare
        # and see if we should flash.
        if self._score is None:
            self._score = score
        else:
            if score > self._score or (countdown and score < self._score):
                extra_flash = (max_score is not None and score >= max_score
                               and not countdown) or (countdown and score == 0)
                if flash:
                    self.flash(countdown, extra_flash)
            self._score = score

        if max_score is None:
            self._bar_width = 0.0
        else:
            if countdown:
                self._bar_width = max(
                    2.0 * self._scale,
                    self._width * (1.0 - (float(score) / max_score)))
            else:
                self._bar_width = max(
                    2.0 * self._scale,
                    self._width * (min(1.0,
                                       float(score) / max_score)))

        cur_width = self._bar_scale.input0
        ba.animate(self._bar_scale, 'input0', {
            0.0: cur_width,
            0.25: self._bar_width
        })
        self._bar_scale.input1 = self._bar_height
        cur_x = self._bar_position.input0
        assert self._pos is not None
        ba.animate(self._bar_position, 'input0', {
            0.0: cur_x,
            0.25: self._pos[0] + self._bar_width / 2
        })
        self._bar_position.input1 = self._pos[1] - self._bar_height / 2
        assert self._score_text.node
        if show_value:
            self._score_text.node.text = str(score)
        else:
            self._score_text.node.text = ''


class _EntryProxy:
    """Encapsulates adding/removing of a scoreboard Entry."""

    def __init__(self, scoreboard: Scoreboard, team: ba.Team):
        self._scoreboard = weakref.ref(scoreboard)

        # Have to store ID here instead of a weak-ref since the team will be
        # dead when we die and need to remove it.
        self._team_id = team.id

    def __del__(self) -> None:
        scoreboard = self._scoreboard()

        # Remove our team from the scoreboard if its still around.
        # (but deferred, in case we die in a sim step or something where
        # its illegal to modify nodes)
        if scoreboard is None:
            return

        try:
            ba.pushcall(ba.Call(scoreboard.remove_team, self._team_id))
        except ba.ContextError:
            # This happens if we fire after the activity expires.
            # In that case we don't need to do anything.
            pass


class Scoreboard:
    """A display for player or team scores during a game.

    category: Gameplay Classes
    """

    _ENTRYSTORENAME = ba.storagename('entry')

    def __init__(self, label: ba.Lstr = None, score_split: float = 0.7):
        """Instantiate a scoreboard.

        Label can be something like 'points' and will
        show up on boards if provided.
        """
        self._flat_tex = ba.gettexture('null')
        self._entries: Dict[int, _Entry] = {}
        self._label = label
        self.score_split = score_split

        # For free-for-all we go simpler since we have one per player.
        self._pos: Sequence[float]
        if isinstance(ba.getsession(), ba.FreeForAllSession):
            self._do_cover = False
            self._spacing = 35.0
            self._pos = (17.0, -65.0)
            self._scale = 0.8
            self._flash_length = 0.5
        else:
            self._do_cover = True
            self._spacing = 50.0
            self._pos = (20.0, -70.0)
            self._scale = 1.0
            self._flash_length = 1.0

    def set_team_value(self,
                       team: ba.Team,
                       score: float,
                       max_score: float = None,
                       countdown: bool = False,
                       flash: bool = True,
                       show_value: bool = True) -> None:
        """Update the score-board display for the given ba.Team."""
        if not team.id in self._entries:
            self._add_team(team)

            # Create a proxy in the team which will kill
            # our entry when it dies (for convenience)
            assert self._ENTRYSTORENAME not in team.customdata
            team.customdata[self._ENTRYSTORENAME] = _EntryProxy(self, team)

        # Now set the entry.
        self._entries[team.id].set_value(score=score,
                                         max_score=max_score,
                                         countdown=countdown,
                                         flash=flash,
                                         show_value=show_value)

    def _add_team(self, team: ba.Team) -> None:
        if team.id in self._entries:
            raise RuntimeError('Duplicate team add')
        self._entries[team.id] = _Entry(self,
                                        team,
                                        do_cover=self._do_cover,
                                        scale=self._scale,
                                        label=self._label,
                                        flash_length=self._flash_length)
        self._update_teams()

    def remove_team(self, team_id: int) -> None:
        """Remove the team with the given id from the scoreboard."""
        del self._entries[team_id]
        self._update_teams()

    def _update_teams(self) -> None:
        pos = list(self._pos)
        for entry in list(self._entries.values()):
            entry.set_position(pos)
            pos[1] -= self._spacing * self._scale
