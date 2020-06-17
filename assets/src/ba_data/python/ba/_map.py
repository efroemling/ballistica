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
"""Map related functionality."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _ba
from ba import _math
from ba._actor import Actor

if TYPE_CHECKING:
    from typing import Set, List, Type, Optional, Sequence, Any, Tuple
    import ba


def preload_map_preview_media() -> None:
    """Preload media needed for map preview UIs.

    Category: Asset Functions
    """
    _ba.getmodel('level_select_button_opaque')
    _ba.getmodel('level_select_button_transparent')
    for maptype in list(_ba.app.maps.values()):
        map_tex_name = maptype.get_preview_texture_name()
        if map_tex_name is not None:
            _ba.gettexture(map_tex_name)


def get_filtered_map_name(name: str) -> str:
    """Filter a map name to account for name changes, etc.

    Category: Asset Functions

    This can be used to support old playlists, etc.
    """
    # Some legacy name fallbacks... can remove these eventually.
    if name in ('AlwaysLand', 'Happy Land'):
        name = 'Happy Thoughts'
    if name == 'Hockey Arena':
        name = 'Hockey Stadium'
    return name


def get_map_display_string(name: str) -> ba.Lstr:
    """Return a ba.Lstr for displaying a given map\'s name.

    Category: Asset Functions
    """
    from ba import _lang
    return _lang.Lstr(translate=('mapsNames', name))


def getmaps(playtype: str) -> List[str]:
    """Return a list of ba.Map types supporting a playtype str.

    Category: Asset Functions

    Maps supporting a given playtype must provide a particular set of
    features and lend themselves to a certain style of play.

    Play Types:

    'melee'
      General fighting map.
      Has one or more 'spawn' locations.

    'team_flag'
      For games such as Capture The Flag where each team spawns by a flag.
      Has two or more 'spawn' locations, each with a corresponding 'flag'
      location (based on index).

    'single_flag'
      For games such as King of the Hill or Keep Away where multiple teams
      are fighting over a single flag.
      Has two or more 'spawn' locations and 1 'flag_default' location.

    'conquest'
      For games such as Conquest where flags are spread throughout the map
      - has 2+ 'flag' locations, 2+ 'spawn_by_flag' locations.

    'king_of_the_hill' - has 2+ 'spawn' locations, 1+ 'flag_default' locations,
                         and 1+ 'powerup_spawn' locations

    'hockey'
      For hockey games.
      Has two 'goal' locations, corresponding 'spawn' locations, and one
      'flag_default' location (for where puck spawns)

    'football'
      For football games.
      Has two 'goal' locations, corresponding 'spawn' locations, and one
      'flag_default' location (for where flag/ball/etc. spawns)

    'race'
      For racing games where players much touch each region in order.
      Has two or more 'race_point' locations.
    """
    return sorted(key for key, val in _ba.app.maps.items()
                  if playtype in val.get_play_types())


def get_unowned_maps() -> List[str]:
    """Return the list of local maps not owned by the current account.

    Category: Asset Functions
    """
    from ba import _store
    unowned_maps: Set[str] = set()
    if not _ba.app.headless_build:
        for map_section in _store.get_store_layout()['maps']:
            for mapitem in map_section['items']:
                if not _ba.get_purchased(mapitem):
                    m_info = _store.get_store_item(mapitem)
                    unowned_maps.add(m_info['map_type'].name)
    return sorted(unowned_maps)


def get_map_class(name: str) -> Type[ba.Map]:
    """Return a map type given a name.

    Category: Asset Functions
    """
    name = get_filtered_map_name(name)
    try:
        return _ba.app.maps[name]
    except KeyError:
        from ba import _error
        raise _error.NotFoundError(f"Map not found: '{name}'") from None


class Map(Actor):
    """A game map.

    Category: Gameplay Classes

    Consists of a collection of terrain nodes, metadata, and other
    functionality comprising a game map.
    """
    defs: Any = None
    name = 'Map'
    _playtypes: List[str] = []

    @classmethod
    def preload(cls) -> None:
        """Preload map media.

        This runs the class's on_preload() method as needed to prep it to run.
        Preloading should generally be done in a ba.Activity's __init__ method.
        Note that this is a classmethod since it is not operate on map
        instances but rather on the class itself before instances are made
        """
        activity = _ba.getactivity()
        if cls not in activity.preloads:
            activity.preloads[cls] = cls.on_preload()

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return []

    @classmethod
    def get_preview_texture_name(cls) -> Optional[str]:
        """Return the name of the preview texture for this map."""
        return None

    @classmethod
    def on_preload(cls) -> Any:
        """Called when the map is being preloaded.

        It should return any media/data it requires to operate
        """
        return None

    @classmethod
    def getname(cls) -> str:
        """Return the unique name of this map, in English."""
        return cls.name

    @classmethod
    def get_music_type(cls) -> Optional[ba.MusicType]:
        """Return a music-type string that should be played on this map.

        If None is returned, default music will be used.
        """
        return None

    def __init__(self,
                 vr_overlay_offset: Optional[Sequence[float]] = None) -> None:
        """Instantiate a map."""
        from ba import _gameutils
        super().__init__()

        # This is expected to always be a ba.Node object (whether valid or not)
        # should be set to something meaningful by child classes.
        self.node: Optional[_ba.Node] = None

        # Make our class' preload-data available to us
        # (and instruct the user if we weren't preloaded properly).
        try:
            self.preloaddata = _ba.getactivity().preloads[type(self)]
        except Exception:
            from ba import _error
            raise _error.NotFoundError(
                'Preload data not found for ' + str(type(self)) +
                '; make sure to call the type\'s preload()'
                ' staticmethod in the activity constructor')

        # Set various globals.
        gnode = _ba.getactivity().globalsnode

        # Set area-of-interest bounds.
        aoi_bounds = self.get_def_bound_box('area_of_interest_bounds')
        if aoi_bounds is None:
            print('WARNING: no "aoi_bounds" found for map:', self.getname())
            aoi_bounds = (-1, -1, -1, 1, 1, 1)
        gnode.area_of_interest_bounds = aoi_bounds

        # Set map bounds.
        map_bounds = self.get_def_bound_box('map_bounds')
        if map_bounds is None:
            print('WARNING: no "map_bounds" found for map:', self.getname())
            map_bounds = (-30, -10, -30, 30, 100, 30)
        _ba.set_map_bounds(map_bounds)

        # Set shadow ranges.
        try:
            gnode.shadow_range = [
                self.defs.points[v][1] for v in [
                    'shadow_lower_bottom', 'shadow_lower_top',
                    'shadow_upper_bottom', 'shadow_upper_top'
                ]
            ]
        except Exception:
            pass

        # In vr, set a fixed point in space for the overlay to show up at.
        # By default we use the bounds center but allow the map to override it.
        center = ((aoi_bounds[0] + aoi_bounds[3]) * 0.5,
                  (aoi_bounds[1] + aoi_bounds[4]) * 0.5,
                  (aoi_bounds[2] + aoi_bounds[5]) * 0.5)
        if vr_overlay_offset is not None:
            center = (center[0] + vr_overlay_offset[0],
                      center[1] + vr_overlay_offset[1],
                      center[2] + vr_overlay_offset[2])
        gnode.vr_overlay_center = center
        gnode.vr_overlay_center_enabled = True

        self.spawn_points = (self.get_def_points('spawn')
                             or [(0, 0, 0, 0, 0, 0)])
        self.ffa_spawn_points = (self.get_def_points('ffa_spawn')
                                 or [(0, 0, 0, 0, 0, 0)])
        self.spawn_by_flag_points = (self.get_def_points('spawn_by_flag')
                                     or [(0, 0, 0, 0, 0, 0)])
        self.flag_points = self.get_def_points('flag') or [(0, 0, 0)]

        # We just want points.
        self.flag_points = [p[:3] for p in self.flag_points]
        self.flag_points_default = (self.get_def_point('flag_default')
                                    or (0, 1, 0))
        self.powerup_spawn_points = self.get_def_points('powerup_spawn') or [
            (0, 0, 0)
        ]

        # We just want points.
        self.powerup_spawn_points = ([
            p[:3] for p in self.powerup_spawn_points
        ])
        self.tnt_points = self.get_def_points('tnt') or []

        # We just want points.
        self.tnt_points = [p[:3] for p in self.tnt_points]

        self.is_hockey = False
        self.is_flying = False

        # FIXME: this should be part of game; not map.
        self._next_ffa_start_index = 0

    def is_point_near_edge(self,
                           point: ba.Vec3,
                           running: bool = False) -> bool:
        """Return whether the provided point is near an edge of the map.

        Simple bot logic uses this call to determine if they
        are approaching a cliff or wall. If this returns True they will
        generally not walk/run any farther away from the origin.
        If 'running' is True, the buffer should be a bit larger.
        """
        del point, running  # Unused.
        return False

    def get_def_bound_box(
        self, name: str
    ) -> Optional[Tuple[float, float, float, float, float, float]]:
        """Return a 6 member bounds tuple or None if it is not defined."""
        try:
            box = self.defs.boxes[name]
            return (box[0] - box[6] / 2.0, box[1] - box[7] / 2.0,
                    box[2] - box[8] / 2.0, box[0] + box[6] / 2.0,
                    box[1] + box[7] / 2.0, box[2] + box[8] / 2.0)
        except Exception:
            return None

    def get_def_point(self, name: str) -> Optional[Sequence[float]]:
        """Return a single defined point or a default value in its absence."""
        val = self.defs.points.get(name)
        return (None if val is None else
                _math.vec3validate(val) if __debug__ else val)

    def get_def_points(self, name: str) -> List[Sequence[float]]:
        """Return a list of named points.

        Return as many sequential ones are defined (flag1, flag2, flag3), etc.
        If none are defined, returns an empty list.
        """
        point_list = []
        if self.defs and name + '1' in self.defs.points:
            i = 1
            while name + str(i) in self.defs.points:
                pts = self.defs.points[name + str(i)]
                if len(pts) == 6:
                    point_list.append(pts)
                else:
                    if len(pts) != 3:
                        raise ValueError('invalid point')
                    point_list.append(pts + (0, 0, 0))
                i += 1
        return point_list

    def get_start_position(self, team_index: int) -> Sequence[float]:
        """Return a random starting position for the given team index."""
        pnt = self.spawn_points[team_index % len(self.spawn_points)]
        x_range = (-0.5, 0.5) if pnt[3] == 0.0 else (-pnt[3], pnt[3])
        z_range = (-0.5, 0.5) if pnt[5] == 0.0 else (-pnt[5], pnt[5])
        pnt = (pnt[0] + random.uniform(*x_range), pnt[1],
               pnt[2] + random.uniform(*z_range))
        return pnt

    def get_ffa_start_position(
            self, players: Sequence[ba.Player]) -> Sequence[float]:
        """Return a random starting position in one of the FFA spawn areas.

        If a list of ba.Players is provided; the returned points will be
        as far from these players as possible.
        """

        # Get positions for existing players.
        player_pts = []
        for player in players:
            if player.is_alive():
                player_pts.append(player.position)

        def _getpt() -> Sequence[float]:
            point = self.ffa_spawn_points[self._next_ffa_start_index]
            self._next_ffa_start_index = ((self._next_ffa_start_index + 1) %
                                          len(self.ffa_spawn_points))
            x_range = (-0.5, 0.5) if point[3] == 0.0 else (-point[3], point[3])
            z_range = (-0.5, 0.5) if point[5] == 0.0 else (-point[5], point[5])
            point = (point[0] + random.uniform(*x_range), point[1],
                     point[2] + random.uniform(*z_range))
            return point

        if not player_pts:
            return _getpt()

        # Let's calc several start points and then pick whichever is
        # farthest from all existing players.
        farthestpt_dist = -1.0
        farthestpt = None
        for _i in range(10):
            testpt = _ba.Vec3(_getpt())
            closest_player_dist = 9999.0
            for ppt in player_pts:
                dist = (ppt - testpt).length()
                if dist < closest_player_dist:
                    closest_player_dist = dist
            if closest_player_dist > farthestpt_dist:
                farthestpt_dist = closest_player_dist
                farthestpt = testpt
        assert farthestpt is not None
        return tuple(farthestpt)

    def get_flag_position(self, team_index: int = None) -> Sequence[float]:
        """Return a flag position on the map for the given team index.

        Pass None to get the default flag point.
        (used for things such as king-of-the-hill)
        """
        if team_index is None:
            return self.flag_points_default[:3]
        return self.flag_points[team_index % len(self.flag_points)][:3]

    def exists(self) -> bool:
        return bool(self.node)

    def handlemessage(self, msg: Any) -> Any:
        from ba import _messages
        if isinstance(msg, _messages.DieMessage):
            if self.node:
                self.node.delete()
        else:
            return super().handlemessage(msg)
        return None


def register_map(maptype: Type[Map]) -> None:
    """Register a map class with the game."""
    if maptype.name in _ba.app.maps:
        raise RuntimeError('map "' + maptype.name + '" already registered')
    _ba.app.maps[maptype.name] = maptype
