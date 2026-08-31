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
    ],
)
