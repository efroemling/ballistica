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
    from typing import List, Dict


def update_cache(makefile_dirs: List[str]) -> None:
    """Given a list of directories containing makefiles, update caches."""

    import multiprocessing
    from efrotools import run
    cpus = multiprocessing.cpu_count()
    fnames: List[str] = []
    for path in makefile_dirs:
        # First, update things..
        cdp = f'cd {path} && ' if path else ''
        subprocess.run(f'{cdp}make -j{cpus} efrocache_build',
                       shell=True,
                       check=True)
        # Now get the list of them.
        fnames += [
            os.path.join(path, s) for s in subprocess.run(
                f'{cdp}make efrocache_list',
                shell=True,
                check=True,
                capture_output=True).stdout.decode().split()
        ]
    staging_dir = 'build/efrocache'
    mapping_file = 'build/efrocachemap'
    run(f'rm -rf {staging_dir}')
    run(f'mkdir -p {staging_dir}')

    _write_cache_files(fnames, staging_dir, mapping_file)

    # Push what we just wrote to the staging server
    print('Pushing cache to staging...', flush=True)
    run('rsync --recursive build/efrocache/'
        ' ubuntu@ballistica.net:files.ballistica.net/cache/ba1/')

    print(f'Cache update successful!')


def _write_cache_files(fnames: List[str], staging_dir: str,
                       mapping_file: str) -> None:
    from efrotools import run
    import hashlib
    import json
    mapping: Dict[str, str] = {}
    baseurl = 'https://files.ballistica.net/cache/ba1/'
    for fname in fnames:

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
        mapping[fname] = baseurl + hashpath
    with open(mapping_file, 'w') as outfile:
        outfile.write(json.dumps(mapping, indent=2, sort_keys=True))
