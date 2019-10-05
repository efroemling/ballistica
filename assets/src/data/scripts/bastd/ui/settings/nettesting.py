"""Provides ui for network related testing."""

from __future__ import annotations

import ba
from bastd.ui.settings import testing


class NetTestingWindow(testing.TestingWindow):
    """Window to test network related settings."""

    def __init__(self, transition: str = 'in_right'):

        entries = [
            {
                'name': 'bufferTime',
                'label': 'Buffer Time',
                'increment': 1.0
            },
            {
                'name': 'delaySampling',
                'label': 'Delay Sampling',
                'increment': 1.0
            },
            {
                'name': 'dynamicsSyncTime',
                'label': 'Dynamics Sync Time',
                'increment': 10
            },
            {
                'name': 'showNetInfo',
                'label': 'Show Net Info',
                'increment': 1
            },
        ]
        testing.TestingWindow.__init__(
            self, ba.Lstr(resource='settingsWindowAdvanced.netTestingText'),
            entries, transition)
