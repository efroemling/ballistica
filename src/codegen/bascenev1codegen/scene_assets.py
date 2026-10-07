# Released under the MIT License. See LICENSE for details.
#
"""The set of assets the scene_v1 node layer draws itself with.

This is the input spec for the scene-asset-set codegen (see
``batools.scene_assets``); the sibling of ``bauiv1codegen.ui_assets``.
Slot names are decoupled from the asset names backing them -- each
slot's ``default`` names its fallback art on the group's
``default_module`` wrapper explicitly.
"""

from batools.scene_assets import Group, Kind, Slot, SceneAssetSpec

SPEC = SceneAssetSpec(
    groups=[
        Group(
            name='nodes',
            default_module='_scenev1assets',
            doc=(
                'Art and sounds scene_v1 nodes draw and play themselves'
                ' with -- character features, flag poles, shields,'
                ' locators and effects.'
            ),
            slots=[
                # ---- Textures ----
                Slot(
                    name='circle_no_alpha',
                    kind=Kind.TEXTURE,
                    doc='Opaque filled circle (locator fills).',
                    default='textures.circle_no_alpha',
                ),
                Slot(
                    name='circle_outline',
                    kind=Kind.TEXTURE,
                    doc='Circle outline (locators).',
                    default='textures.circle_outline',
                ),
                Slot(
                    name='circle_outline_no_alpha',
                    kind=Kind.TEXTURE,
                    doc='Opaque circle outline (locators).',
                    default='textures.circle_outline_no_alpha',
                ),
                Slot(
                    name='explosion',
                    kind=Kind.TEXTURE,
                    doc='Explosion flash billboard.',
                    default='textures.explosion',
                ),
                Slot(
                    name='eye_color',
                    kind=Kind.TEXTURE,
                    doc='Character eyeball color map.',
                    default='textures.eye_color',
                ),
                Slot(
                    name='eye_color_tint_mask',
                    kind=Kind.TEXTURE,
                    doc='Tint mask for character eye color.',
                    default='textures.eye_color_tint_mask',
                ),
                Slot(
                    name='rgb_stripes',
                    kind=Kind.TEXTURE,
                    doc='RGB stripe pattern used by character billboards.',
                    default='textures.rgb_stripes',
                ),
                Slot(
                    name='scorch',
                    kind=Kind.TEXTURE,
                    doc='Ground scorch mark.',
                    default='textures.scorch',
                ),
                Slot(
                    name='scorch_big',
                    kind=Kind.TEXTURE,
                    doc='Large ground scorch mark.',
                    default='textures.scorch_big',
                ),
                Slot(
                    name='shield',
                    kind=Kind.TEXTURE,
                    doc='Energy shield surface.',
                    default='textures.shield',
                ),
                Slot(
                    name='wings',
                    kind=Kind.TEXTURE,
                    doc='Character wings color map.',
                    default='textures.wings',
                ),
                # ---- Meshes ----
                Slot(
                    name='cross_out',
                    kind=Kind.MESH,
                    doc='Cross-out marker mesh.',
                    default='meshes.cross_out',
                ),
                Slot(
                    name='eye_ball',
                    kind=Kind.MESH,
                    doc='Character eyeball.',
                    default='meshes.eye_ball',
                ),
                Slot(
                    name='eye_ball_iris',
                    kind=Kind.MESH,
                    doc='Character eyeball iris.',
                    default='meshes.eye_ball_iris',
                ),
                Slot(
                    name='eye_lid',
                    kind=Kind.MESH,
                    doc='Character eye lid.',
                    default='meshes.eye_lid',
                ),
                Slot(
                    name='flag_pole',
                    kind=Kind.MESH,
                    doc='Flag pole.',
                    default='meshes.flag_pole',
                ),
                Slot(
                    name='flash',
                    kind=Kind.MESH,
                    doc='Billboard flash burst.',
                    default='meshes.flash',
                ),
                Slot(
                    name='hair_tuft1',
                    kind=Kind.MESH,
                    doc='Character hair tuft (style 1).',
                    default='meshes.hair_tuft1',
                ),
                Slot(
                    name='hair_tuft1b',
                    kind=Kind.MESH,
                    doc='Character hair tuft (style 1b).',
                    default='meshes.hair_tuft1b',
                ),
                Slot(
                    name='hair_tuft2',
                    kind=Kind.MESH,
                    doc='Character hair tuft (style 2).',
                    default='meshes.hair_tuft2',
                ),
                Slot(
                    name='hair_tuft3',
                    kind=Kind.MESH,
                    doc='Character hair tuft (style 3).',
                    default='meshes.hair_tuft3',
                ),
                Slot(
                    name='hair_tuft4',
                    kind=Kind.MESH,
                    doc='Character hair tuft (style 4).',
                    default='meshes.hair_tuft4',
                ),
                Slot(
                    name='image1x1_full_screen',
                    kind=Kind.MESH,
                    doc='Full-screen square image sheet.',
                    default='meshes.image1x1_full_screen',
                ),
                Slot(
                    name='image1x1_vrfull_screen',
                    kind=Kind.MESH,
                    doc='Full-screen square image sheet (VR variant).',
                    default='meshes.image1x1_vrfull_screen',
                ),
                Slot(
                    name='locator',
                    kind=Kind.MESH,
                    doc='Ground locator marker.',
                    default='meshes.locator',
                ),
                Slot(
                    name='locator_box',
                    kind=Kind.MESH,
                    doc='Box-shaped ground locator.',
                    default='meshes.locator_box',
                ),
                Slot(
                    name='locator_circle',
                    kind=Kind.MESH,
                    doc='Circular ground locator.',
                    default='meshes.locator_circle',
                ),
                Slot(
                    name='locator_circle_outline',
                    kind=Kind.MESH,
                    doc='Circular ground locator outline.',
                    default='meshes.locator_circle_outline',
                ),
                Slot(
                    name='scorch_mesh',
                    kind=Kind.MESH,
                    doc='Ground scorch decal sheet.',
                    default='meshes.scorch',
                ),
                Slot(
                    name='shield_mesh',
                    kind=Kind.MESH,
                    doc='Energy shield dome.',
                    default='meshes.shield',
                ),
                Slot(
                    name='shock_wave',
                    kind=Kind.MESH,
                    doc='Explosion shock-wave ring.',
                    default='meshes.shock_wave',
                ),
                Slot(
                    name='wing',
                    kind=Kind.MESH,
                    doc='Character wing.',
                    default='meshes.wing',
                ),
                # ---- Sounds ----
                Slot(
                    name='sparkle01',
                    kind=Kind.SOUND,
                    doc='Character sparkle effect 1.',
                    default='audio.sparkle01',
                ),
                Slot(
                    name='sparkle02',
                    kind=Kind.SOUND,
                    doc='Character sparkle effect 2.',
                    default='audio.sparkle02',
                ),
                Slot(
                    name='sparkle03',
                    kind=Kind.SOUND,
                    doc='Character sparkle effect 3.',
                    default='audio.sparkle03',
                ),
                Slot(
                    name='ticking_crazy',
                    kind=Kind.SOUND,
                    doc='Frantic bomb-ticking loop.',
                    default='audio.ticking_crazy',
                ),
            ],
        ),
        Group(
            name='builtin',
            default_module='_builtinassets',
            doc=(
                'Utility art from the builtin asset package that the'
                ' node layer leans on directly.'
            ),
            slots=[
                Slot(
                    name='black',
                    kind=Kind.TEXTURE,
                    doc='Solid black (data role); an identity colorize mask.',
                    default='textures.black_data',
                ),
            ],
        ),
        Group(
            name='character_icon',
            default_module='_classiccatalogassets',
            doc=(
                'What the character display node draws character icons'
                ' with: the shared round shape mask every icon is cut'
                ' with, and the standard-spaz standin icon it shows'
                " whenever a definition's own icon art is not local"
                ' (still downloading, unavailable, or not understood).'
            ),
            slots=[
                Slot(
                    name='character_icon_mask',
                    kind=Kind.TEXTURE,
                    doc='Round shape mask applied to every character icon.',
                    default='textures.character_icon_mask',
                ),
                Slot(
                    name='standin_icon',
                    kind=Kind.TEXTURE,
                    doc='Standin (standard spaz) icon.',
                    default='textures.neo_spaz_icon',
                ),
                Slot(
                    name='standin_icon_color_mask',
                    kind=Kind.TEXTURE,
                    doc='Standin icon colorize mask.',
                    default='textures.neo_spaz_icon_color_mask',
                ),
            ],
        ),
        Group(
            name='character_standin',
            default_module='_classiccharacterassets',
            doc=(
                'The standard-spaz look a spaz node wears whenever'
                ' it has a character id but not (yet) that'
                " character's own art -- still downloading,"
                ' unavailable, or not understood by this client.'
            ),
            slots=[
                # ---- Textures ----
                Slot(
                    name='standin_color',
                    kind=Kind.TEXTURE,
                    doc='Standin character color map.',
                    default='textures.neo_spaz_color',
                ),
                Slot(
                    name='standin_color_mask',
                    kind=Kind.TEXTURE,
                    doc='Standin character colorize mask.',
                    default='textures.neo_spaz_color_mask',
                ),
                # ---- Meshes ----
                Slot(
                    name='standin_head',
                    kind=Kind.MESH,
                    doc='Standin character head mesh.',
                    default='meshes.neo_spaz_head',
                ),
                Slot(
                    name='standin_torso',
                    kind=Kind.MESH,
                    doc='Standin character torso mesh.',
                    default='meshes.neo_spaz_torso',
                ),
                Slot(
                    name='standin_pelvis',
                    kind=Kind.MESH,
                    doc='Standin character pelvis mesh.',
                    default='meshes.neo_spaz_pelvis',
                ),
                Slot(
                    name='standin_upper_arm',
                    kind=Kind.MESH,
                    doc='Standin character upper arm mesh.',
                    default='meshes.neo_spaz_upper_arm',
                ),
                Slot(
                    name='standin_forearm',
                    kind=Kind.MESH,
                    doc='Standin character forearm mesh.',
                    default='meshes.neo_spaz_fore_arm',
                ),
                Slot(
                    name='standin_hand',
                    kind=Kind.MESH,
                    doc='Standin character hand mesh.',
                    default='meshes.neo_spaz_hand',
                ),
                Slot(
                    name='standin_upper_leg',
                    kind=Kind.MESH,
                    doc='Standin character upper leg mesh.',
                    default='meshes.neo_spaz_upper_leg',
                ),
                Slot(
                    name='standin_lower_leg',
                    kind=Kind.MESH,
                    doc='Standin character lower leg mesh.',
                    default='meshes.neo_spaz_lower_leg',
                ),
                Slot(
                    name='standin_toes',
                    kind=Kind.MESH,
                    doc='Standin character toes mesh.',
                    default='meshes.neo_spaz_toes',
                ),
                # ---- Sounds ----
                Slot(
                    name='standin_jump01',
                    kind=Kind.SOUND,
                    doc='Standin character jump sound 1.',
                    default='audio.spaz_jump01',
                ),
                Slot(
                    name='standin_jump02',
                    kind=Kind.SOUND,
                    doc='Standin character jump sound 2.',
                    default='audio.spaz_jump02',
                ),
                Slot(
                    name='standin_jump03',
                    kind=Kind.SOUND,
                    doc='Standin character jump sound 3.',
                    default='audio.spaz_jump03',
                ),
                Slot(
                    name='standin_jump04',
                    kind=Kind.SOUND,
                    doc='Standin character jump sound 4.',
                    default='audio.spaz_jump04',
                ),
                Slot(
                    name='standin_attack01',
                    kind=Kind.SOUND,
                    doc='Standin character attack sound 1.',
                    default='audio.spaz_attack01',
                ),
                Slot(
                    name='standin_attack02',
                    kind=Kind.SOUND,
                    doc='Standin character attack sound 2.',
                    default='audio.spaz_attack02',
                ),
                Slot(
                    name='standin_attack03',
                    kind=Kind.SOUND,
                    doc='Standin character attack sound 3.',
                    default='audio.spaz_attack03',
                ),
                Slot(
                    name='standin_attack04',
                    kind=Kind.SOUND,
                    doc='Standin character attack sound 4.',
                    default='audio.spaz_attack04',
                ),
                Slot(
                    name='standin_impact01',
                    kind=Kind.SOUND,
                    doc='Standin character impact sound 1.',
                    default='audio.spaz_impact01',
                ),
                Slot(
                    name='standin_impact02',
                    kind=Kind.SOUND,
                    doc='Standin character impact sound 2.',
                    default='audio.spaz_impact02',
                ),
                Slot(
                    name='standin_impact03',
                    kind=Kind.SOUND,
                    doc='Standin character impact sound 3.',
                    default='audio.spaz_impact03',
                ),
                Slot(
                    name='standin_impact04',
                    kind=Kind.SOUND,
                    doc='Standin character impact sound 4.',
                    default='audio.spaz_impact04',
                ),
                Slot(
                    name='standin_death01',
                    kind=Kind.SOUND,
                    doc='Standin character death sound 1.',
                    default='audio.spaz_death01',
                ),
                Slot(
                    name='standin_pickup01',
                    kind=Kind.SOUND,
                    doc='Standin character pickup sound 1.',
                    default='audio.spaz_pickup01',
                ),
                Slot(
                    name='standin_fall01',
                    kind=Kind.SOUND,
                    doc='Standin character fall sound 1.',
                    default='audio.spaz_fall01',
                ),
            ],
        ),
    ],
)
