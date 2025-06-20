# Released under the MIT License. See LICENSE for details.
#
"""Functionality to build the openal library."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    pass

# Arch names we take and their official android versions.
ARCHS = {
    'arm': 'armeabi-v7a',
    'arm64': 'arm64-v8a',
    'x86': 'x86',
    'x86_64': 'x86_64',
}

MODES = {'debug', 'release'}


def _build_dir(arch: str, mode: str) -> str:
    """Build dir given an arch and mode."""
    return f'build/openal_build_android_{arch}_{mode}'


def build_openal(arch: str, mode: str) -> None:
    """Do the thing."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals
    from efrotools.util import replace_exact

    if arch not in ARCHS:
        raise CleanError(f"Invalid arch '{arch}'.")

    if mode not in MODES:
        raise CleanError(f"Invalid mode '{mode}'.")

    # If true, we suppress most OpenAL logs to keep logcat tidier.
    reduce_logs = False

    # Inject a function to reroute OpenAL logs to ourself.
    reroute_logs = True

    # Inject an env var to force Oboe to use OpenSL backend.
    opensl_fallback_option = True

    # set_game_usage = True

    # Get ndk path.
    ndk_path = (
        subprocess.run(
            ['tools/pcommand', 'android_sdk_utils', 'get-ndk-path'],
            check=True,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )

    # Grab OpenALSoft
    builddir = _build_dir(arch, mode)
    subprocess.run(['rm', '-rf', builddir], check=True)
    subprocess.run(['mkdir', '-p', os.path.dirname(builddir)], check=True)
    subprocess.run(
        ['git', 'clone', 'https://github.com/kcat/openal-soft.git', builddir],
        check=True,
    )
    subprocess.run(
        [
            'git',
            'checkout',
            # '1.23.1',
            # '1381a951bea78c67281a2e844e6db1dedbd5ed7c',
            # 'bc83c874ff15b29fdab9b6c0bf40b268345b3026',
            # '59c466077fd6f16af64afcc6260bb61aa4e632dc',
            # '1.24.2',
            '1.24.3',
        ],
        check=True,
        cwd=builddir,
    )

    # Grab Oboe
    builddir_oboe = f'{builddir}_oboe'
    subprocess.run(['rm', '-rf', builddir_oboe], check=True)
    subprocess.run(['mkdir', '-p', os.path.dirname(builddir_oboe)], check=True)
    subprocess.run(
        [
            'git',
            'clone',
            'https://github.com/google/oboe',
            builddir_oboe,
        ],
        check=True,
    )
    subprocess.run(
        [
            'git',
            'checkout',
            '1.9.3',
            # '2968fff97730ede42d522ad5afe8b82468a7d1d8',  # Early 1.9.4
        ],
        check=True,
        cwd=builddir_oboe,
    )

    if bool(True):
        oboepath = f'{builddir}/alc/backends/oboe.cpp'
        with open(oboepath, encoding='utf-8') as infile:
            txt = infile.read()

        # Also disable opening a stream just to test that it works.
        txt = replace_exact(
            txt,
            (
                '    /* Open a basic output stream, just to ensure'
                ' it can work. */\n'
                '    oboe::ManagedStream stream;\n'
                '    oboe::Result result{oboe::AudioStreamBuilder{}'
                '.setDirection(oboe::Direction::Output)\n'
                '        ->setPerformanceMode(oboe::PerformanceMode::'
                'LowLatency)\n'
                '        ->openManagedStream(stream)};\n'
                '    if(result != oboe::Result::OK)\n'
                '        throw al::backend_exception{al::backend_error::'
                'DeviceError, "Failed to create stream: {}",\n'
                '            oboe::convertToText(result)};\n'
            ),
            (
                '    /* Open a basic output stream, just to ensure'
                ' it can work. */\n'
                ' // DISABLED BY ERICF\n'
                ' //    oboe::ManagedStream stream;\n'
                ' //   oboe::Result result{oboe::AudioStreamBuilder{}'
                '.setDirection(oboe::Direction::Output)\n'
                ' //       ->setPerformanceMode(oboe::PerformanceMode::'
                'LowLatency)\n'
                ' //       ->openManagedStream(stream)};\n'
                ' //   if(result != oboe::Result::OK)\n'
                ' //       throw al::backend_exception{al::backend_error::'
                'DeviceError, "Failed to create stream: {}",\n'
                ' //           oboe::convertToText(result)};\n'
            ),
        )
        # Add our fallback option.
        if opensl_fallback_option:
            txt = replace_exact(
                txt,
                (
                    '    builder.setPerformanceMode('
                    'oboe::PerformanceMode::LowLatency);\n'
                ),
                (
                    '    builder.setPerformanceMode('
                    'oboe::PerformanceMode::LowLatency);\n'
                    '    if (getenv("BA_OBOE_USE_OPENSLES")) {\n'
                    '        TRACE("BA_OBOE_USE_OPENSLES set;'
                    ' Using OpenSLES\\n");\n'
                    '        builder.setAudioApi(oboe::AudioApi::OpenSLES);\n'
                    '    }\n'
                ),
            )
        # Set game mode.
        # if set_game_usage:
        #     txt = replace_exact(
        #         txt,
        #         (
        #             '    builder.setPerformanceMode('
        #             'oboe::PerformanceMode::LowLatency);\n'
        #         ),
        #         (
        #             '    builder.setPerformanceMode('
        #             'oboe::PerformanceMode::LowLatency);\n'
        #             '    builder.setUsage('
        #             'oboe::Usage::Game);\n'
        #         ),
        #     )

        with open(oboepath, 'w', encoding='utf-8') as outfile:
            outfile.write(txt)

    # By default, openalsoft sends all sorts of log messages to the
    # android log. This is reasonable since its possible to filter by
    # tag/level. However I'd prefer it to send only the ones that it
    # would send to stderr so I don't always have to worry about
    # filtering.
    if reduce_logs or reroute_logs:
        loggingpath = f'{builddir}/core/logging.cpp'
        with open(loggingpath, encoding='utf-8') as infile:
            txt = infile.read()

        logcall = (
            '__android_log_print(android_severity(level),'
            ' "openal", "%.*s%s", al::sizei(prefix),'
            ' prefix.data(), msg.c_str());'
            # '__android_log_print(android_severity(level),'
            #             ' "openal", "%s", str);'
        )
        condition = 'gLogLevel >= level' if reduce_logs else 'true'
        if reroute_logs:
            logcall = (
                'if (alcCustomAndroidLogger) {\n'
                '    alcCustomAndroidLogger(android_severity(level),'
                ' msg.c_str());\n'
                '} else {\n'
                f'  {logcall}\n'
                '}'
            )
        txt = replace_exact(
            txt,
            (
                '    __android_log_print(android_severity(level),'
                ' "openal", "%.*s%s", al::sizei(prefix),\n'
                '        prefix.data(), msg.c_str());'
                # '    __android_log_print(android_severity(level),'
                # ' "openal", "%s", str);'
            ),
            (
                '    // ericf tweak; only send logs that meet some condition.\n'
                f'    if ({condition}) {{\n'
                f'       {logcall}\n'
                '    }'
            ),
        )

        # Note to self: looks like there's actually already a log
        # redirect callback function in OpenALSoft, but it's not an
        # official extension yet and I haven't been able to get it
        # working in its current form. Ideally should adopt that
        # eventually though.
        if reroute_logs:
            txt = replace_exact(
                txt,
                'namespace {\n',
                (
                    'extern void (*alcCustomAndroidLogger)(int, const char*);\n'
                    '\n'
                    'namespace {\n'
                ),
            )
        with open(loggingpath, 'w', encoding='utf-8') as outfile:
            outfile.write(txt)

    # Add a function to set a logging function so we can capture OpenAL
    # logging.
    fpath = f'{builddir}/alc/alc.cpp'
    with open(fpath, encoding='utf-8') as infile:
        txt = infile.read()
    txt = replace_exact(
        txt,
        'ALC_API ALCenum ALC_APIENTRY'
        ' alcGetError(ALCdevice *device) noexcept\n',
        (
            'void (*alcCustomAndroidLogger)(int, const char*) = nullptr;\n'
            '\n'
            'ALC_API void ALC_APIENTRY'
            ' alcSetCustomAndroidLogger(void (*fn)(int, const char*)) {\n'
            '    alcCustomAndroidLogger = fn;\n'
            '}\n'
            '\n'
            'ALC_API ALCenum ALC_APIENTRY'
            ' alcGetError(ALCdevice *device) noexcept\n'
        ),
    )
    with open(fpath, 'w', encoding='utf-8') as outfile:
        outfile.write(txt)

    fpath = f'{builddir}/include/AL/alc.h'
    with open(fpath, encoding='utf-8') as infile:
        txt = infile.read()
    txt = replace_exact(
        txt,
        (
            'ALC_API ALCenum ALC_APIENTRY'
            ' alcGetError(ALCdevice *device) ALC_API_NOEXCEPT;\n'
        ),
        (
            'ALC_API ALCenum ALC_APIENTRY'
            ' alcGetError(ALCdevice *device) ALC_API_NOEXCEPT;\n'
            'ALC_API void ALC_APIENTRY alcSetCustomAndroidLogger('
            'void (*fn)(int, const char*));\n'
        ),
    )
    with open(fpath, 'w', encoding='utf-8') as outfile:
        outfile.write(txt)

    # Let's modify the try/catch around api calls so that we can catch
    # and inspect exceptions thrown by them instead of it just resulting
    # in an insta-terminate.
    #
    # UPDATE: This seems to be gone in latest release.
    if bool(False):
        fpath = f'{builddir}/core/except.h'
        with open(fpath, encoding='utf-8') as infile:
            txt = infile.read()
        txt = replace_exact(
            txt,
            '#define END_API_FUNC catch(...) { std::terminate(); }\n',
            '#define END_API_FUNC\n',
        )
        txt = replace_exact(
            txt, '#define START_API_FUNC try\n', '#define START_API_FUNC\n'
        )
        with open(fpath, 'w', encoding='utf-8') as outfile:
            outfile.write(txt)

    android_platform = 23

    subprocess.run(
        [
            'cmake',
            '.',
            f'-DANDROID_ABI={ARCHS[arch]}',
            f'-DCMAKE_BUILD_TYPE={mode}',
            '-DCMAKE_TOOLCHAIN_FILE='
            f'{ndk_path}/build/cmake/android.toolchain.cmake',
            f'-DANDROID_PLATFORM={android_platform}',
            # Currently fails to compile on new cmakes without this:
            '-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
        ],
        cwd=builddir_oboe,
        check=True,
    )
    subprocess.run(['make'], cwd=builddir_oboe, check=True)

    subprocess.run(
        [
            'cmake',
            '.',
            f'-DANDROID_ABI={ARCHS[arch]}',
            '-DALSOFT_INSTALL=0',  # Prevents odd error.
            '-DALSOFT_REQUIRE_OBOE=1',
            '-DALSOFT_BACKEND_OPENSL=0',
            '-DALSOFT_BACKEND_WAVE=0',
            f'-DCMAKE_BUILD_TYPE={mode}',
            '-DLIBTYPE=STATIC',
            '-DCMAKE_TOOLCHAIN_FILE='
            f'{ndk_path}/build/cmake/android.toolchain.cmake',
            f'-DOBOE_SOURCE={os.path.abspath(builddir_oboe)}',
            f'-DANDROID_PLATFORM={android_platform}',
            # Currently fails to compile on new cmakes without this:
            '-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
        ],
        cwd=builddir,
        check=True,
    )
    subprocess.run(['make'], cwd=builddir, check=True)

    print('SUCCESS!')


def gather() -> None:
    """Gather the things. Assumes all have been built."""

    # Sanity-check; make sure everything appears to be built.
    for arch in ARCHS:
        for mode in MODES:
            builddir = _build_dir(arch, mode)
            libfile = os.path.join(builddir, 'libopenal.a')
            if not os.path.exists(libfile):
                raise CleanError(f"Built lib not found: '{libfile}'.")

    outdir = 'src/external/openal-android'
    subprocess.run(['rm', '-rf', outdir], check=True)

    subprocess.run(['mkdir', '-p', f'{outdir}/include'], check=True)

    builddir = _build_dir('arm', 'debug')  # Doesn't matter here.
    subprocess.run(
        ['cp', '-r', f'{builddir}/include/AL', f'{outdir}/include'],
        check=True,
    )

    for arch, andrarch in ARCHS.items():
        for mode in MODES:
            builddir = _build_dir(arch, mode)
            builddir_oboe = f'{builddir}_oboe'
            installdir = f'{outdir}/lib/{andrarch}_{mode}'
            subprocess.run(['mkdir', '-p', installdir], check=True)
            subprocess.run(
                ['cp', f'{builddir}/libopenal.a', installdir], check=True
            )
            subprocess.run(
                ['cp', f'{builddir_oboe}/liboboe.a', installdir], check=True
            )
    print('OpenAL gather successful!')
