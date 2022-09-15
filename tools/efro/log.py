# Released under the MIT License. See LICENSE for details.
#
"""Logging functionality."""
from __future__ import annotations

import sys
import time
import asyncio
import logging
import datetime
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated
from threading import Thread, current_thread, Lock

from efro.util import utc_now
from efro.call import tpartial
from efro.terminal import TerminalColor
from efro.dataclassio import ioprepped, IOAttrs, dataclass_to_json

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable, TextIO


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


LOG_NAMES_TO_LEVELS = {
    'DEBUG': LogLevel.DEBUG,
    'INFO': LogLevel.INFO,
    'WARNING': LogLevel.WARNING,
    'ERROR': LogLevel.ERROR,
    'CRITICAL': LogLevel.CRITICAL
}

LOG_LEVEL_NUMS_TO_COLOR_CODES: dict[int, tuple[str, str]] = {
    logging.DEBUG: (TerminalColor.CYAN.value, TerminalColor.RESET.value),
    logging.INFO: ('', ''),
    logging.WARNING: (TerminalColor.YELLOW.value, TerminalColor.RESET.value),
    logging.ERROR: (TerminalColor.RED.value, TerminalColor.RESET.value),
    logging.CRITICAL:
        (TerminalColor.STRONG_MAGENTA.value + TerminalColor.BOLD.value +
         TerminalColor.BG_BLACK.value, TerminalColor.RESET.value),
}


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

    _event_loop: asyncio.AbstractEventLoop

    # IMPORTANT: Any debug prints we do here should ONLY go to echofile.
    # Otherwise we can get infinite loops as those prints come back to us
    # as new log entries.

    def __init__(self,
                 path: str | Path | None,
                 echofile: TextIO | None,
                 suppress_non_root_debug: bool = False):
        super().__init__()
        # pylint: disable=consider-using-with
        self._file = (None
                      if path is None else open(path, 'w', encoding='utf-8'))
        self._echofile = echofile
        self._callbacks_lock = Lock()
        self._callbacks: list[Callable[[LogEntry], None]] = []
        self._suppress_non_root_debug = suppress_non_root_debug
        self._file_chunks: dict[str, list[str]] = {'stdout': [], 'stderr': []}
        self._file_chunk_ship_task: dict[str, asyncio.Task | None] = {
            'stdout': None,
            'stderr': None
        }
        self._printed_callback_error = False
        self._thread_bootstrapped = False
        self._thread = Thread(target=self._thread_main, daemon=True)
        self._thread.start()

        # Spin until our thread has set up its basic stuff;
        # otherwise we could wind up trying to push stuff to our
        # event loop before the loop exists.
        while not self._thread_bootstrapped:
            time.sleep(0.001)

    def add_callback(self, call: Callable[[LogEntry], None]) -> None:
        """Add a callback to be run for each LogEntry.

        Note that this callback will always run in a background thread.
        """
        with self._callbacks_lock:
            self._callbacks.append(call)

    def _thread_main(self) -> None:
        self._event_loop = asyncio.new_event_loop()
        # NOTE: if we ever use default threadpool at all we should allow
        # setting it for our loop.
        asyncio.set_event_loop(self._event_loop)
        self._thread_bootstrapped = True
        self._event_loop.run_forever()

    def emit(self, record: logging.LogRecord) -> None:
        # Called by logging to send us records.
        # We simply package them up and ship them to our thread.

        assert current_thread() is not self._thread

        # Special case - filter out this common extra-chatty category.
        # TODO - should use a standard logging.Filter for this.
        if (self._suppress_non_root_debug and record.name != 'root'
                and record.levelname == 'DEBUG'):
            return

        # We want to forward as much as we can along without processing it
        # (better to do so in a bg thread).
        # However its probably best to flatten the message string here since
        # it could cause problems stringifying things in threads where they
        # didn't expect to be stringified.
        msg = self.format(record)

        # Also print pretty colored output to our echo file (generally
        # stderr). We do this part here instead of in our bg thread
        # because the delay can throw off command line prompts or make
        # tight debugging harder.
        if self._echofile is not None:
            cbegin: str
            cend: str
            cbegin, cend = LOG_LEVEL_NUMS_TO_COLOR_CODES.get(
                record.levelno, ('', ''))

            # Should we be flushing here?
            self._echofile.write(f'{cbegin}{msg}{cend}\n')

        self._event_loop.call_soon_threadsafe(
            tpartial(self._emit_in_loop, record.name, record.levelname,
                     record.created, msg))

    def _emit_in_loop(self, name: str, levelname: str, created: float,
                      message: str) -> None:
        try:
            self._emit_entry(
                LogEntry(name=name,
                         message=message,
                         level=LOG_NAMES_TO_LEVELS[levelname],
                         time=datetime.datetime.fromtimestamp(
                             created, datetime.timezone.utc)))
        except Exception:
            import traceback
            traceback.print_exc(file=self._echofile)

    def file_write(self, name: str, output: str) -> None:
        """Send raw stdout/stderr output to the logger to be collated."""

        self._event_loop.call_soon_threadsafe(
            tpartial(self._file_write_in_loop, name, output))

    def _file_write_in_loop(self, name: str, output: str) -> None:
        try:
            assert name in ('stdout', 'stderr')

            # Here we try to be somewhat smart about breaking arbitrary
            # print output into discrete log entries.

            # Individual parts of a print come across as separate writes,
            # and the end of a print will be a standalone '\n' by default.
            # So let's ship whatever we've got when one of those comes in.
            if output == '\n':
                self._ship_file_chunks(name, cancel_ship_task=True)
            else:
                # By default just keep adding chunks.
                # However we keep a timer running anytime we've got
                # unshipped chunks so that we can ship what we've got
                # after a short bit if we never get a newline.
                self._file_chunks[name].append(output)

                ship_task = self._file_chunk_ship_task[name]
                if ship_task is None:
                    self._file_chunk_ship_task[name] = (
                        self._event_loop.create_task(
                            self._ship_chunks_task(name)))

        except Exception:
            import traceback
            traceback.print_exc(file=self._echofile)

    async def _ship_chunks_task(self, name: str) -> None:
        await asyncio.sleep(0.1)
        self._ship_file_chunks(name, cancel_ship_task=False)

    def _ship_file_chunks(self, name: str, cancel_ship_task: bool) -> None:
        self._emit_entry(
            LogEntry(name=name,
                     message=''.join(self._file_chunks[name]),
                     level=LogLevel.INFO,
                     time=utc_now()))
        self._file_chunks[name] = []
        ship_task = self._file_chunk_ship_task[name]
        if cancel_ship_task and ship_task is not None:
            ship_task.cancel()
        self._file_chunk_ship_task[name] = None

    def _emit_entry(self, entry: LogEntry) -> None:
        # This runs in our bg event loop thread and does most of the work.
        assert current_thread() is self._thread

        with self._callbacks_lock:
            for call in self._callbacks:
                try:
                    call(entry)
                except Exception:
                    # Only print one callback error to avoid insanity.
                    if not self._printed_callback_error:
                        import traceback
                        traceback.print_exc(file=self._echofile)
                        self._printed_callback_error = True

        # Dump to our structured log file.
        # TODO: set a timer for flushing; don't flush every line.
        if self._file is not None:
            entry_s = dataclass_to_json(entry)
            assert '\n' not in entry_s  # Make sure its a single line.
            print(entry_s, file=self._file, flush=True)


class FileLogEcho:
    """A file-like object for forwarding stdout/stderr to a LogHandler."""

    def __init__(self, original: TextIO, name: str,
                 handler: LogHandler) -> None:
        assert name in ('stdout', 'stderr')
        self._original = original
        self._name = name
        self._handler = handler

    def write(self, output: Any) -> None:
        """Override standard write call."""
        self._original.write(output)
        self._handler.file_write(self._name, output)

    def flush(self) -> None:
        """Flush the file."""
        self._original.flush()

    def isatty(self) -> bool:
        """Are we a terminal?"""
        return self._original.isatty()


def setup_logging(log_path: str | Path | None,
                  level: LogLevel,
                  suppress_non_root_debug: bool = False,
                  log_stdout_stderr: bool = False) -> LogHandler:
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
    # Note: by passing in the *original* stderr here before we
    # (potentially) replace it, we ensure that our log echos
    # won't themselves be intercepted and sent to the logger
    # which would create an infinite loop.
    loghandler = LogHandler(
        log_path,
        echofile=sys.stderr if sys.stderr.isatty() else None,
        suppress_non_root_debug=suppress_non_root_debug)

    # Note: going ahead with force=True here so that we replace any
    # existing logger. Though we warn if it looks like we are doing
    # that so we can try to avoid creating the first one.
    had_previous_handlers = bool(logging.root.handlers)
    logging.basicConfig(level=lmap[level],
                        format='%(message)s',
                        handlers=[loghandler],
                        force=True)
    if had_previous_handlers:
        logging.warning('setup_logging: force-replacing previous handlers.')

    # Optionally intercept Python's stdout/stderr output and generate
    # log entries from it.
    if log_stdout_stderr:
        sys.stdout = FileLogEcho(  # type: ignore
            sys.stdout, 'stdout', loghandler)
        sys.stderr = FileLogEcho(  # type: ignore
            sys.stderr, 'stderr', loghandler)

    return loghandler
