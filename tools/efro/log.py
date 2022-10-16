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


LEVELNO_LOG_LEVELS = {
    logging.DEBUG: LogLevel.DEBUG,
    logging.INFO: LogLevel.INFO,
    logging.WARNING: LogLevel.WARNING,
    logging.ERROR: LogLevel.ERROR,
    logging.CRITICAL: LogLevel.CRITICAL,
}

LEVELNO_COLOR_CODES: dict[int, tuple[str, str]] = {
    logging.DEBUG: (TerminalColor.CYAN.value, TerminalColor.RESET.value),
    logging.INFO: ('', ''),
    logging.WARNING: (TerminalColor.YELLOW.value, TerminalColor.RESET.value),
    logging.ERROR: (TerminalColor.RED.value, TerminalColor.RESET.value),
    logging.CRITICAL: (
        TerminalColor.STRONG_MAGENTA.value
        + TerminalColor.BOLD.value
        + TerminalColor.BG_BLACK.value,
        TerminalColor.RESET.value,
    ),
}


@ioprepped
@dataclass
class LogEntry:
    """Single logged message."""

    name: Annotated[str, IOAttrs('n', soft_default='root', store_default=False)]
    message: Annotated[str, IOAttrs('m')]
    level: Annotated[LogLevel, IOAttrs('l')]
    time: Annotated[datetime.datetime, IOAttrs('t')]


@ioprepped
@dataclass
class LogArchive:
    """Info and data for a log."""

    # Total number of entries submitted to the log.
    log_size: Annotated[int, IOAttrs('t')]

    # Offset for the entries contained here.
    # (10 means our first entry is the 10th in the log, etc.)
    start_index: Annotated[int, IOAttrs('c')]

    entries: Annotated[list[LogEntry], IOAttrs('e')]


class LogHandler(logging.Handler):
    """Fancy-pants handler for logging output.

    Writes logs to disk in structured json format and echoes them
    to stdout/stderr with pretty colors.
    """

    _event_loop: asyncio.AbstractEventLoop

    # IMPORTANT: Any debug prints we do here should ONLY go to echofile.
    # Otherwise we can get infinite loops as those prints come back to us
    # as new log entries.

    def __init__(
        self,
        path: str | Path | None,
        echofile: TextIO | None,
        suppress_non_root_debug: bool = False,
        cache_size_limit: int = 0,
    ):
        super().__init__()
        # pylint: disable=consider-using-with
        self._file = None if path is None else open(path, 'w', encoding='utf-8')
        self._echofile = echofile
        self._callbacks_lock = Lock()
        self._callbacks: list[Callable[[LogEntry], None]] = []
        self._suppress_non_root_debug = suppress_non_root_debug
        self._file_chunks: dict[str, list[str]] = {'stdout': [], 'stderr': []}
        self._file_chunk_ship_task: dict[str, asyncio.Task | None] = {
            'stdout': None,
            'stderr': None,
        }
        self._cache_size = 0
        assert cache_size_limit >= 0
        self._cache_size_limit = cache_size_limit
        self._cache: list[tuple[int, LogEntry]] = []
        self._cache_index_offset = 0
        self._cache_lock = Lock()
        self._printed_callback_error = False
        self._thread_bootstrapped = False
        self._thread = Thread(target=self._thread_main, daemon=True)
        self._thread.start()

        # Spin until our thread is up and running; otherwise we could
        # wind up trying to push stuff to our event loop before the
        # loop exists.
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
        try:
            self._event_loop.run_forever()
        except BaseException:
            # If this ever goes down we're in trouble.
            # We won't be able to log about it though...
            # Try to make some noise however we can.
            print('LogHandler died!!!', file=sys.stderr)
            import traceback

            traceback.print_exc()
            raise

    def get_cached(
        self, start_index: int = 0, max_entries: int | None = None
    ) -> LogArchive:
        """Build and return an archive of cached log entries.

        This will only include entries that have been processed by the
        background thread, so may not include just-submitted logs or
        entries for partially written stdout/stderr lines.
        Entries from the range [start_index:start_index+max_entries]
        which are still present in the cache will be returned.
        """

        assert start_index >= 0
        if max_entries is not None:
            assert max_entries >= 0
        with self._cache_lock:
            # Transform start_index to our present cache space.
            start_index -= self._cache_index_offset
            # Calc end-index in our present cache space.
            end_index = (
                len(self._cache)
                if max_entries is None
                else start_index + max_entries
            )

            # Clamp both indexes to both ends of our present space.
            start_index = max(0, min(start_index, len(self._cache)))
            end_index = max(0, min(end_index, len(self._cache)))

            return LogArchive(
                log_size=self._cache_index_offset + len(self._cache),
                start_index=start_index + self._cache_index_offset,
                entries=[e[1] for e in self._cache[start_index:end_index]],
            )

    def emit(self, record: logging.LogRecord) -> None:
        # Called by logging to send us records.
        # We simply package them up and ship them to our thread.
        # UPDATE: turns out we CAN get log messages from this thread
        # (the C++ layer can spit out some performance metrics when
        # calls take too long/etc.)
        # assert current_thread() is not self._thread

        # Special case - filter out this common extra-chatty category.
        # TODO - should use a standard logging.Filter for this.
        if (
            self._suppress_non_root_debug
            and record.name != 'root'
            and record.levelname == 'DEBUG'
        ):
            return

        # We want to forward as much as we can along without processing it
        # (better to do so in a bg thread).
        # However its probably best to flatten the message string here since
        # it could cause problems stringifying things in threads where they
        # didn't expect to be stringified.
        msg = self.format(record)

        # Also immediately print pretty colored output to our echo file
        # (generally stderr). We do this part here instead of in our bg
        # thread because the delay can throw off command line prompts or
        # make tight debugging harder.
        if self._echofile is not None:
            ends = LEVELNO_COLOR_CODES.get(record.levelno)
            if ends is not None:
                self._echofile.write(f'{ends[0]}{msg}{ends[1]}\n')
            else:
                self._echofile.write(f'{msg}\n')

        self._event_loop.call_soon_threadsafe(
            tpartial(
                self._emit_in_thread,
                record.name,
                record.levelno,
                record.created,
                msg,
            )
        )

    def _emit_in_thread(
        self, name: str, levelno: int, created: float, message: str
    ) -> None:
        try:
            self._emit_entry(
                LogEntry(
                    name=name,
                    message=message,
                    level=LEVELNO_LOG_LEVELS.get(levelno, LogLevel.INFO),
                    time=datetime.datetime.fromtimestamp(
                        created, datetime.timezone.utc
                    ),
                )
            )
        except Exception:
            import traceback

            traceback.print_exc(file=self._echofile)

    def file_write(self, name: str, output: str) -> None:
        """Send raw stdout/stderr output to the logger to be collated."""

        self._event_loop.call_soon_threadsafe(
            tpartial(self._file_write_in_thread, name, output)
        )

    def _file_write_in_thread(self, name: str, output: str) -> None:
        try:
            assert name in ('stdout', 'stderr')

            # Here we try to be somewhat smart about breaking arbitrary
            # print output into discrete log entries.

            self._file_chunks[name].append(output)

            # Individual parts of a print come across as separate writes,
            # and the end of a print will be a standalone '\n' by default.
            # Let's use that as a hint that we're likely at the end of
            # a full print statement and ship what we've got.
            if output == '\n':
                self._ship_file_chunks(name, cancel_ship_task=True)
            else:
                # By default just keep adding chunks.
                # However we keep a timer running anytime we've got
                # unshipped chunks so that we can ship what we've got
                # after a short bit if we never get a newline.
                ship_task = self._file_chunk_ship_task[name]
                if ship_task is None:
                    self._file_chunk_ship_task[
                        name
                    ] = self._event_loop.create_task(
                        self._ship_chunks_task(name),
                        name='log ship file chunks',
                    )

        except Exception:
            import traceback

            traceback.print_exc(file=self._echofile)

    def file_flush(self, name: str) -> None:
        """Send raw stdout/stderr flush to the logger to be collated."""

        self._event_loop.call_soon_threadsafe(
            tpartial(self._file_flush_in_thread, name)
        )

    def _file_flush_in_thread(self, name: str) -> None:
        try:
            assert name in ('stdout', 'stderr')

            # Immediately ship whatever chunks we've got.
            if self._file_chunks[name]:
                self._ship_file_chunks(name, cancel_ship_task=True)

        except Exception:
            import traceback

            traceback.print_exc(file=self._echofile)

    async def _ship_chunks_task(self, name: str) -> None:
        self._ship_file_chunks(name, cancel_ship_task=False)

    def _ship_file_chunks(self, name: str, cancel_ship_task: bool) -> None:
        # Note: Raw print input generally ends in a newline, but that is
        # redundant when we break things into log entries and results
        # in extra empty lines. So strip off a single trailing newline.
        text = ''.join(self._file_chunks[name]).removesuffix('\n')

        self._emit_entry(
            LogEntry(
                name=name, message=text, level=LogLevel.INFO, time=utc_now()
            )
        )
        self._file_chunks[name] = []
        ship_task = self._file_chunk_ship_task[name]
        if cancel_ship_task and ship_task is not None:
            ship_task.cancel()
        self._file_chunk_ship_task[name] = None

    def _emit_entry(self, entry: LogEntry) -> None:
        assert current_thread() is self._thread

        # Store to our cache.
        if self._cache_size_limit > 0:
            with self._cache_lock:
                # Do a rough calc of how many bytes this entry consumes.
                entry_size = sum(
                    sys.getsizeof(x)
                    for x in (
                        entry,
                        entry.name,
                        entry.message,
                        entry.level,
                        entry.time,
                    )
                )
                self._cache.append((entry_size, entry))
                self._cache_size += entry_size

                # Prune old until we are back at or under our limit.
                while self._cache_size > self._cache_size_limit:
                    popped = self._cache.pop(0)
                    self._cache_size -= popped[0]
                    self._cache_index_offset += 1

        # Pass to callbacks.
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

    def __init__(
        self, original: TextIO, name: str, handler: LogHandler
    ) -> None:
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

        # We also use this as a hint to ship whatever file chunks
        # we've accumulated (we have to try and be smart about breaking
        # our arbitrary file output into discrete entries).
        self._handler.file_flush(self._name)

    def isatty(self) -> bool:
        """Are we a terminal?"""
        return self._original.isatty()


def setup_logging(
    log_path: str | Path | None,
    level: LogLevel,
    suppress_non_root_debug: bool = False,
    log_stdout_stderr: bool = False,
    cache_size_limit: int = 0,
) -> LogHandler:
    """Set up our logging environment.

    Returns the custom handler which can be used to fetch information
    about logs that have passed through it. (worst log-levels, caches, etc.).
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
    # UPDATE: Actually gonna always go to stderr. Is there a
    # reason we shouldn't? This makes debugging possible if all
    # we have is access to a non-interactive terminal or file dump.
    # We could add a '--quiet' arg or whatnot to change this behavior.

    # Note: by passing in the *original* stderr here before we
    # (potentially) replace it, we ensure that our log echos
    # won't themselves be intercepted and sent to the logger
    # which would create an infinite loop.
    loghandler = LogHandler(
        log_path,
        # echofile=sys.stderr if sys.stderr.isatty() else None,
        echofile=sys.stderr,
        suppress_non_root_debug=suppress_non_root_debug,
        cache_size_limit=cache_size_limit,
    )

    # Note: going ahead with force=True here so that we replace any
    # existing logger. Though we warn if it looks like we are doing
    # that so we can try to avoid creating the first one.
    had_previous_handlers = bool(logging.root.handlers)
    logging.basicConfig(
        level=lmap[level],
        format='%(message)s',
        handlers=[loghandler],
        force=True,
    )
    if had_previous_handlers:
        logging.warning('setup_logging: force-replacing previous handlers.')

    # Optionally intercept Python's stdout/stderr output and generate
    # log entries from it.
    if log_stdout_stderr:
        sys.stdout = FileLogEcho(  # type: ignore
            sys.stdout, 'stdout', loghandler
        )
        sys.stderr = FileLogEcho(  # type: ignore
            sys.stderr, 'stderr', loghandler
        )

    return loghandler
