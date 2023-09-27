# Released under the MIT License. See LICENSE for details.
#
"""Stage files for builds."""

from __future__ import annotations

import hashlib
import os
import sys
import subprocess
from functools import partial
from typing import TYPE_CHECKING

from efrotools import PYVER, extract_arg, extract_flag

if TYPE_CHECKING:
    pass

# Suffix for the pyc files we include in stagings. We're using
# deterministic opt pyc files; see PEP 552.
#
# Note: this means anyone wanting to modify .py files in a build will
# need to wipe out the existing .pyc files first or the changes will be
# ignored.
OPT_PYC_SUFFIX = 'cpython-' + PYVER.replace('.', '') + '.opt-1.pyc'


def stage_build(projroot: str, args: list[str] | None = None) -> None:
    """Stage assets for a build."""

    if args is None:
        args = sys.argv

    AssetStager(projroot).run(args)


class AssetStager:
    """Context for a run of the tool."""

    def __init__(self, projroot: str) -> None:
        self.projroot = projroot
        # We always calc src relative to this script.
        self.src = f'{self.projroot}/build/assets'
        self.dst: str | None = None
        self.serverdst: str | None = None
        self.win_extras_src: str | None = None
        self.win_platform: str | None = None
        self.win_type: str | None = None
        self.include_python_dylib = False
        self.include_shell_executable = False
        self.include_audio = True
        self.include_meshes = True
        self.include_collision_meshes = True
        self.include_scripts = True
        self.include_python = True
        self.include_textures = True
        self.include_fonts = True
        self.include_json = True
        self.include_pylib = False
        self.include_binary_executable = False
        self.executable_name: str | None = None
        self.pylib_src_name: str | None = None
        self.include_payload_file = False
        self.tex_suffix: str | None = None
        self.is_payload_full = False
        self.debug: bool | None = None
        self.builddir: str | None = None
        self.dist_mode: bool = False

    def run(self, args: list[str]) -> None:
        """Do the thing."""
        self._parse_args(args)

        # Ok, now for every top level dir in src, come up with a nice single
        # command to sync the needed subset of it to dst.

        # We can now use simple speedy timestamp based updates since we no
        # longer have to try to preserve timestamps to get .pyc files to
        # behave (hooray!).

        # Do our stripped down pylib dir for platforms that use that.
        if self.include_pylib:
            self._sync_pylib()
        else:
            if self.dst is not None and os.path.isdir(f'{self.dst}/pylib'):
                subprocess.run(['rm', '-rf', f'{self.dst}/pylib'], check=True)

        # Sync our server files if we're doing that.
        if self.serverdst is not None:
            self._sync_server_files()

        # On windows we need to pull in some dlls and this and that (we also
        # include a non-stripped-down set of Python libs).
        if self.win_extras_src is not None:
            self._sync_windows_extras()

        # Standard stuff in ba_data.
        self._sync_ba_data()

        # On Android we need to build a payload file so it knows what to
        # pull out of the apk.
        if self.include_payload_file:
            assert self.dst is not None
            _write_payload_file(self.dst, self.is_payload_full)

    def _parse_args(self, args: list[str]) -> None:
        """Parse args and apply to ourself."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        if len(args) < 1:
            raise RuntimeError('Expected at least one argument.')
        platform_arg = args[0]

        # First, look for a few optional args:

        # Some build types require a build dir to pull stuff from beyond
        # the normal assets dir.
        self.builddir = extract_arg(args, '-builddir')

        # In some cases we behave differently when building a 'dist'
        # version compared to a regular version; copying files in instead
        # of symlinking them/etc.
        self.dist_mode = extract_flag(args, '-dist')

        # Require either -debug or -release in args.
        # (or a few common variants from cmake, etc.)
        if '-debug' in args:
            self.debug = True
            assert '-release' not in args
        elif any(
            val in args
            for val in ['-release', '-minsizerel', '-relwithdebinfo']
        ):
            self.debug = False
        else:
            raise RuntimeError(
                "Expected some form of '-debug' or '-release' in args"
                f' ({args=}).'
            )

        if platform_arg == '-android':
            self._parse_android_args(args)
        elif platform_arg.startswith('-win'):
            self._parse_win_args(platform_arg, args)
        elif platform_arg == '-cmake':
            self.dst = args[-1]
            self.tex_suffix = '.dds'
            # Link/copy in a binary *if* builddir is provided.
            self.include_binary_executable = self.builddir is not None
            self.executable_name = 'ballisticakit'
        elif platform_arg == '-cmakemodular':
            self.dst = args[-1]
            self.tex_suffix = '.dds'
            self.include_python_dylib = True
            self.include_shell_executable = True
            self.executable_name = 'ballisticakit'
        elif platform_arg == '-cmakeserver':
            self.dst = os.path.join(args[-1], 'dist')
            self.serverdst = args[-1]
            self.include_textures = False
            self.include_audio = False
            self.include_meshes = False
            # Link/copy in a binary *if* builddir is provided.
            self.include_binary_executable = self.builddir is not None
            self.executable_name = 'ballisticakit_headless'
        elif platform_arg == '-cmakemodularserver':
            self.dst = os.path.join(args[-1], 'dist')
            self.serverdst = args[-1]
            self.include_textures = False
            self.include_audio = False
            self.include_meshes = False
            self.include_python_dylib = True
            self.include_shell_executable = True
            self.executable_name = 'ballisticakit_headless'

        elif platform_arg == '-xcode-mac':
            self.src = os.environ['SOURCE_ROOT'] + '/../build/assets'
            self.dst = (
                os.environ['TARGET_BUILD_DIR']
                + '/'
                + os.environ['UNLOCALIZED_RESOURCES_FOLDER_PATH']
            )
            self.include_pylib = True
            self.pylib_src_name = 'pylib-apple'
            self.tex_suffix = '.dds'
        elif platform_arg == '-xcode-mac-old':
            self.src = os.environ['SOURCE_ROOT'] + '/build/assets'
            self.dst = (
                os.environ['TARGET_BUILD_DIR']
                + '/'
                + os.environ['UNLOCALIZED_RESOURCES_FOLDER_PATH']
            )
            self.include_pylib = True
            self.pylib_src_name = 'pylib-apple'
            self.tex_suffix = '.dds'
        elif platform_arg == '-xcode-ios':
            self.src = os.environ['SOURCE_ROOT'] + '/build/assets'
            self.dst = (
                os.environ['TARGET_BUILD_DIR']
                + '/'
                + os.environ['UNLOCALIZED_RESOURCES_FOLDER_PATH']
            )
            self.include_pylib = True
            self.pylib_src_name = 'pylib-apple'
            self.tex_suffix = '.pvr'
        else:
            raise RuntimeError('No valid platform arg provided.')

    def _parse_android_args(self, args: list[str]) -> None:
        # On Android we get nitpicky with exactly what we want to copy
        # in since we can speed up iterations by installing stripped
        # down apks.
        self.dst = 'assets/ballistica_files'
        self.pylib_src_name = 'pylib-android'
        self.include_payload_file = True
        self.tex_suffix = '.ktx'
        self.include_audio = False
        self.include_meshes = False
        self.include_collision_meshes = False
        self.include_scripts = False
        self.include_python = False
        self.include_textures = False
        self.include_fonts = False
        self.include_json = False
        self.include_pylib = False
        for arg in args:
            if arg == '-full':
                self.include_audio = True
                self.include_meshes = True
                self.include_collision_meshes = True
                self.include_scripts = True
                self.include_python = True
                self.include_textures = True
                self.include_fonts = True
                self.include_json = True
                self.is_payload_full = True
                self.include_pylib = True
            elif arg == '-none':
                pass
            elif arg == '-meshes':
                self.include_meshes = True
                self.include_collision_meshes = True
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

    def _parse_win_args(self, platform: str, args: list[str]) -> None:
        """Parse sub-args in the windows platform string."""
        winempty, wintype, winplt = platform.split('-')
        self.win_platform = winplt
        self.win_type = wintype
        assert winempty == ''
        self.tex_suffix = '.dds'

        if wintype == 'win':
            self.dst = args[-1]
        elif wintype == 'winserver':
            self.dst = os.path.join(args[-1], 'dist')
            self.serverdst = args[-1]
            self.include_textures = False
            self.include_audio = False
            self.include_meshes = False
        else:
            raise RuntimeError(f"Invalid wintype: '{wintype}'.")

        if winplt == 'Win32':
            self.win_extras_src = f'{self.projroot}/build/assets/windows/Win32'
        elif winplt == 'x64':
            self.win_extras_src = f'{self.projroot}/build/assets/windows/x64'
        else:
            raise RuntimeError(f"Invalid winplt: '{winplt}'.")

    def _sync_windows_extras(self) -> None:
        # pylint: disable=too-many-branches
        assert self.win_extras_src is not None
        assert self.win_platform is not None
        assert self.win_type is not None
        if not os.path.isdir(self.win_extras_src):
            raise RuntimeError(
                f"Win extras src dir not found: '{self.win_extras_src}'."
            )

        # Ok, lets do full syncs on each subdir we find so we properly
        # delete anything in dst that disappeared from src. Lastly we'll
        # sync over the remaining top level files. Note: technically it'll
        # be possible to leave orphaned top level files in dst, so when
        # building packages/etc. we should always start from scratch.
        assert self.dst is not None
        assert self.debug is not None
        pyd_rules: list[str]
        if self.debug:
            pyd_rules = ['--include', '*_d.pyd']
        else:
            pyd_rules = ['--exclude', '*_d.pyd', '--include', '*.pyd']

        for dirname in ('DLLs', 'Lib'):
            # EWW: seems Windows Python currently sets its path to ./lib but
            # it comes with Lib. Windows is normally case-insensitive but
            # this messes it up when running under WSL. Let's install it as
            # lib for now.
            dstdirname = 'lib' if dirname == 'Lib' else dirname
            os.makedirs(f'{self.dst}/{dstdirname}', exist_ok=True)
            cmd: list[str] = (
                [
                    'rsync',
                    '--recursive',
                    '--times',
                    '--delete',
                    '--delete-excluded',
                    '--prune-empty-dirs',
                    '--include',
                    '*.ico',
                    '--include',
                    '*.cat',
                    '--include',
                    '*.dll',
                ]
                + pyd_rules
                + [
                    '--include',
                    '*.py',
                    '--include',
                    f'*.{OPT_PYC_SUFFIX}',
                    '--include',
                    '*/',
                    '--exclude',
                    '*',
                    f'{os.path.join(self.win_extras_src, dirname)}/',
                    f'{self.dst}/{dstdirname}/',
                ]
            )
            subprocess.run(cmd, check=True)

        # Now sync the top level individual files that we want. We could
        # technically copy everything over but this keeps staging dirs a bit
        # tidier.
        dbgsfx = '_d' if self.debug else ''

        # Note: Needs updating when Python version changes (currently 3.11).
        toplevelfiles: list[str] = [f'python311{dbgsfx}.dll']

        if self.win_type == 'win':
            toplevelfiles += [
                'libvorbis.dll',
                'libvorbisfile.dll',
                'ogg.dll',
                'OpenAL32.dll',
                'SDL2.dll',
            ]
        elif self.win_type == 'winserver':
            toplevelfiles += [f'python{dbgsfx}.exe']

        # Include debug dlls so folks without msvc can run them.
        if self.debug:
            if self.win_platform == 'x64':
                toplevelfiles += [
                    'msvcp140d.dll',
                    'vcruntime140d.dll',
                    'vcruntime140_1d.dll',
                    'ucrtbased.dll',
                ]
            else:
                toplevelfiles += [
                    'msvcp140d.dll',
                    'vcruntime140d.dll',
                    'ucrtbased.dll',
                ]

        # Include the runtime redistributables in release builds.
        if not self.debug:
            if self.win_platform == 'x64':
                toplevelfiles.append('vc_redist.x64.exe')
            elif self.win_platform == 'Win32':
                toplevelfiles.append('vc_redist.x86.exe')
            else:
                raise RuntimeError(f'Invalid win_platform {self.win_platform}')

        cmd2 = (
            ['rsync', '--times']
            + [os.path.join(self.win_extras_src, f) for f in toplevelfiles]
            + [f'{self.dst}/']
        )
        subprocess.run(cmd2, check=True)

        # If we're running under WSL we won't be able to launch these .exe
        # files unless they're marked executable, so do that here. Update:
        # gonna try simply setting this flag on the source side.
        # _run(f'chmod +x {self.dst}/*.exe')

    def _sync_pylib(self) -> None:
        assert self.pylib_src_name is not None
        assert self.dst is not None
        os.makedirs(f'{self.dst}/pylib', exist_ok=True)
        cmd: list[str] = [
            'rsync',
            '--recursive',
            '--times',
            '--delete',
            '--delete-excluded',
            '--prune-empty-dirs',
            '--include',
            '*.py',
            '--include',
            f'*.{OPT_PYC_SUFFIX}',
            '--include',
            '*/',
            '--exclude',
            '*',
            f'{self.src}/{self.pylib_src_name}/',
            f'{self.dst}/pylib/',
        ]
        subprocess.run(cmd, check=True)

    def _sync_ba_data(self) -> None:
        # pylint: disable=too-many-branches
        assert self.dst is not None
        os.makedirs(f'{self.dst}/ba_data', exist_ok=True)
        cmd: list[str] = [
            'rsync',
            '--recursive',
            '--times',
            '--delete',
            '--prune-empty-dirs',
        ]

        # Normally we use --delete-excluded so that we can do sparse
        # syncs for quick iteration on android apks/etc. However for our
        # modular builds we need to avoid that flag because we do a
        # second pass after to sync in our python-dylib stuff and with
        # that flag it all gets blown on the first pass.
        if not self.include_python_dylib:
            cmd.append('--delete-excluded')
        else:
            # Shouldn't be trying to do sparse stuff.
            if self.serverdst is not None:
                assert self.include_json and self.include_collision_meshes
            else:
                assert (
                    self.include_textures
                    and self.include_audio
                    and self.include_fonts
                    and self.include_json
                    and self.include_meshes
                    and self.include_collision_meshes
                )
            # Keep rsync from trying to prune this as an 'empty' dir.
            cmd += ['--exclude', '/python-dylib']

        if self.include_scripts:
            cmd += [
                '--include',
                '*.py',
                '--include',
                '*.pem',
                '--include',
                f'*.{OPT_PYC_SUFFIX}',
            ]

        if self.include_textures:
            assert self.tex_suffix is not None
            cmd += ['--include', f'*{self.tex_suffix}']

        if self.include_audio:
            cmd += ['--include', '*.ogg']

        if self.include_fonts:
            cmd += ['--include', '*.fdata']

        if self.include_json:
            cmd += ['--include', '*.json']

        if self.include_meshes:
            cmd += ['--include', '*.bob']

        if self.include_collision_meshes:
            cmd += ['--include', '*.cob']

        # By default we want to include all dirs and exclude all files.
        cmd += [
            '--include',
            '*/',
            '--exclude',
            '*',
            f'{self.src}/ba_data/',
            f'{self.dst}/ba_data/',
        ]
        subprocess.run(cmd, check=True)

        if self.include_binary_executable:
            self._sync_binary_executable()

        if self.include_python_dylib:
            self._sync_python_dylib()

        if self.include_shell_executable:
            self._sync_shell_executable()

    def _sync_shell_executable(self) -> None:
        if self.executable_name is None:
            raise RuntimeError('Executable name must be set for this staging.')

        path = f'{self.dst}/{self.executable_name}'

        # For now this is so simple we just do an ad-hoc write each time;
        # not worth setting up files and syncs.
        if self.debug:
            optstuff = 'export PYTHONDEVMODE=1\nexport PYTHONOPTIMIZE=0\n'
        else:
            optstuff = 'export PYTHONDEVMODE=0\nexport PYTHONOPTIMIZE=1\n'

        optnm = 'DEBUG' if self.debug else 'RELEASE'
        with open(path, 'w', encoding='utf-8') as outfile:
            outfile.write(
                '#!/bin/sh\n'
                '\n'
                '# We should error if anything here errors.\n'
                'set -e\n'
                '\n'
                '# We want Python to use UTF-8 everywhere for consistency.\n'
                '# (This will be the default in the future; see PEP 686).\n'
                f'export PYTHONUTF8=1\n'
                '\n'
                f'# This is a Ballistica {optnm} build; set Python to match.\n'
                f'{optstuff}'
                '\n'
                '# Run the app, forwarding along all arguments.\n'
                '# Basically this will do:\n'
                '#   import baenv; baenv.configure();'
                ' import babase; babase.app.run().\n'
                'exec python3.11 ba_data/python/baenv.py "$@"\n'
            )
        subprocess.run(['chmod', '+x', path], check=True)

    def _copy_or_symlink_file(self, srcpath: str, dstpath: str) -> None:
        # Copy the file in for dist mode; otherwise set up a symlink for
        # faster iteration.
        if self.dist_mode:
            # Blow away any symlink.
            if os.path.islink(dstpath):
                os.unlink(dstpath)
            if not os.path.isfile(dstpath):
                subprocess.run(['cp', srcpath, dstpath], check=True)
        else:
            if not os.path.islink(dstpath):
                relpath = os.path.relpath(srcpath, os.path.dirname(dstpath))
                subprocess.run(['ln', '-sf', relpath, dstpath], check=True)

    def _sync_binary_executable(self) -> None:
        if self.builddir is None:
            raise RuntimeError("This staging type requires '-builddir' arg.")
        if self.executable_name is None:
            raise RuntimeError('monolithic-binary-name is not set.')

        mbname = self.executable_name
        self._copy_or_symlink_file(
            f'{self.builddir}/{mbname}', f'{self.dst}/{mbname}'
        )

    def _sync_python_dylib(self) -> None:
        # pylint: disable=too-many-locals
        from batools.featureset import FeatureSet

        # Note: we're technically not *syncing* quite so much as
        # *constructing* here.

        dylib_staging_dir = f'{self.dst}/ba_data/python-dylib'

        if self.executable_name is None:
            raise RuntimeError('executable_name is not set.')

        # Name of our single shared library containing all our stuff.
        soname = f'{self.executable_name}.so'

        # All featuresets in the project with binary modules.
        bmodfeaturesets = {
            f.name: f
            for f in FeatureSet.get_all_for_project(self.projroot)
            if f.has_python_binary_module
        }

        # Map of featureset names (foo) to module filenames (_foo.so).
        fsetmfilenames = {
            f.name: f'{f.name_python_binary_module}.so'
            for f in bmodfeaturesets.values()
        }

        # Set of all module filenames (_foo.so, etc.) we should have.
        fsetmfilenamevals = set(fsetmfilenames.values())

        if not os.path.exists(dylib_staging_dir):
            os.makedirs(dylib_staging_dir, exist_ok=True)

        # Create a symlink to our original built so. (or copy the actual
        # file for dist mode)

        if self.builddir is None:
            raise RuntimeError("This staging type requires '-builddir' arg.")

        built_so_path = f'{self.builddir}/{soname}'
        staged_so_path = f'{dylib_staging_dir}/{soname}'

        self._copy_or_symlink_file(built_so_path, staged_so_path)

        # Ok, now we want to create symlinks for each of our featureset
        # Python modules. All of our stuff lives in the same .so and we
        # can use symlinks to help Python find them all there. See the
        # following:
        # https://peps.python.org/pep-0489/#multiple-modules-in-one-library
        for fsetname, featureset in bmodfeaturesets.items():
            if featureset.has_python_binary_module:
                mfilename = fsetmfilenames[fsetname]
                instpath = f'{dylib_staging_dir}/{mfilename}'
                if not os.path.islink(instpath):
                    subprocess.run(['ln', '-sf', soname, instpath], check=True)

        # Lastly, blow away anything in that dir that's not something we
        # just made (clears out featuresets that get renamed or
        # disabled, etc).
        fnames = os.listdir(dylib_staging_dir)
        for fname in fnames:
            if not fname in fsetmfilenamevals and fname != soname:
                fpath = f'{dylib_staging_dir}/{fname}'
                print(f"Pruning orphaned dylib path: '{fpath}'.")
                subprocess.run(['rm', '-rf', fpath], check=True)

    def _sync_server_files(self) -> None:
        assert self.serverdst is not None
        assert self.debug is not None
        modeval = 'debug' if self.debug else 'release'

        # NOTE: staging these directly from src; not build.
        _stage_server_file(
            projroot=self.projroot,
            mode=modeval,
            infilename=f'{self.projroot}/src/assets/server_package/'
            'ballisticakit_server.py',
            outfilename=os.path.join(
                self.serverdst,
                'ballisticakit_server.py'
                if self.win_type is not None
                else 'ballisticakit_server',
            ),
        )
        _stage_server_file(
            projroot=self.projroot,
            mode=modeval,
            infilename=f'{self.projroot}/src/assets/server_package/README.txt',
            outfilename=os.path.join(self.serverdst, 'README.txt'),
        )
        _stage_server_file(
            projroot=self.projroot,
            mode=modeval,
            infilename=f'{self.projroot}/src/assets/server_package/'
            'config_template.yaml',
            outfilename=os.path.join(self.serverdst, 'config_template.yaml'),
        )
        if self.win_type is not None:
            fname = 'launch_ballisticakit_server.bat'
            _stage_server_file(
                projroot=self.projroot,
                mode=modeval,
                infilename=f'{self.projroot}/src/assets/server_package/{fname}',
                outfilename=os.path.join(self.serverdst, fname),
            )


def _filehash(filename: str) -> str:
    """Generate a hash for a file."""
    md5 = hashlib.md5()
    with open(filename, mode='rb') as infile:
        for buf in iter(partial(infile.read, 1024), b''):
            md5.update(buf)
    return md5.hexdigest()


def _write_payload_file(assets_root: str, full: bool) -> None:
    if not assets_root.endswith('/'):
        assets_root = f'{assets_root}/'

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
                    f"Invalid filename (contains spaces): '{fpathshort}'"
                )
            payload_str += f'{fpathshort} {_filehash(fpath)}\n'
            file_list.append(fpathshort)

    payload_path = f'{assets_root}/payload_info'
    if file_list:
        # Write the file count, whether this is a 'full' payload, and
        # finally the file list.
        fullstr = '1' if full else '0'
        payload_str = f'{len(file_list)}\n{fullstr}\n{payload_str}'
        with open(payload_path, 'w', encoding='utf-8') as outfile:
            outfile.write(payload_str)
    else:
        # Remove the payload file; this will cause the game to
        # completely skip the payload processing step.
        if os.path.exists(payload_path):
            os.unlink(payload_path)


def _write_if_changed(
    path: str, contents: str, make_executable: bool = False
) -> None:
    changed: bool
    try:
        with open(path, encoding='utf-8') as infile:
            existing = infile.read()
        changed = contents != existing
    except FileNotFoundError:
        changed = True
    if changed:
        with open(path, 'w', encoding='utf-8') as outfile:
            outfile.write(contents)
        if make_executable:
            subprocess.run(['chmod', '+x', path], check=True)


def _stage_server_file(
    projroot: str, mode: str, infilename: str, outfilename: str
) -> None:
    """Stage files for the server environment with some filtering."""
    import batools.build
    from efrotools import replace_exact

    if mode not in ('debug', 'release'):
        raise RuntimeError(
            f"Invalid server-file-staging mode '{mode}';"
            f" expected 'debug' or 'release'."
        )

    print(f'Building server file: {os.path.basename(outfilename)}')

    os.makedirs(os.path.dirname(outfilename), exist_ok=True)

    basename = os.path.basename(infilename)
    if basename == 'config_template.yaml':
        # Inject all available config values into the config file.
        _write_if_changed(
            outfilename,
            batools.build.filter_server_config(str(projroot), infilename),
        )

    elif basename == 'ballisticakit_server.py':
        # Run Python in opt mode for release builds.
        with open(infilename, encoding='utf-8') as infile:
            lines = infile.read().splitlines()
            if mode == 'release':
                lines[0] = replace_exact(
                    lines[0],
                    f'#!/usr/bin/env python{PYVER}',
                    f'#!/usr/bin/env -S python{PYVER} -O',
                )
        _write_if_changed(
            outfilename, '\n'.join(lines) + '\n', make_executable=True
        )
    elif basename == 'README.txt':
        with open(infilename, encoding='utf-8') as infile:
            readme = infile.read()
        _write_if_changed(outfilename, readme)
    elif basename == 'launch_ballisticakit_server.bat':
        # Run Python in opt mode for release builds.
        with open(infilename, encoding='utf-8') as infile:
            lines = infile.read().splitlines()
        if mode == 'release':
            lines[1] = replace_exact(
                lines[1],
                ':: Python interpreter.',
                ':: Python interpreter.'
                ' (in opt mode so we use bundled .opt-1.pyc files)',
            )
            lines[2] = replace_exact(
                lines[2],
                'dist\\\\python.exe ballisticakit_server.py',
                'dist\\\\python.exe -O ballisticakit_server.py',
            )
        else:
            # In debug mode we use the bundled debug interpreter.
            lines[2] = replace_exact(
                lines[2],
                'dist\\\\python.exe ballisticakit_server.py',
                'dist\\\\python_d.exe ballisticakit_server.py',
            )

        _write_if_changed(outfilename, '\n'.join(lines) + '\n')
    else:
        raise RuntimeError(f"Unknown server file for staging: '{basename}'.")
