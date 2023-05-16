# Released under the MIT License. See LICENSE for details.
#
"""The public face of Ballistica.

This top level module is a collection of most commonly used functionality.
For many modding purposes, the bits exposed here are all you'll need.
In some specific cases you may need to pull in individual submodules instead.
"""
# pylint: disable=redefined-builtin

import _babase
from _babase import (
    SimpleSound,
    ContextRef,
    ContextCall,
    apptime,
    apptimer,
    AppTimer,
    displaytime,
    displaytimer,
    DisplayTimer,
    Vec3,
    do_once,
    pushcall,
    quit,
    safecolor,
    set_analytics_screen,
    charstr,
    clipboard_is_supported,
    clipboard_has_text,
    clipboard_get_text,
    clipboard_set_text,
    in_logic_thread,
)

from babase._accountv2 import AccountV2Handle
from babase._plugin import PotentialPlugin, Plugin, PluginSubsystem
from babase._app import App
from babase._cloud import CloudSubsystem
from babase._mgen.enums import (
    Permission,
    SpecialChar,
    InputType,
    UIScale,
)
from babase._error import (
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
    MapNotFoundError,
    SessionTeamNotFoundError,
    SessionNotFoundError,
    DelegateNotFoundError,
)

from babase._language import Lstr, LanguageSubsystem
from babase._appconfig import AppConfig
from babase._apputils import is_browser_likely_available, garbage_collect
from babase._general import (
    DisplayTime,
    AppTime,
    WeakCall,
    Call,
    existing,
    Existable,
    verify_object_death,
    storagename,
    getclass,
)
from babase._keyboard import Keyboard
from babase._math import normalized_color, is_point_in_box, vec3validate
from babase._meta import MetadataSubsystem
from babase._text import timestring

_babase.app = app = App()
app.postinit()

__all__ = [
    'app',
    'AccountV2Handle',
    'ActivityNotFoundError',
    'ActorNotFoundError',
    'app',
    'App',
    'AppConfig',
    'Call',
    'charstr',
    'clipboard_get_text',
    'clipboard_has_text',
    'clipboard_is_supported',
    'clipboard_set_text',
    'ContextCall',
    'ContextError',
    'CloudSubsystem',
    'DelegateNotFoundError',
    'do_once',
    'Existable',
    'existing',
    'garbage_collect',
    'getclass',
    'in_logic_thread',
    'InputDeviceNotFoundError',
    'InputType',
    'is_browser_likely_available',
    'is_point_in_box',
    'Keyboard',
    'LanguageSubsystem',
    'Lstr',
    'MapNotFoundError',
    'MetadataSubsystem',
    'NodeNotFoundError',
    'normalized_color',
    'NotFoundError',
    'Permission',
    'PlayerNotFoundError',
    'Plugin',
    'PluginSubsystem',
    'PotentialPlugin',
    'print_error',
    'print_exception',
    'pushcall',
    'quit',
    'safecolor',
    'SessionNotFoundError',
    'SessionPlayerNotFoundError',
    'SessionTeamNotFoundError',
    'set_analytics_screen',
    'SpecialChar',
    'storagename',
    'TeamNotFoundError',
    'apptime',
    'timestring',
    'UIScale',
    'Vec3',
    'vec3validate',
    'verify_object_death',
    'WeakCall',
    'WidgetNotFoundError',
    'AppTime',
    'apptime',
    'apptimer',
    'AppTimer',
    'SimpleSound',
    'ContextRef',
    'DisplayTime',
    'displaytimer',
    'displaytime',
    'DisplayTimer',
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

# Marker we pop down at the very end so other modules can run sanity
# checks to make sure we aren't importing them reciprocally when they
# import us.
_REACHED_END_OF_MODULE = True
