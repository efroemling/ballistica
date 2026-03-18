# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to building python for ios, android, etc."""

# pylint: disable=too-many-lines
from __future__ import annotations

import os
import subprocess
from enum import Enum
from dataclasses import dataclass

from efrotools.util import readfile, writefile, replace_exact

# Python version we build here (not necessarily same as we use in repo).
PY_VER_ANDROID = '3.13'
PY_VER_EXACT_ANDROID = '3.13.12'

# Keeping exact control of the OpenSSL version to avoid known issues
# (ARMV7_TICK probing crashes on some Android devices, 3.0.17 is buggy).
# NOTE: 3.0.17 IS BUGGY (see https://github.com/openssl/openssl/issues/28171)
OPENSSL_VER_ANDROID = '3.0.16'

# Android repo doesn't seem to be getting updated much so manually
# bumping various versions to keep things up to date.
ANDROID_API_VER = 24
ZLIB_VER_ANDROID = '1.3.2'
XZ_VER_ANDROID = '5.8.1'
BZIP2_VER_ANDROID = '1.0.8'
GDBM_VER_ANDROID = '1.24'
LIBFFI_VER_ANDROID = '3.4.7'
LIBUUID_VER_ANDROID = ('2.41', '2.41')
NCURSES_VER_ANDROID = '6.5'
READLINE_VER_ANDROID = '8.2'
SQLITE_VER_ANDROID = ('2025', '3500400')

# Filenames we prune from Python lib dirs in source repo to cut down on
# size.
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
    '_pyrepl/mypy.ini',
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


def build_android(rootdir: str, arch: str, debug: bool = False) -> None:
    """Run a build for android with the given architecture.

    (can be arm, arm64, x86, or x86_64)
    """

    builddir = f'build/python_android_{arch}_old' + ('_debug' if debug else '')
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
    ndkpath = (
        subprocess.check_output(
            [f'{rootdir}/tools/pcommand', 'android_sdk_utils', 'get-ndk-path']
        )
        .decode()
        .strip()
    )
    if not os.path.isdir(ndkpath):
        raise RuntimeError(f'NDK path does not exist: "{ndkpath}".')

    os.environ['ANDROID_NDK'] = ndkpath

    # TEMP - hard coding old ndk for the moment; looks like libffi needs to
    # be fixed to build with it. I *think* this has already been done; we just
    # need to wait for the official update beyond 3.4.4.
    # print('TEMP TEMP TEMP HARD-CODING OLD NDK FOR LIBFFI BUG')
    # os.environ['ANDROID_NDK'] = '/home/ubuntu/AndroidSDK/ndk/25.2.9519653'

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
        "source = 'https://www.openssl.org/source/openssl-3.4.0.tar.gz'",
        f"source = 'https://www.openssl.org/"
        f"source/openssl-{OPENSSL_VER_ANDROID}.tar.gz'",
        count=1,
    )

    # Set specific ZLib version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://www.zlib.net/zlib-1.3.1.tar.gz'",
        f"source = 'https://www.zlib.net/zlib-{ZLIB_VER_ANDROID}.tar.gz'",
        count=1,
    )

    # Set specific XZ version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://tukaani.org/xz/xz-5.6.4.tar.xz'",
        f"source = 'https://tukaani.org/xz/xz-{XZ_VER_ANDROID}.tar.xz'",
        count=1,
    )

    # Set specific BZip2 version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz'",
        f'source = '
        f"'https://sourceware.org/pub/bzip2/bzip2-{BZIP2_VER_ANDROID}.tar.gz'",
        count=1,
    )

    # Set specific GDBM version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://ftp.gnu.org/gnu/gdbm/gdbm-1.24.tar.gz'",
        "source = 'https://ftp.gnu.org/"
        f"gnu/gdbm/gdbm-{GDBM_VER_ANDROID}.tar.gz'",
        count=1,
    )

    # Set specific libffi version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://github.com/libffi/libffi/releases/"
        "download/v3.4.7/libffi-3.4.7.tar.gz'",
        "source = 'https://github.com/libffi/libffi/releases/"
        f"download/v{LIBFFI_VER_ANDROID}/libffi-{LIBFFI_VER_ANDROID}.tar.gz'",
    )

    # Set specific LibUUID version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://mirrors.edge.kernel.org/pub/linux/utils/"
        "util-linux/v2.40/util-linux-2.40.4.tar.xz'",
        "source = 'https://mirrors.edge.kernel.org/pub/linux/utils/"
        f'util-linux/v{LIBUUID_VER_ANDROID[0]}/'
        f"util-linux-{LIBUUID_VER_ANDROID[1]}.tar.xz'",
        count=1,
    )

    # Seems we need to explicitly tell 32 bit libuuid builds to be ok
    # with 32 bit timestamps. Should check this again once NDK 29 comes
    # around.
    if arch in {'arm', 'x86'}:
        ftxt = replace_exact(
            ftxt,
            (
                "    configure_args = ['--disable-all-programs',"
                " '--enable-libuuid']"
            ),
            (
                "    configure_args = ['--disable-all-programs',"
                " '--disable-year2038', '--enable-libuuid']"
            ),
        )

    # Set specific NCurses version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://ftp.gnu.org/gnu/ncurses/ncurses-6.5.tar.gz'",
        "source = 'https://ftp.gnu.org/gnu/ncurses/"
        f"ncurses-{NCURSES_VER_ANDROID}.tar.gz'",
        count=1,
    )

    # Set specific ReadLine version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://ftp.gnu.org/gnu/readline/readline-8.2.tar.gz'",
        "source = 'https://ftp.gnu.org/gnu/readline/"
        f"readline-{READLINE_VER_ANDROID}.tar.gz'",
        count=1,
    )

    # Set specific SQLite version.
    ftxt = replace_exact(
        ftxt,
        "source = 'https://sqlite.org/2024/sqlite-autoconf-3460000.tar.gz'",
        "source = 'https://sqlite.org/"
        f'{SQLITE_VER_ANDROID[0]}/'
        f"sqlite-autoconf-{SQLITE_VER_ANDROID[1]}.tar.gz'",
        count=1,
    )

    # Give ourselves a handle to patch the OpenSSL build.
    ftxt = replace_exact(
        ftxt,
        '        # OpenSSL handles NDK internal paths by itself',
        '        # Ericf addition: do some patching:\n'
        '        self.run(["../../../../../../../tools/pcommand",'
        ' "python_android_patch_ssl_old"])\n'
        '        # OpenSSL handles NDK internal paths by itself',
    )

    writefile('Android/build_deps.py', ftxt)

    ftxt = readfile('Android/util.py')

    ftxt = replace_exact(
        ftxt,
        "choices=range(30, 40), dest='android_api_level'",
        "choices=range(23, 40), dest='android_api_level'",
    )
    writefile('Android/util.py', ftxt)

    # Tweak some things in the base build script; grab the right version
    # of Python and also inject some code to modify bits of python
    # after it is extracted.
    ftxt = readfile('build.sh')

    # Repo has gone 30+, but we currently want our own which is lower.
    # timestampfix = '--disable-year2038 ' if arch == 'arm' else ''

    ftxt = replace_exact(
        ftxt,
        'COMMON_ARGS="--arch ${ARCH:-arm} --api ${ANDROID_API:-30}"',
        'COMMON_ARGS="--arch ${ARCH:-arm} --api ${ANDROID_API:-'
        + str(ANDROID_API_VER)
        + '}"',
    )
    ftxt = replace_exact(ftxt, 'PYVER=3.13.0', f'PYVER={PY_VER_EXACT_ANDROID}')
    ftxt = replace_exact(
        ftxt,
        '    popd\n',
        f'    ../../../tools/pcommand'
        f' python_android_patch_old Python-{PY_VER_EXACT_ANDROID}\n    popd\n',
    )
    writefile('build.sh', ftxt)

    # Ok; let 'er rip!
    exargs = ' --with-pydebug' if debug else ''
    pyvershort = PY_VER_ANDROID.replace('.', '')
    subprocess.run(
        f'ARCH={arch} ANDROID_API={ANDROID_API_VER}'
        f' ./build.sh{exargs} --without-ensurepip'
        f' --with-build-python='
        f'/home/ubuntu/.py{pyvershort}/bin/python{PY_VER_ANDROID}',
        shell=True,
        check=True,
    )
    print('python build complete! (android/' + arch + ')')


def patch_modules_setup(python_dir: str, baseplatform: str) -> None:
    """Muck with the Setup.* files Python uses to build modules."""
    del baseplatform  # Unused.

    assert ' ' not in python_dir

    # Use the shiny new Setup.stdlib setup (Sounds like this will be
    # default in the future?). It looks like by mucking with
    # Setup.stdlib.in we can make pretty minimal changes to get the
    # results we want without having to inject platform-specific linker
    # flags and whatnot like we had to previously.
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
    #
    # TODO(ericf): could automate a warning for at least the last part
    #  of that.
    cmodules: set[tuple[str, int]] = {
        ('_asyncio', 1),
        ('_bisect', 1),
        ('_blake2', 1),
        ('_codecs_cn', 1),
        ('_codecs_hk', 1),
        ('_codecs_iso2022', 1),
        ('_codecs_jp', 1),
        ('_codecs_kr', 1),
        ('_codecs_tw', 1),
        ('_contextvars', 1),
        # ('_crypt', 1),
        ('_csv', 1),
        ('_ctypes_test', 1),
        ('_curses_panel', 1),
        ('_curses', 1),
        ('_datetime', 1),
        ('_decimal', 1),
        ('_gdbm', 1),
        ('_dbm', 1),
        ('_elementtree', 1),
        ('_heapq', 1),
        ('_json', 1),
        ('_lsprof', 1),
        ('_lzma', 1),
        ('_md5', 1),
        ('_multibytecodec', 1),
        ('_multiprocessing', 1),
        ('_opcode', 1),
        ('_pickle', 1),
        ('_posixsubprocess', 1),
        ('_posixshmem', 1),
        ('_queue', 1),
        ('_random', 1),
        ('_sha1', 1),
        ('_sha2', 1),
        ('_sha3', 1),
        ('_socket', 1),
        ('_statistics', 1),
        ('_struct', 1),
        ('_testbuffer', 1),
        ('_testcapi', 1),
        ('_testimportmultiple', 1),
        ('_testinternalcapi', 1),
        ('_testmultiphase', 1),
        ('_testsinglephase', 1),
        ('_testexternalinspection', 1),
        ('_testclinic', 1),
        ('_sqlite3', 1),
        ('_uuid', 1),
        # ('_xxsubinterpreters', 1),
        ('_xxtestfuzz', 1),
        # ('spwd', 1),
        ('_zoneinfo', 1),
        ('array', 1),
        # ('audioop', 1),
        ('binascii', 1),
        ('cmath', 1),
        ('fcntl', 1),
        ('grp', 1),
        ('math', 1),
        ('_tkinter', 1),
        ('mmap', 1),
        # ('ossaudiodev', 1),
        ('pyexpat', 1),
        ('resource', 1),
        ('select', 1),
        # ('nis', 1),
        ('syslog', 1),
        ('termios', 1),
        ('unicodedata', 1),
        ('xxlimited', 1),
        ('xxlimited_35', 1),
        ('zlib', 1),
        ('readline', 1),
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
        '_opcode',
        'unicodedata',
        'fcntl',
        'select',
        'mmap',
        '_csv',
        '_socket',
        '_blake2',
        '_lzma',
        '_sqlite3',
        'binascii',
        '_posixsubprocess',
        'zlib',
    }

    # Muck with things in line form for a bit.
    lines = ftxt.splitlines()

    disable_at_end = set[str]()

    for cmodule, expected_instances in cmodules:
        linebegin = f'@MODULE_{cmodule.upper()}_TRUE@'
        indices = [i for i, val in enumerate(lines) if linebegin in val]
        if len(indices) != expected_instances:
            raise RuntimeError(
                f'Expected to find exactly {expected_instances}'
                f' entry for {cmodule};'
                f' found {len(indices)}.'
            )
        for index in indices:
            line = lines[index]

            is_enabled = not line.startswith('#')
            should_enable = cmodule in enables

            if not should_enable:
                # If something is enabled but we don't want it, comment it
                # out. Also stick all disabled stuff in a *disabled* section
                # at the bottom so it won't get built even as shared.
                if is_enabled:
                    lines[index] = f'#{line}'
                disable_at_end.add(cmodule)
            elif not is_enabled:
                # Ok; its enabled and shouldn't be. What to do...
                if bool(False):
                    # Uncomment the line to enable it.
                    #
                    # UPDATE: Seems this doesn't work; will have to figure
                    # out the right way to get things like _ctypes compiling
                    # statically.
                    lines[index] = replace_exact(
                        line, f'#{linebegin}', linebegin, count=1
                    )
                else:
                    # Don't support this currently.
                    raise RuntimeError(
                        f'UNEXPECTED is_enabled=False'
                        f' should_enable=True for {cmodule}'
                    )

    ftxt = '\n'.join(lines) + '\n'

    # There is one last hacky bit, which is a holdover from previous years.
    # Seems makesetup still has a bug where *any* line containing an equals
    # gets interpreted as a global DEF instead of a target, which means our
    # custom _ctypes lines above get ignored. Ugh.
    #
    # To fix it we need to revert the *=* case to what it apparently used to
    # be: [A-Z]*=*. I wonder why this got changed and how has it not broken
    # tons of stuff? Maybe I'm missing something.
    # fname2 = os.path.join(python_dir, 'Modules', 'makesetup')
    # ftxt2 = readfile(fname2)
    # ftxt2 = replace_exact(
    #     ftxt2,
    #     '		*=*)	DEFS="$line$NL$DEFS"; continue;;',
    #     '		[A-Z]*=*)	DEFS="$line$NL$DEFS"; continue;;',
    # )
    # assert ftxt2.count('[A-Z]*=*') == 1
    # writefile(fname2, ftxt2)

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

    _patch_android_ctypes()


def _patch_android_ctypes() -> None:

    # ctypes seems hard-coded to load python from a .so for android
    # builds, which fails because we are statically compiling Python
    # into our main.so. It seems that the fallback default does the
    # right thing in our case?..
    fname = 'Lib/ctypes/__init__.py'
    txt = readfile(fname)
    txt = replace_exact(
        txt,
        'elif _sys.platform in ["android", "cygwin"]:\n',
        'elif _sys.platform in ["cygwin"]:  # efro: android uses static lib\n',
    )
    writefile(fname, txt)


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

    # Final fix for this problem.
    # It seems that readlink() might be broken in android at the moment,
    # returning an int while claiming it to be a ssize_t value. This makes
    # the error case (-1) actually come out as 4294967295. When cast back
    # to an int it is -1, so that's what we do. This should be fine to do
    # even on a fixed version.
    txt = replace_exact(
        txt,
        '    res = readlink(cpath, cbuf, cbuf_len);\n',
        '    res = (int)readlink(cpath, cbuf, cbuf_len);\n',
    )

    # Verbose problem exploration:
    # txt = replace_exact(
    #     txt,
    #     '#include <stdlib.h>               // mbstowcs()\n',
    #     '#include <stdlib.h>               // mbstowcs()\n'
    #     '#include <sys/syscall.h>\n',
    # )

    # txt = replace_exact(txt, '    Py_ssize_t res;\n', '')

    # txt = replace_exact(
    #     txt,
    #     '    res = readlink(cpath, cbuf, cbuf_len);\n',
    #     (
    #         '    Py_ssize_t res = readlink(cpath, cbuf, cbuf_len);\n'
    #         '    Py_ssize_t res2 = readlink(cpath, cbuf, cbuf_len);\n'
    #         '    ssize_t res3 = readlink(cpath, cbuf, cbuf_len);\n'
    #         '    ssize_t res4 = readlinkat(AT_FDCWD, cpath,
    # cbuf, cbuf_len);\n'
    #         '    int res5 = syscall(SYS_readlinkat, AT_FDCWD, cpath,'
    #         ' cbuf, cbuf_len);\n'
    #         '    ssize_t res6 = syscall(SYS_readlinkat, AT_FDCWD, cpath,'
    #         ' cbuf, cbuf_len);\n'
    #         '    char dlog[512];\n'
    #         '    snprintf(dlog, sizeof(dlog),'
    #         ' "res=%zd res2=%zd res3=%zd res4=%zd res5=%d res6=%zd"\n'
    #         '             " (res == -1)=%d (res2 == -1)=%d (res3 == -1)=%d'
    #         ' (res4 == -1)=%d (res5 == -1)=%d (res6 == -1)=%d",\n'
    #         '             res, res2, res3, res4, res5, res6,\n'
    #         '             (res == -1), (res2 == -1), (res3 == -1),'
    #         ' (res4 == -1), (res5 == -1), (res6 == -1));\n'
    #         '    Py_BallisticaLowLevelDebugLog(dlog);\n'
    #         '\n'
    #         '    char dlog1[512];\n'
    #         '    ssize_t st1;\n'
    #         '    Py_ssize_t st2;\n'
    #         '    snprintf(dlog1, sizeof(dlog1),
    # "ValsA1 sz1=%zu sz2=%zu res=%zd'
    #         ' res_hex=%lX res_cmp=%d res_cmp_2=%d pathlen=%d slen=%d'
    #         ' path=\'%s\'", sizeof(st1), sizeof(st2), res,'
    #         ' res, (int)(res == -1), (int)((int)res == -1),'
    #         ' (int)wcslen(path), (int)strlen(cpath), cpath);\n'
    #         '    Py_BallisticaLowLevelDebugLog(dlog1);\n'
    #     ),
    # )

    # txt = replace_exact(
    #     txt,
    #     "    cbuf[res] = '\\0'; /* buf will be null terminated */",
    #     (
    #         '    char dlog[512];\n'
    #         '    snprintf(dlog, sizeof(dlog), "ValsB res=%d resx=%lX'
    #         ' eq1=%d eq2=%d",'
    #         ' (int)res, res, (int)(res == -1),'
    #         ' (int)((size_t)res == cbuf_len));\n'
    #         '    Py_BallisticaLowLevelDebugLog(dlog);\n'
    #         "    cbuf[res] = '\\0'; /* buf will be null terminated */"
    #     ),
    # )
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


def gather(do_android: bool) -> None:
    # pylint: disable=too-many-statements
    """Gather per-platform python headers, libs, and modules into our src.

    This assumes all embeddable py builds have been run successfully,
    and that PROJROOT is the cwd.
    """
    # pylint: disable=too-many-locals
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
    if do_android:
        subprocess.run(
            [
                'rm',
                '-rf',
                'src/external/python-android-old',
                'src/external/python-android-old-debug',
                'src/assets/pylib-android-old',
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
            'android_arm': f'build/python_android_arm_old{bsuffix}/build',
            'android_arm64': f'build/python_android_arm64_old{bsuffix}/build',
            'android_x86': f'build/python_android_x86_old{bsuffix}/build',
            'android_x86_64': f'build/python_android_x86_64_old{bsuffix}/build',
        }

        # Where some support libraries got built to.
        bases2 = {
            'android_arm': (f'build/python_android_arm_old{bsuffix}/{apost2}'),
            'android_arm64': (
                f'build/python_android_arm64_old{bsuffix}/{apost2}'
            ),
            'android_x86': (f'build/python_android_x86_old{bsuffix}/{apost2}'),
            'android_x86_64': (
                f'build/python_android_x86_64_old{bsuffix}/{apost2}'
            ),
        }

        # Groups should point to base sets of headers and pylibs that
        # are used by all builds in the group.
        groups: dict[str, GroupDef] = {
            'android': GroupDef(
                baseheaders=[
                    f'build/python_android_arm_old/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Include',
                    f'build/python_android_arm64_old/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Include',
                    f'build/python_android_x86_old/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Include',
                    f'build/python_android_x86_64_old/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Include',
                ],
                basepylib=[
                    f'build/python_android_arm_old/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Lib',
                    f'build/python_android_arm64_old/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Lib',
                    f'build/python_android_x86_old/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Lib',
                    f'build/python_android_x86_64_old/src/'
                    f'Python-{PY_VER_EXACT_ANDROID}/Lib',
                ],
            ),
        }

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
                name='android_arm64',
                group=groups['android'],
                config_headers={
                    CompileArch.ANDROID_ARM64: bases['android_arm64']
                    + f'/usr/include/{alibname}/pyconfig.h'
                },
                sys_config_scripts=[
                    bases['android_arm64'] + f'/usr/lib/python{PY_VER_ANDROID}/'
                    f'_sysconfigdata_{debug_d}'
                    # f'_linux_aarch64-linux-android.py'
                    f'_android_aarch64-linux-android.py'
                    # f'_linux_.py'
                ],
                libs=_android_libs('android_arm64'),
                libinst='android_arm64-v8a',
            ),
            BuildDef(
                name='android_arm',
                group=groups['android'],
                config_headers={
                    CompileArch.ANDROID_ARM: bases['android_arm']
                    + f'/usr/include/{alibname}/pyconfig.h'
                },
                sys_config_scripts=[
                    bases['android_arm']
                    + f'/usr/lib/python{PY_VER_ANDROID}/'
                    # f'_sysconfigdata_{debug_d}_linux_arm-linux-androideabi.py'
                    f'_sysconfigdata_{debug_d}_android_arm-linux-androideabi.py'
                    # f'_sysconfigdata_{debug_d}_linux_.py'
                ],
                libs=_android_libs('android_arm'),
                libinst='android_armeabi-v7a',
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
                    # f'_linux_x86_64-linux-android.py'
                    f'_android_x86_64-linux-android.py'
                    # f'_linux_.py'
                ],
                libs=_android_libs('android_x86_64'),
                libinst='android_x86_64',
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
                    # f'_linux_i686-linux-android.py'
                    f'_android_i686-linux-android.py'
                    # f'_linux_.py'
                ],
                libs=_android_libs('android_x86'),
                libinst='android_x86',
            ),
        ]

        # Assemble per-group stuff.
        for grpname, grp in groups.items():
            if not do_android and grpname == 'android':
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

            grpname_out = 'android-old' if grpname == 'android' else grpname
            pylib_dst = f'src/assets/pylib-{grpname_out}'
            src_dst = f'src/external/python-{grpname_out}{bsuffix2}'
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
                f'#if BA_PLATFORM_ANDROID and defined(__arm__)\n'
                f'#include "pyconfig_{CompileArch.ANDROID_ARM.value}.h"\n'
                f'\n'
                f'#elif BA_PLATFORM_ANDROID and defined(__aarch64__)\n'
                f'#include "pyconfig_{CompileArch.ANDROID_ARM64.value}.h"\n'
                f'\n'
                f'#elif BA_PLATFORM_ANDROID and defined(__i386__)\n'
                f'#include "pyconfig_{CompileArch.ANDROID_X86.value}.h"\n'
                f'\n'
                f'#elif BA_PLATFORM_ANDROID and defined(__x86_64__)\n'
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
                        # Note to self: Python 3.12 seemed to change
                        # something where the sys_config_scripts for
                        # each of the architectures has the same name
                        # whereas it did not before. We could patch this
                        # by hand to split them out again, but for now
                        # just going to hope it gets fixed in 3.13 (when
                        # Android Python becomes an officially supported
                        # target; yay!). Hopefully nobody is using stuff
                        # from sysconfig anyway. But if they are, I
                        # rearranged the order so x86 is the actual one
                        # which will hopefully make errors obvious.
                        if os.path.exists(scriptdst):
                            print(
                                'WARNING: TEMPORARILY ALLOWING'
                                ' REPEAT SYS CONFIG SCRIPTS'
                            )
                            # raise RuntimeError(
                            #     'Multiple sys-config-scripts trying to write'
                            #     f" to '{scriptdst}'."
                            # )
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
