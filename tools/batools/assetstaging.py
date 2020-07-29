#!/usr/bin/env python3.7
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
"""Stage assets for a build."""

from __future__ import annotations

import hashlib
import os
import sys
import subprocess
from functools import partial
from typing import TYPE_CHECKING

from efrotools import PYVER

if TYPE_CHECKING:
    from typing import Optional, List

# Suffix for the pyc files we include in stagings.
# We're using deterministic opt pyc files; see PEP 552.
# Note: this means anyone wanting to modify .py files in a build
# will need to wipe out the existing .pyc files first or the changes
# will be ignored.
OPT_PYC_SUFFIX = ('cpython-' + PYVER.replace('.', '') + '.opt-1.pyc')


class Config:
    """Encapsulates command options."""

    def __init__(self, projroot: str) -> None:
        self.projroot = projroot
        # We always calc src relative to this script.
        self.src = self.projroot + '/assets/build'
        self.dst: Optional[str] = None
        self.win_extras_src: Optional[str] = None
        self.win_platform: Optional[str] = None
        self.win_type: Optional[str] = None
        self.include_audio = True
        self.include_models = True
        self.include_collide_models = True
        self.include_scripts = True
        self.include_python = True
        self.include_textures = True
        self.include_fonts = True
        self.include_json = True
        self.include_pylib = False
        self.pylib_src_name: Optional[str] = None
        self.include_payload_file = False
        self.tex_suffix: Optional[str] = None
        self.is_payload_full = False
        self.debug = False

    def _parse_android_args(self, args: List[str]) -> None:
        # On Android we get nitpicky with what
        # we want to copy in since we can speed up
        # iterations by installing stripped down
        # apks.
        self.dst = 'assets/ballistica_files'
        self.pylib_src_name = 'pylib-android'
        self.include_payload_file = True
        self.tex_suffix = '.ktx'
        self.include_audio = False
        self.include_models = False
        self.include_collide_models = False
        self.include_scripts = False
        self.include_python = False
        self.include_textures = False
        self.include_fonts = False
        self.include_json = False
        self.include_pylib = False
        for arg in args:
            if arg == '-full':
                self.include_audio = True
                self.include_models = True
                self.include_collide_models = True
                self.include_scripts = True
                self.include_python = True
                self.include_textures = True
                self.include_fonts = True
                self.include_json = True
                self.is_payload_full = True
                self.include_pylib = True
            elif arg == '-none':
                pass
            elif arg == '-models':
                self.include_models = True
                self.include_collide_models = True
            elif arg == '-python':
                self.include_python = True
                self.include_pylib = True
            elif arg == '-textures':
                self.include_textures = True
            elif arg == '-fonts':
                self.include_fonts = True
            elif arg == '-scripts':
                self.include_scripts = True
            elif arg == '-audio':
                self.include_audio = True

    def _parse_win_platform(self, platform: str, args: List[str]) -> None:
        """Parse sub-args in the windows platform string."""
        winempty, wintype, winplt, wincfg = platform.split('-')
        self.win_platform = winplt
        self.win_type = wintype
        assert winempty == ''
        self.dst = args[1]
        self.tex_suffix = '.dds'

        if wintype == 'win':
            pass
        elif wintype == 'winserver':
            self.include_textures = False
            self.include_audio = False
            self.include_models = False
        else:
            raise RuntimeError(f'Invalid wintype: "{wintype}"')

        if winplt == 'Win32':
            self.win_extras_src = self.projroot + '/assets/build/windows/Win32'
        elif winplt == 'x64':
            self.win_extras_src = self.projroot + '/assets/build/windows/x64'
        else:
            raise RuntimeError(f'Invalid winplt: "{winplt}"')

        if wincfg == 'Debug':
            self.debug = True
        elif wincfg == 'Release':
            self.debug = False
        else:
            raise RuntimeError(f'Invalid wincfg: "{wincfg}"')

    def parse_args(self, args: List[str]) -> None:
        """Parse args and apply to the cfg."""
        if len(args) < 1:
            raise RuntimeError('Expected a platform argument.')
        platform = args[0]
        if platform == '-android':
            self._parse_android_args(args)
        elif platform.startswith('-win'):
            self._parse_win_platform(platform, args)
        elif platform == '-cmake':
            self.dst = args[1]
            self.tex_suffix = '.dds'
        elif '-cmakeserver' in args:
            self.dst = args[1]
            self.include_textures = False
            self.include_audio = False
            self.include_models = False
        elif '-xcode-mac' in args:
            self.src = os.environ['SOURCE_ROOT'] + '/assets/build'
            self.dst = (os.environ['TARGET_BUILD_DIR'] + '/' +
                        os.environ['UNLOCALIZED_RESOURCES_FOLDER_PATH'])
            self.include_pylib = True
            self.pylib_src_name = 'pylib-apple'
            self.tex_suffix = '.dds'
        elif '-xcode-ios' in args:
            self.src = os.environ['SOURCE_ROOT'] + '/assets/build'
            self.dst = (os.environ['TARGET_BUILD_DIR'] + '/' +
                        os.environ['UNLOCALIZED_RESOURCES_FOLDER_PATH'])
            self.include_pylib = True
            self.pylib_src_name = 'pylib-apple'
            self.tex_suffix = '.pvr'
        else:
            raise RuntimeError('No valid platform arg provided.')


def md5sum(filename: str) -> str:
    """Generate an md5sum given a filename."""
    md5 = hashlib.md5()
    with open(filename, mode='rb') as infile:
        for buf in iter(partial(infile.read, 1024), b''):
            md5.update(buf)
    return md5.hexdigest()


def _run(cmd: str, echo: bool = False) -> None:
    """Run an os command; raise Exception on non-zero return value."""
    if echo:
        print(cmd)
    result = os.system(cmd)
    if result != 0:
        raise Exception("error running cmd: '" + cmd + "'")


def _write_payload_file(assets_root: str, full: bool) -> None:
    if not assets_root.endswith('/'):
        assets_root = assets_root + '/'

    # Now construct a payload file if we have any files.
    file_list = []
    payload_str = ''
    for root, _subdirs, fnames in os.walk(assets_root):
        for fname in fnames:
            if fname.startswith('.'):
                continue
            if fname == 'payload_info':
                continue
            fpath = os.path.join(root, fname)
            fpathshort = fpath.replace(assets_root, '')
            if ' ' in fpathshort:
                raise RuntimeError(
                    f"Invalid filename (contains spaces): '{fpathshort}'")
            payload_str += fpathshort + ' ' + md5sum(fpath) + '\n'
            file_list.append(fpathshort)

    payload_path = assets_root + '/payload_info'
    if file_list:
        # Write the file count, whether this is a 'full' payload, and finally
        # the file list.
        payload_str = (str(len(file_list)) + '\n' + ('1' if full else '0') +
                       '\n' + payload_str)
        with open(payload_path, 'w') as outfile:
            outfile.write(payload_str)
    else:
        # Remove the payload file; this will cause the game to completely
        # skip the payload processing step.
        if os.path.exists(payload_path):
            os.unlink(payload_path)


def _sync_windows_extras(cfg: Config) -> None:
    assert cfg.win_extras_src is not None
    assert cfg.win_platform is not None
    assert cfg.win_type is not None
    if not os.path.isdir(cfg.win_extras_src):
        raise Exception('win extras src dir not found: ' + cfg.win_extras_src)

    # Ok, lets do full syncs on each subdir we find so we
    # properly delete anything in dst that disappeared from src.
    # Lastly we'll sync over the remaining top level files.
    # Note: technically it'll be possible to leave orphaned top level
    # files in dst, so when building packages/etc. we should always start
    # from scratch.
    assert cfg.dst is not None
    for dirname in ('DLLs', 'Lib'):
        _run(f'mkdir -p "{cfg.dst}/{dirname}"')
        cmd = ('rsync --recursive --update --delete --delete-excluded '
               ' --prune-empty-dirs'
               " --include '*.ico' --include '*.cat'"
               " --include '*.dll' --include '*.pyd'"
               " --include '*.py' --include '*." + OPT_PYC_SUFFIX + "'"
               " --include '*/' --exclude '*' \"" +
               os.path.join(cfg.win_extras_src, dirname) + '/" '
               '"' + cfg.dst + '/' + dirname + '/"')
        _run(cmd)

    # Now sync the top level individual files that we want.
    # (we could technically copy everything over but this keeps staging
    # dirs a bit tidier)
    toplevelfiles: List[str] = ['python37.dll']

    if cfg.win_type == 'win':
        toplevelfiles += [
            'libvorbis.dll', 'libvorbisfile.dll', 'ogg.dll', 'OpenAL32.dll',
            'SDL2.dll'
        ]
    elif cfg.win_type == 'winserver':
        toplevelfiles += ['python.exe']

    # Include debug dlls so folks without msvc can run them.
    if cfg.debug:
        if cfg.win_platform == 'x64':
            toplevelfiles += [
                'msvcp140d.dll', 'vcruntime140d.dll', 'vcruntime140_1d.dll'
            ]
        else:
            toplevelfiles += ['msvcp140d.dll', 'vcruntime140d.dll']

    # Include the runtime redistributables in release builds.
    if not cfg.debug:
        if cfg.win_platform == 'x64':
            toplevelfiles.append('vc_redist.x64.exe')
        elif cfg.win_platform == 'Win32':
            toplevelfiles.append('vc_redist.x86.exe')
        else:
            raise RuntimeError(f'Invalid win_platform {cfg.win_platform}')

    cmd2 = (['rsync', '--update'] +
            [os.path.join(cfg.win_extras_src, f)
             for f in toplevelfiles] + [cfg.dst + '/'])
    subprocess.run(cmd2, check=True)

    # If we're running under WSL we won't be able to launch these .exe files
    # unless they're marked executable, so do that here.
    # Update: gonna try simply setting this flag on the source side.
    # _run(f'chmod +x {cfg.dst}/*.exe')


def _sync_pylib(cfg: Config) -> None:
    assert cfg.pylib_src_name is not None
    assert cfg.dst is not None
    _run(f'mkdir -p "{cfg.dst}/pylib"')
    cmd = (f'rsync --recursive --update --delete --delete-excluded '
           f' --prune-empty-dirs'
           f" --include '*.py' --include '*.{OPT_PYC_SUFFIX}'"
           f" --include '*/' --exclude '*'"
           f' "{cfg.src}/{cfg.pylib_src_name}/" '
           f'"{cfg.dst}/pylib/"')
    _run(cmd)


def main(projroot: str, args: Optional[List[str]] = None) -> None:
    """Stage assets for a build."""

    if args is None:
        args = sys.argv

    cfg = Config(projroot)
    cfg.parse_args(args)

    # Ok, now for every top level dir in src, come up with a nice single
    # command to sync the needed subset of it to dst.

    # We can now use simple speedy timestamp based updates since
    # we no longer have to try to preserve timestamps to get .pyc files
    # to behave (hooray!)

    # Do our stripped down pylib dir for platforms that use that.
    if cfg.include_pylib:
        _sync_pylib(cfg)
    else:
        if cfg.dst is not None and os.path.isdir(cfg.dst + '/pylib'):
            subprocess.run(['rm', '-rf', cfg.dst + '/pylib'], check=True)

    # On windows we need to pull in some dlls and this and that
    # (we also include a non-stripped-down set of python libs).
    if cfg.win_extras_src is not None:
        _sync_windows_extras(cfg)

    # Now standard common game data.
    assert cfg.dst is not None
    _run('mkdir -p "' + cfg.dst + '/ba_data"')
    cmd = ('rsync --recursive --update --delete --delete-excluded'
           ' --prune-empty-dirs')

    if cfg.include_scripts:
        cmd += " --include '*.py' --include '*." + OPT_PYC_SUFFIX + "'"

    if cfg.include_textures:
        assert cfg.tex_suffix is not None
        cmd += " --include '*" + cfg.tex_suffix + "'"

    if cfg.include_audio:
        cmd += " --include '*.ogg'"

    if cfg.include_fonts:
        cmd += " --include '*.fdata'"

    if cfg.include_json:
        cmd += " --include '*.json'"

    if cfg.include_models:
        cmd += " --include '*.bob'"

    if cfg.include_collide_models:
        cmd += " --include '*.cob'"

    cmd += (" --include='*/' --exclude='*' \"" + cfg.src + '/ba_data/" "' +
            cfg.dst + '/ba_data/"')
    _run(cmd)

    # On Android we need to build a payload file so it knows
    # what to pull out of the apk.
    if cfg.include_payload_file:
        _write_payload_file(cfg.dst, cfg.is_payload_full)


# if __name__ == '__main__':
#     try:
#         main()
#     except CleanError as exc:
#         exc.pretty_print()
#         sys.exit(1)
