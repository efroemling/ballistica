# Released under the MIT License. See LICENSE for details.
#
"""Keeps the primary account's cloud profiles synced and cached locally.

Mirrors the classic purchases sync: the live account data basn pushes us
carries a small ``profiles_state`` id, and we fetch the profiles
themselves (:class:`bacommon.classic.GetClassicProfilesMessage`) only
when our copy doesn't match it. The fetched profiles are also cached on
disk so they can be used offline (for play only; editing always happens
in the cloud).

Three live values decide whether the cache is current: the account's
``profiles_state`` (its stored profiles changed), its
``purchases_state`` (composed profiles depend on entitlements) and the
fleet-wide ``cache_version`` (the server changed what it composes for
the same inputs -- a repin, a table edit, a logic change). A version
change alone marks the cache stale but keeps it *usable*: it is still
handed out while a jittered background refetch runs, since the old
json still works and every client of the fleet hears the change at
the same moment. Any of the other two staling the cache means it is
not handed out (a legacy fallback instead) until the refetch lands.

Cache writes happen on a background thread and are atomic (temp file +
``fsync`` + ``os.replace``). The cache is read once, on the logic
thread, the first time it is needed. Anything unexpected about its
contents (bad json, checksum mismatch, wrong types, invalid profile
json, oversized file) makes us treat it as missing; it is never trusted
partially.
"""

import os
import json
import random
import logging
import hashlib
import tempfile
import threading
from dataclasses import dataclass
from typing import Annotated

from efro.error import CommunicationError
from efro.dataclassio import (
    ioprepped,
    IOAttrs,
    dataclass_from_json,
    dataclass_to_json,
)
from bacommon.logging import ClientLoggerName
import bacommon.classic
import babase

#: Name of the cache file (in the app's cache directory).
CACHE_FILE_NAME = 'classic_cloud_profiles.json'

# Bump when the on-disk layout changes incompatibly; files with any other
# version are ignored (and replaced on the next fetch).
_CACHE_FORMAT_VERSION = 1

# We read the cache on the logic thread, so refuse anything absurd.
_MAX_CACHE_FILE_BYTES = 4 * 1024 * 1024

# Fetch retry backoff (seconds).
_RETRY_DELAY_MIN = 3.456
_RETRY_DELAY_MAX = 120.0

# Warn (once per target) if we still can't get a match after this many
# fetch attempts; that likely points at a server-side state bug.
_MISMATCH_WARN_ATTEMPTS = 6

# A cache-version change reaches every client of the fleet at once, so
# spread the resulting refetches over this many seconds (unless the
# profiles are actually asked for first, which fetches right away).
_VERSION_JITTER_MAX = 60.0

_cachelog = logging.getLogger(ClientLoggerName.CACHE.value)


@ioprepped
@dataclass
class CloudProfilesCacheData:
    """Cloud profiles for one account, as cached on disk."""

    #: Account these profiles belong to.
    account_id: Annotated[str, IOAttrs('a')]

    #: Live-data profiles state these profiles correspond to.
    profiles_state: Annotated[str, IOAttrs('s')]

    #: Live-data purchases state at fetch time. Composed profiles
    #: depend on entitlements, so a purchases change also stales them.
    purchases_state: Annotated[str | None, IOAttrs('ps')]

    #: Fleet-wide classic cache version at fetch time (None if the
    #: server didn't send one; then a later known version stales us).
    cache_version: Annotated[str | None, IOAttrs('cv', soft_default=None)]

    #: One cloud-composed character json string per profile.
    profiles: Annotated[list[str], IOAttrs('p')]


class CloudProfiles:
    """Syncs and caches the primary account's cloud profiles.

    Owned by :class:`~baclassic.ClassicAppSubsystem`; driven by the
    classic app-mode (primary-account changes and live account data).

    :meta private:
    """

    def __init__(self) -> None:
        # (Resolved lazily; we may be constructed before app env is.)
        self._cache_path: str | None = None
        self._writer: _CacheWriter | None = None
        self._cache: CloudProfilesCacheData | None = None
        self._cache_loaded = False

        self._account_id: str | None = None

        # Live-data values (valid only when _have_live_state is True).
        self._have_live_state = False
        self._target_profiles_state: str | None = None
        self._target_purchases_state: str | None = None
        self._target_cache_version: str | None = None

        # Pending jittered refetch after a cache-version-only change.
        self._version_timer: babase.AppTimer | None = None

        # A None live profiles state means the server hasn't computed
        # one for this account (or an older basn node didn't send it).
        # We then fetch once anyway and trust what we get; the server
        # repairs the live state as a side effect.
        self._untargeted_fetch_done = False

        self._request_in_flight = False
        self._retry_timer: babase.AppTimer | None = None
        self._attempts = 0
        self._warned_mismatch = False

    def get_usable_profiles(self) -> list[str] | None:
        """Return cloud profile json strings if we can use them.

        Returns None if cloud profiles are missing or out of date for
        the current account; callers should then fall back to legacy
        profiles (and let the player know they're doing so).
        """
        assert babase.in_logic_thread()
        cache = self._get_cache()
        plus = babase.app.plus
        if cache is None or plus is None:
            return None

        primary = plus.accounts.primary
        if primary is None:
            # No verified account. If credentials are set we're most
            # likely just offline (or not yet verified), in which case
            # the cached profiles are the best we have.
            usable = plus.accounts.have_primary_credentials()
        else:
            # Only when we know the live state can we call the cache
            # stale; before (or without) live data it's our best info.
            # A cache-version mismatch alone doesn't make it unusable
            # (see the module docs), but someone wanting the profiles
            # is the cue to stop waiting out the jitter.
            if self._version_timer is not None:
                self._version_timer = None
                self._possibly_request()
            usable = cache.account_id == primary.accountid and (
                not self._have_live_state
                or self._cache_is_current(ignore_version=True)
            )
        return list(cache.profiles) if usable else None

    def set_account(self, account_id: str | None) -> None:
        """Called when the primary account changes."""
        assert babase.in_logic_thread()
        if account_id == self._account_id:
            return
        self._account_id = account_id
        self._have_live_state = False
        self._target_profiles_state = None
        self._target_purchases_state = None
        self._target_cache_version = None
        self._untargeted_fetch_done = False
        self._retry_timer = None
        self._version_timer = None
        self._attempts = 0
        self._warned_mismatch = False

        # Make sure we've got the cache loaded while we're still in a
        # startup-ish state (it is read on the logic thread).
        if account_id is not None:
            self._get_cache()

    def on_live_state(
        self,
        profiles_state: str | None,
        purchases_state: str | None,
        cache_version: str | None,
    ) -> None:
        """Called with each set of live account data we receive."""
        assert babase.in_logic_thread()
        if self._account_id is None:
            return

        version_only = (
            self._have_live_state
            and profiles_state == self._target_profiles_state
            and purchases_state == self._target_purchases_state
            and cache_version != self._target_cache_version
        )
        changed = (
            version_only
            or not self._have_live_state
            or profiles_state != self._target_profiles_state
            or purchases_state != self._target_purchases_state
        )
        self._have_live_state = True
        self._target_profiles_state = profiles_state
        self._target_purchases_state = purchases_state
        self._target_cache_version = cache_version

        if not changed:
            return

        # New target; start the backoff over.
        self._attempts = 0
        self._warned_mismatch = False

        if self._cache_is_current():
            self._retry_timer = None
            self._version_timer = None
            return

        self._retry_timer = None
        if version_only:
            # Everyone on the fleet just heard this; spread the load.
            delay = random.uniform(0.0, _VERSION_JITTER_MAX)
            babase.accountlog.debug(
                'Classic cache version is now %s; ours is %s.'
                ' Will refetch cloud profiles in %.1fs.',
                cache_version,
                None if self._cache is None else self._cache.cache_version,
                delay,
            )
            self._version_timer = babase.AppTimer(
                delay, babase.WeakCallStrict(self._on_version_timer)
            )
            return

        babase.accountlog.debug(
            'Cloud profiles state is %s (purchases %s, version %s);'
            ' ours is %s. Will fetch.',
            profiles_state,
            purchases_state,
            cache_version,
            None if self._cache is None else self._cache.profiles_state,
        )
        self._version_timer = None
        self._possibly_request()

    def _on_version_timer(self) -> None:
        self._version_timer = None
        self._possibly_request()

    def _cache_is_current(self, *, ignore_version: bool = False) -> bool:
        cache = self._get_cache()
        if (
            cache is None
            or self._account_id is None
            or cache.account_id != self._account_id
            or cache.purchases_state != self._target_purchases_state
        ):
            return False
        if (
            not ignore_version
            and self._target_cache_version is not None
            and cache.cache_version != self._target_cache_version
        ):
            return False
        if self._target_profiles_state is None:
            return self._untargeted_fetch_done
        return cache.profiles_state == self._target_profiles_state

    def _needs_fetch(self) -> bool:
        return (
            self._account_id is not None
            and self._have_live_state
            and not self._cache_is_current()
        )

    def _on_retry_timer(self) -> None:
        self._retry_timer = None
        self._possibly_request()

    def _schedule_retry(self) -> None:
        if not self._needs_fetch() or self._retry_timer is not None:
            return
        delay = min(
            _RETRY_DELAY_MIN * (2 ** min(self._attempts, 8)),
            _RETRY_DELAY_MAX,
        )
        self._retry_timer = babase.AppTimer(
            delay, babase.WeakCallStrict(self._on_retry_timer)
        )

    def _possibly_request(self) -> None:
        if self._request_in_flight or not self._needs_fetch():
            return

        plus = babase.app.plus
        assert plus is not None
        primary = plus.accounts.primary
        account_id = self._account_id
        if (
            primary is None
            or account_id is None
            or primary.accountid != account_id
        ):
            # Account in flux; we'll hear about it via set_account().
            return

        self._request_in_flight = True
        self._attempts += 1
        babase.accountlog.debug('Requesting cloud profiles...')
        with primary:
            plus.cloud.send_message_cb(
                bacommon.classic.GetClassicProfilesMessage(),
                on_response=babase.WeakCallPartial(
                    self._on_response,
                    account_id,
                    self._target_purchases_state,
                    self._target_cache_version,
                ),
            )

    def _on_response(
        self,
        account_id: str,
        purchases_state: str | None,
        cache_version: str | None,
        response: bacommon.classic.GetClassicProfilesResponse | Exception,
    ) -> None:
        assert self._request_in_flight
        self._request_in_flight = False
        try:
            self._handle_response(
                account_id, purchases_state, cache_version, response
            )
        except Exception:
            babase.accountlog.exception(
                'Error handling cloud profiles response.'
            )
        # Keep at it until we're current.
        self._schedule_retry()

    def _handle_response(
        self,
        account_id: str,
        purchases_state: str | None,
        cache_version: str | None,
        response: bacommon.classic.GetClassicProfilesResponse | Exception,
    ) -> None:
        if isinstance(response, Exception):
            if isinstance(response, CommunicationError):
                # Expected when offline/etc.
                babase.accountlog.debug(
                    'Communication error fetching cloud profiles: %s',
                    response,
                )
            else:
                babase.accountlog.error(
                    'Error fetching cloud profiles: %s', response
                )
            return

        # Ignore anything that no longer applies.
        if (
            account_id != self._account_id
            or purchases_state != self._target_purchases_state
            or cache_version != self._target_cache_version
            or not self._needs_fetch()
        ):
            return

        # None means the server couldn't provide profiles (it logs why).
        if response.profiles_state is None:
            babase.accountlog.debug('Cloud profiles unavailable; will retry.')
            return

        if (
            self._target_profiles_state is not None
            and response.profiles_state != self._target_profiles_state
        ):
            # Normally just a race with an update in flight; if it
            # persists, something's off server-side.
            if (
                self._attempts >= _MISMATCH_WARN_ATTEMPTS
                and not self._warned_mismatch
            ):
                self._warned_mismatch = True
                babase.accountlog.warning(
                    'Cloud profiles state mismatch persists after %d'
                    ' attempts (live %s, fetched %s).',
                    self._attempts,
                    self._target_profiles_state,
                    response.profiles_state,
                )
            return

        profiles = _valid_profiles(response.profiles)
        if len(profiles) != len(response.profiles):
            babase.accountlog.error(
                'Got %d invalid cloud profile(s) of %d; dropping them.',
                len(response.profiles) - len(profiles),
                len(response.profiles),
            )

        self._cache = CloudProfilesCacheData(
            account_id=account_id,
            profiles_state=response.profiles_state,
            purchases_state=purchases_state,
            cache_version=cache_version,
            profiles=profiles,
        )
        if self._target_profiles_state is None:
            self._untargeted_fetch_done = True
        self._retry_timer = None
        self._attempts = 0

        try:
            if self._writer is None:
                self._writer = _CacheWriter(self._get_cache_path())
            self._writer.write(_encode_cache(self._cache))
        except Exception:
            babase.accountlog.exception(
                'Error scheduling cloud profiles cache write.'
            )

        babase.accountlog.debug(
            'Updated cloud profiles to state %s (%d profile(s)).',
            response.profiles_state,
            len(profiles),
        )

    def _get_cache_path(self) -> str:
        if self._cache_path is None:
            self._cache_path = os.path.join(
                babase.app.env.cache_directory, CACHE_FILE_NAME
            )
        return self._cache_path

    def _get_cache(self) -> CloudProfilesCacheData | None:
        if not self._cache_loaded:
            self._cache_loaded = True
            try:
                self._cache = _load_cache(self._get_cache_path())
            except Exception:
                # _load_cache handles expected failures itself; this is
                # a catch-all so a bug here can never break the app.
                _cachelog.exception(
                    'Unexpected error loading cloud profiles cache.'
                )
                self._cache = None
        return self._cache


def _valid_profiles(profiles: list[str]) -> list[str]:
    """Return the subset of profile strings that are json objects."""
    out: list[str] = []
    for profile in profiles:
        try:
            if isinstance(json.loads(profile), dict):
                out.append(profile)
        except Exception:
            pass
    return out


def _encode_cache(data: CloudProfilesCacheData) -> str:
    """Encode cache data to file contents (versioned + checksummed)."""
    payload = dataclass_to_json(data)
    return json.dumps(
        {
            'v': _CACHE_FORMAT_VERSION,
            'h': hashlib.sha256(payload.encode()).hexdigest(),
            'd': payload,
        }
    )


def _discard_cache_file(path: str, reason: str) -> None:
    """Warn about and remove an unusable cache file."""
    _cachelog.warning(
        'Discarding cloud profiles cache (%s); will refetch.', reason
    )
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError as exc:
        _cachelog.warning('Unable to remove bad cloud profiles cache: %s', exc)


def _load_cache(path: str) -> CloudProfilesCacheData | None:
    """Load and fully validate the cache file; None if unusable."""
    # pylint: disable=too-many-return-statements
    try:
        size = os.path.getsize(path)
    except FileNotFoundError:
        _cachelog.debug('No cloud profiles cache found.')
        return None
    except OSError as exc:
        _cachelog.warning('Unable to access cloud profiles cache: %s', exc)
        return None

    if size > _MAX_CACHE_FILE_BYTES:
        _discard_cache_file(path, f'oversized: {size} bytes')
        return None

    try:
        with open(path, 'rb') as infile:
            raw = infile.read(_MAX_CACHE_FILE_BYTES + 1)
    except OSError as exc:
        _cachelog.warning('Unable to read cloud profiles cache: %s', exc)
        return None

    try:
        envelope = json.loads(raw.decode())
    except Exception:
        _discard_cache_file(path, 'unparseable')
        return None

    if not isinstance(envelope, dict):
        _discard_cache_file(path, 'not a json object')
        return None

    version = envelope.get('v')
    if version != _CACHE_FORMAT_VERSION:
        # Written by a different client version; not an error.
        _cachelog.info(
            'Ignoring cloud profiles cache with format version %r.', version
        )
        return None

    payload = envelope.get('d')
    checksum = envelope.get('h')
    if not isinstance(payload, str) or not isinstance(checksum, str):
        _discard_cache_file(path, 'malformed envelope')
        return None

    if hashlib.sha256(payload.encode()).hexdigest() != checksum:
        _discard_cache_file(path, 'checksum mismatch')
        return None

    try:
        data = dataclass_from_json(CloudProfilesCacheData, payload)
    except Exception as exc:
        _discard_cache_file(path, f'invalid payload: {exc}')
        return None

    if len(_valid_profiles(data.profiles)) != len(data.profiles):
        _discard_cache_file(path, 'invalid profile json')
        return None

    _cachelog.debug(
        'Loaded cloud profiles cache (state %s, version %s, %d profiles).',
        data.profiles_state,
        data.cache_version,
        len(data.profiles),
    )
    return data


class _CacheWriter:
    """Writes cache contents on a background thread, atomically.

    Writes are coalesced and ordered: only the most recent contents
    passed to :meth:`write` are guaranteed to land, and older contents
    can never overwrite newer ones.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._pending: str | None = None
        self._worker_running = False

    def write(self, contents: str) -> None:
        """Schedule contents to be written."""
        with self._lock:
            self._pending = contents
            if self._worker_running:
                return
            self._worker_running = True
        try:
            babase.app.threadpool.submit_no_wait(self._run)
        except Exception:
            with self._lock:
                self._worker_running = False
            raise

    def _run(self) -> None:
        while True:
            with self._lock:
                contents = self._pending
                self._pending = None
                if contents is None:
                    self._worker_running = False
                    return
            self._write_atomic(contents)

    def _write_atomic(self, contents: str) -> None:
        tmppath: str | None = None
        try:
            dirname = os.path.dirname(self._path)
            os.makedirs(dirname, exist_ok=True)
            fd, tmppath = tempfile.mkstemp(
                dir=dirname, prefix=f'.tmp_{CACHE_FILE_NAME}_'
            )
            with os.fdopen(fd, 'w', encoding='utf-8') as outfile:
                outfile.write(contents)
                outfile.flush()
                os.fsync(outfile.fileno())
            os.replace(tmppath, self._path)
            tmppath = None
            _fsync_dir(dirname)
            _cachelog.debug('Wrote cloud profiles cache.')
        except OSError as exc:
            # Disk full, permissions, etc. The previous file (if any)
            # is untouched; we'll try again on the next update.
            _cachelog.warning('Unable to write cloud profiles cache: %s', exc)
        except Exception:
            _cachelog.exception(
                'Unexpected error writing cloud profiles cache.'
            )
        finally:
            if tmppath is not None:
                try:
                    os.remove(tmppath)
                except OSError:
                    pass


def _fsync_dir(dirname: str) -> None:
    """Make a rename durable (POSIX only; best-effort)."""
    if os.name != 'posix':
        return
    try:
        dirfd = os.open(dirname, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dirfd)
    except OSError:
        pass
    finally:
        os.close(dirfd)
