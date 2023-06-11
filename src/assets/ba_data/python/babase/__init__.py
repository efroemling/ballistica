# Released under the MIT License. See LICENSE for details.
#
"""The public face of Ballistica.

This top level module is a collection of most commonly used functionality.
For many modding purposes, the bits exposed here are all you'll need.
In some specific cases you may need to pull in individual submodules instead.
"""
# pylint: disable=redefined-builtin

from efro.util import set_canonical_module_names

import _babase
from _babase import (
    music_player_set_volume,
    music_player_play,
    music_player_stop,
    music_player_shutdown,
    mac_music_app_init,
    mac_music_app_get_volume,
    mac_music_app_get_library_source,
    mac_music_app_stop,
    mac_music_app_set_volume,
    mac_music_app_get_playlists,
    mac_music_app_play_playlist,
    set_thread_name,
    show_progress_bar,
    print_load_info,
    reload_media,
    set_stress_testing,
    get_max_graphics_quality,
    add_clean_frame_callback,
    has_gamma_control,
    get_string_width,
    get_string_height,
    get_low_level_config_value,
    set_low_level_config_value,
    request_permission,
    have_permission,
    increment_analytics_count,
    fade_screen,
    env,
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
    screenmessage,
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
    native_stack_trace,
    lock_all_input,
    unlock_all_input,
    appname,
    appnameupper,
    set_ui_input_device,
    is_running_on_fire_tv,
    get_replays_dir,
    workspaces_in_use,
    is_xcode_build,
    get_display_resolution,
)

from babase._login import LoginAdapter
from babase._appconfig import commit_app_config
from babase._appintent import AppIntent, AppIntentDefault, AppIntentExec
from babase._appmode import AppMode
from babase._appsubsystem import AppSubsystem
from babase._accountv2 import AccountV2Handle, AccountV2Subsystem
from babase._plugin import PotentialPlugin, Plugin, PluginSubsystem
from babase._app import App
from babase._cloud import CloudSubsystem
from babase._net import get_ip_address_type

# noinspection PyProtectedMember
# (PyCharm inspection bug?)
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
from babase._apputils import (
    handle_leftover_v1_cloud_log_file,
    is_browser_likely_available,
    garbage_collect,
    get_remote_app_name,
)
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
    get_type_name,
    json_prep,
)
from babase._keyboard import Keyboard
from babase._math import normalized_color, is_point_in_box, vec3validate
from babase._meta import MetadataSubsystem
from babase._text import timestring

_babase.app = app = App()
app.postinit()

__all__ = [
    'set_thread_name',
    'app',
    'AccountV2Handle',
    'AccountV2Subsystem',
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
    'AppIntent',
    'AppIntentDefault',
    'AppIntentExec',
    'AppMode',
    'AppSubsystem',
    'screenmessage',
    'native_stack_trace',
    'env',
    'lock_all_input',
    'unlock_all_input',
    'appname',
    'appnameupper',
    'commit_app_config',
    'get_ip_address_type',
    'get_type_name',
    'fade_screen',
    'set_ui_input_device',
    'is_running_on_fire_tv',
    'get_replays_dir',
    'increment_analytics_count',
    'workspaces_in_use',
    'request_permission',
    'have_permission',
    'get_low_level_config_value',
    'set_low_level_config_value',
    'is_xcode_build',
    'get_string_width',
    'get_string_height',
    'has_gamma_control',
    'add_clean_frame_callback',
    'get_max_graphics_quality',
    'get_display_resolution',
    'LoginAdapter',
    'get_remote_app_name',
    'is_browser_likely_available',
    'json_prep',
    'set_stress_testing',
    'reload_media',
    'print_load_info',
    'show_progress_bar',
    'handle_leftover_v1_cloud_log_file',
    'music_player_set_volume',
    'music_player_play',
    'music_player_stop',
    'music_player_shutdown',
    'mac_music_app_init',
    'mac_music_app_get_volume',
    'mac_music_app_get_library_source',
    'mac_music_app_stop',
    'mac_music_app_set_volume',
    'mac_music_app_get_playlists',
    'mac_music_app_play_playlist',
]

# We want stuff to show up as babase.Foo instead of babase._sub.Foo.
set_canonical_module_names(globals())

# Allow the native layer to wrap a few things up.
_babase.reached_end_of_babase()

# Marker we pop down at the very end so other modules can run sanity
# checks to make sure we aren't importing them reciprocally when they
# import us.
_REACHED_END_OF_MODULE = True
