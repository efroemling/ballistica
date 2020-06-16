# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Standard maps."""
# pylint: disable=too-many-lines

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, List, Dict


class HockeyStadium(ba.Map):
    """Stadium map used for ice hockey games."""

    from bastd.mapdata import hockey_stadium as defs
    name = 'Hockey Stadium'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'hockey', 'team_flag', 'keep_away']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'hockeyStadiumPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'models': (ba.getmodel('hockeyStadiumOuter'),
                       ba.getmodel('hockeyStadiumInner'),
                       ba.getmodel('hockeyStadiumStands')),
            'vr_fill_model': ba.getmodel('footballStadiumVRFill'),
            'collide_model': ba.getcollidemodel('hockeyStadiumCollide'),
            'tex': ba.gettexture('hockeyStadium'),
            'stands_tex': ba.gettexture('footballStadium')
        }
        mat = ba.Material()
        mat.add_actions(actions=('modify_part_collision', 'friction', 0.01))
        data['ice_material'] = mat
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode('terrain',
                               delegate=self,
                               attrs={
                                   'model':
                                       self.preloaddata['models'][0],
                                   'collide_model':
                                       self.preloaddata['collide_model'],
                                   'color_texture':
                                       self.preloaddata['tex'],
                                   'materials': [
                                       shared.footing_material,
                                       self.preloaddata['ice_material']
                                   ]
                               })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_model'],
                       'vr_only': True,
                       'lighting': False,
                       'background': True,
                       'color_texture': self.preloaddata['stands_tex']
                   })
        mats = [shared.footing_material, self.preloaddata['ice_material']]
        self.floor = ba.newnode('terrain',
                                attrs={
                                    'model': self.preloaddata['models'][1],
                                    'color_texture': self.preloaddata['tex'],
                                    'opacity': 0.92,
                                    'opacity_in_low_or_medium_quality': 1.0,
                                    'materials': mats
                                })
        self.stands = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['models'][2],
                'visible_in_reflections': False,
                'color_texture': self.preloaddata['stands_tex']
            })
        gnode = ba.getactivity().globalsnode
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


class FootballStadium(ba.Map):
    """Stadium map for football games."""
    from bastd.mapdata import football_stadium as defs

    name = 'Football Stadium'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'football', 'team_flag', 'keep_away']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'footballStadiumPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('footballStadium'),
            'vr_fill_model': ba.getmodel('footballStadiumVRFill'),
            'collide_model': ba.getcollidemodel('footballStadiumCollide'),
            'tex': ba.gettexture('footballStadium')
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'model': self.preloaddata['model'],
                'collide_model': self.preloaddata['collide_model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['tex']
                   })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.3, 1.2, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5

    def is_point_near_edge(self,
                           point: ba.Vec3,
                           running: bool = False) -> bool:
        box_position = self.defs.boxes['edge_box'][0:3]
        box_scale = self.defs.boxes['edge_box'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        return xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5


class Bridgit(ba.Map):
    """Map with a narrow bridge in the middle."""
    from bastd.mapdata import bridgit as defs

    name = 'Bridgit'
    dataname = 'bridgit'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        # print('getting playtypes', cls._getdata()['play_types'])
        return ['melee', 'team_flag', 'keep_away']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bridgitPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model_top': ba.getmodel('bridgitLevelTop'),
            'model_bottom': ba.getmodel('bridgitLevelBottom'),
            'model_bg': ba.getmodel('natureBackground'),
            'bg_vr_fill_model': ba.getmodel('natureBackgroundVRFill'),
            'collide_model': ba.getcollidemodel('bridgitLevelCollide'),
            'tex': ba.gettexture('bridgitLevelColor'),
            'model_bg_tex': ba.gettexture('natureBackgroundColor'),
            'collide_bg': ba.getcollidemodel('natureBackgroundCollide'),
            'railing_collide_model':
                (ba.getcollidemodel('bridgitLevelRailingCollide')),
            'bg_material': ba.Material()
        }
        data['bg_material'].add_actions(actions=('modify_part_collision',
                                                 'friction', 10.0))
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model_top'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['model_bottom'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['model_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['model_bg_tex']
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['bg_vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['model_bg_tex']
                   })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['railing_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        self.bg_collide = ba.newnode('terrain',
                                     attrs={
                                         'collide_model':
                                             self.preloaddata['collide_bg'],
                                         'materials': [
                                             shared.footing_material,
                                             self.preloaddata['bg_material'],
                                             shared.death_material
                                         ]
                                     })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.3)
        gnode.ambient_color = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)


class BigG(ba.Map):
    """Large G shaped map for racing"""

    from bastd.mapdata import big_g as defs

    name = 'Big G'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return [
            'race', 'melee', 'keep_away', 'team_flag', 'king_of_the_hill',
            'conquest'
        ]

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bigGPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model_top': ba.getmodel('bigG'),
            'model_bottom': ba.getmodel('bigGBottom'),
            'model_bg': ba.getmodel('natureBackground'),
            'bg_vr_fill_model': ba.getmodel('natureBackgroundVRFill'),
            'collide_model': ba.getcollidemodel('bigGCollide'),
            'tex': ba.gettexture('bigG'),
            'model_bg_tex': ba.gettexture('natureBackgroundColor'),
            'collide_bg': ba.getcollidemodel('natureBackgroundCollide'),
            'bumper_collide_model': ba.getcollidemodel('bigGBumper'),
            'bg_material': ba.Material()
        }
        data['bg_material'].add_actions(actions=('modify_part_collision',
                                                 'friction', 10.0))
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'color': (0.7, 0.7, 0.7),
                'model': self.preloaddata['model_top'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['model_bottom'],
                                     'color': (0.7, 0.7, 0.7),
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['model_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['model_bg_tex']
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['bg_vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['model_bg_tex']
                   })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['bumper_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        self.bg_collide = ba.newnode('terrain',
                                     attrs={
                                         'collide_model':
                                             self.preloaddata['collide_bg'],
                                         'materials': [
                                             shared.footing_material,
                                             self.preloaddata['bg_material'],
                                             shared.death_material
                                         ]
                                     })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.3)
        gnode.ambient_color = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)


class Roundabout(ba.Map):
    """CTF map featuring two platforms and a long way around between them"""

    from bastd.mapdata import roundabout as defs

    name = 'Roundabout'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'roundaboutPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('roundaboutLevel'),
            'model_bottom': ba.getmodel('roundaboutLevelBottom'),
            'model_bg': ba.getmodel('natureBackground'),
            'bg_vr_fill_model': ba.getmodel('natureBackgroundVRFill'),
            'collide_model': ba.getcollidemodel('roundaboutLevelCollide'),
            'tex': ba.gettexture('roundaboutLevelColor'),
            'model_bg_tex': ba.gettexture('natureBackgroundColor'),
            'collide_bg': ba.getcollidemodel('natureBackgroundCollide'),
            'railing_collide_model':
                (ba.getcollidemodel('roundaboutLevelBumper')),
            'bg_material': ba.Material()
        }
        data['bg_material'].add_actions(actions=('modify_part_collision',
                                                 'friction', 10.0))
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -1, 1))
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['model_bottom'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['model_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['model_bg_tex']
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['bg_vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['model_bg_tex']
                   })
        self.bg_collide = ba.newnode('terrain',
                                     attrs={
                                         'collide_model':
                                             self.preloaddata['collide_bg'],
                                         'materials': [
                                             shared.footing_material,
                                             self.preloaddata['bg_material'],
                                             shared.death_material
                                         ]
                                     })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['railing_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.0, 1.05, 1.1)
        gnode.ambient_color = (1.0, 1.05, 1.1)
        gnode.shadow_ortho = True
        gnode.vignette_outer = (0.63, 0.65, 0.7)
        gnode.vignette_inner = (0.97, 0.95, 0.93)


class MonkeyFace(ba.Map):
    """Map sorta shaped like a monkey face; teehee!"""

    from bastd.mapdata import monkey_face as defs

    name = 'Monkey Face'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'monkeyFacePreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('monkeyFaceLevel'),
            'bottom_model': ba.getmodel('monkeyFaceLevelBottom'),
            'model_bg': ba.getmodel('natureBackground'),
            'bg_vr_fill_model': ba.getmodel('natureBackgroundVRFill'),
            'collide_model': ba.getcollidemodel('monkeyFaceLevelCollide'),
            'tex': ba.gettexture('monkeyFaceLevelColor'),
            'model_bg_tex': ba.gettexture('natureBackgroundColor'),
            'collide_bg': ba.getcollidemodel('natureBackgroundCollide'),
            'railing_collide_model':
                (ba.getcollidemodel('monkeyFaceLevelBumper')),
            'bg_material': ba.Material()
        }
        data['bg_material'].add_actions(actions=('modify_part_collision',
                                                 'friction', 10.0))
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['bottom_model'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['model_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['model_bg_tex']
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['bg_vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['model_bg_tex']
                   })
        self.bg_collide = ba.newnode('terrain',
                                     attrs={
                                         'collide_model':
                                             self.preloaddata['collide_bg'],
                                         'materials': [
                                             shared.footing_material,
                                             self.preloaddata['bg_material'],
                                             shared.death_material
                                         ]
                                     })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['railing_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.2)
        gnode.ambient_color = (1.2, 1.3, 1.3)
        gnode.vignette_outer = (0.60, 0.62, 0.66)
        gnode.vignette_inner = (0.97, 0.95, 0.93)
        gnode.vr_camera_offset = (-1.4, 0, 0)


class ZigZag(ba.Map):
    """A very long zig-zaggy map"""

    from bastd.mapdata import zig_zag as defs

    name = 'Zigzag'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return [
            'melee', 'keep_away', 'team_flag', 'conquest', 'king_of_the_hill'
        ]

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'zigzagPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('zigZagLevel'),
            'model_bottom': ba.getmodel('zigZagLevelBottom'),
            'model_bg': ba.getmodel('natureBackground'),
            'bg_vr_fill_model': ba.getmodel('natureBackgroundVRFill'),
            'collide_model': ba.getcollidemodel('zigZagLevelCollide'),
            'tex': ba.gettexture('zigZagLevelColor'),
            'model_bg_tex': ba.gettexture('natureBackgroundColor'),
            'collide_bg': ba.getcollidemodel('natureBackgroundCollide'),
            'railing_collide_model': ba.getcollidemodel('zigZagLevelBumper'),
            'bg_material': ba.Material()
        }
        data['bg_material'].add_actions(actions=('modify_part_collision',
                                                 'friction', 10.0))
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['model_bg'],
                'lighting': False,
                'color_texture': self.preloaddata['model_bg_tex']
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['model_bottom'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['bg_vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['model_bg_tex']
                   })
        self.bg_collide = ba.newnode('terrain',
                                     attrs={
                                         'collide_model':
                                             self.preloaddata['collide_bg'],
                                         'materials': [
                                             shared.footing_material,
                                             self.preloaddata['bg_material'],
                                             shared.death_material
                                         ]
                                     })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['railing_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.0, 1.15, 1.15)
        gnode.ambient_color = (1.0, 1.15, 1.15)
        gnode.vignette_outer = (0.57, 0.59, 0.63)
        gnode.vignette_inner = (0.97, 0.95, 0.93)
        gnode.vr_camera_offset = (-1.5, 0, 0)


class ThePad(ba.Map):
    """A simple square shaped map with a raised edge."""

    from bastd.mapdata import the_pad as defs

    name = 'The Pad'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'king_of_the_hill']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'thePadPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('thePadLevel'),
            'bottom_model': ba.getmodel('thePadLevelBottom'),
            'collide_model': ba.getcollidemodel('thePadLevelCollide'),
            'tex': ba.gettexture('thePadLevelColor'),
            'bgtex': ba.gettexture('menuBG'),
            'bgmodel': ba.getmodel('thePadBG'),
            'railing_collide_model': ba.getcollidemodel('thePadLevelBumper'),
            'vr_fill_mound_model': ba.getmodel('thePadVRFillMound'),
            'vr_fill_mound_tex': ba.gettexture('vrFillMound')
        }
        # fixme should chop this into vr/non-vr sections for efficiency
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['bottom_model'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['railing_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_mound_model'],
                       'lighting': False,
                       'vr_only': True,
                       'color': (0.56, 0.55, 0.47),
                       'background': True,
                       'color_texture': self.preloaddata['vr_fill_mound_tex']
                   })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.1, 1.0)
        gnode.ambient_color = (1.1, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)


class DoomShroom(ba.Map):
    """A giant mushroom. Of doom!"""

    from bastd.mapdata import doom_shroom as defs

    name = 'Doom Shroom'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'doomShroomPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('doomShroomLevel'),
            'collide_model': ba.getcollidemodel('doomShroomLevelCollide'),
            'tex': ba.gettexture('doomShroomLevelColor'),
            'bgtex': ba.gettexture('doomShroomBGColor'),
            'bgmodel': ba.getmodel('doomShroomBG'),
            'vr_fill_model': ba.getmodel('doomShroomVRFill'),
            'stem_model': ba.getmodel('doomShroomStem'),
            'collide_bg': ba.getcollidemodel('doomShroomStemCollide')
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['bgtex']
                   })
        self.stem = ba.newnode('terrain',
                               attrs={
                                   'model': self.preloaddata['stem_model'],
                                   'lighting': False,
                                   'color_texture': self.preloaddata['tex']
                               })
        self.bg_collide = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['collide_bg'],
                'materials': [shared.footing_material, shared.death_material]
            })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (0.82, 1.10, 1.15)
        gnode.ambient_color = (0.9, 1.3, 1.1)
        gnode.shadow_ortho = False
        gnode.vignette_outer = (0.76, 0.76, 0.76)
        gnode.vignette_inner = (0.95, 0.95, 0.99)

    def is_point_near_edge(self,
                           point: ba.Vec3,
                           running: bool = False) -> bool:
        xpos = point.x
        zpos = point.z
        x_adj = xpos * 0.125
        z_adj = (zpos + 3.7) * 0.2
        if running:
            x_adj *= 1.4
            z_adj *= 1.4
        return x_adj * x_adj + z_adj * z_adj > 1.0


class LakeFrigid(ba.Map):
    """An icy lake fit for racing."""

    from bastd.mapdata import lake_frigid as defs

    name = 'Lake Frigid'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'race']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'lakeFrigidPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('lakeFrigid'),
            'model_top': ba.getmodel('lakeFrigidTop'),
            'model_reflections': ba.getmodel('lakeFrigidReflections'),
            'collide_model': ba.getcollidemodel('lakeFrigidCollide'),
            'tex': ba.gettexture('lakeFrigid'),
            'tex_reflections': ba.gettexture('lakeFrigidReflections'),
            'vr_fill_model': ba.getmodel('lakeFrigidVRFill')
        }
        mat = ba.Material()
        mat.add_actions(actions=('modify_part_collision', 'friction', 0.01))
        data['ice_material'] = mat
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode('terrain',
                               delegate=self,
                               attrs={
                                   'collide_model':
                                       self.preloaddata['collide_model'],
                                   'model':
                                       self.preloaddata['model'],
                                   'color_texture':
                                       self.preloaddata['tex'],
                                   'materials': [
                                       shared.footing_material,
                                       self.preloaddata['ice_material']
                                   ]
                               })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['model_top'],
                       'lighting': False,
                       'color_texture': self.preloaddata['tex']
                   })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['model_reflections'],
                       'lighting': False,
                       'overlay': True,
                       'opacity': 0.15,
                       'color_texture': self.preloaddata['tex_reflections']
                   })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['tex']
                   })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1, 1, 1)
        gnode.ambient_color = (1, 1, 1)
        gnode.shadow_ortho = True
        gnode.vignette_outer = (0.86, 0.86, 0.86)
        gnode.vignette_inner = (0.95, 0.95, 0.99)
        gnode.vr_near_clip = 0.5
        self.is_hockey = True


class TipTop(ba.Map):
    """A pointy map good for king-of-the-hill-ish games."""

    from bastd.mapdata import tip_top as defs

    name = 'Tip Top'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'king_of_the_hill']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'tipTopPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('tipTopLevel'),
            'bottom_model': ba.getmodel('tipTopLevelBottom'),
            'collide_model': ba.getcollidemodel('tipTopLevelCollide'),
            'tex': ba.gettexture('tipTopLevelColor'),
            'bgtex': ba.gettexture('tipTopBGColor'),
            'bgmodel': ba.getmodel('tipTopBG'),
            'railing_collide_model': ba.getcollidemodel('tipTopLevelBumper')
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -0.2, 2.5))
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'color': (0.7, 0.7, 0.7),
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['bottom_model'],
                                     'lighting': False,
                                     'color': (0.7, 0.7, 0.7),
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'color': (0.4, 0.4, 0.4),
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['railing_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (0.8, 0.9, 1.3)
        gnode.ambient_color = (0.8, 0.9, 1.3)
        gnode.vignette_outer = (0.79, 0.79, 0.69)
        gnode.vignette_inner = (0.97, 0.97, 0.99)


class CragCastle(ba.Map):
    """A lovely castle map."""

    from bastd.mapdata import crag_castle as defs

    name = 'Crag Castle'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'cragCastlePreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('cragCastleLevel'),
            'bottom_model': ba.getmodel('cragCastleLevelBottom'),
            'collide_model': ba.getcollidemodel('cragCastleLevelCollide'),
            'tex': ba.gettexture('cragCastleLevelColor'),
            'bgtex': ba.gettexture('menuBG'),
            'bgmodel': ba.getmodel('thePadBG'),
            'railing_collide_model':
                (ba.getcollidemodel('cragCastleLevelBumper')),
            'vr_fill_mound_model': ba.getmodel('cragCastleVRFillMound'),
            'vr_fill_mound_tex': ba.gettexture('vrFillMound')
        }
        # fixme should chop this into vr/non-vr sections
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['bottom_model'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['railing_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_mound_model'],
                       'lighting': False,
                       'vr_only': True,
                       'color': (0.2, 0.25, 0.2),
                       'background': True,
                       'color_texture': self.preloaddata['vr_fill_mound_tex']
                   })
        gnode = ba.getactivity().globalsnode
        gnode.shadow_ortho = True
        gnode.shadow_offset = (0, 0, -5.0)
        gnode.tint = (1.15, 1.05, 0.75)
        gnode.ambient_color = (1.15, 1.05, 0.75)
        gnode.vignette_outer = (0.6, 0.65, 0.6)
        gnode.vignette_inner = (0.95, 0.95, 0.95)
        gnode.vr_near_clip = 1.0


class TowerD(ba.Map):
    """Map used for runaround mini-game."""

    from bastd.mapdata import tower_d as defs

    name = 'Tower D'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'towerDPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model':
                ba.getmodel('towerDLevel'),
            'model_bottom':
                ba.getmodel('towerDLevelBottom'),
            'collide_model':
                ba.getcollidemodel('towerDLevelCollide'),
            'tex':
                ba.gettexture('towerDLevelColor'),
            'bgtex':
                ba.gettexture('menuBG'),
            'bgmodel':
                ba.getmodel('thePadBG'),
            'player_wall_collide_model':
                ba.getcollidemodel('towerDPlayerWall'),
            'player_wall_material':
                ba.Material()
        }
        # fixme should chop this into vr/non-vr sections
        data['player_wall_material'].add_actions(
            actions=('modify_part_collision', 'friction', 0.0))
        # anything that needs to hit the wall can apply this material
        data['collide_with_wall_material'] = ba.Material()
        data['player_wall_material'].add_actions(
            conditions=('they_dont_have_material',
                        data['collide_with_wall_material']),
            actions=('modify_part_collision', 'collide', False))
        data['vr_fill_mound_model'] = ba.getmodel('stepRightUpVRFillMound')
        data['vr_fill_mound_tex'] = ba.gettexture('vrFillMound')
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 1, 1))
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.node_bottom = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'model': self.preloaddata['model_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex']
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_mound_model'],
                       'lighting': False,
                       'vr_only': True,
                       'color': (0.53, 0.57, 0.5),
                       'background': True,
                       'color_texture': self.preloaddata['vr_fill_mound_tex']
                   })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        self.player_wall = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['player_wall_collide_model'],
                'affect_bg_dynamics': False,
                'materials': [self.preloaddata['player_wall_material']]
            })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.15, 1.11, 1.03)
        gnode.ambient_color = (1.2, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.73, 0.7)
        gnode.vignette_inner = (0.95, 0.95, 0.95)

    def is_point_near_edge(self,
                           point: ba.Vec3,
                           running: bool = False) -> bool:
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
        return ((xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5) and
                (xpos2 < -0.5 or xpos2 > 0.5 or zpos2 < -0.5 or zpos2 > 0.5))


class HappyThoughts(ba.Map):
    """Flying map."""

    from bastd.mapdata import happy_thoughts as defs

    name = 'Happy Thoughts'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return [
            'melee', 'keep_away', 'team_flag', 'conquest', 'king_of_the_hill'
        ]

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'alwaysLandPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('alwaysLandLevel'),
            'bottom_model': ba.getmodel('alwaysLandLevelBottom'),
            'bgmodel': ba.getmodel('alwaysLandBG'),
            'collide_model': ba.getcollidemodel('alwaysLandLevelCollide'),
            'tex': ba.gettexture('alwaysLandLevelColor'),
            'bgtex': ba.gettexture('alwaysLandBGColor'),
            'vr_fill_mound_model': ba.getmodel('alwaysLandVRFillMound'),
            'vr_fill_mound_tex': ba.gettexture('vrFillMound')
        }
        return data

    @classmethod
    def get_music_type(cls) -> ba.MusicType:
        return ba.MusicType.FLYING

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -3.7, 2.5))
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['bottom_model'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_mound_model'],
                       'lighting': False,
                       'vr_only': True,
                       'color': (0.2, 0.25, 0.2),
                       'background': True,
                       'color_texture': self.preloaddata['vr_fill_mound_tex']
                   })
        gnode = ba.getactivity().globalsnode
        gnode.happy_thoughts_mode = True
        gnode.shadow_offset = (0.0, 8.0, 5.0)
        gnode.tint = (1.3, 1.23, 1.0)
        gnode.ambient_color = (1.3, 1.23, 1.0)
        gnode.vignette_outer = (0.64, 0.59, 0.69)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        gnode.vr_near_clip = 1.0
        self.is_flying = True

        # throw out some tips on flying
        txt = ba.newnode('text',
                         attrs={
                             'text': ba.Lstr(resource='pressJumpToFlyText'),
                             'scale': 1.2,
                             'maxwidth': 800,
                             'position': (0, 200),
                             'shadow': 0.5,
                             'flatness': 0.5,
                             'h_align': 'center',
                             'v_attach': 'bottom'
                         })
        cmb = ba.newnode('combine',
                         owner=txt,
                         attrs={
                             'size': 4,
                             'input0': 0.3,
                             'input1': 0.9,
                             'input2': 0.0
                         })
        ba.animate(cmb, 'input3', {3.0: 0, 4.0: 1, 9.0: 1, 10.0: 0})
        cmb.connectattr('output', txt, 'color')
        ba.timer(10.0, txt.delete)


class StepRightUp(ba.Map):
    """Wide stepped map good for CTF or Assault."""

    from bastd.mapdata import step_right_up as defs

    name = 'Step Right Up'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'stepRightUpPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('stepRightUpLevel'),
            'model_bottom': ba.getmodel('stepRightUpLevelBottom'),
            'collide_model': ba.getcollidemodel('stepRightUpLevelCollide'),
            'tex': ba.gettexture('stepRightUpLevelColor'),
            'bgtex': ba.gettexture('menuBG'),
            'bgmodel': ba.getmodel('thePadBG'),
            'vr_fill_mound_model': ba.getmodel('stepRightUpVRFillMound'),
            'vr_fill_mound_tex': ba.gettexture('vrFillMound')
        }
        # fixme should chop this into vr/non-vr chunks
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -1, 2))
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.node_bottom = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'model': self.preloaddata['model_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex']
            })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_mound_model'],
                       'lighting': False,
                       'vr_only': True,
                       'color': (0.53, 0.57, 0.5),
                       'background': True,
                       'color_texture': self.preloaddata['vr_fill_mound_tex']
                   })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.2, 1.1, 1.0)
        gnode.ambient_color = (1.2, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)


class Courtyard(ba.Map):
    """A courtyard-ish looking map for co-op levels."""

    from bastd.mapdata import courtyard as defs

    name = 'Courtyard'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'courtyardPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('courtyardLevel'),
            'model_bottom': ba.getmodel('courtyardLevelBottom'),
            'collide_model': ba.getcollidemodel('courtyardLevelCollide'),
            'tex': ba.gettexture('courtyardLevelColor'),
            'bgtex': ba.gettexture('menuBG'),
            'bgmodel': ba.getmodel('thePadBG'),
            'player_wall_collide_model':
                (ba.getcollidemodel('courtyardPlayerWall')),
            'player_wall_material': ba.Material()
        }
        # FIXME: Chop this into vr and non-vr chunks.
        data['player_wall_material'].add_actions(
            actions=('modify_part_collision', 'friction', 0.0))
        # anything that needs to hit the wall should apply this.
        data['collide_with_wall_material'] = ba.Material()
        data['player_wall_material'].add_actions(
            conditions=('they_dont_have_material',
                        data['collide_with_wall_material']),
            actions=('modify_part_collision', 'collide', False))
        data['vr_fill_mound_model'] = ba.getmodel('stepRightUpVRFillMound')
        data['vr_fill_mound_tex'] = ba.gettexture('vrFillMound')
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['model_bottom'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_mound_model'],
                       'lighting': False,
                       'vr_only': True,
                       'color': (0.53, 0.57, 0.5),
                       'background': True,
                       'color_texture': self.preloaddata['vr_fill_mound_tex']
                   })
        # in co-op mode games, put up a wall to prevent players
        # from getting in the turrets (that would foil our brilliant AI)
        if isinstance(ba.getsession(), ba.CoopSession):
            cmodel = self.preloaddata['player_wall_collide_model']
            self.player_wall = ba.newnode(
                'terrain',
                attrs={
                    'collide_model': cmodel,
                    'affect_bg_dynamics': False,
                    'materials': [self.preloaddata['player_wall_material']]
                })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.2, 1.17, 1.1)
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.6, 0.6, 0.64)
        gnode.vignette_inner = (0.95, 0.95, 0.93)

    def is_point_near_edge(self,
                           point: ba.Vec3,
                           running: bool = False) -> bool:
        # count anything off our ground level as safe (for our platforms)
        # see if we're within edge_box
        box_position = self.defs.boxes['edge_box'][0:3]
        box_scale = self.defs.boxes['edge_box'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        return xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5


class Rampage(ba.Map):
    """Wee little map with ramps on the sides."""

    from bastd.mapdata import rampage as defs

    name = 'Rampage'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'rampagePreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('rampageLevel'),
            'bottom_model': ba.getmodel('rampageLevelBottom'),
            'collide_model': ba.getcollidemodel('rampageLevelCollide'),
            'tex': ba.gettexture('rampageLevelColor'),
            'bgtex': ba.gettexture('rampageBGColor'),
            'bgtex2': ba.gettexture('rampageBGColor2'),
            'bgmodel': ba.getmodel('rampageBG'),
            'bgmodel2': ba.getmodel('rampageBG2'),
            'vr_fill_model': ba.getmodel('rampageVRFill'),
            'railing_collide_model': ba.getcollidemodel('rampageBumper')
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 0, 2))
        shared = SharedObjects.get()
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['bottom_model'],
                                     'lighting': False,
                                     'color_texture': self.preloaddata['tex']
                                 })
        self.bg2 = ba.newnode('terrain',
                              attrs={
                                  'model': self.preloaddata['bgmodel2'],
                                  'lighting': False,
                                  'background': True,
                                  'color_texture': self.preloaddata['bgtex2']
                              })
        ba.newnode('terrain',
                   attrs={
                       'model': self.preloaddata['vr_fill_model'],
                       'lighting': False,
                       'vr_only': True,
                       'background': True,
                       'color_texture': self.preloaddata['bgtex2']
                   })
        self.railing = ba.newnode(
            'terrain',
            attrs={
                'collide_model': self.preloaddata['railing_collide_model'],
                'materials': [shared.railing_material],
                'bumper': True
            })
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.2, 1.1, 0.97)
        gnode.ambient_color = (1.3, 1.2, 1.03)
        gnode.vignette_outer = (0.62, 0.64, 0.69)
        gnode.vignette_inner = (0.97, 0.95, 0.93)

    def is_point_near_edge(self,
                           point: ba.Vec3,
                           running: bool = False) -> bool:
        box_position = self.defs.boxes['edge_box'][0:3]
        box_scale = self.defs.boxes['edge_box'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        return xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5
