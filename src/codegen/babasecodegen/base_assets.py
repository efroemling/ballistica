# Released under the MIT License. See LICENSE for details.
#
"""The set of classic-flavored assets base draws itself with.

Input spec for the base-asset-set codegen (see
``batools.base_assets``). These are the assets whose *draw code* is
engine-level (bg_dynamics debris, the smoke component, VR hands,
object reflections) but whose *look* belongs to the classic game.
Slot defaults are neutral builtin placeholders -- white texture,
black cube map, box mesh -- so an app-mode that supplies nothing
gets a plain but coherent world; classic supplies the real art from
its own package.
"""

from batools.base_assets import Group, Kind, Slot, BaseAssetSpec

SPEC = BaseAssetSpec(
    groups=[
        Group(
            name='reflections',
            default_module='_builtinassets',
            doc=(
                'Environment cube maps for object reflections. The'
                ' black placeholder makes an unsupplied reflection a'
                ' no-op (reflections are additive).'
            ),
            slots=[
                Slot(
                    name='reflection_char',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Reflection map for characters.',
                    default='textures.black_cube',
                ),
                Slot(
                    name='reflection_powerup',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Reflection map for powerup boxes.',
                    default='textures.black_cube',
                ),
                Slot(
                    name='reflection_soft',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Soft reflection map.',
                    default='textures.black_cube',
                ),
                Slot(
                    name='reflection_sharp',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Sharp reflection map.',
                    default='textures.black_cube',
                ),
                Slot(
                    name='reflection_sharper',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Sharper reflection map.',
                    default='textures.black_cube',
                ),
                Slot(
                    name='reflection_sharpest',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Sharpest reflection map.',
                    default='textures.black_cube',
                ),
            ],
        ),
        Group(
            name='effects',
            default_module='_builtinassets',
            doc=(
                'Art for the engine-side effect systems -- bg_dynamics'
                ' debris and the smoke component.'
            ),
            slots=[
                Slot(
                    name='smoke',
                    kind=Kind.TEXTURE,
                    doc='Smoke puff sheet.',
                    default='textures.white',
                ),
                Slot(
                    name='sparks',
                    kind=Kind.TEXTURE,
                    doc='Spark streak.',
                    default='textures.white',
                ),
                Slot(
                    name='fuse',
                    kind=Kind.TEXTURE,
                    doc='Bomb fuse.',
                    default='textures.white',
                ),
                Slot(
                    name='shrapnel_rock_color',
                    kind=Kind.TEXTURE,
                    doc='Rock shrapnel chunk color map.',
                    default='textures.white',
                ),
                Slot(
                    name='shrapnel_rock',
                    kind=Kind.MESH,
                    doc='Rock shrapnel chunk.',
                    default='meshes.box',
                ),
                Slot(
                    name='shrapnel_board',
                    kind=Kind.MESH,
                    doc='Wooden-board shrapnel chunk.',
                    default='meshes.box',
                ),
                Slot(
                    name='shrapnel_slime',
                    kind=Kind.MESH,
                    doc='Slime glob shrapnel chunk.',
                    default='meshes.box',
                ),
                Slot(
                    name='light',
                    kind=Kind.TEXTURE,
                    doc='Light/shadow blotch (sharp).',
                    default='textures.white',
                ),
                Slot(
                    name='light_soft',
                    kind=Kind.TEXTURE,
                    doc='Light/shadow blotch (soft).',
                    default='textures.white',
                ),
            ],
        ),
        Group(
            name='props',
            default_module='_builtinassets',
            doc=(
                'Classic-look props base draws directly -- flag'
                ' hardware and the VR boxing-glove hands.'
            ),
            slots=[
                Slot(
                    name='flag_pole_color',
                    kind=Kind.TEXTURE,
                    doc='Flag pole color map (bg_dynamics ropes).',
                    default='textures.white',
                ),
                Slot(
                    name='flag_stand',
                    kind=Kind.MESH,
                    doc='Flag base stand.',
                    default='meshes.box',
                ),
                Slot(
                    name='boxing_glove',
                    kind=Kind.MESH,
                    doc='Boxing glove (VR hands).',
                    default='meshes.box',
                ),
                Slot(
                    name='boxing_gloves_color',
                    kind=Kind.TEXTURE,
                    doc='Boxing glove color map.',
                    default='textures.white',
                ),
                Slot(
                    name='character_icon_mask',
                    kind=Kind.TEXTURE,
                    doc='Mask for character icons in kill messages.',
                    default='textures.white',
                ),
            ],
        ),
        Group(
            name='touch_controls',
            default_module='_builtinassets',
            doc=(
                'Art for the on-screen touch controls -- the game-verb'
                ' button glyphs and movement arrows.'
            ),
            slots=[
                Slot(
                    name='action_buttons',
                    kind=Kind.TEXTURE,
                    doc='Bomb/punch/jump/pickup button glyph sheet.',
                    default='textures.white',
                ),
                Slot(
                    name='touch_arrows',
                    kind=Kind.TEXTURE,
                    doc='Movement arrows sheet.',
                    default='textures.white',
                ),
                Slot(
                    name='touch_arrows_actions',
                    kind=Kind.TEXTURE,
                    doc='Movement arrows sheet (action variant).',
                    default='textures.white',
                ),
                Slot(
                    name='arrow',
                    kind=Kind.TEXTURE,
                    doc='Single directional arrow.',
                    default='textures.white',
                ),
                Slot(
                    name='action_button_bottom',
                    kind=Kind.MESH,
                    doc='Bottom action-button backing.',
                    default='meshes.box',
                ),
                Slot(
                    name='action_button_left',
                    kind=Kind.MESH,
                    doc='Left action-button backing.',
                    default='meshes.box',
                ),
                Slot(
                    name='action_button_right',
                    kind=Kind.MESH,
                    doc='Right action-button backing.',
                    default='meshes.box',
                ),
                Slot(
                    name='action_button_top',
                    kind=Kind.MESH,
                    doc='Top action-button backing.',
                    default='meshes.box',
                ),
                Slot(
                    name='arrow_back',
                    kind=Kind.MESH,
                    doc='Back-arrow mesh.',
                    default='meshes.box',
                ),
                Slot(
                    name='arrow_front',
                    kind=Kind.MESH,
                    doc='Front-arrow mesh.',
                    default='meshes.box',
                ),
            ],
        ),
        Group(
            name='jingles',
            default_module='_builtinassets',
            doc=(
                'Input-device connect/disconnect sounds. cork_pop'
                ' defaults silent (its art moved to classicassets);'
                " gun_cocking's wav is babase-python-pinned so it stays"
                ' builtin and defaults to the real thing.'
            ),
            slots=[
                Slot(
                    name='cork_pop',
                    kind=Kind.SOUND,
                    doc='Device-connect jingle.',
                    default='audio.blank',
                ),
                Slot(
                    name='gun_cocking',
                    kind=Kind.SOUND,
                    doc='Device-disconnect jingle.',
                    default='audio.gun_cocking',
                ),
            ],
        ),
    ],
)
