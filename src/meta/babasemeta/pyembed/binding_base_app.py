# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations
from babase import app

# The C++ layer looks for this variable:
values = [
    app,  # kApp
    app.handle_deep_link,  # kAppHandleDeepLinkCall
    app.lang.get_resource,  # kGetResourceCall
    app.lang.translate,  # kTranslateCall
    app.push_apply_app_config,  # kAppPushApplyAppConfigCall
    app.on_native_start,  # kAppOnNativeStartCall
    app.on_native_bootstrapping_complete,  # kAppOnNativeBootstrappingCompleteCall
    app.on_native_suspend,  # kAppOnNativeSuspendCall
    app.on_native_unsuspend,  # kAppOnNativeUnsuspendCall
    app.on_native_shutdown,  # kAppOnNativeShutdownCall
    app.on_native_shutdown_complete,  # kAppOnNativeShutdownCompleteCall
    app.on_native_active_changed,  # kAppOnNativeActiveChangedCall
    app.devconsole.do_refresh_tab,  # kAppDevConsoleDoRefreshTabCall
    app.devconsole.save_tab,  # kAppDevConsoleSaveTabCall
    app.on_screen_size_change,  # kAppOnScreenSizeChangeCall
    app.gc.collect,  # kAppGCCollectCall
]
