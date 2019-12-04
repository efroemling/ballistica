# Copyright (c) 2011-2019 Eric Froemling
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
"""Defines AppDelegate class for handling high level app functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Type, Optional, Any, Dict, Callable
    import ba


class AppDelegate:
    """Defines handlers for high level app functionality."""

    def create_default_game_config_ui(
        self, gameclass: Type[ba.GameActivity], sessionclass: Type[ba.Session],
        config: Optional[Dict[str, Any]],
        completion_call: Callable[[Optional[Dict[str, Any]]], None]
    ) -> None:
        """Launch a UI to configure the given game config.

        It should manipulate the contents of config and call completion_call
        when done.
        """
        del gameclass, sessionclass, config, completion_call  # unused
        from ba import _error
        _error.print_error(
            "create_default_game_config_ui needs to be overridden")
