# Released under the MIT License. See LICENSE for details.
#
"""Logging functionality."""
from __future__ import annotations

import sys
import time
import logging
import datetime
import threading
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.util import utc_now
from efro.terminal import TerminalColor
from efro.dataclassio import ioprepped, IOAttrs, dataclass_to_json

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable


class LogLevel(Enum):
    """Severity level for a log entry.

    These enums have numeric values so they can be compared in severity.
    Note that these values are not currently interchangeable with the
    logging.ERROR, logging.DEBUG, etc. values.
    """
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@ioprepped
@dataclass
class LogEntry:
    """Single logged message."""
    name: Annotated[str,
                    IOAttrs('n', soft_default='root', store_default=False)]
    message: Annotated[str, IOAttrs('m')]
    level: Annotated[LogLevel, IOAttrs('l')]
    time: Annotated[datetime.datetime, IOAttrs('t')]


class LogHandler(logging.Handler):
    """Fancy-pants handler for logging output.

    Writes logs to disk in structured json format and echoes them
    to stdout/stderr with pretty colors.
    """

    def __init__(self,
                 path: str | Path | None,
                 echofile: Any,
                 suppress_non_root_debug: bool = False):
        super().__init__()
        # pylint: disable=consider-using-with
        self._file = (None
                      if path is None else open(path, 'w', encoding='utf-8'))
        self._echofile = echofile
        self._callbacks: list[Callable[[LogEntry], None]] = []
        self._suppress_non_root_debug = suppress_non_root_debug

    def emit(self, record: logging.LogRecord) -> None:

        # Special case - filter out this common extra-chatty category.
        # TODO - should use a standard logging.Filter for this.
        if (self._suppress_non_root_debug and record.name != 'root'
                and record.levelname == 'DEBUG'):
            return

        # Bake down all log formatting into a simple string.
        msg = self.format(record)

        # Translate Python log levels to our own.
        level = {
            'DEBUG': LogLevel.DEBUG,
            'INFO': LogLevel.INFO,
            'WARNING': LogLevel.WARNING,
            'ERROR': LogLevel.ERROR,
            'CRITICAL': LogLevel.CRITICAL
        }[record.levelname]

        entry = LogEntry(message=msg,
                         name=record.name,
                         level=level,
                         time=datetime.datetime.fromtimestamp(
                             record.created, datetime.timezone.utc))

        for call in self._callbacks:
            call(entry)

        # Also route log entries to the echo file (generally stdout/stderr)
        # with pretty colors.
        if self._echofile is not None:
            cbegin: str
            cend: str
            cbegin, cend = {
                LogLevel.DEBUG:
                    (TerminalColor.CYAN.value, TerminalColor.RESET.value),
                LogLevel.INFO: ('', ''),
                LogLevel.WARNING:
                    (TerminalColor.YELLOW.value, TerminalColor.RESET.value),
                LogLevel.ERROR:
                    (TerminalColor.RED.value, TerminalColor.RESET.value),
                LogLevel.CRITICAL:
                    (TerminalColor.STRONG_MAGENTA.value +
                     TerminalColor.BOLD.value + TerminalColor.BG_BLACK.value,
                     TerminalColor.RESET.value),
            }[level]

            self._echofile.write(f'{cbegin}{msg}{cend}\n')

        # Note to self: it sounds like logging wraps calls to us
        # in a lock so we shouldn't have to worry about garbled
        # json output due to multiple threads writing at once,
        # but may be good to find out for sure?
        if self._file is not None:
            entry_s = dataclass_to_json(entry)
            assert '\n' not in entry_s  # make sure its a single line
            print(entry_s, file=self._file, flush=True)

    def emit_custom(self, name: str, message: str, level: LogLevel) -> None:
        """Custom emit call for our stdout/stderr redirection."""
        entry = LogEntry(name=name,
                         message=message,
                         level=level,
                         time=utc_now())

        for call in self._callbacks:
            call(entry)

        if self._file is not None:
            entry_s = dataclass_to_json(entry)
            assert '\n' not in entry_s  # Make sure its a single line.
            print(entry_s, file=self._file, flush=True)

    def add_callback(self, call: Callable[[LogEntry], None]) -> None:
        """Add a callback to be run for each added entry."""
        self._callbacks.append(call)


class LogRedirect:
    """A file-like object for redirecting stdout/stderr to our log."""

    def __init__(self, name: str, orig_out: Any, log_handler: LogHandler,
                 log_level: LogLevel):
        self._name = name
        self._orig_out = orig_out
        self._log_handler = log_handler
        self._log_level = log_level
        self._chunk = ''
        self._chunk_start_time = 0.0
        self._lock = threading.Lock()

    def write(self, s: str) -> None:
        """Write something to output."""

        assert isinstance(s, str)

        # First, ship it off to the original destination.
        self._orig_out.write(s)

        # Now add this to our chunk and ship completed chunks
        # off to the logger.
        # Let's consider a chunk completed when we're passed
        # a single '\n' by itself. (print() statement will do
        # this at the end by default).
        # We may get some false positives/negatives this way
        # but it should result in *most* big multi-line print
        # statements being wrapped into a single log entry.
        # Also, flush with only_old=True can be called periodically
        # to dump any pending chunks that don't happen to fit
        # this pattern.
        with self._lock:
            if s == '\n':
                self._log_handler.emit_custom(name=self._name,
                                              message=self._chunk,
                                              level=self._log_level)
                self._chunk = ''
            else:
                if self._chunk == '':
                    self._chunk_start_time = time.time()
                self._chunk += s

    def flush(self, only_old: bool = False) -> None:
        """Flushhhhh!"""
        self._orig_out.flush()
        if only_old and time.time() - self._chunk_start_time < 0.5:
            return
        with self._lock:
            if self._chunk != '':
                chunk = self._chunk
                if chunk.endswith('\n'):
                    chunk = chunk[:-1]
                self._log_handler.emit_custom(name=self._name,
                                              message=chunk,
                                              level=self._log_level)
                self._chunk = ''


def setup_logging(log_path: str | Path | None,
                  level: LogLevel,
                  suppress_non_root_debug: bool = False) -> LogHandler:
    """Set up our logging environment.

    Returns the custom handler which can be used to fetch information
    about logs that have passed through it. (worst log-levels, etc.).
    """

    lmap = {
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
        LogLevel.CRITICAL: logging.CRITICAL,
    }

    # Wire logger output to go to a structured log file.
    # Also echo it to stderr IF we're running in a terminal.
    loghandler = LogHandler(
        log_path,
        echofile=sys.stderr if sys.stderr.isatty() else None,
        suppress_non_root_debug=suppress_non_root_debug)

    logging.basicConfig(level=lmap[level],
                        format='%(message)s',
                        handlers=[loghandler])

    # DISABLING THIS BIT FOR NOW - want to keep things as pure as possible.
    if bool(False):
        # Now wire Python stdout/stderr output to generate log entries
        # in addition to its regular routing. Make sure to do this *after* we
        # tell the log-handler to write to stderr, otherwise we get an infinite
        # loop.
        # NOTE: remember that this won't capture subcommands or other
        # non-python stdout/stderr output.
        sys.stdout = LogRedirect(  # type: ignore
            'stdout', sys.stdout, loghandler, LogLevel.INFO)
        sys.stderr = LogRedirect(  # type: ignore
            'stderr', sys.stderr, loghandler, LogLevel.INFO)

    return loghandler
