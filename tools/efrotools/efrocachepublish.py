# Released under the MIT License. See LICENSE for details.
#
"""Publish half of the efrocache system: gathering and uploading.

Everything here is driven by the internal ``efrocache_update``
pcommand, which runs only in ballistica-internal as part of pubsync.
The *consumer* half -- ``get_target`` / ``warm_start_cache``, which is
what public and spinoff repos actually run -- stays in
:mod:`efrotools.efrocache`.

The split is purely to keep both sides under pylint's per-module line
cap; the two halves share a handful of private helpers, imported from
``efrocache`` below rather than duplicated.
"""

import os
import json
import zlib
import shlex
import subprocess
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor

from efro.terminal import Clr

# Shared with the consumer half. Kept private there (they are not part
# of any public surface) and imported here rather than duplicated.
# WTF Pylint. This is our package. It goes last.
# pylint: disable=useless-suppression, wrong-import-order
from efrotools.efrocache import (
    UPLOAD_STATE_CACHE_FILE,
    _cache_prefix_for_file,
    _path_from_hash,
    _project_centric_path,
)

# pylint: enable=useless-suppression, wrong-import-order


def update_cache(makefile_dirs: list[str]) -> None:
    """Given a list of directories containing Makefiles, update caches."""

    import multiprocessing

    cpus = multiprocessing.cpu_count()

    # Build lists of all cached paths as well as the subsets going into
    # our starter caches.
    fnames_starter_gui: list[str] = []
    fnames_starter_server: list[str] = []
    fnames_all: list[str] = []

    # If a path contains any of these substrings it will always be included
    # in starter caches.
    starter_cache_always_include_paths = {
        'build/assets/ba_data/fonts',
        'build/assets/ba_data/data',
        'build/assets/ba_data/python',
        'build/assets/ba_data/python-site-packages',
    }

    # Never add binaries to starter caches since those are specific to
    # one platform/architecture; we should always download those
    # as-needed.
    never_add_to_starter_endings = {
        '.a',
        '.dll',
        '.lib',
        '.exe',
        '.pdb',
        '.so',
        '.pyd',
    }

    for path in makefile_dirs:
        cdp = f'cd {path} && ' if path else ''

        # First, make sure all cache files are built.
        mfpath = os.path.join(path, 'Makefile')
        print(f'Building efrocache targets for {Clr.SBLU}{mfpath}{Clr.RST}...')
        subprocess.run(
            f'{cdp}make -j{cpus} efrocache-build', shell=True, check=True
        )

        rawpaths = (
            subprocess.run(
                f'{cdp}make efrocache-list',
                shell=True,
                check=True,
                capture_output=True,
            )
            .stdout.decode()
            .split()
        )

        # Make sure the paths they gave were relative.
        for rawpath in rawpaths:
            if rawpath.startswith('/'):
                raise RuntimeError(
                    f'Invalid path returned for caching '
                    f'(absolute paths not allowed): {rawpath}'
                )

        for rawpath in rawpaths:
            fullpath = _project_centric_path(os.path.join(path, rawpath))

            # Always add to our full list.
            fnames_all.append(fullpath)

            # Now selectively add to starter cache lists.

            always_include = False

            if any(p in fullpath for p in starter_cache_always_include_paths):
                always_include = True

            # Always keep certain file types out of starter caches.
            if any(
                fullpath.endswith(ending)
                for ending in never_add_to_starter_endings
            ):
                continue

            # Keep big files out of starter caches (unless flagged as
            # always-include). The main benefits of starter-caches is
            # that we can reduce the overhead for downloading individual
            # tiny files by grabbing them all at once, but that
            # advantage diminishes as the files get bigger. And not all
            # platforms will use all files, so it generally more
            # efficient to grab bigger ones as needed.
            if os.path.getsize(fullpath) > 50_000 and not always_include:
                continue

            # Gui starter gets everything that made it this far.
            fnames_starter_gui.append(fullpath)

            # Server starter cuts out everything not explicitly
            # always-included.
            if not always_include:
                continue

            # If it made it this far, add it to the server cache.
            fnames_starter_server.append(fullpath)

    # Ok, we've got a big list of filenames we need to cache in the
    # cloud. First, however, let's do a big hash of everything and if
    # everything is exactly the same as last time we can skip this step.
    hashes = _gen_complete_state_hashes(fnames_all)
    if os.path.isfile(UPLOAD_STATE_CACHE_FILE):
        with open(UPLOAD_STATE_CACHE_FILE, encoding='utf-8') as infile:
            hashes_existing = infile.read()
    else:
        hashes_existing = ''
    if hashes == hashes_existing:
        print(
            f'{Clr.SBLU}Efrocache state unchanged;'
            f' skipping cache push.{Clr.RST}',
            flush=True,
        )
    else:
        _update_cloud_cache(
            fnames_starter_gui,
            fnames_starter_server,
            fnames_all,
            hashes,
            hashes_existing,
        )

    print(f'{Clr.SBLU}Efrocache update successful!{Clr.RST}')

    # Write the cache state so we can skip the next run if nothing
    # changes.
    os.makedirs(os.path.dirname(UPLOAD_STATE_CACHE_FILE), exist_ok=True)
    with open(UPLOAD_STATE_CACHE_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(hashes)


def _gen_complete_state_hashes(fnames: list[str]) -> str:
    import hashlib

    def _get_simple_file_hash(fname: str) -> tuple[str, str]:
        md5 = hashlib.md5()
        with open(fname, mode='rb') as infile:
            md5.update(infile.read())
        return fname, md5.hexdigest()

    # Now use all procs to hash the files efficiently.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        hashes = dict(executor.map(_get_simple_file_hash, fnames))

    return json.dumps(
        hashes,
        separators=(',', ':'),
        allow_nan=False,
    )


def _update_cloud_cache(
    fnames_starter_gui: list[str],
    fnames_starter_server: list[str],
    fnames_all: list[str],
    hashes_str: str,
    hashes_existing_str: str,
) -> None:
    # First, if we've run before, print the files causing us to re-run:
    if hashes_existing_str != '':
        changed_files: set[str] = set()
        hashes = json.loads(hashes_str)
        hashes_existing = json.loads(hashes_existing_str)
        for fname, ftime in hashes.items():
            if ftime != hashes_existing.get(fname, ''):
                changed_files.add(fname)

        # We've covered modifications and additions; add deletions.
        for fname in hashes_existing:
            if fname not in hashes:
                changed_files.add(fname)
        print(
            f'{Clr.SBLU}Updating efrocache due to'
            f' {len(changed_files)} changes:{Clr.RST}'
        )
        for fname in sorted(changed_files):
            print(f'  {Clr.SBLU}{fname}{Clr.RST}')

    # Now do the thing.
    staging_dir = 'build/efrocache'
    mapping_file = 'build/efrocachemap'
    subprocess.run(['rm', '-rf', staging_dir], check=True)
    subprocess.run(['mkdir', '-p', staging_dir], check=True)

    _gather_cache_files(
        fnames_starter_gui,
        fnames_starter_server,
        fnames_all,
        staging_dir,
        mapping_file,
    )

    print(
        f'{Clr.SBLU}Starter gui cache includes {len(fnames_starter_gui)} items;'
        f' excludes {len(fnames_all) - len(fnames_starter_gui)}{Clr.RST}'
    )
    print(
        f'{Clr.SBLU}Starter server cache includes'
        f' {len(fnames_starter_server)} items;'
        f' excludes {len(fnames_all) - len(fnames_starter_server)}{Clr.RST}'
    )

    # Under a network sandbox that only permits egress via a SOCKS5 proxy
    # (e.g. when running these uploads from a sandboxed shell), route
    # ssh/rsync through it; a no-op in normal environments.
    from efro.cloudshell import socks_proxy_ssh_args

    proxy_args = socks_proxy_ssh_args()

    # Sync all individual cache files to the staging server.
    print(f'{Clr.SBLU}Pushing cache to staging...{Clr.RST}', flush=True)
    rsync_cmd = ['rsync', '--progress', '--recursive', '--human-readable']
    if proxy_args:
        # rsync runs --rsh through the shell, so shlex.join keeps the
        # multi-word proxy command intact.
        rsync_cmd.append('--rsh=' + shlex.join(['ssh', *proxy_args]))
    rsync_cmd += [
        'build/efrocache/',
        'ubuntu@staging.ballistica.net:files.ballistica.net/cache/ba1/',
    ]
    subprocess.run(rsync_cmd, check=True)

    # Now generate the starter cache on the server.
    subprocess.run(
        [
            'ssh',
            '-oBatchMode=yes',
            '-oStrictHostKeyChecking=yes',
            *proxy_args,
            'ubuntu@staging.ballistica.net',
            'cd files.ballistica.net/cache/ba1 && python3 genstartercache.py',
        ],
        check=True,
    )


def _gather_cache_files(
    fnames_starter_gui: list[str],
    fnames_starter_server: list[str],
    fnames_all: list[str],
    staging_dir: str,
    mapping_file: str,
) -> None:
    import functools

    fhashpaths_all: set[str] = set()
    names_to_hashes: dict[str, str] = {}
    names_to_hashpaths: dict[str, str] = {}
    writecall = functools.partial(_write_cache_file, staging_dir)

    # Calc hashes and hash-paths for all cache files.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        for fname, fhash, fhashpath in executor.map(writecall, fnames_all):
            names_to_hashes[fname] = fhash
            names_to_hashpaths[fname] = fhashpath
            fhashpaths_all.add(fhashpath)

    # Now calc hashpaths for our starter file sets.
    fhashpaths_starter_gui: set[str] = set()
    for fname in fnames_starter_gui:
        fhashpaths_starter_gui.add(names_to_hashpaths[fname])
    fhashpaths_starter_server: set[str] = set()
    for fname in fnames_starter_server:
        fhashpaths_starter_server.add(names_to_hashpaths[fname])

    # We want the server to have a startercache(server).tar.xz files
    # which contain the entire subsets we were passed. It is much more
    # efficient to build those files on the server than it is to build
    # them here and upload the whole thing. ...so let's simply write a
    # script to generate them and upload that.

    # Also let's have the script touch the full set of files we're still
    # using so we can use mod-times to prune unused ones eventually.
    # Otherwise files that we're still using but which never change
    # might have very old mod times.
    script = (
        'import os\n'
        'import pathlib\n'
        'import subprocess\n'
        f'fnames_starter_gui = {repr(fhashpaths_starter_gui)}\n'
        f'fnames_starter_server = {repr(fhashpaths_starter_server)}\n'
        f'fnames_all = {repr(fhashpaths_all)}\n'
        'print("Updating modtimes on all current cache files...", flush=True)\n'
        'for fname in fnames_all:\n'
        '    fpath = pathlib.Path(fname)\n'
        '    assert fpath.exists()\n'
        '    fpath.touch()\n'
        'for scname, scarchivename, fnames_starter in [\n'
        '      ("gui", "startercache", fnames_starter_gui),\n'
        '      ("server", "startercacheserver", fnames_starter_server)]:\n'
        '    print(f"Gathering {scname} starter-cache files...", flush=True)\n'
        '    subprocess.run(["rm", "-rf", "efrocache"], check=True)\n'
        '    for fname in fnames_starter:\n'
        '        dst = os.path.join("efrocache", fname)\n'
        '        os.makedirs(os.path.dirname(dst), exist_ok=True)\n'
        '        subprocess.run(["cp", fname, dst], check=True)\n'
        '    print(f"Compressing {scname} starter-cache archive...",'
        ' flush=True)\n'
        '    subprocess.run(["tar", "-Jcf", "tmp.tar.xz", "efrocache"],'
        ' check=True)\n'
        '    subprocess.run(["mv", "tmp.tar.xz", f"{scarchivename}.tar.xz"],'
        ' check=True)\n'
        '    subprocess.run(["rm", "-rf", "efrocache"], check=True)\n'
        '    print(scname.capitalize() + "starter-cache generation complete!",'
        ' flush=True)\n'
        'subprocess.run(["rm", "-rf", "genstartercache.py"])\n'
    )

    with open(
        'build/efrocache/genstartercache.py', 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(script)

    with open(mapping_file, 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(names_to_hashes, indent=2, sort_keys=True))


def _write_cache_file(staging_dir: str, fname: str) -> tuple[str, str, str]:
    import hashlib

    print(f'Caching {fname}')

    prefix = _cache_prefix_for_file(fname)

    with open(fname, 'rb') as infile:
        fdataraw = infile.read()

    # Calc a hash of the prefix plus the raw file contents. We want to
    # hash the *uncompressed* file since we'll need to calc this for
    # lots of existing files when seeing if they need to be updated.

    # Just going with ol' md5 here; we're the only ones creating these
    # so security isn't a concern currently.
    md5 = hashlib.md5()
    md5.update(prefix + fdataraw)
    finalhash = md5.hexdigest()
    hashpath = _path_from_hash(finalhash)
    path = os.path.join(staging_dir, hashpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'wb') as outfile:
        outfile.write(prefix + zlib.compress(fdataraw))

    return fname, finalhash, hashpath
