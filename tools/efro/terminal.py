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
"""Functionality related to terminal IO."""
from __future__ import annotations

import sys
import os
from enum import Enum, unique
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


@unique
class TerminalColor(Enum):
    """Color codes for printing to terminals.

    Generally the Clr class should be used when incorporating color into
    terminal output, as it handles non-color-supporting terminals/etc.
    """

    # Styles
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    INVERSE = '\033[7m'

    # Normal foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Normal background colors.
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # Strong foreground colors
    STRONG_BLACK = '\033[90m'
    STRONG_RED = '\033[91m'
    STRONG_GREEN = '\033[92m'
    STRONG_YELLOW = '\033[93m'
    STRONG_BLUE = '\033[94m'
    STRONG_MAGENTA = '\033[95m'
    STRONG_CYAN = '\033[96m'
    STRONG_WHITE = '\033[97m'

    # Strong background colors.
    STRONG_BG_BLACK = '\033[100m'
    STRONG_BG_RED = '\033[101m'
    STRONG_BG_GREEN = '\033[102m'
    STRONG_BG_YELLOW = '\033[103m'
    STRONG_BG_BLUE = '\033[104m'
    STRONG_BG_MAGENTA = '\033[105m'
    STRONG_BG_CYAN = '\033[106m'
    STRONG_BG_WHITE = '\033[107m'


def _default_color_enabled() -> bool:
    """Return whether we should enable ANSI color codes by default."""
    import platform

    # If we're not attached to a terminal, go with no-color.
    if not sys.__stdout__.isatty():
        return False

    # On windows, try to enable ANSI color mode.
    if platform.system() == 'Windows':
        return _windows_enable_color()

    # We seem to be a terminal with color support; let's do it!
    return True


# noinspection PyPep8Naming
def _windows_enable_color() -> bool:
    """Attempt to enable ANSI color on windows terminal; return success."""
    # pylint: disable=invalid-name, import-error, undefined-variable
    # Pulled from: https://bugs.python.org/issue30075
    import msvcrt
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)  # type: ignore

    ERROR_INVALID_PARAMETER = 0x0057
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    def _check_bool(result: Any, _func: Any, args: Any) -> Any:
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())  # type: ignore
        return args

    LPDWORD = ctypes.POINTER(wintypes.DWORD)
    kernel32.GetConsoleMode.errcheck = _check_bool
    kernel32.GetConsoleMode.argtypes = (wintypes.HANDLE, LPDWORD)
    kernel32.SetConsoleMode.errcheck = _check_bool
    kernel32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)

    def set_conout_mode(new_mode: int, mask: int = 0xffffffff) -> int:
        # don't assume StandardOutput is a console.
        # open CONOUT$ instead
        fdout = os.open('CONOUT$', os.O_RDWR)
        try:
            hout = msvcrt.get_osfhandle(fdout)
            old_mode = wintypes.DWORD()
            kernel32.GetConsoleMode(hout, ctypes.byref(old_mode))
            mode = (new_mode & mask) | (old_mode.value & ~mask)
            kernel32.SetConsoleMode(hout, mode)
            return old_mode.value
        finally:
            os.close(fdout)

    def enable_vt_mode() -> int:
        mode = mask = ENABLE_VIRTUAL_TERMINAL_PROCESSING
        try:
            return set_conout_mode(mode, mask)
        except WindowsError as exc:
            if exc.winerror == ERROR_INVALID_PARAMETER:
                raise NotImplementedError from exc
            raise

    try:
        enable_vt_mode()
        return True
    except NotImplementedError:
        return False


class Clr:
    """Convenience class for color terminal output.

    These will be set to ANSI color escape sequences if the current process
    seems to be an interactive terminal (sys.__stdout__.isatty()), otherwise
    they will be empty strings.
    If the environment variable EFRO_TERMCOLORS is set to 0 or 1, that
    value will be used instead.
    """
    _envval = os.environ.get('EFRO_TERMCOLORS')
    color_enabled = (True if _envval == '1' else
                     False if _envval == '0' else _default_color_enabled())
    if color_enabled:

        # Styles
        RST = TerminalColor.RESET.value
        BLD = TerminalColor.BOLD.value
        UND = TerminalColor.UNDERLINE.value
        INV = TerminalColor.INVERSE.value

        # Normal foreground colors
        BLK = TerminalColor.BLACK.value
        RED = TerminalColor.RED.value
        GRN = TerminalColor.GREEN.value
        YLW = TerminalColor.YELLOW.value
        BLU = TerminalColor.BLUE.value
        MAG = TerminalColor.MAGENTA.value
        CYN = TerminalColor.CYAN.value
        WHT = TerminalColor.WHITE.value

        # Normal background colors.
        BBLK = TerminalColor.BG_BLACK.value
        BRED = TerminalColor.BG_RED.value
        BGRN = TerminalColor.BG_GREEN.value
        BYLW = TerminalColor.BG_YELLOW.value
        BBLU = TerminalColor.BG_BLUE.value
        BMAG = TerminalColor.BG_MAGENTA.value
        BCYN = TerminalColor.BG_CYAN.value
        BWHT = TerminalColor.BG_WHITE.value

        # Strong foreground colors
        SBLK = TerminalColor.STRONG_BLACK.value
        SRED = TerminalColor.STRONG_RED.value
        SGRN = TerminalColor.STRONG_GREEN.value
        SYLW = TerminalColor.STRONG_YELLOW.value
        SBLU = TerminalColor.STRONG_BLUE.value
        SMAG = TerminalColor.STRONG_MAGENTA.value
        SCYN = TerminalColor.STRONG_CYAN.value
        SWHT = TerminalColor.STRONG_WHITE.value

        # Strong background colors.
        SBBLK = TerminalColor.STRONG_BG_BLACK.value
        SBRED = TerminalColor.STRONG_BG_RED.value
        SBGRN = TerminalColor.STRONG_BG_GREEN.value
        SBYLW = TerminalColor.STRONG_BG_YELLOW.value
        SBBLU = TerminalColor.STRONG_BG_BLUE.value
        SBMAG = TerminalColor.STRONG_BG_MAGENTA.value
        SBCYN = TerminalColor.STRONG_BG_CYAN.value
        SBWHT = TerminalColor.STRONG_BG_WHITE.value

    else:
        # Styles
        RST = ''
        BLD = ''
        UND = ''
        INV = ''

        # Normal foreground colors
        BLK = ''
        RED = ''
        GRN = ''
        YLW = ''
        BLU = ''
        MAG = ''
        CYN = ''
        WHT = ''

        # Normal background colors.
        BBLK = ''
        BRED = ''
        BGRN = ''
        BYLW = ''
        BBLU = ''
        BMAG = ''
        BCYN = ''
        BWHT = ''

        # Strong foreground colors
        SBLK = ''
        SRED = ''
        SGRN = ''
        SYLW = ''
        SBLU = ''
        SMAG = ''
        SCYN = ''
        SWHT = ''

        # Strong background colors.
        SBBLK = ''
        SBRED = ''
        SBGRN = ''
        SBYLW = ''
        SBBLU = ''
        SBMAG = ''
        SBCYN = ''
        SBWHT = ''
