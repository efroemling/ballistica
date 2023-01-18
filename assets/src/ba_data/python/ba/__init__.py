# Released under the MIT License. See LICENSE for details.
#
"""The public face of Ballistica.

This top level module is a collection of most commonly used functionality.
For many modding purposes, the bits exposed here are all you'll need.
In some specific cases you may need to pull in individual submodules instead.
"""
# pylint: disable=redefined-builtin

from _ba import (
    CollideModel,
    Context,
    ContextCall,
    Data,
    InputDevice,
    Material,
    Model,
    Node,
    SessionPlayer,
    Sound,
    Texture,
    Timer,
    Vec3,
    Widget,
    buttonwidget,
    camerashake,
    checkboxwidget,
    columnwidget,
    containerwidget,
    do_once,
    emitfx,
    getactivity,
    getcollidemodel,
    getmodel,
    getnodes,
    getsession,
    getsound,
    gettexture,
    hscrollwidget,
    imagewidget,
    newactivity,
    newnode,
    playsound,
    printnodes,
    ls_objects,
    ls_input_devices,
    pushcall,
    quit,
    rowwidget,
    safecolor,
    screenmessage,
    scrollwidget,
    set_analytics_screen,
    charstr,
    textwidget,
    time,
    timer,
    open_url,
    widget,
    clipboard_is_supported,
    clipboard_has_text,
    clipboard_get_text,
    clipboard_set_text,
    getdata,
    in_logic_thread,
)
from ba._accountv2 import AccountV2Handle
from ba._activity import Activity
from ba._plugin import PotentialPlugin, Plugin, PluginSubsystem
from ba._actor import Actor
from ba._player import PlayerInfo, Player, EmptyPlayer, StandLocation
from ba._nodeactor import NodeActor
from ba._app import App
from ba._cloud import CloudSubsystem
from ba._coopgame import CoopGameActivity
from ba._coopsession import CoopSession
from ba._dependency import (
    Dependency,
    DependencyComponent,
    DependencySet,
    AssetPackage,
)
from ba._generated.enums import (
    TimeType,
    Permission,
    TimeFormat,
    SpecialChar,
    InputType,
    UIScale,
)
from ba._error import (
    print_exception,
    print_error,
    ContextError,
    NotFoundError,
    PlayerNotFoundError,
    SessionPlayerNotFoundError,
    NodeNotFoundError,
    ActorNotFoundError,
    InputDeviceNotFoundError,
    WidgetNotFoundError,
    ActivityNotFoundError,
    TeamNotFoundError,
    SessionTeamNotFoundError,
    SessionNotFoundError,
    DelegateNotFoundError,
    DependencyError,
)
from ba._freeforallsession import FreeForAllSession
from ba._gameactivity import GameActivity
from ba._gameresults import GameResults
from ba._settings import (
    Setting,
    IntSetting,
    FloatSetting,
    ChoiceSetting,
    BoolSetting,
    IntChoiceSetting,
    FloatChoiceSetting,
)
from ba._language import Lstr, LanguageSubsystem
from ba._map import Map, getmaps
from ba._session import Session
from ba._ui import UISubsystem
from ba._servermode import ServerController
from ba._score import ScoreType, ScoreConfig
from ba._stats import PlayerScoredMessage, PlayerRecord, Stats
from ba._team import SessionTeam, Team, EmptyTeam
from ba._teamgame import TeamGameActivity
from ba._dualteamsession import DualTeamSession
from ba._achievement import Achievement, AchievementSubsystem
from ba._appconfig import AppConfig
from ba._appdelegate import AppDelegate
from ba._apputils import is_browser_likely_available, garbage_collect
from ba._campaign import Campaign
from ba._gameutils import (
    GameTip,
    animate,
    animate_array,
    show_damage_count,
    timestring,
    cameraflash,
)
from ba._general import (
    WeakCall,
    Call,
    existing,
    Existable,
    verify_object_death,
    storagename,
    getclass,
)
from ba._keyboard import Keyboard
from ba._level import Level
from ba._lobby import Lobby, Chooser
from ba._math import normalized_color, is_point_in_box, vec3validate
from ba._meta import MetadataSubsystem
from ba._messages import (
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
from ba._music import (
    setmusic,
    MusicPlayer,
    MusicType,
    MusicPlayMode,
    MusicSubsystem,
)
from ba._powerup import PowerupMessage, PowerupAcceptMessage
from ba._multiteamsession import MultiTeamSession
from ba.ui import Window, UIController, uicleanupcheck
from ba._collision import Collision, getcollision

app: App

__all__ = [
    'AccountV2Handle',
    'Achievement',
    'AchievementSubsystem',
    'Activity',
    'ActivityNotFoundError',
    'Actor',
    'ActorNotFoundError',
    'animate',
    'animate_array',
    'app',
    'App',
    'AppConfig',
    'AppDelegate',
    'AssetPackage',
    'BoolSetting',
    'buttonwidget',
    'Call',
    'cameraflash',
    'camerashake',
    'Campaign',
    'CelebrateMessage',
    'charstr',
    'checkboxwidget',
    'ChoiceSetting',
    'Chooser',
    'clipboard_get_text',
    'clipboard_has_text',
    'clipboard_is_supported',
    'clipboard_set_text',
    'CollideModel',
    'Collision',
    'columnwidget',
    'containerwidget',
    'Context',
    'ContextCall',
    'ContextError',
    'CloudSubsystem',
    'CoopGameActivity',
    'CoopSession',
    'Data',
    'DeathType',
    'DelegateNotFoundError',
    'Dependency',
    'DependencyComponent',
    'DependencyError',
    'DependencySet',
    'DieMessage',
    'do_once',
    'DropMessage',
    'DroppedMessage',
    'DualTeamSession',
    'emitfx',
    'EmptyPlayer',
    'EmptyTeam',
    'Existable',
    'existing',
    'FloatChoiceSetting',
    'FloatSetting',
    'FreeForAllSession',
    'FreezeMessage',
    'GameActivity',
    'GameResults',
    'GameTip',
    'garbage_collect',
    'getactivity',
    'getclass',
    'getcollidemodel',
    'getcollision',
    'getdata',
    'getmaps',
    'getmodel',
    'getnodes',
    'getsession',
    'getsound',
    'gettexture',
    'HitMessage',
    'hscrollwidget',
    'imagewidget',
    'ImpactDamageMessage',
    'in_logic_thread',
    'InputDevice',
    'InputDeviceNotFoundError',
    'InputType',
    'IntChoiceSetting',
    'IntSetting',
    'is_browser_likely_available',
    'is_point_in_box',
    'Keyboard',
    'LanguageSubsystem',
    'Level',
    'Lobby',
    'Lstr',
    'Map',
    'Material',
    'MetadataSubsystem',
    'Model',
    'MultiTeamSession',
    'MusicPlayer',
    'MusicPlayMode',
    'MusicSubsystem',
    'MusicType',
    'newactivity',
    'newnode',
    'Node',
    'NodeActor',
    'NodeNotFoundError',
    'normalized_color',
    'NotFoundError',
    'open_url',
    'OutOfBoundsMessage',
    'Permission',
    'PickedUpMessage',
    'PickUpMessage',
    'Player',
    'PlayerDiedMessage',
    'PlayerInfo',
    'PlayerNotFoundError',
    'PlayerRecord',
    'PlayerScoredMessage',
    'playsound',
    'Plugin',
    'PluginSubsystem',
    'PotentialPlugin',
    'PowerupAcceptMessage',
    'PowerupMessage',
    'print_error',
    'print_exception',
    'printnodes',
    'ls_objects',
    'ls_input_devices',
    'pushcall',
    'quit',
    'rowwidget',
    'safecolor',
    'ScoreConfig',
    'ScoreType',
    'screenmessage',
    'scrollwidget',
    'ServerController',
    'Session',
    'SessionNotFoundError',
    'SessionPlayer',
    'SessionPlayerNotFoundError',
    'SessionTeam',
    'SessionTeamNotFoundError',
    'set_analytics_screen',
    'setmusic',
    'Setting',
    'ShouldShatterMessage',
    'show_damage_count',
    'Sound',
    'SpecialChar',
    'StandLocation',
    'StandMessage',
    'Stats',
    'storagename',
    'Team',
    'TeamGameActivity',
    'TeamNotFoundError',
    'Texture',
    'textwidget',
    'ThawMessage',
    'time',
    'TimeFormat',
    'Timer',
    'timer',
    'timestring',
    'TimeType',
    'uicleanupcheck',
    'UIController',
    'UIScale',
    'UISubsystem',
    'UNHANDLED',
    'Vec3',
    'vec3validate',
    'verify_object_death',
    'WeakCall',
    'Widget',
    'widget',
    'WidgetNotFoundError',
    'Window',
]


# Have these things present themselves cleanly as 'ba.Foo'
# instead of 'ba._submodule.Foo'
def _simplify_module_names() -> None:
    import os

    # Though pdoc gets confused when we override __module__,
    # so let's make an exception for it.
    if os.environ.get('BA_DOCS_GENERATION', '0') != '1':
        from efro.util import set_canonical_module

        globs = globals()
        set_canonical_module(
            module_globals=globs,
            names=[n for n in globs.keys() if not n.startswith('_')],
        )


_simplify_module_names()
del _simplify_module_names
