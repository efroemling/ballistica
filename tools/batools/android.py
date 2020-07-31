#!/usr/bin/env python3.8
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
"""Functionality related to android builds."""
from __future__ import annotations

import os
import sys
import subprocess
from typing import TYPE_CHECKING

import efrotools

if TYPE_CHECKING:
    from typing import List, Optional, Set


def androidaddr(archive_dir: str, arch: str, addr: str) -> None:
    """Print the source file location for an android program-counter.

    command line args: archive_dir architecture addr
    """
    if not os.path.isdir(archive_dir):
        print('ERROR: invalid archive dir: "' + archive_dir + '"')
        sys.exit(255)
    archs = {
        'x86': {
            'prefix': 'x86-',
            'libmain': 'libmain_x86.so'
        },
        'arm': {
            'prefix': 'arm-',
            'libmain': 'libmain_arm.so'
        },
        'arm64': {
            'prefix': 'aarch64-',
            'libmain': 'libmain_arm64.so'
        },
        'x86-64': {
            'prefix': 'x86_64-',
            'libmain': 'libmain_x86-64.so'
        }
    }
    if arch not in archs:
        print('ERROR: invalid arch "' + arch + '"; (choices are ' +
              ', '.join(archs.keys()) + ')')
        sys.exit(255)
    sdkutils = 'tools/android_sdk_utils'
    rootdir = '.'
    ndkpath = subprocess.check_output([sdkutils,
                                       'get-ndk-path']).decode().strip()
    if not os.path.isdir(ndkpath):
        print("ERROR: ndk-path '" + ndkpath + '" does not exist')
        sys.exit(255)
    lines = subprocess.check_output(
        ['find',
         os.path.join(ndkpath, 'toolchains'), '-name',
         '*addr2line']).decode().strip().splitlines()
    # print('RAW LINES', lines)
    lines = [
        line for line in lines
        if archs[arch]['prefix'] in line and '/llvm/' in line
    ]
    if len(lines) != 1:
        print(f"ERROR: can't find addr2line binary ({len(lines)} options).")
        sys.exit(255)
    addr2line = lines[0]
    efrotools.run('mkdir -p "' + os.path.join(rootdir, 'android_addr_tmp') +
                  '"')
    try:
        efrotools.run('cd "' + os.path.join(rootdir, 'android_addr_tmp') +
                      '" && tar -xf "' +
                      os.path.join(archive_dir, 'unstripped_libs',
                                   archs[arch]['libmain'] + '.tgz') + '"')
        efrotools.run(
            addr2line + ' -e "' +
            os.path.join(rootdir, 'android_addr_tmp', archs[arch]['libmain']) +
            '" ' + addr)
    finally:
        os.system('rm -rf "' + os.path.join(rootdir, 'android_addr_tmp') + '"')
