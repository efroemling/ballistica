# Released under the MIT License. See LICENSE for details.
#
"""Ballistica Scene Version 1"""

# ba_meta require api 8

# The stuff we expose here at the top level is our 'public' api.
# It should only be imported by code outside of this package or
# from 'if TYPE_CHECKING' blocks (which will not exec at runtime).
# Code within our package should import things directly from their
# submodules.

from __future__ import annotations

import logging

# Aside from our own stuff, we also bundle a number of things from ba or
# other modules; the goal is to let most simple mods rely solely on this
# module to keep things simple.

from efro.util import set_canonical_module_names


from _babase import (
    app,
    ContextRef,
    lock_all_input,
    unlock_all_input,
    fade_screen,
    safecolor,
    pushcall,
    Vec3,
    increment_analytics_count,
    set_analytics_screen,
    apptime,
    apptimer,
    AppTimer,
    displaytime,
    displaytimer,
    DisplayTimer,
)
from babase import Plugin
from babase._appintent import AppIntent, AppIntentDefault, AppIntentExec
from babase._appmode import AppMode
from babase._error import NotFoundError, NodeNotFoundError, ContextError
from babase._language import Lstr
from babase._general import (
    WeakCall,
    Call,
    storagename,
    existing,
    AppTime,
    DisplayTime,
)
from babase._math import is_point_in_box, normalized_color
from babase._text import timestring
from babase._apputils import get_remote_app_name

from babase._mgen.enums import (
    UIScale,
    InputType,
)

from _bascenev1 import (
    set_internal_music,
    set_master_server_source,
    get_foreground_host_session,
    get_foreground_host_activity,
    get_game_roster,
    set_debug_speed_exponent,
    get_replay_speed_exponent,
    set_replay_speed_exponent,
    reset_random_player_names,
    get_random_names,
    screenmessage,
    set_public_party_stats_url,
    set_admins,
    set_enable_default_kick_voting,
    have_connected_clients,
    is_in_replay,
    client_info_query_response,
    disconnect_from_host,
    set_public_party_queue_enabled,
    set_public_party_max_size,
    set_authenticate_clients,
    set_public_party_enabled,
    get_game_port,
    set_public_party_name,
    get_public_party_enabled,
    get_public_party_max_size,
    connect_to_party,
    host_scan_cycle,
    end_host_scanning,
    set_touchscreen_editing,
    get_ui_input_device,
    get_local_active_input_devices_count,
    have_touchscreen_input,
    capture_keyboard_input,
    release_keyboard_input,
    capture_gamepad_input,
    release_gamepad_input,
    newactivity,
    set_map_bounds,
    get_connection_to_host_info,
    newnode,
    new_replay_session,
    new_host_session,
    getsession,
    InputDevice,
    SessionPlayer,
    Material,
    ActivityData,
    camerashake,
    emitfx,
    ls_objects,
    ls_input_devices,
    CollisionMesh,
    getcollisionmesh,
    Data,
    getdata,
    Mesh,
    getmesh,
    SessionData,
    Sound,
    getsound,
    getnodes,
    printnodes,
    getactivity,
    time,
    timer,
    Node,
    Texture,
    Timer,
    gettexture,
    getinputdevice,
    disconnect_client,
    chatmessage,
    get_chat_messages,
    basetime,
    basetimer,
    BaseTimer,
)

from bascenev1._profile import (
    get_player_colors,
    get_player_profile_icon,
    get_player_profile_colors,
)
from bascenev1._appmode import SceneV1AppMode
from bascenev1._session import Session
from bascenev1._map import Map
from bascenev1._coopsession import CoopSession
from bascenev1._debug import print_live_object_warnings
from bascenev1._multiteamsession import MultiTeamSession
from bascenev1._coopgame import CoopGameActivity
from bascenev1._freeforallsession import FreeForAllSession
from bascenev1._gameactivity import GameActivity
from bascenev1._score import ScoreType, ScoreConfig
from bascenev1._dualteamsession import DualTeamSession
from bascenev1._lobby import Lobby, Chooser
from bascenev1._campaign import Campaign
from bascenev1._level import Level
from bascenev1._messages import (
    UNHANDLED,
    OutOfBoundsMessage,
    DeathType,
    DieMessage,
    PlayerDiedMessage,
    StandMessage,
    PickUpMessage,
    DropMessage,
    PickedUpMessage,
    DroppedMessage,
    ShouldShatterMessage,
    ImpactDamageMessage,
    FreezeMessage,
    ThawMessage,
    HitMessage,
    CelebrateMessage,
)
from bascenev1._player import PlayerInfo, Player, EmptyPlayer, StandLocation
from bascenev1._activity import Activity
from bascenev1._actor import Actor
from bascenev1._gameresults import GameResults
from bascenev1._nodeactor import NodeActor
from bascenev1._collision import Collision, getcollision
from bascenev1._powerup import PowerupMessage, PowerupAcceptMessage
from bascenev1._team import SessionTeam, Team, EmptyTeam
from bascenev1._gameutils import (
    Time,
    BaseTime,
    GameTip,
    animate,
    animate_array,
    show_damage_count,
    cameraflash,
)
from bascenev1._teamgame import TeamGameActivity
from bascenev1._stats import PlayerScoredMessage, PlayerRecord, Stats
from bascenev1._settings import (
    Setting,
    IntSetting,
    FloatSetting,
    ChoiceSetting,
    BoolSetting,
    IntChoiceSetting,
    FloatChoiceSetting,
)
from bascenev1._activitytypes import JoinActivity, ScoreScreenActivity
from bascenev1._music import MusicType, setmusic
from bascenev1._dependency import (
    Dependency,
    DependencyComponent,
    DependencySet,
    AssetPackage,
)
from bascenev1._gameutils import get_trophy_string

__all__ = [
    'set_internal_music',
    'get_trophy_string',
    'app',
    'get_local_active_input_devices_count',
    'lock_all_input',
    'unlock_all_input',
    'getinputdevice',
    'Session',
    'Map',
    'CoopSession',
    'MultiTeamSession',
    'CoopGameActivity',
    'print_live_object_warnings',
    'FreeForAllSession',
    'GameActivity',
    'ScoreType',
    'ScoreConfig',
    'DualTeamSession',
    'UNHANDLED',
    'OutOfBoundsMessage',
    'DeathType',
    'DieMessage',
    'DropMessage',
    'DroppedMessage',
    'FreezeMessage',
    'HitMessage',
    'ImpactDamageMessage',
    'Node',
    'PickedUpMessage',
    'PickUpMessage',
    'PlayerDiedMessage',
    'ShouldShatterMessage',
    'StandMessage',
    'ThawMessage',
    'CelebrateMessage',
    'EmptyPlayer',
    'Player',
    'PlayerInfo',
    'StandLocation',
    'Activity',
    'Actor',
    'GameResults',
    'NodeActor',
    'Collision',
    'getcollision',
    'PowerupMessage',
    'PowerupAcceptMessage',
    'SessionTeam',
    'Team',
    'EmptyTeam',
    'GameTip',
    'animate',
    'animate_array',
    'show_damage_count',
    'cameraflash',
    'TeamGameActivity',
    'PlayerScoredMessage',
    'PlayerRecord',
    'Stats',
    'Setting',
    'IntSetting',
    'FloatSetting',
    'ChoiceSetting',
    'BoolSetting',
    'IntChoiceSetting',
    'FloatChoiceSetting',
    'JoinActivity',
    'ScoreScreenActivity',
    'MusicType',
    'setmusic',
    'newnode',
    'new_host_session',
    'getsession',
    'get_foreground_host_session',
    'get_foreground_host_activity',
    'InputDevice',
    'SessionPlayer',
    'Material',
    'ActivityData',
    'camerashake',
    'emitfx',
    'ls_objects',
    'ls_input_devices',
    'CollisionMesh',
    'getcollisionmesh',
    'Dependency',
    'DependencyComponent',
    'AssetPackage',
    'DependencySet',
    'Data',
    'getdata',
    'Mesh',
    'getmesh',
    'SessionData',
    'Sound',
    'getsound',
    'getnodes',
    'printnodes',
    'getactivity',
    'time',
    'timer',
    'Texture',
    'Vec3',
    'NotFoundError',
    'NodeNotFoundError',
    'Timer',
    'Lstr',
    'gettexture',
    'WeakCall',
    'Call',
    'new_replay_session',
    'increment_analytics_count',
    'set_analytics_screen',
    'set_debug_speed_exponent',
    'screenmessage',
    'InputType',
    'UIScale',
    'pushcall',
    'is_point_in_box',
    'safecolor',
    'storagename',
    'timestring',
    'get_game_roster',
    'disconnect_client',
    'get_connection_to_host_info',
    'chatmessage',
    'get_chat_messages',
    'existing',
    'set_map_bounds',
    'normalized_color',
    'get_remote_app_name',
    'newactivity',
    'ContextError',
    'fade_screen',
    'capture_keyboard_input',
    'release_keyboard_input',
    'capture_gamepad_input',
    'release_gamepad_input',
    'have_touchscreen_input',
    'get_ui_input_device',
    'set_touchscreen_editing',
    'end_host_scanning',
    'host_scan_cycle',
    'connect_to_party',
    'get_public_party_enabled',
    'get_public_party_max_size',
    'set_public_party_name',
    'get_game_port',
    'set_public_party_enabled',
    'set_authenticate_clients',
    'set_public_party_max_size',
    'set_public_party_queue_enabled',
    'disconnect_from_host',
    'client_info_query_response',
    'is_in_replay',
    'have_connected_clients',
    'set_enable_default_kick_voting',
    'set_admins',
    'set_public_party_stats_url',
    'get_random_names',
    'reset_random_player_names',
    'get_replay_speed_exponent',
    'set_replay_speed_exponent',
    'set_debug_speed_exponent',
    'get_game_roster',
    'AppTime',
    'apptime',
    'apptimer',
    'AppTimer',
    'ContextRef',
    'basetime',
    'basetimer',
    'BaseTimer',
    'displaytime',
    'DisplayTime',
    'displaytimer',
    'DisplayTimer',
    'Time',
    'BaseTime',
    'AppIntent',
    'AppIntentDefault',
    'AppIntentExec',
    'AppMode',
    'SceneV1AppMode',
    'Lobby',
    'Chooser',
    'Campaign',
    'Level',
    'Plugin',
    'get_player_colors',
    'get_player_profile_icon',
    'get_player_profile_colors',
    'set_master_server_source',
]

# We want stuff here to show up as bascenev1.Foo instead of
# bascenev1._submodule.Foo.
set_canonical_module_names(globals())

# Sanity check: we want to keep ballistica's dependencies and
# bootstrapping order clearly defined; let's check a few particular
# modules to make sure they never directly or indirectly import us
# before their own execs complete.
if __debug__:
    for _mdl in 'babase', '_babase':
        if not hasattr(__import__(_mdl), '_REACHED_END_OF_MODULE'):
            logging.warning(
                '%s was imported before %s finished importing;'
                ' should not happen.',
                __name__,
                _mdl,
            )
