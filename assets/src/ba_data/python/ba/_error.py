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
"""Error related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any, List
    import ba


class DependencyError(Exception):
    """Exception raised when one or more ba.Dependency items are missing.

    category: Exception Classes

    (this will generally be missing assets).
    """

    def __init__(self, deps: List[ba.Dependency]):
        super().__init__()
        self._deps = deps

    @property
    def deps(self) -> List[ba.Dependency]:
        """The list of missing dependencies causing this error."""
        return self._deps


class ContextError(Exception):
    """Exception raised when a call is made in an invalid context.

    category: Exception Classes

    Examples of this include calling UI functions within an Activity context
    or calling scene manipulation functions outside of a game context.
    """


class NotFoundError(Exception):
    """Exception raised when a referenced object does not exist.

    category: Exception Classes
    """


class PlayerNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Player does not exist.

    category: Exception Classes
    """


class SessionPlayerNotFoundError(NotFoundError):
    """Exception raised when an expected ba.SessionPlayer does not exist.

    category: Exception Classes
    """


class TeamNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Team does not exist.

    category: Exception Classes
    """


class DelegateNotFoundError(NotFoundError):
    """Exception raised when an expected delegate object does not exist.

    category: Exception Classes
    """


class SessionTeamNotFoundError(NotFoundError):
    """Exception raised when an expected ba.SessionTeam does not exist.

    category: Exception Classes
    """


class NodeNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Node does not exist.

    category: Exception Classes
    """


class ActorNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Actor does not exist.

    category: Exception Classes
    """


class ActivityNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Activity does not exist.

    category: Exception Classes
    """


class SessionNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Session does not exist.

    category: Exception Classes
    """


class InputDeviceNotFoundError(NotFoundError):
    """Exception raised when an expected ba.InputDevice does not exist.

    category: Exception Classes
    """


class WidgetNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Widget does not exist.

    category: Exception Classes
    """


def print_exception(*args: Any, **keywds: Any) -> None:
    """Print info about an exception along with pertinent context state.

    category: General Utility Functions

    Prints all arguments provided along with various info about the
    current context and the outstanding exception.
    Pass the keyword 'once' as True if you want the call to only happen
    one time from an exact calling location.
    """
    import traceback
    if keywds:
        allowed_keywds = ['once']
        if any(keywd not in allowed_keywds for keywd in keywds):
            raise TypeError('invalid keyword(s)')
    try:
        # If we're only printing once and already have, bail.
        if keywds.get('once', False):
            if not _ba.do_once():
                return

        err_str = ' '.join([str(a) for a in args])
        print('ERROR:', err_str)
        _ba.print_context()
        print('PRINTED-FROM:')

        # Basically the output of traceback.print_stack()
        stackstr = ''.join(traceback.format_stack())
        print(stackstr, end='')
        print('EXCEPTION:')

        # Basically the output of traceback.print_exc()
        excstr = traceback.format_exc()
        print('\n'.join('  ' + l for l in excstr.splitlines()))
    except Exception:
        # I suppose using print_exception here would be a bad idea.
        print('ERROR: exception in ba.print_exception():')
        traceback.print_exc()


def print_error(err_str: str, once: bool = False) -> None:
    """Print info about an error along with pertinent context state.

    category: General Utility Functions

    Prints all positional arguments provided along with various info about the
    current context.
    Pass the keyword 'once' as True if you want the call to only happen
    one time from an exact calling location.
    """
    import traceback
    try:
        # If we're only printing once and already have, bail.
        if once:
            if not _ba.do_once():
                return

        print('ERROR:', err_str)
        _ba.print_context()

        # Basically the output of traceback.print_stack()
        stackstr = ''.join(traceback.format_stack())
        print(stackstr, end='')
    except Exception:
        print('ERROR: exception in ba.print_error():')
        traceback.print_exc()
