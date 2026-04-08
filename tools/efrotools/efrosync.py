# Released under the MIT License. See LICENSE for details.
#
"""Centralized file synchronization across local repos.

A simplified replacement for the original efrosync system. Instead of
embedding hash markers in synced files and using an upstream/downstream
model, this system:

- Treats all repo copies as peers (no upstream/downstream).
- Stores hashes and state in a central ``~/.efrosync/`` directory.
- Supports glob patterns for worktree directories.
- Syncs when exactly one copy has changed; errors on ambiguity.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import glob as globmod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from efro.terminal import Clr

if TYPE_CHECKING:
    pass

# Paths for config, state, and lock.
CONFIG_DIR = Path.home() / '.efrosync'
CONFIG_PATH = CONFIG_DIR / 'config.json'
STATE_PATH = CONFIG_DIR / 'state.json'
LOCK_PATH = CONFIG_DIR / 'lock'


# ---- data types ----


@dataclass
class RepoConfig:
    """A repo participating in sync."""

    path: str
    worktree_globs: list[str] = field(default_factory=list)


@dataclass
class SyncGroupConfig:
    """A directory or file to keep in sync across repos."""

    path: str
    repos: list[str] = field(default_factory=list)
    repo_path_overrides: dict[str, str] = field(default_factory=dict)


@dataclass
class Config:
    """Top-level efrosync config."""

    repos: dict[str, RepoConfig]
    sync_groups: list[SyncGroupConfig]


@dataclass
class FileStateEntry:
    """Per-file sync state."""

    synced_hash: str
    mtimes: dict[str, float] = field(default_factory=dict)


@dataclass
class SyncState:
    """All stored sync state."""

    files: dict[str, FileStateEntry] = field(default_factory=dict)


@dataclass
class SyncLocation:
    """A resolved location for a sync group."""

    label: str
    abs_path: str


@dataclass
class _PendingSync:
    """A file copy to perform after validation passes."""

    source_path: str
    dst_paths: list[str]
    skey: str
    new_hash: str
    current_hashes: dict[str, str]
    display: str
    src_label: str
    dst_labels: list[str]


@dataclass
class _PendingStateUpdate:
    """A state entry to update after validation passes."""

    skey: str
    new_hash: str
    current_hashes: dict[str, str]


@dataclass
class _SyncContext:
    """Mutable state for a sync run."""

    config: Config
    state: SyncState
    errors: list[str] = field(default_factory=list)
    pending_syncs: list[_PendingSync] = field(default_factory=list)
    pending_state_updates: list[_PendingStateUpdate] = field(
        default_factory=list
    )
    visited_keys: set[str] = field(default_factory=set)
    checked_count: int = 0
    dry_run: bool = False
    check: bool = False


# ---- config / state persistence ----


def load_config() -> Config | None:
    """Load config from ~/.efrosync/config.json.

    Returns ``None`` if no config file exists (efrosync is not
    configured on this machine).
    """
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, encoding='utf-8') as f:
        raw = json.load(f)

    repos: dict[str, RepoConfig] = {}
    for name, rdata in raw.get('repos', {}).items():
        if isinstance(rdata, str):
            repos[name] = RepoConfig(path=rdata)
        else:
            repos[name] = RepoConfig(
                path=rdata['path'],
                worktree_globs=rdata.get('worktree_globs', []),
            )

    groups: list[SyncGroupConfig] = []
    for gdata in raw.get('sync_groups', []):
        groups.append(
            SyncGroupConfig(
                path=gdata['path'],
                repos=gdata.get('repos', []),
                repo_path_overrides=gdata.get('repo_path_overrides', {}),
            )
        )
    return Config(repos=repos, sync_groups=groups)


def load_state() -> SyncState:
    """Load state from ~/.efrosync/state.json."""
    if not STATE_PATH.exists():
        return SyncState()
    with open(STATE_PATH, encoding='utf-8') as f:
        raw = json.load(f)
    state = SyncState()
    for key, fdata in raw.get('files', {}).items():
        state.files[key] = FileStateEntry(
            synced_hash=fdata['synced_hash'],
            mtimes=fdata.get('mtimes', {}),
        )
    return state


def save_state(state: SyncState) -> None:
    """Save state to ~/.efrosync/state.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    raw: dict = {
        'files': {
            key: {
                'synced_hash': entry.synced_hash,
                'mtimes': entry.mtimes,
            }
            for key, entry in sorted(state.files.items())
        }
    }
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(raw, f, indent=2, sort_keys=False)
        f.write('\n')


# ---- hashing and file utils ----


def _hash_file(path: str) -> str:
    """Return hex MD5 hash of file contents."""
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _is_syncable(name: str) -> bool:
    """Should this filename be included in sync?"""
    if name.startswith('.') and name != '.editorconfig':
        return False
    if name == '__pycache__':
        return False
    if name.endswith('.pyc'):
        return False
    if name.startswith('flycheck_'):
        return False
    return True


def _discover_files(dirpath: str) -> list[str]:
    """Discover syncable files under a directory (or a single file).

    Returns paths relative to dirpath. For a single file, returns
    ``['.']`` as a sentinel.
    """
    if os.path.isfile(dirpath):
        return ['.']

    result: list[str] = []
    for root, dirs, files in os.walk(dirpath):
        dirs[:] = [d for d in sorted(dirs) if _is_syncable(d)]
        for fname in sorted(files):
            if not _is_syncable(fname):
                continue
            relpath = os.path.relpath(os.path.join(root, fname), dirpath)
            result.append(relpath)
    return result


def _state_key(group_path: str, rel_file: str) -> str:
    """Build a unique state key for a file in a sync group."""
    if rel_file == '.':
        return group_path
    return f'{group_path}/{rel_file}'


def _abs_file_path(loc_abs_path: str, rel_file: str) -> str:
    """Resolve the absolute path of a file within a sync location."""
    if rel_file == '.':
        return loc_abs_path
    return os.path.join(loc_abs_path, rel_file)


def _display_path(group_path: str, rel_file: str) -> str:
    """Human-readable display path for a synced file."""
    if rel_file == '.':
        return group_path
    return f'{group_path}/{rel_file}'


def _label_for_path(
    abs_path: str,
    rel_file: str,
    locations: list[SyncLocation],
) -> str:
    """Find the label for a location given an absolute file path."""
    for loc in locations:
        if _abs_file_path(loc.abs_path, rel_file) == abs_path:
            return loc.label
    return '?'


# ---- location resolution ----


def _resolve_locations(
    config: Config, group: SyncGroupConfig
) -> list[SyncLocation]:
    """Resolve all locations for a sync group, expanding worktrees."""
    from efro.error import CleanError

    locations: list[SyncLocation] = []

    all_repo_names = list(group.repos) + list(group.repo_path_overrides.keys())

    for repo_name in all_repo_names:
        repo_cfg = config.repos.get(repo_name)
        if repo_cfg is None:
            raise CleanError(
                f'Sync group "{group.path}" references unknown'
                f' repo "{repo_name}".'
            )

        rel_path = group.repo_path_overrides.get(repo_name, group.path)

        # Main repo location.
        main_abs = os.path.join(repo_cfg.path, rel_path)
        if os.path.exists(main_abs):
            locations.append(SyncLocation(label=repo_name, abs_path=main_abs))

        # Worktree locations.
        for wt_glob in repo_cfg.worktree_globs:
            if os.path.isabs(wt_glob):
                pattern = wt_glob
            else:
                pattern = os.path.join(repo_cfg.path, wt_glob)
            for wt_path in sorted(globmod.glob(pattern)):
                if not os.path.isdir(wt_path):
                    continue
                wt_abs = os.path.join(wt_path, rel_path)
                if os.path.exists(wt_abs):
                    wt_label = f'{repo_name}' f'[{os.path.basename(wt_path)}]'
                    locations.append(
                        SyncLocation(label=wt_label, abs_path=wt_abs)
                    )

    return locations


def _format_all_repos(config: Config) -> None:
    """Run 'make format' in all repos in parallel."""
    import subprocess
    import concurrent.futures

    repo_paths = [
        r.path for r in config.repos.values() if os.path.isdir(r.path)
    ]

    print(f'{Clr.BLD}Formatting {len(repo_paths)}' f' projects...{Clr.RST}')

    def _fmt(path: str) -> None:
        subprocess.run(
            ['make', 'format'],
            cwd=path,
            check=True,
            capture_output=True,
        )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(repo_paths)
    ) as executor:
        list(executor.map(_fmt, repo_paths))


# ---- core sync logic ----


def _check_file_presence(
    group: SyncGroupConfig,
    locations: list[SyncLocation],
    file_sets: dict[str, set[str]],
    all_files: list[str],
    errors: list[str],
) -> None:
    """Check that every file exists in all locations."""
    for rel_file in all_files:
        present_in = [
            loc.label
            for loc in locations
            if rel_file in file_sets[loc.abs_path]
        ]
        missing_from = [
            loc.label
            for loc in locations
            if rel_file not in file_sets[loc.abs_path]
        ]
        if missing_from:
            display = _display_path(group.path, rel_file)
            errors.append(
                f'{display}: present in'
                f' {', '.join(present_in)} but missing'
                f' from {', '.join(missing_from)}'
            )


def _compute_hashes(
    ctx: _SyncContext,
    skey: str,
    rel_file: str,
    locations: list[SyncLocation],
) -> dict[str, str]:
    """Compute current hash at each location for a file."""
    current_hashes: dict[str, str] = {}
    for loc in locations:
        abs_file = _abs_file_path(loc.abs_path, rel_file)
        cur_mtime = os.path.getmtime(abs_file)
        stored = ctx.state.files.get(skey)
        if stored is not None and stored.mtimes.get(abs_file) == cur_mtime:
            current_hashes[abs_file] = stored.synced_hash
        else:
            current_hashes[abs_file] = _hash_file(abs_file)
    return current_hashes


def _queue_state_update(
    ctx: _SyncContext,
    skey: str,
    new_hash: str,
    current_hashes: dict[str, str],
) -> None:
    """Queue a state update to apply after validation."""
    ctx.pending_state_updates.append(
        _PendingStateUpdate(
            skey=skey,
            new_hash=new_hash,
            current_hashes=current_hashes,
        )
    )


def _process_file(
    ctx: _SyncContext,
    group: SyncGroupConfig,
    rel_file: str,
    locations: list[SyncLocation],
) -> None:
    """Process a single file across all its locations."""
    ctx.checked_count += 1
    skey = _state_key(group.path, rel_file)
    ctx.visited_keys.add(skey)
    display = _display_path(group.path, rel_file)

    current_hashes = _compute_hashes(ctx, skey, rel_file, locations)
    fi = _FileInfo(
        current_hashes=current_hashes,
        rel_file=rel_file,
        locations=locations,
        display=display,
        skey=skey,
    )
    unique_hashes = set(current_hashes.values())

    # All copies match — just ensure state is current.
    if len(unique_hashes) == 1:
        the_hash = next(iter(unique_hashes))
        stored = ctx.state.files.get(skey)
        if stored is None or stored.synced_hash != the_hash:
            _queue_state_update(ctx, skey, the_hash, current_hashes)
        return

    # Not all equal — need stored state to decide direction.
    stored = ctx.state.files.get(skey)
    if stored is None:
        ctx.errors.append(
            f'{display}: files differ across locations'
            ' and no prior sync state exists.'
            ' Manually align them first.'
        )
        return

    _resolve_differences(ctx, stored.synced_hash, fi)


@dataclass
class _FileInfo:
    """Bundle of per-file state passed between sync helpers."""

    current_hashes: dict[str, str]
    rel_file: str
    locations: list[SyncLocation]
    display: str
    skey: str


def _resolve_differences(
    ctx: _SyncContext,
    synced_hash: str,
    fi: _FileInfo,
) -> None:
    """Handle a file where not all locations match."""
    changed = [p for p, h in fi.current_hashes.items() if h != synced_hash]
    unchanged = [p for p, h in fi.current_hashes.items() if h == synced_hash]

    if not changed:
        return

    changed_hashes = {fi.current_hashes[p] for p in changed}

    if len(changed_hashes) > 1:
        labels = [
            _label_for_path(p, fi.rel_file, fi.locations) for p in changed
        ]
        ctx.errors.append(
            f'{fi.display}: conflicting changes in'
            f' {', '.join(labels)}. Resolve manually.'
        )
        return

    new_hash = next(iter(changed_hashes))

    if not unchanged:
        # All changed the same way.
        _queue_state_update(ctx, fi.skey, new_hash, fi.current_hashes)
        return

    _do_sync(ctx, fi, changed, unchanged, new_hash)


def _do_sync(
    ctx: _SyncContext,
    fi: _FileInfo,
    changed: list[str],
    unchanged: list[str],
    new_hash: str,
) -> None:
    """Queue a file sync from changed to unchanged locations."""
    source_path = changed[0]
    src_label = _label_for_path(source_path, fi.rel_file, fi.locations)
    dst_labels = [
        _label_for_path(p, fi.rel_file, fi.locations) for p in unchanged
    ]

    if ctx.check:
        ctx.errors.append(
            f'{fi.display}: changed in' f' {src_label}, needs sync.'
        )
        return

    ctx.pending_syncs.append(
        _PendingSync(
            source_path=source_path,
            dst_paths=list(unchanged),
            skey=fi.skey,
            new_hash=new_hash,
            current_hashes=fi.current_hashes,
            display=fi.display,
            src_label=src_label,
            dst_labels=dst_labels,
        )
    )


def run_efrosync(
    *,
    dry_run: bool = False,
    check: bool = False,
) -> None:
    """Run the efrosync process."""
    from efro.error import CleanError

    config = load_config()
    if config is None:
        return

    # Run formatting in all repos first so synced files are in
    # their final form. This avoids the round-trip where sync
    # propagates unformatted code and then preflight reformats it.
    if not check:
        _format_all_repos(config)

    ctx = _SyncContext(
        config=config,
        state=load_state(),
        dry_run=dry_run,
        check=check,
    )

    # Validation pass: check all groups, compute hashes, queue
    # actions. No files are modified until validation succeeds.
    for group in ctx.config.sync_groups:
        locations = _resolve_locations(ctx.config, group)
        if len(locations) < 2:
            continue

        file_sets: dict[str, set[str]] = {}
        for loc in locations:
            file_sets[loc.abs_path] = set(_discover_files(loc.abs_path))

        all_files = sorted(set().union(*file_sets.values()))

        err_count_before = len(ctx.errors)
        _check_file_presence(group, locations, file_sets, all_files, ctx.errors)
        if len(ctx.errors) > err_count_before:
            # Can't process files if some are missing; but
            # continue to check remaining groups.
            continue

        for rel_file in all_files:
            _process_file(ctx, group, rel_file, locations)

    if ctx.errors:
        print(f'{Clr.RED}efrosync errors:{Clr.RST}')
        for err in ctx.errors:
            print(f'  {Clr.RED}{err}{Clr.RST}')
        raise CleanError(f'efrosync: {len(ctx.errors)} error(s) found.')

    # Apply pass: all validation passed, now write files and
    # update state.
    _apply_pending(ctx)

    _print_summary(ctx)


def _apply_pending(ctx: _SyncContext) -> None:
    """Apply all queued syncs and state updates."""
    state_updated = False

    for su in ctx.pending_state_updates:
        new_mtimes = {p: os.path.getmtime(p) for p in su.current_hashes}
        ctx.state.files[su.skey] = FileStateEntry(
            synced_hash=su.new_hash, mtimes=new_mtimes
        )
        state_updated = True

    for ps in ctx.pending_syncs:
        if ctx.dry_run:
            print(
                f'  Would sync {ps.display}:'
                f' {ps.src_label}'
                f' -> {', '.join(ps.dst_labels)}'
            )
        else:
            for dst_path in ps.dst_paths:
                shutil.copy2(ps.source_path, dst_path)
            new_mtimes = {p: os.path.getmtime(p) for p in ps.current_hashes}
            ctx.state.files[ps.skey] = FileStateEntry(
                synced_hash=ps.new_hash, mtimes=new_mtimes
            )
            state_updated = True
            print(
                f'  {Clr.BLU}Synced {ps.display}:'
                f' {ps.src_label}'
                f' -> {', '.join(ps.dst_labels)}'
                f'{Clr.RST}'
            )

    # Prune state entries not visited this run (removed files,
    # repos, groups, or worktrees) and stale mtime entries
    # within visited entries (e.g. removed worktrees).
    stale_keys = [k for k in ctx.state.files if k not in ctx.visited_keys]
    for k in stale_keys:
        del ctx.state.files[k]
        state_updated = True

    for entry in ctx.state.files.values():
        stale = [p for p in entry.mtimes if not os.path.exists(p)]
        for p in stale:
            del entry.mtimes[p]
        if stale:
            state_updated = True

    if state_updated:
        save_state(ctx.state)


def _print_summary(ctx: _SyncContext) -> None:
    """Print the sync summary."""
    synced = len(ctx.pending_syncs)
    if ctx.dry_run:
        if synced:
            print(f'{Clr.YLW}{synced} file(s)' f' would be synced.{Clr.RST}')
        else:
            print(
                f'{Clr.GRN}All {ctx.checked_count} files'
                f' are in sync.{Clr.RST}'
            )
    elif ctx.check:
        print(
            f'{Clr.GRN}All {ctx.checked_count} files' f' are in sync.{Clr.RST}'
        )
    elif synced:
        print(f'{Clr.GRN}{synced} file(s) synced' f' successfully.{Clr.RST}')
    else:
        print(
            f'{Clr.GRN}All {ctx.checked_count} files' f' are in sync.{Clr.RST}'
        )


# ---- lock file ----


class SyncLock:
    """File-based lock to prevent concurrent syncs."""

    def __init__(self) -> None:
        self._fd: int | None = None

    def __enter__(self) -> SyncLock:
        from efro.error import CleanError

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self._fd)
            self._fd = None
            raise CleanError(
                'Another efrosync process is running. If this'
                ' is not the case, remove ~/.efrosync/lock and'
                ' retry.'
            ) from None
        return self

    def __exit__(self, *_args: object) -> None:
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None


# ---- entry point ----


def efrosync_main() -> None:
    """Entry point for the efrosync pcommand."""
    import sys

    from efro.error import CleanError

    args = sys.argv[2:]

    dry_run = '--dry-run' in args
    check = '--check' in args

    if dry_run and check:
        raise CleanError('Cannot use --dry-run and --check together.')

    with SyncLock():
        run_efrosync(dry_run=dry_run, check=check)
