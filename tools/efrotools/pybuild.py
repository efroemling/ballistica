# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to building python for ios, android, etc."""

# pylint: disable=too-many-lines
from __future__ import annotations

import os
import subprocess
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efrotools import readfile, writefile, replace_exact

if TYPE_CHECKING:
    pass

# Python version we build here (not necessarily same as we use in repo).
PY_VER_ANDROID = '3.11'
PY_VER_EXACT_ANDROID = '3.11.4'
PY_VER_APPLE = '3.11'
PY_VER_EXACT_APPLE = '3.11.3'

# I occasionally run into openssl problems (particularly on arm systems)
# so keeping exact control of the versions we're building here to try
# and minimize it.
# Earlier I ran into an issue with android builds testing while OpenSSL
# was probing for ARMV7_TICK instruction presence (see android_patch_ssl here),
# and more recently I'm seeing a similar thing in 3.1.0 with arm_v8_sve_probe
# on mac. Ugh.
# See https://stackoverflow.com/questions/74059978/
# why-is-lldb-generating-exc-bad-instruction-with-user-compiled-library-on-macos
OPENSSL_VER_APPLE = '3.0.8'
OPENSSL_VER_ANDROID = '3.0.8'


# Filenames we prune from Python lib dirs in source repo to cut down on size.
PRUNE_LIB_NAMES = [
    'msilib',
    '__phello__',
    'config-*',
    'idlelib',
    'lib-dynload',
    'lib2to3',
    'multiprocessing',
    'pydoc_data',
    'site-packages',
    'ensurepip',
    'tkinter',
    'wsgiref',
    'distutils',
    'turtle.py',
    'turtledemo',
    'test',
    'sqlite3/test',
    'unittest',
    'dbm',
    'venv',
    'ctypes/test',
    'imaplib.py',
    '_sysconfigdata_*',
    'ctypes/macholib/fetch_macholib*',
    'ctypes/macholib/README.ctypes',
]

# Same but for DLLs dir (windows only)
PRUNE_DLL_NAMES = ['*.ico', '*.pdb']


def build_apple(arch: str, debug: bool = False) -> None:
    """Run a build for the provided apple arch (mac, ios, or tvos)."""
    import platform
    from efro.error import CleanError

    # IMPORTANT; seems we currently wind up building against /usr/local gettext
    # stuff. Hopefully the maintainer fixes this, but for now I need to
    # remind myself to blow it away while building.
    # (via brew remove gettext --ignore-dependencies)
    # NOTE: Should check to see if this is still necessary on Apple silicon
    # since homebrew stuff is no longer in /usr/local there.
    if bool(False):
        if (
            'MacBook-Fro' in platform.node()
            and os.environ.get('SKIP_GETTEXT_WARNING') != '1'
        ):
            if (
                subprocess.run(
                    'which gettext', shell=True, check=False
                ).returncode
                == 0
            ):
                raise CleanError(
                    'NEED TO TEMP-KILL GETTEXT (or set SKIP_GETTEXT_WARNING=1)'
                )

    builddir = 'build/python_apple_' + arch + ('_debug' if debug else '')
    subprocess.run(['rm', '-rf', builddir], check=True)
    subprocess.run(['mkdir', '-p', 'build'], check=True)
    subprocess.run(
        [
            'git',
            'clone',
            'https://github.com/beeware/Python-Apple-support.git',
            builddir,
        ],
        check=True,
    )
    os.chdir(builddir)

    # TEMP: Check out a particular commit while the branch head is broken.
    # We can actually fix this to use the current one, but something
    # broke in the underlying build even on old commits so keeping it
    # locked for now...
    # run('git checkout bf1ed73d0d5ff46862ba69dd5eb2ffaeff6f19b6')

    # Grab the branch corresponding to our target python version.
    subprocess.run(['git', 'checkout', PY_VER_APPLE], check=True)

    txt = readfile('Makefile')

    # Turn doc strings on; looks like it only adds a few hundred k.
    # txt = replace_exact(
    #     txt, '--without-doc-strings', '--with-doc-strings', count=2
    # )

    # Customize our minimum version requirements
    txt = replace_exact(
        txt,
        'VERSION_MIN-macOS=10.15\n',
        'VERSION_MIN-macOS=10.15\n',
    )
    txt = replace_exact(
        txt,
        'VERSION_MIN-iOS=12.0\n',
        'VERSION_MIN-iOS=12.0\n',
    )
    txt = replace_exact(
        txt,
        'VERSION_MIN-tvOS=9.0\n',
        'VERSION_MIN-tvOS=9.0\n',
    )
    txt = replace_exact(
        txt,
        'OPENSSL_VERSION=3.1.0\n',
        f'OPENSSL_VERSION={OPENSSL_VER_APPLE}\n',
    )

    # Don't copy in lib-dynload; we don't make it so it errors if we try.
    txt = replace_exact(
        txt,
        '\t$$(foreach sdk,$$(SDKS-$(os)),'
        'cp $$(PYTHON_FATSTDLIB-$$(sdk))/lib-dynload/*',
        '\t# (ericf disabled) $$(foreach sdk,$$(SDKS-$(os)),'
        'cp $$(PYTHON_FATSTDLIB-$$(sdk))/lib-dynload/*',
        count=1,
    )

    assert '--with-pydebug' not in txt
    if debug:
        # Add debug build flag
        txt = replace_exact(
            txt,
            '\t\t\t--enable-ipv6 \\\n',
            '\t\t\t--enable-ipv6 \\\n\t\t\t--with-pydebug \\\n',
            count=2,
        )

        # Debug lib has a different name.
        txt = replace_exact(
            txt,
            '))/lib/libpython$(PYTHON_VER).a',
            '))/lib/libpython$(PYTHON_VER)d.a',
            count=2,
        )

        txt = replace_exact(
            txt,
            '/include/python$(PYTHON_VER)',
            '/include/python$(PYTHON_VER)d',
            count=3,
        )
        txt = replace_exact(
            txt, '/config-$(PYTHON_VER)-', '/config-$(PYTHON_VER)d-', count=3
        )
        txt = replace_exact(
            txt, '/_sysconfigdata__', '/_sysconfigdata_d_', count=6
        )

        # Rename the patch files corresponding to these as well.
        patchpaths = [
            os.path.join('patch/Python', n)
            for n in os.listdir('patch/Python')
            if n.startswith('_sysconfigdata__')
        ]
        for path in patchpaths:
            subprocess.run(
                [
                    'mv',
                    path,
                    path.replace('_sysconfigdata__', '_sysconfigdata_d_'),
                ],
                check=True,
            )

    # Add our bit of patching right after standard patching.
    for tword in ('target', 'sdk'):
        txt = replace_exact(
            txt,
            (
                '\t# Apply target Python patches\n'
                f'\tcd $$(PYTHON_SRCDIR-$({tword})) && '
                'patch -p1 < $(PROJECT_DIR)/patch/Python/Python.patch\n'
            ),
            (
                '\t# Apply target Python patches\n'
                f'\tcd $$(PYTHON_SRCDIR-$({tword})) && '
                'patch -p1 < $(PROJECT_DIR)/patch/Python/Python.patch\n'
                f'\t/opt/homebrew/opt/python@3.11/bin/python3.11'
                ' ../../tools/pcommand python_apple_patch'
                f' $$(PYTHON_SRCDIR-$({tword}))\n'
            ),
            count=1,
        )
    writefile('Makefile', txt)

    # Ok; let 'er rip.
    # (we run these in parallel so limit to 1 job a piece;
    # otherwise they inherit the -j12 or whatever from the top level)
    # (also this build seems to fail with multiple threads)
    subprocess.run(
        [
            'make',
            '-j1',
            {'mac': 'Python-macOS', 'ios': 'Python-iOS', 'tvos': 'Python-tvOS'}[
                arch
            ],
        ],
        check=True,
    )
    print('python build complete! (apple/' + arch + ')')


def build_android(rootdir: str, arch: str, debug: bool = False) -> None:
    """Run a build for android with the given architecture.

    (can be arm, arm64, x86, or x86_64)
    """

    builddir = 'build/python_android_' + arch + ('_debug' if debug else '')
    subprocess.run(['rm', '-rf', builddir], check=True)
    subprocess.run(['mkdir', '-p', 'build'], check=True)
    subprocess.run(
        [
            'git',
            'clone',
            'https://github.com/GRRedWings/python3-android',
            builddir,
        ],
        check=True,
    )
    os.chdir(builddir)

    # If we need to use a particular branch.
    if bool(False):
        subprocess.run(['git', 'checkout', PY_VER_EXACT_ANDROID], check=True)

    # These builds require ANDROID_NDK to be set; make sure that's the case.
    os.environ['ANDROID_NDK'] = (
        subprocess.check_output(
            [f'{rootdir}/tools/pcommand', 'android_sdk_utils', 'get-ndk-path']
        )
        .decode()
        .strip()
    )

    # Disable builds for dependencies we don't use.
    ftxt = readfile('Android/build_deps.py')
    ftxt = replace_exact(
        ftxt,
        '        '
        'BZip2, GDBM, LibFFI, LibUUID, OpenSSL, Readline, SQLite, XZ, ZLib,\n',
        '        BZip2, LibFFI, LibUUID, OpenSSL, SQLite, XZ, ZLib,\n',
    )

    # Set specific OpenSSL version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://www.openssl.org/source/openssl-3.0.7.tar.gz'",
        f"source = 'https://www.openssl.org/"
        f"source/openssl-{OPENSSL_VER_ANDROID}.tar.gz'",
        count=1,
    )

    # Give ourselves a handle to patch the OpenSSL build.
    ftxt = replace_exact(
        ftxt,
        '        # OpenSSL handles NDK internal paths by itself',
        '        # Ericf addition: do some patching:\n'
        '        self.run(["../../../../../../../tools/pcommand",'
        ' "python_android_patch_ssl"])\n'
        '        # OpenSSL handles NDK internal paths by itself',
    )

    writefile('Android/build_deps.py', ftxt)

    # Tweak some things in the base build script; grab the right version
    # of Python and also inject some code to modify bits of python
    # after it is extracted.
    ftxt = readfile('build.sh')

    ftxt = replace_exact(ftxt, 'PYVER=3.11.0', f'PYVER={PY_VER_EXACT_ANDROID}')
    ftxt = replace_exact(
        ftxt,
        '    popd\n',
        f'    ../../../tools/pcommand'
        f' python_android_patch Python-{PY_VER_EXACT_ANDROID}\n    popd\n',
    )
    writefile('build.sh', ftxt)

    # Ok; let 'er rip!
    exargs = ' --with-pydebug' if debug else ''
    subprocess.run(
        f'ARCH={arch} ANDROID_API=21 ./build.sh{exargs} --without-ensurepip'
        f' --with-build-python=/home/ubuntu/.py311/bin/python3.11',
        shell=True,
        check=True,
    )
    print('python build complete! (android/' + arch + ')')


def apple_patch(python_dir: str) -> None:
    """New test."""
    patch_modules_setup(python_dir, 'apple')


def patch_modules_setup(python_dir: str, baseplatform: str) -> None:
    """Muck with the Setup.* files Python uses to build modules."""
    # pylint: disable=too-many-locals

    assert ' ' not in python_dir

    # Use the shiny new Setup.stdlib setup (Sounds like this will be default
    # in the future?). It looks like by mucking with Setup.stdlib.in we can
    # make pretty minimal changes to get the results we want without having
    # to inject platform-specific linker flags and whatnot like we had to
    # previously.
    subprocess.run(
        f'cd {python_dir}/Modules && ln -sf ./Setup.stdlib ./Setup.local',
        shell=True,
        check=True,
    )

    # Edit the inputs for that shiny new setup.
    fname = os.path.join(python_dir, 'Modules', 'Setup.stdlib.in')
    ftxt = readfile(fname)

    # Start by flipping everything to hard-coded static.
    ftxt = replace_exact(
        ftxt,
        '*@MODULE_BUILDTYPE@*',
        '*static*',
        count=1,
    )

    # This list should contain all possible compiled modules to start.
    # If any .so files are coming out of builds or anything unrecognized
    # is showing up in the final Setup.local or the build, add it here.
    # TODO(ericf): could automate a warning for at least the last part
    #  of that.
    cmodules = {
        '_asyncio',
        '_bisect',
        '_blake2',
        '_codecs_cn',
        '_codecs_hk',
        '_codecs_iso2022',
        '_codecs_jp',
        '_codecs_kr',
        '_codecs_tw',
        '_contextvars',
        '_crypt',
        '_csv',
        '_ctypes_test',
        '_curses_panel',
        '_curses',
        '_datetime',
        '_decimal',
        '_gdbm',
        '_dbm',
        '_elementtree',
        '_heapq',
        '_json',
        '_lsprof',
        '_lzma',
        '_md5',
        '_multibytecodec',
        '_multiprocessing',
        '_opcode',
        '_pickle',
        '_posixsubprocess',
        '_posixshmem',
        '_queue',
        '_random',
        '_sha1',
        '_sha3',
        '_sha256',
        '_sha512',
        '_socket',
        '_statistics',
        '_struct',
        '_testbuffer',
        '_testcapi',
        '_testimportmultiple',
        '_testinternalcapi',
        '_testmultiphase',
        '_testclinic',
        '_uuid',
        '_xxsubinterpreters',
        '_xxtestfuzz',
        'spwd',
        '_zoneinfo',
        'array',
        'audioop',
        'binascii',
        'cmath',
        'fcntl',
        'grp',
        'math',
        '_tkinter',
        'mmap',
        'ossaudiodev',
        'pyexpat',
        'resource',
        'select',
        'nis',
        'syslog',
        'termios',
        'unicodedata',
        'xxlimited',
        'xxlimited_35',
        'zlib',
        'readline',
    }

    # The set of modules we want statically compiled into our Python lib.
    enables = {
        '_asyncio',
        'array',
        'cmath',
        'math',
        '_contextvars',
        '_struct',
        '_random',
        '_elementtree',
        '_pickle',
        '_datetime',
        '_zoneinfo',
        '_bisect',
        '_heapq',
        '_json',
        '_ctypes',
        '_statistics',
        'unicodedata',
        'fcntl',
        'select',
        'mmap',
        '_csv',
        '_socket',
        '_sha1',
        '_sha3',
        '_sha256',
        '_sha512',
        '_blake2',
        '_lzma',
        'binascii',
        '_posixsubprocess',
        'zlib',
    }

    # Muck with things in line form for a bit.
    lines = ftxt.splitlines()

    disable_at_end = set[str]()

    for cmodule in cmodules:
        linebegin = f'@MODULE_{cmodule.upper()}_TRUE@'
        indices = [i for i, val in enumerate(lines) if linebegin in val]
        if len(indices) != 1:
            raise RuntimeError(
                f'Expected to find exact 1 entry for {cmodule};'
                f' found {len(indices)}.'
            )
        line = lines[indices[0]]

        is_enabled = not line.startswith('#')
        should_enable = cmodule in enables

        if not should_enable:
            # If something is enabled but we don't want it, comment it out.
            # Also stick all disabled stuff in a *disabled* section at the
            # bottom so it won't get built even as shared.
            if is_enabled:
                lines[indices[0]] = f'#{line}'
            disable_at_end.add(cmodule)
        elif not is_enabled:
            # Ok; its enabled and shouldn't be. What to do...
            if bool(False):
                # Uncomment the line to enable it.
                # UPDATE: Seems this doesn't work; will have to figure out
                # the right way to get things like _ctypes compiling
                # statically.
                lines[indices[0]] = replace_exact(
                    line, f'#{linebegin}', linebegin, count=1
                )
            else:
                # Don't support this currently.
                raise RuntimeError(
                    f'UNEXPECTED is_enabled=False'
                    f' should_enable=True for {cmodule}'
                )

    ftxt = '\n'.join(lines) + '\n'

    # ftxt = replace_exact(
    #     ftxt,
    #     '# Some testing modules MUST be built as shared libraries.\n'
    #     '*shared*\n',
    #     '# Some testing modules MUST be built as shared libraries.\n'
    #     '#*static*\n',
    # )

    # Now for the one remaining ULTRA-HACKY bit: getting _ctypes building
    # statically.
    # It seems that as of 3.11 it is not possible to do this through
    # Setup.stdlib.in like we do with our other stuff, as the line is
    # commented out and we get errors if we change that. Looks like
    # its not commented out anymore in 3.12 so we'll have to revisit
    # this next year, but for now... hacks!

    # To get this working for now we can dump an exact set of build flags
    # for _ctypes into the Setup.stdlib.in. We just need to provide those
    # per-platform. So, to get those:
    #  - Run 'vanilla' ios/android/etc Python builds which generate .so versions
    #  - Look for the flags in the compiler command lines for those .c files
    #  - Stuff those flags in here for the associated platform.
    if baseplatform == 'android':
        ftxt = replace_exact(
            ftxt,
            '#@MODULE__CTYPES_TRUE@_ctypes _ctypes/_ctypes.c'
            ' _ctypes/callbacks.c'
            ' _ctypes/callproc.c _ctypes/stgdict.c _ctypes/cfield.c\n',
            '_ctypes _ctypes/_ctypes.c'
            ' _ctypes/callbacks.c'
            ' _ctypes/callproc.c _ctypes/stgdict.c _ctypes/cfield.c'
            ' -I$(srcdir)/Android/sysroot/usr/include'
            ' -L$(srcdir)/Android/sysroot/usr/lib'
            ' -DHAVE_FFI_PREP_CIF_VAR=1 -DHAVE_FFI_PREP_CLOSURE_LOC=1'
            ' -DHAVE_FFI_CLOSURE_ALLOC=1'
            ' -lffi'
            '\n',
        )
    elif baseplatform == 'apple' and python_dir.split('/')[-2] == 'macosx':
        ftxt = replace_exact(
            ftxt,
            '#@MODULE__CTYPES_TRUE@_ctypes _ctypes/_ctypes.c'
            ' _ctypes/callbacks.c'
            ' _ctypes/callproc.c _ctypes/stgdict.c _ctypes/cfield.c\n',
            '_ctypes _ctypes/_ctypes.c _ctypes/callbacks.c'
            ' _ctypes/callproc.c _ctypes/stgdict.c _ctypes/cfield.c'
            ' _ctypes/malloc_closure.c'
            ' -I_ctypes/darwin -I/Applications/Xcode.app/Contents/Developer'
            '/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/'
            'usr/include/ffi'
            ' -DUSING_MALLOC_CLOSURE_DOT_C=1 -DMACOSX'
            ' -DUSING_APPLE_OS_LIBFFI=1 -DHAVE_FFI_PREP_CIF_VAR=1'
            ' -DHAVE_FFI_PREP_CLOSURE_LOC=1 -DHAVE_FFI_CLOSURE_ALLOC=1'
            ' -lffi'
            '\n',
        )
    elif baseplatform == 'apple':
        arch = python_dir.split('/')[-2]
        if '.' not in arch or arch.split('.')[0] not in {
            'iphoneos',
            'iphonesimulator',
            'appletvos',
            'appletvsimulator',
        }:
            raise RuntimeError(
                f'Unable to determine apple platform; got {arch}'
            )
        archbase = arch.split('.')[0]
        archos = 'iOS' if 'iphone' in archbase else 'tvOS'

        ftxt = replace_exact(
            ftxt,
            '#@MODULE__CTYPES_TRUE@_ctypes _ctypes/_ctypes.c'
            ' _ctypes/callbacks.c'
            ' _ctypes/callproc.c _ctypes/stgdict.c _ctypes/cfield.c\n',
            '_ctypes _ctypes/_ctypes.c _ctypes/callbacks.c'
            ' _ctypes/callproc.c _ctypes/stgdict.c _ctypes/cfield.c'
            ' _ctypes/malloc_closure.c'
            ' -I_ctypes/darwin'
            f' -I$(srcdir)/../../../../merge/{archos}'
            f'/{archbase}/libffi-3.4.2/include'
            f' -L$(srcdir)/../../../../merge/{archos}'
            f'/{archbase}/libffi-3.4.2/lib'
            ' -DUSING_MALLOC_CLOSURE_DOT_C'
            ' -DHAVE_FFI_PREP_CIF_VAR=1'
            ' -DHAVE_FFI_PREP_CLOSURE_LOC=1 -DHAVE_FFI_CLOSURE_ALLOC=1'
            ' -lffi'
            '\n',
        )
    else:
        raise RuntimeError(f'Invalid platform {baseplatform}')

    # There is one last hacky bit, which is a holdover from previous years.
    # Seems makesetup still has a bug where *any* line containing an equals
    # gets interpreted as a global DEF instead of a target, which means our
    # custom _ctypes lines above get ignored. Ugh.
    # To fix it we need to revert the *=* case to what it apparently used to
    # be: [A-Z]*=*. I wonder why this got changed and how has it not broken
    # tons of stuff? Maybe I'm missing something.
    fname2 = os.path.join(python_dir, 'Modules', 'makesetup')
    ftxt2 = readfile(fname2)
    ftxt2 = replace_exact(
        ftxt2,
        '		*=*)	DEFS="$line$NL$DEFS"; continue;;',
        '		[A-Z]*=*)	DEFS="$line$NL$DEFS"; continue;;',
    )
    assert ftxt2.count('[A-Z]*=*') == 1
    writefile(fname2, ftxt2)

    # Explicitly mark the remaining ones as disabled
    # (so Python won't try to build them as dynamic libs).
    remaining_disabled = ' '.join(sorted(disable_at_end))
    ftxt += (
        '\n# Disabled by efrotools build:\n'
        '*disabled*\n'
        f'{remaining_disabled}\n'
    )

    writefile(fname, ftxt)


def android_patch() -> None:
    """Run necessary patches on an android archive before building."""
    patch_modules_setup('.', 'android')

    # Add our low level debug call.
    _patch_py_h()

    # Use that call...
    _patch_py_wreadlink_test()

    # _patch_py_ssl()


def android_patch_ssl() -> None:
    """Run necessary patches on an android ssl before building."""

    # We bundle our own SSL root certificates on various platforms and use
    # the OpenSSL 'SSL_CERT_FILE' env var override to get them to be used
    # by default. However, OpenSSL is picky about allowing env-vars to be
    # used and something about the Android environment makes it disallow
    # them. So we need to force the issue. Alternately we could explicitly
    # pass 'cafile' args to SSLContexts whenever we do network-y stuff
    # but it seems cleaner to just have things work everywhere by default.
    fname = 'crypto/getenv.c'
    txt = readfile(fname)
    txt = replace_exact(
        txt,
        'char *ossl_safe_getenv(const char *name)\n{\n',
        (
            'char *ossl_safe_getenv(const char *name)\n'
            '{\n'
            '    // ERICF TWEAK: ALWAYS ALLOW GETENV.\n'
            '    return getenv(name);\n'
        ),
    )
    writefile(fname, txt)

    # Update: looks like this might have been disabled by default for
    # newer SSL builds used by 3.11+; can remove this if it seems stable.
    if bool(False):
        # Getting a lot of crashes in _armv7_tick, which seems to be a
        # somewhat known issue with certain arm7 devices. Sounds like
        # there are no major downsides to disabling this feature, so doing that.
        # (Sounds like its possible to somehow disable it through an env var
        # but let's just be sure and #ifdef it out in the source.
        # see https://github.com/openssl/openssl/issues/17465
        fname = 'crypto/armcap.c'
        txt = readfile(fname)
        txt = replace_exact(
            txt,
            '    /* Things that getauxval didn\'t tell us */\n'
            '    if (sigsetjmp(ill_jmp, 1) == 0) {\n'
            '        _armv7_tick();\n'
            '        OPENSSL_armcap_P |= ARMV7_TICK;\n'
            '    }\n',
            '# if 0  // ericf disabled; causing crashes'
            ' on some android devices.\n'
            '    /* Things that getauxval didn\'t tell us */\n'
            '    if (sigsetjmp(ill_jmp, 1) == 0) {\n'
            '        _armv7_tick();\n'
            '        OPENSSL_armcap_P |= ARMV7_TICK;\n'
            '    }\n'
            '# endif // 0\n',
        )
        writefile(fname, txt)


def _patch_py_wreadlink_test() -> None:
    fname = 'Python/fileutils.c'
    txt = readfile(fname)

    txt = replace_exact(
        txt,
        '    res = readlink(cpath, cbuf, cbuf_len);\n',
        (
            '    res = readlink(cpath, cbuf, cbuf_len);\n'
            '    const wchar_t *path2 = path;\n'
            '    int path2len = 0;\n'
            '    while (*path2) {\n'
            '        path2++;\n'
            '        path2len++;\n'
            '    }\n'
            '    char dlog1[512];\n'
            '    if (res >= 0) {\n'
            '        snprintf(dlog1, sizeof(dlog1), "ValsA1 pathlen=%d slen=%d'
            ' path=\'%s\'", path2len, strlen(cpath), cpath);\n'
            '    } else {\n'
            '        snprintf(dlog1, sizeof(dlog1), "ValsA2 pathlen=%d",'
            ' path2len);\n'
            '    }\n'
            '    Py_BallisticaLowLevelDebugLog(dlog1);\n'
        ),
    )

    txt = replace_exact(
        txt,
        "    cbuf[res] = '\\0'; /* buf will be null terminated */",
        (
            '    char dlog[512];\n'
            '    snprintf(dlog, sizeof(dlog), "ValsB res=%d resx=%X'
            ' eq1=%d eq2=%d",'
            ' (int)res, res, (int)(res == -1),'
            ' (int)((size_t)res == cbuf_len));\n'
            '    Py_BallisticaLowLevelDebugLog(dlog);\n'
            "    cbuf[res] = '\\0'; /* buf will be null terminated */"
        ),
    )
    writefile(fname, txt)


def _patch_py_h() -> None:
    fname = 'Include/fileutils.h'
    txt = readfile(fname)
    txt = replace_exact(
        txt,
        '\n#ifdef __cplusplus\n}\n',
        (
            '\n'
            '/* ericf hack for debugging */\n'
            '#define PY_HAVE_BALLISTICA_LOW_LEVEL_DEBUG_LOG\n'
            'extern void (*Py_BallisticaLowLevelDebugLog)(const char* msg);\n'
            '\n'
            '#ifdef __cplusplus\n}\n'
        ),
    )
    writefile(fname, txt)

    fname = 'Python/fileutils.c'
    txt = readfile(fname)
    txt = replace_exact(
        txt,
        '    _Py_END_SUPPRESS_IPH\n}',
        '    _Py_END_SUPPRESS_IPH\n}\n\n'
        'void (*Py_BallisticaLowLevelDebugLog)(const char* msg) = NULL;\n',
    )
    writefile(fname, txt)


def _patch_py_ssl() -> None:
    # UPDATE: this is now included in Python as of 3.10.6; woohoo!
    if bool(True):
        return

    # I've tracked down an issue where Python's SSL module
    # can spend lots of time in SSL_CTX_set_default_verify_paths()
    # while holding the GIL, which hitches the game like crazy.
    # On debug builds on older Android devices it can spend up to
    # 1-2 seconds there. So its necessary to release the GIL during that
    # call to keep things smooth. Will submit a report/patch to the
    # Python folks, but for now am just patching it for our Python builds.
    # NOTE TO SELF: It would also be good to look into why that call can be
    # so slow and if there's anything we can do about that.
    # UPDATE: This should be fixed in Python itself as of 3.10.6
    # (see https://github.com/python/cpython/issues/94637)
    # UPDATE 2: Have also confirmed that call is expected to be slow in
    # some situations.
    fname = 'Modules/_ssl.c'
    txt = readfile(fname)
    txt = replace_exact(
        txt,
        '    if (!SSL_CTX_set_default_verify_paths(self->ctx)) {',
        '    int ret = 0;\n'
        '\n'
        '    PySSL_BEGIN_ALLOW_THREADS\n'
        '    ret = SSL_CTX_set_default_verify_paths(self->ctx);\n'
        '    PySSL_END_ALLOW_THREADS\n'
        '\n'
        '    if (!ret) {',
    )
    writefile(fname, txt)


def winprune() -> None:
    """Prune unneeded files from windows python dists.

    Should run this after dropping updated windows libs/dlls/etc into
    our src dirs.
    """
    for libdir in (
        'src/assets/windows/Win32/Lib',
        'src/assets/windows/x64/Lib',
    ):
        assert os.path.isdir(libdir)
        assert all(' ' not in name for name in PRUNE_LIB_NAMES)
        subprocess.run(
            f'cd "{libdir}" && rm -rf ' + ' '.join(PRUNE_LIB_NAMES),
            shell=True,
            check=True,
        )
        # Kill python cache dirs.
        subprocess.run(
            f'find "{libdir}" -name __pycache__ -print0 | xargs -0 rm -rf',
            shell=True,
            check=True,
        )
        tweak_empty_py_files(libdir)

    for dlldir in (
        'src/assets/windows/Win32/DLLs',
        'src/assets/windows/x64/DLLs',
    ):
        assert os.path.isdir(dlldir)
        assert all(' ' not in name for name in PRUNE_DLL_NAMES)
        subprocess.run(
            f'cd "{dlldir}" && rm -rf ' + ' '.join(PRUNE_DLL_NAMES),
            shell=True,
            check=True,
        )

    print('Win-prune successful.')


def gather(do_android: bool, do_apple: bool) -> None:
    """Gather per-platform python headers, libs, and modules into our src.

    This assumes all embeddable py builds have been run successfully,
    and that PROJROOT is the cwd.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    class CompileArch(Enum):
        """The exhaustive set of single architectures we build for.

        Basically if there is a unique pyconfig.h for it somewhere, it
        should be listed here. This does not include debug/release though.
        """

        ANDROID_ARM = 'android_arm'
        ANDROID_ARM64 = 'android_arm64'
        ANDROID_X86 = 'android_x86'
        ANDROID_X86_64 = 'android_x86_64'
        IOS_ARM64 = 'ios_arm64'
        IOS_SIM_ARM64 = 'ios_simulator_arm64'
        IOS_SIM_X86_64 = 'ios_simulator_x86_64'
        TVOS_ARM64 = 'tvos_arm64'
        TVOS_SIM_ARM64 = 'tvos_simulator_arm64'
        TVOS_SIM_X86_64 = 'tvos_simulator_x86_64'
        MAC_ARM64 = 'mac_arm64'
        MAC_X86_64 = 'mac_x86_64'

    @dataclass
    class GroupDef:
        """apple, android, etc."""

        # Vanilla headers from the python version.
        # The first dir will be actually used and any others will
        # simply be checked to make sure they're identical.
        baseheaders: list[str]
        # Vanilla lib dir from the python version.
        basepylib: list[str]

    @dataclass
    class BuildDef:
        """macos, etc."""

        name: str
        group: GroupDef
        config_headers: dict[CompileArch, str]
        libs: list[str]
        libinst: str | None = None
        sys_config_scripts: list[str] | None = None

    # First off, clear out any existing output.
    for platform, enabled in [('android', do_android), ('apple', do_apple)]:
        if enabled:
            subprocess.run(
                [
                    'rm',
                    '-rf',
                    f'src/external/python-{platform}',
                    f'src/external/python-{platform}-debug',
                    f'src/assets/pylib-{platform}',
                ],
                check=True,
            )

    apost2 = f'src/Python-{PY_VER_EXACT_ANDROID}/Android/sysroot'
    for buildtype in ['debug', 'release']:
        debug = buildtype == 'debug'
        debug_d = 'd' if debug else ''
        bsuffix = '_debug' if buildtype == 'debug' else ''
        bsuffix2 = '-debug' if buildtype == 'debug' else ''
        alibname = 'python' + PY_VER_ANDROID + debug_d

        # Where our base stuff got built to.
        bases = {
            'mac': f'build/python_apple_mac{bsuffix}',
            'ios': f'build/python_apple_ios{bsuffix}',
            'ios_simulator': f'build/python_apple_ios{bsuffix}',
            'tvos': f'build/python_apple_tvos{bsuffix}',
            'tvos_simulator': f'build/python_apple_tvos{bsuffix}',
            'android_arm': f'build/python_android_arm{bsuffix}/build',
            'android_arm64': f'build/python_android_arm64{bsuffix}/build',
            'android_x86': f'build/python_android_x86{bsuffix}/build',
            'android_x86_64': f'build/python_android_x86_64{bsuffix}/build',
        }

        # Where some support libraries got built to.
        bases2 = {
            'mac': f'{bases["mac"]}/merge/macOS/macosx',
            'ios': f'{bases["ios"]}/merge/iOS/iphoneos',
            'ios_simulator': (
                f'{bases["ios_simulator"]}/merge/iOS/iphonesimulator'
            ),
            'tvos': f'{bases["tvos"]}/merge/tvOS/appletvos',
            'tvos_simulator': (
                f'{bases["tvos_simulator"]}/merge/tvOS/appletvsimulator'
            ),
            'android_arm': f'build/python_android_arm{bsuffix}/{apost2}',
            'android_arm64': f'build/python_android_arm64{bsuffix}/{apost2}',
            'android_x86': f'build/python_android_x86{bsuffix}/{apost2}',
            'android_x86_64': f'build/python_android_x86_64{bsuffix}/{apost2}',
        }

        # Groups should point to base sets of headers and pylibs that are
        # used by all builds in the group.
        # Note we point to a bunch of bases here but that is only for
        # sanity check purposes (to make sure they are all identical);
        # only the first actually gets used.
        groups: dict[str, GroupDef] = {
            'apple': GroupDef(
                baseheaders=[
                    f'{bases["mac"]}/build/macOS/macosx/'
                    f'python-{PY_VER_EXACT_APPLE}/Include',
                    f'{bases["ios"]}/build/iOS/iphoneos.arm64/'
                    f'python-{PY_VER_EXACT_APPLE}/Include',
                    f'{bases["ios_simulator"]}'
                    f'/build/iOS/iphonesimulator.arm64/'
                    f'python-{PY_VER_EXACT_APPLE}/Include',
                    f'{bases["ios_simulator"]}'
                    f'/build/iOS/iphonesimulator.x86_64/'
                    f'python-{PY_VER_EXACT_APPLE}/Include',
                    f'{bases["tvos"]}/build/tvOS/appletvos.arm64/'
                    f'python-{PY_VER_EXACT_APPLE}/Include',
                    f'{bases["tvos_simulator"]}'
                    f'/build/tvOS/appletvsimulator.arm64/'
                    f'python-{PY_VER_EXACT_APPLE}/Include',
                    f'{bases["tvos_simulator"]}'
                    f'/build/tvOS/appletvsimulator.x86_64/'
                    f'python-{PY_VER_EXACT_APPLE}/Include',
                ],
                basepylib=[
                    f'{bases["mac"]}/build/macOS/macosx/'
                    f'python-{PY_VER_EXACT_APPLE}/Lib',
                    f'{bases["ios"]}/build/iOS/iphoneos.arm64/'
                    f'python-{PY_VER_EXACT_APPLE}/Lib',
                    f'{bases["ios_simulator"]}'
                    f'/build/iOS/iphonesimulator.arm64/'
                    f'python-{PY_VER_EXACT_APPLE}/Lib',
                    f'{bases["ios_simulator"]}'
                    f'/build/iOS/iphonesimulator.x86_64/'
                    f'python-{PY_VER_EXACT_APPLE}/Lib',
                    f'{bases["tvos"]}/build/tvOS/appletvos.arm64/'
                    f'python-{PY_VER_EXACT_APPLE}/Lib',
                    f'{bases["tvos_simulator"]}'
                    f'/build/tvOS/appletvsimulator.arm64/'
                    f'python-{PY_VER_EXACT_APPLE}/Lib',
                    f'{bases["tvos_simulator"]}'
                    f'/build/tvOS/appletvsimulator.x86_64/'
                    f'python-{PY_VER_EXACT_APPLE}/Lib',
                ],
            ),
            'android': GroupDef(
                baseheaders=[
                    f'build/python_android_arm/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Include',
                    f'build/python_android_arm64/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Include',
                    f'build/python_android_x86/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Include',
                    f'build/python_android_x86_64/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Include',
                ],
                basepylib=[
                    f'build/python_android_arm/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Lib',
                    f'build/python_android_arm64/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Lib',
                    f'build/python_android_x86/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Lib',
                    f'build/python_android_x86_64/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Lib',
                ],
            ),
        }

        def _apple_libs(base: str) -> list[str]:
            # pylint: disable=cell-var-from-loop
            out = [
                (
                    f'{bases2[base]}/python-{PY_VER_EXACT_APPLE}'
                    f'/libPython{PY_VER_APPLE}.a'
                ),
                f'{bases2[base]}/openssl-{OPENSSL_VER_APPLE}/lib/libssl.a',
                f'{bases2[base]}/openssl-{OPENSSL_VER_APPLE}/lib/libcrypto.a',
                f'{bases2[base]}/xz-5.4.2/lib/liblzma.a',
                f'{bases2[base]}/bzip2-1.0.8/lib/libbz2.a',
            ]
            if base != 'mac':
                out.append(f'{bases2[base]}/libffi-3.4.2/lib/libffi.a')
            return out

        def _android_libs(base: str) -> list[str]:
            # pylint: disable=cell-var-from-loop
            return [
                f'{bases[base]}/usr/lib/lib{alibname}.a',
                f'{bases2[base]}/usr/lib/libssl.a',
                f'{bases2[base]}/usr/lib/libcrypto.a',
                f'{bases2[base]}/usr/lib/liblzma.a',
                f'{bases2[base]}/usr/lib/libsqlite3.a',
                f'{bases2[base]}/usr/lib/libffi.a',
                f'{bases2[base]}/usr/lib/libbz2.a',
                f'{bases2[base]}/usr/lib/libuuid.a',
            ]

        builds: list[BuildDef] = [
            BuildDef(
                name='macos',
                group=groups['apple'],
                # There's just a single config for the universal build;
                # that seems odd but I guess it's right?...
                config_headers={
                    CompileArch.MAC_ARM64: bases2['mac']
                    + f'/python-{PY_VER_EXACT_APPLE}/Headers/pyconfig.h',
                    CompileArch.MAC_X86_64: bases2['mac']
                    + f'/python-{PY_VER_EXACT_APPLE}/Headers/pyconfig.h',
                },
                sys_config_scripts=[
                    bases2['mac']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_darwin_darwin.py'
                ],
                libs=_apple_libs('mac'),
            ),
            BuildDef(
                name='ios',
                group=groups['apple'],
                config_headers={
                    CompileArch.IOS_ARM64: bases2['ios']
                    + f'/python-{PY_VER_EXACT_APPLE}/Headers/pyconfig-arm64.h',
                },
                sys_config_scripts=[
                    bases2['ios']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_ios_iphoneos.py',
                    bases2['ios']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_ios_iphoneos_arm64.py',
                ],
                libs=_apple_libs('ios'),
            ),
            BuildDef(
                name='ios_simulator',
                group=groups['apple'],
                config_headers={
                    CompileArch.IOS_SIM_ARM64: bases2['ios_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/Headers/pyconfig-arm64.h',
                    CompileArch.IOS_SIM_X86_64: bases2['ios_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/Headers/pyconfig-x86_64.h',
                },
                sys_config_scripts=[
                    bases2['ios_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_ios_iphonesimulator.py',
                    bases2['ios_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_ios_iphonesimulator_arm64.py',
                    bases2['ios_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_ios_iphonesimulator_x86_64.py',
                ],
                libs=_apple_libs('ios_simulator'),
            ),
            BuildDef(
                name='tvos',
                group=groups['apple'],
                config_headers={
                    CompileArch.TVOS_ARM64: bases2['tvos']
                    + f'/python-{PY_VER_EXACT_APPLE}/Headers/pyconfig-arm64.h',
                },
                sys_config_scripts=[
                    bases2['tvos']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_tvos_appletvos.py',
                    bases2['tvos']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_tvos_appletvos_arm64.py',
                ],
                libs=_apple_libs('tvos'),
            ),
            BuildDef(
                name='tvos_simulator',
                group=groups['apple'],
                config_headers={
                    CompileArch.TVOS_SIM_ARM64: bases2['tvos_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/Headers/pyconfig-arm64.h',
                    CompileArch.TVOS_SIM_X86_64: bases2['ios_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/Headers/pyconfig-x86_64.h',
                },
                sys_config_scripts=[
                    bases2['tvos_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_tvos_appletvsimulator.py',
                    bases2['tvos_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_tvos_appletvsimulator_arm64.py',
                    bases2['tvos_simulator']
                    + f'/python-{PY_VER_EXACT_APPLE}/python-stdlib/'
                    f'_sysconfigdata_{debug_d}_tvos_appletvsimulator_x86_64.py',
                ],
                libs=_apple_libs('tvos_simulator'),
            ),
            BuildDef(
                name='android_arm',
                group=groups['android'],
                config_headers={
                    CompileArch.ANDROID_ARM: bases['android_arm']
                    + f'/usr/include/{alibname}/pyconfig.h'
                },
                sys_config_scripts=[
                    bases['android_arm'] + f'/usr/lib/python{PY_VER_ANDROID}/'
                    f'_sysconfigdata_{debug_d}_linux_arm-linux-androideabi.py'
                ],
                libs=_android_libs('android_arm'),
                libinst='android_armeabi-v7a',
            ),
            BuildDef(
                name='android_arm64',
                group=groups['android'],
                config_headers={
                    CompileArch.ANDROID_ARM64: bases['android_arm64']
                    + f'/usr/include/{alibname}/pyconfig.h'
                },
                sys_config_scripts=[
                    bases['android_arm64'] + f'/usr/lib/python{PY_VER_ANDROID}/'
                    f'_sysconfigdata_{debug_d}'
                    f'_linux_aarch64-linux-android.py'
                ],
                libs=_android_libs('android_arm64'),
                libinst='android_arm64-v8a',
            ),
            BuildDef(
                name='android_x86',
                group=groups['android'],
                config_headers={
                    CompileArch.ANDROID_X86: bases['android_x86']
                    + f'/usr/include/{alibname}/pyconfig.h'
                },
                sys_config_scripts=[
                    bases['android_x86'] + f'/usr/lib/python{PY_VER_ANDROID}/'
                    f'_sysconfigdata_{debug_d}'
                    f'_linux_i686-linux-android.py'
                ],
                libs=_android_libs('android_x86'),
                libinst='android_x86',
            ),
            BuildDef(
                name='android_x86_64',
                group=groups['android'],
                config_headers={
                    CompileArch.ANDROID_X86_64: bases['android_x86_64']
                    + f'/usr/include/{alibname}/pyconfig.h'
                },
                sys_config_scripts=[
                    bases['android_x86_64']
                    + f'/usr/lib/python{PY_VER_ANDROID}/'
                    f'_sysconfigdata_{debug_d}'
                    f'_linux_x86_64-linux-android.py'
                ],
                libs=_android_libs('android_x86_64'),
                libinst='android_x86_64',
            ),
        ]

        # Assemble per-group stuff.
        for grpname, grp in groups.items():
            if not do_android and grpname == 'android':
                continue
            if not do_apple and grpname == 'apple':
                continue

            # Sanity check: if we have more than one set of base headers/libs
            # for this group, make sure they're all identical.
            for dirlist, dirdesc in [
                (grp.baseheaders, 'baseheaders'),
                (grp.basepylib, 'basepylib'),
            ]:
                for i in range(len(dirlist) - 1):
                    returncode = subprocess.run(
                        ['diff', dirlist[i], dirlist[i + 1]],
                        check=False,
                        capture_output=True,
                    ).returncode
                    if returncode != 0:
                        raise RuntimeError(
                            f'Sanity check failed: the following {dirdesc}'
                            f' dirs differ:\n'
                            f'{dirlist[i]}\n'
                            f'{dirlist[i+1]}'
                        )

            pylib_dst = f'src/assets/pylib-{grpname}'
            src_dst = f'src/external/python-{grpname}{bsuffix2}'
            include_dst = os.path.join(src_dst, 'include')
            lib_dst = os.path.join(src_dst, 'lib')

            assert not os.path.exists(src_dst)
            assert not os.path.exists(lib_dst)
            subprocess.run(['mkdir', '-p', src_dst], check=True)
            subprocess.run(['mkdir', '-p', lib_dst], check=True)

            # Copy in the base 'include' dir for this group.
            subprocess.run(
                ['cp', '-r', grp.baseheaders[0], include_dst],
                check=True,
            )

            # Write a master pyconfig.h that reroutes to each
            # compile-arch's actual header (pyconfig-FOO_BAR.h).
            # FIXME - we are using ballistica-specific values here;
            #  could be nice to generalize this so its usable elsewhere.
            unified_pyconfig = (
                f'#if BA_XCODE_BUILD\n'
                f'// Necessary to get the TARGET_OS_SIMULATOR define.\n'
                f'#include <TargetConditionals.h>\n'
                f'#endif\n'
                f'\n'
                f'#if BA_OSTYPE_MACOS and defined(__aarch64__)\n'
                f'#include "pyconfig_{CompileArch.MAC_ARM64.value}.h"\n'
                f'\n'
                f'#elif BA_OSTYPE_MACOS and defined(__x86_64__)\n'
                f'#include "pyconfig_{CompileArch.MAC_X86_64.value}.h"\n'
                f'\n'
                f'#elif BA_OSTYPE_IOS and defined(__aarch64__)\n'
                f'#if TARGET_OS_SIMULATOR\n'
                f'#include "pyconfig_{CompileArch.IOS_SIM_ARM64.value}.h"\n'
                f'#else\n'
                f'#include "pyconfig_{CompileArch.IOS_ARM64.value}.h"\n'
                f'#endif  // TARGET_OS_SIMULATOR\n'
                f'\n'
                f'#elif BA_OSTYPE_IOS and defined(__x86_64__)\n'
                f'#if TARGET_OS_SIMULATOR\n'
                f'#include "pyconfig_{CompileArch.IOS_SIM_X86_64.value}.h"\n'
                f'#else\n'
                f'#error this platform combo should not be possible\n'
                f'#endif  // TARGET_OS_SIMULATOR\n'
                f'\n'
                f'#elif BA_OSTYPE_TVOS and defined(__aarch64__)\n'
                f'#if TARGET_OS_SIMULATOR\n'
                f'#include "pyconfig_{CompileArch.TVOS_SIM_ARM64.value}.h"\n'
                f'#else\n'
                f'#include "pyconfig_{CompileArch.TVOS_ARM64.value}.h"\n'
                f'#endif  // TARGET_OS_SIMULATOR\n'
                f'\n'
                f'#elif BA_OSTYPE_TVOS and defined(__x86_64__)\n'
                f'#if TARGET_OS_SIMULATOR\n'
                f'#include "pyconfig_{CompileArch.TVOS_SIM_X86_64.value}.h"\n'
                f'#else\n'
                f'#error this platform combo should not be possible\n'
                f'#endif  // TARGET_OS_SIMULATOR\n'
                f'\n'
                f'#elif BA_OSTYPE_ANDROID and defined(__arm__)\n'
                f'#include "pyconfig_{CompileArch.ANDROID_ARM.value}.h"\n'
                f'\n'
                f'#elif BA_OSTYPE_ANDROID and defined(__aarch64__)\n'
                f'#include "pyconfig_{CompileArch.ANDROID_ARM64.value}.h"\n'
                f'\n'
                f'#elif BA_OSTYPE_ANDROID and defined(__i386__)\n'
                f'#include "pyconfig_{CompileArch.ANDROID_X86.value}.h"\n'
                f'\n'
                f'#elif BA_OSTYPE_ANDROID and defined(__x86_64__)\n'
                f'#include "pyconfig_{CompileArch.ANDROID_X86_64.value}.h"\n'
                f'\n'
                f'#else\n'
                f'#error unknown platform\n'
                f'\n'
                f'#endif\n'
            )
            with open(
                f'{include_dst}/pyconfig.h', 'w', encoding='utf-8'
            ) as hfile:
                hfile.write(unified_pyconfig)

            # Pylib is the same for debug and release, so we only need
            # to assemble for one of them.
            if not os.path.exists(pylib_dst):
                assert not os.path.exists(pylib_dst)
                subprocess.run(['mkdir', '-p', pylib_dst], check=True)
                subprocess.run(
                    [
                        'rsync',
                        '--recursive',
                        '--include',
                        '*.py',
                        '--exclude',
                        '__pycache__',
                        '--include',
                        '*/',
                        '--exclude',
                        '*',
                        f'{grp.basepylib[0]}/',
                        pylib_dst,
                    ],
                    check=True,
                )
                tweak_empty_py_files(pylib_dst)

                # Prune a bunch of modules we don't need to cut down on size.
                # NOTE: allowing shell expansion in PRUNE_LIB_NAMES so need
                # to run this as shell=True.
                subprocess.run(
                    'cd "'
                    + pylib_dst
                    + '" && rm -rf '
                    + ' '.join(PRUNE_LIB_NAMES),
                    shell=True,
                    check=True,
                )

                # UPDATE: now bundling sysconfigdata scripts AND
                # disabling site.py when initializing python for bundled
                # builds so this should no longer be necessary.
                if bool(False):
                    # Some minor filtering to system scripts:
                    # on iOS/tvOS, addusersitepackages() leads to a crash
                    # due to _sysconfigdata_dm_ios_darwin module not existing,
                    # so let's remove that logic in all cases.
                    # In general we *could* bundle _sysconfigdata everywhere but
                    # gonna try to just avoid anything that uses it for now
                    # and save a bit of memory.
                    fname = f'{pylib_dst}/site.py'
                    txt = readfile(fname)
                    txt = replace_exact(
                        txt,
                        '    known_paths = addusersitepackages(known_paths)',
                        '    # efro tweak: this craps out on ios/tvos.\n'
                        '    # (and we don\'t use it anyway)\n'
                        '    # known_paths = addusersitepackages(known_paths)',
                    )
                    writefile(fname, txt)

            # Pull stuff in from all builds in this group.
            for build in builds:
                if build.group is not grp:
                    continue

                # Copy the build's pyconfig.h in with a unique name
                # (which the unified pyconfig.h we wrote above will route to).
                for compilearch, pycfgpath in build.config_headers.items():
                    dstpath = f'{include_dst}/pyconfig_{compilearch.value}.h'
                    assert not os.path.exists(dstpath), f'exists!: {dstpath}'
                    subprocess.run(['cp', pycfgpath, dstpath], check=True)

                # If the build points at any sysconfig scripts, pull those
                # in (and ensure each has a unique name).
                if build.sys_config_scripts is not None:
                    for script in build.sys_config_scripts:
                        scriptdst = os.path.join(
                            pylib_dst, os.path.basename(script)
                        )
                        if os.path.exists(scriptdst):
                            raise RuntimeError(
                                'Multiple sys-config-scripts trying to write'
                                f" to '{scriptdst}'."
                            )
                        subprocess.run(['cp', script, pylib_dst], check=True)

                # Copy in this build's libs.
                libinst = (
                    build.libinst if build.libinst is not None else build.name
                )
                targetdir = f'{lib_dst}/{libinst}'
                subprocess.run(['rm', '-rf', targetdir], check=True)
                subprocess.run(['mkdir', '-p', targetdir], check=True)
                for lib in build.libs:
                    finalpath = os.path.join(targetdir, os.path.basename(lib))
                    assert not os.path.exists(finalpath)
                    subprocess.run(['cp', lib, targetdir], check=True)
                    assert os.path.exists(finalpath)

    print('Great success!')


def tweak_empty_py_files(dirpath: str) -> None:
    """Find any zero-length Python files and make them length 1

    I'm finding that my jenkins server updates modtimes on all empty files
    when fetching updates regardless of whether anything has changed.
    This leads to a decent number of assets getting rebuilt when not
    necessary.

    As a slightly-hacky-but-effective workaround I'm sticking a newline
    up in there.
    """
    for root, _subdirs, fnames in os.walk(dirpath):
        for fname in fnames:
            if (
                fname.endswith('.py') or fname == 'py.typed'
            ) and os.path.getsize(os.path.join(root, fname)) == 0:
                if bool(False):
                    print('Tweaking empty py file:', os.path.join(root, fname))
                with open(
                    os.path.join(root, fname), 'w', encoding='utf-8'
                ) as outfile:
                    outfile.write('\n')
