# Released under the MIT License. See LICENSE for details.
#
"""Appearance functionality for spazzes."""

from typing import TYPE_CHECKING, overload

from bacommon.assetspec import TextureSpec
from bacommon.assetpackage import ApverNum
import babase
import bascenev1 as bs
from bascenev1 import _classiccharacterassets, _classiccharacterassets2

if TYPE_CHECKING:
    from typing import Literal

    import bauiv1

    from collections.abc import Container, Sequence


def _character_name_table() -> dict[str, babase.LangStr]:
    """Appearance name -> its authored display name.

    First-party appearances with an authored name; mirrors the
    store-side mapping in bamaster ``storeitem.py`` (``OldLady``/
    ``Zola`` are internal keys whose display names are Betty/Lucky).
    Appearances absent here (mods') show their own name untranslated.
    """
    c = _classiccharacterassets.strings.characters
    # (Characters whose sources aren't for copying live in a package
    # of their own.)
    c2 = _classiccharacterassets2.strings.characters
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
        'Taobao Mascot': c2.taobao_mascot,
        'OldLady': c.betty,
        'Zola': c.lucky,
        'Spaz': c.spaz,
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
        if 'characters.taobaomascot' not in purchases:
            disallowed.append('Taobao Mascot')
        if 'characters.agent' not in purchases:
            disallowed.append('Agent Johnson')
        if 'characters.assassin' not in purchases:
            disallowed.append('Zola')
        if 'characters.wizard' not in purchases:
            disallowed.append('Grumbledorf')
        if 'characters.oldlady' not in purchases:
            disallowed.append('OldLady')
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
#: asset-package wrapper (``_classiccharacterassets.textures.zoe_icon``);
#: the bare ``str`` form is the legacy asset name, kept so existing mods keep
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
    apvernum, sep, name = qualified.partition(':')
    if not sep or not name or not apvernum.isdigit():
        return _classiccharacterassets.textures.neo_spaz_icon
    return TextureSpec(ApverNum(int(apvernum)), name)


class Appearance:
    """Create and fill out one of these suckers to define a spaz appearance.

    An appearance's in-game look is given one of two ways:

    - **A character**: set :attr:`character` to a character from an
      asset-package wrapper (``mypackage.characters.zoe``), which is a
      whole look in one piece: its body art, voice, proportions and
      face. The individual mesh, texture, sound and ``style`` fields
      are then not used.
    - **Piece by piece** (the older way, which keeps working): leave
      :attr:`character` unset and fill in every mesh, body texture and
      sound list, plus a ``style`` preset.

    Either way, the icon textures and default colors are set here.
    """

    def __init__(self, name: str):
        assert bs.app.classic is not None
        self.name = name
        if self.name in bs.app.classic.spaz_appearances:
            raise RuntimeError(
                f'spaz appearance name "{self.name}" already exists.'
            )
        bs.app.classic.spaz_appearances[self.name] = self

        #: The whole in-game look as one character (see the class
        #: docs); None to give it piece by piece below.
        self.character: bs.CharacterHandle | None = None

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

    # Every builtin is a character: its whole in-game look is a .bchar
    # in the character package (characters/spaz.bchar ...), leaving
    # only its icon and default colors to say here.
    uitex = _classiccharacterassets.textures
    chars = _classiccharacterassets.characters
    # Spaz #######################################
    a = Appearance('Spaz')
    a.character = chars.spaz
    a.icon_texture = uitex.neo_spaz_icon
    a.icon_mask_texture = uitex.neo_spaz_icon_color_mask

    # Zoe #####################################
    a = Appearance('Zoe')
    a.character = chars.zoe
    a.icon_texture = uitex.zoe_icon
    a.icon_mask_texture = uitex.zoe_icon_color_mask
    a.default_color = (0.6, 0.6, 0.6)
    a.default_highlight = (0, 1, 0)

    # Ninja ##########################################
    a = Appearance('Snake Shadow')
    a.character = chars.snake_shadow
    a.icon_texture = uitex.ninja_icon
    a.icon_mask_texture = uitex.ninja_icon_color_mask
    a.default_color = (1, 1, 1)
    a.default_highlight = (0.55, 0.8, 0.55)

    # Barbarian #####################################
    a = Appearance('Kronk')
    a.character = chars.kronk
    a.icon_texture = uitex.kronk_icon
    a.icon_mask_texture = uitex.kronk_icon_color_mask
    a.default_color = (0.4, 0.5, 0.4)
    a.default_highlight = (1, 0.5, 0.3)

    # Chef ###########################################
    a = Appearance('Mel')
    a.character = chars.mel
    a.icon_texture = uitex.mel_icon
    a.icon_mask_texture = uitex.mel_icon_color_mask
    a.default_color = (1, 1, 1)
    a.default_highlight = (0.1, 0.6, 0.1)

    # Pirate #######################################
    a = Appearance('Jack Morgan')
    a.character = chars.jack_morgan
    a.icon_texture = uitex.jack_icon
    a.icon_mask_texture = uitex.jack_icon_color_mask
    a.default_color = (1, 0.2, 0.1)
    a.default_highlight = (1, 1, 0)

    # Santa ######################################
    a = Appearance('Santa Claus')
    a.character = chars.santa_claus
    a.icon_texture = uitex.santa_icon
    a.icon_mask_texture = uitex.santa_icon_color_mask
    a.default_color = (1, 0, 0)
    a.default_highlight = (1, 1, 1)

    # Snowman ###################################
    a = Appearance('Frosty')
    a.character = chars.frosty
    a.icon_texture = uitex.frosty_icon
    a.icon_mask_texture = uitex.frosty_icon_color_mask
    a.default_color = (0.5, 0.5, 1)
    a.default_highlight = (1, 0.5, 0)

    # Skeleton ################################
    a = Appearance('Bones')
    a.character = chars.bones
    a.icon_texture = uitex.bones_icon
    a.icon_mask_texture = uitex.bones_icon_color_mask
    a.default_color = (0.6, 0.9, 1)
    a.default_highlight = (0.6, 0.9, 1)

    # Bear ###################################
    a = Appearance('Bernard')
    a.character = chars.bernard
    a.icon_texture = uitex.bear_icon
    a.icon_mask_texture = uitex.bear_icon_color_mask
    a.default_color = (0.7, 0.5, 0.0)

    # Penguin ###################################
    a = Appearance('Pascal')
    a.character = chars.pascal
    a.icon_texture = uitex.penguin_icon
    a.icon_mask_texture = uitex.penguin_icon_color_mask
    a.default_color = (0.3, 0.5, 0.8)
    a.default_highlight = (1, 0, 0)

    # Ali ###################################
    # (In the second character package: the first one's sources are
    # offered for anyone to copy, and this character's aren't.)
    a = Appearance('Taobao Mascot')
    a.character = _classiccharacterassets2.characters.taobao_mascot
    a.icon_texture = _classiccharacterassets2.textures.ali_icon
    a.icon_mask_texture = _classiccharacterassets2.textures.ali_icon_color_mask
    a.default_color = (1, 0.5, 0)
    a.default_highlight = (1, 1, 1)

    # Cyborg ###################################
    a = Appearance('B-9000')
    a.character = chars.b9000
    a.icon_texture = uitex.cyborg_icon
    a.icon_mask_texture = uitex.cyborg_icon_color_mask
    a.default_color = (0.5, 0.5, 0.5)
    a.default_highlight = (1, 0, 0)

    # Agent ###################################
    a = Appearance('Agent Johnson')
    a.character = chars.agent_johnson
    a.icon_texture = uitex.agent_icon
    a.icon_mask_texture = uitex.agent_icon_color_mask
    a.default_color = (0.3, 0.3, 0.33)
    a.default_highlight = (1, 0.5, 0.3)

    # Lucky the Leprechaun ############################
    #
    # Note: repurposing assassin slot. Lucky is not actually an
    # assassin. He is a good and friendly Leprechaun.
    a = Appearance('Zola')
    a.character = chars.lucky
    a.icon_texture = uitex.assassin_icon
    a.icon_mask_texture = uitex.assassin_icon_color_mask
    a.default_color = (0.2, 1.0, 0.5)
    a.default_highlight = (1.0, 0.3, 0)

    # Wizard ###################################
    a = Appearance('Grumbledorf')
    a.character = chars.grumbledorf
    a.icon_texture = uitex.wizard_icon
    a.icon_mask_texture = uitex.wizard_icon_color_mask
    a.default_color = (0.2, 0.4, 1.0)
    a.default_highlight = (0.06, 0.15, 0.4)

    # OldLady ###################################
    a = Appearance('OldLady')
    a.character = chars.betty
    a.icon_texture = uitex.old_lady_icon
    a.icon_mask_texture = uitex.old_lady_icon_color_mask
    a.default_color = (0.2, 1.0, 1.0)
    a.default_highlight = (0.5, 0.25, 1.0)

    # Pixie ###################################
    a = Appearance('Pixel')
    a.character = chars.pixel
    a.icon_texture = uitex.pixie_icon
    a.icon_mask_texture = uitex.pixie_icon_color_mask
    a.default_color = (0, 1, 0.7)
    a.default_highlight = (0.65, 0.35, 0.75)

    # Bunny ###################################
    a = Appearance('Easter Bunny')
    a.character = chars.easter_bunny
    a.icon_texture = uitex.bunny_icon
    a.icon_mask_texture = uitex.bunny_icon_color_mask
    a.default_color = (1, 1, 1)
    a.default_highlight = (1, 0.5, 0.5)
