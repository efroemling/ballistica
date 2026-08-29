# Released under the MIT License. See LICENSE for details.
#
"""Appearance functionality for spazzes."""

# pylint: disable=too-many-lines

from typing import TYPE_CHECKING, overload

from bacommon.assetspec import TextureSpec
import babase
import bascenev1 as bs
from bascenev1 import _classicassets

if TYPE_CHECKING:
    from typing import Literal

    import bauiv1

    from collections.abc import Container, Sequence


def _character_name_table() -> dict[str, babase.LangStr]:
    """Appearance name -> its authored display name.

    First-party appearances with an authored name; mirrors the
    store-side mapping in bamaster ``storeitem.py`` (``OldLady``/
    ``Zola`` are internal keys whose display names are Betty/Lucky).
    Appearances absent here -- mods', plus the never-translated
    Alien/Gladiator/Robot/Warrior/Witch/Wrestler -- show their own
    name untranslated.
    """
    c = _classicassets.strings.characters
    return {
        'Kronk': c.kronk,
        'Zoe': c.zoe,
        'Jack Morgan': c.jack_morgan,
        'Mel': c.mel,
        'Snake Shadow': c.snake_shadow,
        'Bones': c.bones,
        'Bernard': c.bernard,
        'Agent Johnson': c.agent_johnson,
        'Frosty': c.frosty,
        'Pascal': c.pascal,
        'Pixel': c.pixel,
        'Grumbledorf': c.grumbledorf,
        'B-9000': c.b9000,
        'Santa Claus': c.santa_claus,
        'Easter Bunny': c.easter_bunny,
        'Taobao Mascot': c.taobao_mascot,
        'OldLady': c.betty,
        'Zola': c.lucky,
        'Butch': c.butch,
        'Gretel': c.gretel,
        'Lee': c.lee,
        'Middle-Man': c.middle_man,
        'Spaz': c.spaz,
        'Todd McBurton': c.todd_mcburton,
    }


@overload
def get_appearance_display_name(
    name: str, *, langstr: Literal[False] = False
) -> babase.Lstr: ...


@overload
def get_appearance_display_name(
    name: str, *, langstr: Literal[True]
) -> babase.LangStr: ...


def get_appearance_display_name(
    name: str, *, langstr: bool = False
) -> babase.Lstr | babase.LangStr:
    """Return a displayable name for a spaz appearance.

    ``name`` is an appearance's registered key (see
    :func:`get_appearances`). First-party characters resolve to their
    authored name; a mod's character (or one we have no entry for) is
    shown exactly as its key.

    Pass ``langstr=True`` to receive a :class:`~babase.LangStr`. The
    legacy :class:`~babase.Lstr` form goes away when api 9 support
    ends.
    """
    if langstr:
        entry = _character_name_table().get(name)
        return entry if entry is not None else babase.LangStr.from_text(name)
    return babase.Lstr(translate=('characterNames', name))


def get_appearances(
    include_locked: bool = False,
    purchases: Container[str] | None = None,
) -> list[str]:
    """Get the list of available spaz appearances.

    If ``purchases`` is None (the default), the local player's
    ``bs.app.classic.purchases`` set is used. Pass an explicit
    ``purchases`` container to get the list of characters owned by
    some other account (e.g. a remote player's authoritative list
    from the master server).
    """
    # pylint: disable=too-many-branches
    assert bs.app.classic is not None
    if purchases is None:
        plus = bs.app.plus
        assert plus is not None
        purchases = bs.app.classic.purchases

    disallowed = []
    if not include_locked:
        # Hmm yeah this'll be tough to hack...
        if 'characters.santa' not in purchases:
            disallowed.append('Santa Claus')
        if 'characters.frosty' not in purchases:
            disallowed.append('Frosty')
        if 'characters.bones' not in purchases:
            disallowed.append('Bones')
        if 'characters.bernard' not in purchases:
            disallowed.append('Bernard')
        if 'characters.pixie' not in purchases:
            disallowed.append('Pixel')
        if 'characters.pascal' not in purchases:
            disallowed.append('Pascal')
        if 'characters.actionhero' not in purchases:
            disallowed.append('Todd McBurton')
        if 'characters.taobaomascot' not in purchases:
            disallowed.append('Taobao Mascot')
        if 'characters.agent' not in purchases:
            disallowed.append('Agent Johnson')
        if 'characters.jumpsuit' not in purchases:
            disallowed.append('Lee')
        if 'characters.assassin' not in purchases:
            disallowed.append('Zola')
        if 'characters.wizard' not in purchases:
            disallowed.append('Grumbledorf')
        if 'characters.cowboy' not in purchases:
            disallowed.append('Butch')
        if 'characters.witch' not in purchases:
            disallowed.append('Witch')
        if 'characters.warrior' not in purchases:
            disallowed.append('Warrior')
        if 'characters.superhero' not in purchases:
            disallowed.append('Middle-Man')
        if 'characters.alien' not in purchases:
            disallowed.append('Alien')
        if 'characters.oldlady' not in purchases:
            disallowed.append('OldLady')
        if 'characters.gladiator' not in purchases:
            disallowed.append('Gladiator')
        if 'characters.wrestler' not in purchases:
            disallowed.append('Wrestler')
        if 'characters.operasinger' not in purchases:
            disallowed.append('Gretel')
        if 'characters.robot' not in purchases:
            disallowed.append('Robot')
        if 'characters.cyborg' not in purchases:
            disallowed.append('B-9000')
        if 'characters.bunny' not in purchases:
            disallowed.append('Easter Bunny')
        if 'characters.kronk' not in purchases:
            disallowed.append('Kronk')
        if 'characters.zoe' not in purchases:
            disallowed.append('Zoe')
        if 'characters.jackmorgan' not in purchases:
            disallowed.append('Jack Morgan')
        if 'characters.mel' not in purchases:
            disallowed.append('Mel')
        if 'characters.snakeshadow' not in purchases:
            disallowed.append('Snake Shadow')
    return [
        s
        for s in list(bs.app.classic.spaz_appearances.keys())
        if s not in disallowed
    ]


#: An appearance's texture field. Prefer a handle off an
#: asset-package wrapper (``_classicassets.textures.zoe_icon``); the bare
#: ``str`` form is the legacy asset name, kept so existing mods keep
#: working, and goes away when api 9 support ends.
type TexVal = str | bs.TextureHandle

#: An appearance's mesh field; see :obj:`TexVal`.
type MeshVal = str | bs.MeshHandle

#: An entry in one of an appearance's sound lists; see :obj:`TexVal`.
type SoundVal = str | bs.SoundHandle


def scene_texture(val: TexVal) -> bs.Texture:
    """Load an appearance texture field as a scene texture."""
    return (
        val.get() if isinstance(val, bs.TextureHandle) else bs.gettexture(val)
    )


def scene_mesh(val: MeshVal) -> bs.Mesh:
    """Load an appearance mesh field as a scene mesh."""
    return val.get() if isinstance(val, bs.MeshHandle) else bs.getmesh(val)


def scene_sound(val: SoundVal) -> bs.Sound:
    """Load an appearance sound entry as a scene sound."""
    return val.get() if isinstance(val, bs.SoundHandle) else bs.getsound(val)


def ui_texture(val: TexVal) -> bauiv1.Texture:
    """Load an appearance texture field as a ui texture.

    Converts a scene handle to its ui form (see
    :meth:`bascenev1.TextureHandle.ui`) -- appearances hold
    scene-form refs since they are otherwise scene data.
    """
    import bauiv1

    return (
        val.ui().get()
        if isinstance(val, bs.TextureHandle)
        else bauiv1.gettexture(val)
    )


def ui_sound(val: SoundVal) -> bauiv1.Sound:
    """Load an appearance sound entry as a ui sound; see :func:`ui_texture`."""
    import bauiv1

    return (
        val.ui().get()
        if isinstance(val, bs.SoundHandle)
        else bauiv1.getsound(val)
    )


def texture_spec(val: TexVal) -> TextureSpec:
    """An appearance texture field as a plain spec (for the wire/doc-ui).

    A handle *is* a :class:`~bacommon.assetspec.TextureSpec`, so
    this is a passthrough for the modern form, and a legacy *qualified*
    (``<apverid>:<name>``) string parses back into one.

    A legacy *bare* name (``'neoSpazIcon'``) carries no asset-package
    identity on its own -- only the engine's asset-name compat table
    knows where it now lives -- so it is resolved through that table
    (the same one the loaders use) before being split. A name with no
    known home falls back to the default character icon rather than
    yielding a malformed spec that would fail its package resolve and
    render blank on the far end.
    """
    if isinstance(val, bs.TextureHandle):
        return val
    qualified = babase.resolve_legacy_asset_name(val, 'textures')
    apverid, sep, name = qualified.partition(':')
    if not sep or not name:
        return _classicassets.textures.neo_spaz_icon
    return TextureSpec(apverid, name)


class Appearance:
    """Create and fill out one of these suckers to define a spaz appearance."""

    def __init__(self, name: str):
        assert bs.app.classic is not None
        self.name = name
        if self.name in bs.app.classic.spaz_appearances:
            raise RuntimeError(
                f'spaz appearance name "{self.name}" already exists.'
            )
        bs.app.classic.spaz_appearances[self.name] = self
        self.color_texture: TexVal = ''
        self.color_mask_texture: TexVal = ''
        self.icon_texture: TexVal = ''
        self.icon_mask_texture: TexVal = ''
        self.head_mesh: MeshVal = ''
        self.torso_mesh: MeshVal = ''
        self.pelvis_mesh: MeshVal = ''
        self.upper_arm_mesh: MeshVal = ''
        self.forearm_mesh: MeshVal = ''
        self.hand_mesh: MeshVal = ''
        self.upper_leg_mesh: MeshVal = ''
        self.lower_leg_mesh: MeshVal = ''
        self.toes_mesh: MeshVal = ''
        self.jump_sounds: Sequence[SoundVal] = []
        self.attack_sounds: Sequence[SoundVal] = []
        self.impact_sounds: Sequence[SoundVal] = []
        self.death_sounds: Sequence[SoundVal] = []
        self.pickup_sounds: Sequence[SoundVal] = []
        self.fall_sounds: Sequence[SoundVal] = []
        self.style = 'spaz'
        self.default_color: tuple[float, float, float] | None = None
        self.default_highlight: tuple[float, float, float] | None = None


def register_appearances() -> None:
    # pylint: disable=too-many-statements
    """Register our builtin spaz appearances."""

    # A big hand-written table; it wants to be data eventually.
    # pylint: disable=too-many-locals

    # Shorthands for the wrapper groups; these blocks are almost
    # entirely asset assignments and the full paths drown them out.
    tex = _classicassets.textures
    mesh = _classicassets.meshes
    snd = _classicassets.audio

    # Spaz #######################################
    a = Appearance('Spaz')
    a.color_texture = tex.neo_spaz_color
    a.color_mask_texture = tex.neo_spaz_color_mask
    a.icon_texture = tex.neo_spaz_icon
    a.icon_mask_texture = tex.neo_spaz_icon_color_mask
    a.head_mesh = mesh.neo_spaz_head
    a.torso_mesh = mesh.neo_spaz_torso
    a.pelvis_mesh = mesh.neo_spaz_pelvis
    a.upper_arm_mesh = mesh.neo_spaz_upper_arm
    a.forearm_mesh = mesh.neo_spaz_fore_arm
    a.hand_mesh = mesh.neo_spaz_hand
    a.upper_leg_mesh = mesh.neo_spaz_upper_leg
    a.lower_leg_mesh = mesh.neo_spaz_lower_leg
    a.toes_mesh = mesh.neo_spaz_toes
    a.jump_sounds = [
        snd.spaz_jump01,
        snd.spaz_jump02,
        snd.spaz_jump03,
        snd.spaz_jump04,
    ]
    a.attack_sounds = [
        snd.spaz_attack01,
        snd.spaz_attack02,
        snd.spaz_attack03,
        snd.spaz_attack04,
    ]
    a.impact_sounds = [
        snd.spaz_impact01,
        snd.spaz_impact02,
        snd.spaz_impact03,
        snd.spaz_impact04,
    ]
    a.death_sounds = [snd.spaz_death01]
    a.pickup_sounds = [snd.spaz_pickup01]
    a.fall_sounds = [snd.spaz_fall01]
    a.style = 'spaz'

    # Zoe #####################################
    a = Appearance('Zoe')
    a.color_texture = tex.zoe_color
    a.color_mask_texture = tex.zoe_color_mask
    a.icon_texture = tex.zoe_icon
    a.icon_mask_texture = tex.zoe_icon_color_mask
    a.head_mesh = mesh.zoe_head
    a.torso_mesh = mesh.zoe_torso
    a.pelvis_mesh = mesh.zoe_pelvis
    a.upper_arm_mesh = mesh.zoe_upper_arm
    a.forearm_mesh = mesh.zoe_fore_arm
    a.hand_mesh = mesh.zoe_hand
    a.upper_leg_mesh = mesh.zoe_upper_leg
    a.lower_leg_mesh = mesh.zoe_lower_leg
    a.toes_mesh = mesh.zoe_toes
    a.jump_sounds = [
        snd.zoe_jump01,
        snd.zoe_jump02,
        snd.zoe_jump03,
    ]
    a.attack_sounds = [
        snd.zoe_attack01,
        snd.zoe_attack02,
        snd.zoe_attack03,
        snd.zoe_attack04,
    ]
    a.impact_sounds = [
        snd.zoe_impact01,
        snd.zoe_impact02,
        snd.zoe_impact03,
        snd.zoe_impact04,
    ]
    a.death_sounds = [snd.zoe_death01]
    a.pickup_sounds = [snd.zoe_pickup01]
    a.fall_sounds = [snd.zoe_fall01]
    a.style = 'female'
    a.default_color = (0.6, 0.6, 0.6)
    a.default_highlight = (0, 1, 0)

    # Ninja ##########################################
    a = Appearance('Snake Shadow')
    a.color_texture = tex.ninja_color
    a.color_mask_texture = tex.ninja_color_mask
    a.icon_texture = tex.ninja_icon
    a.icon_mask_texture = tex.ninja_icon_color_mask
    a.head_mesh = mesh.ninja_head
    a.torso_mesh = mesh.ninja_torso
    a.pelvis_mesh = mesh.ninja_pelvis
    a.upper_arm_mesh = mesh.ninja_upper_arm
    a.forearm_mesh = mesh.ninja_fore_arm
    a.hand_mesh = mesh.ninja_hand
    a.upper_leg_mesh = mesh.ninja_upper_leg
    a.lower_leg_mesh = mesh.ninja_lower_leg
    a.toes_mesh = mesh.ninja_toes
    ninja_attacks = [
        snd.ninja_attack1,
        snd.ninja_attack2,
        snd.ninja_attack3,
        snd.ninja_attack4,
        snd.ninja_attack5,
        snd.ninja_attack6,
        snd.ninja_attack7,
    ]
    ninja_hits = [
        snd.ninja_hit1,
        snd.ninja_hit2,
        snd.ninja_hit3,
        snd.ninja_hit4,
        snd.ninja_hit5,
        snd.ninja_hit6,
        snd.ninja_hit7,
        snd.ninja_hit8,
    ]
    ninja_jumps = [
        snd.ninja_attack1,
        snd.ninja_attack2,
        snd.ninja_attack3,
        snd.ninja_attack4,
        snd.ninja_attack5,
        snd.ninja_attack6,
        snd.ninja_attack7,
    ]
    a.jump_sounds = ninja_jumps
    a.attack_sounds = ninja_attacks
    a.impact_sounds = ninja_hits
    a.death_sounds = [snd.ninja_death1]
    a.pickup_sounds = ninja_attacks
    a.fall_sounds = [snd.ninja_fall1]
    a.style = 'ninja'
    a.default_color = (1, 1, 1)
    a.default_highlight = (0.55, 0.8, 0.55)

    # Barbarian #####################################
    a = Appearance('Kronk')
    a.color_texture = tex.kronk
    a.color_mask_texture = tex.kronk_color_mask
    a.icon_texture = tex.kronk_icon
    a.icon_mask_texture = tex.kronk_icon_color_mask
    a.head_mesh = mesh.kronk_head
    a.torso_mesh = mesh.kronk_torso
    a.pelvis_mesh = mesh.kronk_pelvis
    a.upper_arm_mesh = mesh.kronk_upper_arm
    a.forearm_mesh = mesh.kronk_fore_arm
    a.hand_mesh = mesh.kronk_hand
    a.upper_leg_mesh = mesh.kronk_upper_leg
    a.lower_leg_mesh = mesh.kronk_lower_leg
    a.toes_mesh = mesh.kronk_toes
    kronk_sounds = [
        snd.kronk1,
        snd.kronk2,
        snd.kronk3,
        snd.kronk4,
        snd.kronk5,
        snd.kronk6,
        snd.kronk7,
        snd.kronk8,
        snd.kronk9,
        snd.kronk10,
    ]
    a.jump_sounds = kronk_sounds
    a.attack_sounds = kronk_sounds
    a.impact_sounds = kronk_sounds
    a.death_sounds = [snd.kronk_death]
    a.pickup_sounds = kronk_sounds
    a.fall_sounds = [snd.kronk_fall]
    a.style = 'kronk'
    a.default_color = (0.4, 0.5, 0.4)
    a.default_highlight = (1, 0.5, 0.3)

    # Chef ###########################################
    a = Appearance('Mel')
    a.color_texture = tex.mel_color
    a.color_mask_texture = tex.mel_color_mask
    a.icon_texture = tex.mel_icon
    a.icon_mask_texture = tex.mel_icon_color_mask
    a.head_mesh = mesh.mel_head
    a.torso_mesh = mesh.mel_torso
    a.pelvis_mesh = mesh.kronk_pelvis
    a.upper_arm_mesh = mesh.mel_upper_arm
    a.forearm_mesh = mesh.mel_fore_arm
    a.hand_mesh = mesh.mel_hand
    a.upper_leg_mesh = mesh.mel_upper_leg
    a.lower_leg_mesh = mesh.mel_lower_leg
    a.toes_mesh = mesh.mel_toes
    mel_sounds = [
        snd.mel01,
        snd.mel02,
        snd.mel03,
        snd.mel04,
        snd.mel05,
        snd.mel06,
        snd.mel07,
        snd.mel08,
        snd.mel09,
        snd.mel10,
    ]
    a.jump_sounds = mel_sounds
    a.attack_sounds = mel_sounds
    a.impact_sounds = mel_sounds
    a.death_sounds = [snd.mel_death01]
    a.pickup_sounds = mel_sounds
    a.fall_sounds = [snd.mel_fall01]
    a.style = 'mel'
    a.default_color = (1, 1, 1)
    a.default_highlight = (0.1, 0.6, 0.1)

    # Pirate #######################################
    a = Appearance('Jack Morgan')
    a.color_texture = tex.jack_color
    a.color_mask_texture = tex.jack_color_mask
    a.icon_texture = tex.jack_icon
    a.icon_mask_texture = tex.jack_icon_color_mask
    a.head_mesh = mesh.jack_head
    a.torso_mesh = mesh.jack_torso
    a.pelvis_mesh = mesh.kronk_pelvis
    a.upper_arm_mesh = mesh.jack_upper_arm
    a.forearm_mesh = mesh.jack_fore_arm
    a.hand_mesh = mesh.jack_hand
    a.upper_leg_mesh = mesh.jack_upper_leg
    a.lower_leg_mesh = mesh.jack_lower_leg
    a.toes_mesh = mesh.jack_toes
    hit_sounds = [
        snd.jack_hit01,
        snd.jack_hit02,
        snd.jack_hit03,
        snd.jack_hit04,
        snd.jack_hit05,
        snd.jack_hit06,
        snd.jack_hit07,
    ]
    sounds = [
        snd.jack01,
        snd.jack02,
        snd.jack03,
        snd.jack04,
        snd.jack05,
        snd.jack06,
    ]
    a.jump_sounds = sounds
    a.attack_sounds = sounds
    a.impact_sounds = hit_sounds
    a.death_sounds = [snd.jack_death01]
    a.pickup_sounds = sounds
    a.fall_sounds = [snd.jack_fall01]
    a.style = 'pirate'
    a.default_color = (1, 0.2, 0.1)
    a.default_highlight = (1, 1, 0)

    # Santa ######################################
    a = Appearance('Santa Claus')
    a.color_texture = tex.santa_color
    a.color_mask_texture = tex.santa_color_mask
    a.icon_texture = tex.santa_icon
    a.icon_mask_texture = tex.santa_icon_color_mask
    a.head_mesh = mesh.santa_head
    a.torso_mesh = mesh.santa_torso
    a.pelvis_mesh = mesh.kronk_pelvis
    a.upper_arm_mesh = mesh.santa_upper_arm
    a.forearm_mesh = mesh.santa_fore_arm
    a.hand_mesh = mesh.santa_hand
    a.upper_leg_mesh = mesh.santa_upper_leg
    a.lower_leg_mesh = mesh.santa_lower_leg
    a.toes_mesh = mesh.santa_toes
    hit_sounds = [
        snd.santa_hit01,
        snd.santa_hit02,
        snd.santa_hit03,
        snd.santa_hit04,
    ]
    sounds = [
        snd.santa01,
        snd.santa02,
        snd.santa03,
        snd.santa04,
        snd.santa05,
    ]
    a.jump_sounds = sounds
    a.attack_sounds = sounds
    a.impact_sounds = hit_sounds
    a.death_sounds = [snd.santa_death]
    a.pickup_sounds = sounds
    a.fall_sounds = [snd.santa_fall]
    a.style = 'santa'
    a.default_color = (1, 0, 0)
    a.default_highlight = (1, 1, 1)

    # Snowman ###################################
    a = Appearance('Frosty')
    a.color_texture = tex.frosty_color
    a.color_mask_texture = tex.frosty_color_mask
    a.icon_texture = tex.frosty_icon
    a.icon_mask_texture = tex.frosty_icon_color_mask
    a.head_mesh = mesh.frosty_head
    a.torso_mesh = mesh.frosty_torso
    a.pelvis_mesh = mesh.frosty_pelvis
    a.upper_arm_mesh = mesh.frosty_upper_arm
    a.forearm_mesh = mesh.frosty_fore_arm
    a.hand_mesh = mesh.frosty_hand
    a.upper_leg_mesh = mesh.frosty_upper_leg
    a.lower_leg_mesh = mesh.frosty_lower_leg
    a.toes_mesh = mesh.frosty_toes
    frosty_sounds = [
        snd.frosty01,
        snd.frosty02,
        snd.frosty03,
        snd.frosty04,
        snd.frosty05,
    ]
    frosty_hit_sounds = [
        snd.frosty_hit01,
        snd.frosty_hit02,
        snd.frosty_hit03,
    ]
    a.jump_sounds = frosty_sounds
    a.attack_sounds = frosty_sounds
    a.impact_sounds = frosty_hit_sounds
    a.death_sounds = [snd.frosty_death]
    a.pickup_sounds = frosty_sounds
    a.fall_sounds = [snd.frosty_fall]
    a.style = 'frosty'
    a.default_color = (0.5, 0.5, 1)
    a.default_highlight = (1, 0.5, 0)

    # Skeleton ################################
    a = Appearance('Bones')
    a.color_texture = tex.bones_color
    a.color_mask_texture = tex.bones_color_mask
    a.icon_texture = tex.bones_icon
    a.icon_mask_texture = tex.bones_icon_color_mask
    a.head_mesh = mesh.bones_head
    a.torso_mesh = mesh.bones_torso
    a.pelvis_mesh = mesh.bones_pelvis
    a.upper_arm_mesh = mesh.bones_upper_arm
    a.forearm_mesh = mesh.bones_fore_arm
    a.hand_mesh = mesh.bones_hand
    a.upper_leg_mesh = mesh.bones_upper_leg
    a.lower_leg_mesh = mesh.bones_lower_leg
    a.toes_mesh = mesh.bones_toes
    bones_sounds = [
        snd.bones1,
        snd.bones2,
        snd.bones3,
    ]
    bones_hit_sounds = [
        snd.bones1,
        snd.bones2,
        snd.bones3,
    ]
    a.jump_sounds = bones_sounds
    a.attack_sounds = bones_sounds
    a.impact_sounds = bones_hit_sounds
    a.death_sounds = [snd.bones_death]
    a.pickup_sounds = bones_sounds
    a.fall_sounds = [snd.bones_fall]
    a.style = 'bones'
    a.default_color = (0.6, 0.9, 1)
    a.default_highlight = (0.6, 0.9, 1)

    # Bear ###################################
    a = Appearance('Bernard')
    a.color_texture = tex.bear_color
    a.color_mask_texture = tex.bear_color_mask
    a.icon_texture = tex.bear_icon
    a.icon_mask_texture = tex.bear_icon_color_mask
    a.head_mesh = mesh.bear_head
    a.torso_mesh = mesh.bear_torso
    a.pelvis_mesh = mesh.bear_pelvis
    a.upper_arm_mesh = mesh.bear_upper_arm
    a.forearm_mesh = mesh.bear_fore_arm
    a.hand_mesh = mesh.bear_hand
    a.upper_leg_mesh = mesh.bear_upper_leg
    a.lower_leg_mesh = mesh.bear_lower_leg
    a.toes_mesh = mesh.bear_toes
    bear_sounds = [
        snd.bear1,
        snd.bear2,
        snd.bear3,
        snd.bear4,
    ]
    bear_hit_sounds = [
        snd.bear_hit1,
        snd.bear_hit2,
    ]
    a.jump_sounds = bear_sounds
    a.attack_sounds = bear_sounds
    a.impact_sounds = bear_hit_sounds
    a.death_sounds = [snd.bear_death]
    a.pickup_sounds = bear_sounds
    a.fall_sounds = [snd.bear_fall]
    a.style = 'bear'
    a.default_color = (0.7, 0.5, 0.0)

    # Penguin ###################################
    a = Appearance('Pascal')
    a.color_texture = tex.penguin_color
    a.color_mask_texture = tex.penguin_color_mask
    a.icon_texture = tex.penguin_icon
    a.icon_mask_texture = tex.penguin_icon_color_mask
    a.head_mesh = mesh.penguin_head
    a.torso_mesh = mesh.penguin_torso
    a.pelvis_mesh = mesh.penguin_pelvis
    a.upper_arm_mesh = mesh.penguin_upper_arm
    a.forearm_mesh = mesh.penguin_fore_arm
    a.hand_mesh = mesh.penguin_hand
    a.upper_leg_mesh = mesh.penguin_upper_leg
    a.lower_leg_mesh = mesh.penguin_lower_leg
    a.toes_mesh = mesh.penguin_toes
    penguin_sounds = [
        snd.penguin1,
        snd.penguin2,
        snd.penguin3,
        snd.penguin4,
    ]
    penguin_hit_sounds = [
        snd.penguin_hit1,
        snd.penguin_hit2,
    ]
    a.jump_sounds = penguin_sounds
    a.attack_sounds = penguin_sounds
    a.impact_sounds = penguin_hit_sounds
    a.death_sounds = [snd.penguin_death]
    a.pickup_sounds = penguin_sounds
    a.fall_sounds = [snd.penguin_fall]
    a.style = 'penguin'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Ali ###################################
    a = Appearance('Taobao Mascot')
    a.color_texture = tex.ali_color
    a.color_mask_texture = tex.ali_color_mask
    a.icon_texture = tex.ali_icon
    a.icon_mask_texture = tex.ali_icon_color_mask
    a.head_mesh = mesh.ali_head
    a.torso_mesh = mesh.ali_torso
    a.pelvis_mesh = mesh.ali_pelvis
    a.upper_arm_mesh = mesh.ali_upper_arm
    a.forearm_mesh = mesh.ali_fore_arm
    a.hand_mesh = mesh.ali_hand
    a.upper_leg_mesh = mesh.ali_upper_leg
    a.lower_leg_mesh = mesh.ali_lower_leg
    a.toes_mesh = mesh.ali_toes
    ali_sounds = [
        snd.ali1,
        snd.ali2,
        snd.ali3,
        snd.ali4,
    ]
    ali_hit_sounds = [
        snd.ali_hit1,
        snd.ali_hit2,
    ]
    a.jump_sounds = ali_sounds
    a.attack_sounds = ali_sounds
    a.impact_sounds = ali_hit_sounds
    a.death_sounds = [snd.ali_death]
    a.pickup_sounds = ali_sounds
    a.fall_sounds = [snd.ali_fall]
    a.style = 'ali'
    a.default_color = (1, 0.5, 0)
    a.default_highlight = (1, 1, 1)

    # Cyborg ###################################
    a = Appearance('B-9000')
    a.color_texture = tex.cyborg_color
    a.color_mask_texture = tex.cyborg_color_mask
    a.icon_texture = tex.cyborg_icon
    a.icon_mask_texture = tex.cyborg_icon_color_mask
    a.head_mesh = mesh.cyborg_head
    a.torso_mesh = mesh.cyborg_torso
    a.pelvis_mesh = mesh.cyborg_pelvis
    a.upper_arm_mesh = mesh.cyborg_upper_arm
    a.forearm_mesh = mesh.cyborg_fore_arm
    a.hand_mesh = mesh.cyborg_hand
    a.upper_leg_mesh = mesh.cyborg_upper_leg
    a.lower_leg_mesh = mesh.cyborg_lower_leg
    a.toes_mesh = mesh.cyborg_toes
    cyborg_sounds = [
        snd.cyborg1,
        snd.cyborg2,
        snd.cyborg3,
        snd.cyborg4,
    ]
    cyborg_hit_sounds = [
        snd.cyborg_hit1,
        snd.cyborg_hit2,
    ]
    a.jump_sounds = cyborg_sounds
    a.attack_sounds = cyborg_sounds
    a.impact_sounds = cyborg_hit_sounds
    a.death_sounds = [snd.cyborg_death]
    a.pickup_sounds = cyborg_sounds
    a.fall_sounds = [snd.cyborg_fall]
    a.style = 'cyborg'
    a.default_color = (0.5, 0.5, 0.5)
    a.default_highlight = (1, 0, 0)

    # Agent ###################################
    a = Appearance('Agent Johnson')
    a.color_texture = tex.agent_color
    a.color_mask_texture = tex.agent_color_mask
    a.icon_texture = tex.agent_icon
    a.icon_mask_texture = tex.agent_icon_color_mask
    a.head_mesh = mesh.agent_head
    a.torso_mesh = mesh.agent_torso
    a.pelvis_mesh = mesh.agent_pelvis
    a.upper_arm_mesh = mesh.agent_upper_arm
    a.forearm_mesh = mesh.agent_fore_arm
    a.hand_mesh = mesh.agent_hand
    a.upper_leg_mesh = mesh.agent_upper_leg
    a.lower_leg_mesh = mesh.agent_lower_leg
    a.toes_mesh = mesh.agent_toes
    agent_sounds = [
        snd.agent1,
        snd.agent2,
        snd.agent3,
        snd.agent4,
    ]
    agent_hit_sounds = [
        snd.agent_hit1,
        snd.agent_hit2,
    ]
    a.jump_sounds = agent_sounds
    a.attack_sounds = agent_sounds
    a.impact_sounds = agent_hit_sounds
    a.death_sounds = [snd.agent_death]
    a.pickup_sounds = agent_sounds
    a.fall_sounds = [snd.agent_fall]
    a.style = 'agent'
    a.default_color = (0.3, 0.3, 0.33)
    a.default_highlight = (1, 0.5, 0.3)

    # Jumpsuit ###################################
    a = Appearance('Lee')
    a.color_texture = tex.jumpsuit_color
    a.color_mask_texture = tex.jumpsuit_color_mask
    a.icon_texture = tex.jumpsuit_icon
    a.icon_mask_texture = tex.jumpsuit_icon_color_mask
    a.head_mesh = mesh.jumpsuit_head
    a.torso_mesh = mesh.jumpsuit_torso
    a.pelvis_mesh = mesh.jumpsuit_pelvis
    a.upper_arm_mesh = mesh.jumpsuit_upper_arm
    a.forearm_mesh = mesh.jumpsuit_fore_arm
    a.hand_mesh = mesh.jumpsuit_hand
    a.upper_leg_mesh = mesh.jumpsuit_upper_leg
    a.lower_leg_mesh = mesh.jumpsuit_lower_leg
    a.toes_mesh = mesh.jumpsuit_toes
    jumpsuit_sounds = [
        snd.jumpsuit1,
        snd.jumpsuit2,
        snd.jumpsuit3,
        snd.jumpsuit4,
    ]
    jumpsuit_hit_sounds = [
        snd.jumpsuit_hit1,
        snd.jumpsuit_hit2,
    ]
    a.jump_sounds = jumpsuit_sounds
    a.attack_sounds = jumpsuit_sounds
    a.impact_sounds = jumpsuit_hit_sounds
    a.death_sounds = [snd.jumpsuit_death]
    a.pickup_sounds = jumpsuit_sounds
    a.fall_sounds = [snd.jumpsuit_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # ActionHero ###################################
    a = Appearance('Todd McBurton')
    a.color_texture = tex.action_hero_color
    a.color_mask_texture = tex.action_hero_color_mask
    a.icon_texture = tex.action_hero_icon
    a.icon_mask_texture = tex.action_hero_icon_color_mask
    a.head_mesh = mesh.action_hero_head
    a.torso_mesh = mesh.action_hero_torso
    a.pelvis_mesh = mesh.action_hero_pelvis
    a.upper_arm_mesh = mesh.action_hero_upper_arm
    a.forearm_mesh = mesh.action_hero_fore_arm
    a.hand_mesh = mesh.action_hero_hand
    a.upper_leg_mesh = mesh.action_hero_upper_leg
    a.lower_leg_mesh = mesh.action_hero_lower_leg
    a.toes_mesh = mesh.action_hero_toes
    action_hero_sounds = [
        snd.action_hero1,
        snd.action_hero2,
        snd.action_hero3,
        snd.action_hero4,
    ]
    action_hero_hit_sounds = [
        snd.action_hero_hit1,
        snd.action_hero_hit2,
    ]
    a.jump_sounds = action_hero_sounds
    a.attack_sounds = action_hero_sounds
    a.impact_sounds = action_hero_hit_sounds
    a.death_sounds = [snd.action_hero_death]
    a.pickup_sounds = action_hero_sounds
    a.fall_sounds = [snd.action_hero_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Lucky the Leprechaun ############################
    #
    # Note: repurposing assassin slot. Lucky is not actually an
    # assassin. He is a good and friendly Leprechaun.
    a = Appearance('Zola')
    a.color_texture = tex.assassin_color
    a.color_mask_texture = tex.assassin_color_mask
    a.icon_texture = tex.assassin_icon
    a.icon_mask_texture = tex.assassin_icon_color_mask
    a.head_mesh = mesh.assassin_head
    a.torso_mesh = mesh.assassin_torso
    a.pelvis_mesh = mesh.assassin_pelvis
    a.upper_arm_mesh = mesh.assassin_upper_arm
    a.forearm_mesh = mesh.assassin_fore_arm
    a.hand_mesh = mesh.assassin_hand
    a.upper_leg_mesh = mesh.assassin_upper_leg
    a.lower_leg_mesh = mesh.assassin_lower_leg
    a.toes_mesh = mesh.assassin_toes
    assassin_sounds = [
        snd.assassin1,
        snd.assassin2,
        snd.assassin3,
        snd.assassin4,
    ]
    assassin_hit_sounds = [
        snd.assassin_hit1,
        snd.assassin_hit2,
    ]
    a.jump_sounds = assassin_sounds
    a.attack_sounds = assassin_sounds
    a.impact_sounds = assassin_hit_sounds
    a.death_sounds = [snd.assassin_death]
    a.pickup_sounds = assassin_sounds
    a.fall_sounds = [snd.assassin_fall]
    a.style = 'spaz'
    a.default_color = (0.2, 1.0, 0.5)
    a.default_highlight = (1.0, 0.3, 0)

    # Wizard ###################################
    a = Appearance('Grumbledorf')
    a.color_texture = tex.wizard_color
    a.color_mask_texture = tex.wizard_color_mask
    a.icon_texture = tex.wizard_icon
    a.icon_mask_texture = tex.wizard_icon_color_mask
    a.head_mesh = mesh.wizard_head
    a.torso_mesh = mesh.wizard_torso
    a.pelvis_mesh = mesh.wizard_pelvis
    a.upper_arm_mesh = mesh.wizard_upper_arm
    a.forearm_mesh = mesh.wizard_fore_arm
    a.hand_mesh = mesh.wizard_hand
    a.upper_leg_mesh = mesh.wizard_upper_leg
    a.lower_leg_mesh = mesh.wizard_lower_leg
    a.toes_mesh = mesh.wizard_toes
    wizard_sounds = [
        snd.wizard1,
        snd.wizard2,
        snd.wizard3,
        snd.wizard4,
    ]
    wizard_hit_sounds = [
        snd.wizard_hit1,
        snd.wizard_hit2,
    ]
    a.jump_sounds = wizard_sounds
    a.attack_sounds = wizard_sounds
    a.impact_sounds = wizard_hit_sounds
    a.death_sounds = [snd.wizard_death]
    a.pickup_sounds = wizard_sounds
    a.fall_sounds = [snd.wizard_fall]
    a.style = 'spaz'
    a.default_color = (0.2, 0.4, 1.0)
    a.default_highlight = (0.06, 0.15, 0.4)

    # Cowboy ###################################
    a = Appearance('Butch')
    a.color_texture = tex.cowboy_color
    a.color_mask_texture = tex.cowboy_color_mask
    a.icon_texture = tex.cowboy_icon
    a.icon_mask_texture = tex.cowboy_icon_color_mask
    a.head_mesh = mesh.cowboy_head
    a.torso_mesh = mesh.cowboy_torso
    a.pelvis_mesh = mesh.cowboy_pelvis
    a.upper_arm_mesh = mesh.cowboy_upper_arm
    a.forearm_mesh = mesh.cowboy_fore_arm
    a.hand_mesh = mesh.cowboy_hand
    a.upper_leg_mesh = mesh.cowboy_upper_leg
    a.lower_leg_mesh = mesh.cowboy_lower_leg
    a.toes_mesh = mesh.cowboy_toes
    cowboy_sounds = [
        snd.cowboy1,
        snd.cowboy2,
        snd.cowboy3,
        snd.cowboy4,
    ]
    cowboy_hit_sounds = [
        snd.cowboy_hit1,
        snd.cowboy_hit2,
    ]
    a.jump_sounds = cowboy_sounds
    a.attack_sounds = cowboy_sounds
    a.impact_sounds = cowboy_hit_sounds
    a.death_sounds = [snd.cowboy_death]
    a.pickup_sounds = cowboy_sounds
    a.fall_sounds = [snd.cowboy_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Witch ###################################
    a = Appearance('Witch')
    a.color_texture = tex.witch_color
    a.color_mask_texture = tex.witch_color_mask
    a.icon_texture = tex.witch_icon
    a.icon_mask_texture = tex.witch_icon_color_mask
    a.head_mesh = mesh.witch_head
    a.torso_mesh = mesh.witch_torso
    a.pelvis_mesh = mesh.witch_pelvis
    a.upper_arm_mesh = mesh.witch_upper_arm
    a.forearm_mesh = mesh.witch_fore_arm
    a.hand_mesh = mesh.witch_hand
    a.upper_leg_mesh = mesh.witch_upper_leg
    a.lower_leg_mesh = mesh.witch_lower_leg
    a.toes_mesh = mesh.witch_toes
    witch_sounds = [
        snd.witch1,
        snd.witch2,
        snd.witch3,
        snd.witch4,
    ]
    witch_hit_sounds = [
        snd.witch_hit1,
        snd.witch_hit2,
    ]
    a.jump_sounds = witch_sounds
    a.attack_sounds = witch_sounds
    a.impact_sounds = witch_hit_sounds
    a.death_sounds = [snd.witch_death]
    a.pickup_sounds = witch_sounds
    a.fall_sounds = [snd.witch_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Warrior ###################################
    a = Appearance('Warrior')
    a.color_texture = tex.warrior_color
    a.color_mask_texture = tex.warrior_color_mask
    a.icon_texture = tex.warrior_icon
    a.icon_mask_texture = tex.warrior_icon_color_mask
    a.head_mesh = mesh.warrior_head
    a.torso_mesh = mesh.warrior_torso
    a.pelvis_mesh = mesh.warrior_pelvis
    a.upper_arm_mesh = mesh.warrior_upper_arm
    a.forearm_mesh = mesh.warrior_fore_arm
    a.hand_mesh = mesh.warrior_hand
    a.upper_leg_mesh = mesh.warrior_upper_leg
    a.lower_leg_mesh = mesh.warrior_lower_leg
    a.toes_mesh = mesh.warrior_toes
    warrior_sounds = [
        snd.warrior1,
        snd.warrior2,
        snd.warrior3,
        snd.warrior4,
    ]
    warrior_hit_sounds = [
        snd.warrior_hit1,
        snd.warrior_hit2,
    ]
    a.jump_sounds = warrior_sounds
    a.attack_sounds = warrior_sounds
    a.impact_sounds = warrior_hit_sounds
    a.death_sounds = [snd.warrior_death]
    a.pickup_sounds = warrior_sounds
    a.fall_sounds = [snd.warrior_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Superhero ###################################
    a = Appearance('Middle-Man')
    a.color_texture = tex.superhero_color
    a.color_mask_texture = tex.superhero_color_mask
    a.icon_texture = tex.superhero_icon
    a.icon_mask_texture = tex.superhero_icon_color_mask
    a.head_mesh = mesh.superhero_head
    a.torso_mesh = mesh.superhero_torso
    a.pelvis_mesh = mesh.superhero_pelvis
    a.upper_arm_mesh = mesh.superhero_upper_arm
    a.forearm_mesh = mesh.superhero_fore_arm
    a.hand_mesh = mesh.superhero_hand
    a.upper_leg_mesh = mesh.superhero_upper_leg
    a.lower_leg_mesh = mesh.superhero_lower_leg
    a.toes_mesh = mesh.superhero_toes
    superhero_sounds = [
        snd.superhero1,
        snd.superhero2,
        snd.superhero3,
        snd.superhero4,
    ]
    superhero_hit_sounds = [
        snd.superhero_hit1,
        snd.superhero_hit2,
    ]
    a.jump_sounds = superhero_sounds
    a.attack_sounds = superhero_sounds
    a.impact_sounds = superhero_hit_sounds
    a.death_sounds = [snd.superhero_death]
    a.pickup_sounds = superhero_sounds
    a.fall_sounds = [snd.superhero_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Alien ###################################
    a = Appearance('Alien')
    a.color_texture = tex.alien_color
    a.color_mask_texture = tex.alien_color_mask
    a.icon_texture = tex.alien_icon
    a.icon_mask_texture = tex.alien_icon_color_mask
    a.head_mesh = mesh.alien_head
    a.torso_mesh = mesh.alien_torso
    a.pelvis_mesh = mesh.alien_pelvis
    a.upper_arm_mesh = mesh.alien_upper_arm
    a.forearm_mesh = mesh.alien_fore_arm
    a.hand_mesh = mesh.alien_hand
    a.upper_leg_mesh = mesh.alien_upper_leg
    a.lower_leg_mesh = mesh.alien_lower_leg
    a.toes_mesh = mesh.alien_toes
    alien_sounds = [
        snd.alien1,
        snd.alien2,
        snd.alien3,
        snd.alien4,
    ]
    alien_hit_sounds = [
        snd.alien_hit1,
        snd.alien_hit2,
    ]
    a.jump_sounds = alien_sounds
    a.attack_sounds = alien_sounds
    a.impact_sounds = alien_hit_sounds
    a.death_sounds = [snd.alien_death]
    a.pickup_sounds = alien_sounds
    a.fall_sounds = [snd.alien_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # OldLady ###################################
    a = Appearance('OldLady')
    a.color_texture = tex.old_lady_color
    a.color_mask_texture = tex.old_lady_color_mask
    a.icon_texture = tex.old_lady_icon
    a.icon_mask_texture = tex.old_lady_icon_color_mask
    a.head_mesh = mesh.old_lady_head
    a.torso_mesh = mesh.old_lady_torso
    a.pelvis_mesh = mesh.old_lady_pelvis
    a.upper_arm_mesh = mesh.old_lady_upper_arm
    a.forearm_mesh = mesh.old_lady_fore_arm
    a.hand_mesh = mesh.old_lady_hand
    a.upper_leg_mesh = mesh.old_lady_upper_leg
    a.lower_leg_mesh = mesh.old_lady_lower_leg
    a.toes_mesh = mesh.old_lady_toes
    old_lady_sounds = [
        snd.old_lady1,
        snd.old_lady2,
        snd.old_lady3,
        snd.old_lady4,
    ]
    old_lady_hit_sounds = [
        snd.old_lady_hit1,
        snd.old_lady_hit2,
    ]
    a.jump_sounds = old_lady_sounds
    a.attack_sounds = old_lady_sounds
    a.impact_sounds = old_lady_hit_sounds
    a.death_sounds = [snd.old_lady_death]
    a.pickup_sounds = old_lady_sounds
    a.fall_sounds = [snd.old_lady_fall]
    a.style = 'bones'
    a.default_color = (0.2, 1.0, 1.0)
    a.default_highlight = (0.5, 0.25, 1.0)

    # Gladiator ###################################
    a = Appearance('Gladiator')
    a.color_texture = tex.gladiator_color
    a.color_mask_texture = tex.gladiator_color_mask
    a.icon_texture = tex.gladiator_icon
    a.icon_mask_texture = tex.gladiator_icon_color_mask
    a.head_mesh = mesh.gladiator_head
    a.torso_mesh = mesh.gladiator_torso
    a.pelvis_mesh = mesh.gladiator_pelvis
    a.upper_arm_mesh = mesh.gladiator_upper_arm
    a.forearm_mesh = mesh.gladiator_fore_arm
    a.hand_mesh = mesh.gladiator_hand
    a.upper_leg_mesh = mesh.gladiator_upper_leg
    a.lower_leg_mesh = mesh.gladiator_lower_leg
    a.toes_mesh = mesh.gladiator_toes
    gladiator_sounds = [
        snd.gladiator1,
        snd.gladiator2,
        snd.gladiator3,
        snd.gladiator4,
    ]
    gladiator_hit_sounds = [
        snd.gladiator_hit1,
        snd.gladiator_hit2,
    ]
    a.jump_sounds = gladiator_sounds
    a.attack_sounds = gladiator_sounds
    a.impact_sounds = gladiator_hit_sounds
    a.death_sounds = [snd.gladiator_death]
    a.pickup_sounds = gladiator_sounds
    a.fall_sounds = [snd.gladiator_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Wrestler ###################################
    a = Appearance('Wrestler')
    a.color_texture = tex.wrestler_color
    a.color_mask_texture = tex.wrestler_color_mask
    a.icon_texture = tex.wrestler_icon
    a.icon_mask_texture = tex.wrestler_icon_color_mask
    a.head_mesh = mesh.wrestler_head
    a.torso_mesh = mesh.wrestler_torso
    a.pelvis_mesh = mesh.wrestler_pelvis
    a.upper_arm_mesh = mesh.wrestler_upper_arm
    a.forearm_mesh = mesh.wrestler_fore_arm
    a.hand_mesh = mesh.wrestler_hand
    a.upper_leg_mesh = mesh.wrestler_upper_leg
    a.lower_leg_mesh = mesh.wrestler_lower_leg
    a.toes_mesh = mesh.wrestler_toes
    wrestler_sounds = [
        snd.wrestler1,
        snd.wrestler2,
        snd.wrestler3,
        snd.wrestler4,
    ]
    wrestler_hit_sounds = [
        snd.wrestler_hit1,
        snd.wrestler_hit2,
    ]
    a.jump_sounds = wrestler_sounds
    a.attack_sounds = wrestler_sounds
    a.impact_sounds = wrestler_hit_sounds
    a.death_sounds = [snd.wrestler_death]
    a.pickup_sounds = wrestler_sounds
    a.fall_sounds = [snd.wrestler_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # OperaSinger ###################################
    a = Appearance('Gretel')
    a.color_texture = tex.opera_singer_color
    a.color_mask_texture = tex.opera_singer_color_mask
    a.icon_texture = tex.opera_singer_icon
    a.icon_mask_texture = tex.opera_singer_icon_color_mask
    a.head_mesh = mesh.opera_singer_head
    a.torso_mesh = mesh.opera_singer_torso
    a.pelvis_mesh = mesh.opera_singer_pelvis
    a.upper_arm_mesh = mesh.opera_singer_upper_arm
    a.forearm_mesh = mesh.opera_singer_fore_arm
    a.hand_mesh = mesh.opera_singer_hand
    a.upper_leg_mesh = mesh.opera_singer_upper_leg
    a.lower_leg_mesh = mesh.opera_singer_lower_leg
    a.toes_mesh = mesh.opera_singer_toes
    opera_singer_sounds = [
        snd.opera_singer1,
        snd.opera_singer2,
        snd.opera_singer3,
        snd.opera_singer4,
    ]
    opera_singer_hit_sounds = [
        snd.opera_singer_hit1,
        snd.opera_singer_hit2,
    ]
    a.jump_sounds = opera_singer_sounds
    a.attack_sounds = opera_singer_sounds
    a.impact_sounds = opera_singer_hit_sounds
    a.death_sounds = [snd.opera_singer_death]
    a.pickup_sounds = opera_singer_sounds
    a.fall_sounds = [snd.opera_singer_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Pixie ###################################
    a = Appearance('Pixel')
    a.color_texture = tex.pixie_color
    a.color_mask_texture = tex.pixie_color_mask
    a.icon_texture = tex.pixie_icon
    a.icon_mask_texture = tex.pixie_icon_color_mask
    a.head_mesh = mesh.pixie_head
    a.torso_mesh = mesh.pixie_torso
    a.pelvis_mesh = mesh.pixie_pelvis
    a.upper_arm_mesh = mesh.pixie_upper_arm
    a.forearm_mesh = mesh.pixie_fore_arm
    a.hand_mesh = mesh.pixie_hand
    a.upper_leg_mesh = mesh.pixie_upper_leg
    a.lower_leg_mesh = mesh.pixie_lower_leg
    a.toes_mesh = mesh.pixie_toes
    pixie_sounds = [
        snd.pixie1,
        snd.pixie2,
        snd.pixie3,
        snd.pixie4,
    ]
    pixie_hit_sounds = [
        snd.pixie_hit1,
        snd.pixie_hit2,
    ]
    a.jump_sounds = pixie_sounds
    a.attack_sounds = pixie_sounds
    a.impact_sounds = pixie_hit_sounds
    a.death_sounds = [snd.pixie_death]
    a.pickup_sounds = pixie_sounds
    a.fall_sounds = [snd.pixie_fall]
    a.style = 'pixie'
    a.default_color = (0, 1, 0.7)
    a.default_highlight = (0.65, 0.35, 0.75)

    # Robot ###################################
    a = Appearance('Robot')
    a.color_texture = tex.robot_color
    a.color_mask_texture = tex.robot_color_mask
    a.icon_texture = tex.robot_icon
    a.icon_mask_texture = tex.robot_icon_color_mask
    a.head_mesh = mesh.robot_head
    a.torso_mesh = mesh.robot_torso
    a.pelvis_mesh = mesh.robot_pelvis
    a.upper_arm_mesh = mesh.robot_upper_arm
    a.forearm_mesh = mesh.robot_fore_arm
    a.hand_mesh = mesh.robot_hand
    a.upper_leg_mesh = mesh.robot_upper_leg
    a.lower_leg_mesh = mesh.robot_lower_leg
    a.toes_mesh = mesh.robot_toes
    robot_sounds = [
        snd.robot1,
        snd.robot2,
        snd.robot3,
        snd.robot4,
    ]
    robot_hit_sounds = [
        snd.robot_hit1,
        snd.robot_hit2,
    ]
    a.jump_sounds = robot_sounds
    a.attack_sounds = robot_sounds
    a.impact_sounds = robot_hit_sounds
    a.death_sounds = [snd.robot_death]
    a.pickup_sounds = robot_sounds
    a.fall_sounds = [snd.robot_fall]
    a.style = 'spaz'
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Bunny ###################################
    a = Appearance('Easter Bunny')
    a.color_texture = tex.bunny_color
    a.color_mask_texture = tex.bunny_color_mask
    a.icon_texture = tex.bunny_icon
    a.icon_mask_texture = tex.bunny_icon_color_mask
    a.head_mesh = mesh.bunny_head
    a.torso_mesh = mesh.bunny_torso
    a.pelvis_mesh = mesh.bunny_pelvis
    a.upper_arm_mesh = mesh.bunny_upper_arm
    a.forearm_mesh = mesh.bunny_fore_arm
    a.hand_mesh = mesh.bunny_hand
    a.upper_leg_mesh = mesh.bunny_upper_leg
    a.lower_leg_mesh = mesh.bunny_lower_leg
    a.toes_mesh = mesh.bunny_toes
    bunny_sounds = [
        snd.bunny1,
        snd.bunny2,
        snd.bunny3,
        snd.bunny4,
    ]
    bunny_hit_sounds = [
        snd.bunny_hit1,
        snd.bunny_hit2,
    ]
    a.jump_sounds = [snd.bunny_jump]
    a.attack_sounds = bunny_sounds
    a.impact_sounds = bunny_hit_sounds
    a.death_sounds = [snd.bunny_death]
    a.pickup_sounds = bunny_sounds
    a.fall_sounds = [snd.bunny_fall]
    a.style = 'bunny'
    a.default_color = (1, 1, 1)
    a.default_highlight = (1, 0.5, 0.5)
