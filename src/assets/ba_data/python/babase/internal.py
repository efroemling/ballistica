# Released under the MIT License. See LICENSE for details.
#
"""Exposed functionality not intended for full public use.

Classes and functions contained here, while technically 'public', may change
or disappear without warning, so should be avoided (or used sparingly and
defensively).
"""
from __future__ import annotations

from _babase import (
    add_clean_frame_callback,
    increment_analytics_count,
    get_string_height,
    get_string_width,
    appnameupper,
    appname,
    workspaces_in_use,
    charstr,
    have_permission,
    request_permission,
    is_xcode_build,
    set_low_level_config_value,
    get_low_level_config_value,
    has_gamma_control,
    get_max_graphics_quality,
    get_display_resolution,
    is_running_on_fire_tv,
    android_get_external_files_dir,
    get_replays_dir,
)

from babase._login import LoginAdapter
from babase._appconfig import commit_app_config
from babase._general import getclass, json_prep, get_type_name
from babase._apputils import (
    is_browser_likely_available,
    get_remote_app_name,
    should_submit_debug_info,
    dump_app_state,
    log_dumped_app_state,
)
from babase._net import (
    get_ip_address_type,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
)

__all__ = [
    'LoginAdapter',
    'add_clean_frame_callback',
    'increment_analytics_count',
    'get_string_height',
    'get_string_width',
    'appnameupper',
    'appname',
    'workspaces_in_use',
    'charstr',
    'have_permission',
    'request_permission',
    'is_xcode_build',
    'set_low_level_config_value',
    'get_low_level_config_value',
    'has_gamma_control',
    'get_max_graphics_quality',
    'get_display_resolution',
    'is_running_on_fire_tv',
    'android_get_external_files_dir',
    'get_replays_dir',
    'commit_app_config',
    'getclass',
    'json_prep',
    'get_type_name',
    'is_browser_likely_available',
    'get_remote_app_name',
    'should_submit_debug_info',
    'get_ip_address_type',
    'DEFAULT_REQUEST_TIMEOUT_SECONDS',
    'dump_app_state',
    'log_dumped_app_state',
]
