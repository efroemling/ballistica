# Copyright (c) 2011-2020 Eric Froemling
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
"""General functionality related to running builds."""
from __future__ import annotations

import os
from enum import Enum
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

CLRBLU = '\033[94m'  # Blue.
CLRHDR = '\033[95m'  # Header.
CLREND = '\033[0m'  # End.


class SourceCategory(Enum):
    """Types of sources."""
    RESOURCES = 'resources_src'
    CODE_GEN = 'code_gen_src'
    ASSETS = 'assets_src'
    CMAKE = 'cmake_src'
    WIN = 'win_src'


def _checkpaths(inpaths: List[str], category: SourceCategory,
                target: str) -> bool:
    # pylint: disable=too-many-branches

    mtime = None if not os.path.exists(target) else os.path.getmtime(target)

    if target.startswith('.cache/lazybuild/'):
        tnamepretty = target[len('.cache/lazybuild/'):]
    else:
        tnamepretty = target

    def _testpath(path: str) -> bool:
        # Now see this path is newer than our target..
        if mtime is None or os.path.getmtime(path) >= mtime:
            print(f'{CLRHDR}Build of {tnamepretty} triggered by'
                  f' {path}{CLREND}')
            return True
        return False

    unchanged_count = 0
    for inpath in inpaths:
        # Add files verbatim; recurse through dirs.
        if os.path.isfile(inpath):
            if _testpath(inpath):
                return True
            unchanged_count += 1
            continue
        for root, _dnames, fnames in os.walk(inpath):

            # Only gen category uses gen src.
            if (root.startswith('src/generated_src')
                    and category is not SourceCategory.CODE_GEN):
                continue

            # None of our targets use tools-src.
            if root.startswith('src/tools'):
                continue

            # Skip most of external except for key cases.
            if root.startswith('src/external'):
                if category is SourceCategory.WIN and root.startswith(
                        'src/external/windows'):
                    pass
                else:
                    continue

            # Ignore python cache files.
            if '__pycache__' in root:
                continue
            for fname in fnames:
                # Ignore dot files
                if fname.startswith('.'):
                    continue
                fpath = os.path.join(root, fname)
                if ' ' in fpath:
                    raise RuntimeError(f'Invalid path with space: {fpath}')

                if _testpath(fpath):
                    return True
                unchanged_count += 1
    print(f'{CLRBLU}Skipping build of {tnamepretty}'
          f' ({unchanged_count} inputs unchanged){CLREND}')
    return False


def lazy_build(target: str, category: SourceCategory, command: str) -> None:
    """Run a build if anything in category is newer than target.

    Note that target's mod-time will always be updated when the build happens
    regardless of whether the build itself did so itself.
    """
    paths: List[str]
    if category is SourceCategory.CODE_GEN:
        # Everything possibly affecting generated code.
        paths = ['tools/generate_code', 'src/generated_src']
    elif category is SourceCategory.ASSETS:
        paths = ['tools/convert_util', 'assets/src']
    elif category is SourceCategory.CMAKE:
        # Everything possibly affecting CMake builds.
        paths = ['src', 'ballisticacore-cmake/CMakeLists.txt']
    elif category is SourceCategory.WIN:
        # Everything possibly affecting Windows binary builds.
        paths = ['src', 'resources/src']
    elif category is SourceCategory.RESOURCES:
        # Everything possibly affecting resources builds.
        paths = ['resources/src', 'resources/Makefile']
    else:
        raise ValueError(f'Invalid source category: {category}')

    # Now do the thing if any our our input mod times changed.
    if _checkpaths(paths, category, target):

        subprocess.run(command, shell=True, check=True)

        # We also explicitly update the mod-time of the target;
        # the command we (such as a VM build) may not have actually
        # done anything but we still want to update our target to
        # be newer than all the lazy sources.
        os.makedirs(os.path.dirname(target), exist_ok=True)
        Path(target).touch()
