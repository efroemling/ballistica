# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations

from baclassic._music import do_play_music
from baclassic._input import get_input_device_mapped_value

# The C++ layer looks for this variable:
values = [
    do_play_music,  # kDoPlayMusicCall
    get_input_device_mapped_value,  # kGetInputDeviceMappedValueCall
]
