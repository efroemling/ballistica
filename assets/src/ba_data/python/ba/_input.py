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
"""Input related functionality"""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any, Dict, Tuple
    import ba


def get_device_value(device: ba.InputDevice, name: str) -> Any:
    """Returns a mapped value for an input device.

    This checks the user config and falls back to default values
    where available.
    """
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    devicename = device.name
    unique_id = device.unique_identifier
    app = _ba.app
    useragentstring = app.user_agent_string
    platform = app.platform
    subplatform = app.subplatform
    appconfig = _ba.app.config

    # If there's an entry in our config for this controller, use it.
    if 'Controllers' in appconfig:
        ccfgs = appconfig['Controllers']
        if devicename in ccfgs:
            mapping = None
            if unique_id in ccfgs[devicename]:
                mapping = ccfgs[devicename][unique_id]
            elif 'default' in ccfgs[devicename]:
                mapping = ccfgs[devicename]['default']
            if mapping is not None:
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
                'buttonIgnored': 11
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
                'triggerRun1': 5
            }.get(name, -1)

    # Look for some exact types.
    if _ba.is_running_on_fire_tv():
        if devicename in ['Thunder', 'Amazon Fire Game Controller']:
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
                'triggerRun1': 24
            }.get(name, -1)
        if devicename == 'NYKO PLAYPAD PRO':
            return {
                'triggerRun2': 23,
                'triggerRun1': 24,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'buttonUp': 20,
                'buttonLeft': 22,
                'buttonRight': 23,
                'buttonStart': 83,
                'buttonPunch': 100,
                'buttonDown': 21
            }.get(name, -1)
        if devicename == 'Logitech Dual Action':
            return {
                'triggerRun2': 23,
                'triggerRun1': 24,
                'buttonPickUp': 98,
                'buttonBomb': 101,
                'buttonJump': 100,
                'buttonStart': 109,
                'buttonPunch': 97
            }.get(name, -1)
        if devicename == 'Xbox 360 Wireless Receiver':
            return {
                'triggerRun2': 23,
                'triggerRun1': 24,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'buttonUp': 20,
                'buttonLeft': 22,
                'buttonRight': 23,
                'buttonStart': 83,
                'buttonPunch': 100,
                'buttonDown': 21
            }.get(name, -1)
        if devicename == 'Microsoft X-Box 360 pad':
            return {
                'triggerRun2': 23,
                'triggerRun1': 24,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'buttonStart': 83,
                'buttonPunch': 100
            }.get(name, -1)
        if devicename in [
                'Amazon Remote', 'Amazon Bluetooth Dev',
                'Amazon Fire TV Remote'
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
                'buttonDown': 21
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
                'buttonIgnored2': 86
            }.get(name, -1)
    elif platform == 'mac':
        if devicename == 'PLAYSTATION(R)3 Controller':
            return {
                'buttonLeft': 8,
                'buttonUp': 5,
                'buttonRight': 6,
                'buttonDown': 7,
                'buttonJump': 15,
                'buttonPunch': 16,
                'buttonBomb': 14,
                'buttonPickUp': 13,
                'buttonStart': 4,
                'buttonIgnored': 17
            }.get(name, -1)
        if devicename in ['Wireless 360 Controller', 'Controller']:

            # Xbox360 gamepads
            return {
                'analogStickDeadZone': 1.2,
                'buttonBomb': 13,
                'buttonDown': 2,
                'buttonJump': 12,
                'buttonLeft': 3,
                'buttonPickUp': 15,
                'buttonPunch': 14,
                'buttonRight': 4,
                'buttonStart': 5,
                'buttonUp': 1,
                'triggerRun1': 5,
                'triggerRun2': 6,
                'buttonIgnored': 11
            }.get(name, -1)
        if (devicename
                in ['Logitech Dual Action', 'Logitech Cordless RumblePad 2']):
            return {
                'buttonJump': 2,
                'buttonPunch': 1,
                'buttonBomb': 3,
                'buttonPickUp': 4,
                'buttonStart': 10
            }.get(name, -1)

        # Old gravis gamepad.
        if devicename == 'GamePad Pro USB ':
            return {
                'buttonJump': 2,
                'buttonPunch': 1,
                'buttonBomb': 3,
                'buttonPickUp': 4,
                'buttonStart': 10
            }.get(name, -1)

        if devicename == 'Microsoft SideWinder Plug & Play Game Pad':
            return {
                'buttonJump': 1,
                'buttonPunch': 3,
                'buttonBomb': 2,
                'buttonPickUp': 4,
                'buttonStart': 6
            }.get(name, -1)

        # Saitek P2500 Rumble Force Pad.. (hopefully works for others too?..)
        if devicename == 'Saitek P2500 Rumble Force Pad':
            return {
                'buttonJump': 3,
                'buttonPunch': 1,
                'buttonBomb': 4,
                'buttonPickUp': 2,
                'buttonStart': 11
            }.get(name, -1)

        # Some crazy 'Senze' dual gamepad.
        if devicename == 'Twin USB Joystick':
            return {
                'analogStickLR': 3,
                'analogStickLR_B': 7,
                'analogStickUD': 4,
                'analogStickUD_B': 8,
                'buttonBomb': 2,
                'buttonBomb_B': 14,
                'buttonJump': 3,
                'buttonJump_B': 15,
                'buttonPickUp': 1,
                'buttonPickUp_B': 13,
                'buttonPunch': 4,
                'buttonPunch_B': 16,
                'buttonRun1': 7,
                'buttonRun1_B': 19,
                'buttonRun2': 8,
                'buttonRun2_B': 20,
                'buttonStart': 10,
                'buttonStart_B': 22,
                'enableSecondary': 1,
                'unassignedButtonsRun': False
            }.get(name, -1)
        if devicename == 'USB Gamepad ':  # some weird 'JITE' gamepad
            return {
                'analogStickLR': 4,
                'analogStickUD': 5,
                'buttonJump': 3,
                'buttonPunch': 4,
                'buttonBomb': 2,
                'buttonPickUp': 1,
                'buttonStart': 10
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
        'buttonVRReorient': 110
    }

    # Generic android...
    if platform == 'android':

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
                'buttonVRReorient': 108
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
                'triggerRun1': 18
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
                'triggerRun1': 18
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
                'uiOnly': True
            }.get(name, -1)

        # flag particular gamepads to use exact android defaults..
        # (so they don't even ask to configure themselves)
        if devicename in ['Samsung Game Pad EI-GP20', 'ASUS Gamepad'
                          ] or devicename.startswith('Freefly VR Glide'):
            return default_android_mapping.get(name, -1)

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
                'triggerRun1': 18
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
                'buttonStart': 263
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
            'buttonDown': 1073741905
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
            'buttonRight': 100
        }.get(name, -1)

    # Ok, this gamepad's not in our specific preset list;
    # fall back to some (hopefully) reasonable defaults.

    # Leaving these in here for now but not gonna add any more now that we have
    # fancy-pants config sharing across the internet.
    if platform == 'mac':
        if 'PLAYSTATION' in devicename:  # ps3 gamepad?..
            return {
                'buttonLeft': 8,
                'buttonUp': 5,
                'buttonRight': 6,
                'buttonDown': 7,
                'buttonJump': 15,
                'buttonPunch': 16,
                'buttonBomb': 14,
                'buttonPickUp': 13,
                'buttonStart': 4
            }.get(name, -1)

        # Dual Action Config - hopefully applies to more...
        if 'Logitech' in devicename:
            return {
                'buttonJump': 2,
                'buttonPunch': 1,
                'buttonBomb': 3,
                'buttonPickUp': 4,
                'buttonStart': 10
            }.get(name, -1)

        # Saitek P2500 Rumble Force Pad.. (hopefully works for others too?..)
        if 'Saitek' in devicename:
            return {
                'buttonJump': 3,
                'buttonPunch': 1,
                'buttonBomb': 4,
                'buttonPickUp': 2,
                'buttonStart': 11
            }.get(name, -1)

        # Gravis stuff?...
        if 'GamePad' in devicename:
            return {
                'buttonJump': 2,
                'buttonPunch': 1,
                'buttonBomb': 3,
                'buttonPickUp': 4,
                'buttonStart': 10
            }.get(name, -1)

    # Reasonable defaults.
    if platform == 'android':
        if _ba.is_running_on_fire_tv():

            # Mostly same as default firetv controller.
            return {
                'triggerRun2': 23,
                'triggerRun1': 24,
                'buttonPickUp': 101,
                'buttonBomb': 98,
                'buttonJump': 97,
                'buttonStart': 83,
                'buttonPunch': 100,
                'buttonDown': 21,
                'buttonUp': 20,
                'buttonLeft': 22,
                'buttonRight': 23,
                'startButtonActivatesDefaultWidget': False,
            }.get(name, -1)

        # Mostly same as 'Gamepad' except with 'menu' for default start
        # button instead of 'mode'.
        return default_android_mapping.get(name, -1)

    # Is there a point to any sort of fallbacks here?.. should check.
    return {
        'buttonJump': 1,
        'buttonPunch': 2,
        'buttonBomb': 3,
        'buttonPickUp': 4,
        'buttonStart': 5
    }.get(name, -1)


def _gen_android_input_hash() -> str:
    import os
    import hashlib
    md5 = hashlib.md5()

    # Currently we just do a single hash of *all* inputs on android
    # and that's it.. good enough.
    # (grabbing mappings for a specific device looks to be non-trivial)
    for dirname in [
            '/system/usr/keylayout', '/data/usr/keylayout',
            '/data/system/devices/keylayout'
    ]:
        try:
            if os.path.isdir(dirname):
                for f_name in os.listdir(dirname):
                    # This is usually volume keys and stuff;
                    # assume we can skip it?..
                    # (since it'll vary a lot across devices)
                    if f_name == 'gpio-keys.kl':
                        continue
                    try:
                        with open(f'{dirname}/{f_name}', 'rb') as infile:
                            md5.update(infile.read())
                    except PermissionError:
                        pass
        except Exception:
            from ba import _error
            _error.print_exception(
                'error in _gen_android_input_hash inner loop')
    return md5.hexdigest()


def get_input_map_hash(inputdevice: ba.InputDevice) -> str:
    """Given an input device, return a hash based on its raw input values.

    This lets us avoid sharing mappings across devices that may
    have the same name but actually produce different input values.
    (Different Android versions, for example, may return different
    key codes for button presses on a given type of controller)
    """
    del inputdevice  # Currently unused.
    app = _ba.app
    try:
        if app.input_map_hash is None:
            if app.platform == 'android':
                app.input_map_hash = _gen_android_input_hash()
            else:
                app.input_map_hash = ''
        return app.input_map_hash
    except Exception:
        from ba import _error
        _error.print_exception('Exception in get_input_map_hash')
        return ''


def get_input_device_config(device: ba.InputDevice,
                            default: bool) -> Tuple[Dict, str]:
    """Given an input device, return its config dict in the app config.

    The dict will be created if it does not exist.
    """
    cfg = _ba.app.config
    name = device.name
    ccfgs: Dict[str, Any] = cfg.setdefault('Controllers', {})
    ccfgs.setdefault(name, {})
    unique_id = device.unique_identifier
    if default:
        if unique_id in ccfgs[name]:
            del ccfgs[name][unique_id]
        if 'default' not in ccfgs[name]:
            ccfgs[name]['default'] = {}
        return ccfgs[name], 'default'
    if unique_id not in ccfgs[name]:
        ccfgs[name][unique_id] = {}
    return ccfgs[name], unique_id


def get_last_player_name_from_input_device(device: ba.InputDevice) -> str:
    """Return a reasonable player name associated with a device.

    (generally the last one used there)
    """
    appconfig = _ba.app.config

    # Look for a default player profile name for them;
    # otherwise default to their current random name.
    profilename = '_random'
    key_name = device.name + ' ' + device.unique_identifier
    if ('Default Player Profiles' in appconfig
            and key_name in appconfig['Default Player Profiles']):
        profilename = appconfig['Default Player Profiles'][key_name]
    if profilename == '_random':
        profilename = device.get_default_player_name()
    if profilename == '__account__':
        profilename = _ba.get_account_display_string()
    return profilename
