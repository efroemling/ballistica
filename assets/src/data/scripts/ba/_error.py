"""Error related functionality."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any, List
    import ba


class _UnhandledType:
    pass


# A special value that should be returned from handlemessage()
# functions for unhandled message types.  This may result
# in fallback message types being attempted/etc.
UNHANDLED = _UnhandledType()


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


class NotFoundError(Exception):
    """Exception raised when a referenced object does not exist.

    category: Exception Classes
    """


class PlayerNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Player does not exist.

    category: Exception Classes
    """


class TeamNotFoundError(NotFoundError):
    """Exception raised when an expected ba.Team does not exist.

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


def exc_str() -> str:
    """Returns a tidied up string for the current exception.

    This performs some minor cleanup such as printing paths relative
    to script dirs (full paths are often unwieldy in game installs).
    """
    import traceback
    excstr = traceback.format_exc()
    for path in sys.path:
        excstr = excstr.replace(path + '/', '')
    return excstr


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
            raise Exception("invalid keyword(s)")
    try:
        # If we're only printing once and already have, bail.
        if keywds.get('once', False):
            if not _ba.do_once():
                return

        # Most tracebacks are gonna have ugly long install directories in them;
        # lets strip those out when we can.
        err_str = ' '.join([str(a) for a in args])
        print('ERROR:', err_str)
        _ba.print_context()
        print('PRINTED-FROM:')

        # Basically the output of traceback.print_stack() slightly prettified:
        stackstr = ''.join(traceback.format_stack())
        for path in sys.path:
            stackstr = stackstr.replace(path + '/', '')
        print(stackstr, end='')
        print('EXCEPTION:')

        # Basically the output of traceback.print_exc() slightly prettified:
        excstr = traceback.format_exc()
        for path in sys.path:
            excstr = excstr.replace(path + '/', '')
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

        # Most tracebacks are gonna have ugly long install directories in them;
        # lets strip those out when we can.
        print('ERROR:', err_str)
        _ba.print_context()

        # Basically the output of traceback.print_stack() slightly prettified:
        stackstr = ''.join(traceback.format_stack())
        for path in sys.path:
            stackstr = stackstr.replace(path + '/', '')
        print(stackstr, end='')
    except Exception:
        print('ERROR: exception in ba.print_error():')
        traceback.print_exc()
