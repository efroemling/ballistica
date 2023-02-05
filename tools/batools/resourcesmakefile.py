# Released under the MIT License. See LICENSE for details.
#
"""Generate our resources Makefile.

(builds things like icons, banners, images, etc.)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
from dataclasses import dataclass

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    pass


@dataclass
class Target:
    """A target to be added to the Makefile."""

    src: list[str]
    dst: str
    cmd: str
    mkdir: bool = False

    def emit(self) -> str:
        """Gen a Makefile target."""
        out: str = self.dst.replace(' ', '\\ ')
        out += (
            ' : '
            + ' '.join(s for s in self.src)
            + (
                ('\n\t@mkdir -p "' + os.path.dirname(self.dst) + '"')
                if self.mkdir
                else ''
            )
            + '\n\t@'
            + self.cmd
            + '\n'
        )
        return out


def _emit_group_build_lines(targets: list[Target], basename: str) -> list[str]:
    """Gen a group build target."""
    del basename  # Unused.
    out: list[str] = []
    if not targets:
        return out
    all_dsts = set()
    for target in targets:
        all_dsts.add(target.dst)
    out.append(
        'resources: \\\n  '
        + ' \\\n  '.join(dst.replace(' ', '\\ ') for dst in sorted(all_dsts))
        + '\n'
    )
    return out


def _emit_group_clean_lines(targets: list[Target], basename: str) -> list[str]:
    """Gen a group clean target."""
    out: list[str] = []
    if not targets:
        return out
    out.append(f'clean: clean-{basename}\n')
    all_dsts = set()
    for target in targets:
        all_dsts.add(target.dst)
    out.append(
        f'clean-{basename}:\n\trm -f '
        + ' \\\n         '.join('"' + dst + '"' for dst in sorted(all_dsts))
        + '\n'
    )
    return out


def _emit_group_efrocache_lines(targets: list[Target]) -> list[str]:
    """Gen a group clean target."""
    out: list[str] = []
    if not targets:
        return out
    all_dsts = set()
    for target in targets:
        # We may need to make pipeline adjustments if/when we get filenames
        # with spaces in them.
        if ' ' in target.dst:
            raise CleanError(
                'FIXME: need to account for spaces in filename'
                f' "{target.dst}".'
            )
        all_dsts.add(target.dst)
    out.append(
        'efrocache-list:\n\t@echo '
        + ' \\\n        '.join('"' + dst + '"' for dst in sorted(all_dsts))
        + '\n'
    )
    out.append('efrocache-build: resources\n')

    return out


# These paths need to be relative to the dir we're writing the Makefile to.
TOOLS_DIR = '../tools'
ROOT_DIR = '..'
RES_DIR = '.'
RESIZE_CMD = os.path.join(TOOLS_DIR, 'pcommand resize_image')


def _add_windows_icon(
    targets: list[Target], generic: bool, oculus: bool, inputs: bool
) -> None:
    sizes = [256, 128, 96, 64, 48, 32, 16]
    all_icons = []
    for size in sizes:
        dst_base = 'build'
        src = os.path.join('src', 'icon', 'icon_clipped.png')
        dst = os.path.join(dst_base, 'win_icon_' + str(size) + '_tmp.png')
        cmd = ' '.join(
            [RESIZE_CMD, str(size), str(size), '"' + src + '"', '"' + dst + '"']
        )
        all_icons.append(dst)
        if inputs:
            targets.append(Target(src=[src], dst=dst, cmd=cmd, mkdir=True))

    # Assemble all the bits we just made into .ico files.
    for path, enable in [
        (
            ROOT_DIR + '/ballisticacore-windows/Generic/BallisticaCore.ico',
            generic,
        ),
        (
            ROOT_DIR + '/ballisticacore-windows/Oculus/BallisticaCore.ico',
            oculus,
        ),
    ]:
        cmd = (
            'convert '
            + ''.join([' "' + f + '"' for f in all_icons])
            + ' "'
            + path
            + '"'
        )
        if enable:
            targets.append(Target(src=all_icons, dst=path, cmd=cmd))


def _add_ios_app_icon(targets: list[Target]) -> None:
    sizes = [
        (20, 2),
        (20, 3),
        (29, 2),
        (29, 3),
        (40, 2),
        (40, 3),
        (60, 2),
        (60, 3),
        (20, 1),
        (29, 1),
        (40, 1),
        (76, 1),
        (76, 2),
        (83.5, 2),
        (1024, 1),
    ]
    for size in sizes:
        res = int(size[0] * size[1])
        src = os.path.join('src', 'icon', 'icon_flat.png')
        dst = os.path.join(
            ROOT_DIR,
            'ballisticacore-xcode',
            'BallisticaCore Shared',
            'Assets.xcassets',
            'AppIcon iOS.appiconset',
            'icon_' + str(size[0]) + 'x' + str(size[1]) + '.png',
        )
        cmd = ' '.join(
            [RESIZE_CMD, str(res), str(res), '"' + src + '"', '"' + dst + '"']
        )
        targets.append(Target(src=[src], dst=dst, cmd=cmd))


def _add_macos_app_icon(targets: list[Target]) -> None:
    sizes = [
        (16, 1),
        (16, 2),
        (32, 1),
        (32, 2),
        (128, 1),
        (128, 2),
        (256, 1),
        (256, 2),
        (512, 1),
        (512, 2),
    ]
    for size in sizes:
        res = int(size[0] * size[1])
        src = os.path.join(RES_DIR, 'src', 'icon', 'icon_clipped.png')
        dst = os.path.join(
            ROOT_DIR,
            'ballisticacore-xcode',
            'BallisticaCore Shared',
            'Assets.xcassets',
            'AppIcon macOS.appiconset',
            'icon_' + str(size[0]) + 'x' + str(size[1]) + '.png',
        )
        cmd = ' '.join(
            [RESIZE_CMD, str(res), str(res), '"' + src + '"', '"' + dst + '"']
        )
        targets.append(Target(src=[src], dst=dst, cmd=cmd))


def _add_android_app_icon(
    targets: list[Target],
    src_name: str = 'icon_clipped.png',
    variant_name: str = 'main',
) -> None:
    sizes = [
        ('mdpi', 48),
        ('hdpi', 72),
        ('xhdpi', 96),
        ('xxhdpi', 144),
        ('xxxhdpi', 192),
    ]
    for size in sizes:
        res = size[1]
        src = os.path.join(RES_DIR, 'src', 'icon', src_name)
        dst = os.path.join(
            ROOT_DIR,
            'ballisticacore-android',
            'BallisticaCore',
            'src',
            variant_name,
            'res',
            'mipmap-' + size[0],
            'ic_launcher.png',
        )
        cmd = ' '.join(
            [RESIZE_CMD, str(res), str(res), '"' + src + '"', '"' + dst + '"']
        )
        targets.append(Target(src=[src], dst=dst, cmd=cmd, mkdir=True))


def _add_android_app_icon_new(
    targets: list[Target],
    src_fg_name: str = 'icon_android_layered_fg.png',
    src_bg_name: str = 'icon_android_layered_bg.png',
    variant_name: str = 'main',
) -> None:
    sizes = [
        ('mdpi', 108),
        ('hdpi', 162),
        ('xhdpi', 216),
        ('xxhdpi', 324),
        ('xxxhdpi', 432),
    ]
    for size in sizes:
        res = size[1]

        # Foreground component.
        src = os.path.join(RES_DIR, 'src', 'icon', src_fg_name)
        dst = os.path.join(
            ROOT_DIR,
            'ballisticacore-android',
            'BallisticaCore',
            'src',
            variant_name,
            'res',
            'mipmap-' + size[0],
            'ic_launcher_foreground.png',
        )
        cmd = ' '.join(
            [RESIZE_CMD, str(res), str(res), '"' + src + '"', '"' + dst + '"']
        )
        targets.append(Target(src=[src], dst=dst, cmd=cmd, mkdir=True))

        # Background component.
        src = os.path.join(RES_DIR, 'src', 'icon', src_bg_name)
        dst = os.path.join(
            ROOT_DIR,
            'ballisticacore-android',
            'BallisticaCore',
            'src',
            variant_name,
            'res',
            'mipmap-' + size[0],
            'ic_launcher_background.png',
        )
        cmd = ' '.join(
            [RESIZE_CMD, str(res), str(res), '"' + src + '"', '"' + dst + '"']
        )
        targets.append(Target(src=[src], dst=dst, cmd=cmd, mkdir=True))


def _add_android_cardboard_app_icon(targets: list[Target]) -> None:
    _add_android_app_icon(
        targets=targets,
        src_name='icon_clipped_vr.png',
        variant_name='cardboard',
    )


def _add_android_cardboard_app_icon_new(targets: list[Target]) -> None:
    _add_android_app_icon_new(
        targets=targets,
        src_fg_name='icon_android_layered_fg_vr.png',
        variant_name='cardboard',
    )


def _add_android_tv_banner(targets: list[Target]) -> None:
    res = (320, 180)
    src = os.path.join(RES_DIR, 'src', 'banner', 'banner_16x9.png')
    dst = os.path.join(
        ROOT_DIR,
        'ballisticacore-android',
        'BallisticaCore',
        'src',
        'main',
        'res',
        'drawable-xhdpi',
        'banner.png',
    )
    cmd = ' '.join(
        [RESIZE_CMD, str(res[0]), str(res[1]), '"' + src + '"', '"' + dst + '"']
    )
    targets.append(Target(src=[src], dst=dst, cmd=cmd, mkdir=True))


def _add_apple_tv_top_shelf(targets: list[Target]) -> None:
    instances = [
        ('24x9', '', '', 1920, 720),
        ('29x9', ' Wide', '_wide', 2320, 720),
    ]
    for instance in instances:
        for scale in [1, 2]:
            res = (instance[3] * scale, instance[4] * scale)
            src = os.path.join(
                RES_DIR, 'src', 'banner', 'banner_' + instance[0] + '.png'
            )
            dst = os.path.join(
                ROOT_DIR,
                'ballisticacore-xcode',
                'BallisticaCore Shared',
                'Assets.xcassets',
                'tvOS App Icon & Top Shelf Image.brandassets',
                'Top Shelf Image' + instance[1] + '.imageset',
                'shelf' + instance[2] + '_' + str(scale) + 'x.png',
            )
            cmd = ' '.join(
                [
                    RESIZE_CMD,
                    str(res[0]),
                    str(res[1]),
                    '"' + src + '"',
                    '"' + dst + '"',
                ]
            )
            targets.append(Target(src=[src], dst=dst, cmd=cmd))


def _add_apple_tv_3d_icon(targets: list[Target]) -> None:
    res = (400, 240)
    for layer in ['Layer1', 'Layer2', 'Layer3', 'Layer4', 'Layer5']:
        for scale in [1, 2]:
            src = os.path.join(
                RES_DIR, 'src', 'icon_appletv', layer.lower() + '.png'
            )
            dst = os.path.join(
                ROOT_DIR,
                'ballisticacore-xcode',
                'BallisticaCore Shared',
                'Assets.xcassets',
                'tvOS App Icon & Top Shelf Image.brandassets',
                'App Icon.imagestack',
                layer + '.imagestacklayer',
                'Content.imageset',
                layer.lower() + '_' + str(scale) + 'x.png',
            )
            cmd = ' '.join(
                [
                    RESIZE_CMD,
                    str(res[0] * scale),
                    str(res[1] * scale),
                    '"' + src + '"',
                    '"' + dst + '"',
                ]
            )
            targets.append(Target(src=[src], dst=dst, cmd=cmd))


def _add_apple_tv_store_icon(targets: list[Target]) -> None:
    res = (1280, 768)
    for layer in ['Layer1', 'Layer2', 'Layer3', 'Layer4', 'Layer5']:
        for scale in [1]:
            src = os.path.join(
                RES_DIR, 'src', 'icon_appletv', layer.lower() + '.png'
            )
            dst = os.path.join(
                ROOT_DIR,
                'ballisticacore-xcode',
                'BallisticaCore Shared',
                'Assets.xcassets',
                'tvOS App Icon & Top Shelf Image.brandassets',
                'App Icon - App Store.imagestack',
                layer + '.imagestacklayer',
                'Content.imageset',
                layer.lower() + '_' + str(scale) + 'x.png',
            )
            cmd = ' '.join(
                [
                    RESIZE_CMD,
                    str(res[0] * scale),
                    str(res[1] * scale),
                    '"' + src + '"',
                    '"' + dst + '"',
                ]
            )
            targets.append(Target(src=[src], dst=dst, cmd=cmd))


def _add_google_vr_icon(targets: list[Target]) -> None:
    res = (512, 512)
    for layer in ['vr_icon_background', 'vr_icon']:
        src = os.path.join(RES_DIR, 'src', 'icon_googlevr', layer + '.png')
        dst = os.path.join(
            ROOT_DIR,
            'ballisticacore-android',
            'BallisticaCore',
            'src',
            'cardboard',
            'res',
            'drawable-nodpi',
            layer + '.png',
        )
        cmd = ' '.join(
            [
                RESIZE_CMD,
                str(res[0]),
                str(res[1]),
                '"' + src + '"',
                '"' + dst + '"',
            ]
        )
        targets.append(Target(src=[src], dst=dst, cmd=cmd, mkdir=True))


def _empty_line_if(condition: bool) -> list[str]:
    return [''] if condition else []


def update(projroot: str, check: bool) -> None:
    """main script entry point"""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    from efrotools import getconfig

    # Operate out of root dist dir for consistency.
    os.chdir(projroot)

    public = getconfig(Path('.'))['public']
    assert isinstance(public, bool)

    fname = 'resources/Makefile'
    with open(fname, encoding='utf-8') as infile:
        original = infile.read()
    lines = original.splitlines()

    auto_start_public = lines.index('# __AUTOGENERATED_PUBLIC_BEGIN__')
    auto_end_public = lines.index('# __AUTOGENERATED_PUBLIC_END__')
    auto_start_private = lines.index('# __AUTOGENERATED_PRIVATE_BEGIN__')
    auto_end_private = lines.index('# __AUTOGENERATED_PRIVATE_END__')

    # Public targets (full sources available in public)
    targets: list[Target] = []
    basename = 'public'
    our_lines_public = (
        _empty_line_if(bool(targets))
        + _emit_group_build_lines(targets, basename)
        + _emit_group_clean_lines(targets, basename)
        + [t.emit() for t in targets]
    )

    # Only rewrite the private section in the private repo; otherwise
    # keep the existing one intact.
    if public:
        our_lines_private = lines[auto_start_private + 1 : auto_end_private]
    else:
        # Private targets (available in public through efrocache)
        targets = []
        basename = 'private'
        _add_windows_icon(targets, generic=True, oculus=False, inputs=False)
        our_lines_private_1 = (
            _empty_line_if(bool(targets))
            + _emit_group_build_lines(targets, basename)
            + _emit_group_clean_lines(targets, basename)
            + ['# __EFROCACHE_TARGET__\n' + t.emit() for t in targets]
            + _emit_group_efrocache_lines(targets)
        )

        # Private-internal targets (not available at all in public)
        targets = []
        basename = 'private-internal'
        _add_windows_icon(targets, generic=False, oculus=True, inputs=True)
        _add_ios_app_icon(targets)
        _add_macos_app_icon(targets)
        _add_android_app_icon(targets)
        _add_android_app_icon_new(targets)
        _add_android_cardboard_app_icon(targets)
        _add_android_cardboard_app_icon_new(targets)
        _add_android_tv_banner(targets)
        _add_apple_tv_top_shelf(targets)
        _add_apple_tv_3d_icon(targets)
        _add_apple_tv_store_icon(targets)
        _add_google_vr_icon(targets)
        our_lines_private_2 = (
            ['# __PUBSYNC_STRIP_BEGIN__']
            + _empty_line_if(bool(targets))
            + _emit_group_build_lines(targets, basename)
            + _emit_group_clean_lines(targets, basename)
            + [t.emit() for t in targets]
            + ['# __PUBSYNC_STRIP_END__']
        )
        our_lines_private = our_lines_private_1 + our_lines_private_2

    filtered = (
        lines[: auto_start_public + 1]
        + our_lines_public
        + lines[auto_end_public : auto_start_private + 1]
        + our_lines_private
        + lines[auto_end_private:]
    )
    out = '\n'.join(filtered) + '\n'

    if out == original:
        print(f'{fname} is up to date.')
    else:
        if check:
            if bool(False):
                print(
                    f'FOUND------\n{original}\nEND FOUND--------\n'
                    f'EXPECTED------\n{out}\nEND EXPECTED-------\n'
                )
            raise CleanError(f"ERROR: file is out of date: '{fname}'.")
        print(f'{Clr.SBLU}Updating: {fname}{Clr.RST}')
        with open(fname, 'w', encoding='utf-8') as outfile:
            outfile.write(out)
