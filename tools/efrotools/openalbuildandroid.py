# Released under the MIT License. See LICENSE for details.
#
"""Build OpenAL Soft (+ Oboe) static libs for Android.

Cross-compiles OpenAL Soft as a static ``libopenal.a`` (plus its Oboe backend
dependency ``liboboe.a``) for each Android ABI (armeabi-v7a / arm64-v8a / x86 /
x86_64), in debug and release, using the Android NDK's cmake toolchain.
``gather`` then installs the results into
``src/external/openal-android/{lib,include}``.

**Build host:** runs *locally* wherever the Android NDK is installed (resolved
via ``android_sdk_utils get-ndk-path``). There is no cloud build+gather target;
CI builds individual ABIs on linbeast purely as a canary (no gather).

**Driving it:** ``make openal-android-all`` builds all eight ABI/mode combos
(one ``openal_android_build <arch> <mode>`` pcommand each), then ``make
openal-android-gather`` installs them into the source tree. Per-ABI targets
(``openal-android-arm`` etc.) exist too.

**Why tarballs:** sources are fetched as github release *tarballs*, not git
clones, so the build creates no nested ``.git`` -- which keeps it runnable
under restricted filesystem sandboxes (the build sandbox forbids creating or
even deleting ``.git`` dirs). Everything lives under ``build/openal-android/``;
remove that dir to clean up. OpenAL Soft is pinned by ``OPENAL_SOFT_TAG``, Oboe
by ``OBOE_TAG``.

**Local source tweaks** applied after extraction: reroute OpenAL's Android
logging through our ``alcSetCustomAndroidLogger`` hook; add a
``BA_OBOE_USE_OPENSLES`` env-var escape hatch to force Oboe's OpenSL backend;
record the audio api (AAudio or OpenSL ES) each opened Oboe stream actually
got, readable via ``alcGetCustomAndroidOboeAudioApi`` (Oboe drops to OpenSL
on its own when AAudio is missing or fails, and callers need to know);
disable Oboe's open-a-test-stream probe; and demote OpenAL Soft 1.25.2's
``-Werror=function-effects`` to a warning (it trips its own code under newer
clang -- same patch the Apple build applies).
"""

import os
import shutil
import tarfile
import subprocess
import urllib.request

from efro.error import CleanError

# Source versions. Fetched as github release tarballs (see module docstring re:
# why, not clones). Prior OpenAL pins: 1.23.1 / 1.24.2 / 1.24.3 / 1.25.1 (+
# assorted commit SHAs); prior Oboe: 1.9.3 / 1.9.4-ish / 1.10.0.
OPENAL_SOFT_TAG = '1.25.2'
OBOE_TAG = '1.11.0'
OPENAL_SOFT_TARBALL = (
    'https://github.com/kcat/openal-soft/archive/refs/tags/'
    f'{OPENAL_SOFT_TAG}.tar.gz'
)
OBOE_TARBALL = (
    f'https://github.com/google/oboe/archive/refs/tags/{OBOE_TAG}.tar.gz'
)

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
    return f'build/openal-android/{arch}_{mode}'


def _download_cached(url: str) -> str:
    """Download ``url`` once into a shared cache dir; return its path.

    All eight ABI/mode builds use the same two tarballs, so each is
    fetched once and reused. Downloads that come up short (seen through
    proxies, e.g. the Claude sandbox's, which truncate transfers
    intermittently) are retried rather than failing the build.
    """
    import hashlib
    import http.client

    cachedir = 'build/openal-android/_downloads'
    os.makedirs(cachedir, exist_ok=True)
    path = os.path.join(
        cachedir,
        hashlib.sha256(url.encode()).hexdigest()[:16]
        + '_'
        + os.path.basename(url),
    )
    if os.path.exists(path):
        return path
    attempts = 5
    for attempt in range(1, attempts + 1):
        print(f'Downloading {url} ...', flush=True)
        try:
            with urllib.request.urlopen(url) as resp:
                data = resp.read()
        except http.client.IncompleteRead as exc:
            if attempt == attempts:
                raise
            print(
                f'Download came up short ({len(exc.partial)} bytes);'
                f' retrying ({attempt}/{attempts}).',
                flush=True,
            )
            continue
        # Write-then-rename so concurrent builds never see a partial file.
        tmppath = f'{path}.{os.getpid()}.tmp'
        with open(tmppath, 'wb') as outfile:
            outfile.write(data)
        os.replace(tmppath, path)
        break
    return path


def _fetch_tarball(url: str, dest: str) -> None:
    """Download + extract a github release tarball so ``dest`` is its root.

    The tarball's single top-level dir is stripped, leaving ``dest`` as the
    source root (the same layout a clone-into-``dest`` produced). ``dest`` is
    wiped first; no ``.git`` is ever created.
    """
    subprocess.run(['rm', '-rf', dest], check=True)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = f'{dest}.extract'
    subprocess.run(['rm', '-rf', tmp], check=True)
    os.makedirs(tmp)
    tarball = _download_cached(url)
    print(f'Extracting {os.path.basename(url)} ...', flush=True)
    with tarfile.open(tarball, 'r:gz') as tar:
        tar.extractall(tmp, filter='data')
    inner = [
        os.path.join(tmp, n)
        for n in os.listdir(tmp)
        if os.path.isdir(os.path.join(tmp, n))
    ]
    if len(inner) != 1:
        raise CleanError(f'Expected one top-level dir in tarball; got {inner}.')
    os.rename(inner[0], dest)
    shutil.rmtree(tmp)


def build_openal(arch: str, mode: str) -> None:
    """Do the thing."""
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

    # Grab OpenAL Soft.
    builddir = _build_dir(arch, mode)
    _fetch_tarball(OPENAL_SOFT_TARBALL, builddir)

    # Demote OpenAL Soft 1.25.2's -Werror=function-effects to a warning -- it
    # unconditionally promotes that diagnostic and trips its own code under
    # newer clang (same fix the Apple build applies). Safe no-op if absent.
    cmakelists = f'{builddir}/CMakeLists.txt'
    with open(cmakelists, encoding='utf-8') as infile:
        cml_txt = infile.read()
    if '-Werror=function-effects' in cml_txt:
        with open(cmakelists, 'w', encoding='utf-8') as outfile:
            outfile.write(
                cml_txt.replace(
                    '-Werror=function-effects', '-Wfunction-effects'
                )
            )

    # Grab Oboe (OpenAL Soft's low-latency Android backend dependency).
    builddir_oboe = f'{builddir}_oboe'
    _fetch_tarball(OBOE_TARBALL, builddir_oboe)

    if bool(True):
        oboepath = f'{builddir}/alc/backends/oboe.cpp'
        with open(oboepath, encoding='utf-8') as infile:
            txt = infile.read()

        # Also disable opening a stream just to test that it works.
        txt = replace_exact(
            txt,
            (
                '    /* Open a basic output stream,'
                ' just to ensure it can work. */\n'
                '    auto stream = std::shared_ptr<oboe::AudioStream>{};\n'
                '    const auto result = oboe::AudioStreamBuilder{}'
                '.setDirection(oboe::Direction::Output)\n'
                '        ->setPerformanceMode('
                'oboe::PerformanceMode::LowLatency)\n'
                '        ->openStream(stream);\n'
                '    if(result != oboe::Result::OK)\n'
                '        throw al::backend_exception{'
                'al::backend_error::DeviceError,'
                ' "Failed to create stream: {}",\n'
                '            oboe::convertToText(result)};\n'
            ),
            (
                '    /* Open a basic output stream,'
                ' just to ensure it can work. */\n'
                '    // auto stream = std::shared_ptr<oboe::AudioStream>{};\n'
                '    // const auto result = oboe::AudioStreamBuilder{}'
                '.setDirection(oboe::Direction::Output)\n'
                '    //     ->setPerformanceMode('
                'oboe::PerformanceMode::LowLatency)\n'
                '    //     ->openStream(stream);\n'
                '    // if(result != oboe::Result::OK)\n'
                '    //     throw al::backend_exception{'
                'al::backend_error::DeviceError,'
                ' "Failed to create stream: {}",\n'
                '    //         oboe::convertToText(result)};\n'
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
        # Record which audio api the stream actually got. Oboe quietly
        # falls back to OpenSL ES when AAudio is unavailable, and output
        # on OpenSL can't be tagged as game audio, so the app needs to
        # know (see alcGetCustomAndroidOboeAudioApi below).
        txt = replace_exact(
            txt,
            '#include "oboe/Oboe.h"\n',
            (
                '#include "oboe/Oboe.h"\n'
                '\n'
                '#include <atomic>\n'
                'extern std::atomic<int> alcCustomAndroidOboeAudioApi;\n'
            ),
        )
        # (Anchored on the playback stream's open; capture has its own.)
        txt = replace_exact(
            txt,
            (
                '        mStream->getBufferCapacityInFrames()));\n'
                '    TRACE("Got stream with properties:\\n{}",'
                ' oboe::convertToText(mStream.get()));\n'
            ),
            (
                '        mStream->getBufferCapacityInFrames()));\n'
                '    TRACE("Got stream with properties:\\n{}",'
                ' oboe::convertToText(mStream.get()));\n'
                '    alcCustomAndroidOboeAudioApi.store('
                'static_cast<int>(mStream->getAudioApi()));\n'
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
            '    __android_log_print(android_severity(level),'
            ' "openal", "%.*s%s",\n'
            '        al::saturate_cast<int>(prefix.size()),'
            ' prefix.data(), msg.c_str());'
            # '__android_log_print(android_severity(level),'
            # ' "openal", "%.*s%s", al::sizei(prefix),'
            # ' prefix.data(), msg.c_str());'
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
                ' "openal", "%.*s%s",\n'
                '        al::saturate_cast<int>(prefix.size()),'
                ' prefix.data(), msg.c_str());'
                # '    __android_log_print(android_severity(level),'
                # ' "openal", "%.*s%s", al::sizei(prefix),\n'
                # '        prefix.data(), msg.c_str());'
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
            '// Set by the Oboe backend each time it opens a stream.\n'
            'std::atomic<int> alcCustomAndroidOboeAudioApi{0};\n'
            '\n'
            'ALC_API int ALC_APIENTRY'
            ' alcGetCustomAndroidOboeAudioApi() {\n'
            '    return alcCustomAndroidOboeAudioApi.load();\n'
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
            '/* Audio api of the most recently opened Oboe stream, as'
            ' an oboe::AudioApi\n'
            ' * value: 0 = none opened yet, 1 = OpenSL ES, 2 = AAudio. */\n'
            'ALC_API int ALC_APIENTRY'
            ' alcGetCustomAndroidOboeAudioApi(void);\n'
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
            # We only gather libopenal.a; skip the rest. (As of 1.25.2 the
            # examples fail to link with duplicate-symbol errors against the
            # static lib anyway.)
            '-DALSOFT_EXAMPLES=OFF',
            '-DALSOFT_UTILS=OFF',
            '-DALSOFT_TESTS=OFF',
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
