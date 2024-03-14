# Released under the MIT License. See LICENSE for details.
#
"""Input related functionality"""
from __future__ import annotations

from typing import TYPE_CHECKING
import logging

import babase

if TYPE_CHECKING:
    from typing import Any


def get_input_device_mapped_value(
    devicename: str,
    unique_id: str,
    name: str,
    default: bool = False,
) -> Any:
    """Returns a mapped value for an input device.

    This checks the user config and falls back to default values
    where available.
    """
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches

    app = babase.app
    assert app.classic is not None
    useragentstring = app.classic.legacy_user_agent_string
    platform = app.classic.platform
    subplatform = app.classic.subplatform
    appconfig = babase.app.config

    # If there's an entry in our config for this controller and
    # we're not looking for our default mappings, use it.
    if 'Controllers' in appconfig and not default:
        ccfgs = appconfig['Controllers']
        if devicename in ccfgs:
            mapping = None
            if unique_id in ccfgs[devicename]:
                mapping = ccfgs[devicename][unique_id]
            elif 'default' in ccfgs[devicename]:
                mapping = ccfgs[devicename]['default']

            # We now use the config mapping *only* if it is not empty.
            # There have been cases of config writing code messing up
            # and leaving empty dicts in the app config, which currently
            # leaves the device unusable. Alternatively, we'd perhaps
            # want to fall back to defaults for individual missing
            # values, but that is a bigger change we can make later.
            if isinstance(mapping, dict) and mapping:
                return mapping.get(name, -1)

    if platform == 'windows':
        # XInput (hopefully this mapping is consistent?...)
        if devicename.startswith('XInput Controller'):
            return {
                'triggerRun2': 3,
                'unassignedButtonsRun': False,
                'buttonPickUp': 4,
                'buttonBomb': 2,
                'buttonStart': 8,
                'buttonIgnored2': 7,
                'triggerRun1': 6,
                'buttonPunch': 3,
                'buttonRun2': 5,
                'buttonRun1': 6,
                'buttonJump': 1,
                'buttonIgnored': 11,
            }.get(name, -1)

        # Ps4 controller.
        if devicename == 'Wireless Controller':
            return {
                'triggerRun2': 4,
                'unassignedButtonsRun': False,
                'buttonPickUp': 4,
                'buttonBomb': 3,
                'buttonJump': 2,
                'buttonStart': 10,
                'buttonPunch': 1,
                'buttonRun2': 5,
                'buttonRun1': 6,
                'triggerRun1': 5,
            }.get(name, -1)

    elif 'NVIDIA SHIELD;' in useragentstring:
        if 'NVIDIA Controller' in devicename:
            return {
                'triggerRun2': 19,
                'triggerRun1': 18,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'analogStickDeadZone': 0.0,
                'buttonStart': 109,
                'buttonPunch': 100,
                'buttonIgnored': 184,
                'buttonIgnored2': 86,
            }.get(name, -1)

    default_android_mapping = {
        'triggerRun2': 19,
        'unassignedButtonsRun': False,
        'buttonPickUp': 101,
        'buttonBomb': 98,
        'buttonJump': 97,
        'buttonStart': 83,
        'buttonStart2': 109,
        'buttonPunch': 100,
        'buttonRun2': 104,
        'buttonRun1': 103,
        'triggerRun1': 18,
        'buttonLeft': 22,
        'buttonRight': 23,
        'buttonUp': 20,
        'buttonDown': 21,
        'buttonVRReorient': 110,
    }

    # Generic android...
    if platform == 'android':
        if devicename in ['Amazon Fire Game Controller']:
            return {
                'triggerRun2': 23,
                'unassignedButtonsRun': False,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'analogStickDeadZone': 0.0,
                'startButtonActivatesDefaultWidget': False,
                'buttonStart': 83,
                'buttonPunch': 100,
                'buttonRun2': 103,
                'buttonRun1': 104,
                'triggerRun1': 24,
            }.get(name, -1)
        if devicename in [
            'Amazon Remote',
            'Amazon Bluetooth Dev',
            'Amazon Fire TV Remote',
        ]:
            return {
                'triggerRun2': 23,
                'triggerRun1': 24,
                'buttonPickUp': 24,
                'buttonBomb': 91,
                'buttonJump': 86,
                'buttonUp': 20,
                'buttonLeft': 22,
                'startButtonActivatesDefaultWidget': False,
                'buttonRight': 23,
                'buttonStart': 83,
                'buttonPunch': 90,
                'buttonDown': 21,
            }.get(name, -1)

        # Steelseries stratus xl.
        if devicename == 'SteelSeries Stratus XL':
            return {
                'triggerRun2': 23,
                'unassignedButtonsRun': False,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'buttonStart': 83,
                'buttonStart2': 109,
                'buttonPunch': 100,
                'buttonRun2': 104,
                'buttonRun1': 103,
                'triggerRun1': 24,
                'buttonLeft': 22,
                'buttonRight': 23,
                'buttonUp': 20,
                'buttonDown': 21,
                'buttonVRReorient': 108,
            }.get(name, -1)

        # Adt-1 gamepad (use funky 'mode' button for start).
        if devicename == 'Gamepad':
            return {
                'triggerRun2': 19,
                'unassignedButtonsRun': False,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'buttonStart': 111,
                'buttonPunch': 100,
                'startButtonActivatesDefaultWidget': False,
                'buttonRun2': 104,
                'buttonRun1': 103,
                'triggerRun1': 18,
            }.get(name, -1)
        # Nexus player remote.
        if devicename == 'Nexus Remote':
            return {
                'triggerRun2': 19,
                'unassignedButtonsRun': False,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'buttonUp': 20,
                'buttonLeft': 22,
                'buttonDown': 21,
                'buttonRight': 23,
                'buttonStart': 83,
                'buttonStart2': 109,
                'buttonPunch': 24,
                'buttonRun2': 104,
                'buttonRun1': 103,
                'triggerRun1': 18,
            }.get(name, -1)

        if devicename == 'virtual-remote':
            return {
                'triggerRun2': 19,
                'unassignedButtonsRun': False,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonStart': 83,
                'buttonJump': 24,
                'buttonUp': 20,
                'buttonLeft': 22,
                'buttonRight': 23,
                'triggerRun1': 18,
                'buttonStart2': 109,
                'buttonPunch': 100,
                'buttonRun2': 104,
                'buttonRun1': 103,
                'buttonDown': 21,
                'startButtonActivatesDefaultWidget': False,
                'uiOnly': True,
            }.get(name, -1)

        # Nvidia controller is default, but gets some strange
        # keypresses we want to ignore.. touching the touchpad,
        # so lets ignore those.
        if 'NVIDIA Controller' in devicename:
            return {
                'triggerRun2': 19,
                'unassignedButtonsRun': False,
                'buttonPickUp': 101,
                'buttonIgnored': 126,
                'buttonIgnored2': 1,
                'buttonBomb': 98,
                'buttonJump': 97,
                'buttonStart': 83,
                'buttonStart2': 109,
                'buttonPunch': 100,
                'buttonRun2': 104,
                'buttonRun1': 103,
                'triggerRun1': 18,
            }.get(name, -1)

    # Default keyboard vals across platforms..
    if devicename == 'Keyboard' and unique_id == '#2':
        if platform == 'mac' and subplatform == 'appstore':
            return {
                'buttonJump': 258,
                'buttonPunch': 257,
                'buttonBomb': 262,
                'buttonPickUp': 261,
                'buttonUp': 273,
                'buttonDown': 274,
                'buttonLeft': 276,
                'buttonRight': 275,
                'buttonStart': 263,
            }.get(name, -1)
        return {
            'buttonPickUp': 1073741917,
            'buttonBomb': 1073741918,
            'buttonJump': 1073741914,
            'buttonUp': 1073741906,
            'buttonLeft': 1073741904,
            'buttonRight': 1073741903,
            'buttonStart': 1073741919,
            'buttonPunch': 1073741913,
            'buttonDown': 1073741905,
        }.get(name, -1)
    if devicename == 'Keyboard' and unique_id == '#1':
        return {
            'buttonJump': 107,
            'buttonPunch': 106,
            'buttonBomb': 111,
            'buttonPickUp': 105,
            'buttonUp': 119,
            'buttonDown': 115,
            'buttonLeft': 97,
            'buttonRight': 100,
        }.get(name, -1)

    # Ok, this gamepad's not in our specific preset list; fall back to
    # some (hopefully) reasonable defaults.

    # Reasonable defaults.
    if platform == 'android':
        return default_android_mapping.get(name, -1)

    # Is there a point to any sort of fallbacks here?.. should check.
    return {
        'buttonJump': 1,
        'buttonPunch': 2,
        'buttonBomb': 3,
        'buttonPickUp': 4,
        'buttonStart': 5,
    }.get(name, -1)


def _gen_android_input_hash() -> str:
    import os
    import hashlib

    md5 = hashlib.md5()

    # Currently we just do a single hash of *all* inputs on android and
    # that's it. Good enough. (grabbing mappings for a specific device
    # looks to be non-trivial)
    for dirname in [
        '/system/usr/keylayout',
        '/data/usr/keylayout',
        '/data/system/devices/keylayout',
    ]:
        try:
            if os.path.isdir(dirname):
                for f_name in os.listdir(dirname):
                    # This is usually volume keys and stuff; assume we
                    # can skip it?.. (since it'll vary a lot across
                    # devices)
                    if f_name == 'gpio-keys.kl':
                        continue
                    try:
                        with open(f'{dirname}/{f_name}', 'rb') as infile:
                            md5.update(infile.read())
                    except PermissionError:
                        pass
        except Exception:
            logging.exception('Error in _gen_android_input_hash inner loop.')
    return md5.hexdigest()


def get_input_device_map_hash() -> str:
    """Given an input device, return a hash based on its raw input values.

    This lets us avoid sharing mappings across devices that may
    have the same name but actually produce different input values.
    (Different Android versions, for example, may return different
    key codes for button presses on a given type of controller)
    """
    app = babase.app

    # Currently only using this when classic is present. Need to replace
    # with a modern equivalent.
    if app.classic is not None:
        try:
            if app.classic.input_map_hash is None:
                if app.classic.platform == 'android':
                    app.classic.input_map_hash = _gen_android_input_hash()
                else:
                    app.classic.input_map_hash = ''
            return app.classic.input_map_hash
        except Exception:
            logging.exception('Error in get_input_map_hash.')
            return ''
    return ''


def get_input_device_config(
    name: str, unique_id: str, default: bool
) -> tuple[dict, str]:
    """Given an input device, return its config dict in the app config.

    The dict will be created if it does not exist.
    """
    cfg = babase.app.config
    ccfgs: dict[str, Any] = cfg.setdefault('Controllers', {})
    ccfgs.setdefault(name, {})
    if default:
        if unique_id in ccfgs[name]:
            del ccfgs[name][unique_id]
        if 'default' not in ccfgs[name]:
            ccfgs[name]['default'] = {}
        return ccfgs[name], 'default'
    if unique_id not in ccfgs[name]:
        ccfgs[name][unique_id] = {}
    return ccfgs[name], unique_id
