# Copyright (c) 2011-2019 Eric Froemling
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
"""A simple cloud caching system for making built binaries/assets available."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Dict, Tuple

CLRHDR = '\033[95m'  # Header.
CLRGRN = '\033[92m'  # Green.
CLRBLU = '\033[94m'  # Glue.
CLRRED = '\033[91m'  # Red.
CLREND = '\033[0m'  # End.

BASE_URL = 'https://files.ballistica.net/cache/ba1/'

TARGET_TAG = '#__EFROCACHE_TARGET__'
STRIP_BEGIN_TAG = '#__EFROCACHE_STRIP_BEGIN__'
STRIP_END_TAG = '#__EFROCACHE_STRIP_END__'

CACHE_DIR_NAME = '.efrocache'
CACHE_MAP_NAME = '.efrocachemap'


def get_file_hash(path: str) -> str:
    """Return the hash used for caching.

    This incorporates the file contents as well as its path.
    """
    import hashlib
    md5 = hashlib.md5()
    with open(path, 'rb') as infile:
        md5.update(infile.read())
    md5.update(path.encode())
    return md5.hexdigest()


def get_target(path: str) -> None:
    """Fetch a target path from the cache, downloading if need be."""

    import json
    from efrotools import run
    with open(CACHE_MAP_NAME) as infile:
        efrocachemap = json.loads(infile.read())
    if path not in efrocachemap:
        raise RuntimeError(f'Path not found in efrocache: {path}')
    url = efrocachemap[path]
    subpath = '/'.join(url.split('/')[-3:])
    local_cache_path = os.path.join(CACHE_DIR_NAME, subpath)
    local_cache_path_dl = local_cache_path + '.download'
    hashval = ''.join(subpath.split('/'))

    # First off: if there's already a file in place, check its hash.
    # If it matches the cache, we can just update its timestamp and
    # call it a day.
    if os.path.isfile(path):
        existing_hash = get_file_hash(path)
        if existing_hash == hashval:
            os.utime(path, None)
            print(f'Refreshing from cache: {path}')
            return

    # Ok there's not a valid file in place already.
    # Clear out whatever is there to start with.
    if os.path.exists(path):
        os.unlink(path)

    # Now if we don't have this entry in our local cache,
    # download it.
    if not os.path.exists(local_cache_path):
        os.makedirs(os.path.dirname(local_cache_path), exist_ok=True)
        print(f'Downloading: {CLRBLU}{path}{CLREND}')
        run(f'curl --silent {url} > {local_cache_path_dl}')
        run(f'mv {local_cache_path_dl} {local_cache_path}')

    # Ok we should have a valid .tar.gz file in our cache dir at this point.
    # Just expand it and it get placed wherever it belongs.
    run(f'tar -zxf {local_cache_path}')

    # The file will wind up with the timestamp it was compressed with,
    # so let's update its timestamp or else it will still be considered
    # dirty.
    run(f'touch {path}')
    if not os.path.exists(path):
        raise RuntimeError(f'File {path} did not wind up as expected.')


def filter_makefile(makefile_dir: str, contents: str) -> str:
    """Filter makefile contents to use efrocache lookups."""

    if makefile_dir:
        # Assuming just one level deep at the moment; can revisit later.
        assert '/' not in makefile_dir
        to_proj_root = '..'
    else:
        to_proj_root = ''

    cachemap = os.path.join(to_proj_root, CACHE_MAP_NAME)
    lines = contents.splitlines()
    snippets = 'tools/snippets'

    # Strip out parts they don't want.
    while STRIP_BEGIN_TAG in lines:
        index = lines.index(STRIP_BEGIN_TAG)
        endindex = index
        while lines[endindex] != STRIP_END_TAG:
            endindex += 1

        # If the line after us is blank, include it too to keep spacing clean.
        if not lines[endindex + 1].strip():
            endindex += 1

        del lines[index:endindex + 1]

    # Replace cachable targets with cache lookups
    while TARGET_TAG in lines:
        index = lines.index(TARGET_TAG)
        endindex = index
        while lines[endindex].strip() != '':
            endindex += 1
        tname = lines[index + 1].split(':')[0]
        del lines[index:endindex]
        lines.insert(index, tname + ': ' + cachemap)
        target = (makefile_dir + '/' + '$@') if makefile_dir else '$@'
        pre = f'cd {to_proj_root} && ' if makefile_dir else ''
        lines.insert(index + 1, f'\t@{pre}{snippets} efrocache_get {target}')
    return '\n'.join(lines) + '\n'


def update_cache(makefile_dirs: List[str]) -> None:
    """Given a list of directories containing makefiles, update caches."""

    import multiprocessing
    from efrotools import run
    cpus = multiprocessing.cpu_count()
    fnames1: List[str] = []
    fnames2: List[str] = []
    for path in makefile_dirs:
        # First, make sure all cache files are built.
        cdp = f'cd {path} && ' if path else ''
        mfpath = os.path.join(path, 'Makefile')
        print(f'Building cache targets for {mfpath}...')
        subprocess.run(f'{cdp}make -j{cpus} efrocache_build',
                       shell=True,
                       check=True)

        rawpaths = subprocess.run(f'{cdp}make efrocache_list',
                                  shell=True,
                                  check=True,
                                  capture_output=True).stdout.decode().split()

        # Make sure the paths they gave were relative.
        for rawpath in rawpaths:
            if rawpath.startswith('/'):
                raise RuntimeError(f'Invalid path returned for caching '
                                   f'(absolute paths not allowed): {rawpath}')

        # Break these into 2 lists, one of which will be included in the
        # starter-cache.
        for rawpath in rawpaths:
            fullpath = os.path.join(path, rawpath)

            # The main reason for this cache is to reduce round trips to
            # the staging server for tiny files, so let's include small files
            # only here. For larger stuff its ok to have a request per file.
            if os.path.getsize(fullpath) < 100000:
                fnames1.append(fullpath)
            else:
                fnames2.append(fullpath)

    staging_dir = 'build/efrocache'
    mapping_file = 'build/efrocachemap'
    run(f'rm -rf {staging_dir}')
    run(f'mkdir -p {staging_dir}')

    _write_cache_files(fnames1, fnames2, staging_dir, mapping_file)

    print(f"Starter cache includes {len(fnames1)} items;"
          f" excludes {len(fnames2)}")
    # Push what we just wrote to the staging server
    print('Pushing cache to staging...', flush=True)
    run('rsync --recursive build/efrocache/'
        ' ubuntu@ballistica.net:files.ballistica.net/cache/ba1/')

    print(f'Cache update successful!')


def _write_cache_file(staging_dir: str, fname: str) -> Tuple[str, str]:
    import hashlib
    from efrotools import run
    print(f'Caching {fname}')
    if ' ' in fname:
        raise RuntimeError('Spaces in paths not supported.')

    # Just going with ol' md5 here; we're the only ones creating these so
    # security isn't a concern.
    md5 = hashlib.md5()
    with open(fname, 'rb') as infile:
        md5.update(infile.read())
    md5.update(fname.encode())
    finalhash = md5.hexdigest()
    hashpath = os.path.join(finalhash[:2], finalhash[2:4], finalhash[4:])
    path = os.path.join(staging_dir, hashpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Fancy pipe stuff which will give us deterministic
    # tar.gz files (no embedded timestamps)
    run(f'tar cf - {fname} | gzip -n > {path}')
    return fname, hashpath


def _write_cache_files(fnames1: List[str], fnames2: List[str],
                       staging_dir: str, mapping_file: str) -> None:
    from multiprocessing import cpu_count
    from concurrent.futures import ThreadPoolExecutor
    from efrotools import run
    import functools
    import json
    mapping: Dict[str, str] = {}
    call = functools.partial(_write_cache_file, staging_dir)

    # Do the first set.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        results = executor.map(call, fnames1)
    for result in results:
        mapping[result[0]] = BASE_URL + result[1]

    # Once we've written our first set, create
    # a starter-cache file from everything we wrote.
    # This consists of some subset of the cache dir we just filled out.
    # Clients initing their cache dirs can grab this as a starting point
    # which should greatly reduce the individual file downloads they have
    # to do (at least when first building).
    print('Writing starter-cache...')
    run('cd build && tar -Jcf startercache.tar.xz efrocache'
        ' && mv startercache.tar.xz efrocache')

    # Now finish up with the second set.
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        results = executor.map(call, fnames2)
        for result in results:
            mapping[result[0]] = BASE_URL + result[1]

    with open(mapping_file, 'w') as outfile:
        outfile.write(json.dumps(mapping, indent=2, sort_keys=True))


def _check_warm_start_entry(entry: Tuple[str, str]) -> None:
    import hashlib
    fname, filehash = entry
    md5 = hashlib.md5()
    with open(fname, 'rb') as infile:
        md5.update(infile.read())
    md5.update(fname.encode())
    finalhash = md5.hexdigest()

    # If the file still matches the hash value we have for it,
    # go ahead and update its timestamp.
    if finalhash == filehash:
        os.utime(fname, None)


def _check_warm_start_entries(entries: List[Tuple[str, str]]) -> None:
    from multiprocessing import cpu_count
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        # Converting this to a list pulls results and propagates errors)
        list(executor.map(_check_warm_start_entry, entries))


def warm_start_cache() -> None:
    """Run a pre-pass on the efrocache to improve efficiency."""
    import json
    from efrotools import run

    # We maintain a starter-cache on the staging server, which
    # is simply the latest set of cache entries compressed into a single
    # compressed archive. If we have no local cache yet we can download
    # and expand this to give us a nice head start and greatly reduce
    # the initial set of individual files we have to fetch.
    # (downloading a single compressed archive is much more efficient than
    # downloading thousands)
    if not os.path.exists(CACHE_DIR_NAME):
        print('Downloading asset starter-cache...', flush=True)
        run(f'curl {BASE_URL}startercache.tar.xz > startercache.tar.xz')
        print('Decompressing starter-cache...', flush=True)
        run('tar -xvf startercache.tar.xz')
        run(f'mv efrocache {CACHE_DIR_NAME}')
        run(f'rm startercache.tar.xz')
        print('Starter-cache fetched successful!'
              ' (should speed up asset builds)')

    # In the public build, let's scan through all files managed by
    # efrocache and update any with timestamps older than the latest
    # cache-map that we already have the data for.
    # Otherwise those files will update individually the next time
    # they are 'built'. Even though that only takes a fraction of a
    # second per file, it adds up when done for thousands of assets
    # each time the cache map changes. It is much more efficient to do
    # it in one go here.
    cachemap: Dict[str, str]
    with open(CACHE_MAP_NAME) as infile:
        cachemap = json.loads(infile.read())
    assert isinstance(cachemap, dict)
    cachemap_mtime = os.path.getmtime(CACHE_MAP_NAME)
    entries: List[Tuple[str, str]] = []
    for fname, url in cachemap.items():

        # File hasn't been pulled from cache yet = ignore.
        if not os.path.exists(fname):
            continue

        # File is newer than the cache map = ignore.
        if cachemap_mtime < os.path.getmtime(fname):
            continue

        # Don't have the cache source file for this guy = ignore.
        cachefile = CACHE_DIR_NAME + '/' + '/'.join(url.split('/')[-3:])
        if not os.path.exists(cachefile):
            continue

        # Ok, add it to the list of files we can potentially update timestamps
        # on once we check its hash.
        filehash = ''.join(url.split('/')[-3:])
        entries.append((fname, filehash))

    if entries:
        # Now fire off a multithreaded executor to check hashes and update
        # timestamps.
        _check_warm_start_entries(entries)
