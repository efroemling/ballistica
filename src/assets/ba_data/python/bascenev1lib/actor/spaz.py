# Released under the MIT License. See LICENSE for details.
#
"""Defines the spaz actor."""
# pylint: disable=too-many-lines

from __future__ import annotations

import random
import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.bomb import Bomb, Blast
from bascenev1lib.actor.powerupbox import PowerupBoxFactory, PowerupBox
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable

POWERUP_WEAR_OFF_TIME = 20000

# Obsolete - just used for demo guy now.
BASE_PUNCH_POWER_SCALE = 1.2
BASE_PUNCH_COOLDOWN = 400


class PickupMessage:
    """We wanna pick something up."""


class PunchHitMessage:
    """Message saying an object was hit."""


class CurseExplodeMessage:
    """We are cursed and should blow up now."""


class BombDiedMessage:
    """A bomb has died and thus can be recycled."""


class Spaz(bs.Actor):
    """
    Base class for various Spazzes.

    A Spaz is the standard little humanoid character in the game.
    It can be controlled by a player or by AI, and can have
    various different appearances.  The name 'Spaz' is not to be
    confused with the 'Spaz' character in the game, which is just
    one of the skins available for instances of this class.
    """

    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-locals

    node: bs.Node
    """The 'spaz' bs.Node."""

    points_mult = 1
    curse_time: float | None = 5.0
    default_bomb_count = 1
    default_bomb_type = 'normal'
    default_boxing_gloves = False
    default_shields = False
    default_hitpoints = 1000

    def __init__(
        self,
        *,
        color: Sequence[float] = (1.0, 1.0, 1.0),
        highlight: Sequence[float] = (0.5, 0.5, 0.5),
        character: str = 'Spaz',
        source_player: bs.Player | None = None,
        start_invincible: bool = True,
        can_accept_powerups: bool = True,
        powerups_expire: bool = False,
        demo_mode: bool = False,
    ):
        """Create a spaz with the requested color, character, etc."""
        # pylint: disable=too-many-statements

        super().__init__()
        shared = SharedObjects.get()
        activity = self.activity

        factory = SpazFactory.get()

        # We need to behave slightly different in the tutorial.
        self._demo_mode = demo_mode

        self.play_big_death_sound = False

        # Scales how much impacts affect us (most damage calcs).
        self.impact_scale = 1.0

        self.source_player = source_player
        self._dead = False
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = BASE_PUNCH_POWER_SCALE
        else:
            self._punch_power_scale = factory.punch_power_scale
        self.fly = bs.getactivity().globalsnode.happy_thoughts_mode
        if isinstance(activity, bs.GameActivity):
            self._hockey = activity.map.is_hockey
        else:
            self._hockey = False
        self._punched_nodes: set[bs.Node] = set()
        self._cursed = False
        self._connected_to_player: bs.Player | None = None
        materials = [
            factory.spaz_material,
            shared.object_material,
            shared.player_material,
        ]
        roller_materials = [factory.roller_material, shared.player_material]
        extras_material = []

        if can_accept_powerups:
            pam = PowerupBoxFactory.get().powerup_accept_material
            materials.append(pam)
            roller_materials.append(pam)
            extras_material.append(pam)

        media = factory.get_media(character)
        punchmats = (factory.punch_material, shared.attack_material)
        pickupmats = (factory.pickup_material, shared.pickup_material)
        self.node: bs.Node = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': color,
                'behavior_version': 0 if demo_mode else 1,
                'demo_mode': demo_mode,
                'highlight': highlight,
                'jump_sounds': media['jump_sounds'],
                'attack_sounds': media['attack_sounds'],
                'impact_sounds': media['impact_sounds'],
                'death_sounds': media['death_sounds'],
                'pickup_sounds': media['pickup_sounds'],
                'fall_sounds': media['fall_sounds'],
                'color_texture': media['color_texture'],
                'color_mask_texture': media['color_mask_texture'],
                'head_mesh': media['head_mesh'],
                'torso_mesh': media['torso_mesh'],
                'pelvis_mesh': media['pelvis_mesh'],
                'upper_arm_mesh': media['upper_arm_mesh'],
                'forearm_mesh': media['forearm_mesh'],
                'hand_mesh': media['hand_mesh'],
                'upper_leg_mesh': media['upper_leg_mesh'],
                'lower_leg_mesh': media['lower_leg_mesh'],
                'toes_mesh': media['toes_mesh'],
                'style': factory.get_style(character),
                'fly': self.fly,
                'hockey': self._hockey,
                'materials': materials,
                'roller_materials': roller_materials,
                'extras_material': extras_material,
                'punch_materials': punchmats,
                'pickup_materials': pickupmats,
                'invincible': start_invincible,
                'source_player': source_player,
            },
        )
        self.shield: bs.Node | None = None

        if start_invincible:

            def _safesetattr(node: bs.Node | None, attr: str, val: Any) -> None:
                if node:
                    setattr(node, attr, val)

            bs.timer(1.0, bs.Call(_safesetattr, self.node, 'invincible', False))
        self.hitpoints = self.default_hitpoints
        self.hitpoints_max = self.default_hitpoints
        self.shield_hitpoints: int | None = None
        self.shield_hitpoints_max = 650
        self.shield_decay_rate = 0
        self.shield_decay_timer: bs.Timer | None = None
        self._boxing_gloves_wear_off_timer: bs.Timer | None = None
        self._boxing_gloves_wear_off_flash_timer: bs.Timer | None = None
        self._bomb_wear_off_timer: bs.Timer | None = None
        self._bomb_wear_off_flash_timer: bs.Timer | None = None
        self._multi_bomb_wear_off_timer: bs.Timer | None = None
        self._multi_bomb_wear_off_flash_timer: bs.Timer | None = None
        self._curse_timer: bs.Timer | None = None
        self.bomb_count = self.default_bomb_count
        self._max_bomb_count = self.default_bomb_count
        self.bomb_type_default = self.default_bomb_type
        self.bomb_type = self.bomb_type_default
        self.land_mine_count = 0
        self.blast_radius = 2.0
        self.powerups_expire = powerups_expire
        if self._demo_mode:  # Preserve old behavior.
            self._punch_cooldown = BASE_PUNCH_COOLDOWN
        else:
            self._punch_cooldown = factory.punch_cooldown
        self._jump_cooldown = 250
        self._pickup_cooldown = 0
        self._bomb_cooldown = 0
        self._has_boxing_gloves = False
        if self.default_boxing_gloves:
            self.equip_boxing_gloves()
        self.last_punch_time_ms = -9999
        self.last_pickup_time_ms = -9999
        self.last_jump_time_ms = -9999
        self.last_run_time_ms = -9999
        self._last_run_value = 0.0
        self.last_bomb_time_ms = -9999
        self._turbo_filter_times: dict[str, int] = {}
        self._turbo_filter_time_bucket = 0
        self._turbo_filter_counts: dict[str, int] = {}
        self.frozen = False
        self.shattered = False
        self._last_hit_time: int | None = None
        self._num_times_hit = 0
        self._bomb_held = False
        if self.default_shields:
            self.equip_shields()
        self._dropped_bomb_callbacks: list[Callable[[Spaz, bs.Actor], Any]] = []

        self._score_text: bs.Node | None = None
        self._score_text_hide_timer: bs.Timer | None = None
        self._last_stand_pos: Sequence[float] | None = None

        # Deprecated stuff.. should make these into lists.
        self.punch_callback: Callable[[Spaz], Any] | None = None
        self.pick_up_powerup_callback: Callable[[Spaz], Any] | None = None

    @override
    def exists(self) -> bool:
        return bool(self.node)

    @override
    def on_expire(self) -> None:
        super().on_expire()

        # Release callbacks/refs so we don't wind up with dependency loops.
        self._dropped_bomb_callbacks = []
        self.punch_callback = None
        self.pick_up_powerup_callback = None

    def add_dropped_bomb_callback(
        self, call: Callable[[Spaz, bs.Actor], Any]
    ) -> None:
        """
        Add a call to be run whenever this Spaz drops a bomb.
        The spaz and the newly-dropped bomb are passed as arguments.
        """
        assert not self.expired
        self._dropped_bomb_callbacks.append(call)

    @override
    def is_alive(self) -> bool:
        """
        Method override; returns whether ol' spaz is still kickin'.
        """
        return not self._dead

    def _hide_score_text(self) -> None:
        if self._score_text:
            assert isinstance(self._score_text.scale, float)
            bs.animate(
                self._score_text,
                'scale',
                {0.0: self._score_text.scale, 0.2: 0.0},
            )

    def _turbo_filter_add_press(self, source: str) -> None:
        """
        Can pass all button presses through here; if we see an obscene number
        of them in a short time let's shame/pushish this guy for using turbo.
        """
        t_ms = int(bs.basetime() * 1000.0)
        assert isinstance(t_ms, int)
        t_bucket = int(t_ms / 1000)
        if t_bucket == self._turbo_filter_time_bucket:
            # Add only once per timestep (filter out buttons triggering
            # multiple actions).
            if t_ms != self._turbo_filter_times.get(source, 0):
                self._turbo_filter_counts[source] = (
                    self._turbo_filter_counts.get(source, 0) + 1
                )
                self._turbo_filter_times[source] = t_ms
                # (uncomment to debug; prints what this count is at)
                # bs.broadcastmessage( str(source) + " "
                #                   + str(self._turbo_filter_counts[source]))
                if self._turbo_filter_counts[source] == 15:
                    # Knock 'em out.  That'll learn 'em.
                    assert self.node
                    self.node.handlemessage('knockout', 500.0)

                    # Also issue periodic notices about who is turbo-ing.
                    now = bs.apptime()
                    assert bs.app.classic is not None
                    if now > bs.app.classic.last_spaz_turbo_warn_time + 30.0:
                        bs.app.classic.last_spaz_turbo_warn_time = now
                        bs.broadcastmessage(
                            bs.Lstr(
                                translate=(
                                    'statements',
                                    (
                                        'Warning to ${NAME}:  '
                                        'turbo / button-spamming knocks'
                                        ' you out.'
                                    ),
                                ),
                                subs=[('${NAME}', self.node.name)],
                            ),
                            color=(1, 0.5, 0),
                        )
                        bs.getsound('error').play()
        else:
            self._turbo_filter_times = {}
            self._turbo_filter_time_bucket = t_bucket
            self._turbo_filter_counts = {source: 1}

    def set_score_text(
        self,
        text: str | bs.Lstr,
        color: Sequence[float] = (1.0, 1.0, 0.4),
        flash: bool = False,
    ) -> None:
        """
        Utility func to show a message momentarily over our spaz that follows
        him around; Handy for score updates and things.
        """
        color_fin = bs.safecolor(color)[:3]
        if not self.node:
            return
        if not self._score_text:
            start_scale = 0.0
            mnode = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.4, 0), 'operation': 'add'},
            )
            self.node.connectattr('torso_position', mnode, 'input2')
            self._score_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': text,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': color_fin,
                    'scale': 0.02,
                    'h_align': 'center',
                },
            )
            mnode.connectattr('output', self._score_text, 'position')
        else:
            self._score_text.color = color_fin
            assert isinstance(self._score_text.scale, float)
            start_scale = self._score_text.scale
            self._score_text.text = text
        if flash:
            combine = bs.newnode(
                'combine', owner=self._score_text, attrs={'size': 3}
            )
            scl = 1.8
            offs = 0.5
            tval = 0.300
            for i in range(3):
                cl1 = offs + scl * color_fin[i]
                cl2 = color_fin[i]
                bs.animate(
                    combine,
                    'input' + str(i),
                    {0.5 * tval: cl2, 0.75 * tval: cl1, 1.0 * tval: cl2},
                )
            combine.connectattr('output', self._score_text, 'color')

        bs.animate(self._score_text, 'scale', {0.0: start_scale, 0.2: 0.02})
        self._score_text_hide_timer = bs.Timer(
            1.0, bs.WeakCall(self._hide_score_text)
        )

    def on_jump_press(self) -> None:
        """
        Called to 'press jump' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_jump_time_ms >= self._jump_cooldown:
            self.node.jump_pressed = True
            self.last_jump_time_ms = t_ms
        self._turbo_filter_add_press('jump')

    def on_jump_release(self) -> None:
        """
        Called to 'release jump' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        self.node.jump_pressed = False

    def on_pickup_press(self) -> None:
        """
        Called to 'press pick-up' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_pickup_time_ms >= self._pickup_cooldown:
            self.node.pickup_pressed = True
            self.last_pickup_time_ms = t_ms
        self._turbo_filter_add_press('pickup')

    def on_pickup_release(self) -> None:
        """
        Called to 'release pick-up' on this spaz;
        used by player or AI connections.
        """
        if not self.node:
            return
        self.node.pickup_pressed = False

    def on_hold_position_press(self) -> None:
        """
        Called to 'press hold-position' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.hold_position_pressed = True
        self._turbo_filter_add_press('holdposition')

    def on_hold_position_release(self) -> None:
        """
        Called to 'release hold-position' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.hold_position_pressed = False

    def on_punch_press(self) -> None:
        """
        Called to 'press punch' on this spaz;
        used for player or AI connections.
        """
        if not self.node or self.frozen or self.node.knockout > 0.0:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_punch_time_ms >= self._punch_cooldown:
            if self.punch_callback is not None:
                self.punch_callback(self)
            self._punched_nodes = set()  # Reset this.
            self.last_punch_time_ms = t_ms
            self.node.punch_pressed = True
            if not self.node.hold_node:
                bs.timer(
                    0.1,
                    bs.WeakCall(
                        self._safe_play_sound,
                        SpazFactory.get().swish_sound,
                        0.8,
                    ),
                )
        self._turbo_filter_add_press('punch')

    def _safe_play_sound(self, sound: bs.Sound, volume: float) -> None:
        """Plays a sound at our position if we exist."""
        if self.node:
            sound.play(volume, self.node.position)

    def on_punch_release(self) -> None:
        """
        Called to 'release punch' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.punch_pressed = False

    def on_bomb_press(self) -> None:
        """
        Called to 'press bomb' on this spaz;
        used for player or AI connections.
        """
        if (
            not self.node
            or self._dead
            or self.frozen
            or self.node.knockout > 0.0
        ):
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.last_bomb_time_ms >= self._bomb_cooldown:
            self.last_bomb_time_ms = t_ms
            self.node.bomb_pressed = True
            if not self.node.hold_node:
                self.drop_bomb()
        self._turbo_filter_add_press('bomb')

    def on_bomb_release(self) -> None:
        """
        Called to 'release bomb' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.bomb_pressed = False

    def on_run(self, value: float) -> None:
        """
        Called to 'press run' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        self.last_run_time_ms = t_ms
        self.node.run = value

        # Filtering these events would be tough since its an analog
        # value, but lets still pass full 0-to-1 presses along to
        # the turbo filter to punish players if it looks like they're turbo-ing.
        if self._last_run_value < 0.01 and value > 0.99:
            self._turbo_filter_add_press('run')

        self._last_run_value = value

    def on_fly_press(self) -> None:
        """
        Called to 'press fly' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        # Not adding a cooldown time here for now; slightly worried
        # input events get clustered up during net-games and we'd wind up
        # killing a lot and making it hard to fly.. should look into this.
        self.node.fly_pressed = True
        self._turbo_filter_add_press('fly')

    def on_fly_release(self) -> None:
        """
        Called to 'release fly' on this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.fly_pressed = False

    def on_move(self, x: float, y: float) -> None:
        """
        Called to set the joystick amount for this spaz;
        used for player or AI connections.
        """
        if not self.node:
            return
        self.node.handlemessage('move', x, y)

    def on_move_up_down(self, value: float) -> None:
        """
        Called to set the up/down joystick amount on this spaz;
        used for player or AI connections.
        value will be between -32768 to 32767
        WARNING: deprecated; use on_move instead.
        """
        if not self.node:
            return
        self.node.move_up_down = value

    def on_move_left_right(self, value: float) -> None:
        """
        Called to set the left/right joystick amount on this spaz;
        used for player or AI connections.
        value will be between -32768 to 32767
        WARNING: deprecated; use on_move instead.
        """
        if not self.node:
            return
        self.node.move_left_right = value

    def on_punched(self, damage: int) -> None:
        """Called when this spaz gets punched."""

    def get_death_points(self, how: bs.DeathType) -> tuple[int, int]:
        """Get the points awarded for killing this spaz."""
        del how  # Unused.
        num_hits = float(max(1, self._num_times_hit))

        # Base points is simply 10 for 1-hit-kills and 5 otherwise.
        importance = 2 if num_hits < 2 else 1
        return (10 if num_hits < 2 else 5) * self.points_mult, importance

    def curse(self) -> None:
        """
        Give this poor spaz a curse;
        he will explode in 5 seconds.
        """
        if not self._cursed:
            factory = SpazFactory.get()
            self._cursed = True

            # Add the curse material.
            for attr in ['materials', 'roller_materials']:
                materials = getattr(self.node, attr)
                if factory.curse_material not in materials:
                    setattr(
                        self.node, attr, materials + (factory.curse_material,)
                    )

            # None specifies no time limit.
            assert self.node
            if self.curse_time is None:
                self.node.curse_death_time = -1
            else:
                # Note: curse-death-time takes milliseconds.
                tval = bs.time()
                assert isinstance(tval, (float, int))
                self.node.curse_death_time = int(
                    1000.0 * (tval + self.curse_time)
                )
                self._curse_timer = bs.Timer(
                    self.curse_time,
                    bs.WeakCall(self.handlemessage, CurseExplodeMessage()),
                )

    def equip_boxing_gloves(self) -> None:
        """
        Give this spaz some boxing gloves.
        """
        assert self.node
        self.node.boxing_gloves = True
        self._has_boxing_gloves = True
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 1.7
            self._punch_cooldown = 300
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = factory.punch_power_scale_gloves
            self._punch_cooldown = factory.punch_cooldown_gloves

    def equip_shields(self, decay: bool = False) -> None:
        """
        Give this spaz a nice energy shield.
        """

        if not self.node:
            logging.exception('Can\'t equip shields; no node.')
            return

        factory = SpazFactory.get()
        if self.shield is None:
            self.shield = bs.newnode(
                'shield',
                owner=self.node,
                attrs={'color': (0.3, 0.2, 2.0), 'radius': 1.3},
            )
            self.node.connectattr('position_center', self.shield, 'position')
        self.shield_hitpoints = self.shield_hitpoints_max = 650
        self.shield_decay_rate = factory.shield_decay_rate if decay else 0
        self.shield.hurt = 0
        factory.shield_up_sound.play(1.0, position=self.node.position)

        if self.shield_decay_rate > 0:
            self.shield_decay_timer = bs.Timer(
                0.5, bs.WeakCall(self.shield_decay), repeat=True
            )
            # So user can see the decay.
            self.shield.always_show_health_bar = True

    def shield_decay(self) -> None:
        """Called repeatedly to decay shield HP over time."""
        if self.shield:
            assert self.shield_hitpoints is not None
            self.shield_hitpoints = max(
                0, self.shield_hitpoints - self.shield_decay_rate
            )
            assert self.shield_hitpoints is not None
            self.shield.hurt = (
                1.0 - float(self.shield_hitpoints) / self.shield_hitpoints_max
            )
            if self.shield_hitpoints <= 0:
                self.shield.delete()
                self.shield = None
                self.shield_decay_timer = None
                assert self.node
                SpazFactory.get().shield_down_sound.play(
                    1.0,
                    position=self.node.position,
                )
        else:
            self.shield_decay_timer = None

    @override
    def handlemessage(self, msg: Any) -> Any:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        assert not self.expired

        if isinstance(msg, bs.PickedUpMessage):
            if self.node:
                self.node.handlemessage('hurt_sound')
                self.node.handlemessage('picked_up')

            # This counts as a hit.
            self._num_times_hit += 1

        elif isinstance(msg, bs.ShouldShatterMessage):
            # Eww; seems we have to do this in a timer or it wont work right.
            # (since we're getting called from within update() perhaps?..)
            # NOTE: should test to see if that's still the case.
            bs.timer(0.001, bs.WeakCall(self.shatter))

        elif isinstance(msg, bs.ImpactDamageMessage):
            # Eww; seems we have to do this in a timer or it wont work right.
            # (since we're getting called from within update() perhaps?..)
            bs.timer(0.001, bs.WeakCall(self._hit_self, msg.intensity))

        elif isinstance(msg, bs.PowerupMessage):
            if self._dead or not self.node:
                return True
            if self.pick_up_powerup_callback is not None:
                self.pick_up_powerup_callback(self)
            if msg.poweruptype == 'triple_bombs':
                tex = PowerupBoxFactory.get().tex_bomb
                self._flash_billboard(tex)
                self.set_bomb_count(3)
                if self.powerups_expire:
                    self.node.mini_billboard_1_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_1_start_time = t_ms
                    self.node.mini_billboard_1_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._multi_bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._multi_bomb_wear_off_flash),
                    )
                    self._multi_bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._multi_bomb_wear_off),
                    )
            elif msg.poweruptype == 'land_mines':
                self.set_land_mine_count(min(self.land_mine_count + 3, 3))
            elif msg.poweruptype == 'impact_bombs':
                self.bomb_type = 'impact'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'sticky_bombs':
                self.bomb_type = 'sticky'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'punch':
                tex = PowerupBoxFactory.get().tex_punch
                self._flash_billboard(tex)
                self.equip_boxing_gloves()
                if self.powerups_expire and not self.default_boxing_gloves:
                    self.node.boxing_gloves_flashing = False
                    self.node.mini_billboard_3_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_3_start_time = t_ms
                    self.node.mini_billboard_3_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._boxing_gloves_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._gloves_wear_off_flash),
                    )
                    self._boxing_gloves_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._gloves_wear_off),
                    )
            elif msg.poweruptype == 'shield':
                factory = SpazFactory.get()

                # Let's allow powerup-equipped shields to lose hp over time.
                self.equip_shields(decay=factory.shield_decay_rate > 0)
            elif msg.poweruptype == 'curse':
                self.curse()
            elif msg.poweruptype == 'ice_bombs':
                self.bomb_type = 'ice'
                tex = self._get_bomb_type_tex()
                self._flash_billboard(tex)
                if self.powerups_expire:
                    self.node.mini_billboard_2_texture = tex
                    t_ms = int(bs.time() * 1000.0)
                    assert isinstance(t_ms, int)
                    self.node.mini_billboard_2_start_time = t_ms
                    self.node.mini_billboard_2_end_time = (
                        t_ms + POWERUP_WEAR_OFF_TIME
                    )
                    self._bomb_wear_off_flash_timer = bs.Timer(
                        (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                        bs.WeakCall(self._bomb_wear_off_flash),
                    )
                    self._bomb_wear_off_timer = bs.Timer(
                        POWERUP_WEAR_OFF_TIME / 1000.0,
                        bs.WeakCall(self._bomb_wear_off),
                    )
            elif msg.poweruptype == 'health':
                if self._cursed:
                    self._cursed = False

                    # Remove cursed material.
                    factory = SpazFactory.get()
                    for attr in ['materials', 'roller_materials']:
                        materials = getattr(self.node, attr)
                        if factory.curse_material in materials:
                            setattr(
                                self.node,
                                attr,
                                tuple(
                                    m
                                    for m in materials
                                    if m != factory.curse_material
                                ),
                            )
                    self.node.curse_death_time = 0
                self.hitpoints = self.hitpoints_max
                self._flash_billboard(PowerupBoxFactory.get().tex_health)
                self.node.hurt = 0
                self._last_hit_time = None
                self._num_times_hit = 0

            self.node.handlemessage('flash')
            if msg.sourcenode:
                msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())
            return True

        elif isinstance(msg, bs.FreezeMessage):
            if not self.node:
                return None
            if self.node.invincible:
                SpazFactory.get().block_sound.play(
                    1.0,
                    position=self.node.position,
                )
                return None
            if self.shield:
                return None
            if not self.frozen:
                self.frozen = True
                self.node.frozen = True
                bs.timer(
                    msg.time, bs.WeakCall(self.handlemessage, bs.ThawMessage())
                )
                # Instantly shatter if we're already dead.
                # (otherwise its hard to tell we're dead).
                if self.hitpoints <= 0:
                    self.shatter()

        elif isinstance(msg, bs.ThawMessage):
            if self.frozen and not self.shattered and self.node:
                self.frozen = False
                self.node.frozen = False

        elif isinstance(msg, bs.HitMessage):
            if not self.node:
                return None
            if self.node.invincible:
                SpazFactory.get().block_sound.play(
                    1.0,
                    position=self.node.position,
                )
                return True

            # If we were recently hit, don't count this as another.
            # (so punch flurries and bomb pileups essentially count as 1 hit).
            local_time = int(bs.time() * 1000.0)
            assert isinstance(local_time, int)
            if (
                self._last_hit_time is None
                or local_time - self._last_hit_time > 1000
            ):
                self._num_times_hit += 1
                self._last_hit_time = local_time

            mag = msg.magnitude * self.impact_scale
            velocity_mag = msg.velocity_magnitude * self.impact_scale
            damage_scale = 0.22

            # If they've got a shield, deliver it to that instead.
            if self.shield:
                if msg.flat_damage:
                    damage = msg.flat_damage * self.impact_scale
                else:
                    # Hit our spaz with an impulse but tell it to only return
                    # theoretical damage; not apply the impulse.
                    assert msg.force_direction is not None
                    self.node.handlemessage(
                        'impulse',
                        msg.pos[0],
                        msg.pos[1],
                        msg.pos[2],
                        msg.velocity[0],
                        msg.velocity[1],
                        msg.velocity[2],
                        mag,
                        velocity_mag,
                        msg.radius,
                        1,
                        msg.force_direction[0],
                        msg.force_direction[1],
                        msg.force_direction[2],
                    )
                    damage = damage_scale * self.node.damage

                assert self.shield_hitpoints is not None
                self.shield_hitpoints -= int(damage)
                self.shield.hurt = (
                    1.0
                    - float(self.shield_hitpoints) / self.shield_hitpoints_max
                )

                # Its a cleaner event if a hit just kills the shield
                # without damaging the player.
                # However, massive damage events should still be able to
                # damage the player. This hopefully gives us a happy medium.
                max_spillover = SpazFactory.get().max_shield_spillover_damage
                if self.shield_hitpoints <= 0:
                    # FIXME: Transition out perhaps?
                    self.shield.delete()
                    self.shield = None
                    SpazFactory.get().shield_down_sound.play(
                        1.0,
                        position=self.node.position,
                    )

                    # Emit some cool looking sparks when the shield dies.
                    npos = self.node.position
                    bs.emitfx(
                        position=(npos[0], npos[1] + 0.9, npos[2]),
                        velocity=self.node.velocity,
                        count=random.randrange(20, 30),
                        scale=1.0,
                        spread=0.6,
                        chunk_type='spark',
                    )

                else:
                    SpazFactory.get().shield_hit_sound.play(
                        0.5,
                        position=self.node.position,
                    )

                # Emit some cool looking sparks on shield hit.
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 1.0,
                        msg.force_direction[1] * 1.0,
                        msg.force_direction[2] * 1.0,
                    ),
                    count=min(30, 5 + int(damage * 0.005)),
                    scale=0.5,
                    spread=0.3,
                    chunk_type='spark',
                )

                # If they passed our spillover threshold,
                # pass damage along to spaz.
                if self.shield_hitpoints <= -max_spillover:
                    leftover_damage = -max_spillover - self.shield_hitpoints
                    shield_leftover_ratio = leftover_damage / damage

                    # Scale down the magnitudes applied to spaz accordingly.
                    mag *= shield_leftover_ratio
                    velocity_mag *= shield_leftover_ratio
                else:
                    return True  # Good job shield!
            else:
                shield_leftover_ratio = 1.0

            if msg.flat_damage:
                damage = int(
                    msg.flat_damage * self.impact_scale * shield_leftover_ratio
                )
            else:
                # Hit it with an impulse and get the resulting damage.
                assert msg.force_direction is not None
                self.node.handlemessage(
                    'impulse',
                    msg.pos[0],
                    msg.pos[1],
                    msg.pos[2],
                    msg.velocity[0],
                    msg.velocity[1],
                    msg.velocity[2],
                    mag,
                    velocity_mag,
                    msg.radius,
                    0,
                    msg.force_direction[0],
                    msg.force_direction[1],
                    msg.force_direction[2],
                )

                damage = int(damage_scale * self.node.damage)
            self.node.handlemessage('hurt_sound')

            # Play punch impact sound based on damage if it was a punch.
            if msg.hit_type == 'punch':
                self.on_punched(damage)

                # If damage was significant, lets show it.
                if damage >= 350:
                    assert msg.force_direction is not None
                    bs.show_damage_count(
                        '-' + str(int(damage / 10)) + '%',
                        msg.pos,
                        msg.force_direction,
                        self._dead,
                    )

                # Let's always add in a super-punch sound with boxing
                # gloves just to differentiate them.
                if msg.hit_subtype == 'super_punch':
                    SpazFactory.get().punch_sound_stronger.play(
                        1.0,
                        position=self.node.position,
                    )
                if damage >= 500:
                    sounds = SpazFactory.get().punch_sound_strong
                    sound = sounds[random.randrange(len(sounds))]
                elif damage >= 100:
                    sound = SpazFactory.get().punch_sound
                else:
                    sound = SpazFactory.get().punch_sound_weak
                sound.play(1.0, position=self.node.position)

                # Throw up some chunks.
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 0.5,
                        msg.force_direction[1] * 0.5,
                        msg.force_direction[2] * 0.5,
                    ),
                    count=min(10, 1 + int(damage * 0.0025)),
                    scale=0.3,
                    spread=0.03,
                )

                bs.emitfx(
                    position=msg.pos,
                    chunk_type='sweat',
                    velocity=(
                        msg.force_direction[0] * 1.3,
                        msg.force_direction[1] * 1.3 + 5.0,
                        msg.force_direction[2] * 1.3,
                    ),
                    count=min(30, 1 + int(damage * 0.04)),
                    scale=0.9,
                    spread=0.28,
                )

                # Momentary flash.
                hurtiness = damage * 0.003
                punchpos = (
                    msg.pos[0] + msg.force_direction[0] * 0.02,
                    msg.pos[1] + msg.force_direction[1] * 0.02,
                    msg.pos[2] + msg.force_direction[2] * 0.02,
                )
                flash_color = (1.0, 0.8, 0.4)
                light = bs.newnode(
                    'light',
                    attrs={
                        'position': punchpos,
                        'radius': 0.12 + hurtiness * 0.12,
                        'intensity': 0.3 * (1.0 + 1.0 * hurtiness),
                        'height_attenuated': False,
                        'color': flash_color,
                    },
                )
                bs.timer(0.06, light.delete)

                flash = bs.newnode(
                    'flash',
                    attrs={
                        'position': punchpos,
                        'size': 0.17 + 0.17 * hurtiness,
                        'color': flash_color,
                    },
                )
                bs.timer(0.06, flash.delete)

            if msg.hit_type == 'impact':
                assert msg.force_direction is not None
                bs.emitfx(
                    position=msg.pos,
                    velocity=(
                        msg.force_direction[0] * 2.0,
                        msg.force_direction[1] * 2.0,
                        msg.force_direction[2] * 2.0,
                    ),
                    count=min(10, 1 + int(damage * 0.01)),
                    scale=0.4,
                    spread=0.1,
                )
            if self.hitpoints > 0:
                # It's kinda crappy to die from impacts, so lets reduce
                # impact damage by a reasonable amount *if* it'll keep us alive.
                if msg.hit_type == 'impact' and damage >= self.hitpoints:
                    # Drop damage to whatever puts us at 10 hit points,
                    # or 200 less than it used to be whichever is greater
                    # (so it *can* still kill us if its high enough).
                    newdamage = max(damage - 200, self.hitpoints - 10)
                    damage = newdamage
                self.node.handlemessage('flash')

                # If we're holding something, drop it.
                if damage > 0.0 and self.node.hold_node:
                    self.node.hold_node = None
                self.hitpoints -= damage
                self.node.hurt = (
                    1.0 - float(self.hitpoints) / self.hitpoints_max
                )

                # If we're cursed, *any* damage blows us up.
                if self._cursed and damage > 0:
                    bs.timer(
                        0.05,
                        bs.WeakCall(
                            self.curse_explode, msg.get_source_player(bs.Player)
                        ),
                    )

                # If we're frozen, shatter.. otherwise die if we hit zero
                if self.frozen and (damage > 200 or self.hitpoints <= 0):
                    self.shatter()
                elif self.hitpoints <= 0:
                    self.node.handlemessage(
                        bs.DieMessage(how=bs.DeathType.IMPACT)
                    )

            # If we're dead, take a look at the smoothed damage value
            # (which gives us a smoothed average of recent damage) and shatter
            # us if its grown high enough.
            if self.hitpoints <= 0:
                damage_avg = self.node.damage_smoothed * damage_scale
                if damage_avg >= 1000:
                    self.shatter()

        elif isinstance(msg, BombDiedMessage):
            self.bomb_count += 1

        elif isinstance(msg, bs.DieMessage):
            wasdead = self._dead
            self._dead = True
            self.hitpoints = 0
            if msg.immediate:
                if self.node:
                    self.node.delete()
            elif self.node:
                if not wasdead:
                    self.node.hurt = 1.0
                    if self.play_big_death_sound:
                        SpazFactory.get().single_player_death_sound.play()
                    self.node.dead = True
                    bs.timer(2.0, self.node.delete)

        elif isinstance(msg, bs.OutOfBoundsMessage):
            # By default we just die here.
            self.handlemessage(bs.DieMessage(how=bs.DeathType.FALL))

        elif isinstance(msg, bs.StandMessage):
            self._last_stand_pos = (
                msg.position[0],
                msg.position[1],
                msg.position[2],
            )
            if self.node:
                self.node.handlemessage(
                    'stand',
                    msg.position[0],
                    msg.position[1],
                    msg.position[2],
                    msg.angle,
                )

        elif isinstance(msg, CurseExplodeMessage):
            self.curse_explode()

        elif isinstance(msg, PunchHitMessage):
            if not self.node:
                return None
            node = bs.getcollision().opposingnode

            # Don't want to physically affect powerups.
            if node.getdelegate(PowerupBox):
                return None

            # Only allow one hit per node per punch.
            if node and (node not in self._punched_nodes):
                punch_momentum_angular = (
                    self.node.punch_momentum_angular * self._punch_power_scale
                )
                punch_power = self.node.punch_power * self._punch_power_scale

                # Ok here's the deal:  we pass along our base velocity for use
                # in the impulse damage calculations since that is a more
                # predictable value than our fist velocity, which is rather
                # erratic. However, we want to actually apply force in the
                # direction our fist is moving so it looks better. So we still
                # pass that along as a direction. Perhaps a time-averaged
                # fist-velocity would work too?.. perhaps should try that.

                # If its something besides another spaz, just do a muffled
                # punch sound.
                if node.getnodetype() != 'spaz':
                    sounds = SpazFactory.get().impact_sounds_medium
                    sound = sounds[random.randrange(len(sounds))]
                    sound.play(1.0, position=self.node.position)

                ppos = self.node.punch_position
                punchdir = self.node.punch_velocity
                vel = self.node.punch_momentum_linear

                self._punched_nodes.add(node)
                node.handlemessage(
                    bs.HitMessage(
                        pos=ppos,
                        velocity=vel,
                        magnitude=punch_power * punch_momentum_angular * 110.0,
                        velocity_magnitude=punch_power * 40,
                        radius=0,
                        srcnode=self.node,
                        source_player=self.source_player,
                        force_direction=punchdir,
                        hit_type='punch',
                        hit_subtype=(
                            'super_punch'
                            if self._has_boxing_gloves
                            else 'default'
                        ),
                    )
                )

                # Also apply opposite to ourself for the first punch only.
                # This is given as a constant force so that it is more
                # noticeable for slower punches where it matters. For fast
                # awesome looking punches its ok if we punch 'through'
                # the target.
                mag = -400.0
                if self._hockey:
                    mag *= 0.5
                if len(self._punched_nodes) == 1:
                    self.node.handlemessage(
                        'kick_back',
                        ppos[0],
                        ppos[1],
                        ppos[2],
                        punchdir[0],
                        punchdir[1],
                        punchdir[2],
                        mag,
                    )
        elif isinstance(msg, PickupMessage):
            if not self.node:
                return None

            try:
                collision = bs.getcollision()
                opposingnode = collision.opposingnode
                opposingbody = collision.opposingbody
            except bs.NotFoundError:
                return True

            # Don't allow picking up of invincible dudes.
            try:
                if opposingnode.invincible:
                    return True
            except Exception:
                pass

            # If we're grabbing the pelvis of a non-shattered spaz, we wanna
            # grab the torso instead.
            if (
                opposingnode.getnodetype() == 'spaz'
                and not opposingnode.shattered
                and opposingbody == 4
            ):
                opposingbody = 1

            # Special case #1 - if we're holding a flag, don't replace it
            # Special case #2 - corpses should have lower priority
            # (hmm - should make this customizable or more low level).
            held = self.node.hold_node
            if held:
                spaz = opposingnode.getdelegate(Spaz)
                if held.getnodetype() == 'flag' or (
                    spaz and not spaz.is_alive()
                ):
                    return True

            # Note: hold_body needs to be set before hold_node.
            self.node.hold_body = opposingbody
            self.node.hold_node = opposingnode
        elif isinstance(msg, bs.CelebrateMessage):
            if self.node:
                self.node.handlemessage('celebrate', int(msg.duration * 1000))

        else:
            return super().handlemessage(msg)
        return None

    def drop_bomb(self) -> Bomb | None:
        """
        Tell the spaz to drop one of his bombs, and returns
        the resulting bomb object.
        If the spaz has no bombs or is otherwise unable to
        drop a bomb, returns None.
        """

        if (self.land_mine_count <= 0 and self.bomb_count <= 0) or self.frozen:
            return None
        assert self.node
        pos = self.node.position_forward
        vel = self.node.velocity

        if self.land_mine_count > 0:
            dropping_bomb = False
            self.set_land_mine_count(self.land_mine_count - 1)
            bomb_type = 'land_mine'
        else:
            dropping_bomb = True
            bomb_type = self.bomb_type

        bomb = Bomb(
            position=(pos[0], pos[1] - 0.0, pos[2]),
            velocity=(vel[0], vel[1], vel[2]),
            bomb_type=bomb_type,
            blast_radius=self.blast_radius,
            source_player=self.source_player,
            owner=self.node,
        ).autoretain()

        assert bomb.node
        if dropping_bomb:
            self.bomb_count -= 1
            bomb.node.add_death_action(
                bs.WeakCall(self.handlemessage, BombDiedMessage())
            )
        self._pick_up(bomb.node)

        for clb in self._dropped_bomb_callbacks:
            clb(self, bomb)

        return bomb

    def _pick_up(self, node: bs.Node) -> None:
        if self.node:
            # Note: hold_body needs to be set before hold_node.
            self.node.hold_body = 0
            self.node.hold_node = node

    def set_land_mine_count(self, count: int) -> None:
        """Set the number of land-mines this spaz is carrying."""
        self.land_mine_count = count
        if self.node:
            if self.land_mine_count != 0:
                self.node.counter_text = 'x' + str(self.land_mine_count)
                self.node.counter_texture = (
                    PowerupBoxFactory.get().tex_land_mines
                )
            else:
                self.node.counter_text = ''

    def curse_explode(self, source_player: bs.Player | None = None) -> None:
        """Explode the poor spaz spectacularly."""
        if self._cursed and self.node:
            self.shatter(extreme=True)
            self.handlemessage(bs.DieMessage())
            activity = self._activity()
            if activity:
                Blast(
                    position=self.node.position,
                    velocity=self.node.velocity,
                    blast_radius=3.0,
                    blast_type='normal',
                    source_player=(
                        source_player if source_player else self.source_player
                    ),
                ).autoretain()
            self._cursed = False

    def shatter(self, extreme: bool = False) -> None:
        """Break the poor spaz into little bits."""
        if self.shattered:
            return
        self.shattered = True
        assert self.node
        if self.frozen:
            # Momentary flash of light.
            light = bs.newnode(
                'light',
                attrs={
                    'position': self.node.position,
                    'radius': 0.5,
                    'height_attenuated': False,
                    'color': (0.8, 0.8, 1.0),
                },
            )

            bs.animate(
                light, 'intensity', {0.0: 3.0, 0.04: 0.5, 0.08: 0.07, 0.3: 0}
            )
            bs.timer(0.3, light.delete)

            # Emit ice chunks.
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(random.random() * 10.0 + 10.0),
                scale=0.6,
                spread=0.2,
                chunk_type='ice',
            )
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(random.random() * 10.0 + 10.0),
                scale=0.3,
                spread=0.2,
                chunk_type='ice',
            )
            SpazFactory.get().shatter_sound.play(
                1.0,
                position=self.node.position,
            )
        else:
            SpazFactory.get().splatter_sound.play(
                1.0,
                position=self.node.position,
            )
        self.handlemessage(bs.DieMessage())
        self.node.shattered = 2 if extreme else 1

    def _hit_self(self, intensity: float) -> None:
        if not self.node:
            return
        pos = self.node.position
        self.handlemessage(
            bs.HitMessage(
                flat_damage=50.0 * intensity,
                pos=pos,
                force_direction=self.node.velocity,
                hit_type='impact',
            )
        )
        self.node.handlemessage('knockout', max(0.0, 50.0 * intensity))
        sounds: Sequence[bs.Sound]
        if intensity >= 5.0:
            sounds = SpazFactory.get().impact_sounds_harder
        elif intensity >= 3.0:
            sounds = SpazFactory.get().impact_sounds_hard
        else:
            sounds = SpazFactory.get().impact_sounds_medium
        sound = sounds[random.randrange(len(sounds))]
        sound.play(position=pos, volume=5.0)

    def _get_bomb_type_tex(self) -> bs.Texture:
        factory = PowerupBoxFactory.get()
        if self.bomb_type == 'sticky':
            return factory.tex_sticky_bombs
        if self.bomb_type == 'ice':
            return factory.tex_ice_bombs
        if self.bomb_type == 'impact':
            return factory.tex_impact_bombs
        raise ValueError('invalid bomb type')

    def _flash_billboard(self, tex: bs.Texture) -> None:
        assert self.node
        self.node.billboard_texture = tex
        self.node.billboard_cross_out = False
        bs.animate(
            self.node,
            'billboard_opacity',
            {0.0: 0.0, 0.1: 1.0, 0.4: 1.0, 0.5: 0.0},
        )

    def set_bomb_count(self, count: int) -> None:
        """Sets the number of bombs this Spaz has."""
        # We can't just set bomb_count because some bombs may be laid currently
        # so we have to do a relative diff based on max.
        diff = count - self._max_bomb_count
        self._max_bomb_count += diff
        self.bomb_count += diff

    def _gloves_wear_off_flash(self) -> None:
        if self.node:
            self.node.boxing_gloves_flashing = True
            self.node.billboard_texture = PowerupBoxFactory.get().tex_punch
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _gloves_wear_off(self) -> None:
        if self._demo_mode:  # Preserve old behavior.
            self._punch_power_scale = 1.2
            self._punch_cooldown = BASE_PUNCH_COOLDOWN
        else:
            factory = SpazFactory.get()
            self._punch_power_scale = factory.punch_power_scale
            self._punch_cooldown = factory.punch_cooldown
        self._has_boxing_gloves = False
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.boxing_gloves = False
            self.node.billboard_opacity = 0.0

    def _multi_bomb_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = PowerupBoxFactory.get().tex_bomb
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _multi_bomb_wear_off(self) -> None:
        self.set_bomb_count(self.default_bomb_count)
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0

    def _bomb_wear_off_flash(self) -> None:
        if self.node:
            self.node.billboard_texture = self._get_bomb_type_tex()
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True

    def _bomb_wear_off(self) -> None:
        self.bomb_type = self.bomb_type_default
        if self.node:
            PowerupBoxFactory.get().powerdown_sound.play(
                position=self.node.position,
            )
            self.node.billboard_opacity = 0.0
