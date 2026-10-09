# Released under the MIT License. See LICENSE for details.
#
"""The fixed numbers of a character's rig.

How a character is put together physically: the bodies it is simulated
as, where its joints anchor on them, and how its art is placed on
them. These are the game's own values. The game's code is generated
from this module, so anything else that reads it (tools that show a
character outside the game, say) is looking at exactly what plays.

Nearly everything here is simulation state: every machine in a game
builds the same bodies from it, so changing a number changes gameplay
for every character at once. Treat edits accordingly.
"""

from dataclasses import dataclass

#: Three numbers: a point or offset as ``(x, y, z)``. Y is up, z is
#: forward, and a character's own right is -x.
type Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class SpazRig:
    """The fixed numbers of a spaz's own rig (see :data:`SPAZ_RIG`).

    Lengths are in the game's world units and angles in degrees. A
    capsule lies along its own z axis and its length leaves out its
    two round caps. Anything given for one side is the character's
    right; the left mirrors it in x.
    """

    # ---- The bodies. (A torso's radius, a thigh's and an ankle's are
    # per character; see bacommon.characterranges.) ----

    #: Radius of the head's ball.
    head_radius: float = 0.23

    #: Width, height and depth of the pelvis's box.
    pelvis_size: Vec3 = (0.35, 0.16, 0.1)

    #: Radius of the ball a spaz rolls around on, at its full
    #: (standing) size.
    roller_radius: float = 0.3

    #: Radius of an upper arm's capsule.
    upper_arm_radius: float = 0.06

    #: Length of an upper arm's capsule.
    upper_arm_length: float = 0.16

    #: Radius of a lower arm's capsule.
    lower_arm_radius: float = 0.06

    #: Length of a lower arm's capsule.
    lower_arm_length: float = 0.13

    #: Length of an upper leg's capsule (its radius is the character's
    #: thigh radius).
    upper_leg_length: float = 0.12

    #: A lower leg's capsule is this long less twice its radius (the
    #: character's ankle radius), so its whole span stays the same
    #: whatever its thickness.
    lower_leg_span: float = 0.26

    #: Radius of a foot's ball.
    toes_radius: float = 0.075

    # ---- Where the middle bodies start out, as heights above a
    # common base. Their joints are made from these placements, so the
    # gaps between them are the rig's own proportions. ----

    #: Starting height of the head's center.
    stand_head_height: float = 2.25

    #: Starting height of the torso's center.
    stand_torso_height: float = 1.8

    #: Starting height of the pelvis's center.
    stand_pelvis_height: float = 1.66

    #: Starting height of the roller ball's center.
    stand_roller_height: float = 1.6

    # ---- Where joints anchor. A joint pins a point on one body to a
    # point on the next; each is given in its own body's space. ----

    #: The joint between pelvis and torso sits this far below the
    #: torso's center.
    pelvis_joint_drop: float = 0.05

    #: On the torso, that joint also sits this far forward, like the
    #: curve of a spine.
    pelvis_joint_forward: float = 0.05

    #: A shoulder's place on the torso, before the character's own
    #: shoulder offset.
    shoulder_on_torso: Vec3 = (-0.15, 0.14, 0.0)

    #: A shoulder's place on its upper arm.
    shoulder_on_upper_arm: Vec3 = (0.02, 0.0, -0.1)

    #: An elbow's place on its upper arm.
    elbow_on_upper_arm: Vec3 = (0.0, 0.0, 0.07)

    #: An elbow's place on its lower arm.
    elbow_on_lower_arm: Vec3 = (0.0, 0.0, -0.08)

    #: A hip's place on the pelvis.
    hip_on_pelvis: Vec3 = (-0.1, -0.01, 0.0)

    #: A hip's place on its upper leg.
    hip_on_upper_leg: Vec3 = (0.0, 0.0, -0.05)

    #: A knee's place on its upper leg.
    knee_on_upper_leg: Vec3 = (0.0, 0.0, 0.05)

    #: A knee's place on its lower leg.
    knee_on_lower_leg: Vec3 = (0.0, 0.0, -0.05)

    #: An ankle's place on its lower leg.
    ankle_on_lower_leg: Vec3 = (0.0, 0.05, 0.05)

    #: An ankle's place on its foot.
    ankle_on_toes: Vec3 = (0.0, -0.04, 0.0)

    # ---- How art is placed on the bodies. ----

    #: An upper arm's art stretches along its length to reach from the
    #: shoulder to this point on the lower arm (in the lower arm's
    #: space), so the two always meet.
    arm_stretch_point: Vec3 = (0.0, 0.0, -0.1)

    #: The same for an upper leg, reaching from the hip to this point
    #: on the lower leg.
    leg_stretch_point: Vec3 = (0.0, 0.0, -0.05)

    #: The reach at which an upper arm's art is drawn unstretched.
    arm_stretch_rest: float = 0.192

    #: The reach at which an upper leg's art is drawn unstretched.
    leg_stretch_rest: float = 0.2

    #: The most any limb art is ever stretched.
    limb_stretch_max: float = 1.6

    #: A forearm's art takes its arm's stretch too, about the point
    #: this far along the lower arm.
    forearm_stretch_pivot: float = 0.1

    #: A hand's art sits this far along the lower arm.
    hand_offset: float = 0.04

    #: How far an empty hand's art is turned about the lower arm's y
    #: axis.
    hand_turn: float = 10.0

    #: The size the shared eye art (ball, iris and lid) is drawn at.
    eye_mesh_scale: float = 0.09

    #: An eyeball's resting turn about its x axis, so it looks
    #: slightly down.
    eyeball_pitch: float = -10.0


#: The spaz rig's numbers.
SPAZ_RIG = SpazRig()


@dataclass(frozen=True)
class AttachmentSegmentRig:
    """The rig of one simulated segment of an attachment.

    A segment is a capsule lying along its own z axis, hung by a spring
    joint from the segment before it (or, for the first, from the spot
    on the body part where its attachment sits).
    """

    #: Radius of the capsule that collides.
    geom_radius: float

    #: Length of the capsule that collides, not counting its caps.
    geom_length: float

    #: Radius of the capsule its mass is worked out from, or 0 to use
    #: the one that collides.
    mass_radius: float

    #: Length of that capsule, likewise.
    mass_length: float

    #: How dense that capsule is.
    density: float

    #: Where its joint anchors on the segment before it, in that
    #: segment's space. Unused for a first segment.
    parent_anchor: Vec3

    #: Where its joint anchors on itself, in its own space.
    child_anchor: Vec3

    #: How strongly its joint's spring pulls it into place.
    linear_stiffness: float

    #: How strongly that pull is damped.
    linear_damping: float

    #: How strongly its joint's spring turns it to its rest angle.
    angular_stiffness: float

    #: How strongly that turning is damped.
    angular_damping: float

    #: Whether it bumps into things (a ponytail's tip does not).
    collides: bool = True


def _tuft(geom_radius: float, own_mass: bool) -> AttachmentSegmentRig:
    """A legacy hair tuft: one size of capsule, one shared weight.

    Every tuft weighs what the large one does whatever its size
    (``own_mass`` is that large one, whose mass capsule is its own).
    """
    return AttachmentSegmentRig(
        geom_radius=geom_radius,
        geom_length=0.13,
        mass_radius=0.0 if own_mass else 0.07,
        mass_length=0.0 if own_mass else 0.13,
        density=0.01,
        parent_anchor=(0.0, 0.0, 0.0),
        child_anchor=(0.0, -0.08, -0.12),
        linear_stiffness=0.2,
        linear_damping=0.01,
        angular_stiffness=0.00025,
        angular_damping=0.000001,
    )


def _antenna(root: bool) -> AttachmentSegmentRig:
    """One segment of an antenna chain.

    The smallest tuft's body on much stiffer springs, so it mostly
    holds its pose. Each joint sits at the center of the touching
    end caps, so a chain reads as balls and rods, and a root's sits
    squarely at its own base so it points straight out from wherever
    it is put.
    """
    return AttachmentSegmentRig(
        geom_radius=0.04,
        geom_length=0.13,
        mass_radius=0.07,
        mass_length=0.13,
        density=0.01,
        parent_anchor=(0.0, 0.0, 0.0) if root else (0.0, 0.0, 0.065),
        child_anchor=(0.0, 0.0, -0.065),
        linear_stiffness=0.8,
        linear_damping=0.0005,
        angular_stiffness=0.00001,
        angular_damping=0.00000001,
    )


#: The segments of each kind of simulated attachment, first segment
#: first. Keyed by kind, in the game's own order of kinds, which must
#: not change (a static attachment has no rig and is not here).
ATTACHMENT_RIGS: dict[str, tuple[AttachmentSegmentRig, ...]] = {
    # The classic front-right hair tuft.
    'legacy_tuft_large': (_tuft(0.07, own_mass=True),),
    # Midway between large and small.
    'legacy_tuft_medium': (_tuft(0.055, own_mass=False),),
    # The classic front-left tuft.
    'legacy_tuft_small': (_tuft(0.04, own_mass=False),),
    # A stiffer root and a floppy tip that bumps into nothing. The tip
    # hangs off the root, so turning the attachment carries both.
    'legacy_ponytail_2': (
        AttachmentSegmentRig(
            geom_radius=0.09,
            geom_length=0.1,
            mass_radius=0.0,
            mass_length=0.0,
            density=0.01,
            parent_anchor=(0.0, 0.0, 0.0),
            child_anchor=(0.0, -0.01, 0.1),
            linear_stiffness=1.0,
            linear_damping=0.03,
            angular_stiffness=0.0015,
            angular_damping=0.000003,
        ),
        AttachmentSegmentRig(
            geom_radius=0.09,
            geom_length=0.13,
            mass_radius=0.0,
            mass_length=0.0,
            density=0.01,
            parent_anchor=(0.0, 0.01, -0.1),
            child_anchor=(0.0, -0.01, 0.12),
            linear_stiffness=0.4,
            linear_damping=0.02,
            angular_stiffness=0.00025,
            angular_damping=0.000001,
            collides=False,
        ),
    ),
    'antenna': (_antenna(root=True),),
    'antenna_2': (_antenna(root=True), _antenna(root=False)),
    'antenna_3': (_antenna(root=True),) + (_antenna(root=False),) * 2,
    'antenna_4': (_antenna(root=True),) + (_antenna(root=False),) * 3,
}
