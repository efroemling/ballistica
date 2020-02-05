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
