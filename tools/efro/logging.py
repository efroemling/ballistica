# Released under the MIT License. See LICENSE for details.
#
"""Logging functionality."""
from __future__ import annotations

import sys
import time
import asyncio
import logging
import datetime
import itertools
from enum import Enum
from functools import partial
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override
from threading import Thread, current_thread, Lock

from efro.util import utc_now
from efro.terminal import Clr, color_enabled
from efro.dataclassio import ioprepped, IOAttrs, dataclass_to_json

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Callable, TextIO, Literal


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

    @property
    def python_logging_level(self) -> int:
        """Give the corresponding logging level."""
        return LOG_LEVEL_LEVELNOS[self]

    @classmethod
    def from_python_logging_level(cls, levelno: int) -> LogLevel:
        """Given a Python logging level, return a LogLevel."""
        return LEVELNO_LOG_LEVELS[levelno]


# Python logging levels from LogLevels
LOG_LEVEL_LEVELNOS = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.CRITICAL: logging.CRITICAL,
}

# LogLevels from Python logging levels
LEVELNO_LOG_LEVELS = {
    logging.DEBUG: LogLevel.DEBUG,
    logging.INFO: LogLevel.INFO,
    logging.WARNING: LogLevel.WARNING,
    logging.ERROR: LogLevel.ERROR,
    logging.CRITICAL: LogLevel.CRITICAL,
}

LEVELNO_COLOR_CODES: dict[int, tuple[str, str]] = {
    logging.DEBUG: (Clr.CYN, Clr.RST),
    logging.INFO: ('', ''),
    logging.WARNING: (Clr.YLW, Clr.RST),
    logging.ERROR: (Clr.RED, Clr.RST),
    logging.CRITICAL: (Clr.SMAG + Clr.BLD + Clr.BLK, Clr.RST),
}


@ioprepped
@dataclass
class LogEntry:
    """Single logged message."""

    name: Annotated[str, IOAttrs('n', soft_default='root', store_default=False)]
    message: Annotated[str, IOAttrs('m')]
    level: Annotated[LogLevel, IOAttrs('l')]
    time: Annotated[datetime.datetime, IOAttrs('t')]

    # We support arbitrary string labels per log entry which can be
    # incorporated into custom log processing. To populate this, our
    # LogHandler class looks for a 'labels' dict passed in the optional
    # 'extra' dict arg to standard Python log calls.
    labels: Annotated[dict[str, str], IOAttrs('la', store_default=False)] = (
        field(default_factory=dict)
    )


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
        *,
        path: str | Path | None,
        echofile: TextIO | None,
        cache_size_limit: int,
        cache_time_limit: datetime.timedelta | None,
        echofile_timestamp_format: Literal['default', 'relative'] = 'default',
        launch_time: float | None = None,
        strict_threads: bool = False,
    ):
        super().__init__()
        # pylint: disable=consider-using-with
        self._file = None if path is None else open(path, 'w', encoding='utf-8')
        self._echofile = echofile
        self._echofile_timestamp_format = echofile_timestamp_format
        self._callbacks: list[Callable[[LogEntry], None]] = []
        self._file_chunks: dict[str, list[str]] = {'stdout': [], 'stderr': []}
        self._file_chunk_ship_task: dict[str, asyncio.Task | None] = {
            'stdout': None,
            'stderr': None,
        }
        self._launch_time = time.time() if launch_time is None else launch_time
        self._cache_size = 0
        assert cache_size_limit >= 0
        self._cache_size_limit = cache_size_limit
        self._cache_time_limit = cache_time_limit
        self._cache = deque[tuple[int, LogEntry]]()
        self._cache_index_offset = 0
        self._cache_lock = Lock()
        self._printed_callback_error = False
        if __debug__:
            self._last_slow_emit_warning_time: float | None = None

        # Strict-threads mode means we don't use a daemon thread, but then
        # it is up to the user to explicitly call shutdown() to get our
        # background thread to exit.
        self._thread_bootstrapped = False
        self._thread = Thread(
            target=self._log_thread_main, daemon=not strict_threads
        )
        self._thread.start()

        # Spin until our thread is up and running; otherwise we could
        # wind up trying to push stuff to our event loop before the loop
        # exists.
        while not self._thread_bootstrapped:
            time.sleep(0.001)

    def add_callback(
        self, call: Callable[[LogEntry], None], feed_existing_logs: bool = False
    ) -> None:
        """Add a callback to be run for each LogEntry.

        Note that this callback will always run in a background thread.
        Passing True for feed_existing_logs will cause all cached logs
        in the handler to be fed to the callback (still in the
        background thread though).
        """

        # Kick this over to our bg thread to add the callback and
        # process cached entries at the same time to ensure there are no
        # race conditions that could cause entries to be skipped/etc.
        self._event_loop.call_soon_threadsafe(
            partial(self._add_callback_in_thread, call, feed_existing_logs)
        )

    def _add_callback_in_thread(
        self, call: Callable[[LogEntry], None], feed_existing_logs: bool
    ) -> None:
        """Add a callback to be run for each LogEntry.

        Note that this callback will always run in a background thread.
        Passing True for feed_existing_logs will cause all cached logs
        in the handler to be fed to the callback (still in the
        background thread though).
        """
        assert current_thread() is self._thread
        self._callbacks.append(call)

        # Run all of our cached entries through the new callback if desired.
        if feed_existing_logs and self._cache_size_limit > 0:
            with self._cache_lock:
                for _id, entry in self._cache:
                    self._run_callback_on_entry(call, entry)

    def _log_thread_main(self) -> None:
        self._event_loop = asyncio.new_event_loop()

        # In our background thread event loop we do a fair amount of
        # slow synchronous stuff such as mucking with the log cache.
        # Let's avoid getting tons of warnings about this in debug mode
        # since being ultra-real-time is not a huge priority here.
        self._event_loop.slow_callback_duration = 2.0  # Default is 0.1

        # NOTE: if we ever use default threadpool at all we should allow
        # setting it for our loop.
        asyncio.set_event_loop(self._event_loop)
        self._thread_bootstrapped = True
        try:
            if self._cache_time_limit is not None:
                _prunetask = self._event_loop.create_task(
                    self._time_prune_cache()
                )
            self._event_loop.run_forever()
        except BaseException:
            # If this ever goes down we're in trouble; we won't be able
            # to log about it though. Try to make some noise however we
            # can.
            print('LogHandler died!!!', file=sys.stderr)
            import traceback

            traceback.print_exc()
            raise

    async def _time_prune_cache(self) -> None:
        assert self._cache_time_limit is not None
        while bool(True):
            await asyncio.sleep(61.27)
            now = utc_now()
            with self._cache_lock:
                # Prune the oldest entry as long as there is a first one
                # that is too old.
                while (
                    self._cache
                    and (now - self._cache[0][1].time) >= self._cache_time_limit
                ):
                    popped = self._cache.popleft()
                    self._cache_size -= popped[0]
                    self._cache_index_offset += 1

    def get_cached(
        self, start_index: int = 0, max_entries: int | None = None
    ) -> LogArchive:
        """Build and return an archive of cached log entries.

        This will only include entries that have been processed by the
        background thread, so may not include just-submitted logs or
        entries for partially written stdout/stderr lines. Entries from
        the range [start_index:start_index+max_entries] which are still
        present in the cache will be returned.
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
                entries=self._cache_slice(start_index, end_index),
            )

    def _cache_slice(
        self, start: int, end: int, step: int = 1
    ) -> list[LogEntry]:
        # Deque doesn't natively support slicing but we can do it
        # manually. It sounds like rotating the deque and pulling from
        # the beginning is the most efficient way to do this. The
        # downside is the deque gets temporarily modified in the process
        # so we need to make sure we're holding the lock.
        assert self._cache_lock.locked()
        cache = self._cache
        cache.rotate(-start)
        slc = [e[1] for e in itertools.islice(cache, 0, end - start, step)]
        cache.rotate(start)
        return slc

    @classmethod
    def _is_immutable_log_data(cls, data: Any) -> bool:
        if isinstance(data, (str, bool, int, float, bytes)):
            return True
        if isinstance(data, tuple):
            return all(cls._is_immutable_log_data(x) for x in data)
        return False

    def call_in_thread(self, call: Callable[[], Any]) -> None:
        """Submit a call to be run in the logging background thread."""
        self._event_loop.call_soon_threadsafe(call)

    @override
    def emit(self, record: logging.LogRecord) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals

        if __debug__:
            starttime = time.monotonic()

        # Called by logging to send us records.

        # Optimization: if our log args are all simple immutable values,
        # we can just kick the whole thing over to our background thread
        # to be formatted there at our leisure. If anything is mutable
        # and thus could possibly change between now and then or if we
        # want to do immediate file echoing then we need to bite the
        # bullet and do that stuff here at the call site.
        fast_path = self._echofile is None and self._is_immutable_log_data(
            record.args
        )

        # Note: just assuming types are correct here, but they'll be
        # checked properly when the resulting LogEntry gets exported.
        labels: dict[str, str] | None = getattr(record, 'labels', None)
        if labels is None:
            labels = {}

        if fast_path:
            if __debug__:
                formattime = echotime = time.monotonic()
            self._event_loop.call_soon_threadsafe(
                partial(
                    self._emit_in_thread,
                    record.name,
                    record.levelno,
                    record.created,
                    record,
                    labels,
                )
            )
        else:
            # Slow case; do formatting and echoing here at the log call
            # site.
            msg = self.format(record)

            if __debug__:
                formattime = time.monotonic()

            # Also immediately print pretty colored output to our echo
            # file (generally stderr). We do this part here instead of
            # in our bg thread because the delay can throw off command
            # line prompts or make tight debugging harder.
            if self._echofile is not None:
                if self._echofile_timestamp_format == 'relative':
                    timestamp = f'{record.created - self._launch_time:.3f}'
                else:
                    timestamp = (
                        datetime.datetime.fromtimestamp(
                            record.created, tz=datetime.UTC
                        ).strftime('%H:%M:%S')
                        + f'.{int(record.msecs):03d}'
                    )

                # If color printing is disabled, show level through text
                # instead of color.
                lvlnameex = (
                    ''
                    if color_enabled
                    else f' {logging.getLevelName(record.levelno)}'
                )

                preinfo = (
                    f'{Clr.WHT}{timestamp}{lvlnameex} {record.name}:'
                    f'{Clr.RST} '
                )
                ends = LEVELNO_COLOR_CODES.get(record.levelno)
                if ends is not None:
                    self._echofile.write(f'{preinfo}{ends[0]}{msg}{ends[1]}\n')
                else:
                    self._echofile.write(f'{preinfo}{msg}\n')
                self._echofile.flush()

            if __debug__:
                echotime = time.monotonic()

            self._event_loop.call_soon_threadsafe(
                partial(
                    self._emit_in_thread,
                    record.name,
                    record.levelno,
                    record.created,
                    msg,
                    labels,
                )
            )

        if __debug__:
            # pylint: disable=used-before-assignment
            #
            # Make noise if we're taking a significant amount of time
            # here. Limit the noise to once every so often though;
            # otherwise we could get a feedback loop where every log
            # emit results in a warning log which results in another,
            # etc.
            now = time.monotonic()
            duration = now - starttime
            format_duration = formattime - starttime
            echo_duration = echotime - formattime
            if duration > 0.05 and (
                self._last_slow_emit_warning_time is None
                or now > self._last_slow_emit_warning_time + 10.0
            ):
                # Logging calls from *within* a logging handler sounds
                # sketchy, so let's just kick this over to the bg event
                # loop thread we've already got.
                self._last_slow_emit_warning_time = now
                self._event_loop.call_soon_threadsafe(
                    partial(
                        logging.warning,
                        'efro.logging.LogHandler emit took too long'
                        ' (%.3fs total; %.3fs format, %.3fs echo,'
                        ' fast_path=%s).',
                        duration,
                        format_duration,
                        echo_duration,
                        fast_path,
                    )
                )

    def _emit_in_thread(
        self,
        name: str,
        levelno: int,
        created: float,
        message: str | logging.LogRecord,
        labels: dict[str, str],
    ) -> None:
        # pylint: disable=too-many-positional-arguments
        try:
            # If they passed a raw record here, bake it down to a string.
            if isinstance(message, logging.LogRecord):
                message = self.format(message)

            self._emit_entry(
                LogEntry(
                    name=name,
                    message=message,
                    level=LEVELNO_LOG_LEVELS.get(levelno, LogLevel.INFO),
                    time=datetime.datetime.fromtimestamp(
                        created, datetime.timezone.utc
                    ),
                    labels=labels,
                )
            )
        except Exception:
            import traceback

            traceback.print_exc(file=self._echofile)

    def file_write(self, name: str, output: str) -> None:
        """Send raw stdout/stderr output to the logger to be collated."""

        # Note to self: it turns out that things like '^^^^^^^^^^^^^^'
        # lines in stack traces get written as lots of individual '^'
        # writes. It feels a bit dirty to be pushing a deferred call to
        # another thread for each character. Perhaps should do some sort
        # of basic accumulation here?
        self._event_loop.call_soon_threadsafe(
            partial(self._file_write_in_thread, name, output)
        )

    def _file_write_in_thread(self, name: str, output: str) -> None:
        try:
            assert name in ('stdout', 'stderr')

            # Here we try to be somewhat smart about breaking arbitrary
            # print output into discrete log entries.

            self._file_chunks[name].append(output)

            # Individual parts of a print come across as separate
            # writes, and the end of a print will be a standalone '\n'
            # by default. Let's use that as a hint that we're likely at
            # the end of a full print statement and ship what we've got.
            if output == '\n':
                self._ship_file_chunks(name, cancel_ship_task=True)
            else:
                # By default just keep adding chunks. However we keep a
                # timer running anytime we've got unshipped chunks so
                # that we can ship what we've got after a short bit if
                # we never get a newline.
                ship_task = self._file_chunk_ship_task[name]
                if ship_task is None:
                    self._file_chunk_ship_task[name] = (
                        self._event_loop.create_task(
                            self._ship_chunks_task(name),
                            name='log ship file chunks',
                        )
                    )

        except Exception:
            import traceback

            traceback.print_exc(file=self._echofile)

    def shutdown(self) -> None:
        """Kill bg thread and flush pending logs/prints."""
        assert current_thread() is not self._thread

        # done = False
        self.file_flush('stdout')
        self.file_flush('stderr')

        # Push a message to our thread to break out of its loop, and
        # then wait for the thread to exit. This will effectively flush
        # all pending messages up to this point but will leave the loop
        # intact so if anyone pushes a message at this point it won't
        # error (though it will never get processed either).
        self._event_loop.call_soon_threadsafe(self._event_loop.stop)
        self._thread.join()

        # def _set_done() -> None:
        #     nonlocal done
        #     done = True

        # self._event_loop.call_soon_threadsafe(_set_done)

        # starttime = time.monotonic()
        # while not done:
        #     if time.monotonic() - starttime > 5.0:
        #         print('LogHandler shutdown hung!!!', file=sys.stderr)
        #         break
        #     time.sleep(0.01)

    def file_flush(self, name: str) -> None:
        """Send raw stdout/stderr flush to the logger to be collated."""

        self._event_loop.call_soon_threadsafe(
            partial(self._file_flush_in_thread, name)
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
        # Note: it's important we sleep here for a moment. Otherwise,
        # things like '^^^^^^^^^^^^' lines in stack traces, which come
        # through as lots of individual '^' writes, tend to get broken
        # into lots of tiny little lines by us.
        await asyncio.sleep(0.01)
        self._ship_file_chunks(name, cancel_ship_task=False)

    def _ship_file_chunks(self, name: str, cancel_ship_task: bool) -> None:
        # Note: Raw print input generally ends in a newline, but that is
        # redundant when we break things into log entries and results in
        # extra empty lines. So strip off a single trailing newline if
        # one is present.
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
                    popped = self._cache.popleft()
                    self._cache_size -= popped[0]
                    self._cache_index_offset += 1

        # Pass to callbacks.
        for call in self._callbacks:
            self._run_callback_on_entry(call, entry)

        # Dump to our structured log file.
        #
        # TODO: should set a timer for flushing; don't flush every line.
        if self._file is not None:
            entry_s = dataclass_to_json(entry)
            assert '\n' not in entry_s  # Make sure its a single line.
            print(entry_s, file=self._file, flush=True)

    def _run_callback_on_entry(
        self, callback: Callable[[LogEntry], None], entry: LogEntry
    ) -> None:
        """Run a callback and handle any errors."""
        try:
            callback(entry)
        except Exception:
            # Only print the first callback error to avoid insanity.
            if not self._printed_callback_error:
                import traceback

                traceback.print_exc(file=self._echofile)
                self._printed_callback_error = True


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
    *,
    log_stdout_stderr: bool = False,
    echo_to_stderr: bool = True,
    cache_size_limit: int = 0,
    cache_time_limit: datetime.timedelta | None = None,
    launch_time: float | None = None,
    strict_threads: bool = False,
    standard_filters: bool = True,
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

    # Wire logger output to go to a structured log file. Also echo it to
    # stderr IF we're running in a terminal.
    #
    # UPDATE: Actually gonna always go to stderr. Is there a reason we
    # shouldn't? This makes debugging possible if all we have is access
    # to a non-interactive terminal or file dump. We could add a
    # '--quiet' arg or whatnot to change this behavior.

    # Note: by passing in the *original* stderr here before we
    # (potentially) replace it, we ensure that our log echos won't
    # themselves be intercepted and sent to the logger which would
    # create an infinite loop.
    loghandler = LogHandler(
        path=log_path,
        echofile=sys.stderr if echo_to_stderr else None,
        echofile_timestamp_format='relative',
        cache_size_limit=cache_size_limit,
        cache_time_limit=cache_time_limit,
        launch_time=launch_time,
        strict_threads=strict_threads,
    )

    if standard_filters:

        # The warning for retrying a connection really should be an info.
        # See https://github.com/urllib3/urllib3/issues/2583
        class _DowngradeURLLib3RetryWarningFilter(logging.Filter):
            """Downgrades 'retrying' warning to info."""

            @override
            def filter(self, record: logging.LogRecord) -> bool:
                if (
                    record.levelno == logging.WARNING
                    and 'Retrying (' in record.msg
                ):
                    newlevel = logging.INFO

                    record.levelno = newlevel
                    record.levelname = logging.getLevelName(newlevel)

                    # Since log-level pruning happened before we reached
                    # this point, we're still destined to show up even
                    # if we change level to something that's not being
                    # displayed. So let's manually check level and
                    # discard if this new level shouldn't be shown.
                    if not logging.getLogger(record.name).isEnabledFor(
                        newlevel
                    ):
                        return False

                return True

        logging.getLogger('urllib3.connectionpool').addFilter(
            _DowngradeURLLib3RetryWarningFilter()
        )

    # Note: going ahead with force=True here so that we replace any
    # existing logger. Though we warn if it looks like we are doing that
    # so we can try to avoid creating the first one.
    had_previous_handlers = bool(logging.root.handlers)
    logging.basicConfig(
        level=lmap[level],
        # We dump *only* the message here. We pass various log record
        # bits around so we can write rich logs or format things later.
        format='%(message)s',
        handlers=[loghandler],
        force=True,
    )
    if had_previous_handlers:
        logging.warning(
            'setup_logging: Replacing existing handlers.'
            ' Something may have logged before expected.'
        )

    # Optionally intercept Python's stdout/stderr output and generate
    # log entries from it.
    if log_stdout_stderr:
        sys.stdout = FileLogEcho(sys.stdout, 'stdout', loghandler)
        sys.stderr = FileLogEcho(sys.stderr, 'stderr', loghandler)

    return loghandler
