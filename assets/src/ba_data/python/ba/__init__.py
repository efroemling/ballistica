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
"""The public face of Ballistica.

This top level module is a collection of most commonly used functionality.
For many modding purposes, the bits exposed here are all you'll need.
In some specific cases you may need to pull in individual submodules instead.
"""
# pylint: disable=unused-import
# pylint: disable=redefined-builtin

from _ba import (CollideModel, Context, ContextCall, Data, InputDevice,
                 Material, Model, Node, SessionPlayer, Sound, Texture, Timer,
                 Vec3, Widget, buttonwidget, camerashake, checkboxwidget,
                 columnwidget, containerwidget, do_once, emitfx, getactivity,
                 getcollidemodel, getmodel, getnodes, getsession, getsound,
                 gettexture, hscrollwidget, imagewidget, log, newactivity,
                 newnode, playsound, printnodes, printobjects, pushcall, quit,
                 rowwidget, safecolor, screenmessage, scrollwidget,
                 set_analytics_screen, charstr, textwidget, time, timer,
                 open_url, widget)
from ba._activity import Activity
from ba._plugin import PotentialPlugin, Plugin
from ba._actor import Actor
from ba._player import PlayerInfo, Player, EmptyPlayer, StandLocation
from ba._nodeactor import NodeActor
from ba._app import App
from ba._coopgame import CoopGameActivity
from ba._coopsession import CoopSession
from ba._dependency import (Dependency, DependencyComponent, DependencySet,
                            AssetPackage)
from ba._enums import (TimeType, Permission, TimeFormat, SpecialChar,
                       InputType, UIScale)
from ba._error import (
    print_exception, print_error, ContextError, NotFoundError,
    PlayerNotFoundError, SessionPlayerNotFoundError, NodeNotFoundError,
    ActorNotFoundError, InputDeviceNotFoundError, WidgetNotFoundError,
    ActivityNotFoundError, TeamNotFoundError, SessionTeamNotFoundError,
    SessionNotFoundError, DelegateNotFoundError, DependencyError)
from ba._freeforallsession import FreeForAllSession
from ba._gameactivity import GameActivity
from ba._gameresults import GameResults
from ba._settings import (Setting, IntSetting, FloatSetting, ChoiceSetting,
                          BoolSetting, IntChoiceSetting, FloatChoiceSetting)
from ba._lang import Lstr, setlanguage, get_valid_languages
from ba._map import Map, getmaps
from ba._session import Session
from ba._servermode import ServerController
from ba._score import ScoreType, ScoreConfig
from ba._stats import PlayerScoredMessage, PlayerRecord, Stats
from ba._team import SessionTeam, Team, EmptyTeam
from ba._teamgame import TeamGameActivity
from ba._dualteamsession import DualTeamSession
from ba._achievement import Achievement
from ba._appconfig import AppConfig
from ba._appdelegate import AppDelegate
from ba._apputils import is_browser_likely_available
from ba._campaign import Campaign
from ba._gameutils import (GameTip, animate, animate_array, show_damage_count,
                           timestring, cameraflash)
from ba._general import (WeakCall, Call, existing, Existable,
                         verify_object_death, storagename)
from ba._level import Level
from ba._lobby import Lobby, Chooser
from ba._math import normalized_color, is_point_in_box, vec3validate
from ba._messages import (UNHANDLED, OutOfBoundsMessage, DeathType, DieMessage,
                          PlayerDiedMessage, StandMessage, PickUpMessage,
                          DropMessage, PickedUpMessage, DroppedMessage,
                          ShouldShatterMessage, ImpactDamageMessage,
                          FreezeMessage, ThawMessage, HitMessage,
                          CelebrateMessage)
from ba._music import setmusic, MusicPlayer, MusicType, MusicPlayMode
from ba._powerup import PowerupMessage, PowerupAcceptMessage
from ba._multiteamsession import MultiTeamSession
from ba.ui import Window, UIController, uicleanupcheck
from ba._collision import Collision, getcollision

app: App


# Change everything's listed module to simply 'ba' (instead of 'ba.foo.bar').
def _simplify_module_names() -> None:
    for attr, obj in globals().items():
        if not attr.startswith('_'):
            if getattr(obj, '__module__', None) not in [None, 'ba']:
                obj.__module__ = 'ba'


_simplify_module_names()
del _simplify_module_names
