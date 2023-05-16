# Released under the MIT License. See LICENSE for details.
#
"""Functionality for syncing specific directories between different projects.

This can be preferable vs using shared git subrepos for certain use cases.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import Sequence


class Mode(Enum):
    """Modes for sync operations."""

    PULL = 'pull'  # Pull updates from theirs to ours; errors if ours changed.
    FULL = 'full'  # Like pull but also push changes back to src if possible.
    LIST = 'list'  # Simply list all sync operations that would occur.
    FORCE = 'force'  # Pull all from src without checking for dst changes.
    CHECK = 'check'  # Make no changes; errors if dst has changed since sync.


def _valid_filename(fname: str) -> bool:
    """Is this a file we're ok with syncing?

    (we need to be able to append a comment without breaking it)
    """
    if os.path.basename(fname) != fname:
        raise ValueError(f'{fname} is not a simple filename.')
    if fname in [
        'requirements.txt',
        'pylintrc',
        'clang-format',
        'pycheckers',
        'style.yapf',
        'test_task_bin',
        '.editorconfig',
        'cloudshell',
        'vmshell',
        'editorconfig',
    ]:
        return True
    return (
        any(fname.endswith(ext) for ext in ('.py', '.pyi'))
        and 'flycheck_' not in fname
    )


@dataclass
class SyncItem:
    """Defines a file or directory to be synced from another project."""

    src_project_id: str
    src_path: str
    dst_path: str | None = None


def run_standard_syncs(
    projectroot: Path, mode: Mode, syncitems: Sequence[SyncItem]
) -> None:
    """Run a standard set of syncs.

    Syncitems should be a list of tuples consisting of a src project name,
    a src subpath, and optionally a dst subpath (src will be used by default).
    """
    # pylint: disable=too-many-locals
    from efrotools import getlocalconfig

    localconfig = getlocalconfig(projectroot)
    total_count = 0
    verbose = False
    for syncitem in syncitems:
        assert isinstance(syncitem, SyncItem)
        src_project = syncitem.src_project_id
        src_subpath = syncitem.src_path
        dst_subpath = (
            syncitem.dst_path
            if syncitem.dst_path is not None
            else syncitem.src_path
        )
        dstname = os.path.basename(dst_subpath)
        if mode == Mode.CHECK:
            if verbose:
                print(f'Checking sync target {dstname}...')
            count = check_path(Path(dst_subpath))
            total_count += count
            if verbose:
                print(f'Sync check passed for {count} items.')
        else:
            link_entry = f'linked_{src_project}'

            # Actual syncs require localconfig entries.
            if link_entry not in localconfig:
                print(f'No link entry for {src_project}; skipping sync entry.')
                continue
            src = Path(localconfig[link_entry], src_subpath)
            if verbose:
                print(f'Processing {dstname} in {mode.name} mode...')
            count = sync_paths(src_project, src, Path(dst_subpath), mode)
            total_count += count
            if verbose:
                if mode in [Mode.LIST, Mode.CHECK]:
                    print(f'Scanned {count} items.')
                else:
                    print(f'Sync successful for {count} items.')

    projbasename = os.path.basename(projectroot)
    if mode in [Mode.LIST, Mode.CHECK]:
        print(f'Checked {total_count} synced items in {projbasename}.')
    else:
        print(f'Synced {total_count} items in {projbasename}.')


def sync_paths(src_proj: str, src: Path, dst: Path, mode: Mode) -> int:
    """Sync src and dst paths."""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    if mode == Mode.CHECK:
        raise ValueError('sync_paths cannot be called in CHECK mode')
    if not (src.is_dir() or src.is_file()):
        raise ValueError(f'src path is not a dir or file: {src}')

    changed_error_dst_files: list[Path] = []

    # Build a list of all valid source files and their equivalent paths in dst.
    allpaths: list[tuple[Path, Path]] = []

    if src.is_file():
        if not _valid_filename(src.name):
            raise ValueError(f'provided sync-path {src} is not syncable')
        allpaths.append((src, dst))
    else:
        for root, _dirs, fnames in os.walk(src):
            for fname in fnames:
                if _valid_filename(fname):
                    srcpathfull = Path(root, fname)
                    relpath = srcpathfull.relative_to(src)
                    dstpathfull = Path(dst, relpath)
                    allpaths.append((srcpathfull, dstpathfull))
    for srcfile, dstfile in allpaths:
        if not srcfile.is_file():
            raise RuntimeError(f'Invalid src file: {srcfile}.')
        dstfile.parent.mkdir(parents=True, exist_ok=True)
        with srcfile.open() as infile:
            srcdata = infile.read()
        src_hash = string_hash(srcdata)

        if not dstfile.is_file() or mode == Mode.FORCE:
            if mode == Mode.LIST:
                print(
                    f'Would pull from {src_proj}:'
                    f' {Clr.SGRN}{dstfile}{Clr.RST}'
                )
            else:
                print(f'Pulling from {src_proj}: {Clr.SGRN}{dstfile}{Clr.RST}')

                # No dst file; pull src across.
                with dstfile.open('w') as outfile:
                    outfile.write(add_marker(src_proj, srcdata))
            continue

        marker_hash, dst_hash, dstdata = get_dst_file_info(dstfile)

        # Ok, we've now got hashes for src and dst as well as a 'last-known'
        # hash. If only one of the two files differs from it we can
        # do a directional sync. If they both differ then we're out of luck.
        if src_hash != marker_hash and dst_hash == marker_hash:
            if mode == Mode.LIST:
                print(
                    f'Would pull from {src_proj}:'
                    f' {Clr.SGRN}{dstfile}{Clr.RST}'
                )
            else:
                print(f'Pulling from {src_proj}: {Clr.SGRN}{dstfile}{Clr.RST}')

                # Src has changed; simply pull across to dst.
                with dstfile.open('w') as outfile:
                    outfile.write(add_marker(src_proj, srcdata))
            continue
        if src_hash == marker_hash and dst_hash != marker_hash:
            # Dst has changed; we only copy backwards to src
            # if we're in full mode.
            if mode == Mode.LIST:
                print(
                    f'Would push to {src_proj}:'
                    f' {Clr.SBLU}{dstfile}{Clr.RST}'
                )
            elif mode == Mode.FULL:
                print(f'Pushing to {src_proj}: {Clr.SBLU}{dstfile}{Clr.RST}')
                with srcfile.open('w') as outfile:
                    outfile.write(dstdata)

                # We ALSO need to rewrite dst to update its embedded hash
                with dstfile.open('w') as outfile:
                    outfile.write(add_marker(src_proj, dstdata))
            else:
                # Just make note here; we'll error after forward-syncs run.
                changed_error_dst_files.append(dstfile)
            continue

        if marker_hash not in (src_hash, dst_hash):
            # One more option: source and dst could have been changed in
            # identical ways (common when doing global search/replaces).
            # In this case the calced hash from src and dst will match
            # but the stored hash in dst won't.
            if src_hash == dst_hash:
                if mode == Mode.LIST:
                    print(
                        f'Would update dst hash (both files changed'
                        f' identically) from {src_proj}:'
                        f' {Clr.SGRN}{dstfile}{Clr.RST}'
                    )
                else:
                    print(
                        f'Updating hash (both files changed)'
                        f' from {src_proj}: {Clr.SGRN}{dstfile}{Clr.RST}'
                    )
                    with dstfile.open('w') as outfile:
                        outfile.write(add_marker(src_proj, srcdata))
                continue
            # Src/dst hashes don't match and marker doesn't match either.
            # We give up.
            srcabs = os.path.abspath(srcfile)
            dstabs = os.path.abspath(dstfile)
            raise RuntimeError(
                f'both src and dst sync files changed: {srcabs} {dstabs}'
                '; this must be resolved manually.'
            )

        # (if we got here this file should be healthy..)
        assert src_hash == marker_hash and dst_hash == marker_hash

    # Now, if dst is a dir, iterate through and kill anything not in src.
    if dst.is_dir():
        killpaths: list[Path] = []
        for root, dirnames, fnames in os.walk(dst):
            for name in dirnames + fnames:
                if (
                    name.startswith('.')
                    or '__pycache__' in root
                    or '__pycache__' in name
                ):
                    continue
                dstpathfull = Path(root, name)
                relpath = dstpathfull.relative_to(dst)
                srcpathfull = Path(src, relpath)
                if not os.path.exists(srcpathfull):
                    killpaths.append(dstpathfull)

        # This is sloppy in that we'll probably recursively kill dirs and then
        # files under them, so make sure we look before we leap.
        for killpath in killpaths:
            if os.path.exists(killpath):
                if mode == Mode.LIST:
                    print(
                        f'Would remove orphaned sync path:'
                        f' {Clr.SRED}{killpath}{Clr.RST}'
                    )
                else:
                    print(
                        f'Removing orphaned sync path:'
                        f' {Clr.SRED}{killpath}{Clr.RST}'
                    )
                    os.system('rm -rf "' + str(killpath) + '"')

    # Lastly throw an error if we found any changed dst files and aren't
    # allowed to reverse-sync them back.
    if changed_error_dst_files:
        raise RuntimeError(
            f'sync dst file(s) changed since last sync:'
            f' {changed_error_dst_files}; run a FULL mode'
            ' sync to push changes back to src'
        )

    return len(allpaths)


def check_path(dst: Path) -> int:
    """Verify files under dst have not changed from their last sync."""
    allpaths: list[Path] = []
    for root, _dirs, fnames in os.walk(dst):
        for fname in fnames:
            if _valid_filename(fname):
                allpaths.append(Path(root, fname))
    for dstfile in allpaths:
        marker_hash, dst_hash, _dstdata = get_dst_file_info(dstfile)

        # All we can really check here is that the current hash hasn't
        # changed since the last sync.
        if marker_hash != dst_hash:
            raise RuntimeError(
                f'sync dst file changed since last sync: {dstfile}'
            )
    return len(allpaths)


def add_marker(src_proj: str, srcdata: str) -> str:
    """Given the contents of a file, adds a 'synced from' notice and hash."""

    lines = srcdata.splitlines()

    # Normally we add our hash as the first line in the file, but if there's
    # a shebang, we put it under that.
    firstline = 0
    if len(lines) > 0 and lines[0].startswith('#!'):
        firstline = 1

    # Make sure we're not operating on an already-synced file; that's just
    # asking for trouble.
    if len(lines) > (firstline + 1) and (
        'EFRO_SYNC_HASH=' in lines[firstline + 1]
    ):
        raise RuntimeError('Attempting to sync a file that is itself synced.')

    hashstr = string_hash(srcdata)
    lines.insert(
        firstline, f'# Synced from {src_proj}.\n# EFRO_SYNC_HASH={hashstr}\n#'
    )
    return '\n'.join(lines) + '\n'


def string_hash(data: str) -> str:
    """Given a string, return a hash."""
    import hashlib

    md5 = hashlib.md5()
    md5.update(data.encode())

    # Note: returning plain integers instead of hex so linters
    # don't see words and give spelling errors.
    return str(int.from_bytes(md5.digest(), byteorder='big'))


def get_dst_file_info(dstfile: Path) -> tuple[str, str, str]:
    """Given a path, returns embedded marker hash and its actual hash."""
    with dstfile.open() as infile:
        dstdata = infile.read()
    dstlines = dstdata.splitlines()
    if not dstlines:
        raise ValueError(f'no lines found in {dstfile}')
    found = False
    offs: int | None = None
    marker_hash: str | None = None
    for offs in range(2):
        checkline = 1 + offs
        if 'EFRO_SYNC_HASH' in dstlines[checkline]:
            marker_hash = dstlines[checkline].split('EFRO_SYNC_HASH=')[1]
            found = True
            break
    if not found:
        raise ValueError(f'no EFRO_SYNC_HASH found in {dstfile}')
    assert offs is not None
    assert marker_hash is not None

    # Return data minus the 3 hash lines:
    dstlines.pop(offs)
    dstlines.pop(offs)
    dstlines.pop(offs)
    dstdata = '\n'.join(dstlines) + '\n'
    dst_hash = string_hash(dstdata)
    return marker_hash, dst_hash, dstdata
