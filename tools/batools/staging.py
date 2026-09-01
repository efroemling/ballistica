# Released under the MIT License. See LICENSE for details.
#
"""Stage files for builds."""

import os
import sys
import subprocess

from efro.terminal import Clr
from efro.util import extract_arg, extract_flag
from efrotools.util import is_wsl_windows_build_path
from efrotools.pyver import PYVER, PYVERNODOT
from batools._bundlestage import sync_asset_bundle
from batools._pycstage import update_pycs


def stage_build(projroot: str, args: list[str] | None = None) -> None:
    """Stage assets for a build."""

    if args is None:
        args = sys.argv

    BuildStager(projroot).run(args)


class BuildStager:
    """Context for a run of the tool."""

    def __init__(self, projroot: str) -> None:
        self.projroot = projroot
        self.desc = 'unknown'
        # We always calc src relative to this script.
        self.src = f'{self.projroot}/build/assets'
        self.dst: str | None = None
        self.serverdst: str | None = None
        self.win_extras_src: str | None = None
        self.win_platform: str | None = None
        self.win_type: str | None = None
        self.include_python_dylib = False
        self.include_shell_executable = False
        self.include_scripts = True
        self.include_python = True
        self.include_json = True
        self.include_pylib = False
        # Name of the asset-bundle profile to stage (see
        # batools.assetbundleprofiles). When set, copies
        # ``.cache/asset_bundle/<profile>/manifest.json`` + the CAS
        # blobs it references into ``<staged>/ba_data/``. None means no
        # bundle is staged for this build.
        self.asset_bundle_profile: str | None = None
        self.include_binary_executable = False
        self.executable_name: str | None = None
        self.pylib_src_path: str | None = None
        # Android-only: generate side-by-side .pyc files for staged
        # Python (for zipimport directly from the apk) and protect
        # them from our rsync delete passes.
        self.include_payload_pycs = False
        # Suffix for staged bundle blob names; Android uses '.bablob'
        # so blobs pack uncompressed in the apk (suffix-matched gradle
        # noCompress) and get served as spans from the apk mapping.
        # COUPLED to kUseAssetsFromApk in platform_android.cc.
        self.bundled_blob_suffix = ''
        self.debug: bool | None = None
        self.builddir: str | None = None
        self.dist_mode: bool = False
        self.wsl_chmod_workaround = False

    def run(self, args: list[str]) -> None:
        """Do the thing."""
        self._parse_args(args)

        print(
            f'{Clr.BLU}Staging for {Clr.MAG}{Clr.BLD}{self.desc}{Clr.RST}'
            f'{Clr.BLU} at {Clr.MAG}{Clr.BLD}{self.dst}'
            f'{Clr.RST}{Clr.BLU}...{Clr.RST}',
            flush=True,
        )

        # Do our janky wsl permissions workaround if need be.
        if (
            self.wsl_chmod_workaround
            and self.dst is not None
            and os.path.exists(self.dst)
        ):
            cmd = ['chmod', '-R', 'u+w', self.dst]
            print(
                f'{Clr.CYN}'
                f'Running WSL permissions workaround: {cmd}'
                f'{Clr.RST}...'
            )
            subprocess.run(cmd, check=True)

        # Ok, now for every top level dir in src, come up with a nice
        # single command to sync the needed subset of it to dst.

        # We can now use simple speedy timestamp based updates since we
        # no longer have to try to preserve timestamps to get .pyc files
        # to behave (hooray!).

        # Do our stripped down pylib dir for platforms that use that.
        if self.include_pylib:
            self._sync_pylib()
        else:
            if self.dst is not None and os.path.isdir(f'{self.dst}/pylib'):
                subprocess.run(['rm', '-rf', f'{self.dst}/pylib'], check=True)

        # Sync our server files if we're doing that.
        if self.serverdst is not None:
            self._sync_server_files()

        # On windows we need to pull in some dlls and this and that (we
        # also include a non-stripped-down set of Python libs).
        if self.win_extras_src is not None:
            self._sync_windows_extras()

        # Legacy assets going into ba_data.
        self._sync_ba_data_legacy()

        if self.asset_bundle_profile is not None:
            assert self.dst is not None
            sync_asset_bundle(
                self.projroot,
                self.dst,
                self.asset_bundle_profile,
                blob_suffix=self.bundled_blob_suffix,
            )

        if self.include_binary_executable:
            self._sync_binary_executable()

        if self.include_python_dylib:
            self._sync_python_dylib()

        if self.include_shell_executable:
            self._sync_shell_executable()

        # On Android, generate side-by-side .pyc files for all staged
        # Python; zipimport reads these when importing directly out of
        # the apk (see docs/initiatives/android-apk-direct-ba-data.md).
        # Must run before payload-file generation so they're included
        # in its manifest.
        if self.include_payload_pycs:
            assert self.dst is not None
            # Transitional cleanup: drop the legacy extraction payload
            # manifest if this staged tree still carries one from
            # before the extract-to-disk phase was retired (nothing
            # reads it anymore; safe to remove once this has run).
            legacy_payload = os.path.join(self.dst, 'payload_info')
            if os.path.isfile(legacy_payload):
                os.unlink(legacy_payload)
            # Guard against staging pycs the device interpreter would
            # silently *ignore*: pyc magic is feature-release-specific,
            # so the interpreter running this stage must match the
            # project's bundled Python version (a mismatch wouldn't
            # error at runtime — zipimport just quietly falls back to
            # compiling source on every launch).
            hostver = '.'.join(str(v) for v in sys.version_info[:2])
            if hostver != PYVER:
                raise RuntimeError(
                    f'Staging under Python {hostver} but the project'
                    f' bundles Python {PYVER}; staged .pyc files would'
                    f' be silently ignored by the bundled interpreter.'
                    f' Stage with Python {PYVER}.'
                )
            # Match the level the device interpreter runs at
            # (core_python.cc: 0 for debug builds, 1 for release) —
            # assert stripping and __debug__ folding are compile-time,
            # and zipimport loads these pycs regardless of the runtime
            # -O flag, so a mismatch silently ships the wrong
            # semantics.
            assert self.debug is not None
            pycresults = update_pycs(self.dst, optimize=0 if self.debug else 1)
            if pycresults.errors:
                errstr = '\n'.join(pycresults.errors)
                raise RuntimeError(
                    f'{len(pycresults.errors)} error(s)'
                    f' staging .pyc files:\n{errstr}'
                )
            print(
                f'{Clr.BLU}Staged .pycs for {self.dst}:'
                f' {Clr.BLD}{pycresults.compiled}{Clr.RST}{Clr.BLU} compiled,'
                f' {Clr.BLD}{pycresults.pruned}{Clr.RST}{Clr.BLU} pruned,'
                f' {Clr.BLD}{pycresults.up_to_date}{Clr.RST}{Clr.BLU}'
                f' up to date.{Clr.RST}',
                flush=True,
            )

    def _parse_args(self, args: list[str]) -> None:
        """Parse args and apply to ourself."""

        if len(args) < 1:
            raise RuntimeError('Expected at least one argument.')
        platform_arg = args[0]

        # First, look for a few optional args:

        # Some build types require a build dir to pull stuff from beyond
        # the normal assets dir.
        self.builddir = extract_arg(args, '-builddir')

        # In some cases we behave differently when building a 'dist'
        # version compared to a regular version; copying files in
        # instead of symlinking them/etc.
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
            self.desc = 'android'
            self._parse_android_args()
        elif platform_arg.startswith('-win'):
            self.desc = 'windows'
            self._parse_win_args(platform_arg, args)
        elif platform_arg == '-cmake':
            self.desc = 'cmake'
            self.dst = args[-1]
            # Link/copy in a binary *if* builddir is provided.
            self.include_binary_executable = self.builddir is not None
            self.executable_name = 'ballisticakit'
        elif platform_arg == '-cmakemodular':
            self.desc = 'cmake modular'
            self.dst = args[-1]
            self.include_python_dylib = True
            self.include_shell_executable = True
            self.executable_name = 'ballisticakit'
        elif platform_arg == '-cmakeserver':
            self.desc = 'cmake server'
            self.dst = os.path.join(args[-1], 'dist')
            self.serverdst = args[-1]
            # Link/copy in a binary *if* builddir is provided.
            self.include_binary_executable = self.builddir is not None
            self.executable_name = 'ballisticakit_headless'
        elif platform_arg == '-cmakemodularserver':
            self.desc = 'cmake modular server'
            self.dst = os.path.join(args[-1], 'dist')
            self.serverdst = args[-1]
            self.include_python_dylib = True
            self.include_shell_executable = True
            self.executable_name = 'ballisticakit_headless'
        elif platform_arg == '-xcode-mac':
            self.desc = 'xcode mac'
            self.src = os.environ['SOURCE_ROOT'] + '/../build/assets'
            self.dst = (
                os.environ['TARGET_BUILD_DIR']
                + '/'
                + os.environ['UNLOCALIZED_RESOURCES_FOLDER_PATH']
            )
            self.include_pylib = True
            self.pylib_src_path = 'pylib-apple'
        elif platform_arg in ('-xcode-ios', '-xcode-tvos'):
            # iOS and tvOS stage identically (same Apple pylib + asset
            # layout into the .app bundle's flat Resources dir).
            self.desc = 'xcode ' + platform_arg.removeprefix('-xcode-')
            self.src = os.environ['SOURCE_ROOT'] + '/../build/assets'
            self.dst = (
                os.environ['TARGET_BUILD_DIR']
                + '/'
                + os.environ['UNLOCALIZED_RESOURCES_FOLDER_PATH']
            )
            self.include_pylib = True
            self.pylib_src_path = 'pylib-apple'
        else:
            raise RuntimeError('No valid platform arg provided.')

        # Every staged build bundles a named asset-package profile (see
        # batools.assetbundleprofiles): server builds (``serverdst`` set)
        # get the headless profile, other builds the gui one. This now
        # includes Apple Xcode builds -- their staging phase runs
        # remotely (inside xcodebuild on the ba-apple env), so their
        # cloud-build Make targets (_mac-cloud-build / _ios-cloud-build /
        # _tvos-cloud-build) run `asset_bundle_build gui-minimal` on that
        # remote env before xcodebuild, ensuring the .cache/asset_bundle
        # tree is present when this staging phase reads it there.
        self.asset_bundle_profile = (
            'headless-minimal' if self.serverdst is not None else 'gui-minimal'
        )

        # Special case: running rsync to a windows drive via WSL fails
        # to overwrite non-writable files.
        #
        # See: https://github.com/microsoft/WSL/issues/5087
        #
        # As a janky workaround, make everything in our dst dir writable
        # by us before we do our work.
        if is_wsl_windows_build_path(self.projroot):
            self.wsl_chmod_workaround = True

    def _parse_android_args(self) -> None:
        # Android serves everything staged here directly out of the
        # apk at runtime (Python via zipimport, bundled asset blobs as
        # spans from a memory-map); nothing is extracted to disk. See
        # docs/initiatives/android-apk-direct-ba-data.md.
        self.dst = 'assets/ballistica_files'
        self.pylib_src_path = 'pylib-android'
        self.include_pylib = True
        self.include_payload_pycs = True
        self.bundled_blob_suffix = '.bablob'

    def _parse_win_args(self, platform: str, args: list[str]) -> None:
        """Parse sub-args in the windows platform string."""
        winempty, wintype, winplt = platform.split('-')
        self.win_platform = winplt
        self.win_type = wintype
        assert winempty == ''

        if wintype == 'win':
            self.dst = args[-1]
        elif wintype == 'winserver':
            self.dst = os.path.join(args[-1], 'dist')
            self.serverdst = args[-1]
        else:
            raise RuntimeError(f"Invalid wintype: '{wintype}'.")

        if winplt == 'Win32':
            self.win_extras_src = f'{self.projroot}/build/assets/windows/Win32'
        elif winplt == 'x64':
            self.win_extras_src = f'{self.projroot}/build/assets/windows/x64'
        else:
            raise RuntimeError(f"Invalid winplt: '{winplt}'.")

    def _sync_windows_extras(self) -> None:
        assert self.win_extras_src is not None
        assert self.win_platform is not None
        assert self.win_type is not None
        if not os.path.isdir(self.win_extras_src):
            raise RuntimeError(
                f"Win extras src dir not found: '{self.win_extras_src}'."
            )

        # Ok, lets do full syncs on each subdir we find so we properly
        # delete anything in dst that disappeared from src. Lastly we'll
        # sync over the remaining top level files. Note: technically
        # it'll be possible to leave orphaned top level files in dst, so
        # when building packages/etc. we should always start from
        # scratch.
        assert self.dst is not None
        assert self.debug is not None
        pyd_rules: list[str]
        if self.debug:
            pyd_rules = ['--include', '*_d.pyd']
        else:
            pyd_rules = ['--exclude', '*_d.pyd', '--include', '*.pyd']

        for dirname in ('DLLs', 'Lib'):
            # EWW: seems Windows Python currently sets its path to ./lib
            # but it comes with Lib. Windows is normally
            # case-insensitive but this messes it up when running under
            # WSL. Let's install it as lib for now.
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
                    '*/',
                    '--exclude',
                    '*',
                    f'{os.path.join(self.win_extras_src, dirname)}/',
                    f'{self.dst}/{dstdirname}/',
                ]
            )
            self._purge_pycache_dirs(f'{self.dst}/{dstdirname}/')
            subprocess.run(cmd, check=True)

        # Now sync the top level individual files that we want. We could
        # technically copy everything over but this keeps staging dirs a
        # bit tidier.
        dbgsfx = '_d' if self.debug else ''

        toplevelfiles: list[str] = [f'python{PYVERNODOT}{dbgsfx}.dll']

        if self.win_type == 'win':
            toplevelfiles += [
                'libEGL.dll',
                'libGLESv2.dll',
                'libvorbis.dll',
                'libvorbisfile.dll',
                'ogg.dll',
                'OpenAL32.dll',
                'SDL3.dll',
                # ANGLE (libGLESv2.dll) depends on zlib1.dll for shader
                # blob caching. Through Python 3.13 we borrowed the copy
                # in Python's DLLs/; 3.14 links zlib statically and no
                # longer ships the dll, so we now stage our own top-level
                # copy alongside the other ANGLE bits.
                'zlib1.dll',
            ]
        elif self.win_type == 'winserver':
            toplevelfiles += [f'python{dbgsfx}.exe']

        # Include debug dlls so folks without msvc can run them.
        #
        # UPDATE: No longer doing this as of build 22258. If people need
        # to run debug builds they should do things the 'right' way and
        # install VS.
        if self.debug and bool(False):
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

        # If we're running under WSL we won't be able to launch these
        # .exe files unless they're marked executable, so do that here.
        # Update: gonna try simply setting this flag on the source side.
        # _run(f'chmod +x {self.dst}/*.exe')

    def _purge_pycache_dirs(self, path: str) -> None:
        # Added this at all locations where we used to sync in built pyc
        # files under __pycache__ dirs; we don't do that anymore but
        # there's lots of old dirs scattered in existing builds. Doing
        # explicit purges for now to avoid 'cannot delete non-empty
        # directory' warnings about those dirs. We can kill this after a
        # while.
        pcachepaths: list[str] = []
        for root, dnames, _fnames in os.walk(path):
            if '__pycache__' in dnames:
                pcachepaths.append(os.path.join(root, '__pycache__'))

        if pcachepaths:
            import shutil

            for pcachepath in pcachepaths:
                print(
                    f'Purging old staged pycache dir'
                    f' (we don\'t bundle pycache files anymore): {pcachepath}'
                )
                shutil.rmtree(pcachepath)

    def _sync_pylib(self) -> None:
        assert self.pylib_src_path is not None
        assert not self.pylib_src_path.endswith('/')
        assert self.dst is not None
        os.makedirs(f'{self.dst}/pylib', exist_ok=True)
        cmd: list[str] = [
            'rsync',
            '--recursive',
            '--times',
            '--delete',
            '--delete-excluded',
            '--prune-empty-dirs',
        ]
        if self.include_payload_pycs:
            # Shield our generated side-by-side .pyc files from the
            # deletion pass (a plain exclude wouldn't survive
            # --delete-excluded; a protect rule does). Android-only;
            # other platforms don't stage pycs and keep current
            # behavior.
            cmd += ['--filter', 'P *.pyc']
        cmd += [
            '--include',
            '*.py',
            '--include',
            '*.so',
            '--include',
            '*/',  # Note to self: is this necessary?
            '--exclude',
            '*',
            f'{self.src}/{self.pylib_src_path}/',
            f'{self.dst}/pylib/',
        ]
        self._purge_pycache_dirs(f'{self.dst}/pylib/')
        subprocess.run(cmd, check=True)

    def _sync_ba_data_legacy(self) -> None:
        assert self.dst is not None
        os.makedirs(f'{self.dst}/ba_data', exist_ok=True)
        cmd: list[str] = [
            'rsync',
            '--recursive',
            '--times',
            '--delete',
            '--prune-empty-dirs',
        ]

        # Traditionally we used --delete-excluded so that we could do
        # sparse syncs for quick iteration on android apks/etc. However
        # for our modular builds we need to avoid that flag because we
        # do a further pass after to sync in python-dylib stuff and
        # with that flag it all gets blown away on the first pass.
        if not self.include_python_dylib:
            cmd.append('--delete-excluded')
        else:
            # Shouldn't be trying to do sparse stuff in server builds.
            assert self.include_json
            # Keep rsync from deleting the other stuff we're overlaying.
            cmd += ['--exclude', '/python-dylib']

        if self.include_payload_pycs:
            # Shield our generated side-by-side .pyc files from the
            # deletion pass (a plain exclude wouldn't survive
            # --delete-excluded; a protect rule does). Android-only;
            # other platforms don't stage pycs and keep current
            # behavior.
            cmd += ['--filter', 'P *.pyc']

        if self.include_scripts:
            cmd += [
                '--include',
                '*.py',
                '--include',
                '*.pem',
                # Bundled zstd dictionaries (e.g. bacommon mesh dicts) ride
                # along with the scripts they accompany.
                '--include',
                '*.zstddict',
            ]

        if self.include_json:
            cmd += ['--include', '*.json']

        # By default we want to include all dirs and exclude all files.
        cmd += [
            '--include',
            '*/',
            '--exclude',
            '*',
            f'{self.src}/ba_data/',
            f'{self.dst}/ba_data/',
        ]
        self._purge_pycache_dirs(f'{self.dst}/ba_data/')
        subprocess.run(cmd, check=True)

    def _sync_shell_executable(self) -> None:
        if self.executable_name is None:
            raise RuntimeError('Executable name must be set for this staging.')

        path = f'{self.dst}/{self.executable_name}'

        # For now this is so simple we just do an ad-hoc write each
        # time; not worth setting up files and syncs.
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
                f'exec python{PYVER} ba_data/python/baenv.py "$@"\n'
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
                (
                    'ballisticakit_server.py'
                    if self.win_type is not None
                    else 'ballisticakit_server'
                ),
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
            'config_template.toml',
            outfilename=os.path.join(self.serverdst, 'config_template.toml'),
        )
        if self.win_type is not None:
            fname = 'launch_ballisticakit_server.bat'
            _stage_server_file(
                projroot=self.projroot,
                mode=modeval,
                infilename=f'{self.projroot}/src/assets/server_package/{fname}',
                outfilename=os.path.join(self.serverdst, fname),
            )


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
    from efrotools.util import replace_exact

    if mode not in ('debug', 'release'):
        raise RuntimeError(
            f"Invalid server-file-staging mode '{mode}';"
            f" expected 'debug' or 'release'."
        )

    print(f'Building server file: {os.path.basename(outfilename)}')

    os.makedirs(os.path.dirname(outfilename), exist_ok=True)

    basename = os.path.basename(infilename)
    if basename == 'config_template.toml':
        # Inject all available config values into the config file.
        _write_if_changed(
            outfilename,
            batools.build.filter_server_config_toml(str(projroot), infilename),
        )

    elif basename == 'ballisticakit_server.py':
        # Run Python in opt mode for release builds.
        with open(infilename, encoding='utf-8') as infile:
            lines = infile.read().splitlines()
            if mode == 'release':
                lines[0] = replace_exact(
                    lines[0],
                    f'#!/usr/bin/env -S python{PYVER} -B',
                    f'#!/usr/bin/env -S python{PYVER} -OB',
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
                ':: Python interpreter. (in opt mode)',
            )
            lines[2] = replace_exact(
                lines[2],
                'dist\\\\python.exe -B ballisticakit_server.py',
                'dist\\\\python.exe -OB ballisticakit_server.py',
            )
        else:
            # In debug mode we use the bundled debug interpreter.
            lines[2] = replace_exact(
                lines[2],
                'dist\\\\python.exe -B ballisticakit_server.py',
                'dist\\\\python_d.exe -B ballisticakit_server.py',
            )

        _write_if_changed(outfilename, '\n'.join(lines) + '\n')
    else:
        raise RuntimeError(f"Unknown server file for staging: '{basename}'.")
