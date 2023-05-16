# Released under the MIT License. See LICENSE for details.
#
"""Error related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from typing import Any


class ContextError(Exception):
    """Exception raised when a call is made in an invalid context.

    Category: **Exception Classes**

    Examples of this include calling UI functions within an Activity context
    or calling scene manipulation functions outside of a game context.
    """


class NotFoundError(Exception):
    """Exception raised when a referenced object does not exist.

    Category: **Exception Classes**
    """


class PlayerNotFoundError(NotFoundError):
    """Exception raised when an expected player does not exist.

    Category: **Exception Classes**
    """


class SessionPlayerNotFoundError(NotFoundError):
    """Exception raised when an expected session-player does not exist.

    Category: **Exception Classes**
    """


class TeamNotFoundError(NotFoundError):
    """Exception raised when an expected bascenev1.Team does not exist.

    Category: **Exception Classes**
    """


class MapNotFoundError(NotFoundError):
    """Exception raised when an expected bascenev1.Map does not exist.

    Category: **Exception Classes**
    """


class DelegateNotFoundError(NotFoundError):
    """Exception raised when an expected delegate object does not exist.

    Category: **Exception Classes**
    """


class SessionTeamNotFoundError(NotFoundError):
    """Exception raised when an expected session-team does not exist.

    Category: **Exception Classes**
    """


class NodeNotFoundError(NotFoundError):
    """Exception raised when an expected Node does not exist.

    Category: **Exception Classes**
    """


class ActorNotFoundError(NotFoundError):
    """Exception raised when an expected actor does not exist.

    Category: **Exception Classes**
    """


class ActivityNotFoundError(NotFoundError):
    """Exception raised when an expected bascenev1.Activity does not exist.

    Category: **Exception Classes**
    """


class SessionNotFoundError(NotFoundError):
    """Exception raised when an expected session does not exist.

    Category: **Exception Classes**
    """


class InputDeviceNotFoundError(NotFoundError):
    """Exception raised when an expected input-device does not exist.

    Category: **Exception Classes**
    """


class WidgetNotFoundError(NotFoundError):
    """Exception raised when an expected widget does not exist.

    Category: **Exception Classes**
    """


# TODO: Should integrate some sort of context printing into our
# log handling so we can just use logging.exception() and kill these
# two functions.


def print_exception(*args: Any, **keywds: Any) -> None:
    """Print info about an exception along with pertinent context state.

    Category: **General Utility Functions**

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
            if not _babase.do_once():
                return

        err_str = ' '.join([str(a) for a in args])
        print('ERROR:', err_str)
        _babase.print_context()
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
        print('ERROR: exception in babase.print_exception():')
        traceback.print_exc()


def print_error(err_str: str, once: bool = False) -> None:
    """Print info about an error along with pertinent context state.

    Category: **General Utility Functions**

    Prints all positional arguments provided along with various info about the
    current context.
    Pass the keyword 'once' as True if you want the call to only happen
    one time from an exact calling location.
    """
    import traceback

    try:
        # If we're only printing once and already have, bail.
        if once:
            if not _babase.do_once():
                return

        print('ERROR:', err_str)
        _babase.print_context()

        # Basically the output of traceback.print_stack()
        stackstr = ''.join(traceback.format_stack())
        print(stackstr, end='')
    except Exception:
        print('ERROR: exception in babase.print_error():')
        traceback.print_exc()
