# Released under the MIT License. See LICENSE for details.
#
"""A viewer showing a character standing around."""

import math
from typing import TYPE_CHECKING, override

import bascenev1 as bs
import bauiv1 as bui
from bascenev1 import _classicassets, _classicmapassets

if TYPE_CHECKING:
    from typing import Any, Self

#: Where to stand a spaz for it to start out at rest on our floor.
STAND_HEIGHT = -0.58

#: Where our spaz stands (x, z) and which way it faces (degrees).
_HOME = (0.0, 0.0)
_HOME_ANGLE = 20.0

#: Where we look on from.
_CAMERA_POSITION = (0.96, 1.5, 4.5)

# Pressing on the viewer (a little easter egg): our spaz jumps, and if
# that (with the physics' help) sends it off, it wanders back home.

#: How long after a jump before heading home (seconds); lets it land.
_HOP_SETTLE_TIME = 1.2

#: Further from home than this (x/z) and our spaz walks back...
_WANDER_START_DIST = 0.35

#: ...until it's within this.
_WANDER_STOP_DIST = 0.12

#: Within this of home, walking eases off toward a stroll.
_WALK_EASE_DIST = 0.6

#: Slowest a walk home goes (stick amount).
_WALK_MIN_SPEED = 0.3

#: Once home, how long to stand before turning back to face us...
_FACE_DELAY = 0.6

#: ...which it does with a brief, slight push of the stick our way
#: (just enough to turn it, barely moving it).
_FACE_NUDGE_AMOUNT = 0.2
_FACE_NUDGE_TIME = 0.12

#: Anywhere this far off (or fallen through the floor) and we just
#: stand it back at home.
_LOST_DIST = 8.0
_LOST_HEIGHT = -3.0

#: How often our spaz's brain runs (seconds).
_TICK_TIME = 0.1


class CharacterViewer(bui.Viewer):
    """Shows a character standing on a bit of terrain.

    For previewing characters in ui (a profile editor, say): a little
    scene of its own holding a single spaz, which can be handed a new
    character definition at any time.

    Use :meth:`get` to get the one kept under an id (made if need be)
    and hand its :attr:`source` to a viewer widget.

    :meta private:
    """

    def __init__(self) -> None:
        # Size gets set by whatever widget shows us.
        self._viewer = bs.SceneViewer(256, 256)
        self._spaz_json: str | None = None
        self._spaz_def: bs.SpazDef | None = None

        with self._viewer.context:
            gnode = bs.newnode('globals')
            self._globals = gnode
            gnode.tint = (1.3, 1.2, 1.0)
            gnode.ambient_color = (1.3, 1.2, 1.0)
            gnode.vignette_outer = (0.57, 0.57, 0.57)
            gnode.vignette_inner = (0.9, 0.9, 0.9)

            # Spazzes stand up only on what tells them it is footing.
            footing = bs.Material()
            self._roller_material = bs.Material()
            self._spaz_material = bs.Material()
            for mat in (self._roller_material, self._spaz_material):
                mat.add_actions(
                    conditions=('they_have_material', footing),
                    actions=(
                        ('message', 'our_node', 'at_connect', 'footing', 1),
                        (
                            'message',
                            'our_node',
                            'at_disconnect',
                            'footing',
                            -1,
                        ),
                    ),
                )
            self._footing_material = footing

            # Footfalls, landings and tumbles sound as they do in games
            # (see bascenev1lib.actor.spazfactory).
            foot_impacts = (
                _classicassets.audio.foot_impact01.get(),
                _classicassets.audio.foot_impact02.get(),
                _classicassets.audio.foot_impact03.get(),
            )
            self._roller_material.add_actions(
                conditions=('they_have_material', footing),
                actions=(
                    ('impact_sound', foot_impacts, 1, 0.2),
                    ('skid_sound', _classicassets.audio.skid01.get(), 20, 0.3),
                    (
                        'roll_sound',
                        _classicassets.audio.scamper01.get(),
                        20,
                        3.0,
                    ),
                ),
            )
            gravel_skid = _classicassets.audio.gravel_skid.get()
            self._spaz_material.add_actions(
                conditions=('they_have_material', footing),
                actions=(
                    ('impact_sound', foot_impacts, 20, 6),
                    ('skid_sound', gravel_skid, 2.0, 1),
                    ('roll_sound', gravel_skid, 2.0, 1),
                ),
            )

            self._terrain = bs.newnode(
                'terrain',
                attrs={
                    'mesh': _classicmapassets.meshes.football_stadium.get(),
                    'collision_mesh': (
                        _classicmapassets.meshes
                    ).football_stadium_collide.get(),
                    'color_texture': (
                        _classicmapassets.textures.football_stadium.get()
                    ),
                    'materials': [footing],
                },
            )
        self._spaz: bs.Node | None = None

        # Field of view is vertical, so our character takes up the
        # same share of a pane's height whatever the pane's shape
        # (about 70%, which leaves it clear of the toolbars that lie
        # over a pane's top and bottom at small ui-scale). Panes can
        # get narrow though (small ui-scale on a squarish screen), so
        # past the point where a character with its arms out would
        # start getting cut off at the sides we see more instead.
        # We look on from about 12 degrees off to the right (same
        # distance out) so we aren't staring straight down the field's
        # yard lines.
        self._viewer.set_camera(
            position=_CAMERA_POSITION,
            target=(0.0, 0.85, 0.0),
            field_of_view=30.0,
            near_clip=0.5,
            far_clip=80.0,
            min_horizontal_field_of_view=20.0,
        )

        # A touch of hand-held wobble to its aim.
        self._viewer.set_camera_shake(
            strength=1.3,
            stiffness=100.0,
            damping=2.0,
            poke_interval_min=0.15,
            poke_interval_max=1.0,
        )

        # Turning the device turns our view of the character with it
        # (a fraction as far; a full turn's worth is too much).
        self._viewer.set_camera_tilt_orbit(0.2)

        # Our character stands about 4.65 out from the camera. It and
        # whatever it holds or wears stay sharp; the ground running up
        # to it and away behind it goes soft.
        self._viewer.set_depth_of_field(focus=(3.9, 5.4), blur=(2.6, 8.0))

        # Heard as our camera would hear it. It sits much closer to our
        # character than a game camera does, so things come out louder
        # than in games; volume makes up for that.
        self._viewer.set_sound(True, volume=0.6, pan_scale=1.0)
        self._play = _SpazPlay(self._viewer)
        self.set_spaz_def(None)

    @classmethod
    def for_depiction(cls, key: str, depiction_json: str) -> Self:
        """Return the viewer showing a character-viewer depiction.

        Registered as the live-depiction maker for that kind (see
        ``bauiv1.UIV1AppSubsystem.live_depictions``); carries on with
        the viewer kept under ``key`` so a changed character updates
        the picture in place.
        """
        from efro.dataclassio import dataclass_from_json
        import bacommon.depiction as bdep

        depiction = dataclass_from_json(bdep.Depiction, depiction_json)
        assert isinstance(depiction, bdep.CharacterViewerDepiction)
        viewer = cls.get(key)
        viewer.set_spaz_def(depiction.spaz)
        return viewer

    @classmethod
    def get(cls, viewer_id: str) -> Self:
        """Return the viewer kept under an id, making it if need be."""
        viewers = bui.app.ui_v1.viewers
        viewer = viewers.get(viewer_id, cls)
        if viewer is None:
            viewer = cls()
            viewers.add(viewer_id, viewer)
        return viewer

    @override
    @property
    def source(self) -> bui.ViewerSource:
        return self._viewer.source

    @override
    def shutdown(self) -> None:
        self._play.shutdown()
        self._spaz = None
        self._spaz_def = None
        self._viewer.shutdown()

    @override
    def wants_presses(self) -> bool:
        return True

    @override
    def handle_press(self, x: float, y: float) -> None:
        self._play.press(x, y)

    @override
    def handle_release(self) -> None:
        self._play.release()

    def set_spaz_def(self, spaz_json: str | None) -> None:
        """Show a spaz, given its definition json (a character's spaz part).

        Pass None for the standard one.
        """
        if spaz_json is None:
            # A definition with no spaz block is the engine's standard
            # spaz (the standin) in every respect; the client carries
            # no character json of its own (cloud-profiles D11).
            spaz_json = '{}'

        # Nothing to do if that's who we're showing.
        if self._spaz and spaz_json == self._spaz_json:
            return
        self._spaz_json = spaz_json

        with self._viewer.context:
            self._spaz_def = bs.SpazDef(spaz_json)

            # Our spaz just changes definition in place (proportions and
            # looks both follow along), so edits don't pop it out and
            # back in.
            if self._spaz:
                self._spaz.spaz_def = self._spaz_def
                return

            # The definition alone decides how our character looks,
            # colors included.
            self._spaz = bs.newnode(
                'spaz',
                attrs={
                    'behavior_version': 2,
                    'spaz_def': self._spaz_def,
                    'use_spaz_def_color': True,
                    'use_spaz_def_highlight': True,
                    'materials': [self._spaz_material],
                    'roller_materials': [self._roller_material],
                    'is_area_of_interest': False,
                },
            )

            # Stood at a point on the ground, a spaz starts out most of
            # a unit above it and drops in, the way players arrive in
            # a game. The landing takes a second or so to settle and
            # can leave it turned any which way, so we stand ours where
            # it would come to rest instead.
            self._spaz.handlemessage(
                'stand', _HOME[0], STAND_HEIGHT, _HOME[1], _HOME_ANGLE
            )
        self._play.set_spaz(self._spaz)


class _SpazPlay:
    """A single spaz's easter-egg antics: jumping when poked, going home.

    Poke (press on) the viewer and the spaz jumps (held for as long as
    you hold the press, as a jump button would be). If it lands away
    from its spot, it walks back; either way it then turns to face you
    again. Driven purely through the spaz's player inputs (stick,
    jump), so it moves just as a player would.
    """

    def __init__(self, viewer: bs.SceneViewer) -> None:
        self._viewer = viewer
        self._spaz: bs.Node | None = None
        self._walking = False
        self._settle_until = 0.0
        self._home_since: float | None = None
        self._faced = True
        self._nudge_until: float | None = None
        with viewer.context:
            self._timer: bs.Timer | None = bs.Timer(
                _TICK_TIME, bui.WeakCallStrict(self._tick), repeat=True
            )

    def shutdown(self) -> None:
        """Stop for good."""
        self._timer = None
        self._spaz = None

    def set_spaz(self, spaz: bs.Node) -> None:
        """Take charge of a (freshly made) spaz standing at home."""
        self._spaz = spaz
        self._walking = False
        self._settle_until = 0.0
        self._home_since = None
        self._faced = True
        self._nudge_until = None

    def press(self, x: float, y: float) -> None:
        """A press on the viewer, at fractions across and up it."""
        del x, y  # Unused; a press anywhere is a jump.
        spaz = self._spaz
        if not spaz:
            return
        with self._viewer.context:
            self._stop(spaz)
            spaz.jump_pressed = True
            self._walking = False
            self._settle_until = bs.time() + _HOP_SETTLE_TIME
            self._home_since = None
            self._nudge_until = None
            self._faced = False

    def release(self) -> None:
        """The press let go."""
        if self._spaz:
            self._spaz.jump_pressed = False

    def _tick(self) -> None:
        spaz = self._spaz
        if not spaz:
            return
        now = bs.time()
        pos = spaz.position
        to_x = _HOME[0] - pos[0]
        to_z = _HOME[1] - pos[2]
        dist = math.hypot(to_x, to_z)

        # Somewhere it shouldn't be (knocked clean off, fallen through):
        # just put it back.
        if dist > _LOST_DIST or pos[1] < _LOST_HEIGHT:
            self._stop(spaz)
            spaz.handlemessage(
                'stand', _HOME[0], STAND_HEIGHT, _HOME[1], _HOME_ANGLE
            )
            self.set_spaz(spaz)
            return

        # Just jumped: let it land.
        if now < self._settle_until:
            return

        if not self._walking and dist > _WANDER_START_DIST:
            self._walking = True
        if self._walking:
            if dist < _WANDER_STOP_DIST:
                self._walking = False
                self._stop(spaz)
            else:
                speed = max(_WALK_MIN_SPEED, min(1.0, dist / _WALK_EASE_DIST))
                spaz.move_left_right = speed * to_x / dist
                spaz.move_up_down = -speed * to_z / dist
                self._home_since = None
                return

        # Settled near home: after a moment, turn back to face us with
        # a brief, slight push of the stick our way (a spaz turns to
        # face where it's pushed; this one barely moves it).
        if self._faced:
            return
        if self._nudge_until is not None:
            if now >= self._nudge_until:
                self._stop(spaz)
                self._nudge_until = None
                self._faced = True
            return
        if self._home_since is None:
            self._home_since = now
        elif now - self._home_since > _FACE_DELAY:
            cam_x = _CAMERA_POSITION[0] - pos[0]
            cam_z = _CAMERA_POSITION[2] - pos[2]
            cam_dist = math.hypot(cam_x, cam_z)
            if cam_dist > 0.0:
                spaz.move_left_right = _FACE_NUDGE_AMOUNT * cam_x / cam_dist
                spaz.move_up_down = -_FACE_NUDGE_AMOUNT * cam_z / cam_dist
            self._nudge_until = now + _FACE_NUDGE_TIME

    def _stop(self, spaz: bs.Node) -> None:
        spaz.move_left_right = 0.0
        spaz.move_up_down = 0.0
