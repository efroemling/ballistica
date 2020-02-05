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
"""Provides UI for testing vr settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.ui.settings import testing

if TYPE_CHECKING:
    from typing import Any, Dict, List


class VRTestingWindow(testing.TestingWindow):
    """Window for testing vr settings."""

    def __init__(self, transition: str = 'in_right'):

        entries: List[Dict[str, Any]] = []
        app = ba.app
        # these are gear-vr only
        if app.platform == 'android' and app.subplatform == 'oculus':
            entries += [
                {
                    'name': 'timeWarpDebug',
                    'label': 'Time Warp Debug',
                    'increment': 1.0
                },
                {
                    'name': 'chromaticAberrationCorrection',
                    'label': 'Chromatic Aberration Correction',
                    'increment': 1.0
                },
                {
                    'name': 'vrMinimumVSyncs',
                    'label': 'Minimum Vsyncs',
                    'increment': 1.0
                },
                # {'name':'eyeOffsX','label':'Eye IPD','increment':0.001}
            ]
        # cardboard/gearvr get eye offset controls..
        # if app.platform == 'android':
        #     entries += [
        #         {'name':'eyeOffsY','label':'Eye Offset Y','increment':0.01},
        #         {'name':'eyeOffsZ','label':'Eye Offset Z','increment':0.005}]
        # everyone gets head-scale
        entries += [{
            'name': 'headScale',
            'label': 'Head Scale',
            'increment': 1.0
        }]
        # and everyone gets all these..
        entries += [
            {
                'name': 'vrCamOffsetY',
                'label': 'In-Game Cam Offset Y',
                'increment': 0.1
            },
            {
                'name': 'vrCamOffsetZ',
                'label': 'In-Game Cam Offset Z',
                'increment': 0.1
            },
            {
                'name': 'vrOverlayScale',
                'label': 'Overlay Scale',
                'increment': 0.025
            },
            {
                'name': 'allowCameraMovement',
                'label': 'Allow Camera Movement',
                'increment': 1.0
            },
            {
                'name': 'cameraPanSpeedScale',
                'label': 'Camera Movement Speed',
                'increment': 0.1
            },
            {
                'name': 'showOverlayBounds',
                'label': 'Show Overlay Bounds',
                'increment': 1
            },
        ]

        super().__init__(
            ba.Lstr(resource='settingsWindowAdvanced.vrTestingText'), entries,
            transition)
