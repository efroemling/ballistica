"""The public face of Ballistica.

This top level module is a collection of most commonly used functionality.
For many modding purposes, the bits exposed here are all you'll need.
In some specific cases you may need to pull in individual submodules instead.
"""

# pylint: disable=unused-import
# pylint: disable=redefined-builtin

from _ba import (CollideModel, Context, ContextCall, Data, InputDevice,
                 Material, Model, Node, Player, Sound, Texture, Timer, Vec3,
                 Widget, buttonwidget, camerashake, checkboxwidget,
                 columnwidget, containerwidget, do_once, emitfx,
                 get_collision_info, getactivity, getcollidemodel, getmodel,
                 getnodes, getsession, getsound, gettexture, hscrollwidget,
                 imagewidget, log, new_activity, newnode, playsound,
                 printnodes, printobjects, pushcall, quit, rowwidget,
                 safecolor, screenmessage, scrollwidget, set_analytics_screen,
                 charstr, textwidget, time, timer, open_url, widget)
from ba._activity import Activity
from ba._actor import Actor
from ba._app import App
from ba._coopgame import CoopGameActivity
from ba._coopsession import CoopSession
from ba._dep import Dep, Dependency, DepComponent, DepSet, AssetPackage
from ba._enums import TimeType, Permission, TimeFormat, SpecialChar
from ba._error import (UNHANDLED, print_exception, print_error, NotFoundError,
                       PlayerNotFoundError, NodeNotFoundError,
                       ActorNotFoundError, InputDeviceNotFoundError,
                       WidgetNotFoundError, ActivityNotFoundError,
                       TeamNotFoundError, SessionNotFoundError,
                       DependencyError)
from ba._freeforallsession import FreeForAllSession
from ba._gameactivity import GameActivity
from ba._gameresults import TeamGameResults
from ba._lang import Lstr, setlanguage, get_valid_languages
from ba._maps import Map, getmaps
from ba._session import Session
from ba._stats import PlayerScoredMessage, PlayerRecord, Stats
from ba._team import Team
from ba._teamgame import TeamGameActivity
from ba._teamssession import TeamsSession
from ba._achievement import Achievement
from ba._appconfig import AppConfig
from ba._appdelegate import AppDelegate
from ba._apputils import is_browser_likely_available
from ba._campaign import Campaign
from ba._gameutils import (animate, animate_array, show_damage_count,
                           sharedobj, timestring, cameraflash)
from ba._general import WeakCall, Call
from ba._level import Level
from ba._lobby import Lobby, Chooser
from ba._math import normalized_color, is_point_in_box, vec3validate
from ba._messages import (OutOfBoundsMessage, DieMessage, StandMessage,
                          PickUpMessage, DropMessage, PickedUpMessage,
                          DroppedMessage, ShouldShatterMessage,
                          ImpactDamageMessage, FreezeMessage, ThawMessage,
                          HitMessage)
from ba._music import setmusic, MusicPlayer
from ba._powerup import PowerupMessage, PowerupAcceptMessage
from ba._teambasesession import TeamBaseSession
from ba.ui import (OldWindow, UILocation, UILocationWindow, UIController,
                   uicleanupcheck)

app: App


# Change everything's listed module to ba (instead of ba.foo.bar.etc).
def _simplify_module_names() -> None:
    for attr, obj in globals().items():
        if not attr.startswith('_'):
            if getattr(obj, '__module__', None) not in [None, 'ba']:
                obj.__module__ = 'ba'


_simplify_module_names()
del _simplify_module_names
