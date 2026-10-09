# Released under the MIT License. See LICENSE for details.
#
"""Character builders: the authoring form of a character.

A ``.bchar`` file in an assets workspace holds one
:class:`CharacterBuilder` as json. It says everything needed for a
character to appear in the store and in games -- its name, its icon,
its default colors, and how it looks and is proportioned in play --
by pointing at other assets **in the same workspace**.

This is an *authoring* format: written by people (or the workspace
editor), stored once, and read by the server, which builds the
compact definitions clients actually receive from it. So its keys are
plain words, and nothing here is sent to game clients as is.

Every asset is named by its **logical path**: its source file's path
from the workspace root, minus the extension (``zoe/head.obj`` is
``zoe/head``). Logical paths are unique across all kinds of asset in
a workspace, so a path alone is never ambiguous. Assets in other
workspaces or packages cannot be referenced; copy what a character
needs into its own workspace.

Files inside published package versions are kept forever, so this
schema only ever grows: new optional fields, or a new
:class:`CharacterBuilderData` kind beside the existing ones.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

#: The file extension of a character builder in a workspace.
CHARACTER_BUILDER_EXTENSION = '.bchar'


class CharacterBuilderDataTypeID(Enum):
    """Type ID for each kind of character a builder can describe."""

    BASIC_SPAZ = 'basic_spaz'


class CharacterBuilderData(IOMultiType[CharacterBuilderDataTypeID]):
    """A complete character of some kind; see the kinds below.

    A kind owns everything about its characters: name, icon, colors
    and in-game form alike.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CharacterBuilderDataTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: CharacterBuilderDataTypeID
    ) -> type[CharacterBuilderData]:
        t = CharacterBuilderDataTypeID
        if type_id is t.BASIC_SPAZ:
            return BasicSpazBuilder
        assert_never(type_id)

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return 'type'


class BuilderEyeStyle(Enum):
    """How one of a character's eyes is drawn."""

    #: Eyeball plus a resting/blinking eyelid.
    REGULAR = 'regular'

    #: Bare eyeball; the lid appears only during blinks.
    LIDLESS = 'lidless'

    #: No eye drawn at all (painted-on or eyeless heads, eyepatches).
    NONE = 'none'


@ioprepped
@dataclass
class BuilderTransform:
    """A placement: move, turn and resize, in that order of effect.

    Applied to a thing in the space of whatever it is attached to. The
    thing is resized about its own origin, then turned, then moved; so
    ``scale`` never changes how far ``translate`` moves it, and
    ``rotate`` never swings it around some distant point. Left out
    entirely, a transform changes nothing.

    ``rotate`` is heading, pitch and roll in degrees, applied in that
    order and described the way an aircraft's are, the thing's 'nose'
    being its own forward (+z) axis:

    * **heading** turns it about the up axis of what it is attached
      to. Positive turns right, so something pointing out of a
      character's nose swings toward the character's right ear.
    * **pitch** then raises its nose. Positive aims it up, so toward
      the top of a head.
    * **roll** then spins it about its own nose without changing
      where that points. Positive is clockwise seen from behind.
    """

    translate: Annotated[
        tuple[float, float, float], IOAttrs('translate', store_default=False)
    ] = (0.0, 0.0, 0.0)
    rotate: Annotated[
        tuple[float, float, float], IOAttrs('rotate', store_default=False)
    ] = (0.0, 0.0, 0.0)
    scale: Annotated[
        tuple[float, float, float], IOAttrs('scale', store_default=False)
    ] = (1.0, 1.0, 1.0)


class BuilderAttachTarget(Enum):
    """A body part an attachment can hang off."""

    HEAD = 'head'
    TORSO = 'torso'
    PELVIS = 'pelvis'
    UPPER_ARM = 'upper_arm'
    FOREARM = 'forearm'
    HAND = 'hand'
    UPPER_LEG = 'upper_leg'
    LOWER_LEG = 'lower_leg'
    TOES = 'toes'


class BuilderAttachSide(Enum):
    """Which of a paired body part's two sides an attachment is on.

    Like the limb meshes themselves, a limb attachment is authored for
    the character's right side and drawn mirrored on the left.
    """

    #: Both sides. The only choice for the head, torso and pelvis.
    BOTH = 'both'
    RIGHT = 'right'
    LEFT = 'left'


class BuilderAttachmentKind(Enum):
    """How an attachment moves.

    Each kind is a ready-made physical rig; an attachment picks one,
    places it, tunes it and supplies art for its segments. All of them
    are for looks only and never affect play.

    The ``LEGACY_`` kinds reproduce one classic hair rig and twirl
    oddly when disturbed; prefer the ``ANTENNA`` kinds for anything
    new.
    """

    #: Single softly-jointed capsule. One segment.
    LEGACY_TUFT_LARGE = 'legacy_tuft_large'
    #: The same with a medium-sized capsule. One segment.
    LEGACY_TUFT_MEDIUM = 'legacy_tuft_medium'
    #: The same with a small capsule. One segment.
    LEGACY_TUFT_SMALL = 'legacy_tuft_small'
    #: A stiffer root capsule plus a floppy tip. Two segments.
    LEGACY_PONYTAIL_2 = 'legacy_ponytail_2'
    #: A stiff single capsule that mostly holds its pose, for
    #: antennas, ears, horns and the like. One segment.
    ANTENNA = 'antenna'
    #: A chain of two such capsules. Two segments.
    ANTENNA_2 = 'antenna_2'
    #: A chain of three. Three segments.
    ANTENNA_3 = 'antenna_3'
    #: A chain of four. Four segments.
    ANTENNA_4 = 'antenna_4'
    #: No movement at all, just art fixed to the body part, for hats,
    #: horns, badges and the like. One segment. The only kind limbs
    #: can take.
    STATIC = 'static'


@ioprepped
@dataclass
class BuilderAttachmentSegment:
    """The art for one segment of an attachment.

    Drawn with the character's own texture, tint mask, color and
    highlight, like every other piece of it.
    """

    #: The segment's mesh, by logical path.
    mesh: Annotated[str, IOAttrs('mesh')]

    #: How the mesh is drawn on its segment (for a static attachment,
    #: on the body part itself).
    transform: Annotated[
        BuilderTransform, IOAttrs('transform', store_default=False)
    ] = field(default_factory=BuilderTransform)


@ioprepped
@dataclass
class BuilderAttachment:
    """One piece hung off one of a character's body parts.

    The tuning numbers below run 0 to 1 (or -1 to 1 where noted) and
    what they adjust depends on the kind; a static attachment ignores
    them all.
    """

    # pylint: disable=too-many-instance-attributes

    #: The body part it hangs off.
    target: Annotated[BuilderAttachTarget, IOAttrs('target')]

    kind: Annotated[BuilderAttachmentKind, IOAttrs('kind')]

    #: Art for each of the kind's segments, root first.
    segments: Annotated[list[BuilderAttachmentSegment], IOAttrs('segments')]

    side: Annotated[BuilderAttachSide, IOAttrs('side', store_default=False)] = (
        BuilderAttachSide.BOTH
    )

    #: Where it is anchored on the body part and which way it rests.
    #: A static attachment is simply drawn there. Scale is not used;
    #: resize a segment's own transform instead.
    transform: Annotated[
        BuilderTransform, IOAttrs('transform', store_default=False)
    ] = field(default_factory=BuilderTransform)

    #: How firmly it springs back to its resting pose.
    stiffness: Annotated[float, IOAttrs('stiffness', store_default=False)] = 0.5
    #: How quickly its motion settles.
    damping: Annotated[float, IOAttrs('damping', store_default=False)] = 0.5
    #: How much it trails behind a moving character.
    drag: Annotated[float, IOAttrs('drag', store_default=False)] = 0.5
    #: Resting bend at every joint of a chain, -1 to 1. Positive bends
    #: toward the attachment's own up; 1 is a right angle per joint.
    curl: Annotated[float, IOAttrs('curl', store_default=False)] = 0.0
    #: Segment length. The default 0.5 is the kind's own length; 0 is
    #: half of it and 1 is one and a half times it. Art is unaffected.
    length: Annotated[float, IOAttrs('length', store_default=False)] = 0.5
    #: Segment thickness. The default 0 is the kind's own; 1 is three
    #: times it. Art is unaffected.
    radius: Annotated[float, IOAttrs('radius', store_default=False)] = 0.0
    #: How much the same-named number above changes from one segment
    #: of a chain to the next, -1 to 1 each. A chain can run stiff at
    #: the root and floppy at the tip, say.
    curl_change: Annotated[
        float, IOAttrs('curl_change', store_default=False)
    ] = 0.0
    length_change: Annotated[
        float, IOAttrs('length_change', store_default=False)
    ] = 0.0
    radius_change: Annotated[
        float, IOAttrs('radius_change', store_default=False)
    ] = 0.0
    stiffness_change: Annotated[
        float, IOAttrs('stiffness_change', store_default=False)
    ] = 0.0
    damping_change: Annotated[
        float, IOAttrs('damping_change', store_default=False)
    ] = 0.0


@ioprepped
@dataclass
class BasicSpazBuilder(CharacterBuilderData):
    """A classic spaz: per-body-part meshes sharing one texture.

    Has one name, one icon, a color and up to two highlights. Every
    part is drawn from a single color texture, tinted through a single
    mask texture: the mask's red channel takes the character's color,
    its green channel the highlight and its blue channel the second
    highlight. Arm and leg meshes are authored
    for the character's right side and mirrored for the left.

    Numbers left out take the standard spaz's values, so a builder
    need only state what makes its character different.
    """

    # pylint: disable=too-many-instance-attributes

    # ---- Identity ----
    #: The character's name, as the logical path of a string (a
    #: ``.bstr`` file) in the same workspace, so it can be translated.
    name: Annotated[str, IOAttrs('name')]
    #: The picture that stands for the character in menus, and its
    #: tint mask (red takes the color, green the highlight).
    icon_texture: Annotated[str, IOAttrs('icon_texture')]
    icon_mask_texture: Annotated[str, IOAttrs('icon_mask_texture')]
    #: The character's own colors. It is shown in these wherever nobody
    #: has picked others (the store, a new profile).
    color: Annotated[tuple[float, float, float], IOAttrs('color')]
    highlight: Annotated[tuple[float, float, float], IOAttrs('highlight')]

    # ---- Textures ----
    color_texture: Annotated[str, IOAttrs('color_texture')]
    color_mask_texture: Annotated[str, IOAttrs('color_mask_texture')]

    # ---- Meshes ----
    head_mesh: Annotated[str, IOAttrs('head_mesh')]
    torso_mesh: Annotated[str, IOAttrs('torso_mesh')]
    upper_arm_mesh: Annotated[str, IOAttrs('upper_arm_mesh')]
    upper_leg_mesh: Annotated[str, IOAttrs('upper_leg_mesh')]
    lower_leg_mesh: Annotated[str, IOAttrs('lower_leg_mesh')]
    toes_mesh: Annotated[str, IOAttrs('toes_mesh')]
    #: Optional. Left out, nothing is drawn for that part (an upper-arm
    #: mesh may be the whole arm; a big round body may hide its pelvis).
    forearm_mesh: Annotated[
        str | None, IOAttrs('forearm_mesh', store_default=False)
    ] = None
    hand_mesh: Annotated[
        str | None, IOAttrs('hand_mesh', store_default=False)
    ] = None
    pelvis_mesh: Annotated[
        str | None, IOAttrs('pelvis_mesh', store_default=False)
    ] = None

    # ---- Highlights ----
    # (Here, apart from ``color`` and ``highlight`` above, because
    # everything from this point on can be left out.)
    #: What the highlight is called where someone picks it (a profile
    #: editor): the logical path of a string in the same workspace, as
    #: ``name`` is, for a character whose highlight is something in
    #: particular ('Hair Color'). Empty: plain 'Highlight'.
    highlight_name: Annotated[
        str, IOAttrs('highlight_name', store_default=False)
    ] = ''
    #: Whether someone using the character may pick its highlight
    #: themselves. Off for one whose highlight is part of who it is.
    highlight_editing: Annotated[
        bool, IOAttrs('highlight_editing', store_default=False)
    ] = True
    #: A second highlight, taken by the masks' blue channel. White (the
    #: default) leaves what that channel covers untinted, so a
    #: character that doesn't use one needn't say anything.
    highlight2: Annotated[
        tuple[float, float, float], IOAttrs('highlight2', store_default=False)
    ] = (1.0, 1.0, 1.0)
    #: As ``highlight_name`` and ``highlight_editing``, for the second
    #: highlight (plain name: 'Highlight 2'). Not editable unless a
    #: character says so: most don't have one.
    highlight2_name: Annotated[
        str, IOAttrs('highlight2_name', store_default=False)
    ] = ''
    highlight2_editing: Annotated[
        bool, IOAttrs('highlight2_editing', store_default=False)
    ] = False

    # ---- Sounds ----
    # (each set is picked from at random; empty means silent)
    jump_sounds: Annotated[
        list[str], IOAttrs('jump_sounds', store_default=False)
    ] = field(default_factory=list)
    attack_sounds: Annotated[
        list[str], IOAttrs('attack_sounds', store_default=False)
    ] = field(default_factory=list)
    impact_sounds: Annotated[
        list[str], IOAttrs('impact_sounds', store_default=False)
    ] = field(default_factory=list)
    death_sounds: Annotated[
        list[str], IOAttrs('death_sounds', store_default=False)
    ] = field(default_factory=list)
    pickup_sounds: Annotated[
        list[str], IOAttrs('pickup_sounds', store_default=False)
    ] = field(default_factory=list)
    fall_sounds: Annotated[
        list[str], IOAttrs('fall_sounds', store_default=False)
    ] = field(default_factory=list)

    # ---- Physique ----
    # (These shape the character's physical body in play, not just how
    # it is drawn.)
    torso_radius: Annotated[
        float, IOAttrs('torso_radius', store_default=False)
    ] = 0.15
    shoulder_offset: Annotated[
        tuple[float, float, float],
        IOAttrs('shoulder_offset', store_default=False),
    ] = (0.0, 0.0, 0.0)
    thigh_radius: Annotated[
        float, IOAttrs('thigh_radius', store_default=False)
    ] = 0.04
    ankle_radius: Annotated[
        float, IOAttrs('ankle_radius', store_default=False)
    ] = 0.07
    #: Sideways distance between the feet while walking.
    step_separation: Annotated[
        float, IOAttrs('step_separation', store_default=False)
    ] = 0.08
    #: How stiffly the lower arms are held while idle. 1 is fully
    #: rigid; lower values give relaxed dangling arms.
    idle_arm_stiffness: Annotated[
        float, IOAttrs('idle_arm_stiffness', store_default=False)
    ] = 1.0
    #: How far the arms swing while walking.
    arm_swing: Annotated[float, IOAttrs('arm_swing', store_default=False)] = 0.6
    #: How far the body sways while standing.
    idle_sway: Annotated[float, IOAttrs('idle_sway', store_default=False)] = (
        0.05
    )

    # ---- Eyes ----
    # (Sides are the character's own left and right.)
    eye_style_left: Annotated[
        BuilderEyeStyle, IOAttrs('eye_style_left', store_default=False)
    ] = BuilderEyeStyle.REGULAR
    eye_style_right: Annotated[
        BuilderEyeStyle, IOAttrs('eye_style_right', store_default=False)
    ] = BuilderEyeStyle.REGULAR
    eye_scale: Annotated[float, IOAttrs('eye_scale', store_default=False)] = 1.0
    #: Where one eye sits relative to the head's center; the other
    #: mirrors it.
    eye_offset: Annotated[
        tuple[float, float, float], IOAttrs('eye_offset', store_default=False)
    ] = (0.065, -0.036, 0.205)
    #: Iris color.
    eye_color: Annotated[
        tuple[float, float, float], IOAttrs('eye_color', store_default=False)
    ] = (0.5, 0.5, 1.2)
    eyeball_color: Annotated[
        tuple[float, float, float],
        IOAttrs('eyeball_color', store_default=False),
    ] = (0.46, 0.38, 0.36)
    eyelid_color: Annotated[
        tuple[float, float, float], IOAttrs('eyelid_color', store_default=False)
    ] = (0.5, 0.3, 0.2)
    #: Resting eyelid tilt in degrees (positive reads as angry).
    eyelid_angle: Annotated[
        float, IOAttrs('eyelid_angle', store_default=False)
    ] = 0.0

    # ---- Surface ----
    #: How strongly the body mirrors its surroundings. 0 is matte;
    #: higher is glossier.
    reflection_scale: Annotated[
        float, IOAttrs('reflection_scale', store_default=False)
    ] = 0.1

    # ---- Attachments ----
    #: Extra pieces hung off the character's body parts, such as hair,
    #: antennas and hats.
    attachments: Annotated[
        list[BuilderAttachment], IOAttrs('attachments', store_default=False)
    ] = field(default_factory=list)

    @override
    @classmethod
    def get_type_id(cls) -> CharacterBuilderDataTypeID:
        return CharacterBuilderDataTypeID.BASIC_SPAZ


@ioprepped
@dataclass
class CharacterBuilder:
    """One character; a ``.bchar`` file's contents.

    Deliberately just a wrapper: everything that defines the character
    -- even its name, icon and colors -- belongs to its
    :class:`CharacterBuilderData` kind, so a later kind is free to
    define any of those differently (several highlights, none, ...).
    Fields land here only if they turn out to be common to every kind.
    """

    #: The character itself.
    data: Annotated[CharacterBuilderData, IOAttrs('data')]
