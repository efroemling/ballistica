# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations

from baclassic._music import do_play_music
from baclassic._input import get_input_device_mapped_value
from baclassic._chest import (
    CHEST_APPEARANCE_DISPLAY_INFOS,
    CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,
)
from baclassic._hooks import on_engine_did_reset, on_engine_will_reset

# The C++ layer looks for this variable:
values = [
    do_play_music,  # kDoPlayMusicCall
    get_input_device_mapped_value,  # kGetInputDeviceMappedValueCall
    CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,  # kChestAppearanceDisplayInfoDefault
    CHEST_APPEARANCE_DISPLAY_INFOS,  # kChestAppearanceDisplayInfos
    on_engine_will_reset,  # kOnEngineWillResetCall
    on_engine_did_reset,  # kOnEngineDidResetCall
]
