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
"""Functionality related to building python for ios, android, etc."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import efrotools

if TYPE_CHECKING:
    from typing import List, Dict, Any

# Overall version we're using for the game currently.
PYTHON_VERSION_MAJOR = "3.7"

# Specific version we're using on apple builds.
PYTHON_VERSION_APPLE = "3.7.0"

# Specific version we're using on android builds.
PYTHON_VERSION_ANDROID = "3.7.2"

ENABLE_OPENSSL = True


def build_apple(arch: str, debug: bool = False) -> None:
    """Run a build for the provided apple arch (mac, ios, or tvos)."""
    builddir = 'build/python_apple_' + arch + ('_debug' if debug else '')
    efrotools.run('rm -rf "' + builddir + '"')
    efrotools.run('mkdir -p build')
    efrotools.run('git clone '
                  'git@github.com:pybee/Python-Apple-support.git "' +
                  builddir + '"')
    os.chdir(builddir)
    efrotools.run('git checkout 3.7')

    # On mac we currently have to add the _scproxy module or urllib will
    # fail.
    txt = efrotools.readfile('patch/Python/Setup.embedded')
    if arch == 'mac':
        txt += ('\n'
                '# ericf added - mac urllib needs this\n'
                '_scproxy _scproxy.c '
                '-framework SystemConfiguration '
                '-framework CoreFoundation')

    # Turn off sqlite module. (scratch that; leaving it in.)
    # txt = efrotools.replace_one(txt, '_sqlite3 -I$(', '#_sqlite3 -I$(')
    # txt = txt.replace('    _sqlite/', '#    _sqlite/')

    # Turn off xz compression module. (scratch that; leaving it in.)
    # txt = efrotools.replace_one(txt, '_lzma _', '#_lzma _')

    # Turn off bzip2 module.
    txt = efrotools.replace_one(txt, '_bz2 _b', '#_bz2 _b')

    # Turn off openssl module (only if not doing openssl).
    if not ENABLE_OPENSSL:
        txt = efrotools.replace_one(txt, '_hashlib _hashopenssl.c',
                                    '#_hashlib _hashopenssl.c')

    # Turn off various other stuff we don't use.
    for line in [
            '_codecs _codecsmodule.c',
            '_codecs_cn cjkcodecs/_codecs_cn.c',
            '_codecs_hk cjkcodecs/_codecs_hk.c',
            '_codecs_iso2022 cjkcodecs/',
            '_codecs_jp cjkcodecs/_codecs_jp.c',
            '_codecs_jp cjkcodecs/_codecs_jp.c',
            '_codecs_kr cjkcodecs/_codecs_kr.c',
            '_codecs_tw cjkcodecs/_codecs_tw.c',
            '_lsprof _lsprof.o rotatingtree.c',
            '_multibytecodec cjkcodecs/multibytecodec.c',
            '_multiprocessing _multiprocessing/multiprocessing.c',
            '_opcode _opcode.c',
            'audioop audioop.c',
            'grp grpmodule.c',
            'mmap mmapmodule.c',
            'parser parsermodule.c',
            'pyexpat expat/xmlparse.c',
            '    expat/xmlrole.c ',
            '    expat/xmltok.c ',
            '    pyexpat.c ',
            '    -I$(srcdir)/Modules/expat ',
            '    -DHAVE_EXPAT_CONFIG_H -DUSE_PYEXPAT_CAPI'
            ' -DXML_DEV_URANDOM',
            'resource resource.c',
            'syslog syslogmodule.c',
            'termios termios.c',
            '_ctypes_test _ctypes/_ctypes_test.c',
            '_testbuffer _testbuffer.c',
            '_testimportmultiple _testimportmultiple.c',
            '_crypt _cryptmodule.c',  # not on android so disabling here too
    ]:
        txt = efrotools.replace_one(txt, line, '#' + line)

    if ENABLE_OPENSSL:

        # _md5 and _sha modules are normally only built if the
        # system does not have the OpenSSL libs containing an optimized
        # version.
        # Note: seems we still need sha3 or we get errors
        for line in [
                '_md5 md5module.c',
                '_sha1 sha1module.c',
                # '_sha3 _sha3/sha3module.c',
                '_sha256 sha256module.c',
                '_sha512 sha512module.c',
        ]:
            txt = efrotools.replace_one(txt, line, '#' + line)
    else:
        txt = efrotools.replace_one(txt, '_ssl _ssl.c', '#_ssl _ssl.c')
    efrotools.writefile('patch/Python/Setup.embedded', txt)

    txt = efrotools.readfile('Makefile')

    # Fix a bug where spaces in PATH cause errors (darn you vmware fusion!)
    txt = efrotools.replace_one(
        txt, '&& PATH=$(PROJECT_DIR)/$(PYTHON_DIR-macOS)/dist/bin:$(PATH) .',
        '&& PATH="$(PROJECT_DIR)/$(PYTHON_DIR-macOS)/dist/bin:$(PATH)" .')
    txt = efrotools.replace_one(
        txt, '&& PATH=$(PROJECT_DIR)/$(PYTHON_DIR-macOS)/dist/bin:$(PATH) m',
        '&& PATH="$(PROJECT_DIR)/$(PYTHON_DIR-macOS)/dist/bin:$(PATH)" m')

    # Remove makefile dependencies so we don't build the
    # libs we're not using.
    srctxt = '$$(PYTHON_DIR-$1)/dist/lib/libpython$(PYTHON_VER)m.a: '
    txt = efrotools.replace_one(
        txt, srctxt, '$$(PYTHON_DIR-$1)/dist/lib/libpython$(PYTHON_VER)m.a: ' +
        ('build/$2/Support/OpenSSL ' if ENABLE_OPENSSL else '') +
        'build/$2/Support/XZ $$(PYTHON_DIR-$1)/Makefile\n#' + srctxt)
    srctxt = ('dist/Python-$(PYTHON_VER)-$1-support.'
              'b$(BUILD_NUMBER).tar.gz: ')
    txt = efrotools.replace_one(
        txt, srctxt,
        'dist/Python-$(PYTHON_VER)-$1-support.b$(BUILD_NUMBER).tar.gz:'
        ' $$(PYTHON_FRAMEWORK-$1)\n#' + srctxt)

    # Turn doc strings on; looks like it only adds a few hundred k.
    txt = txt.replace('--without-doc-strings', '--with-doc-strings')

    # We're currently aiming at 10.13+ on mac
    # (see issue with utimensat and futimens).
    txt = efrotools.replace_one(txt, 'MACOSX_DEPLOYMENT_TARGET=10.8',
                                'MACOSX_DEPLOYMENT_TARGET=10.13')
    # And equivalent iOS (11+).
    txt = efrotools.replace_one(txt, 'CFLAGS-iOS=-mios-version-min=7.0',
                                'CFLAGS-iOS=-mios-version-min=11.0')
    # Ditto for tvOS.
    txt = efrotools.replace_one(txt, 'CFLAGS-tvOS=-mtvos-version-min=9.0',
                                'CFLAGS-tvOS=-mtvos-version-min=11.0')

    if debug:

        # Add debug build flag
        # (Currently expect to find 2 instances of this).
        dline = '--with-doc-strings --enable-ipv6 --without-ensurepip'
        splitlen = len(txt.split(dline))
        if splitlen != 3:
            raise Exception("unexpected configure lines")
        txt = txt.replace(dline, '--with-pydebug ' + dline)

        # Debug has a different name.
        # (Currently expect to replace 13 instances of this).
        dline = 'python$(PYTHON_VER)m'
        splitlen = len(txt.split(dline))
        if splitlen != 14:
            raise Exception("unexpected configure lines")
        txt = txt.replace(dline, 'python$(PYTHON_VER)dm')

    efrotools.writefile('Makefile', txt)

    # Ok; let 'er rip.
    # (we run these in parallel so limit to 1 job a piece;
    # otherwise they inherit the -j12 or whatever from the top level)
    # (also this build seems to fail with multiple threads)
    efrotools.run('make -j1 ' + {
        'mac': 'Python-macOS',
        'ios': 'Python-iOS',
        'tvos': 'Python-tvOS'
    }[arch])
    print('python build complete! (apple/' + arch + ')')


def build_android(rootdir: str, arch: str, debug: bool = False) -> None:
    """Run a build for android with the given architecture.

    (can be arm, arm64, x86, or x86_64)
    """
    import subprocess
    builddir = 'build/python_android_' + arch + ('_debug' if debug else '')
    efrotools.run('rm -rf "' + builddir + '"')
    efrotools.run('mkdir -p build')
    efrotools.run('git clone '
                  'git@github.com:yan12125/python3-android.git "' + builddir +
                  '"')
    os.chdir(builddir)

    # Commit from Dec 6th, 2018.  Looks like right after this one the repo
    # switched to ndk r19 beta 2 and now seems to require r19, so we can
    # try switching back to master one r19 comes down the pipe.
    # noinspection PyUnreachableCode
    if False:  # pylint: disable=using-constant-test
        efrotools.run('git checkout eb587c52db349fecfc4666c6bf7e077352513035')

    # Commit from ~March 14 2019.  Looks like right after this the project
    # switched to compiling python as a shared library which would be a pretty
    # big change.
    # noinspection PyUnreachableCode
    if False:  # pylint: disable=using-constant-test
        efrotools.run('git checkout b3024bf350fd5134542ee974a9a28921a687a8a0')
    ftxt = efrotools.readfile('pybuild/env.py')

    # Set the packages we build.
    ftxt = efrotools.replace_one(
        ftxt, 'packages = (', "packages = ('zlib', 'sqlite', 'xz'," +
        (" 'openssl'" if ENABLE_OPENSSL else "") + ")\n# packages = (")

    # Don't wanna bother with gpg signing stuff.
    ftxt = efrotools.replace_one(ftxt, 'verify_source = True',
                                 'verify_source = False')

    # Sub in the min api level we're targeting.
    ftxt = efrotools.replace_one(ftxt, 'android_api_level = 21',
                                 'android_api_level = 21')
    ftxt = efrotools.replace_one(ftxt, "target_arch = 'arm'",
                                 "target_arch = '" + arch + "'")
    efrotools.writefile('pybuild/env.py', ftxt)
    ftxt = efrotools.readfile('Makefile')

    # This needs to be python3 for us.
    ftxt = efrotools.replace_one(ftxt, 'PYTHON?=python\n', 'PYTHON?=python3\n')
    efrotools.writefile('Makefile', ftxt)
    ftxt = efrotools.readfile('pybuild/packages/python.py')

    # We currently build as a static lib.
    ftxt = efrotools.replace_one(ftxt, "            '--enable-shared',\n", "")
    ftxt = efrotools.replace_one(
        ftxt, "super().__init__('https://github.com/python/cpython/')",
        "super().__init__('https://github.com/python/cpython/', branch='3.7')")

    # Turn ipv6 on (curious why its turned off here?...)
    ftxt = efrotools.replace_one(ftxt, "'--disable-ipv6',", "'--enable-ipv6',")
    if debug:
        ftxt = efrotools.replace_one(ftxt, "'./configure',",
                                     "'./configure', '--with-pydebug',")

    # We don't use this stuff so lets strip it out to simplify.
    ftxt = efrotools.replace_one(ftxt, "'--with-system-ffi',", "")
    ftxt = efrotools.replace_one(ftxt, "'--with-system-expat',", "")
    ftxt = efrotools.replace_one(ftxt, "'--without-ensurepip',", "")

    # This builds all modules as dynamic libs, but we want to be consistent
    # with our other embedded builds and just static-build the ones we
    # need... so to change that we'll need to add a hook for ourself after
    # python is downloaded but before it is built so we can muck with it.
    ftxt = efrotools.replace_one(
        ftxt, '    def prepare(self):',
        '    def prepare(self):\n        import os\n'
        '        if os.system(\'"' + rootdir +
        '/tools/snippets" python_android_patch "' + os.getcwd() +
        '"\') != 0: raise Exception("patch apply failed")')

    efrotools.writefile('pybuild/packages/python.py', ftxt)

    # Set this to a particular cpython commit to target exact releases from git
    commit = 'e09359112e250268eca209355abeb17abf822486'  # 3.7.4 release
    if commit is not None:
        ftxt = efrotools.readfile('pybuild/source.py')

        # Check out a particular commit right after the clone.
        ftxt = efrotools.replace_one(
            ftxt,
            "'git', 'clone', '-b', self.branch, self.source_url, self.dest])",
            "'git', 'clone', '-b', self.branch, self.source_url, self.dest])\n"
            "        run_in_dir(['git', 'checkout', '" + commit +
            "'], self.source_dir)")
        efrotools.writefile('pybuild/source.py', ftxt)
    ftxt = efrotools.readfile('pybuild/util.py')

    # Still don't wanna bother with gpg signing stuff.
    ftxt = efrotools.replace_one(
        ftxt, 'def gpg_verify_file(sig_filename, filename, validpgpkeys):\n',
        'def gpg_verify_file(sig_filename, filename, validpgpkeys):\n'
        '    print("gpg-verify disabled by ericf")\n'
        '    return\n')
    efrotools.writefile('pybuild/util.py', ftxt)

    # These builds require ANDROID_NDK to be set, so make sure that's
    # the case.
    os.environ['ANDROID_NDK'] = subprocess.check_output(
        [rootdir + '/tools/android_sdk_utils',
         'get-ndk-path']).decode().strip()

    # Ok, let 'er rip
    # (we often run these builds in parallel so limit to 1 job a piece;
    # otherwise they each inherit the -j12 or whatever from the top level).
    efrotools.run('make -j1')
    print('python build complete! (android/' + arch + ')')


def android_patch() -> None:
    """Run necessary patches on an android archive before building."""
    fname = 'src/cpython/Modules/Setup.dist'
    txt = efrotools.readfile(fname)

    # Need to switch some flags on this one.
    txt = efrotools.replace_one(txt, '#zlib zlibmodule.c',
                                'zlib zlibmodule.c -lz\n#zlib zlibmodule.c')
    # Just turn all these on.
    for enable in [
            '#array arraymodule.c', '#cmath cmathmodule.c _math.c',
            '#math mathmodule.c', '#_contextvars _contextvarsmodule.c',
            '#_struct _struct.c', '#_weakref _weakref.c',
            '#_testcapi _testcapimodule.c', '#_random _randommodule.c',
            '#_elementtree -I', '#_pickle _pickle.c',
            '#_datetime _datetimemodule.c', '#_bisect _bisectmodule.c',
            '#_heapq _heapqmodule.c', '#_asyncio _asynciomodule.c',
            '#unicodedata unicodedata.c', '#fcntl fcntlmodule.c',
            '#select selectmodule.c', '#_csv _csv.c',
            '#_socket socketmodule.c', '#_blake2 _blake2/blake2module.c',
            '#binascii binascii.c', '#_posixsubprocess _posixsubprocess.c',
            '#_sha3 _sha3/sha3module.c'
    ]:
        txt = efrotools.replace_one(txt, enable, enable[1:])
    if ENABLE_OPENSSL:
        txt = efrotools.replace_one(txt, '#_ssl _ssl.c \\',
                                    '_ssl _ssl.c -DUSE_SSL -lssl -lcrypto')
    else:
        # Note that the _md5 and _sha modules are normally only built if the
        # system does not have the OpenSSL libs containing an optimized
        # version.
        for enable in [
                '#_md5 md5module.c', '#_sha1 sha1module.c',
                '#_sha256 sha256module.c', '#_sha512 sha512module.c'
        ]:
            txt = efrotools.replace_one(txt, enable, enable[1:])

    # Turn this off (its just an example module).
    txt = efrotools.replace_one(txt, 'xxsubtype xxsubtype.c',
                                '#xxsubtype xxsubtype.c')

    # For whatever reason this stuff isn't in there at all; add it.
    txt += '\n_json _json.c\n'

    txt += '\n_lzma _lzmamodule.c -llzma\n'

    txt += ('\n_sqlite3 -I$(srcdir)/Modules/_sqlite'
            ' -DMODULE_NAME=\'\\"sqlite3\\"\' -DSQLITE_OMIT_LOAD_EXTENSION'
            ' -lsqlite3 \\\n'
            '    _sqlite/cache.c \\\n'
            '    _sqlite/connection.c \\\n'
            '    _sqlite/cursor.c \\\n'
            '    _sqlite/microprotocols.c \\\n'
            '    _sqlite/module.c \\\n'
            '    _sqlite/prepare_protocol.c \\\n'
            '    _sqlite/row.c \\\n'
            '    _sqlite/statement.c \\\n'
            '    _sqlite/util.c\n')

    if ENABLE_OPENSSL:
        txt += '\n\n_hashlib _hashopenssl.c -DUSE_SSL -lssl -lcrypto\n'

    txt += '\n\n*disabled*\n_ctypes _crypt grp'

    efrotools.writefile(fname, txt)

    # Ok, this is weird.
    # When applying the module Setup, python looks for any line containing *=*
    # and interprets the whole thing a a global define?...
    # This breaks things for our static sqlite compile above.
    # The check used to look for [A-Z]*=* which didn't break, so let' just
    # change it back to that for now.
    fname = 'src/cpython/Modules/makesetup'
    txt = efrotools.readfile(fname)
    txt = efrotools.replace_one(
        txt, '		*=*)	DEFS="$line$NL$DEFS"; continue;;',
        '		[A-Z]*=*)	DEFS="$line$NL$DEFS"; continue;;')
    efrotools.writefile(fname, txt)

    print("APPLIED EFROTOOLS ANDROID BUILD PATCHES.")


def gather() -> None:
    """Gather per-platform python headers, libs, and modules together.

    This assumes all embeddable py builds have been run successfully,
    and that PROJROOT is the cwd.
    """
    # pylint: disable=too-many-locals

    # First off, clear out any existing output.
    existing_dirs = [
        os.path.join('src/external', d) for d in os.listdir('src/external')
        if d.startswith('python-') and d != 'python-notes.txt'
    ]
    existing_dirs += [
        os.path.join('assets/src', d) for d in os.listdir('assets/src')
        if d.startswith('pylib-')
    ]
    for existing_dir in existing_dirs:
        efrotools.run('rm -rf "' + existing_dir + '"')

    # Build our set of site-packages that we'll bundle in addition
    # to the base system.
    # FIXME: Should we perhaps make this part more explicit?..
    #  we might get unexpected changes sneaking if we're just
    #  pulling from installed python. But then again, anytime we're doing
    #  a new python build/gather we should expect *some* changes even if
    #  only at the build-system level since we pull some of that directly
    #  from latest git stuff.
    efrotools.run('mkdir -p "assets/src/pylib-site-packages"')
    efrotools.run('cp "/usr/local/lib/python' + PYTHON_VERSION_MAJOR +
                  '/site-packages/typing_extensions.py"'
                  ' "assets/src/pylib-site-packages/"')

    for buildtype in ['debug', 'release']:
        debug = buildtype == 'debug'
        bsuffix = '_debug' if buildtype == 'debug' else ''
        bsuffix2 = '-debug' if buildtype == 'debug' else ''

        libname = 'python' + PYTHON_VERSION_MAJOR + ('dm' if debug else 'm')

        bases = {
            'mac':
                f'build/python_apple_mac{bsuffix}/build/macOS',
            'ios':
                f'build/python_apple_ios{bsuffix}/build/iOS',
            'tvos':
                f'build/python_apple_tvos{bsuffix}/build/tvOS',
            'android_arm':
                f'build/python_android_arm{bsuffix}/build/sysroot',
            'android_arm64':
                f'build/python_android_arm64{bsuffix}/build/sysroot',
            'android_x86':
                f'build/python_android_x86{bsuffix}/build/sysroot',
            'android_x86_64':
                f'build/python_android_x86_64{bsuffix}/build/sysroot'
        }

        # Note: only need pylib for the first in each group.
        builds: List[Dict[str, Any]] = [{
            'name':
                'macos',
            'group':
                'apple',
            'headers':
                bases['mac'] + '/Support/Python/Headers',
            'libs': [
                bases['mac'] + '/Support/Python/libPython.a',
                bases['mac'] + '/Support/OpenSSL/libOpenSSL.a',
                bases['mac'] + '/Support/XZ/libxz.a'
            ],
            'pylib':
                (bases['mac'] + '/python/lib/python' + PYTHON_VERSION_MAJOR),
        }, {
            'name':
                'ios',
            'group':
                'apple',
            'headers':
                bases['ios'] + '/Support/Python/Headers',
            'libs': [
                bases['ios'] + '/Support/Python/libPython.a',
                bases['ios'] + '/Support/OpenSSL/libOpenSSL.a',
                bases['ios'] + '/Support/XZ/libxz.a'
            ],
        }, {
            'name':
                'tvos',
            'group':
                'apple',
            'headers':
                bases['tvos'] + '/Support/Python/Headers',
            'libs': [
                bases['tvos'] + '/Support/Python/libPython.a',
                bases['tvos'] + '/Support/OpenSSL/libOpenSSL.a',
                bases['tvos'] + '/Support/XZ/libxz.a'
            ],
        }, {
            'name':
                'android_arm',
            'group':
                'android',
            'headers':
                bases['android_arm'] + f'/usr/include/{libname}',
            'libs': [
                bases['android_arm'] + f'/usr/lib/lib{libname}.a',
                bases['android_arm'] + '/usr/lib/libssl.a',
                bases['android_arm'] + '/usr/lib/libcrypto.a',
                bases['android_arm'] + '/usr/lib/liblzma.a',
                bases['android_arm'] + '/usr/lib/libsqlite3.a'
            ],
            'libinst':
                'android_armeabi-v7a',
            'pylib': (bases['android_arm'] + '/usr/lib/python' +
                      PYTHON_VERSION_MAJOR),
        }, {
            'name': 'android_arm64',
            'group': 'android',
            'headers': bases['android_arm64'] + f'/usr/include/{libname}',
            'libs': [
                bases['android_arm64'] + f'/usr/lib/lib{libname}.a',
                bases['android_arm64'] + '/usr/lib/libssl.a',
                bases['android_arm64'] + '/usr/lib/libcrypto.a',
                bases['android_arm64'] + '/usr/lib/liblzma.a',
                bases['android_arm64'] + '/usr/lib/libsqlite3.a'
            ],
            'libinst': 'android_arm64-v8a',
        }, {
            'name': 'android_x86',
            'group': 'android',
            'headers': bases['android_x86'] + f'/usr/include/{libname}',
            'libs': [
                bases['android_x86'] + f'/usr/lib/lib{libname}.a',
                bases['android_x86'] + '/usr/lib/libssl.a',
                bases['android_x86'] + '/usr/lib/libcrypto.a',
                bases['android_x86'] + '/usr/lib/liblzma.a',
                bases['android_x86'] + '/usr/lib/libsqlite3.a'
            ],
            'libinst': 'android_x86',
        }, {
            'name': 'android_x86_64',
            'group': 'android',
            'headers': bases['android_x86_64'] + f'/usr/include/{libname}',
            'libs': [
                bases['android_x86_64'] + f'/usr/lib/lib{libname}.a',
                bases['android_x86_64'] + '/usr/lib/libssl.a',
                bases['android_x86_64'] + '/usr/lib/libcrypto.a',
                bases['android_x86_64'] + '/usr/lib/liblzma.a',
                bases['android_x86_64'] + '/usr/lib/libsqlite3.a'
            ],
            'libinst': 'android_x86_64',
        }]

        for build in builds:

            grp = build['group']
            builddir = f'src/external/python-{grp}{bsuffix2}'
            header_dst = os.path.join(builddir, 'include')
            lib_dst = os.path.join(builddir, 'lib')
            assets_src_dst = f'assets/src/pylib-{grp}'

            # Do some setup only once per group.
            if not os.path.exists(builddir):
                efrotools.run('mkdir -p "' + builddir + '"')
                efrotools.run('mkdir -p "' + lib_dst + '"')

                # Only pull modules into game assets on release pass
                if not debug:
                    # Copy system modules into the src assets
                    # dir for this group
                    efrotools.run('mkdir -p "' + assets_src_dst + '"')
                    efrotools.run(
                        'rsync --recursive --include "*.py"'
                        ' --exclude __pycache__ --include "*/" --exclude "*" "'
                        + build['pylib'] + '/" "' + assets_src_dst + '"')

                    # Prune a bunch of modules we don't need to cut
                    # down on size.
                    prune = [
                        'config-*', 'idlelib', 'lib-dynload', 'lib2to3',
                        'multiprocessing', 'pydoc_data', 'site-packages',
                        'ensurepip', 'tkinter', 'wsgiref', 'distutils',
                        'turtle.py', 'turtledemo', 'test', 'sqlite3/test',
                        'unittest', 'dbm', 'venv', 'ctypes/test', 'imaplib.py'
                    ]
                    efrotools.run('cd "' + assets_src_dst + '" && rm -rf ' +
                                  ' '.join(prune))

                # Copy in a base set of headers (everything in a group should
                # be using the same headers)
                efrotools.run(f'cp -r "{build["headers"]}" "{header_dst}"')

                # Clear whatever pyconfigs came across; we'll build our own
                # universal one below.
                efrotools.run('rm ' + header_dst + '/pyconfig*')

                # Write a master pyconfig header that reroutes to each
                # platform's actual header.
                with open(header_dst + '/pyconfig.h', 'w') as hfile:
                    hfile.write(
                        '#if BA_OSTYPE_MACOS\n'
                        '#include "pyconfig-macos.h"\n\n'
                        '#elif BA_OSTYPE_IOS\n'
                        '#include "pyconfig-ios.h"\n\n'
                        '#elif BA_OSTYPE_TVOS\n'
                        '#include "pyconfig-tvos.h"\n\n'
                        '#elif BA_OSTYPE_ANDROID and defined(__arm__)\n'
                        '#include "pyconfig-android_arm.h"\n\n'
                        '#elif BA_OSTYPE_ANDROID and defined(__aarch64__)\n'
                        '#include "pyconfig-android_arm64.h"\n\n'
                        '#elif BA_OSTYPE_ANDROID and defined(__i386__)\n'
                        '#include "pyconfig-android_x86.h"\n\n'
                        '#elif BA_OSTYPE_ANDROID and defined(__x86_64__)\n'
                        '#include "pyconfig-android_x86_64.h"\n\n'
                        '#else\n'
                        '#error unknown platform\n\n'
                        '#endif\n')

            # Now copy each build's config headers in with unique names.
            cfgs = [
                f for f in os.listdir(build['headers'])
                if f.startswith('pyconfig')
            ]

            # Copy config headers to their filtered names.
            for cfg in cfgs:
                out = cfg.replace('pyconfig', 'pyconfig-' + build['name'])
                if cfg == 'pyconfig.h':

                    # For platform's root pyconfig.h we need to filter
                    # contents too (those headers can themselves include
                    # others; ios for instance points to a arm64 and a
                    # x86_64 variant).
                    contents = efrotools.readfile(build['headers'] + '/' + cfg)
                    contents = contents.replace('pyconfig',
                                                'pyconfig-' + build['name'])
                    efrotools.writefile(header_dst + '/' + out, contents)
                else:
                    # other configs we just rename
                    efrotools.run('cp "' + build['headers'] + '/' + cfg +
                                  '" "' + header_dst + '/' + out + '"')

            # Copy in libs. If the lib gave a specific install name,
            # use that; otherwise use name.
            targetdir = lib_dst + '/' + build.get('libinst', build['name'])
            efrotools.run('rm -rf "' + targetdir + '"')
            efrotools.run('mkdir -p "' + targetdir + '"')
            for lib in build['libs']:
                efrotools.run('cp "' + lib + '" "' + targetdir + '"')

    print('Great success!')
