# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.baclassicmapassets.260911`` (bascenev1).

Everything a classic map is made of: terrain, backdrop, bumper, vr-fill and
collision meshes and their textures -- exactly what the map classes in
bascenev1lib/maps.py reference, minus previews, which live in
BaClassicCatalogAssets. Bundled with the game.
"""

# ba_meta require api 9
# ba_meta require asset-package 319

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bacommon.assetpackage import ApverNum

from bascenev1._assetref import AssetGroup

# a-0.baclassicmapassets.260911
_ASSET_PACKAGE = ApverNum(319)

if TYPE_CHECKING:
    from bascenev1._assetref import (
        CollisionMeshHandle,
        MeshHandle,
        TextureHandle,
    )

    class MeshesGroup:
        """
        ::

            Map terrain, backdrop, bumper, vr-fill and collision meshes.

            See source for the full asset list.
        """

        always_land_bg: MeshHandle
        always_land_level: MeshHandle
        always_land_level_bottom: MeshHandle
        always_land_level_collide: CollisionMeshHandle
        always_land_vrfill_mound: MeshHandle
        big_g: MeshHandle
        big_gbottom: MeshHandle
        big_gbumper: CollisionMeshHandle
        big_gcollide: CollisionMeshHandle
        bridgit_level_bottom: MeshHandle
        bridgit_level_collide: CollisionMeshHandle
        bridgit_level_railing_collide: CollisionMeshHandle
        bridgit_level_top: MeshHandle
        courtyard_level: MeshHandle
        courtyard_level_bottom: MeshHandle
        courtyard_level_collide: CollisionMeshHandle
        courtyard_player_wall: CollisionMeshHandle
        crag_castle_level: MeshHandle
        crag_castle_level_bottom: MeshHandle
        crag_castle_level_bumper: CollisionMeshHandle
        crag_castle_level_collide: CollisionMeshHandle
        crag_castle_vrfill_mound: MeshHandle
        doom_shroom_bg: MeshHandle
        doom_shroom_level: MeshHandle
        doom_shroom_level_collide: CollisionMeshHandle
        doom_shroom_stem: MeshHandle
        doom_shroom_stem_collide: CollisionMeshHandle
        doom_shroom_vrfill: MeshHandle
        football_stadium: MeshHandle
        football_stadium_collide: CollisionMeshHandle
        football_stadium_vrfill: MeshHandle
        hockey_stadium_collide: CollisionMeshHandle
        hockey_stadium_inner: MeshHandle
        hockey_stadium_outer: MeshHandle
        hockey_stadium_stands: MeshHandle
        lake_frigid: MeshHandle
        lake_frigid_collide: CollisionMeshHandle
        lake_frigid_reflections: MeshHandle
        lake_frigid_top: MeshHandle
        lake_frigid_vrfill: MeshHandle
        monkey_face_level: MeshHandle
        monkey_face_level_bottom: MeshHandle
        monkey_face_level_bumper: CollisionMeshHandle
        monkey_face_level_collide: CollisionMeshHandle
        nature_background: MeshHandle
        nature_background_collide: CollisionMeshHandle
        nature_background_vrfill: MeshHandle
        rampage_bg: MeshHandle
        rampage_bg2: MeshHandle
        rampage_bumper: CollisionMeshHandle
        rampage_level: MeshHandle
        rampage_level_bottom: MeshHandle
        rampage_level_collide: CollisionMeshHandle
        rampage_vrfill: MeshHandle
        roundabout_level: MeshHandle
        roundabout_level_bottom: MeshHandle
        roundabout_level_bumper: CollisionMeshHandle
        roundabout_level_collide: CollisionMeshHandle
        step_right_up_level: MeshHandle
        step_right_up_level_bottom: MeshHandle
        step_right_up_level_collide: CollisionMeshHandle
        step_right_up_vrfill_mound: MeshHandle
        the_pad_bg: MeshHandle
        the_pad_level: MeshHandle
        the_pad_level_bottom: MeshHandle
        the_pad_level_bumper: CollisionMeshHandle
        the_pad_level_collide: CollisionMeshHandle
        the_pad_vrfill_mound: MeshHandle
        tip_top_bg: MeshHandle
        tip_top_level: MeshHandle
        tip_top_level_bottom: MeshHandle
        tip_top_level_bumper: CollisionMeshHandle
        tip_top_level_collide: CollisionMeshHandle
        tower_dlevel: MeshHandle
        tower_dlevel_bottom: MeshHandle
        tower_dlevel_collide: CollisionMeshHandle
        zig_zag_level: MeshHandle
        zig_zag_level_bottom: MeshHandle
        zig_zag_level_bumper: CollisionMeshHandle
        zig_zag_level_collide: CollisionMeshHandle

    class TexturesGroup:
        """
        ::

            Map terrain, backdrop and reflection textures.

            See source for the full asset list.
        """

        always_land_bgcolor: TextureHandle
        always_land_level_color: TextureHandle
        big_g: TextureHandle
        bridgit_level_color: TextureHandle
        courtyard_level_color: TextureHandle
        crag_castle_level_color: TextureHandle
        doom_shroom_bgcolor: TextureHandle
        doom_shroom_level_color: TextureHandle
        football_stadium: TextureHandle
        hockey_stadium: TextureHandle
        lake_frigid: TextureHandle
        lake_frigid_reflections: TextureHandle
        menu_bg: TextureHandle
        monkey_face_level_color: TextureHandle
        nature_background_color: TextureHandle
        rampage_bgcolor: TextureHandle
        rampage_bgcolor2: TextureHandle
        rampage_level_color: TextureHandle
        roundabout_level_color: TextureHandle
        step_right_up_level_color: TextureHandle
        the_pad_level_color: TextureHandle
        tip_top_bgcolor: TextureHandle
        tip_top_level_color: TextureHandle
        tower_dlevel_color: TextureHandle
        vr_fill_mound: TextureHandle
        zig_zag_level_color: TextureHandle

    #: The ``meshes`` group - 80 assets (``always_land_bg``,
    #: ``always_land_level``, ``always_land_level_bottom``,
    #: ``always_land_level_collide``, ``always_land_vrfill_mound``, and 75
    #: more). Full list in source.
    meshes: MeshesGroup

    #: The ``textures`` group - 26 assets (``always_land_bgcolor``,
    #: ``always_land_level_color``, ``big_g``, ``bridgit_level_color``,
    #: ``courtyard_level_color``, and 21 more). Full list in source.
    textures: TexturesGroup

_TREE = {
    'meshes': {
        'always_land_bg': 'm',
        'always_land_level': 'm',
        'always_land_level_bottom': 'm',
        'always_land_level_collide': 'c',
        'always_land_vrfill_mound': 'm',
        'big_g': 'm',
        'big_gbottom': 'm',
        'big_gbumper': 'c',
        'big_gcollide': 'c',
        'bridgit_level_bottom': 'm',
        'bridgit_level_collide': 'c',
        'bridgit_level_railing_collide': 'c',
        'bridgit_level_top': 'm',
        'courtyard_level': 'm',
        'courtyard_level_bottom': 'm',
        'courtyard_level_collide': 'c',
        'courtyard_player_wall': 'c',
        'crag_castle_level': 'm',
        'crag_castle_level_bottom': 'm',
        'crag_castle_level_bumper': 'c',
        'crag_castle_level_collide': 'c',
        'crag_castle_vrfill_mound': 'm',
        'doom_shroom_bg': 'm',
        'doom_shroom_level': 'm',
        'doom_shroom_level_collide': 'c',
        'doom_shroom_stem': 'm',
        'doom_shroom_stem_collide': 'c',
        'doom_shroom_vrfill': 'm',
        'football_stadium': 'm',
        'football_stadium_collide': 'c',
        'football_stadium_vrfill': 'm',
        'hockey_stadium_collide': 'c',
        'hockey_stadium_inner': 'm',
        'hockey_stadium_outer': 'm',
        'hockey_stadium_stands': 'm',
        'lake_frigid': 'm',
        'lake_frigid_collide': 'c',
        'lake_frigid_reflections': 'm',
        'lake_frigid_top': 'm',
        'lake_frigid_vrfill': 'm',
        'monkey_face_level': 'm',
        'monkey_face_level_bottom': 'm',
        'monkey_face_level_bumper': 'c',
        'monkey_face_level_collide': 'c',
        'nature_background': 'm',
        'nature_background_collide': 'c',
        'nature_background_vrfill': 'm',
        'rampage_bg': 'm',
        'rampage_bg2': 'm',
        'rampage_bumper': 'c',
        'rampage_level': 'm',
        'rampage_level_bottom': 'm',
        'rampage_level_collide': 'c',
        'rampage_vrfill': 'm',
        'roundabout_level': 'm',
        'roundabout_level_bottom': 'm',
        'roundabout_level_bumper': 'c',
        'roundabout_level_collide': 'c',
        'step_right_up_level': 'm',
        'step_right_up_level_bottom': 'm',
        'step_right_up_level_collide': 'c',
        'step_right_up_vrfill_mound': 'm',
        'the_pad_bg': 'm',
        'the_pad_level': 'm',
        'the_pad_level_bottom': 'm',
        'the_pad_level_bumper': 'c',
        'the_pad_level_collide': 'c',
        'the_pad_vrfill_mound': 'm',
        'tip_top_bg': 'm',
        'tip_top_level': 'm',
        'tip_top_level_bottom': 'm',
        'tip_top_level_bumper': 'c',
        'tip_top_level_collide': 'c',
        'tower_dlevel': 'm',
        'tower_dlevel_bottom': 'm',
        'tower_dlevel_collide': 'c',
        'zig_zag_level': 'm',
        'zig_zag_level_bottom': 'm',
        'zig_zag_level_bumper': 'c',
        'zig_zag_level_collide': 'c',
    },
    'textures': {
        'always_land_bgcolor': 't',
        'always_land_level_color': 't',
        'big_g': 't',
        'bridgit_level_color': 't',
        'courtyard_level_color': 't',
        'crag_castle_level_color': 't',
        'doom_shroom_bgcolor': 't',
        'doom_shroom_level_color': 't',
        'football_stadium': 't',
        'hockey_stadium': 't',
        'lake_frigid': 't',
        'lake_frigid_reflections': 't',
        'menu_bg': 't',
        'monkey_face_level_color': 't',
        'nature_background_color': 't',
        'rampage_bgcolor': 't',
        'rampage_bgcolor2': 't',
        'rampage_level_color': 't',
        'roundabout_level_color': 't',
        'step_right_up_level_color': 't',
        'the_pad_level_color': 't',
        'tip_top_bgcolor': 't',
        'tip_top_level_color': 't',
        'tower_dlevel_color': 't',
        'vr_fill_mound': 't',
        'zig_zag_level_color': 't',
    },
}


if not TYPE_CHECKING:
    meshes = AssetGroup(_ASSET_PACKAGE, _TREE['meshes'], 'meshes')
    textures = AssetGroup(_ASSET_PACKAGE, _TREE['textures'], 'textures')
