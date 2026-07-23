# Released under the MIT License. See LICENSE for details.
#
"""Standard maps."""

# pylint: disable=too-many-lines

from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1 import classicassets

from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


def register_all_maps() -> None:
    """Registering all maps."""
    for maptype in [
        HockeyStadium,
        FootballStadium,
        Bridgit,
        BigG,
        Roundabout,
        MonkeyFace,
        ZigZag,
        ThePad,
        DoomShroom,
        LakeFrigid,
        TipTop,
        CragCastle,
        TowerD,
        HappyThoughts,
        StepRightUp,
        Courtyard,
        Rampage,
    ]:
        bs.register_map(maptype)


def _tex(name: str) -> str:
    """Qualified classicassets ref for a map texture name."""
    return f'{classicassets.__asset_package__}:textures/{name}'


class HockeyStadium(bs.Map):
    """Stadium map used for ice hockey games."""

    from bascenev1lib.mapdata import hockey_stadium as defs

    name = 'Hockey Stadium'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'hockey', 'team_flag', 'keep_away']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('hockey_stadium_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': (
                classicassets.meshes.hockey_stadium_outer,
                classicassets.meshes.hockey_stadium_inner,
                classicassets.meshes.hockey_stadium_stands,
            ),
            'vr_fill_mesh': classicassets.meshes.football_stadium_vrfill,
            'collision_mesh': classicassets.meshes.hockey_stadium_collide,
            'tex': classicassets.textures.hockey_stadium,
            'stands_tex': classicassets.textures.football_stadium,
        }
        mat = bs.Material()
        mat.add_actions(actions=('modify_part_collision', 'friction', 0.01))
        data['ice_material'] = mat
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['meshes'][0],
                'collision_mesh': self.preloaddata['collision_mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['ice_material'],
                ],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'vr_only': True,
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['stands_tex'],
            },
        )
        mats = [shared.footing_material, self.preloaddata['ice_material']]
        self.floor = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['meshes'][1],
                'color_texture': self.preloaddata['tex'],
                'opacity': 0.92,
                'opacity_in_low_or_medium_quality': 1.0,
                'materials': mats,
            },
        )
        self.stands = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['meshes'][2],
                'visible_in_reflections': False,
                'color_texture': self.preloaddata['stands_tex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.floor_reflection = True
        gnode.debris_friction = 0.3
        gnode.debris_kill_height = -0.3
        gnode.tint = (1.2, 1.3, 1.33)
        gnode.ambient_color = (1.15, 1.25, 1.6)
        gnode.vignette_outer = (0.66, 0.67, 0.73)
        gnode.vignette_inner = (0.93, 0.93, 0.95)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5
        self.is_hockey = True


class FootballStadium(bs.Map):
    """Stadium map for football games."""

    from bascenev1lib.mapdata import football_stadium as defs

    name = 'Football Stadium'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'football', 'team_flag', 'keep_away']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('football_stadium_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.football_stadium,
            'vr_fill_mesh': classicassets.meshes.football_stadium_vrfill,
            'collision_mesh': classicassets.meshes.football_stadium_collide,
            'tex': classicassets.textures.football_stadium,
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh'],
                'collision_mesh': self.preloaddata['collision_mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['tex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.3, 1.2, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5

    @override
    def is_point_near_edge(self, point: bs.Vec3, running: bool = False) -> bool:
        box_position = self.defs.boxes['edge_box'][0:3]
        box_scale = self.defs.boxes['edge_box'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        return xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5


class Bridgit(bs.Map):
    """Map with a narrow bridge in the middle."""

    from bascenev1lib.mapdata import bridgit as defs

    name = 'Bridgit'
    dataname = 'bridgit'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        # print('getting playtypes', cls._getdata()['play_types'])
        return ['melee', 'team_flag', 'keep_away']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('bridgit_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh_top': classicassets.meshes.bridgit_level_top,
            'mesh_bottom': classicassets.meshes.bridgit_level_bottom,
            'mesh_bg': classicassets.meshes.nature_background,
            'bg_vr_fill_mesh': classicassets.meshes.nature_background_vrfill,
            'collision_mesh': classicassets.meshes.bridgit_level_collide,
            'tex': classicassets.textures.bridgit_level_color,
            'mesh_bg_tex': classicassets.textures.nature_background_color,
            'collide_bg': classicassets.meshes.nature_background_collide,
            'railing_collision_mesh': (
                classicassets.meshes.bridgit_level_railing_collide
            ),
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh_top'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['bg_material'],
                    shared.death_material,
                ],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.3)
        gnode.ambient_color = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)


class BigG(bs.Map):
    """Large G shaped map for racing"""

    from bascenev1lib.mapdata import big_g as defs

    name = 'Big G'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return [
            'race',
            'melee',
            'keep_away',
            'team_flag',
            'king_of_the_hill',
            'conquest',
        ]

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('big_gpreview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh_top': classicassets.meshes.big_g,
            'mesh_bottom': classicassets.meshes.big_gbottom,
            'mesh_bg': classicassets.meshes.nature_background,
            'bg_vr_fill_mesh': classicassets.meshes.nature_background_vrfill,
            'collision_mesh': classicassets.meshes.big_gcollide,
            'tex': classicassets.textures.big_g,
            'mesh_bg_tex': classicassets.textures.nature_background_color,
            'collide_bg': classicassets.meshes.nature_background_collide,
            'bumper_collision_mesh': classicassets.meshes.big_gbumper,
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'color': (0.7, 0.7, 0.7),
                'mesh': self.preloaddata['mesh_top'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'color': (0.7, 0.7, 0.7),
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['bumper_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['bg_material'],
                    shared.death_material,
                ],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.3)
        gnode.ambient_color = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)


class Roundabout(bs.Map):
    """CTF map featuring two platforms and a long way around between them"""

    from bascenev1lib.mapdata import roundabout as defs

    name = 'Roundabout'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('roundabout_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.roundabout_level,
            'mesh_bottom': classicassets.meshes.roundabout_level_bottom,
            'mesh_bg': classicassets.meshes.nature_background,
            'bg_vr_fill_mesh': classicassets.meshes.nature_background_vrfill,
            'collision_mesh': classicassets.meshes.roundabout_level_collide,
            'tex': classicassets.textures.roundabout_level_color,
            'mesh_bg_tex': classicassets.textures.nature_background_color,
            'collide_bg': classicassets.meshes.nature_background_collide,
            'railing_collision_mesh': (
                classicassets.meshes.roundabout_level_bumper
            ),
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -1, 1))
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['bg_material'],
                    shared.death_material,
                ],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.0, 1.05, 1.1)
        gnode.ambient_color = (1.0, 1.05, 1.1)
        gnode.shadow_ortho = True
        gnode.vignette_outer = (0.63, 0.65, 0.7)
        gnode.vignette_inner = (0.97, 0.95, 0.93)


class MonkeyFace(bs.Map):
    """Map sorta shaped like a monkey face; teehee!"""

    from bascenev1lib.mapdata import monkey_face as defs

    name = 'Monkey Face'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('monkey_face_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.monkey_face_level,
            'bottom_mesh': classicassets.meshes.monkey_face_level_bottom,
            'mesh_bg': classicassets.meshes.nature_background,
            'bg_vr_fill_mesh': classicassets.meshes.nature_background_vrfill,
            'collision_mesh': classicassets.meshes.monkey_face_level_collide,
            'tex': classicassets.textures.monkey_face_level_color,
            'mesh_bg_tex': classicassets.textures.nature_background_color,
            'collide_bg': classicassets.meshes.nature_background_collide,
            'railing_collision_mesh': (
                classicassets.meshes.monkey_face_level_bumper
            ),
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bottom_mesh'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['bg_material'],
                    shared.death_material,
                ],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.2)
        gnode.ambient_color = (1.2, 1.3, 1.3)
        gnode.vignette_outer = (0.60, 0.62, 0.66)
        gnode.vignette_inner = (0.97, 0.95, 0.93)
        gnode.vr_camera_offset = (-1.4, 0, 0)


class ZigZag(bs.Map):
    """A very long zig-zaggy map"""

    from bascenev1lib.mapdata import zig_zag as defs

    name = 'Zigzag'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return [
            'melee',
            'keep_away',
            'team_flag',
            'conquest',
            'king_of_the_hill',
        ]

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('zigzag_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.zig_zag_level,
            'mesh_bottom': classicassets.meshes.zig_zag_level_bottom,
            'mesh_bg': classicassets.meshes.nature_background,
            'bg_vr_fill_mesh': classicassets.meshes.nature_background_vrfill,
            'collision_mesh': classicassets.meshes.zig_zag_level_collide,
            'tex': classicassets.textures.zig_zag_level_color,
            'mesh_bg_tex': classicassets.textures.nature_background_color,
            'collide_bg': classicassets.meshes.nature_background_collide,
            'railing_collision_mesh': classicassets.meshes.zig_zag_level_bumper,
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['bg_material'],
                    shared.death_material,
                ],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.0, 1.15, 1.15)
        gnode.ambient_color = (1.0, 1.15, 1.15)
        gnode.vignette_outer = (0.57, 0.59, 0.63)
        gnode.vignette_inner = (0.97, 0.95, 0.93)
        gnode.vr_camera_offset = (-1.5, 0, 0)


class ThePad(bs.Map):
    """A simple square shaped map with a raised edge."""

    from bascenev1lib.mapdata import the_pad as defs

    name = 'The Pad'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'king_of_the_hill']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('the_pad_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.the_pad_level,
            'bottom_mesh': classicassets.meshes.the_pad_level_bottom,
            'collision_mesh': classicassets.meshes.the_pad_level_collide,
            'tex': classicassets.textures.the_pad_level_color,
            'bgtex': classicassets.textures.menu_bg,
            'bgmesh': classicassets.meshes.the_pad_bg,
            'railing_collision_mesh': classicassets.meshes.the_pad_level_bumper,
            'vr_fill_mound_mesh': classicassets.meshes.the_pad_vrfill_mound,
            'vr_fill_mound_tex': classicassets.textures.vr_fill_mound,
        }
        # fixme should chop this into vr/non-vr sections for efficiency
        return data

    def __init__(self, main_menu_style: bool = False) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs=(
                {
                    'collision_mesh': self.preloaddata['collision_mesh'],
                    'mesh': self.preloaddata['mesh'],
                    'color_texture': self.preloaddata['tex'],
                    'materials': [shared.footing_material],
                    'reflection': 'soft',
                    'reflection_scale': [0.3],
                }
                if main_menu_style
                else {
                    'collision_mesh': self.preloaddata['collision_mesh'],
                    'mesh': self.preloaddata['mesh'],
                    'color_texture': self.preloaddata['tex'],
                    'materials': [shared.footing_material],
                }
            ),
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs=(
                {
                    'mesh': self.preloaddata['bottom_mesh'],
                    'lighting': False,
                    'color_texture': self.preloaddata['tex'],
                    'reflection': 'soft',
                    'reflection_scale': [0.45],
                }
                if main_menu_style
                else {
                    'mesh': self.preloaddata['bottom_mesh'],
                    'lighting': False,
                    'color_texture': self.preloaddata['tex'],
                }
            ),
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mound_mesh'],
                'lighting': False,
                'vr_only': True,
                'color': (0.56, 0.55, 0.47),
                'background': True,
                'color_texture': self.preloaddata['vr_fill_mound_tex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.1, 1.0)
        gnode.ambient_color = (1.1, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)


class DoomShroom(bs.Map):
    """A giant mushroom. Of doom!"""

    from bascenev1lib.mapdata import doom_shroom as defs

    name = 'Doom Shroom'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('doom_shroom_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.doom_shroom_level,
            'collision_mesh': classicassets.meshes.doom_shroom_level_collide,
            'tex': classicassets.textures.doom_shroom_level_color,
            'bgtex': classicassets.textures.doom_shroom_bgcolor,
            'bgmesh': classicassets.meshes.doom_shroom_bg,
            'vr_fill_mesh': classicassets.meshes.doom_shroom_vrfill,
            'stem_mesh': classicassets.meshes.doom_shroom_stem,
            'collide_bg': classicassets.meshes.doom_shroom_stem_collide,
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        self.stem = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['stem_mesh'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [shared.footing_material, shared.death_material],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.82, 1.10, 1.15)
        gnode.ambient_color = (0.9, 1.3, 1.1)
        gnode.shadow_ortho = False
        gnode.vignette_outer = (0.76, 0.76, 0.76)
        gnode.vignette_inner = (0.95, 0.95, 0.99)

    @override
    def is_point_near_edge(self, point: bs.Vec3, running: bool = False) -> bool:
        xpos = point.x
        zpos = point.z
        x_adj = xpos * 0.125
        z_adj = (zpos + 3.7) * 0.2
        if running:
            x_adj *= 1.4
            z_adj *= 1.4
        return x_adj * x_adj + z_adj * z_adj > 1.0


class LakeFrigid(bs.Map):
    """An icy lake fit for racing."""

    from bascenev1lib.mapdata import lake_frigid as defs

    name = 'Lake Frigid'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'race']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('lake_frigid_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.lake_frigid,
            'mesh_top': classicassets.meshes.lake_frigid_top,
            'mesh_reflections': classicassets.meshes.lake_frigid_reflections,
            'collision_mesh': classicassets.meshes.lake_frigid_collide,
            'tex': classicassets.textures.lake_frigid,
            'tex_reflections': classicassets.textures.lake_frigid_reflections,
            'vr_fill_mesh': classicassets.meshes.lake_frigid_vrfill,
        }
        mat = bs.Material()
        mat.add_actions(actions=('modify_part_collision', 'friction', 0.01))
        data['ice_material'] = mat
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['ice_material'],
                ],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_top'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_reflections'],
                'lighting': False,
                'overlay': True,
                'opacity': 0.15,
                'color_texture': self.preloaddata['tex_reflections'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['tex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1, 1, 1)
        gnode.ambient_color = (1, 1, 1)
        gnode.shadow_ortho = True
        gnode.vignette_outer = (0.86, 0.86, 0.86)
        gnode.vignette_inner = (0.95, 0.95, 0.99)
        gnode.vr_near_clip = 0.5
        self.is_hockey = True


class TipTop(bs.Map):
    """A pointy map good for king-of-the-hill-ish games."""

    from bascenev1lib.mapdata import tip_top as defs

    name = 'Tip Top'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'king_of_the_hill']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('tip_top_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.tip_top_level,
            'bottom_mesh': classicassets.meshes.tip_top_level_bottom,
            'collision_mesh': classicassets.meshes.tip_top_level_collide,
            'tex': classicassets.textures.tip_top_level_color,
            'bgtex': classicassets.textures.tip_top_bgcolor,
            'bgmesh': classicassets.meshes.tip_top_bg,
            'railing_collision_mesh': classicassets.meshes.tip_top_level_bumper,
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -0.2, 2.5))
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'color': (0.7, 0.7, 0.7),
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bottom_mesh'],
                'lighting': False,
                'color': (0.7, 0.7, 0.7),
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'color': (0.4, 0.4, 0.4),
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.8, 0.9, 1.3)
        gnode.ambient_color = (0.8, 0.9, 1.3)
        gnode.vignette_outer = (0.79, 0.79, 0.69)
        gnode.vignette_inner = (0.97, 0.97, 0.99)


class CragCastle(bs.Map):
    """A lovely castle map."""

    from bascenev1lib.mapdata import crag_castle as defs

    name = 'Crag Castle'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'conquest']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('crag_castle_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.crag_castle_level,
            'bottom_mesh': classicassets.meshes.crag_castle_level_bottom,
            'collision_mesh': classicassets.meshes.crag_castle_level_collide,
            'tex': classicassets.textures.crag_castle_level_color,
            'bgtex': classicassets.textures.menu_bg,
            'bgmesh': classicassets.meshes.the_pad_bg,
            'railing_collision_mesh': (
                classicassets.meshes.crag_castle_level_bumper
            ),
            'vr_fill_mound_mesh': classicassets.meshes.crag_castle_vrfill_mound,
            'vr_fill_mound_tex': classicassets.textures.vr_fill_mound,
        }
        # fixme should chop this into vr/non-vr sections
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bottom_mesh'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mound_mesh'],
                'lighting': False,
                'vr_only': True,
                'color': (0.2, 0.25, 0.2),
                'background': True,
                'color_texture': self.preloaddata['vr_fill_mound_tex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.shadow_ortho = True
        gnode.shadow_offset = (0, 0, -5.0)
        gnode.tint = (1.15, 1.05, 0.75)
        gnode.ambient_color = (1.15, 1.05, 0.75)
        gnode.vignette_outer = (0.6, 0.65, 0.6)
        gnode.vignette_inner = (0.95, 0.95, 0.95)
        gnode.vr_near_clip = 1.0


class TowerD(bs.Map):
    """Map used for runaround mini-game."""

    from bascenev1lib.mapdata import tower_d as defs

    name = 'Tower D'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return []

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('tower_dpreview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.tower_dlevel,
            'mesh_bottom': classicassets.meshes.tower_dlevel_bottom,
            'collision_mesh': classicassets.meshes.tower_dlevel_collide,
            'tex': classicassets.textures.tower_dlevel_color,
            'bgtex': classicassets.textures.menu_bg,
            'bgmesh': classicassets.meshes.the_pad_bg,
            'player_wall_collision_mesh': (
                classicassets.meshes
            ).tower_dplayer_wall,
            'player_wall_material': bs.Material(),
        }
        # fixme should chop this into vr/non-vr sections
        data['player_wall_material'].add_actions(
            actions=('modify_part_collision', 'friction', 0.0)
        )
        # anything that needs to hit the wall can apply this material
        data['collide_with_wall_material'] = bs.Material()
        data['player_wall_material'].add_actions(
            conditions=(
                'they_dont_have_material',
                data['collide_with_wall_material'],
            ),
            actions=('modify_part_collision', 'collide', False),
        )
        data['vr_fill_mound_mesh'] = (
            classicassets.meshes.step_right_up_vrfill_mound
        )
        data['vr_fill_mound_tex'] = classicassets.textures.vr_fill_mound
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 1, 1))
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.node_bottom = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mound_mesh'],
                'lighting': False,
                'vr_only': True,
                'color': (0.53, 0.57, 0.5),
                'background': True,
                'color_texture': self.preloaddata['vr_fill_mound_tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        self.player_wall = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata[
                    'player_wall_collision_mesh'
                ],
                'affect_bg_dynamics': False,
                'materials': [self.preloaddata['player_wall_material']],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.15, 1.11, 1.03)
        gnode.ambient_color = (1.2, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.73, 0.7)
        gnode.vignette_inner = (0.95, 0.95, 0.95)

    @override
    def is_point_near_edge(self, point: bs.Vec3, running: bool = False) -> bool:
        # see if we're within edge_box
        boxes = self.defs.boxes
        box_position = boxes['edge_box'][0:3]
        box_scale = boxes['edge_box'][6:9]
        box_position2 = boxes['edge_box2'][0:3]
        box_scale2 = boxes['edge_box2'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        xpos2 = (point.x - box_position2[0]) / box_scale2[0]
        zpos2 = (point.z - box_position2[2]) / box_scale2[2]
        # if we're outside of *both* boxes we're near the edge
        return (xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5) and (
            xpos2 < -0.5 or xpos2 > 0.5 or zpos2 < -0.5 or zpos2 > 0.5
        )


class HappyThoughts(bs.Map):
    """Flying map."""

    from bascenev1lib.mapdata import happy_thoughts as defs

    name = 'Happy Thoughts'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return [
            'melee',
            'keep_away',
            'team_flag',
            'conquest',
            'king_of_the_hill',
        ]

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('always_land_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.always_land_level,
            'bottom_mesh': classicassets.meshes.always_land_level_bottom,
            'bgmesh': classicassets.meshes.always_land_bg,
            'collision_mesh': classicassets.meshes.always_land_level_collide,
            'tex': classicassets.textures.always_land_level_color,
            'bgtex': classicassets.textures.always_land_bgcolor,
            'vr_fill_mound_mesh': classicassets.meshes.always_land_vrfill_mound,
            'vr_fill_mound_tex': classicassets.textures.vr_fill_mound,
        }
        return data

    @override
    @classmethod
    def get_music_type(cls) -> bs.MusicType:
        return bs.MusicType.FLYING

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -3.7, 2.5))
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bottom_mesh'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mound_mesh'],
                'lighting': False,
                'vr_only': True,
                'color': (0.2, 0.25, 0.2),
                'background': True,
                'color_texture': self.preloaddata['vr_fill_mound_tex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.happy_thoughts_mode = True
        gnode.shadow_offset = (0.0, 8.0, 5.0)
        gnode.tint = (1.3, 1.23, 1.0)
        gnode.ambient_color = (1.3, 1.23, 1.0)
        gnode.vignette_outer = (0.64, 0.59, 0.69)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        gnode.vr_near_clip = 1.0
        self.is_flying = True

        # throw out some tips on flying
        txt = bs.newnode(
            'text',
            attrs={
                'text': classicassets.strings.game.press_jump_to_fly,
                'scale': 1.2,
                'maxwidth': 800,
                'position': (0, 200),
                'shadow': 0.5,
                'flatness': 0.5,
                'h_align': 'center',
                'v_attach': 'bottom',
            },
        )
        cmb = bs.newnode(
            'combine',
            owner=txt,
            attrs={'size': 4, 'input0': 0.3, 'input1': 0.9, 'input2': 0.0},
        )
        bs.animate(cmb, 'input3', {3.0: 0, 4.0: 1, 9.0: 1, 10.0: 0})
        cmb.connectattr('output', txt, 'color')
        bs.timer(10.0, txt.delete)


class StepRightUp(bs.Map):
    """Wide stepped map good for CTF or Assault."""

    from bascenev1lib.mapdata import step_right_up as defs

    name = 'Step Right Up'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'conquest']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('step_right_up_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.step_right_up_level,
            'mesh_bottom': classicassets.meshes.step_right_up_level_bottom,
            'collision_mesh': classicassets.meshes.step_right_up_level_collide,
            'tex': classicassets.textures.step_right_up_level_color,
            'bgtex': classicassets.textures.menu_bg,
            'bgmesh': classicassets.meshes.the_pad_bg,
            'vr_fill_mound_mesh': (
                classicassets.meshes
            ).step_right_up_vrfill_mound,
            'vr_fill_mound_tex': classicassets.textures.vr_fill_mound,
        }
        # fixme should chop this into vr/non-vr chunks
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -1, 2))
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.node_bottom = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mound_mesh'],
                'lighting': False,
                'vr_only': True,
                'color': (0.53, 0.57, 0.5),
                'background': True,
                'color_texture': self.preloaddata['vr_fill_mound_tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.1, 1.0)
        gnode.ambient_color = (1.2, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)


class Courtyard(bs.Map):
    """A courtyard-ish looking map for co-op levels."""

    from bascenev1lib.mapdata import courtyard as defs

    name = 'Courtyard'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('courtyard_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.courtyard_level,
            'mesh_bottom': classicassets.meshes.courtyard_level_bottom,
            'collision_mesh': classicassets.meshes.courtyard_level_collide,
            'tex': classicassets.textures.courtyard_level_color,
            'bgtex': classicassets.textures.menu_bg,
            'bgmesh': classicassets.meshes.the_pad_bg,
            'player_wall_collision_mesh': (
                classicassets.meshes.courtyard_player_wall
            ),
            'player_wall_material': bs.Material(),
        }
        # FIXME: Chop this into vr and non-vr chunks.
        data['player_wall_material'].add_actions(
            actions=('modify_part_collision', 'friction', 0.0)
        )
        # anything that needs to hit the wall should apply this.
        data['collide_with_wall_material'] = bs.Material()
        data['player_wall_material'].add_actions(
            conditions=(
                'they_dont_have_material',
                data['collide_with_wall_material'],
            ),
            actions=('modify_part_collision', 'collide', False),
        )
        data['vr_fill_mound_mesh'] = (
            classicassets.meshes.step_right_up_vrfill_mound
        )
        data['vr_fill_mound_tex'] = classicassets.textures.vr_fill_mound
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mound_mesh'],
                'lighting': False,
                'vr_only': True,
                'color': (0.53, 0.57, 0.5),
                'background': True,
                'color_texture': self.preloaddata['vr_fill_mound_tex'],
            },
        )
        # in co-op mode games, put up a wall to prevent players
        # from getting in the turrets (that would foil our brilliant AI)
        if isinstance(bs.getsession(), bs.CoopSession):
            cmesh = self.preloaddata['player_wall_collision_mesh']
            self.player_wall = bs.newnode(
                'terrain',
                attrs={
                    'collision_mesh': cmesh,
                    'affect_bg_dynamics': False,
                    'materials': [self.preloaddata['player_wall_material']],
                },
            )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.17, 1.1)
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.6, 0.6, 0.64)
        gnode.vignette_inner = (0.95, 0.95, 0.93)

    @override
    def is_point_near_edge(self, point: bs.Vec3, running: bool = False) -> bool:
        # count anything off our ground level as safe (for our platforms)
        # see if we're within edge_box
        box_position = self.defs.boxes['edge_box'][0:3]
        box_scale = self.defs.boxes['edge_box'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        return xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5


class Rampage(bs.Map):
    """Wee little map with ramps on the sides."""

    from bascenev1lib.mapdata import rampage as defs

    name = 'Rampage'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return _tex('rampage_preview')

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': classicassets.meshes.rampage_level,
            'bottom_mesh': classicassets.meshes.rampage_level_bottom,
            'collision_mesh': classicassets.meshes.rampage_level_collide,
            'tex': classicassets.textures.rampage_level_color,
            'bgtex': classicassets.textures.rampage_bgcolor,
            'bgtex2': classicassets.textures.rampage_bgcolor2,
            'bgmesh': classicassets.meshes.rampage_bg,
            'bgmesh2': classicassets.meshes.rampage_bg2,
            'vr_fill_mesh': classicassets.meshes.rampage_vrfill,
            'railing_collision_mesh': classicassets.meshes.rampage_bumper,
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 0, 2))
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bottom_mesh'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.bg2 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh2'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex2'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['bgtex2'],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.1, 0.97)
        gnode.ambient_color = (1.3, 1.2, 1.03)
        gnode.vignette_outer = (0.62, 0.64, 0.69)
        gnode.vignette_inner = (0.97, 0.95, 0.93)

    @override
    def is_point_near_edge(self, point: bs.Vec3, running: bool = False) -> bool:
        box_position = self.defs.boxes['edge_box'][0:3]
        box_scale = self.defs.boxes['edge_box'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        return xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5
