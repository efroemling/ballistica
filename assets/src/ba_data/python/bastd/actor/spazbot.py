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
"""Bot versions of Spaz."""
# pylint: disable=too-many-lines

from __future__ import annotations

import random
import weakref
from typing import TYPE_CHECKING

import ba
from bastd.actor.spaz import Spaz

if TYPE_CHECKING:
    from typing import Any, Optional, List, Tuple, Sequence, Type, Callable
    from bastd.actor.flag import Flag

LITE_BOT_COLOR = (1.2, 0.9, 0.2)
LITE_BOT_HIGHLIGHT = (1.0, 0.5, 0.6)
DEFAULT_BOT_COLOR = (0.6, 0.6, 0.6)
DEFAULT_BOT_HIGHLIGHT = (0.1, 0.3, 0.1)
PRO_BOT_COLOR = (1.0, 0.2, 0.1)
PRO_BOT_HIGHLIGHT = (0.6, 0.1, 0.05)


class SpazBotPunchedMessage:
    """A message saying a ba.SpazBot got punched.

    category: Message Classes

    Attributes:

       spazbot
          The ba.SpazBot that got punched.

       damage
          How much damage was done to the ba.SpazBot.
    """

    def __init__(self, spazbot: SpazBot, damage: int):
        """Instantiate a message with the given values."""
        self.spazbot = spazbot
        self.damage = damage


class SpazBotDiedMessage:
    """A message saying a ba.SpazBot has died.

    category: Message Classes

    Attributes:

       spazbot
          The ba.SpazBot that was killed.

       killerplayer
          The ba.Player that killed it (or None).

       how
          The particular type of death.
    """

    def __init__(self, spazbot: SpazBot, killerplayer: Optional[ba.Player],
                 how: ba.DeathType):
        """Instantiate with given values."""
        self.spazbot = spazbot
        self.killerplayer = killerplayer
        self.how = how


class SpazBot(Spaz):
    """A really dumb AI version of ba.Spaz.

    category: Bot Classes

    Add these to a ba.BotSet to use them.

    Note: currently the AI has no real ability to
    navigate obstacles and so should only be used
    on wide-open maps.

    When a SpazBot is killed, it delivers a ba.SpazBotDiedMessage
    to the current activity.

    When a SpazBot is punched, it delivers a ba.SpazBotPunchedMessage
    to the current activity.
    """

    character = 'Spaz'
    punchiness = 0.5
    throwiness = 0.7
    static = False
    bouncy = False
    run = False
    charge_dist_min = 0.0  # When we can start a new charge.
    charge_dist_max = 2.0  # When we can start a new charge.
    run_dist_min = 0.0  # How close we can be to continue running.
    charge_speed_min = 0.4
    charge_speed_max = 1.0
    throw_dist_min = 5.0
    throw_dist_max = 9.0
    throw_rate = 1.0
    default_bomb_type = 'normal'
    default_bomb_count = 3
    start_cursed = False
    color = DEFAULT_BOT_COLOR
    highlight = DEFAULT_BOT_HIGHLIGHT

    def __init__(self) -> None:
        """Instantiate a spaz-bot."""
        super().__init__(color=self.color,
                         highlight=self.highlight,
                         character=self.character,
                         source_player=None,
                         start_invincible=False,
                         can_accept_powerups=False)

        # If you need to add custom behavior to a bot, set this to a callable
        # which takes one arg (the bot) and returns False if the bot's normal
        # update should be run and True if not.
        self.update_callback: Optional[Callable[[SpazBot], Any]] = None
        activity = self.activity
        assert isinstance(activity, ba.GameActivity)
        self._map = weakref.ref(activity.map)
        self.last_player_attacked_by: Optional[ba.Player] = None
        self.last_attacked_time = 0.0
        self.last_attacked_type: Optional[Tuple[str, str]] = None
        self.target_point_default: Optional[ba.Vec3] = None
        self.held_count = 0
        self.last_player_held_by: Optional[ba.Player] = None
        self.target_flag: Optional[Flag] = None
        self._charge_speed = 0.5 * (self.charge_speed_min +
                                    self.charge_speed_max)
        self._lead_amount = 0.5
        self._mode = 'wait'
        self._charge_closing_in = False
        self._last_charge_dist = 0.0
        self._running = False
        self._last_jump_time = 0.0

        self._throw_release_time: Optional[float] = None
        self._have_dropped_throw_bomb: Optional[bool] = None
        self._player_pts: Optional[List[Tuple[ba.Vec3, ba.Vec3]]] = None

        # These cooldowns didn't exist when these bots were calibrated,
        # so take them out of the equation.
        self._jump_cooldown = 0
        self._pickup_cooldown = 0
        self._fly_cooldown = 0
        self._bomb_cooldown = 0

        if self.start_cursed:
            self.curse()

    @property
    def map(self) -> ba.Map:
        """The map this bot was created on."""
        mval = self._map()
        assert mval is not None
        return mval

    def _get_target_player_pt(
            self) -> Tuple[Optional[ba.Vec3], Optional[ba.Vec3]]:
        """Returns the position and velocity of our target.

        Both values will be None in the case of no target.
        """
        assert self.node
        botpt = ba.Vec3(self.node.position)
        closest_dist: Optional[float] = None
        closest_vel: Optional[ba.Vec3] = None
        closest: Optional[ba.Vec3] = None
        assert self._player_pts is not None
        for plpt, plvel in self._player_pts:
            dist = (plpt - botpt).length()

            # Ignore player-points that are significantly below the bot
            # (keeps bots from following players off cliffs).
            if (closest_dist is None
                    or dist < closest_dist) and (plpt[1] > botpt[1] - 5.0):
                closest_dist = dist
                closest_vel = plvel
                closest = plpt
        if closest_dist is not None:
            assert closest_vel is not None
            assert closest is not None
            return (ba.Vec3(closest[0], closest[1], closest[2]),
                    ba.Vec3(closest_vel[0], closest_vel[1], closest_vel[2]))
        return None, None

    def set_player_points(self, pts: List[Tuple[ba.Vec3, ba.Vec3]]) -> None:
        """Provide the spaz-bot with the locations of its enemies."""
        self._player_pts = pts

    def update_ai(self) -> None:
        """Should be called periodically to update the spaz' AI."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        if self.update_callback is not None:
            if self.update_callback(self):
                # Bot has been handled.
                return

        if not self.node:
            return

        pos = self.node.position
        our_pos = ba.Vec3(pos[0], 0, pos[2])
        can_attack = True

        target_pt_raw: Optional[ba.Vec3]
        target_vel: Optional[ba.Vec3]

        # If we're a flag-bearer, we're pretty simple-minded - just walk
        # towards the flag and try to pick it up.
        if self.target_flag:
            if self.node.hold_node:
                holding_flag = (self.node.hold_node.getnodetype() == 'flag')
            else:
                holding_flag = False

            # If we're holding the flag, just walk left.
            if holding_flag:
                # Just walk left.
                self.node.move_left_right = -1.0
                self.node.move_up_down = 0.0

            # Otherwise try to go pick it up.
            elif self.target_flag.node:
                target_pt_raw = ba.Vec3(*self.target_flag.node.position)
                diff = (target_pt_raw - our_pos)
                diff = ba.Vec3(diff[0], 0, diff[2])  # Don't care about y.
                dist = diff.length()
                to_target = diff.normalized()

                # If we're holding some non-flag item, drop it.
                if self.node.hold_node:
                    self.node.pickup_pressed = True
                    self.node.pickup_pressed = False
                    return

                # If we're a runner, run only when not super-near the flag.
                if self.run and dist > 3.0:
                    self._running = True
                    self.node.run = 1.0
                else:
                    self._running = False
                    self.node.run = 0.0

                self.node.move_left_right = to_target.x
                self.node.move_up_down = -to_target.z
                if dist < 1.25:
                    self.node.pickup_pressed = True
                    self.node.pickup_pressed = False
            return

        # Not a flag-bearer. If we're holding anything but a bomb, drop it.
        if self.node.hold_node:
            holding_bomb = (self.node.hold_node.getnodetype()
                            in ['bomb', 'prop'])
            if not holding_bomb:
                self.node.pickup_pressed = True
                self.node.pickup_pressed = False
                return

        target_pt_raw, target_vel = self._get_target_player_pt()

        if target_pt_raw is None:
            # Use default target if we've got one.
            if self.target_point_default is not None:
                target_pt_raw = self.target_point_default
                target_vel = ba.Vec3(0, 0, 0)
                can_attack = False

            # With no target, we stop moving and drop whatever we're holding.
            else:
                self.node.move_left_right = 0
                self.node.move_up_down = 0
                if self.node.hold_node:
                    self.node.pickup_pressed = True
                    self.node.pickup_pressed = False
                return

        # We don't want height to come into play.
        target_pt_raw[1] = 0.0
        assert target_vel is not None
        target_vel[1] = 0.0

        dist_raw = (target_pt_raw - our_pos).length()

        # Use a point out in front of them as real target.
        # (more out in front the farther from us they are)
        target_pt = (target_pt_raw +
                     target_vel * dist_raw * 0.3 * self._lead_amount)

        diff = (target_pt - our_pos)
        dist = diff.length()
        to_target = diff.normalized()

        if self._mode == 'throw':
            # We can only throw if alive and well.
            if not self._dead and not self.node.knockout:

                assert self._throw_release_time is not None
                time_till_throw = self._throw_release_time - ba.time()

                if not self.node.hold_node:
                    # If we haven't thrown yet, whip out the bomb.
                    if not self._have_dropped_throw_bomb:
                        self.drop_bomb()
                        self._have_dropped_throw_bomb = True

                    # Otherwise our lack of held node means we successfully
                    # released our bomb; lets retreat now.
                    else:
                        self._mode = 'flee'

                # Oh crap, we're holding a bomb; better throw it.
                elif time_till_throw <= 0.0:
                    # Jump and throw.
                    def _safe_pickup(node: ba.Node) -> None:
                        if node and self.node:
                            self.node.pickup_pressed = True
                            self.node.pickup_pressed = False

                    if dist > 5.0:
                        self.node.jump_pressed = True
                        self.node.jump_pressed = False

                        # Throws:
                        ba.timer(0.1, ba.Call(_safe_pickup, self.node))
                    else:
                        # Throws:
                        ba.timer(0.1, ba.Call(_safe_pickup, self.node))

                if self.static:
                    if time_till_throw < 0.3:
                        speed = 1.0
                    elif time_till_throw < 0.7 and dist > 3.0:
                        speed = -1.0  # Whiplash for long throws.
                    else:
                        speed = 0.02
                else:
                    if time_till_throw < 0.7:
                        # Right before throw charge full speed towards target.
                        speed = 1.0
                    else:
                        # Earlier we can hold or move backward for a whiplash.
                        speed = 0.0125
                self.node.move_left_right = to_target.x * speed
                self.node.move_up_down = to_target.z * -1.0 * speed

        elif self._mode == 'charge':
            if random.random() < 0.3:
                self._charge_speed = random.uniform(self.charge_speed_min,
                                                    self.charge_speed_max)

                # If we're a runner we run during charges *except when near
                # an edge (otherwise we tend to fly off easily).
                if self.run and dist_raw > self.run_dist_min:
                    self._lead_amount = 0.3
                    self._running = True
                    self.node.run = 1.0
                else:
                    self._lead_amount = 0.01
                    self._running = False
                    self.node.run = 0.0

            self.node.move_left_right = to_target.x * self._charge_speed
            self.node.move_up_down = to_target.z * -1.0 * self._charge_speed

        elif self._mode == 'wait':
            # Every now and then, aim towards our target.
            # Other than that, just stand there.
            if ba.time(timeformat=ba.TimeFormat.MILLISECONDS) % 1234 < 100:
                self.node.move_left_right = to_target.x * (400.0 / 33000)
                self.node.move_up_down = to_target.z * (-400.0 / 33000)
            else:
                self.node.move_left_right = 0
                self.node.move_up_down = 0

        elif self._mode == 'flee':
            # Even if we're a runner, only run till we get away from our
            # target (if we keep running we tend to run off edges).
            if self.run and dist < 3.0:
                self._running = True
                self.node.run = 1.0
            else:
                self._running = False
                self.node.run = 0.0
            self.node.move_left_right = to_target.x * -1.0
            self.node.move_up_down = to_target.z

        # We might wanna switch states unless we're doing a throw
        # (in which case that's our sole concern).
        if self._mode != 'throw':

            # If we're currently charging, keep track of how far we are
            # from our target. When this value increases it means our charge
            # is over (ran by them or something).
            if self._mode == 'charge':
                if (self._charge_closing_in
                        and self._last_charge_dist < dist < 3.0):
                    self._charge_closing_in = False
                self._last_charge_dist = dist

            # If we have a clean shot, throw!
            if (self.throw_dist_min <= dist < self.throw_dist_max
                    and random.random() < self.throwiness and can_attack):
                self._mode = 'throw'
                self._lead_amount = ((0.4 + random.random() * 0.6)
                                     if dist_raw > 4.0 else
                                     (0.1 + random.random() * 0.4))
                self._have_dropped_throw_bomb = False
                self._throw_release_time = (ba.time() +
                                            (1.0 / self.throw_rate) *
                                            (0.8 + 1.3 * random.random()))

            # If we're static, always charge (which for us means barely move).
            elif self.static:
                self._mode = 'wait'

            # If we're too close to charge (and aren't in the middle of an
            # existing charge) run away.
            elif dist < self.charge_dist_min and not self._charge_closing_in:
                # ..unless we're near an edge, in which case we've got no
                # choice but to charge.
                if self.map.is_point_near_edge(our_pos, self._running):
                    if self._mode != 'charge':
                        self._mode = 'charge'
                        self._lead_amount = 0.2
                        self._charge_closing_in = True
                        self._last_charge_dist = dist
                else:
                    self._mode = 'flee'

            # We're within charging distance, backed against an edge,
            # or farther than our max throw distance.. chaaarge!
            elif (dist < self.charge_dist_max or dist > self.throw_dist_max
                  or self.map.is_point_near_edge(our_pos, self._running)):
                if self._mode != 'charge':
                    self._mode = 'charge'
                    self._lead_amount = 0.01
                    self._charge_closing_in = True
                    self._last_charge_dist = dist

            # We're too close to throw but too far to charge - either run
            # away or just chill if we're near an edge.
            elif dist < self.throw_dist_min:
                # Charge if either we're within charge range or
                # cant retreat to throw.
                self._mode = 'flee'

            # Do some awesome jumps if we're running.
            # FIXME: pylint: disable=too-many-boolean-expressions
            if ((self._running and 1.2 < dist < 2.2
                 and ba.time() - self._last_jump_time > 1.0)
                    or (self.bouncy and ba.time() - self._last_jump_time > 0.4
                        and random.random() < 0.5)):
                self._last_jump_time = ba.time()
                self.node.jump_pressed = True
                self.node.jump_pressed = False

            # Throw punches when real close.
            if dist < (1.6 if self._running else 1.2) and can_attack:
                if random.random() < self.punchiness:
                    self.on_punch_press()
                    self.on_punch_release()

    def on_punched(self, damage: int) -> None:
        """
        Method override; sends ba.SpazBotPunchedMessage
        to the current activity.
        """
        ba.getactivity().handlemessage(SpazBotPunchedMessage(self, damage))

    def on_expire(self) -> None:
        super().on_expire()

        # We're being torn down; release our callback(s) so there's
        # no chance of them keeping activities or other things alive.
        self.update_callback = None

    def handlemessage(self, msg: Any) -> Any:
        # pylint: disable=too-many-branches
        assert not self.expired

        # Keep track of if we're being held and by who most recently.
        if isinstance(msg, ba.PickedUpMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self.held_count += 1
            picked_up_by = msg.node.source_player
            if picked_up_by:
                self.last_player_held_by = picked_up_by

        elif isinstance(msg, ba.DroppedMessage):
            super().handlemessage(msg)  # Augment standard behavior.
            self.held_count -= 1
            if self.held_count < 0:
                print('ERROR: spaz held_count < 0')

            # Let's count someone dropping us as an attack.
            try:
                if msg.node:
                    picked_up_by = msg.node.source_player
                else:
                    picked_up_by = None
            except Exception:
                ba.print_exception('Error on SpazBot DroppedMessage.')
                picked_up_by = None

            if picked_up_by:
                self.last_player_attacked_by = picked_up_by
                self.last_attacked_time = ba.time()
                self.last_attacked_type = ('picked_up', 'default')

        elif isinstance(msg, ba.DieMessage):

            # Report normal deaths for scoring purposes.
            if not self._dead and not msg.immediate:

                killerplayer: Optional[ba.Player]

                # If this guy was being held at the time of death, the
                # holder is the killer.
                if self.held_count > 0 and self.last_player_held_by:
                    killerplayer = self.last_player_held_by
                else:
                    # If they were attacked by someone in the last few
                    # seconds that person's the killer.
                    # Otherwise it was a suicide.
                    if (self.last_player_attacked_by
                            and ba.time() - self.last_attacked_time < 4.0):
                        killerplayer = self.last_player_attacked_by
                    else:
                        killerplayer = None
                activity = self._activity()

                # (convert dead player refs to None)
                if not killerplayer:
                    killerplayer = None
                if activity is not None:
                    activity.handlemessage(
                        SpazBotDiedMessage(self, killerplayer, msg.how))
            super().handlemessage(msg)  # Augment standard behavior.

        # Keep track of the player who last hit us for point rewarding.
        elif isinstance(msg, ba.HitMessage):
            source_player = msg.get_source_player(ba.Player)
            if source_player:
                self.last_player_attacked_by = source_player
                self.last_attacked_time = ba.time()
                self.last_attacked_type = (msg.hit_type, msg.hit_subtype)
            super().handlemessage(msg)
        else:
            super().handlemessage(msg)


class BomberBot(SpazBot):
    """A bot that throws regular bombs and occasionally punches.

    category: Bot Classes
    """
    character = 'Spaz'
    punchiness = 0.3


class BomberBotLite(BomberBot):
    """A less aggressive yellow version of ba.BomberBot.

    category: Bot Classes
    """
    color = LITE_BOT_COLOR
    highlight = LITE_BOT_HIGHLIGHT
    punchiness = 0.2
    throw_rate = 0.7
    throwiness = 0.1
    charge_speed_min = 0.6
    charge_speed_max = 0.6


class BomberBotStaticLite(BomberBotLite):
    """A less aggressive generally immobile weak version of ba.BomberBot.

    category: Bot Classes
    """
    static = True
    throw_dist_min = 0.0


class BomberBotStatic(BomberBot):
    """A version of ba.BomberBot who generally stays in one place.

    category: Bot Classes
    """
    static = True
    throw_dist_min = 0.0


class BomberBotPro(BomberBot):
    """A more powerful version of ba.BomberBot.

    category: Bot Classes
    """
    points_mult = 2
    color = PRO_BOT_COLOR
    highlight = PRO_BOT_HIGHLIGHT
    default_bomb_count = 3
    default_boxing_gloves = True
    punchiness = 0.7
    throw_rate = 1.3
    run = True
    run_dist_min = 6.0


class BomberBotProShielded(BomberBotPro):
    """A more powerful version of ba.BomberBot who starts with shields.

    category: Bot Classes
    """
    points_mult = 3
    default_shields = True


class BomberBotProStatic(BomberBotPro):
    """A more powerful ba.BomberBot who generally stays in one place.

    category: Bot Classes
    """
    static = True
    throw_dist_min = 0.0


class BomberBotProStaticShielded(BomberBotProShielded):
    """A powerful ba.BomberBot with shields who is generally immobile.

    category: Bot Classes
    """
    static = True
    throw_dist_min = 0.0


class BrawlerBot(SpazBot):
    """A bot who walks and punches things.

    category: Bot Classes
    """
    character = 'Kronk'
    punchiness = 0.9
    charge_dist_max = 9999.0
    charge_speed_min = 1.0
    charge_speed_max = 1.0
    throw_dist_min = 9999
    throw_dist_max = 9999


class BrawlerBotLite(BrawlerBot):
    """A weaker version of ba.BrawlerBot.

    category: Bot Classes
    """
    color = LITE_BOT_COLOR
    highlight = LITE_BOT_HIGHLIGHT
    punchiness = 0.3
    charge_speed_min = 0.6
    charge_speed_max = 0.6


class BrawlerBotPro(BrawlerBot):
    """A stronger version of ba.BrawlerBot.

    category: Bot Classes
    """
    color = PRO_BOT_COLOR
    highlight = PRO_BOT_HIGHLIGHT
    run = True
    run_dist_min = 4.0
    default_boxing_gloves = True
    punchiness = 0.95
    points_mult = 2


class BrawlerBotProShielded(BrawlerBotPro):
    """A stronger version of ba.BrawlerBot who starts with shields.

    category: Bot Classes
    """
    default_shields = True
    points_mult = 3


class ChargerBot(SpazBot):
    """A speedy melee attack bot.

    category: Bot Classes
    """

    character = 'Snake Shadow'
    punchiness = 1.0
    run = True
    charge_dist_min = 10.0
    charge_dist_max = 9999.0
    charge_speed_min = 1.0
    charge_speed_max = 1.0
    throw_dist_min = 9999
    throw_dist_max = 9999
    points_mult = 2


class BouncyBot(SpazBot):
    """A speedy attacking melee bot that jumps constantly.

    category: Bot Classes
    """

    color = (1, 1, 1)
    highlight = (1.0, 0.5, 0.5)
    character = 'Easter Bunny'
    punchiness = 1.0
    run = True
    bouncy = True
    default_boxing_gloves = True
    charge_dist_min = 10.0
    charge_dist_max = 9999.0
    charge_speed_min = 1.0
    charge_speed_max = 1.0
    throw_dist_min = 9999
    throw_dist_max = 9999
    points_mult = 2


class ChargerBotPro(ChargerBot):
    """A stronger ba.ChargerBot.

    category: Bot Classes
    """
    color = PRO_BOT_COLOR
    highlight = PRO_BOT_HIGHLIGHT
    default_shields = True
    default_boxing_gloves = True
    points_mult = 3


class ChargerBotProShielded(ChargerBotPro):
    """A stronger ba.ChargerBot who starts with shields.

    category: Bot Classes
    """
    default_shields = True
    points_mult = 4


class TriggerBot(SpazBot):
    """A slow moving bot with trigger bombs.

    category: Bot Classes
    """
    character = 'Zoe'
    punchiness = 0.75
    throwiness = 0.7
    charge_dist_max = 1.0
    charge_speed_min = 0.3
    charge_speed_max = 0.5
    throw_dist_min = 3.5
    throw_dist_max = 5.5
    default_bomb_type = 'impact'
    points_mult = 2


class TriggerBotStatic(TriggerBot):
    """A ba.TriggerBot who generally stays in one place.

    category: Bot Classes
    """
    static = True
    throw_dist_min = 0.0


class TriggerBotPro(TriggerBot):
    """A stronger version of ba.TriggerBot.

    category: Bot Classes
    """
    color = PRO_BOT_COLOR
    highlight = PRO_BOT_HIGHLIGHT
    default_bomb_count = 3
    default_boxing_gloves = True
    charge_speed_min = 1.0
    charge_speed_max = 1.0
    punchiness = 0.9
    throw_rate = 1.3
    run = True
    run_dist_min = 6.0
    points_mult = 3


class TriggerBotProShielded(TriggerBotPro):
    """A stronger version of ba.TriggerBot who starts with shields.

    category: Bot Classes
    """
    default_shields = True
    points_mult = 4


class StickyBot(SpazBot):
    """A crazy bot who runs and throws sticky bombs.

    category: Bot Classes
    """
    character = 'Mel'
    punchiness = 0.9
    throwiness = 1.0
    run = True
    charge_dist_min = 4.0
    charge_dist_max = 10.0
    charge_speed_min = 1.0
    charge_speed_max = 1.0
    throw_dist_min = 0.0
    throw_dist_max = 4.0
    throw_rate = 2.0
    default_bomb_type = 'sticky'
    default_bomb_count = 3
    points_mult = 3


class StickyBotStatic(StickyBot):
    """A crazy bot who throws sticky-bombs but generally stays in one place.

    category: Bot Classes
    """
    static = True


class ExplodeyBot(SpazBot):
    """A bot who runs and explodes in 5 seconds.

    category: Bot Classes
    """
    character = 'Jack Morgan'
    run = True
    charge_dist_min = 0.0
    charge_dist_max = 9999
    charge_speed_min = 1.0
    charge_speed_max = 1.0
    throw_dist_min = 9999
    throw_dist_max = 9999
    start_cursed = True
    points_mult = 4


class ExplodeyBotNoTimeLimit(ExplodeyBot):
    """A bot who runs but does not explode on his own.

    category: Bot Classes
    """
    curse_time = None


class ExplodeyBotShielded(ExplodeyBot):
    """A ba.ExplodeyBot who starts with shields.

    category: Bot Classes
    """
    default_shields = True
    points_mult = 5


class SpazBotSet:
    """A container/controller for one or more ba.SpazBots.

    category: Bot Classes
    """

    def __init__(self) -> None:
        """Create a bot-set."""

        # We spread our bots out over a few lists so we can update
        # them in a staggered fashion.
        self._bot_list_count = 5
        self._bot_add_list = 0
        self._bot_update_list = 0
        self._bot_lists: List[List[SpazBot]] = [
            [] for _ in range(self._bot_list_count)
        ]
        self._spawn_sound = ba.getsound('spawn')
        self._spawning_count = 0
        self._bot_update_timer: Optional[ba.Timer] = None
        self.start_moving()

    def __del__(self) -> None:
        self.clear()

    def spawn_bot(self,
                  bot_type: Type[SpazBot],
                  pos: Sequence[float],
                  spawn_time: float = 3.0,
                  on_spawn_call: Callable[[SpazBot], Any] = None) -> None:
        """Spawn a bot from this set."""
        from bastd.actor import spawner
        spawner.Spawner(pt=pos,
                        spawn_time=spawn_time,
                        send_spawn_message=False,
                        spawn_callback=ba.Call(self._spawn_bot, bot_type, pos,
                                               on_spawn_call))
        self._spawning_count += 1

    def _spawn_bot(self, bot_type: Type[SpazBot], pos: Sequence[float],
                   on_spawn_call: Optional[Callable[[SpazBot], Any]]) -> None:
        spaz = bot_type()
        ba.playsound(self._spawn_sound, position=pos)
        assert spaz.node
        spaz.node.handlemessage('flash')
        spaz.node.is_area_of_interest = False
        spaz.handlemessage(ba.StandMessage(pos, random.uniform(0, 360)))
        self.add_bot(spaz)
        self._spawning_count -= 1
        if on_spawn_call is not None:
            on_spawn_call(spaz)

    def have_living_bots(self) -> bool:
        """Return whether any bots in the set are alive or spawning."""
        return (self._spawning_count > 0
                or any(any(b.is_alive() for b in l) for l in self._bot_lists))

    def get_living_bots(self) -> List[SpazBot]:
        """Get the living bots in the set."""
        bots: List[SpazBot] = []
        for botlist in self._bot_lists:
            for bot in botlist:
                if bot.is_alive():
                    bots.append(bot)
        return bots

    def _update(self) -> None:

        # Update one of our bot lists each time through.
        # First off, remove no-longer-existing bots from the list.
        try:
            bot_list = self._bot_lists[self._bot_update_list] = ([
                b for b in self._bot_lists[self._bot_update_list] if b
            ])
        except Exception:
            bot_list = []
            ba.print_exception('Error updating bot list: ' +
                               str(self._bot_lists[self._bot_update_list]))
        self._bot_update_list = (self._bot_update_list +
                                 1) % self._bot_list_count

        # Update our list of player points for the bots to use.
        player_pts = []
        for player in ba.getactivity().players:
            assert isinstance(player, ba.Player)
            try:
                # TODO: could use abstracted player.position here so we
                # don't have to assume their actor type, but we have no
                # abstracted velocity as of yet.
                if player.is_alive():
                    assert isinstance(player.actor, Spaz)
                    assert player.actor.node
                    player_pts.append((ba.Vec3(player.actor.node.position),
                                       ba.Vec3(player.actor.node.velocity)))
            except Exception:
                ba.print_exception('Error on bot-set _update.')

        for bot in bot_list:
            bot.set_player_points(player_pts)
            bot.update_ai()

    def clear(self) -> None:
        """Immediately clear out any bots in the set."""

        # Don't do this if the activity is shutting down or dead.
        activity = ba.getactivity(doraise=False)
        if activity is None or activity.expired:
            return

        for i in range(len(self._bot_lists)):
            for bot in self._bot_lists[i]:
                bot.handlemessage(ba.DieMessage(immediate=True))
            self._bot_lists[i] = []

    def start_moving(self) -> None:
        """Start processing bot AI updates so they start doing their thing."""
        self._bot_update_timer = ba.Timer(0.05,
                                          ba.WeakCall(self._update),
                                          repeat=True)

    def stop_moving(self) -> None:
        """Tell all bots to stop moving and stops updating their AI.

        Useful when players have won and you want the
        enemy bots to just stand and look bewildered.
        """
        self._bot_update_timer = None
        for botlist in self._bot_lists:
            for bot in botlist:
                if bot.node:
                    bot.node.move_left_right = 0
                    bot.node.move_up_down = 0

    def celebrate(self, duration: float) -> None:
        """Tell all living bots in the set to celebrate momentarily.

        Duration is given in seconds.
        """
        msg = ba.CelebrateMessage(duration=duration)
        for botlist in self._bot_lists:
            for bot in botlist:
                if bot:
                    bot.handlemessage(msg)

    def final_celebrate(self) -> None:
        """Tell all bots in the set to stop what they were doing and celebrate.

        Use this when the bots have won a game.
        """
        self._bot_update_timer = None

        # At this point stop doing anything but jumping and celebrating.
        for botlist in self._bot_lists:
            for bot in botlist:
                if bot:
                    assert bot.node  # (should exist if 'if bot' was True)
                    bot.node.move_left_right = 0
                    bot.node.move_up_down = 0
                    ba.timer(0.5 * random.random(),
                             ba.Call(bot.handlemessage, ba.CelebrateMessage()))
                    jump_duration = random.randrange(400, 500)
                    j = random.randrange(0, 200)
                    for _i in range(10):
                        bot.node.jump_pressed = True
                        bot.node.jump_pressed = False
                        j += jump_duration
                    ba.timer(random.uniform(0.0, 1.0),
                             ba.Call(bot.node.handlemessage, 'attack_sound'))
                    ba.timer(random.uniform(1.0, 2.0),
                             ba.Call(bot.node.handlemessage, 'attack_sound'))
                    ba.timer(random.uniform(2.0, 3.0),
                             ba.Call(bot.node.handlemessage, 'attack_sound'))

    def add_bot(self, bot: SpazBot) -> None:
        """Add a ba.SpazBot instance to the set."""
        self._bot_lists[self._bot_add_list].append(bot)
        self._bot_add_list = (self._bot_add_list + 1) % self._bot_list_count
