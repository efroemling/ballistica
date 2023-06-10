# Released under the MIT License. See LICENSE for details.
#
"""Ballistica UI Version 1"""

# ba_meta require api 8

# The stuff we expose here at the top level is our 'public' api.
# It should only be imported by code outside of this package or
# from 'if TYPE_CHECKING' blocks (which will not exec at runtime).
# Code within our package should import things directly from their
# submodules.

from __future__ import annotations

# pylint: disable=redefined-builtin

import logging

from efro.util import set_canonical_module_names


from babase import (
    get_display_resolution,
    get_max_graphics_quality,
    add_clean_frame_callback,
    has_gamma_control,
    get_string_width,
    get_string_height,
    set_analytics_screen,
    is_xcode_build,
    get_low_level_config_value,
    set_low_level_config_value,
    have_permission,
    request_permission,
    workspaces_in_use,
    increment_analytics_count,
    get_replays_dir,
    is_running_on_fire_tv,
    set_ui_input_device,
    fade_screen,
    apptime,
    apptimer,
    AppTimer,
    displaytime,
    displaytimer,
    DisplayTimer,
    in_logic_thread,
    appname,
    appnameupper,
    clipboard_set_text,
    clipboard_is_supported,
    lock_all_input,
    unlock_all_input,
    safecolor,
    quit,
    charstr,
    pushcall,
    ContextRef,
    app,
    AppIntent,
    AppIntentDefault,
    AppIntentExec,
    AppMode,
    Call,
    WeakCall,
    AppTime,
    DisplayTime,
    screenmessage,
    Lstr,
    PotentialPlugin,
    Plugin,
    do_once,
    Keyboard,
    commit_app_config,
    get_ip_address_type,
    getclass,
    get_type_name,
)
from babase._apputils import get_remote_app_name, is_browser_likely_available
from babase._login import LoginAdapter


from babase._error import NotFoundError

from babase._mgen.enums import (
    Permission,
    UIScale,
    SpecialChar,
)
from babase._text import timestring

from _bauiv1 import (
    uibounds,
    set_party_window_open,
    get_qrcode_texture,
    is_party_icon_visible,
    set_party_icon_always_visible,
    open_url,
    have_incentivized_ad,
    has_video_ads,
    get_special_widget,
    open_file_externally,
    Sound,
    getsound,
    Texture,
    gettexture,
    Mesh,
    getmesh,
    checkboxwidget,
    columnwidget,
    imagewidget,
    buttonwidget,
    containerwidget,
    rowwidget,
    scrollwidget,
    textwidget,
    hscrollwidget,
    Widget,
    widget,
)
from bauiv1._uitypes import Window, uicleanupcheck
from bauiv1._subsystem import UIV1Subsystem


__all__ = [
    'lock_all_input',
    'unlock_all_input',
    'get_qrcode_texture',
    'get_replays_dir',
    'fade_screen',
    'increment_analytics_count',
    'workspaces_in_use',
    'appname',
    'is_party_icon_visible',
    'LoginAdapter',
    'safecolor',
    'is_browser_likely_available',
    'NotFoundError',
    'set_party_icon_always_visible',
    'get_remote_app_name',
    'appnameupper',
    'open_url',
    'Permission',
    'request_permission',
    'have_permission',
    'get_low_level_config_value',
    'set_low_level_config_value',
    'is_xcode_build',
    'apptime',
    'set_analytics_screen',
    'have_incentivized_ad',
    'has_video_ads',
    'timestring',
    'get_string_width',
    'get_string_height',
    'get_special_widget',
    'has_gamma_control',
    'WeakCall',
    'apptimer',
    'pushcall',
    'PotentialPlugin',
    'Plugin',
    'screenmessage',
    'SpecialChar',
    'charstr',
    'UIScale',
    'uicleanupcheck',
    'Lstr',
    'app',
    'Call',
    'widget',
    'Window',
    'Sound',
    'getsound',
    'Texture',
    'gettexture',
    'Mesh',
    'getmesh',
    'checkboxwidget',
    'columnwidget',
    'imagewidget',
    'buttonwidget',
    'containerwidget',
    'rowwidget',
    'scrollwidget',
    'textwidget',
    'hscrollwidget',
    'Widget',
    'getclass',
    'get_type_name',
    'get_ip_address_type',
    'do_once',
    'Keyboard',
    'clipboard_is_supported',
    'clipboard_set_text',
    'set_ui_input_device',
    'set_party_window_open',
    'add_clean_frame_callback',
    'in_logic_thread',
    'open_file_externally',
    'appnameupper',
    'commit_app_config',
    'quit',
    'get_display_resolution',
    'get_max_graphics_quality',
    'is_running_on_fire_tv',
    'AppTime',
    'AppTimer',
    'ContextRef',
    'displaytime',
    'DisplayTime',
    'displaytimer',
    'DisplayTimer',
    'uibounds',
    'AppIntent',
    'AppIntentDefault',
    'AppIntentExec',
    'AppMode',
    'UIV1Subsystem',
]

# We want stuff to show up as bauiv1.Foo instead of bauiv1._sub.Foo.
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
