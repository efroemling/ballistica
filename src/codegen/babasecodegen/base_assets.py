# Released under the MIT License. See LICENSE for details.
#
"""The set of classic-flavored assets base draws itself with.

Input spec for the base-asset-set codegen (see
``batools.base_assets``). These are the assets whose *draw code* is
engine-level (bg_dynamics debris, the smoke component, VR hands,
object reflections) but whose *look* belongs to the classic game.
Unsupplied slots get neutral engine placeholders chosen by kind (see
``batools.base_assets``), so an app-mode that supplies nothing gets a
plain but coherent world; classic supplies the real art from its own
packages.
"""

from batools.base_assets import Group, Kind, Slot, BaseAssetSpec

SPEC = BaseAssetSpec(
    groups=[
        Group(
            name='reflections',            doc=(
                'Environment cube maps for object reflections. The'
                ' black placeholder makes an unsupplied reflection a'
                ' no-op (reflections are additive).'
            ),
            slots=[
                Slot(
                    name='reflection_char',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Reflection map for characters.',                ),
                Slot(
                    name='reflection_powerup',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Reflection map for powerup boxes.',                ),
                Slot(
                    name='reflection_soft',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Soft reflection map.',                ),
                Slot(
                    name='reflection_sharp',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Sharp reflection map.',                ),
                Slot(
                    name='reflection_sharper',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Sharper reflection map.',                ),
                Slot(
                    name='reflection_sharpest',
                    kind=Kind.CUBE_MAP_TEXTURE,
                    doc='Sharpest reflection map.',                ),
            ],
        ),
        Group(
            name='effects',            doc=(
                'Art for the engine-side effect systems -- bg_dynamics'
                ' debris and the smoke component.'
            ),
            slots=[
                Slot(
                    name='smoke',
                    kind=Kind.TEXTURE,
                    doc='Smoke puff sheet.',                ),
                Slot(
                    name='sparks',
                    kind=Kind.TEXTURE,
                    doc='Spark streak.',                ),
                Slot(
                    name='fuse',
                    kind=Kind.TEXTURE,
                    doc='Bomb fuse.',                ),
                Slot(
                    name='shrapnel_rock_color',
                    kind=Kind.TEXTURE,
                    doc='Rock shrapnel chunk color map.',                ),
                Slot(
                    name='shrapnel_rock',
                    kind=Kind.MESH,
                    doc='Rock shrapnel chunk.',                ),
                Slot(
                    name='shrapnel_board',
                    kind=Kind.MESH,
                    doc='Wooden-board shrapnel chunk.',                ),
                Slot(
                    name='shrapnel_slime',
                    kind=Kind.MESH,
                    doc='Slime glob shrapnel chunk.',                ),
                Slot(
                    name='light',
                    kind=Kind.TEXTURE,
                    doc='Light/shadow blotch (sharp).',                ),
                Slot(
                    name='light_soft',
                    kind=Kind.TEXTURE,
                    doc='Light/shadow blotch (soft).',                ),
            ],
        ),
        Group(
            name='props',            doc=(
                'Classic-look props base draws directly -- flag'
                ' hardware and the VR boxing-glove hands.'
            ),
            slots=[
                Slot(
                    name='flag_pole_color',
                    kind=Kind.TEXTURE,
                    doc='Flag pole color map (bg_dynamics ropes).',                ),
                Slot(
                    name='flag_stand',
                    kind=Kind.MESH,
                    doc='Flag base stand.',                ),
                Slot(
                    name='boxing_glove',
                    kind=Kind.MESH,
                    doc='Boxing glove (VR hands).',                ),
                Slot(
                    name='boxing_gloves_color',
                    kind=Kind.TEXTURE,
                    doc='Boxing glove color map.',                ),
                Slot(
                    name='character_icon_mask',
                    kind=Kind.TEXTURE,
                    doc='Round mask for character icons.',                ),
                Slot(
                    name='standin_icon',
                    kind=Kind.TEXTURE,
                    doc='Standin character icon (while real art loads).',                ),
                Slot(
                    name='standin_icon_color_mask',
                    kind=Kind.TEXTURE,
                    doc='Colorize mask for the standin icon.',                ),
                Slot(
                    name='depiction_spinner',
                    kind=Kind.TEXTURE,
                    doc=(
                        'Faded busy spinner shown while a depiction\'s art'
                        ' loads (spun in place).'
                    ),                ),
            ],
        ),
        Group(
            name='touch_controls',            doc=(
                'Art for the on-screen touch controls -- the game-verb'
                ' button glyphs and movement arrows.'
            ),
            slots=[
                Slot(
                    name='action_buttons',
                    kind=Kind.TEXTURE,
                    doc='Bomb/punch/jump/pickup button glyph sheet.',                ),
                Slot(
                    name='touch_arrows',
                    kind=Kind.TEXTURE,
                    doc='Movement arrows sheet.',                ),
                Slot(
                    name='touch_arrows_actions',
                    kind=Kind.TEXTURE,
                    doc='Movement arrows sheet (action variant).',                ),
                Slot(
                    name='arrow',
                    kind=Kind.TEXTURE,
                    doc='Single directional arrow.',                ),
                Slot(
                    name='action_button_bottom',
                    kind=Kind.MESH,
                    doc='Bottom action-button backing.',                ),
                Slot(
                    name='action_button_left',
                    kind=Kind.MESH,
                    doc='Left action-button backing.',                ),
                Slot(
                    name='action_button_right',
                    kind=Kind.MESH,
                    doc='Right action-button backing.',                ),
                Slot(
                    name='action_button_top',
                    kind=Kind.MESH,
                    doc='Top action-button backing.',                ),
                Slot(
                    name='arrow_back',
                    kind=Kind.MESH,
                    doc='Back-arrow mesh.',                ),
                Slot(
                    name='arrow_front',
                    kind=Kind.MESH,
                    doc='Front-arrow mesh.',                ),
            ],
        ),
        Group(
            name='jingles',            doc=(
                'Connect/disconnect sounds for input devices and party'
                ' members.'
            ),
            slots=[
                Slot(
                    name='cork_pop',
                    kind=Kind.SOUND,
                    doc='Device-disconnect / player-left jingle.',
                ),
                Slot(
                    name='gun_cocking',
                    kind=Kind.SOUND,
                    doc='Device-connect / player-joined jingle.',
                ),
            ],
        ),
    ],
)
