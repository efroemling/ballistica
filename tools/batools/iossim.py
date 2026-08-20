# Released under the MIT License. See LICENSE for details.
"""Build a Ballistica Xcode target for a simulator and run it there.

Powers ``make ios`` / ``make tvos`` -- the simulator analogue of ``make mac``.
Unlike a macOS app (a runnable binary we can ``subprocess.run`` directly), an
iOS/tvOS ``.app`` must be installed into a Simulator and launched via
``simctl``. This handles the whole lifecycle: build-for-sim, pick + boot a
device (foolproof defaults), install, launch, and stream the engine's os_log.
"""

import os
import json
import subprocess
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import Any

# The engine's os_log subsystem (see EmitPlatformLog on Apple). Overridable via
# env for spinoffs.
DEFAULT_LOG_SUBSYSTEM = 'net.froemling.ballistica'

# Per-platform Simulator knobs.
_PLATFORM_INFO = {
    'ios': {
        'destination': 'generic/platform=iOS Simulator',
        'runtime_tag': '.iOS-',
        'preferred_name_prefix': 'iPhone',
    },
    'tvos': {
        'destination': 'generic/platform=tvOS Simulator',
        'runtime_tag': '.tvOS-',
        'preferred_name_prefix': 'Apple TV',
    },
}


def run(
    *, project: str, scheme: str, configuration: str, platform: str
) -> None:
    """Build the scheme for the simulator, then install + launch + log it."""
    app_path, bundle_id = build_for_sim(
        project=project,
        scheme=scheme,
        configuration=configuration,
        platform=platform,
    )

    udid = ensure_booted_device(platform)
    print(
        f'{Clr.BLU}Installing {os.path.basename(app_path)}...{Clr.RST}',
        flush=True,
    )
    _simctl(['install', udid, app_path])
    print(f'{Clr.BLU}Launching {bundle_id}...{Clr.RST}', flush=True)
    _simctl(['launch', udid, bundle_id])

    subsystem = os.environ.get('IOS_LOG_SUBSYSTEM', DEFAULT_LOG_SUBSYSTEM)
    print(
        f'{Clr.GRN}Running. Streaming os_log (subsystem={subsystem}); '
        f'Ctrl-C to detach (app keeps running).{Clr.RST}',
        flush=True,
    )
    stream_log(udid, subsystem)


def build_for_sim(
    *, project: str, scheme: str, configuration: str, platform: str
) -> tuple[str, str]:
    """Build the scheme for the simulator.

    Returns ``(app_path, bundle_id)`` for the built product. Also used
    by external drivers (e.g. test_game_run's ios leg) that manage
    their own install/launch lifecycle.
    """
    if platform not in _PLATFORM_INFO:
        raise CleanError(f"Unknown platform '{platform}'.")
    info = _PLATFORM_INFO[platform]

    # Resolve product (.app) + bundle-id, then build.
    settings = _build_settings(project, scheme, configuration, info)
    app_path = os.path.join(
        settings['TARGET_BUILD_DIR'], settings['FULL_PRODUCT_NAME']
    )
    bundle_id = settings['PRODUCT_BUNDLE_IDENTIFIER']

    print(
        f'{Clr.BLU}Building {scheme} ({configuration}) for the '
        f'{platform} simulator...{Clr.RST}',
        flush=True,
    )
    _build(project, scheme, configuration, info)
    return app_path, bundle_id


def ensure_booted_device(platform: str) -> str:
    """Return a booted sim udid for a platform, picking/booting if needed.

    See ``_ensure_booted_device`` for the selection rules.
    """
    if platform not in _PLATFORM_INFO:
        raise CleanError(f"Unknown platform '{platform}'.")
    return _ensure_booted_device(platform, _PLATFORM_INFO[platform])


def install_app(udid: str, app_path: str) -> None:
    """Install a built .app onto a booted sim."""
    _simctl(['install', udid, app_path])


def stream_log(udid: str, subsystem: str) -> None:
    """Stream the engine's os_log for a booted sim until interrupted."""
    try:
        subprocess.run(
            [
                'xcrun',
                'simctl',
                'spawn',
                udid,
                'log',
                'stream',
                '--level',
                'debug',
                '--predicate',
                f'subsystem == "{subsystem}"',
            ],
            check=False,
        )
    except KeyboardInterrupt:
        pass


def _xcodebuild_base(
    project: str, scheme: str, configuration: str, info: dict[str, str]
) -> list[str]:
    return [
        'xcodebuild',
        '-project',
        project,
        '-scheme',
        scheme,
        '-configuration',
        configuration,
        '-destination',
        info['destination'],
        'CODE_SIGNING_ALLOWED=NO',
    ]


def _build_settings(
    project: str, scheme: str, configuration: str, info: dict[str, str]
) -> dict[str, str]:
    """Resolve build settings (product path, bundle id) for the sim build."""
    out = subprocess.run(
        _xcodebuild_base(project, scheme, configuration, info)
        + ['-showBuildSettings', '-json'],
        capture_output=True,
        check=True,
    ).stdout.decode()
    # simctl/xcodebuild json is untyped third-party output, hence Any.
    data: list[dict[str, Any]] = json.loads(out)
    # -showBuildSettings -json is a list of {target, action, buildSettings}.
    for entry in data:
        bsraw = entry.get('buildSettings', {})
        if all(
            k in bsraw
            for k in (
                'TARGET_BUILD_DIR',
                'FULL_PRODUCT_NAME',
                'PRODUCT_BUNDLE_IDENTIFIER',
            )
        ):
            return {k: str(v) for k, v in bsraw.items()}
    raise CleanError('Unable to resolve build settings for the sim build.')


def _build(
    project: str, scheme: str, configuration: str, info: dict[str, str]
) -> None:
    subprocess.run(
        _xcodebuild_base(project, scheme, configuration, info)
        + ['-quiet', 'build'],
        check=True,
    )


def _runtime_version(runtime_id: str) -> tuple[int, ...]:
    """Parse e.g. '...SimRuntime.iOS-26-5' -> (26, 5) for sorting."""
    tail = runtime_id.rsplit('.', 1)[-1]  # 'iOS-26-5'
    parts = tail.split('-')[1:]  # ['26', '5']
    return tuple(int(p) for p in parts if p.isdigit())


def _simulator_current_udid() -> str | None:
    """The device the Simulator app currently targets (its last-used one).

    The Simulator app auto-boots this on launch, so preferring it keeps us
    from spawning a second window next to the one it opens.
    """
    out = subprocess.run(
        ['defaults', 'read', 'com.apple.iphonesimulator', 'CurrentDeviceUDID'],
        capture_output=True,
        check=False,
    )
    if out.returncode != 0:
        return None
    return out.stdout.decode().strip() or None


def _ensure_booted_device(platform: str, info: dict[str, str]) -> str:
    """Return a booted sim udid, picking + booting one if needed.

    Selection order: an IOS_SIM_DEVICE override, else any already-booted
    device of this platform, else the newest available device (preferring a
    standard device for the platform).
    """
    out = subprocess.run(
        ['xcrun', 'simctl', 'list', 'devices', 'available', '--json'],
        capture_output=True,
        check=True,
    ).stdout.decode()
    # Untyped third-party json, hence Any.
    devices_by_runtime: dict[str, list[dict[str, Any]]] = json.loads(out)[
        'devices'
    ]

    # Flatten this platform's devices, tagging each with its runtime version.
    tag = info['runtime_tag']
    candidates: list[tuple[tuple[int, ...], dict[str, Any]]] = []
    booted: list[dict[str, Any]] = []
    for runtime_id, devices in devices_by_runtime.items():
        if tag not in runtime_id:
            continue
        ver = _runtime_version(runtime_id)
        for dev in devices:
            candidates.append((ver, dev))
            if dev.get('state') == 'Booted':
                booted.append(dev)

    override = os.environ.get('IOS_SIM_DEVICE', '').strip()
    if override:
        for _ver, dev in candidates:
            if override in (dev.get('name'), dev.get('udid')):
                return _boot(dev)
        raise CleanError(
            f"IOS_SIM_DEVICE '{override}' not found among available"
            f' {platform} simulators.'
        )

    # Reuse an already-booted device rather than spinning up a new one (don't
    # disrupt a running sim).
    if booted:
        return _boot(booted[0])

    # Nothing booted: prefer the device the Simulator app will auto-open on
    # launch (its CurrentDeviceUDID / last session), so our pick matches its
    # restored window instead of spawning a second one alongside it.
    current = _simulator_current_udid()
    if current:
        for _ver, dev in candidates:
            if dev.get('udid') == current:
                return _boot(dev)

    if not candidates:
        raise CleanError(
            f'No available {platform} simulators found. Install a'
            f' {platform} runtime via Xcode and retry.'
        )

    # Newest runtime first; within that, prefer a standard device by name.
    prefix = info['preferred_name_prefix']
    candidates.sort(
        key=lambda c: (c[0], str(c[1].get('name', '')).startswith(prefix)),
        reverse=True,
    )
    return _boot(candidates[0][1])


def _boot(dev: dict[str, Any]) -> str:
    """Boot a device (if needed), show the Simulator UI, wait until ready."""
    udid = str(dev['udid'])
    if dev.get('state') != 'Booted':
        name = dev.get('name', udid)
        print(
            f'{Clr.BLU}Booting simulator {name}...{Clr.RST}',
            flush=True,
        )
    # Boot (if needed) and wait until fully ready BEFORE bringing up the
    # Simulator app. Opening the app first makes it race to auto-boot its
    # current device at the same moment we boot that same device, and the
    # losing boot pops an 'Unable to boot device in current state: Booted'
    # dialog. Booting to completion up front means the app just attaches to a
    # settled device with no competing boot. We use 'bootstatus -b' (boot if
    # needed, then wait) rather than 'simctl boot': it's a clean no-op on an
    # already-booted device, whereas 'simctl boot' prints that same scary
    # 'Unable to boot...: Booted' error to stderr on a re-run.
    subprocess.run(['xcrun', 'simctl', 'bootstatus', udid, '-b'], check=False)
    # Device is settled now, so the Simulator window just attaches to it.
    subprocess.run(['open', '-a', 'Simulator'], check=False)
    return udid


def _simctl(args: list[str]) -> None:
    subprocess.run(['xcrun', 'simctl'] + args, check=True)
