# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.bascenev1assets.260831`` (bascenev1).

Art and sounds the scene_v1 node layer draws itself with -- character
eyes/hair/wings, flag poles, shields, locators, scorch and shock-wave effects.
Supplied to scene_v1 by the active app-mode (see bascenev1.SceneV1AssetSet), so
an app-mode can reskin them by supplying its own set instead. scene_v1 is the
BombSquad scene system, so game-specific concepts are at home here.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.bascenev1assets.260831

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bascenev1._assetref import AssetGroup

_ASSET_PACKAGE = 'a-0.bascenev1assets.260831'

if TYPE_CHECKING:
    from bascenev1._assetref import MeshHandle, SoundHandle, TextureHandle

    class AudioGroup:
        """
        ::

            Sounds scene_v1 nodes play themselves (spaz sparkles, bomb ticking).

            See source for the full asset list.
        """

        sparkle01: SoundHandle
        sparkle02: SoundHandle
        sparkle03: SoundHandle
        ticking_crazy: SoundHandle

    class MeshesGroup:
        """
        ::

            Meshes scene_v1 nodes draw themselves with.

            See source for the full asset list.
        """

        cross_out: MeshHandle
        eye_ball: MeshHandle
        eye_ball_iris: MeshHandle
        eye_lid: MeshHandle
        flag_pole: MeshHandle
        flash: MeshHandle
        hair_tuft1: MeshHandle
        hair_tuft1b: MeshHandle
        hair_tuft2: MeshHandle
        hair_tuft3: MeshHandle
        hair_tuft4: MeshHandle
        image1x1_full_screen: MeshHandle
        image1x1_vrfull_screen: MeshHandle
        locator: MeshHandle
        locator_box: MeshHandle
        locator_circle: MeshHandle
        locator_circle_outline: MeshHandle
        scorch: MeshHandle
        shield: MeshHandle
        shock_wave: MeshHandle
        wing: MeshHandle

    class TexturesGroup:
        """
        ::

            Textures scene_v1 nodes draw themselves with.

            See source for the full asset list.
        """

        circle_no_alpha: TextureHandle
        circle_outline: TextureHandle
        circle_outline_no_alpha: TextureHandle
        explosion: TextureHandle
        eye_color: TextureHandle
        eye_color_tint_mask: TextureHandle
        rgb_stripes: TextureHandle
        scorch: TextureHandle
        scorch_big: TextureHandle
        shield: TextureHandle
        wings: TextureHandle

    #: The ``audio`` group - 4 assets (``sparkle01``, ``sparkle02``,
    #: ``sparkle03``, ``ticking_crazy``). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 21 assets (``cross_out``, ``eye_ball``,
    #: ``eye_ball_iris``, ``eye_lid``, ``flag_pole``, and 16 more). Full list in
    #: source.
    meshes: MeshesGroup

    #: The ``textures`` group - 11 assets (``circle_no_alpha``,
    #: ``circle_outline``, ``circle_outline_no_alpha``, ``explosion``,
    #: ``eye_color``, and 6 more). Full list in source.
    textures: TexturesGroup

_TREE = {
    'audio': {
        'sparkle01': 's',
        'sparkle02': 's',
        'sparkle03': 's',
        'ticking_crazy': 's',
    },
    'meshes': {
        'cross_out': 'm',
        'eye_ball': 'm',
        'eye_ball_iris': 'm',
        'eye_lid': 'm',
        'flag_pole': 'm',
        'flash': 'm',
        'hair_tuft1': 'm',
        'hair_tuft1b': 'm',
        'hair_tuft2': 'm',
        'hair_tuft3': 'm',
        'hair_tuft4': 'm',
        'image1x1_full_screen': 'm',
        'image1x1_vrfull_screen': 'm',
        'locator': 'm',
        'locator_box': 'm',
        'locator_circle': 'm',
        'locator_circle_outline': 'm',
        'scorch': 'm',
        'shield': 'm',
        'shock_wave': 'm',
        'wing': 'm',
    },
    'textures': {
        'circle_no_alpha': 't',
        'circle_outline': 't',
        'circle_outline_no_alpha': 't',
        'explosion': 't',
        'eye_color': 't',
        'eye_color_tint_mask': 't',
        'rgb_stripes': 't',
        'scorch': 't',
        'scorch_big': 't',
        'shield': 't',
        'wings': 't',
    },
}


if not TYPE_CHECKING:
    audio = AssetGroup(_ASSET_PACKAGE, _TREE['audio'], 'audio')
    meshes = AssetGroup(_ASSET_PACKAGE, _TREE['meshes'], 'meshes')
    textures = AssetGroup(_ASSET_PACKAGE, _TREE['textures'], 'textures')
