# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for testing vr settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.ui.settings.testing import TestingWindow

if TYPE_CHECKING:
    from typing import Any


class VRTestingWindow(TestingWindow):
    """Window for testing vr settings."""

    def __init__(self, transition: str = 'in_right'):

        entries: list[dict[str, Any]] = []
        app = ba.app
        # these are gear-vr only
        if app.platform == 'android' and app.subplatform == 'oculus':
            entries += [
                {
                    'name': 'timeWarpDebug',
                    'label': 'Time Warp Debug',
                    'increment': 1.0,
                },
                {
                    'name': 'chromaticAberrationCorrection',
                    'label': 'Chromatic Aberration Correction',
                    'increment': 1.0,
                },
                {
                    'name': 'vrMinimumVSyncs',
                    'label': 'Minimum Vsyncs',
                    'increment': 1.0,
                },
                # {'name':'eyeOffsX','label':'Eye IPD','increment':0.001}
            ]
        # cardboard/gearvr get eye offset controls..
        # if app.platform == 'android':
        #     entries += [
        #         {'name':'eyeOffsY','label':'Eye Offset Y','increment':0.01},
        #         {'name':'eyeOffsZ','label':'Eye Offset Z','increment':0.005}]
        # everyone gets head-scale
        entries += [
            {'name': 'headScale', 'label': 'Head Scale', 'increment': 1.0}
        ]
        # and everyone gets all these..
        entries += [
            {
                'name': 'vrCamOffsetY',
                'label': 'In-Game Cam Offset Y',
                'increment': 0.1,
            },
            {
                'name': 'vrCamOffsetZ',
                'label': 'In-Game Cam Offset Z',
                'increment': 0.1,
            },
            {
                'name': 'vrOverlayScale',
                'label': 'Overlay Scale',
                'increment': 0.025,
            },
            {
                'name': 'allowCameraMovement',
                'label': 'Allow Camera Movement',
                'increment': 1.0,
            },
            {
                'name': 'cameraPanSpeedScale',
                'label': 'Camera Movement Speed',
                'increment': 0.1,
            },
            {
                'name': 'showOverlayBounds',
                'label': 'Show Overlay Bounds',
                'increment': 1,
            },
        ]

        super().__init__(
            ba.Lstr(resource='settingsWindowAdvanced.vrTestingText'),
            entries,
            transition,
        )
