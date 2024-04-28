# Released under the MIT License. See LICENSE for details.
#
"""Map related functionality."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import babase

import _bascenev1
from bascenev1._actor import Actor

if TYPE_CHECKING:
    from typing import Sequence, Any

    import bascenev1


def get_filtered_map_name(name: str) -> str:
    """Filter a map name to account for name changes, etc.

    Category: **Asset Functions**

    This can be used to support old playlists, etc.
    """
    # Some legacy name fallbacks... can remove these eventually.
    if name in ('AlwaysLand', 'Happy Land'):
        name = 'Happy Thoughts'
    if name == 'Hockey Arena':
        name = 'Hockey Stadium'
    return name


def get_map_display_string(name: str) -> babase.Lstr:
    """Return a babase.Lstr for displaying a given map\'s name.

    Category: **Asset Functions**
    """
    return babase.Lstr(translate=('mapsNames', name))


def get_map_class(name: str) -> type[Map]:
    """Return a map type given a name.

    Category: **Asset Functions**
    """
    assert babase.app.classic is not None
    name = get_filtered_map_name(name)
    try:
        mapclass: type[Map] = babase.app.classic.maps[name]
        return mapclass
    except KeyError:
        raise babase.NotFoundError(f"Map not found: '{name}'") from None


class Map(Actor):
    """A game map.

    Category: **Gameplay Classes**

    Consists of a collection of terrain nodes, metadata, and other
    functionality comprising a game map.
    """

    defs: Any = None
    name = 'Map'
    _playtypes: list[str] = []

    @classmethod
    def preload(cls) -> None:
        """Preload map media.

        This runs the class's on_preload() method as needed to prep it to run.
        Preloading should generally be done in a bascenev1.Activity's
        __init__ method. Note that this is a classmethod since it is not
        operate on map instances but rather on the class itself before
        instances are made
        """
        activity = _bascenev1.getactivity()
        if cls not in activity.preloads:
            activity.preloads[cls] = cls.on_preload()

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str | None:
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
    def get_music_type(cls) -> bascenev1.MusicType | None:
        """Return a music-type string that should be played on this map.

        If None is returned, default music will be used.
        """
        return None

    def __init__(
        self, vr_overlay_offset: Sequence[float] | None = None
    ) -> None:
        """Instantiate a map."""
        super().__init__()

        # This is expected to always be a bascenev1.Node object
        # (whether valid or not) should be set to something meaningful
        # by child classes.
        self.node: _bascenev1.Node | None = None

        # Make our class' preload-data available to us
        # (and instruct the user if we weren't preloaded properly).
        try:
            self.preloaddata = _bascenev1.getactivity().preloads[type(self)]
        except Exception as exc:
            raise babase.NotFoundError(
                'Preload data not found for '
                + str(type(self))
                + '; make sure to call the type\'s preload()'
                ' staticmethod in the activity constructor'
            ) from exc

        # Set various globals.
        gnode = _bascenev1.getactivity().globalsnode

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
        _bascenev1.set_map_bounds(map_bounds)

        # Set shadow ranges.
        try:
            gnode.shadow_range = [
                self.defs.points[v][1]
                for v in [
                    'shadow_lower_bottom',
                    'shadow_lower_top',
                    'shadow_upper_bottom',
                    'shadow_upper_top',
                ]
            ]
        except Exception:
            pass

        # In vr, set a fixed point in space for the overlay to show up at.
        # By default we use the bounds center but allow the map to override it.
        center = (
            (aoi_bounds[0] + aoi_bounds[3]) * 0.5,
            (aoi_bounds[1] + aoi_bounds[4]) * 0.5,
            (aoi_bounds[2] + aoi_bounds[5]) * 0.5,
        )
        if vr_overlay_offset is not None:
            center = (
                center[0] + vr_overlay_offset[0],
                center[1] + vr_overlay_offset[1],
                center[2] + vr_overlay_offset[2],
            )
        gnode.vr_overlay_center = center
        gnode.vr_overlay_center_enabled = True

        self.spawn_points = self.get_def_points('spawn') or [(0, 0, 0, 0, 0, 0)]
        self.ffa_spawn_points = self.get_def_points('ffa_spawn') or [
            (0, 0, 0, 0, 0, 0)
        ]
        self.spawn_by_flag_points = self.get_def_points('spawn_by_flag') or [
            (0, 0, 0, 0, 0, 0)
        ]
        self.flag_points = self.get_def_points('flag') or [(0, 0, 0)]

        # We just want points.
        self.flag_points = [p[:3] for p in self.flag_points]
        self.flag_points_default = self.get_def_point('flag_default') or (
            0,
            1,
            0,
        )
        self.powerup_spawn_points = self.get_def_points('powerup_spawn') or [
            (0, 0, 0)
        ]

        # We just want points.
        self.powerup_spawn_points = [p[:3] for p in self.powerup_spawn_points]
        self.tnt_points = self.get_def_points('tnt') or []

        # We just want points.
        self.tnt_points = [p[:3] for p in self.tnt_points]

        self.is_hockey = False
        self.is_flying = False

        # FIXME: this should be part of game; not map.
        # Let's select random index for first spawn point,
        # so that no one is offended by the constant spawn on the edge.
        self._next_ffa_start_index = random.randrange(
            len(self.ffa_spawn_points)
        )

    def is_point_near_edge(
        self, point: babase.Vec3, running: bool = False
    ) -> bool:
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
    ) -> tuple[float, float, float, float, float, float] | None:
        """Return a 6 member bounds tuple or None if it is not defined."""
        try:
            box = self.defs.boxes[name]
            return (
                box[0] - box[6] / 2.0,
                box[1] - box[7] / 2.0,
                box[2] - box[8] / 2.0,
                box[0] + box[6] / 2.0,
                box[1] + box[7] / 2.0,
                box[2] + box[8] / 2.0,
            )
        except Exception:
            return None

    def get_def_point(self, name: str) -> Sequence[float] | None:
        """Return a single defined point or a default value in its absence."""
        val = self.defs.points.get(name)
        return (
            None
            if val is None
            else babase.vec3validate(val) if __debug__ else val
        )

    def get_def_points(self, name: str) -> list[Sequence[float]]:
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
        pnt = (
            pnt[0] + random.uniform(*x_range),
            pnt[1],
            pnt[2] + random.uniform(*z_range),
        )
        return pnt

    def get_ffa_start_position(
        self, players: Sequence[bascenev1.Player]
    ) -> Sequence[float]:
        """Return a random starting position in one of the FFA spawn areas.

        If a list of bascenev1.Player-s is provided; the returned points
        will be as far from these players as possible.
        """

        # Get positions for existing players.
        player_pts = []
        for player in players:
            if player.is_alive():
                player_pts.append(player.position)

        def _getpt() -> Sequence[float]:
            point = self.ffa_spawn_points[self._next_ffa_start_index]
            self._next_ffa_start_index = (self._next_ffa_start_index + 1) % len(
                self.ffa_spawn_points
            )
            x_range = (-0.5, 0.5) if point[3] == 0.0 else (-point[3], point[3])
            z_range = (-0.5, 0.5) if point[5] == 0.0 else (-point[5], point[5])
            point = (
                point[0] + random.uniform(*x_range),
                point[1],
                point[2] + random.uniform(*z_range),
            )
            return point

        if not player_pts:
            return _getpt()

        # Let's calc several start points and then pick whichever is
        # farthest from all existing players.
        farthestpt_dist = -1.0
        farthestpt = None
        for _i in range(10):
            testpt = babase.Vec3(_getpt())
            closest_player_dist = 9999.0
            for ppt in player_pts:
                dist = (ppt - testpt).length()
                closest_player_dist = min(dist, closest_player_dist)
            if closest_player_dist > farthestpt_dist:
                farthestpt_dist = closest_player_dist
                farthestpt = testpt
        assert farthestpt is not None
        return tuple(farthestpt)

    def get_flag_position(
        self, team_index: int | None = None
    ) -> Sequence[float]:
        """Return a flag position on the map for the given team index.

        Pass None to get the default flag point.
        (used for things such as king-of-the-hill)
        """
        if team_index is None:
            return self.flag_points_default[:3]
        return self.flag_points[team_index % len(self.flag_points)][:3]

    @override
    def exists(self) -> bool:
        return bool(self.node)

    @override
    def handlemessage(self, msg: Any) -> Any:
        from bascenev1 import _messages

        if isinstance(msg, _messages.DieMessage):
            if self.node:
                self.node.delete()
        else:
            return super().handlemessage(msg)
        return None


def register_map(maptype: type[Map]) -> None:
    """Register a map class with the game."""
    assert babase.app.classic is not None
    if maptype.name in babase.app.classic.maps:
        raise RuntimeError(f'Map "{maptype.name}" is already registered.')
    babase.app.classic.maps[maptype.name] = maptype
