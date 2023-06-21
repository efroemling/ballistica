# ba_meta require api 7

#  - Maps:               
#  - Neo Zone           
#  - Big H                
#  - The Limbo             
#  - Platforms             
#  - Powerups Factory     
#  - Skull Temple         
#  - Bottom Rampage      
#  - Collosal Bridgit   
#  - Collosal Monkey   
#  - Tower Zoe          
#  - The Crusade        
#  - The Arena          
#  - Island Mine        
#  - Space Thoughts     



from __future__ import annotations

from typing import TYPE_CHECKING

from bastd.maps import *
import ba
import _ba
from ba import _map
import random

if TYPE_CHECKING:
    from typing import Any, List, Dict
    
##Complementos##

class CollideBox:
    def __init__(self,position: Sequence[float] = (0, 0, 0),scale: Sequence[float] = (1, 1, 1),color: Sequence[float] = (1, 1, 1), visible: bool = True, ice: bool = False, death: bool = False):
        shared = SharedObjects.get()
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('they_are_different_node_than_us', ), actions=(('modify_part_collision', 'collide', True)))
        self.no_physical_collide = ba.Material()
        self.no_physical_collide.add_actions(conditions=('they_are_different_node_than_us', ), actions=(('modify_part_collision', 'collide',True), ('modify_part_collision', 'physical', False)))
        self.ice_material = ba.Material()
        self.ice_material.add_actions(actions=('modify_part_collision','friction',0.01))
        
        mats = [self._collide_with_player, shared.footing_material]
        if ice: mats.append(self.ice_material)
        if death:
            mats = [self.no_physical_collide,shared.death_material]
        
        self.region = ba.newnode('region',attrs={'position': position,'scale': scale,'type': 'box','materials': mats})
        if visible:
            locator = ba.newnode('locator',attrs={'shape':'box',
                'color':color,'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False})
            self.region.connectattr('position', locator,'position')
            self.region.connectattr('scale', locator,'size')


class FadeEfect():
    def __init__(self, map_tint = (1,1,1)):
        gnode = ba.getactivity().globalsnode
        ba.animate_array(gnode,'tint',3,{0:(0,0,0),0.5:(0,0,0),1.2:map_tint})
        
        text = ba.newnode('text',
                              attrs={
                                    'position': (0,325),
                                    'text': 'Building Map...',
                                    'color': (1,1,1),
                                    'h_align': 'center','v_align': 'center', 'vr_depth': 410, 'maxwidth': 600, 'shadow': 1.0, 'flatness': 1.0, 'scale':2, 'h_attach': 'center', 'v_attach': 'bottom'})
        ba.animate(text,'opacity',{0:1,0.2:1,0.7:0})
        ba.timer(1,text.delete)
        
        text = ba.newnode('text',
                              attrs={
                                    'position': (0,295),
                                    'text': 'Maps by Sebastian2059-ZackerTz',
                                    'color': (0.1,0.0,0.76),
                                    'h_align': 'center', 'v_align': 'center', 'vr_depth': 410, 'maxwidth': 600, 'shadow': 1.0, 'flatness': 1.0, 'scale':0.7, 'h_attach': 'center', 'v_attach': 'bottom'})
        ba.animate(text,'opacity',{0:1,0.2:1,0.7:0})
        ba.timer(1,text.delete)
        

class Credits:
    """ Don't delete this if you respect other people's work"""
    def __init__(self):
        t = ba.newnode('text',
               attrs={ 'text':"Maps by: SEBASTIAN2059-Zacker Tz", 
        'scale':0.6,
        'position':(0,0), 
        'opacity': 0.1,
        'shadow':0.5,
        'flatness':1.2,
        'color':(1, 1, 1),
        'h_align':'center',
        'v_attach':'bottom'}) # :bobolu:       
# Ultra secret 
#NEW_OBJECTS
class CustomModel(ba.Actor):
    
    def __init__(self, position: Sequence[float] = (0, 0, 0),model: str = '', texture: str = '', scale: float = 1.0):
        super().__init__()
        
        shared = SharedObjects.get()
        
        self._collide_custom=ba.Material()
        self.dont_collide=ba.Material()
        
        self._collide_custom.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self._collide_custom.add_actions(conditions=('they_have_material', self.dont_collide), actions=(('modify_part_collision', 'collide', True)))

        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self.dont_collide.add_actions(conditions=('they_have_material', self._collide_custom), actions=(('modify_part_collision', 'collide', True)))
        
        self.position = position
        self.node = ba.newnode('prop',
                attrs={'body': 'puck','position':self.position,
                       'model': ba.getmodel(model), 'color_texture': ba.gettexture(texture), 
                       'model_scale': scale, 'body_scale': 1.0, 
                       'shadow_size': 0.0, 'gravity_scale':1.0,'reflection': 'soft', 'reflection_scale': [0.0], 'is_area_of_interest': False, 'materials': [self.dont_collide]})
        self.node.extra_acceleration = (0,21.5,0)
        self.region = ba.newnode('region',attrs={'position': (self.position[0],self.position[1]-0.6,self.position[2]-0.54),'scale': (3,0.5,0.5),'type': 'box','materials': (self._collide_custom,)})
        self.region1 = ba.newnode('region',attrs={'position': (self.position[0],self.position[1]+1,self.position[2]+0.54),'scale': (3,0.5,0.5),'type': 'box','materials': (self._collide_custom,)})
            
        def stop():
            self.node.extra_acceleration = (0,0,0)
            self.node.velocity = (0,0,0)
            self.node.gravity_scale = 0
        
        def move():
            ba.animate_array(self.region,'scale',3,{0:(3,0.5,0.5),0.03:(3,4,0.5)})
            ba.animate_array(self.region1,'scale',3,{0:(3,0.5,0.5),0.03:(3,4,0.5)})
            ba.timer(0.035,stop)
        ba.timer(0.001,move)

class CustomModelR3(ba.Actor):
    
    def __init__(self, position: Sequence[float] = (0, 0, 0),model: str = '', texture: str = '', scale: float = 1.0,rotate = 'right'):
        super().__init__()
        
        shared = SharedObjects.get()
        
        self._collide_custom=ba.Material()
        self.dont_collide=ba.Material()
        
        self._collide_custom.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self._collide_custom.add_actions(conditions=('they_have_material', self.dont_collide), actions=(('modify_part_collision', 'collide', True)))

        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self.dont_collide.add_actions(conditions=('they_have_material', self._collide_custom), actions=(('modify_part_collision', 'collide', True)))
        
        self.position = position
        
        x = self.position[0]
        y = self.position[1]
        z = self.position[2]
        
        self.model = ba.newnode('prop',
                attrs={'body': 'puck','position': (x,y,z),
                       'model': ba.getmodel(model), 'color_texture': ba.gettexture(texture), 
                       'model_scale': scale, 'body_scale': 1.0, 
                       'shadow_size': 0.0, 'gravity_scale':1.0,'reflection': 'soft', 'reflection_scale': [0.0], 'is_area_of_interest': False, 'materials': [self.dont_collide]})
        self.model.extra_acceleration = (0,21.5,0)
        
        self.r1 = ba.newnode('region',attrs={'position': (x,y-0.6,z-0.54),'scale': (3,0.5,0.5),'type': 'box','materials': (self._collide_custom,)})
        self.r2 = ba.newnode('region',attrs={'position': (x,y+1,z+0.54),'scale': (3,0.5,0.5),'type': 'box','materials': (self._collide_custom,)})
        
        def stop():
            #ba.screenmessage('stop')
            self.model.extra_acceleration = (0,0,0)
            self.model.velocity = (0,0,0)
            self.model.gravity_scale = 0
            def stop_v2():
                self.model.velocity = (0,0,0)
            ba.timer(0.1,stop_v2)
            
        def move3():
            self.r1.scale = (0.5,0.5,3)
            self.r2.scale = (0.5,0.5,3)
            if rotate == 'right':
                self.r1.position = (x+0.7,y+0.54,z)
                self.r2.position = (x-0.7,y-0.54,z)
            elif rotate == 'left':
                self.r1.position = (x-0.7,y+0.54,z)
                self.r2.position = (x+0.7,y-0.54,z)
            
            ba.animate_array(self.r1,'scale',3,{0:(0.5,0.5,3),0.03:(4,0.5,3)})
            ba.animate_array(self.r2,'scale',3,{0:(0.5,0.5,3),0.03:(4,0.5,3)})
            ba.timer(0.035,stop)
            
        def move2():
            self.r1.scale = (0.5,3,0.5)
            self.r2.scale = (0.5,3,0.5)
            if rotate == 'left':
                self.r1.position = (x+0.54,y,z-0.7)
                self.r2.position = (x-0.54,y,z+0.7)
            elif rotate == 'right':
                self.r1.position = (x+0.54,y,z+0.7)
                self.r2.position = (x-0.54,y,z-0.7)
            ba.animate_array(self.r1,'scale',3,{0:(0.5,3,0.5),0.03:(0.5,3,4)})
            ba.animate_array(self.r2,'scale',3,{0:(0.5,3,0.5),0.03:(0.5,3,4)})
            ba.timer(0.1,move3)
            
        
        def move():
            ba.animate_array(self.r1,'scale',3,{0:(3,0.5,0.5),0.03:(3,4,0.5)})
            ba.animate_array(self.r2,'scale',3,{0:(3,0.5,0.5),0.03:(3,4,0.5)})
            ba.timer(0.05,move2)
        ba.timer(0.001,move)
        
class CustomModelR2(ba.Actor):
    
    def __init__(self, position: Sequence[float] = (0, 0, 0),model: str = '', texture: str = '', scale: float = 1.0,rotate = 'right'):
        super().__init__()
        
        shared = SharedObjects.get()
        
        self._collide_custom=ba.Material()
        self.dont_collide=ba.Material()
        
        self._collide_custom.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self._collide_custom.add_actions(conditions=('they_have_material', self.dont_collide), actions=(('modify_part_collision', 'collide', True)))

        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self.dont_collide.add_actions(conditions=('they_have_material', self._collide_custom), actions=(('modify_part_collision', 'collide', True)))
        
        self.position = position
        
        x = self.position[0]
        y = self.position[1]
        z = self.position[2]
        
        self.model = ba.newnode('prop',
                attrs={'body': 'puck','position': (x,y,z),
                       'model': ba.getmodel(model), 'color_texture': ba.gettexture(texture), 
                       'model_scale': scale, 'body_scale': 1.0, 
                       'shadow_size': 0.0, 'gravity_scale':1.0,'reflection': 'soft', 'reflection_scale': [0.0], 'is_area_of_interest': False, 'materials': [self.dont_collide]})
        self.model.extra_acceleration = (0,21.5,0)
        
        self.r1 = ba.newnode('region',attrs={'position': (x,y-0.6,z-0.54),'scale': (3,0.5,0.5),'type': 'box','materials': (self._collide_custom,)})
        self.r2 = ba.newnode('region',attrs={'position': (x,y+1,z+0.54),'scale': (3,0.5,0.5),'type': 'box','materials': (self._collide_custom,)})
        
        def stop():
            #ba.screenmessage('stop')
            self.model.extra_acceleration = (0,0,0)
            self.model.velocity = (0,0,0)
            self.model.gravity_scale = 0
            def stop_v2():
                self.model.velocity = (0,0,0)
            ba.timer(0.1,stop_v2)
            
        def move2():
            self.r1.scale = (0.5,3,0.5)
            self.r2.scale = (0.5,3,0.5)
            if rotate == 'left':
                self.r1.position = (x+0.54,y,z-0.7)
                self.r2.position = (x-0.54,y,z+0.7)
            elif rotate == 'right':
                self.r1.position = (x+0.54,y,z+0.7)
                self.r2.position = (x-0.54,y,z-0.7)
            ba.animate_array(self.r1,'scale',3,{0:(0.5,3,0.5),0.03:(0.5,3,4)})
            ba.animate_array(self.r2,'scale',3,{0:(0.5,3,0.5),0.03:(0.5,3,4)})
            ba.timer(0.035,stop)
            
        
        def move():
            ba.animate_array(self.r1,'scale',3,{0:(3,0.5,0.5),0.03:(3,4,0.5)})
            ba.animate_array(self.r2,'scale',3,{0:(3,0.5,0.5),0.03:(3,4,0.5)})
            ba.timer(0.1,move2)
        ba.timer(0.001,move)      



        
###End###


#Map by Zacker Tz 
#Map #1
class neo_defs():
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 4, 0) + (0, 0, 0) + (50, 10, 20)
    boxes['edge_box'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (40, 2, 10)
    boxes['map_bounds'] = (0, 4, 0) + (0, 0, 0) + (28, 10, 28)
    points['ffa_spawn1'] = (-10,3.17,0) + (1.0,0.1,1.0)
    points['ffa_spawn2'] = (10,3.17,0) + (1.0,0.1,1.0)
    points['ffa_spawn3'] = (-5.25,3.17,-1.75) + (0.5,0.1,0.5) 
    points['ffa_Spawn4'] = (5.25,3.17,-1.75) + (0.5,0.1,0.5) 
    points['spawn1'] = (-11,3.17,0) + (1.0,0.1,1.0)
    points['spawn2'] = (11,3.17,0) + (1.0,0.1,1.0)
    points['flag1'] = (-12.0,3.3,0) + (2.0,0.1,2.0)
    points['flag2'] = (12.0,3.3,0) + (2.0,0.1,2.0)
    points['flag_default'] = (0,3.3,1.75)
    points['powerup_spawn1'] = (-11,4.0,-1.75)
    points['powerup_spawn2'] = (-11,4.0,1.75)
    points['powerup_spawn3'] = (-1.75,4.0,0)
    points['powerup_spawn4'] = (1.75,4.0,0.0)
    points['powerup_spawn5'] = (11,4.0,-1.75)
    points['powerup_spawn6'] = (11,4.0,1.75)
 

class NeoZone(ba.Map):
    """Agent john's former workplace"""

    defs = neo_defs()
    name = 'Neo Zone'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee','king_of_the_hill','keep_away','team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'rgbStripes'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('landMine'),
            'tex': ba.gettexture('landMine'),
            'bgtex': ba.gettexture('black'),
            'bgmodel': ba.getmodel('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        
        self._map_model = ba.getmodel('image1x1')
        self._map_model2 = ba.getmodel('tnt')
        self._map_tex = ba.gettexture('powerupIceBombs')
        self._map_tex1 = ba.gettexture('ouyaUButton') 
        
        self.background = ba.newnode('terrain',
                                    attrs={
                                    'model': self.preloaddata['bgmodel'],
                                    'lighting': False,
                                    'background': True,
                                    'color_texture': self.preloaddata['bgtex']
            })

        locations = [(7.0,0.0,0),(5.25,0.0,0),(5.25,0.0,-1.75),
                (3.5,0.0,-1.75),(1.75,0.0,-1.75),(1.75,0.0,0),
                (1.75,0.0,1.75),
                (0,0.0,1.75),
                (-7.0,0.0,0),(-5.25,0.0,0),(-5.25,3.17,-1.75),
                (-3.5,0.0,-1.75),(-1.75,0.0,-1.75),(-1.75,0.0,0),
                (-1.75,0.0,1.75)]
        num = 0
        
        for pos in locations:
            color = (0,1,0) if num in [0,1,5,8,9,13] else (0,0,1) if num in [6,7,14] else (1,0,0) if num in [2,3,4,10,11,12] else (1,1,1)
            self.decor = ba.newnode('prop',
                    attrs={'body': 'puck',
                           'position': (pos[0],3.17,pos[2]),
                           'model': self._map_model,
                           'model_scale': 1.7,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex1,
                           'reflection': 'soft',
                           'reflection_scale': [0.5],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})
            self.region = ba.newnode('region',attrs={
                                        'position': (pos[0],2.3,pos[2]),
                                        'scale': (1.9,1.9,1.9),
                                        'type': 'box',
                                        'materials': (self._collide_with_player, shared.footing_material)})
            self.zone = ba.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(pos[0],2.3,pos[2]),
                                    'color':color,
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[1.75,1.75,1.75]})
            num += 1
        
        #Sides  
        side_locations = [(-10.5,2.3,0),(10.5,2.3,0)]    
        for pos in side_locations:
            self.big_region = ba.newnode('region',attrs={
                                        'position': pos,
                                        'scale': (5.7,1.9,5.7),
                                        'type': 'box',
                                        'materials': (self._collide_with_player, shared.footing_material)})        
            self.big_zone = ba.newnode('locator',
                                        attrs={'shape':'box',
                                        'position':pos,
                                        'color':(0,1,1.5),
                                        'opacity':1,'draw_beauty':True,'additive':False,'size':[5.25,1.75,5.25]})         
                                    
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.05, 1.17)
        gnode.happy_thoughts_mode = False
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.9, 0.9, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()

#Map by Sebastian2059
#Map #2
class c_defs():
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 4, 0) + (0, 0, 0) + (50, 10, 20)
    boxes['edge_box'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (40, 2, 10)
    boxes['map_bounds'] = (0, 4, 0) + (0, 0, 0) + (28, 10, 28)
    points['ffa_spawn1'] = (-9,0.5,-3) + (1.0,0.1,5.0)
    points['ffa_spawn2'] = (9,0.5,-3) + (1.0,0.1,5.0)
    points['ffa_spawn3'] = (-6,0.5,-6.0) + (2.0,0.1,1.0) 
    points['ffa_Spawn4'] = (6,0.5,0.0) + (2.0,0.1,1.0) 
    points['ffa_spawn5'] = (6,0.5,-6.0) + (2.0,0.1,1.0) 
    points['ffa_Spawn6'] = (-6,0.5,0.0) + (2.0,0.1,1.0) 
    points['spawn1'] = (-9,0.5,-3) + (1.0,0.1,1.0)
    points['spawn2'] = (9,0.5,-3) + (1.0,0.1,1.0)
    points['flag1'] = (-10.0,0.8,-3) + (2.0,0.1,2.0)
    points['flag2'] = (10.0,0.8,-3) + (2.0,0.1,2.0)
    points['flag_default'] = (0,0.8,-3.0)
    points['powerup_spawn1'] = (-9,1.0,-8)
    points['powerup_spawn2'] = (-9,1.0,3)
    points['powerup_spawn3'] = (-1.5,1.0,-8.25)
    points['powerup_spawn4'] = (1.5,1.0,-8.25)
    points['powerup_spawn5'] = (-1.5,1.0,2.25)
    points['powerup_spawn6'] = (1.5,1.0,2.25)
    points['powerup_spawn7'] = (9,1.0,-8)
    points['powerup_spawn8'] = (9,1.0,3)
    
    points['race_mine1'] = (-1.5, 0.7, -0.7)
    points['race_mine2'] = (-1.5, 0.7, 0.7)
    points['race_mine3'] = (-4.5, 0.7, 0.0)
    points['race_mine4'] = (4.5, 0.7, 0.0)
    points['race_mine5'] = (4.5, 0.7, -6.0)
    points['race_mine6'] = (-4.5, 0.7, -6.0)
    points['race_mine7'] = (0.0, 0.7, -6.0)
    points['race_mine8'] = (-10.0, 0.7, -4.5)
    points['race_mine9'] = (10.0, 0.7, -4.5)    
    points['race_mine10'] = (10.0, 0.7, -1.5)
    points['race_mine11'] = (-10.0, 0.7, -1.5)
    
    points['race_point1'] = (0.0, 0.5, 0.0) + (0.3, 2.0, 1.5)
    points['race_point2'] = (3.5, 0.5, 0.0) + (0.3, 2.0, 1.5)
    points['race_point3'] = (7.0, 0.5, 0.0) + (0.3, 2.0, 1.5)
    points['race_point4'] = (9.0, 0.5, -2.0) + (1.5, 2.0, 0.3)
    points['race_point5'] = (9.0, 0.5, -4.0) + (1.5, 2.0, 0.3)
    points['race_point6'] = (7.0, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point7'] = (3.5, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point8'] = (0.0, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point9'] = (-3.5, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point10'] = (-7.0, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point11'] = (-9.0, 0.5, -2.0) + (1.5, 2.0, 0.3)
    points['race_point12'] = (-9.0, 0.5, -4.0) + (1.5, 2.0, 0.3)
    points['race_point13'] = (-7.0, 0.5, 0.0) + (0.3, 2.0, 1.5)
    points['race_point14'] = (-3.5, 0.5, 0.0) + (0.3, 2.0, 1.5)
 
class CMap(ba.Map):
    """Jack Morgan used to run here"""
    
    defs = c_defs()
    name = 'Big H'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee','king_of_the_hill','keep_away','team_flag','race']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bigG'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('landMine'),
            'tex': ba.gettexture('landMine'),
            'bgtex': ba.gettexture('black'),
            'bgmodel': ba.getmodel('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self.ice_material = ba.Material()
        self.ice_material.add_actions(actions=('modify_part_collision','friction',0.01))
        
        self._map_model = ba.getmodel('image1x1')
        self._map_model2 = ba.getmodel('tnt')
        self._map_tex = ba.gettexture('powerupIceBombs')
        self._map_tex1 = ba.gettexture('circleOutlineNoAlpha') 
        self._map_tex2 = ba.gettexture('black') 
        
        self.background = ba.newnode('terrain',
                                    attrs={
                                    'model': self.preloaddata['bgmodel'],
                                    'lighting': False,
                                    'background': True,
                                    'color_texture': self.preloaddata['bgtex']
            })

        posS = [(0.0,0.05,0)]
        for m_pos in posS:
            self.mv_center = ba.newnode('prop',
                    attrs={'body': 'puck',
                           'position': m_pos,
                           'model': self._map_model,
                           'model_scale': 35,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex2,
                           'reflection': 'soft',
                           'reflection_scale': [0],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})        
        
        locations = [(-9,0.0,-3.0),(9,0.0,-3.0),(0.0,0.0,-6.0),(0.0,0.0,0.0),(0.0,0.0,-3.0)]
        scales = [[3.0,1.0,14.0],[3.0,1.0,14.0],[15.0,1.0,3.0],[15.0,1.0,3.0],[3.0,1.0,3.0]]
        index = 0
        for pos in locations:
            #
            scale = scales[index]
            ba.newnode('region',attrs={'position': pos,'scale': scale,'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
            ba.newnode('locator',attrs={'shape':'box','position':pos,
                'color':(1,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':scale})
            index += 1
        
        pos = [-3.0,0.0,-8.25]
        for p in range(10):
            scale = [1.5,1.0,1.5]
            ba.newnode('region',attrs={'position': pos,'scale': scale,'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
            ba.newnode('locator',attrs={'shape':'box','position':pos,
                'color':(1,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':scale})
            pos[0] += 1.5
            if p == 4:
                pos[0] = -3.0
                pos[2] = 2.25
        
        try:
            self._gamemode = ba.getactivity().name
        except Exception:
            #print('error')
            pass
        if self._gamemode == 'Race':
         #   print('Es carrera')
            ice_locations = [(-8,0.0,0),(8,0.0,0),
                             (-8,0.0,-6),(8,0.0,-6),
                             (-9,0.0,-3),(9,0.0,-3)]

            for pos in ice_locations:
                scale = [3.0,1.025,3.0]
                ba.newnode('region',attrs={'position': pos,'scale': scale,'type': 'box','materials': (self._collide_with_player, shared.footing_material, self.ice_material)})
                ba.newnode('locator',attrs={'shape':'box','position':pos,
                    'color':(0,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':scale})                         
        #Meme
        text = ba.newnode('text',
                              attrs={'position':(0,21,0),
                                     'text':'Tz = Tz \nTz = Trolleador Zaturno\nTrolleador Zaturno = Tazer\nTazer = The Game ',
                                     'in_world':True,
                                     'shadow':1.5,
                                     'flatness':0.7,
                                     'color':(1,1,1.2),
                                     'opacity':1.0,
                                     'scale':0.023,
                                     'h_align':'center'})              
                    
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.05, 1.17)
        gnode.happy_thoughts_mode = False
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.9, 0.9, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)  
        FadeEfect(gnode.tint)
        Credits()          

#Map by Zaker DC [Inspiration from a map of Sebastian]
#Map 3#
class factory_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 4, 0) + (0, 0, 0) + (50, 10, 20)
    boxes['edge_box'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (40, 2, 10)
    boxes['map_bounds'] = (0, 4, 0) + (0, 0, 0) + (28, 10, 28)
    
    points['ffa_spawn1'] = (-8,3.5,0) 
    points['ffa_spawn2'] = (8,3.5,0) 
    points['ffa_spawn3'] = (3.4,3.75,3) 
    points['ffa_Spawn4'] = (-3.4,-0.75,-3)
    
    points['spawn1'] = (-8,3.5,0) + (1.0,0.1,1.0)
    points['spawn2'] = (8,3.5,0) + (1.0,0.1,1.0)
    
    points['flag1'] = (-9.5,3.5,0) + (2.0,0.1,2.0)
    points['flag2'] = (9.5,3.5,0) + (2.0,0.1,2.0)
    points['flag_default'] = (0,3.7,0)
    
    points['powerup_spawn1'] = (4.8,3.65,3)
    points['powerup_spawn2'] = (-4.8,3.65,-3)
    points['powerup_spawn3'] = (-4.2,3.7,1.4)    
    points['powerup_spawn4'] = (4.1,3.7,-1.4)

class FactoryMap(ba.Map):
    """Grambledorf former experiment room"""

    defs = factory_defs 
    name = 'Powerups Factory'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee','king_of_the_hill','keep_away','team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'zigZagLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'model': ba.getmodel('landMine'),
            'tex': ba.gettexture('landMine'),
            'bgtex': ba.gettexture('bg'),
            'bgmodel': ba.getmodel('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        
        self._map_model = ba.getmodel('image1x1')
        self._map_model2 = ba.getmodel('tnt')
        self._map_tex1 = ba.gettexture('powerupImpactBombs') 
        self._map_tex2 = ba.gettexture('reflectionChar_-y') 
        self._map_tex3 = ba.gettexture('flagPoleColor')

        
        self.background = ba.newnode('terrain',
                                    attrs={
                                    'model': self.preloaddata['bgmodel'],
                                    'lighting': False,
                                    'background': True,
                                    'color': (1.3, 1.3, 1.3),
                                    'color_texture': self.preloaddata['bgtex']
            })

        posXD = [(1.5,2.3,0),(-1.5,2.3,0),(0,2.3,0), (4.0,2.3,1.5),(4.0,2.3,-1.5),(4.0,2.3,0), (4.8,2.3,3),(3.4,2.3,3),(1.9,2.3,3), (-4.0,2.3,1.5),(-4.0,2.3,-1.5),(-4.0,2.3,0), (-4.8,2.3,-3),(-3.4,2.3,-3),(-1.9,2.3,-3)
                ]        
        for m_pos in posXD:
            self.mv_center = ba.newnode('prop',
                    attrs={'body': 'puck',
                           'position': m_pos,
                           'model': self._map_model2,
                           'model_scale': 2.2,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex1,
                           'reflection': 'soft',
                           'reflection_scale': [0.5],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})
                           
        posXD = [(-3.4,0.75,-3),(-3.4,-0.75,-3)
                ]                          
        for m_pos in posXD:
            self.mc_center = ba.newnode('region',attrs={ 'position': m_pos,
                                        'scale': (1.5,1.5,1.5), 'type': 'box', 'materials': (self._collide_with_player, shared.footing_material)})        
                                                                
        for m_pos in [(0,2.3,0)]:
            self.mc_center = ba.newnode('region',attrs={'position': m_pos,
                                        'scale': (4.5,1.5,1.5), 'type': 'box', 'materials': (self._collide_with_player, shared.footing_material)})     
                                        
        for m_pos in [(4.0,2.3,0),(-4.0,2.3,0)]:
            self.mc_center = ba.newnode('region',attrs={'position': m_pos,
                                        'scale': (1.5,1.5,4.5), 'type': 'box', 'materials': (self._collide_with_player, shared.footing_material)})  
                                        
        for m_pos in [(3.4,2.3,3),(-3.4,2.3,-3)]:
            self.mc_center = ba.newnode('region',attrs={'position': m_pos,
                                        'scale': (4.5,1.5,1.5), 'type': 'box', 'materials': (self._collide_with_player, shared.footing_material)})                                              
     
        # Cajas Grandes Normales     
        for m_pos in [(8.7,1.72,0),(6.10,1.72,0),(-8.7,1.72,0),(-6.10,1.72,0)]:
            self.mv_d2 = ba.newnode('prop',
                    attrs={'body': 'puck', 'position': m_pos,
                           'model': self._map_model2,
                           'model_scale': 3.8,
                           'color_texture': self._map_tex1, 
                           'reflection_scale': [1.0], 'body_scale': 0.1,  'shadow_size': 0.0, 'gravity_scale':0.0, 'reflection': 'soft', 'is_area_of_interest': True, 'materials': [self.dont_collide]})
                           
        for m_pos in [(7.45,1.72,0),(-7.45,1.72,0)]:                           
            self.mc_d2 = ba.newnode('region',attrs={'position': m_pos,
                                 'scale': (5.25,2.7,2.7), 'type': 'box', 'materials': (self._collide_with_player, shared.footing_material)})
                                 
        #Superficie
        pos = [(-1.5,3.075,0),(0,3.075,0),(1.5,3.075,0), (4.0,3.075,1.5),(4.0,3.075,-1.5),(4.0,3.075,0), (-4.0,3.075,-1.5),(-4.0,3.075,1.5),(-4.0,3.075,0), (-4.8,3.075,-3),(-3.4,3.075,-3),(-1.9,3.075,-3), (4.8,3.075,3),(3.4,3.075,3),(1.9,3.075,3)]
        for m_pos in pos:  
            self.mv_centera = ba.newnode('prop',
                    attrs={'body': 'puck', 'position': m_pos,
                           'model': self._map_model,
                           'color_texture': self._map_tex3,
                           'model_scale': 1.5, 'body_scale': 0.1, 'shadow_size': 0.0, 'gravity_scale':0.0, 'reflection': 'soft', 'reflection_scale': [0.5],'is_area_of_interest': True,
                           'materials': [self.dont_collide]})
           
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.1, 1.17)
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.8, 0.7, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()
        

# Map by SEBASTIAN2059 
# Map 4#
class platforms_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 4, 0) + (0, 0, 0) + (50, 10, 20)
    boxes['edge_box'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (40, 2, 10)
    boxes['map_bounds'] = (0, 4, 0) + (0, 0, 0) + (28, 10, 28)
    points['ffa_spawn1'] = (-10,3.5,0) + (2.0,0.1,2.0)
    points['ffa_spawn2'] = (10,3.5,0) + (2.0,0.1,2.0)
    points['ffa_spawn3'] = (0,3.5,1) 
    points['ffa_Spawn4'] = (0,3.5,-1)
    points['spawn1'] = (-10,3.5,0) + (2.0,0.1,2.0)
    points['spawn2'] = (10,3.5,0) + (2.0,0.1,2.0)
    points['flag1'] = (-12,3.5,0) + (2.0,0.1,2.0)
    points['flag2'] = (12,3.5,0) + (2.0,0.1,2.0)
    points['flag_default'] = (0,3.5,0)    
    points['powerup_spawn1'] = (-11.8,4,-1.8)
    points['powerup_spawn2'] = (-8.2,4,1.8)
    points['powerup_spawn3'] = (8.2,4,-1.8)
    points['powerup_spawn4'] = (11.8,4,1.8)

class PlatformsMap(ba.Map):
    """Plataforms!"""
    defs = platforms_defs
    name = 'Platforms'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee','king_of_the_hill','keep_away','team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bridgitLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'bgtex': ba.gettexture('bg'),
            'bgmodel': ba.getmodel('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        
        self._map_model = ba.getmodel('image1x1')
        self._map_tex = ba.gettexture('powerupIceBombs')
        self._map_tex1 = ba.gettexture('powerupPunch') 
        self._map_tex2 = ba.gettexture('powerupImpactBombs')
        
        self.background = ba.newnode('terrain',
                                    attrs={
                                    'model': self.preloaddata['bgmodel'],
                                    'lighting': False,
                                    'background': True,
                                    'color_texture': self.preloaddata['bgtex']
            })
            
        for m_pos in [(-10,2.5,0),(10,2.5,0)]:
            self.e_cnnt = ba.newnode('math', owner=self.node, attrs={'input1': (0, 0.5, 0), 'operation': 'add'})
            self.mc = ba.newnode('region',attrs={'position': m_pos,'scale': (5.0,1,5.0),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
            self.mv = ba.newnode('prop', owner=self.mc,
                    attrs={'body': 'puck','position': m_pos, 'model': self._map_model, 'model_scale': 5.0, 'body_scale': 0.1, 'shadow_size': 0.0, 'gravity_scale':0.0, 'color_texture': self._map_tex, 'reflection': 'soft', 'reflection_scale': [1.0], 'is_area_of_interest': True, 'materials': [self.dont_collide]})
            self.mc.connectattr('position', self.e_cnnt, 'input2')
            self.e_cnnt.connectattr('output', self.mv, 'position')
            
        for m_pos in [(0,2.5,1.35),(0,2.5,-1.35)]:
            self.c_cnnt = ba.newnode('math', owner=self.node, attrs={'input1': (0, 0.5, 0), 'operation': 'add'})
            self.mc_center = ba.newnode('region',attrs={'position': m_pos,'scale': (2.7,1,2.7),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
            self.mv_center = ba.newnode('prop', owner=self.mc,
                    attrs={'body': 'puck','position': m_pos, 'model': self._map_model, 'model_scale': 2.7, 'body_scale': 0.1, 'shadow_size': 0.0, 'gravity_scale':0.0, 'color_texture': self._map_tex, 'reflection': 'soft', 'reflection_scale': [1.0], 'is_area_of_interest': True, 'materials': [self.dont_collide]})
            self.mc_center.connectattr('position', self.c_cnnt, 'input2')
            self.c_cnnt.connectattr('output', self.mv_center, 'position')
        
        for m_pos in [(1.1,3.01,0),(-1.1,3.01,0)]:
            self.dec = ba.newnode('prop', owner=self.mc,
                    attrs={'body': 'puck','position': m_pos, 'model': self._map_model, 'model_scale': 0.5, 'body_scale': 0.1, 'shadow_size': 0.0, 'gravity_scale':0.0, 'color_texture': self._map_tex2, 'reflection': 'soft', 'reflection_scale': [1.0], 'is_area_of_interest': True, 'materials': [self.dont_collide]})

        pos = [(-5.9,2.5,1),(-3,2.5,-1),(3,2.5,1),(5.9,2.5,-1)]
        for m_pos in pos:
            self.m_cnnt = ba.newnode('math', owner=self.node, attrs={'input1': (0, 0.5, 0), 'operation': 'add'})
            self.mc_a = ba.newnode('region',attrs={'position': m_pos,'scale': (2.5,1,2.5),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
            self.mv_a = ba.newnode('prop', owner=self.mc,
                    attrs={'body': 'puck','position': m_pos, 'model': self._map_model, 'model_scale': 2.5, 'body_scale': 0.1, 'shadow_size': 0.0, 'gravity_scale':0.0, 'color_texture': self._map_tex1, 'reflection': 'soft', 'reflection_scale': [1.0], 'is_area_of_interest': True, 'materials': [self.dont_collide]})
            self.mc_a.connectattr('position', self.m_cnnt, 'input2')
            self.m_cnnt.connectattr('output', self.mv_a, 'position')
            if m_pos[2] == -1:
                ba.animate_array(self.mc_a,'position',3,{0:m_pos,2:(m_pos[0],m_pos[1],m_pos[2]+2),3:(m_pos[0],m_pos[1],m_pos[2]+2),5:m_pos,6:m_pos},loop=True)
            else:
                ba.animate_array(self.mc_a,'position',3,{0:m_pos,2:(m_pos[0],m_pos[1],m_pos[2]-2),3:(m_pos[0],m_pos[1],m_pos[2]-2),5:m_pos,6:m_pos},loop=True)
        
    
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.05, 1.17)
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.9, 0.9, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()
        
#Map By Zacker 
#Map 5#
class darkzone_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 6, 0) + (0, 5, 0) + (17, 9, 5520)
    boxes['map_bounds'] = (0, 0, 0) + (0, 0, 0) + (20.0, 23, 7.25)
    points['flag_default'] = (0,5.1,0)
    points['flag1'] = (-6.5,5.79,0.4)
    points['spawn1'] = (-4.4,5,0)
    points['flag2'] = (6.5,5.79,0.4)
    points['spawn2'] = (4.4,5,0)
    points['ffa_spawn1'] = (3,5.2,0)
    points['ffa_spawn2'] = (-3,5.2,0)
    points['ffa_spawn3'] = (4,5.2,0)
    points['ffa_spawn4'] = (-4,5.2,0)   
    points['ffa_spawn5'] = (0,5.2,0)
    points['powerup_spawn1'] = (-5.5,7,0) 
    points['powerup_spawn2'] = (5.5,7,0)

class DarkZone(ba.Map):
    """Unknown city"""
    defs = darkzone_defs 
    name = 'The Limbo'
    
    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee','king_of_the_hill','keep_away','team_flag']
    
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'shrapnel1Color'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'bottom_model': ba.getmodel('rampageLevelBottom'), 
            'tex': ba.gettexture('rampageLevelColor'),
            'bgmodel1': ba.getmodel('rampageBG'),
            'bgtex1': ba.gettexture('rampageBGColor'),          
            'bgtex': ba.gettexture('shrapnel1Color'),
            'bgmodel': ba.getmodel('thePadBG'),
        }
        return data
        
    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        
        self._map_model1 = ba.getmodel('image1x1')
        self._map_model2 = ba.getmodel('tnt')
        self._map_tex1 = ba.gettexture('black') 
        self._map_tex2 = ba.gettexture('reflectionChar_-y') 
        self._map_tex3 = ba.gettexture('bg')
        self._map_tex4 = ba.gettexture('circleOutlineNoAlpha')
        
        self.background = ba.newnode('terrain',
                                    attrs={
                                    'model': self.preloaddata['bgmodel'],
                                    'lighting': False,
                                    'background': True,
                                    'color_texture': self.preloaddata['bgtex']
            })
            
        self.bg2 = ba.newnode('terrain',
                              attrs={
                                  'model': self.preloaddata['bgmodel1'],
                                  'lighting': False,
                                  'background': True,
                                  'color_texture': self.preloaddata['bgtex1']
                              })                              
         
        self.zone = ba.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(0,5,0),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[15.5,0.05,5.3]})
        ba.animate_array(self.zone, 'color', 3,{0:(0,0,0), 1.5:(0,0,0), 2.00:(0,0,0), 2.05:(1,1,1), 2.1:(0,0,0), 2.15:(1,1,1), 2.2:(0,0,0),
                                                2.25:(1,1,1), 2.3:(0,0,0), 2.35:(1,1,1), 2.4:(0,0,0), 2.45:(0.7,0.7,0.7)},False)
                                    
        self.zone = ba.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(0,3,0),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[15.5,0.05,5.3]})                          
        ba.animate_array(self.zone, 'color', 3,{0:(0,0,0), 1.5:(0,0,0), 2.00:(0,0,0), 2.05:(1,1,1), 2.1:(0,0,0), 2.15:(1,1,1), 2.2:(0,0,0),
                                                2.25:(1,1,1), 2.3:(0,0,0), 2.35:(1,1,1), 2.4:(0,0,0), 2.45:(0.7,0.7,0.7)},False)
                                                
        self.zone = ba.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(0,1,0),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[15.5,0.05,5.3]})
        ba.animate_array(self.zone, 'color', 3,{0:(0,0,0), 1.5:(0,0,0), 2.00:(0,0,0), 2.05:(1,1,1), 2.1:(0,0,0), 2.15:(1,1,1), 2.2:(0,0,0),
                                                2.25:(1,1,1), 2.3:(0,0,0), 2.35:(1,1,1), 2.4:(0,0,0), 2.45:(0.7,0.7,0.7)},False)

        for m_pos1 in [(-5,3,0),(0,3,0),(5,3,0)]:   
            self.mv_center = ba.newnode('prop',
                    attrs={'body': 'puck',
                           'position': m_pos1,
                           'model': self._map_model2,
                           'model_scale': 7.23,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex3,
                           'reflection': 'soft',
                           'reflection_scale': [0.37],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})    
                           
        for m_pos1 in [(0,3,0)]:                              
            self.mc_center = ba.newnode('region',attrs={
                                        'position': m_pos1,
                                        'scale': (15,5,5),
                                        'type': 'box',
                                        'materials': (self._collide_with_player, shared.footing_material)})                                
                           
                           
        for m_pos1 in [(-5,5.4,0),(0,5.4,0),(5,5.4,0)]:    
            self.mv_center = ba.newnode('prop',
                    attrs={'body': 'puck',
                           'position': m_pos1,
                           'model': self._map_model1,
                           'model_scale': 4.00,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex4,
                           'reflection': 'soft',
                           'reflection_scale': [0.0],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})                             
        
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.2,1.2,1.2)
        gnode.ambient_color = (1.15,1.25,1.6)
        gnode.vignette_outer = (0.5,-0.25,0.5)
        gnode.vignette_inner = (0.93,0.93,0.95)
        FadeEfect(gnode.tint)
        Credits()        
        
class arena_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 6, -7) + (0, 5, 0) + (17, 9, 5520)
    boxes['map_bounds'] = (0, 0, 0) + (0, 0, 0) + (20.0, 23, 20.25)
    points['flag_default'] = (0,5.5,0)
    
    points['spawn1'] = (-4.4,5,0)
    points['spawn2'] = (4.4,5,0)   
    
    points['flag1'] = (-6, 6, 0) 
    points['flag2'] = (6, 6, 0)
    points['flag3'] = (0, 6, 6)
    points['flag4'] = (0, 6, -6)
    points['flag5'] = (-4, 6, -4.4)
    points['flag6'] = (4, 6, -4.4)
    points['flag7'] = (-4.4, 6, 4)
    points['flag8'] = (4.4, 6, 4)
    
    points['spawn_by_flag1'] = (-6, 6, 0)
    points['spawn_by_flag2'] = (6, 6, 0)
    points['spawn_by_flag3'] = (0, 6, 6)
    points['spawn_by_flag4'] = (0, 6, -6)       
    points['spawn_by_flag5'] = (-4, 6, -4.4)
    points['spawn_by_flag6'] = (4, 6, -4.4)
    points['spawn_by_flag7'] = (-4.4, 6, 4)
    points['spawn_by_flag8'] = (4.4, 6, 4)    

    points['ffa_spawn1'] = (-6, 6, 0) 
    points['ffa_spawn2'] = (6, 6, 0)
    points['ffa_spawn3'] = (0, 6, 6)
    points['ffa_spawn4'] = (0, 6, -6)
    points['ffa_spawn5'] = (-4, 6, -4.4)
    points['ffa_spawn6'] = (4, 6, -4.4)
    points['ffa_spawn7'] = (-4.4, 6, 4)
    points['ffa_spawn8'] = (4.4, 6, 4)    
    
    points['powerup_spawn1'] = (-4.0,7,0) 
    points['powerup_spawn2'] = (4.0,7,0)
    points['powerup_spawn3'] = (0,7,-4.0)
    points['powerup_spawn4'] = (0,7,4.0)
    

class Tarena(ba.Map):
    """? ? ?"""
    defs =  arena_defs
    name = 'The Arena'
    
    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee','king_of_the_hill','keep_away','team_flag','conquest']
    
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'natureBackgroundColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'bottom_model': ba.getmodel('rampageLevelBottom'), 
            'tex': ba.gettexture('rampageLevelColor'),
            'bgmodel1': ba.getmodel('rampageBG'),
            'bgtex1': ba.gettexture('rampageBGColor'),          
            'bgtex': ba.gettexture('black'),
            'bgmodel': ba.getmodel('thePadBG'),
        }
        return data
        
    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        
        self._map_model1 = ba.getmodel('image1x1')
        self._map_model2 = ba.getmodel('tnt')
        self._map_tex1 = ba.gettexture('black') 
        self._map_tex2 = ba.gettexture('reflectionChar_-y') 
        self._map_tex3 = ba.gettexture('bg')
        self._map_tex4 = ba.gettexture('circleOutlineNoAlpha')
        
        self.background = ba.newnode('terrain',
                                    attrs={
                                    'model': self.preloaddata['bgmodel'],
                                    'lighting': False,
                                    'background': True,
                                    'color_texture': self.preloaddata['bgtex']
            })        
        
 
        for m_pos1 in [(0,5.44,0)]:   
            self.mv_center = ba.newnode('prop',
                    attrs={'body': 'puck',
                           'position': m_pos1,
                           'model': self._map_model1,
                           'model_scale': 17.23,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex3,
                           'reflection': 'soft',
                           'reflection_scale': [0.37],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})  
                              

        CollideBox(position=(0,3,0),scale=(24, 5, 24),color=(1,0,1), visible=False)
                                        
        #Principal                   
        self.zone = ba.newnode('locator',
                                    attrs={'shape':'circleOutline',
                                    'position':(0,5.46,0),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[16.7]})  
        ba.animate_array(self.zone, 'color', 3,{0:(0,0,0), 1.5:(0,0,0), 2.00:(0,0,0), 2.05:(1,1,1), 2.1:(0,0,0), 2.15:(1,1,1), 2.2:(0,0,0),
                                                2.25:(1,1,1), 2.3:(0,0,0), 2.35:(1,1,1), 2.4:(0,0,0), 2.45:(1.1,1.1,1.1)},False)  

        ###
        scale = 17.6
        for zone in range(10):
            self.zone = ba.newnode('locator',
                                        attrs={'shape':'circleOutline',
                                        'position':(0,5.46,0),
                                        'color':(0,0,0),
                                        'opacity':1,'draw_beauty':True,'additive':False,'size':[scale]})  
            scale += 0.8 
                                                       
        #Meme
        text = ba.newnode('text',
                              attrs={'position':(0,21,0),
                                     'text':'Never gonna give you up\nNever gonna let you down\nNever gonna run around and desert you',
                                     'in_world':True,
                                     'shadow':1.5,
                                     'flatness':0.7,
                                     'color':(1,1,1.2),
                                     'opacity':1.0,
                                     'scale':0.023,
                                     'h_align':'center'})   
        
        self._region_material = ba.Material()
        self._region_material.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect',
                 ba.Call(self._handle_collide, True)),
                ('call', 'at_disconnect',
                 ba.Call(self._handle_collide, False)),
            ))
        
        # Flag region.
        scale = 7.25+0.1
        mats = [self._region_material, shared.region_material]
        self.kill_region = ba.newnode('region',
                   attrs={
                       'position': (0,5.5,0),
                       'scale': (scale, scale, scale),
                       'type': 'sphere',
                       'materials': mats
                   })
        # ba.newnode('locator',
                                    # attrs={'shape':'circleOutline',
                                    # 'position':(0,5.46,0),
                                    # 'color':(1,1,0),
                                    # 'opacity':1,'draw_beauty':True,'additive':False,'size':[scale*2.4]})  

        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.2,1.2,1.2)
        gnode.ambient_color = (1.15,1.25,1.6)
        gnode.vignette_outer = (0.5,0.4,0.5)
        gnode.vignette_inner = (0.93,0.93,0.95)   
        FadeEfect(gnode.tint)
        Credits()
    
    def _handle_collide(self,collide: bool):
        try:
            node = ba.getcollision().opposingnode
            #ba.screenmessage('Collide: '+str(collide))
            #print(str(node.getnodetype()))
            if not collide:
                p1 = node.position
                p2 = self.kill_region.position
                diff = (ba.Vec3(p1[0]-p2[0],p1[1]-p2[1],p1[2]-p2[2]))
                dist = (diff.length())
                #print(str(dist))
                if dist > 7.6:
                    node.handlemessage(ba.DieMessage())
        except: pass                

class island_mine:
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (0, 10, -0) + (0.0, 0.0, 0.0) + (20, 20, 10)
    boxes['map_bounds'] = (0, 3.5, -5) + (0.0, 0.0, 0.0) + (20, 15, 30)
    
    points['ffa_spawn1'] = (-4.5, 7, -8) + (2,2,2)
    points['ffa_spawn2'] = (4.5, 7, -8) + (2,2,2)
    points['ffa_spawn3'] = (3, 3.5, -0.5) + (3,2,2)
    points['ffa_spawn4'] = (-3, 3.5, -0.5) + (3,2,2)
    
    points['flag1'] = (-5, 6.5, -8)
    points['flag2'] = (5, 6.5, -8)
    points['flag3'] = (-5, 4.0, -0.5)
    points['flag4'] = (5, 4.0, -0.5)
    points['flag_default'] = (0, 4.0, -0.5)
    
    points['spawn1'] = (-4.5, 6, -8) + (1.0,2,1.5)
    points['spawn2'] = (4.5, 6, -8) + (1.0,2,1.5)
    points['spawn_by_flag1'] = (-4.5, 6, -8) + (1.0,2,1.5)
    points['spawn_by_flag2'] = (4.5, 6, -8) + (1.0,2,1.5)
    points['spawn_by_flag3'] = (-4, 3.5, -0.5) + (1.5, 1.5, 1.5)
    points['spawn_by_flag4'] = (4, 3.5, -0.5) + (1.5, 1.5, 1.5) 
    
    points['powerup_spawn1'] = (-3,4,-2.5) 
    points['powerup_spawn2'] = (-2,4,1.5)
    points['powerup_spawn3'] = (3,4,-2.5)
    points['powerup_spawn4'] = (2,4,1.5)
    
class IslandMine(ba.Map):
    """A simple square shaped map with a raised edge."""

    defs = island_mine

    name = 'Island Mine'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'king_of_the_hill','conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'landMine'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
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
        
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('they_are_different_node_than_us', ), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self.ice_material = ba.Material()
        self.ice_material.add_actions(actions=('modify_part_collision','friction',0.0))
        self.plataform_material = ba.Material()
        self.plataform_material.add_actions(conditions=('they_have_material',shared.footing_material),actions=(('modify_part_collision', 'collide', True)))
        
        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })
        
        
        self.r0 = ba.newnode('region',attrs={'position': (0,6,-8.0),'scale': [6,0.1,2.5-0.1],'type': 'box','materials': (self.plataform_material, self.ice_material)})

        self.r01 = ba.newnode('region',attrs={'position': (0,6.25,-8.0-1.25+0.05),'scale': [6,1,0.01],'type': 'box','materials': (self.plataform_material, self.ice_material)})

        self.r02 = ba.newnode('region',attrs={'position': (0,6.25,-8.0+1.25-0.05),'scale': [6,1,0.01],'type': 'box','materials': (self.plataform_material, self.ice_material)})
        
        
        self.mine = ba.newnode('prop', delegate=self, attrs={
            'position': (0,6.5,-8.0),
            'velocity': (2,0,0),
            'color_texture': ba.gettexture('landMine'),
            'model': ba.getmodel('landMine'),
            #'light_model': ba.getmodel('powerupSimple'),
            'model_scale':3.3,
            'body': 'landMine',
            'body_scale':3.3,
            'density':1,
            'gravity_scale':0.2,
            'reflection': 'soft',
            'reflection_scale': [0.25],
            'shadow_size': 0.0,
            'max_speed':1.5,
            'materials': [shared.footing_material]})
            
        #print(str(dir(self.mine)))
        
            
        def move_platform(value,time):
           # print('move')
            v = self.mine.velocity
            def _safe_setattr(node,attr,val):
          #      print('safe_attr, '+str(attr)+', '+str(val))
                if node.exists(): setattr(node,attr,val)
            def repeat_move():
                ba.timer(0.001,ba.Call(_safe_setattr,self.mine,'velocity',(-value/3,0,0)))
                ba.timer(0.001,ba.Call(_safe_setattr,self.mine,'extra_acceleration',(-value/1.5,0,0)))
                ba.timer(time+0.3,ba.Call(_safe_setattr,self.mine,'velocity',(value/3,0,0)))
                ba.timer(time+0.3,ba.Call(_safe_setattr,self.mine,'extra_acceleration',(value/1.5,0,0)))
                ba.timer(time*2+0.3,ba.Call(repeat_move))
            ba.timer(0.001,ba.Call(_safe_setattr,self.mine,'velocity',(value/3,0,0)))
            ba.timer(0.001,ba.Call(_safe_setattr,self.mine,'extra_acceleration',(value/1.5,0,0)))
            ba.timer(time/2,ba.Call(repeat_move))
                
        move_platform(1,3)
        
        self.r = ba.newnode('region',attrs={'position': (0,2,-0.5),'scale': [12,3,6],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('prop', delegate=self, attrs={
            'position': (-3,0.4,-0.5),
            'velocity': (0,0,0),
            'color_texture': ba.gettexture('flagColor'),
            'model': ba.getmodel('powerupSimple'),
            'model_scale':10.6,
            'body': 'puck',
            'body_scale':3,
            'density':1,
            'gravity_scale':0,
            'reflection': 'soft',
            'reflection_scale': [0.0],
            'shadow_size': 0.0,
            'materials': [self.dont_collide]})
            
        ba.newnode('prop', delegate=self, attrs={
            'position': (3,0.4,-0.5),
            'velocity': (0,0,0),
            'color_texture': ba.gettexture('flagColor'),
            'model': ba.getmodel('powerupSimple'),
            'model_scale':10.6,
            'body': 'puck',
            'body_scale':3,
            'density':1,
            'gravity_scale':0,
            'reflection': 'soft',
            'reflection_scale': [0.0],
            'shadow_size': 0.0,
            'materials': [self.dont_collide]})
        
        self.r1 = ba.newnode('region',attrs={'position': (4.5,5,-5-4+1),'scale': [3,3,3],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        
        p = ba.newnode('prop', delegate=self, attrs={
            'position': (0,6.5,-8.0),
            'velocity': (2,0,0),
            'color_texture': ba.gettexture('flagColor'),
            'model': ba.getmodel('powerupSimple'),
            'model_scale':5.3,
            'body': 'puck',
            'body_scale':1,
            'density':1,
            'gravity_scale':0.2,
            'reflection': 'soft',
            'reflection_scale': [0.0],
            'shadow_size': 0.0,
            'max_speed':1.5,
            'materials': [self.dont_collide]})
        self.r1.connectattr('position', p,'position')
                   
        self.r2 = ba.newnode('region',attrs={'position': (-4.5,5,-5-4+1),'scale': [3,3,3],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        p2 = ba.newnode('prop', delegate=self, attrs={
            'position': (0,6.5,-8.0),
            'velocity': (2,0,0),
            'color_texture': ba.gettexture('flagColor'),
            'model': ba.getmodel('powerupSimple'),
            'model_scale':5.3,
            'body': 'puck',
            'body_scale':1,
            'density':1,
            'gravity_scale':0.2,
            'reflection': 'soft',
            'reflection_scale': [0.0],
            'shadow_size': 0.0,
            'max_speed':1.5,
            'materials': [self.dont_collide]})
        self.r2.connectattr('position', p2,'position')
        
        self.r3 = ba.newnode('region',attrs={'position': (-4.5,2,-5),'scale': [3,3,3],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        p3 = ba.newnode('prop', delegate=self, attrs={
            'position': (0,6.5,-8.0),
            'velocity': (2,0,0),
            'color_texture': ba.gettexture('powerupLandMines'),
            'model': ba.getmodel('powerupSimple'),
     
            'model_scale':5.3,
            'body': 'puck',
            'body_scale':1,
            'density':1,
            'gravity_scale':0.2,
            'reflection': 'soft',
            'reflection_scale': [0.0],
            'shadow_size': 0.0,
            'max_speed':1.5,
            'materials': [self.dont_collide]})
        self.r3.connectattr('position', p3,'position')
        
        self.r4 = ba.newnode('region',attrs={'position': (4.5,5,-5),'scale': [3,3,3],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
 
        
        p4 = ba.newnode('prop', delegate=self, attrs={
            'position': (0,6.5,-8.0),
            'velocity': (2,0,0),
            'color_texture': ba.gettexture('powerupLandMines'),
            'model': ba.getmodel('powerupSimple'),
            'model_scale':5.3,
            'body': 'puck',
            'body_scale':1,
            'density':1,
            'gravity_scale':0.2,
            'reflection': 'soft',
            'reflection_scale': [0.0],
            'shadow_size': 0.0,
            'max_speed':1.5,
            'materials': [self.dont_collide]})
        self.r4.connectattr('position', p4,'position')
        
        
        ba.animate_array(self.r3,'position',3,{0:(-5,2,-5),1:(-5,2,-5),4:(-5,5,-5),5:(-5,5,-5),8:(-5,2,-5)},loop=True)
        ba.animate_array(self.r4,'position',3,{0:(5,5,-5),1:(5,5,-5),4:(5,2,-5),5:(5,2,-5),8:(5,5,-5)},loop=True)
                   
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.1, 1.0)
        gnode.ambient_color = (1.1, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)          
        FadeEfect(gnode.tint)
        Credits()
#################################
class spaz_defs():
    points = {}
    boxes = {}
    points['flag_default'] = (0.3, 4.2, -3)
    points['flag1'] = (-7.7,5.7,-10) + (1.0,0.1,1.0)
    points['flag2'] = (8.4,5.7,3.5) + (1.0,0.1,1.0)
    points['flag3'] = ( 8.5,5.7,-9.7) + (1.0,0.1,1.0)
    points['flag4'] = (-7.5,5.7,3.1) + (1.0,0.1,1.0)
    points['flag5'] = (0.3,4.3,-2.9) + (1.0,0.1,1.0)
    
    
    points['spawn_by_flag1'] = (-7.7,5.7,-10) + (1.0,0.1,1.0)
    points['spawn_by_flag2'] = (8.4,5.7,3.5) + (1.0,0.1,1.0)
    points['spawn_by_flag3'] = ( 8.5,5.7,-9.7) + (1.0,0.1,1.0)
    points['spawn_by_flag4'] = (-7.5,5.7,3.1) + (1.0,0.1,1.0)
    points['spawn_by_flag5'] = (0.3,4.3,-2.9) + (1.0,0.1,1.0)
    
    boxes['area_of_interest_bounds'] = (0, 5, -1) + (0.0, 0.0, 0.0) + (40, 20, 25)
    boxes['map_bounds'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (30, 15, 30)
    
    points['ffa_spawn1'] = (-5,4.2,-3) + (0.5,0.1,1.5)
    points['ffa_spawn2'] = (5.2,4.2,-3) + (0.5,0.1,1.5)
    points['ffa_spawn3'] = (8.40,5.77,2.77)
    points['ffa_spawn4'] = (8.40,5.77,-8.04)
    points['ffa_spawn5'] = (-7.68,5.77,-8.94)
    points['ffa_spawn6'] = (-7.68,5.77, 2.80)
    
    
    points['spawn1'] = (-7.7,5.7,-9) + (1.7,0.1,1.2)
    points['spawn2'] = (8.4,5.7,2.5) + (1.7,0.1,1.2)
    
    points['powerup_spawn1'] = (-3.8,4.5,-3)
    points['powerup_spawn2'] = (4,4.5,-3)
    points['powerup_spawn3'] = (-5.7,6.5,-10.3)
    points['powerup_spawn4'] = (6.6,6.5,3.5) 
    points['powerup_spawn5'] = (-9.5,6.5,-10.3)
    points['powerup_spawn6'] = (10.5,6.5,3.5)
    
    points['powerup_spawn7'] = (-5.7,6.5,3.5)
    points['powerup_spawn8'] = (6.6,6.5,-10.3) 
    points['powerup_spawn9'] = (-9.5,6.5,3.5)
    points['powerup_spawn10'] = (10.5,6.5,-10.3)
    
    points['shadow_lower_bottom'] = (0, 4.0, 2)
    points['shadow_lower_top'] = (0, 5, 2)
    points['shadow_upper_bottom'] = (0, 6, 2)
    points['shadow_upper_top'] = (0, 7, 2)

class SpazMap(ba.Map):
    defs = spaz_defs()
    name = 'Skull Temple'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee','team_flag', 'keep_away', 'conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bonesColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'bgtex': ba.gettexture('menuBG'),
            'bgmodel': ba.getmodel('thePadBG')
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self._map_tex2 = ba.gettexture('tnt')
        self._map_model = ba.getmodel('powerupSimple')
        
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self.ice_material = ba.Material()
        self.ice_material.add_actions(actions=(('modify_part_collision','friction',0.01)))
        
        self.node = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False, 
                'background': True,
                'color':(0,1,1),
                'color_texture': self.preloaddata['bgtex']
            })
        ########Rampage###
        pos = (0,4,-3)
        pos_extra = 6.5
        self.r4 = ba.newnode('region',attrs={'position': (0,3.57,-3),'scale': [16,1,4.3],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ####
        ba.newnode('region',attrs={'position': (-7.8,pos[1]+0.95,2.6),'scale': [4.75,1.0,3.4],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (-7.7,pos[1]+0.95,-2.6*3.5),'scale': [4.75,1.0,3.4],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (-7.725,pos[1]+0.95,-3.2),'scale': [1.35,1.0,8.2],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ####
        ba.newnode('region',attrs={'position': (7.8+0.8,pos[1]+0.95,2.6),'scale': [4.75,1.0,3.4],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (7.7+0.8,pos[1]+0.95,-2.6*3.5),'scale': [4.75,1.0,3.4],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (7.725+0.8,pos[1]+0.95,-3.2),'scale': [1.35,1.0,8.2],'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ####
        for x in [-6.5,7.3]:
            m_pos = (x,pos[1]+0.3,-3.5)
            ba.newnode('region',attrs={'position': m_pos,'scale': (1.0,1.0,1.0),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
            ba.newnode('prop',
                    attrs={'body': 'puck','position': m_pos, 'model': self._map_model, 'model_scale': 1.635, 'body_scale': 0.0, 'shadow_size': 0.0, 'gravity_scale':0.0, 'damping':0, 'color_texture': self._map_tex2, 'reflection': 'soft', 'reflection_scale': [0.0], 'is_area_of_interest': False, 'materials': [self.dont_collide]})
            m_pos = (x,pos[1]+0.3,-2.5)
            ba.newnode('region',attrs={'position': m_pos,'scale': (1.0,1.0,1.0),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
            ba.newnode('prop',
                    attrs={'body': 'puck','position': m_pos, 'model': self._map_model, 'model_scale': 1.635, 'body_scale': 0.0, 'shadow_size': 0.0, 'gravity_scale':0.0, 'damping':0, 'color_texture': self._map_tex2, 'reflection': 'soft', 'reflection_scale': [0.0], 'is_area_of_interest': False, 'materials': [self.dont_collide]})
            
        ####################################
        #Rampage
        a = ba.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': (0.4,2,0.5),
                'highlight': (0.4,2,0.5),
                'color_texture': ba.gettexture('rampageLevelColor'),
                'color_mask_texture': ba.gettexture('bonesColorMask'),
                'head_model': ba.getmodel('rampageLevel'),
                'style':'bones',
                'materials': [self.dont_collide],
                'roller_materials': [self.dont_collide],
                'extras_material': [self.dont_collide],
                'punch_materials': [self.dont_collide],
                'pickup_materials': [self.dont_collide],
            })
        a.is_area_of_interest = False
        #
        b = ba.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': (1,1,1),
                'highlight': (1,1,1),
                'color_texture': ba.gettexture('rampageLevelColor'),
                'color_mask_texture': ba.gettexture('bonesColorMask'),
                'head_model': ba.getmodel('rampageLevelBottom'),
                'style':'bones',
                'materials': [self.dont_collide],
                'roller_materials': [self.dont_collide],
                'extras_material': [self.dont_collide],
                'punch_materials': [self.dont_collide],
                'pickup_materials': [self.dont_collide],
            })
        b.is_area_of_interest = False
        ###Bridgit
        c = ba.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': (0,2,3),
                'highlight': (0,2,3),
                'color_texture': ba.gettexture('bridgitLevelColor'),
                'color_mask_texture': ba.gettexture('bonesColorMask'),
                'head_model': ba.getmodel('bridgitLevelTop'),
                'style':'bones',
                'materials': [self.dont_collide],
                'roller_materials': [self.dont_collide],
                'extras_material': [self.dont_collide],
                'punch_materials': [self.dont_collide],
                'pickup_materials': [self.dont_collide],
            })
        c.is_area_of_interest = False
        d = ba.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': (0,2,3),
                'highlight': (0,2,3),
                'color_texture': ba.gettexture('bridgitLevelColor'),
                'color_mask_texture': ba.gettexture('bonesColorMask'),
                'head_model': ba.getmodel('bridgitLevelTop'),
                'style':'bones',
                'materials': [self.dont_collide],
                'roller_materials': [self.dont_collide],
                'extras_material': [self.dont_collide],
                'punch_materials': [self.dont_collide],
                'pickup_materials': [self.dont_collide],
            })
        d.is_area_of_interest = False
        
        def p():
            if a:
                a.handlemessage('stand', pos[0],pos[1]-pos_extra,pos[2]+4.25,0)
                a.handlemessage('knockout', 500.0)
            if b:
                b.handlemessage('stand', pos[0],pos[1]-pos_extra,pos[2]+4.25,0)
                b.handlemessage('knockout', 500.0)
            if c:
                c.handlemessage('stand', pos[0]-6.2,pos[1]-pos_extra+2.7,pos[2]+4.25-4.8,90)
                c.handlemessage('knockout', 500.0)
            if d:
                d.handlemessage('stand', pos[0]+7,pos[1]-pos_extra+2.75,pos[2]+4.25-3.7-0.5,-90)
                d.handlemessage('knockout', 500.0)
        ba.timer(0.001,p,repeat=True)
       # print(str(dir(a)))
                #Meme
        text = ba.newnode('text',
                              attrs={'position':(0,21,0),
                                     'text':'GOATSTIAN GOATSTIAN GOATSTIAN\nGOATSTIAN GOATSTIAN GOATSTIAN ',
                                     'in_world':True,
                                     'shadow':1.5,
                                     'flatness':0.7,
                                     'color':(1,1,1.2),
                                     'opacity':1.0,
                                     'scale':0.023,
                                     'h_align':'center'}) 
        CustomModel(position=(0.4, 1.5, -1.4), model = 'bonesHead', texture = 'bonesColor', scale = 6.7) 
        
        ####################################
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.3, 1.2, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5
        FadeEfect(gnode.tint)
        Credits()     
        
#Rombo
class ram_defs():
    points = {}
    boxes = {}
    points['flag_default'] = (0.0, 4.2, -5)
    points['flag1'] = (4.5,4.2,-4) + (0.5,0.1,1.5)
    points['flag2'] = (-4.5,4.2,-4) + (0.5,0.1,1.5)
    
    boxes['area_of_interest_bounds'] = (0, 5, -1) + (0.0, 0.0, 0.0) + (40, 20, 25)
    boxes['map_bounds'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (30, 15, 30)
    
    points['ffa_spawn1'] = (-4,4.2,-5) + (0.5,0.1,1.5)
    points['ffa_spawn2'] = (4.2,4.2,-5) + (0.5,0.1,1.5)
    points['ffa_spawn3'] = (0,4.2,-10) + (0.5,0.1,1.5)
    points['ffa_spawn4'] = (0,4.2,1) + (0.5,0.1,1.5)    
    
    points['spawn1'] = (4.2,4.2,-4) + (0.5,0.1,1.5)
    points['spawn2'] = (-4,4.2,-4) + (0.5,0.1,1.5)
    
    points['powerup_spawn1'] = (3,4.5,-5)
    points['powerup_spawn2'] = (-3,4.5,-5)
    
    points['shadow_lower_bottom'] = (0, 4.0, 2)
    points['shadow_lower_top'] = (0, 5, 2)
    points['shadow_upper_bottom'] = (0, 6, 2)
    points['shadow_upper_top'] = (0, 7, 2)        
        
###################
class RampageMod(ba.Map):
    """Wee little map with ramps on the sides."""
    defs = ram_defs()
    name = 'Botton Rampage'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'rampageLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'model': ba.getmodel('rampageLevel'),
            'bottom_model': ba.getmodel('rampageLevelBottom'),
            'collide_model': ba.getcollidemodel('rampageLevelCollide'),
            'tex': ba.gettexture('rampageLevelColor'),
            'bgtex': ba.gettexture('shrapnel1Color'),
            'bgtex2': ba.gettexture('shrapnel1Color'),
            'bgmodel': ba.getmodel('rampageBG'),
            'bgmodel2': ba.getmodel('rampageBG2'),
            'vr_fill_model': ba.getmodel('rampageVRFill'),
            'railing_collide_model': ba.getcollidemodel('rampageBumper')
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 0, 2))
        shared = SharedObjects.get()
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        
        # self.node = ba.newnode(
            # 'terrain',
            # delegate=self,
            # attrs={
                # 'collide_model': self.preloaddata['collide_model'],
                # 'model': self.preloaddata['model'],
                # 'color_texture': self.preloaddata['tex'],
                # 'materials': [shared.footing_material]
            # })

        # self.bottom = ba.newnode('terrain',
                                 # attrs={
                                     # 'model': self.preloaddata['bottom_model'],
                                     # 'lighting': False,
                                     # 'color_texture': self.preloaddata['tex']
                                 # })
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
        # self.railing = ba.newnode(
            # 'terrain',
            # attrs={
                # 'collide_model': self.preloaddata['railing_collide_model'],
                # 'materials': [shared.railing_material],
                # 'bumper': True
            # })
            
        ba.newnode('region',attrs={'position': (0,3,-4.5),'scale': (2.7,2,16.7),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (2.0,3,-4.6),'scale': (1.3,2,12.9),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (-2.0,3,-4.6),'scale': (1.3,2,12.9),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (3.3,3,-4.5),'scale': (1.3,2,9.5),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (-3.3,3,-4.5),'scale': (1.3,2,9.5),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (4.7,3,-4.4),'scale': (1.3,2,6.4),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (-4.7,3,-4.8),'scale': (1.3,2,6.3),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (6.2,3,-4.5),'scale': (1.3,2,3.2),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        ba.newnode('region',attrs={'position': (-6.2,3,-4.7),'scale': (1.3,2,3.2),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        self.zone = ba.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(0,3.93,-4.65),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[14,0.1,2.9]})
        ba.animate_array(self.zone, 'color', 3,{0:(0,0,0), 0.0:(0,0,0), 0.50:(0,0,0), 0.55:(1,1,1), 0.6:(0,0,0), 0.65:(1,1,1), 0.7:(0,0,0),
                                                0.75:(1,1,1), 0.8:(0,0,0), 0.85:(1,1,1), 0.9:(0,0,0), 0.95:(1.2,0.0,0.0)},False)    
            
        
        # r.connectattr('position',l,'position')
        # r.connectattr('scale',l,'size')
            
        CustomModelR3(position=(4.95,6,-4.3), model = 'rampageLevelBottom', texture= 'rampageLevelColor', rotate='right')
        CustomModelR3(position=(-4.95,6,-5), model = 'rampageLevelBottom', texture= 'rampageLevelColor', rotate='left')
            
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.2,1.2,1.2)
        gnode.ambient_color = (1.15,1.25,1.6)
        gnode.vignette_outer = (0.3,-0.1,0.5)
        gnode.vignette_inner = (0.93,0.93,0.95)
        FadeEfect(gnode.tint)
        Credits()

    def is_point_near_edge(self,
                           point: ba.Vec3,
                           running: bool = False) -> bool:
        box_position = self.defs.boxes['edge_box'][0:3]
        box_scale = self.defs.boxes['edge_box'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        return xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5        
        
#########################TESTTTTTT###
class collosal_bridgit():
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (-0.2457963347*2.5+1, 3.828181068*2.5-28,
                                        -1.528362695*2.5-25) + (0.0, 0.0, 0.0) + (
                                            19.14849937*2.0, 7.312788846*1.25, 8.436232726*1.25)
    points['ffa_spawn1'] = (-5.869295124*2.5+1, 3.715437928*2.5-46,
                            -1.617274877*2.5-50) + (0.9410329222*2.5, 1.0, 1.818908238*2.5)
    points['ffa_spawn2'] = (5.160809653*2.5+1, 3.761793434*2.5-46,
                            -1.443012115*2.5-50) + (0.7729807005*2.5, 1.0, 1.818908238*2.5)
    points['ffa_spawn3'] = (-0.4266381164*2.5+1, 3.761793434*2.5-46,
                            -1.555562653*2.5-50) + (4.034151421*2.5, 1.0, 0.2731725824*2.5)
    points['flag1'] = (-7.354603923*2.5+1, 3.770769731*2.5-46, -1.617274877*2.5-50)
    points['flag2'] = (6.885846926*2.5+1, 3.770685211*2.5-46, -1.443012115*2.5-50)
    points['flag_default'] = (-0.2227795102*2.5+1, 3.802429326*2.5-46, -1.562586233*2.5-50)
    boxes['map_bounds'] = (-0.1916036665*2.5+1, 7.481446847*2.5-46, -1.311948055*2.5-50) + (
        0.0, 0.0, 0.0) + (27.41996888*2.5, 18.47258973*2.5, 19.52220249*2.5)
    points['powerup_spawn1'] = (6.82849491*2.5+1, 4.658454461*2.5-46, 0.1938139802*2.5-50)
    points['powerup_spawn2'] = (-7.253381358*2.5+1, 4.728692078*2.5-46, 0.252121017*2.5-50)
    points['powerup_spawn3'] = (6.82849491*2.5+1, 4.658454461*2.5-46, -3.461765427*2.5-50)
    points['powerup_spawn4'] = (-7.253381358*2.5+1, 4.728692078*2.5-46, -3.40345839*2.5-50)
    points['shadow_lower_bottom'] = (-0.2227795102, 2.83188898, 2.680075641)
    points['shadow_lower_top'] = (-0.2227795102, 3.498267184, 2.680075641)
    points['shadow_upper_bottom'] = (-0.2227795102, 6.305086402, 2.680075641)
    points['shadow_upper_top'] = (-0.2227795102, 9.470923628, 2.680075641)
    points['spawn1'] = (-5.869295124*2.5+1, 3.715437928*2.5-46,
                        -1.617274877*2.5-50) + (0.9410329222*2.5, 1.0, 1.818908238*2.5)
    points['spawn2'] = (5.160809653*2.5+1, 3.761793434*2.5-46,
                        -1.443012115*2.5-50) + (0.7729807005*2.5, 1.0, 1.818908238*2.5)

class BridgitC(ba.Map):
    """Map with a narrow bridge in the middle."""
    defs = collosal_bridgit()

    name = 'Collosal Bridgit'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        # print('getting playtypes', cls._getdata()['play_types'])
        return ['melee', 'team_flag', 'keep_away']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bridgitLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
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
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        
    
        m = 10
        CustomModel(position=(0+1, -4.6*m-0.2, -5*m), model = 'bridgitLevelTop', texture = 'bridgitLevelColor', scale = 1.0*2.5)
        CustomModel(position=(0+1, -4.6*m-0.2, -5*m), model = 'bridgitLevelBottom', texture = 'bridgitLevelColor', scale = 1.0*2.5)
        
        CustomModel(position=(0, -4.6*m-0.2, -5*m), model = 'natureBackground', texture = 'natureBackgroundColor', scale = 1.0*2.5)
        
        
        ###NEW###
        pos = ((0.35-0.75)*2.5+1,3.1*2.5-46,-1.5*2.5-50)
        ba.newnode('region',attrs={'position': pos,'scale': (8.25*2.5,1.2*2.5,1.37*2.5),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        # l = ba.newnode('locator',attrs={'shape':'box','position':pos,
            # 'color':(1,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':[8.25*2.5,1.2*2.5,1.37*2.5]})
            
        pos = (-6.15*2.5+1,2.7*2.5-46,-1.6*2.5-50)
        ba.newnode('region',attrs={'position': pos,'scale': (3.4*2.5,2*2.5,4.75*2.5),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        # l = ba.newnode('locator',attrs={'shape':'box','position':pos,
            # 'color':(1,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':[3.4*2.5,2*2.5,4.75*2.5]})
        
        pos = (5.5*2.5+1,2.7*2.5-46,-1.5*2.5-50)
        ba.newnode('region',attrs={'position': pos,'scale': (3.5*2.5,2*2.5,5*2.5),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        # l = ba.newnode('locator',attrs={'shape':'box','position':pos,
            # 'color':(1,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':[3.5*2.5,2*2.5,5*2.5]})
    
                                
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.3)
        gnode.ambient_color = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)    
        FadeEfect(gnode.tint)
        Credits() 

#########################TESTTTTTT###
class tcrus():
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (0.35, 5.61, -2.06) + (0.0, 0.0, 0.0) + (19.90, 10.34, 8.16)
   # boxes['area_of_interest_bounds'] = (0, 10, -14) + (0.0, 0.0, 0.0) + (40, 20, 25)    
    boxes['edge_box'] = (0.3544110667, 5.438284793, -4.100357672) + (
    0.0, 0.0, 0.0) + (12.57718032, 4.645176013, 3.605557343)
    points['ffa_spawn1'] = (0.50, 5.05, -5.79) + (6.62, 1.0, 0.34)
    points['ffa_spawn2'] = (0.50, 5.05, -2.43) + (6.62, 1.0, 0.34)
    points['ffa_spawn3'] = (0.20, 5.49, 1.51)
    points['ffa_spawn4'] = (0.20, 5.49, -9.51)
    points['ffa_spawn5'] = (4.80, 5.49, -9.56)
    points['ffa_spawn6'] = (-4.50, 5.49, 1.25)
    points['ffa_spawn7'] = (3.50, 5.49, 1.25)
    
                        
    points['flag1'] = (-5.885814199, 5.112162255, -4.251754911)
    points['flag2'] = (6.700855451, 5.10270501, -4.259912982)
    points['flag3'] = (-4.2, 5.49, -10.41)
    points['flag4'] = (4.92, 5.49, -9.76)
    points['flag5'] = (4.76, 5.49, 1.44)
    points['flag6'] = (-4.44, 5.49, 1.68)
    points['flag_default'] = (0.3196701116, 5.49, -4.292515158)
    
    points['spawn_by_flag1'] = (-5.885814199, 5.112162255, -4.251754911)
    points['spawn_by_flag2'] = (6.700855451, 5.10270501, -4.259912982)
    points['spawn_by_flag3'] = (-4.2, 5.49, -10.41)
    points['spawn_by_flag4'] = (4.92, 5.49, -9.76)
    points['spawn_by_flag5'] = (4.76, 5.49, 1.44)
    points['spawn_by_flag6'] = (-4.44, 5.49, 1.68)
    
    boxes['map_bounds'] = (0.45, 4.89, -0.54) + (0.0, 0.0, 0.0) + (23.54, 14.19, 23.08)
    
    points['powerup_spawn1'] = (-2.64, 6.42, -4.22)
    points['powerup_spawn2'] =  (3.54, 6.54, -4.19)
    points['powerup_spawn3'] =  (-2.03, 5.49, -10.15)
    points['powerup_spawn4'] =  (2.39, 5.49, -10.1)
    points['powerup_spawn5'] =  (2.39, 5.49, 1.6)
    points['powerup_spawn6'] =  (-1.94, 5.54, 1.70)
    
    points['shadow_lower_bottom'] = (5.580073911, 3.136491026, 5.341226521)
    points['shadow_lower_top'] = (5.580073911, 4.321758709, 5.341226521)
    points['shadow_upper_bottom'] = (5.274539479, 8.425373402, 5.341226521)
    points['shadow_upper_top'] = (5.274539479, 11.93458162, 5.341226521)
    points['spawn1'] = (-4.75, 5.05, -4.24) + (0.91, 1.0, 0.51)
    points['spawn2'] = (5.83, 5.05,-4.25) + (0.91, 1.0, 0.51)
  #  points['spawn2'] = (5.83, 5.05,-4.25)

class thec(ba.Map):
    """Wee little map with ramps on the sides."""
    defs = tcrus()
    name = 'The Crusade'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'crossOut'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'model': ba.getmodel('rampageLevel'),
            'bottom_model': ba.getmodel('rampageLevelBottom'),
            'collide_model': ba.getcollidemodel('rampageLevelCollide'),
            'tex': ba.gettexture('rampageLevelColor'),
            'bgtex': ba.gettexture('shrapnel1Color'),
            'bgtex2': ba.gettexture('shrapnel1Color'),
            'bgmodel': ba.getmodel('rampageBG'),
            'bgmodel2': ba.getmodel('rampageBG2'),
            'vr_fill_model': ba.getmodel('rampageVRFill'),
            'railing_collide_model': ba.getcollidemodel('rampageBumper')
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 0, 2))
        shared = SharedObjects.get()
        
        self._collide_custom=ba.Material()
        self.dont_collide=ba.Material()
        
        self._collide_custom.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self._collide_custom.add_actions(conditions=('they_have_material', self.dont_collide), actions=(('modify_part_collision', 'collide', True)))
            
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collide_model': self.preloaddata['collide_model'],
                'model': self.preloaddata['model'],
                'color_texture': self.preloaddata['tex'],
                'color':(0.9,0.4,1),
                'materials': [shared.footing_material]
            })
        self.bottom = ba.newnode('terrain',
                                 attrs={
                                     'model': self.preloaddata['bottom_model'],
                                     'lighting': False,
                                     'color':(0,1.2,0),
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
                       'color':(0,0,1),
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
        
        #iz
        self.r1 = ba.newnode('region',attrs={'position': (-4.35,4.6, -4.3),'scale': (1.47,1.2,8.7),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        #centro
        self.r1 = ba.newnode('region',attrs={'position': (0.25,4.6, -4.3),'scale': (1.47,1.2,8.7),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        #der
        self.r1 = ba.newnode('region',attrs={'position': (4.65,4.6, -4.3),'scale': (1.47,1.2,8.7),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        self.r1 = ba.newnode('region',attrs={'position': (0.25,4.6, -10.2),'scale': (14.0,1.2,3.4),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        self.r1 = ba.newnode('region',attrs={'position': (0.25,4.6, 1.5),'scale': (14.0,1.2,3.6),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        
        
        CustomModelR2(position=(-5.80, 1.6,-4.1), model = 'bridgitLevelTop', texture = 'bridgitLevelColor', scale = 1, rotate='left')        
        CustomModelR2(position=(-1.25, 1.58,-4.1), model = 'bridgitLevelTop', texture = 'bridgitLevelColor', scale = 1, rotate='left')
        CustomModelR2(position=(3.20, 1.6,-4.1), model = 'bridgitLevelTop', texture = 'bridgitLevelColor', scale = 1, rotate='left')          
        text = ba.newnode('text',
                              attrs={'position':(0,21,0),
                                     'text':'Tz: Se me paso por la mente crear esto\n por mas raro que haya sido \n el resultado jaja',
                                     'in_world':True,
                                     'shadow':1.5,
                                     'flatness':0.7,
                                     'color':(1,1,1.2),
                                     'opacity':1.0,
                                     'scale':0.023,
                                     'h_align':'center'}) 
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.2,1.2,1.2)
        gnode.ambient_color = (1.15,1.25,1.6)
        gnode.vignette_outer = (0.4,-0.4,0.4)
        gnode.vignette_inner = (0.93,0.93,0.95)
        FadeEfect(gnode.tint)
        Credits()
        
                
class collosal_monkey():
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (-0.2457963347*2.5+1, 1.028181068*2.5-28,-4.98362695*2.5-25) + (0.0, 0.0, 0.0) + (19.14849937*2.0, 0.312788846*1.25, 8.436232726*1.25)                                          
    boxes['map_bounds'] = (-0.1916036665*2.5+1, 7.481446847*2.5-46, -1.311948055*2.5-50) + (0.0, 0.0, 0.0) + (27.41996888*2.5, 18.47258973*2.5, 19.52220249*2.5)        
    points['ffa_spawn1'] = (-3.40, -37.65, -55.85)
    points['ffa_spawn2'] = (-3.40, -37.65, -64.85)
    points['ffa_spawn3'] = (12.20, -37.65, -57.05) 
    points['ffa_spawn4'] = (-18.56, -37.65, -56.72)
    points['ffa_spawn5'] = (-11.66, -37.65, -44.24)
    points['ffa_spawn6'] = (5.66, -37.65, -44.24)
    points['ffa_spawn7'] = (7.66, -37.65, -66.54)
    points['ffa_spawn8'] = (-14.66, -37.65, -66.54)
    points['spawn1'] = (-8.026373566*2.5+1, 3.349937889*2.5-46,
                    -2.542088202*2.5-50) + (0.9450583628*2.5, 0.9450583628, 1.181509268*2.5)
    points['spawn2'] = (4.73470012*2.5+1, 3.308679998*2.5-46, -2.757871588*2.5-50) + (0.9335931003*2.5,
                                                              1.0, 1.217352295*2.5)                            
        
    points['flag1'] = (-8.968414135*2.5+1, 3.35709348*2.5-46, -2.804123917*2.5-50)
    points['flag2'] = (5.945128279*2.5+1, 3.354825248*2.5-46, -2.663635497*2.5-50)
    points['flag3'] = (-1.688166134*2.5+1, 3.392387172*2.5-46, -2.238613943*2.5-50)   
    points['flag4'] = (-11.86, 3.392387172*2.5-46, -49.41)
    points['flag5'] = ( 5.4, 3.392387172*2.5-46, -49.47)
    points['flag6'] = (-3.2, 3.392387172*2.5-46, -65.52)
    
    points['spawn_by_flag1'] = (-8.968414135*2.5+1, 3.35709348*2.5-46, -2.804123917*2.5-50)
    points['spawn_by_flag2'] = (5.945128279*2.5+1, 3.354825248*2.5-46, -2.663635497*2.5-50)
    points['spawn_by_flag3'] = (-1.688166134*2.5+1, 3.392387172*2.5-46, -2.238613943*2.5-50)   
    points['spawn_by_flag4'] = (-11.86, 3.392387172*2.5-46, -49.41)
    points['spawn_by_flag5'] = ( 5.4, 3.392387172*2.5-46, -49.47)
    points['spawn_by_flag6'] = (-3.2, 3.392387172*2.5-46, -65.52)
    
    points['flag_default'] = (-1.688166134*2.5+1, 3.392387172*2.5-46, -2.238613943*2.5-50)    
        
    points['powerup_spawn1'] = (-18.50, -37.55, -58.50)
    points['powerup_spawn2'] = (-16.50, -37.55, -66.40)
    points['powerup_spawn3'] = ( 9.3, -37.55, -66.50)
    points['powerup_spawn4'] = ( 13.0, -37.55, -59.22)
    points['powerup_spawn5'] = ( 5.0, -37.55, -43.32)
    points['powerup_spawn6'] = (-12.0, -37.55, -43.22)
    
    points['shadow_lower_bottom'] = (-0.2227795102, 2.83188898, 2.680075641)
    points['shadow_lower_top'] = (-0.2227795102, 3.498267184, 2.680075641)
    points['shadow_upper_bottom'] = (-0.2227795102, 6.305086402, 2.680075641)
    points['shadow_upper_top'] = (-0.2227795102, 9.470923628, 2.680075641)
      

class collosal_monkey(ba.Map):
    """Map with a narrow bridge in the middle."""
    defs = collosal_monkey()

    name = 'Collosal Monkey'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        # print('getting playtypes', cls._getdata()['play_types'])
        return ['melee', 'team_flag', 'keep_away', 'conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'monkeyFaceLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'el_flipante_mono_que_es_el_mapa_de_cara_de_mono_pero_mas_grande': ba.getmodel('monkeyFaceLevel'),
            'bg_material': ba.Material()
        }
        data['bg_material'].add_actions(actions=('modify_part_collision',
                                                 'friction', 10.0))
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        
        m = 10
        CustomModel(position=(0+1, -4.6*m-0.2, -5*m), model = 'monkeyFaceLevel', texture = 'monkeyFaceLevelColor', scale = 1.0*2.5)
        CustomModel(position=(0+1, -4.6*m-0.2, -5*m), model = 'monkeyFaceLevelBottom', texture = 'monkeyFaceLevelColor', scale = 1.0*2.5)
        
        CustomModel(position=(0, -4.6*m-0.2, -5*m), model = 'natureBackground', texture = 'natureBackgroundColor', scale = 1.0*2.5)
        
        self.r1 = ba.newnode('region',attrs={'position': (-18.10, -39.9, -56.37),'scale': (9.00, 3.90, 8.10),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        
        self.r1 = ba.newnode('region',attrs={'position': (11.8, -39.9, -57.00),'scale': (9.75, 3.90, 7.85),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        self.r1 = ba.newnode('region',attrs={'position': (-3.0,-39.9, -55.30),'scale': (21.55, 3.90, 4.4),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        self.r1 = ba.newnode('region',attrs={'position': (-3.39, -39.9, -60.30),'scale': (6.2, 3.90, 15.37),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        
        self.r1 = ba.newnode('region',attrs={'position': (-3.39, -39.9, -66.35),'scale': (27.25, 3.90, 3.085),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        
        self.r1 = ba.newnode('region',attrs={'position': (-3.39, -39.9, -44.0),'scale': (21.0, 3.90, 4.2),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        
        self.r1 = ba.newnode('region',attrs={'position': (5.39, -39.9, -50.30),'scale': (3.3, 3.90, 9.37),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        
        self.r1 = ba.newnode('region',attrs={'position': (-11.93, -39.9, -50.30),'scale': (3.5, 3.90, 9.6),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        
        self.r1 = ba.newnode('region',attrs={'position': (-15.39, -39.9, -60.30),'scale': (3.5, 3.90, 9.4),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
                             
        self.r1 = ba.newnode('region',attrs={'position': (8.6, -39.9, -60.30),'scale': (3.44, 3.90, 9.4),
                             'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
        text = ba.newnode('text',
                              attrs={'position':(0,21,0),
                                     'text':'El Gran mono',
                                     'in_world':True,
                                     'shadow':1.5,
                                     'flatness':0.7,
                                     'color':(1,1,1.2),
                                     'opacity':1.0,
                                     'scale':0.023,
                                     'h_align':'center'})  
                                
        gnode = ba.getactivity().globalsnode
        gnode.tint           = (1.1, 1.2, 1.3)
        gnode.ambient_color  = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)    
        FadeEfect(gnode.tint)
        Credits()                 
        
# Tower Zoe by Zacker con ayudita de sebastian :v        
# Tower Zoe by Zacker con ayudita de sebastian :v        
class bazinga_defs():
    points = {}
    boxes = {}
    points['flag_default'] = (0.52, 7.93, -4.09)
    points['flag1'] = (8.2,7.93,-2.53)
    points['flag2'] = (-7.5,7.93,-6)
    
    boxes['area_of_interest_bounds'] = (0, 10, -14) + (0.0, 0.0, 0.0) + (40, 20, 25)
    boxes['map_bounds'] = (0, 12.5-5, 0) + (0.0, 0.0, 0.0) + (30, 15, 30)
    
    points['ffa_spawn1'] = (-7.2,7.93,-6)  
    points['ffa_spawn2'] = (8.2,7.93,-2.53) 
    points['ffa_spawn3'] = (1.54,7.93,-2.48) 
    points['ffa_spawn4'] = (-0.24,7.93,-5.77)   
    
    points['spawn1'] = (8.2,7.93,-2.53) 
    points['spawn2'] = (-7.2,7.93,-6)
    
    points['powerup_spawn1'] = (8.99,7.97,-3.10)
    points['powerup_spawn2'] = (0.16, 7.94, -1.79)
    points['powerup_spawn3'] = (1.2, 7.94, -6.79)
    points['powerup_spawn4'] = (-8.4,8.07,-3.10)
    
    
    points['shadow_lower_bottom'] = (0, 4.0, 2)
    points['shadow_lower_top'] = (0, 5, 2)
    points['shadow_upper_bottom'] = (0, 6, 2)
    points['shadow_upper_top'] = (0, 7, 2)        
        
class tZoe(ba.Map):
    """Wide stepped map good for CTF or Assault."""
    defs = bazinga_defs()
    name = 'Tower Zoe'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'zoeIcon'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'model': ba.getmodel('stepRightUpLevel'),
            'model_bottom': ba.getmodel('stepRightUpLevelBottom'),
            'collide_model': ba.getcollidemodel('stepRightUpLevelCollide'),
            'tex': ba.gettexture('stepRightUpLevelColor'),
            'bgtex': ba.gettexture('shrapnel1Color'),
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
            

        self._collide_custom=ba.Material()
        self.dont_collide=ba.Material()
        self._death=ba.Material()
        
        self._death.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', True),('modify_part_collision', 'physical', False)))
        
        self._collide_custom.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        self._collide_custom.add_actions(conditions=('they_have_material', self.dont_collide), actions=(('modify_part_collision', 'collide', True)))
            
        self._collide_with_player=ba.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=ba.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
            
        self._map_model = ba.getmodel('image1x1')
        self._map_tex = ba.gettexture('powerupIceBombs')
        self._map_tex2 = ba.gettexture('shrapnel1Color')             
            
            
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
        #death region
        ba.newnode('region',attrs={'position': (0, 6.5, -5),'scale': (30,0.1,30),'type': 'box','materials': (shared.death_material,self._death)})
  
        self.r1 = ba.newnode('region',attrs={'position': (0.5,7.18,-4.3),'scale': (2.3,0.9,6.3),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        self.r1 = ba.newnode('region',attrs={'position': (8.07,7.18,-2.58),'scale': (2.27,0.90,3.27),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
    
        self.r1 = ba.newnode('region',attrs={'position': (-7.07,7.18, -6),'scale': (2.27,0.90,3.10),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
 
        self.r1 = ba.newnode('region',attrs={'position': (-3.4,7.18, -5.86),'scale': (6.0,0.90,1),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})

        self.r1 = ba.newnode('region',attrs={'position': (4.4,7.18, -2.59),'scale': (6.0,0.90,1),'type': 'box','materials': (self._collide_with_player, shared.footing_material)})
          

        posS = [(0.0,6.5,-7)]
        for m_pos in posS:
            self.mv_center = ba.newnode('prop',
                    attrs={'body': 'puck',
                           'position': m_pos,
                           'model': self._map_model,
                           'model_scale': 120,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex2,
                           'reflection': 'soft',
                           'reflection_scale': [0],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})         
            
        CustomModel(position=(-3.1, 5.135,-4.9), model = 'bridgitLevelTop', texture = 'bridgitLevelColor', scale = 0.65)     
        CustomModel(position=(4.5, 5.135,-1.6), model = 'bridgitLevelTop', texture = 'bridgitLevelColor', scale = 0.65) 
        CustomModel(position=(2.4, 2.12,-6.6), model = 'zigZagLevelBottom', texture = 'zigZagLevelColor', scale = 0.8)       
        CustomModel(position=(2.4, 2.2,-6.6), model = 'zigZagLevel', texture = 'zigZagLevelColor', scale = 0.8)    
        text = ba.newnode('text',
                              attrs={'position':(0,21,0),
                                     'text':':Bear_wave: :Bear_wave: :Bear_wave:',
                                     'in_world':True,
                                     'shadow':1.5,
                                     'flatness':0.7,
                                     'color':(1,1,1.2),
                                     'opacity':1.0,
                                     'scale':0.023,
                                     'h_align':'center'}) 
            
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.2, 1.1, 1.0)
        gnode.ambient_color = (1.2, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits() 
        
class Thoughts_d:
    points = {}
# noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (-1.045859963, 12.67722855,-5.401537075) + (0.0, 0.0, 0.0) + (34.46156851, 20.94044653, 0.6931564611)
    boxes['map_bounds'] = (-0.8748348681, 10.212941713, -5.729538885) + (0.0, 0.0, 0.0) + (36.09666006, 21.19950145, 7.89541168)
    
    points['ffa_spawn1'] = (-12.44, 10.29, -5.46) + (1.55, 1.45, 0.11)
    points['ffa_spawn2'] = (9.64, 10.29, -5.46) + (1.55, 1.45, 0.04)
    points['ffa_spawn3'] = (3.86, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['ffa_spawn4'] = (-6.42, 17.04,-5.46) + (1.33, 1.45, 0.04)
    points['ffa_spawn5'] = (-6.42, 4.04, -5.46) + (1.33, 1.45, 0.04)
    points['ffa_spawn6'] = (3.67, 4.04, -5.46) + (1.87, 1.45, 0.04)
    
    points['powerup_spawn1'] = (-8.07, 17.04, 5.46)
    points['powerup_spawn2'] = (5.50, 17.04, -5.46)
    points['powerup_spawn3'] = (5.50, 4.36, -5.46)
    points['powerup_spawn4'] = (-8.07, 4.35, 5.46)
    
    points['spawn1'] = (-12.44, 10.29, -5.46) + (1.55, 1.45, 0.11)
    points['spawn2'] = (9.64, 10.29, -5.46) + (1.55, 1.45, 0.04)
                    
    points['flag_default'] = (-1.42, 12.80, -5.46)  
    
    points['flag1'] = (-13.86, 10.04, -5.46) + (1.33, 1.45, 0.04)
    points['flag2'] = (11.29, 10.04, -5.46) + (1.33, 1.45, 0.04) 
    points['flag3'] = (3.86, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['flag4'] = (-6.42, 17.04,-5.46) + (1.33, 1.45, 0.04)
    points['flag5'] = (-6.42, 4.04, -5.46) + (1.33, 1.45, 0.04)
    points['flag6'] = (3.67, 4.04, -5.46) + (1.87, 1.45, 0.04)      
    
    points['spawn_by_flag1'] = (-13.86, 10.04, -5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag2'] = (11.29, 10.04, -5.46) + (1.33, 1.45, 0.04) 
    points['spawn_by_flag3'] = (3.86, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag4'] = (-6.42, 17.04,-5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag5'] = (-6.42, 4.04, -5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag6'] = (3.67, 4.04, -5.46) + (1.87, 1.45, 0.04)

class rT(ba.Map):
    """Flying map."""

    defs = Thoughts_d
    name = 'Space Thoughts'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return [
            'melee', 'keep_away', 'team_flag', 'conquest', 'king_of_the_hill'
        ]

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'alwaysLandLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
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
        
        

        self.background = ba.newnode(
            'terrain',
            attrs={
                'model': self.preloaddata['bgmodel'],
                'lighting': False,
                'color': (0.4,0.2,0.7),
                'background': True,
                'color_texture': self.preloaddata['bgtex']
            })

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
         
        self.zone = ba.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(-0.8748348681, 10.212941713, -5.729538885),
                                    'color':(-1,-1,-1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[36.09666006, 21.19950145, 0.07]})
        
        CollideBox(position=(11+ -1.3, 9, -5.5),scale=(5, 2, 0.5),color=(1,1,1), visible=True)    #1
        CollideBox(position=(-11+ -1.3, 9, -5.5),scale=(5, 2, 0.5),color=(1,1,1), visible=True)   #2
        CollideBox(position=(0+ -1.3, 10, -5.5),scale=(1.5, 5, 0.5),color=(1,1,1), visible=True)  #3
        CollideBox(position=(5+ -1.3, 3, -5.5),scale=(5, 1.5, 0.5),color=(1,1,1), visible=True)   #4 
        CollideBox(position=(-5+ -1.3, 3, -5.5),scale=(5, 1.5, 0.5),color=(1,1,1), visible=True)  #5 
        CollideBox(position=(5+ -1.3, 16, -5.5),scale=(5, 1.5, 0.5),color=(1,1,1), visible=True)  #6
        CollideBox(position=(-5+ -1.3, 16, -5.5),scale=(5, 1.5, 0.5),color=(1,1,1), visible=True) #7 
        text = ba.newnode('text',
                              attrs={'position':(0,32,0),
                                     'text':'Not Easter Egg Lol',
                                     'in_world':True,
                                     'shadow':1.5,
                                     'flatness':0.7,
                                     'color':(1,1,1.2),
                                     'opacity':1.0,
                                     'scale':0.023,
                                     'h_align':'center'}) 
        gnode = ba.getactivity().globalsnode
        gnode.happy_thoughts_mode = True
        gnode.shadow_offset = (0.0, 8.0, 5.0)
        gnode.tint = (1.3, 1.23, 1.0)
        gnode.ambient_color = (1.3, 1.23, 1.0)
        gnode.vignette_outer = (0.64, 0.59, 0.69)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        gnode.vr_near_clip = 1.0
        self.is_flying = True                                    
        FadeEfect(gnode.tint)
        Credits()
        
#List Maps
zk2059 = [SpazMap, RampageMod, BridgitC, thec, collosal_monkey, tZoe, rT, #ULTIMATE UPDATE
          Tarena, IslandMine, #v3 UPDATE
          FactoryMap,PlatformsMap,DarkZone, #v2
          NeoZone,CMap #v1
          ]

def register_maps():
    for new_map in zk2059:
        _map.register_map(new_map)
# Crown 
# ba_meta export plugin
class Zk2059(ba.Plugin):
    def __init__(self):
        if _ba.env().get("build_number", 0) >= 20258:
            register_maps()
        else:
            print("Zk5020 maps only runs with BombSquad versions higher than 1.5.29.")
            