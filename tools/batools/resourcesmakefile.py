# Released under the MIT License. See LICENSE for details.
#
"""Generate our resources Makefile.

(builds things like icons, banners, images, etc.)
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import Optional, List, Dict

# These paths need to be relative to the dir we're writing the Makefile to.
TOOLS_DIR = '../tools'
ROOT_DIR = '..'
RES_DIR = '.'
RESIZE_CMD = os.path.join(TOOLS_DIR, 'pcommand resize_image')


def _add_windows_icon(targets: List[Dict]) -> None:

    # Windows Icon
    sizes = [256, 128, 96, 64, 48, 32, 16]
    all_icons = []
    for size in sizes:
        dst_base = 'build'
        src = os.path.join('src', 'icon', 'icon_clipped.png')
        dst = os.path.join(dst_base, 'win_icon_' + str(size) + '_tmp.png')
        cmd = ' '.join([
            RESIZE_CMD,
            str(size),
            str(size), '"' + src + '"', '"' + dst + '"'
        ])
        all_icons.append(dst)
        targets.append({'src': [src], 'dst': dst, 'cmd': cmd, 'mkdir': True})

    # Assemble all the bits we just made into .ico files.
    for path in [
            ROOT_DIR + '/ballisticacore-windows/Generic/BallisticaCore.ico',
            ROOT_DIR + '/ballisticacore-windows/Oculus/BallisticaCore.ico',
    ]:
        cmd = ('convert ' + ''.join([' "' + f + '"'
                                     for f in all_icons]) + ' "' + path + '"')
        targets.append({'src': all_icons, 'dst': path, 'cmd': cmd})


def _add_ios_app_icon(targets: List[Dict]) -> None:
    sizes = [(20, 2), (20, 3), (29, 2), (29, 3), (40, 2), (40, 3), (60, 2),
             (60, 3), (20, 1), (29, 1), (40, 1), (76, 1), (76, 2), (83.5, 2),
             (1024, 1)]
    for size in sizes:
        res = int(size[0] * size[1])
        src = os.path.join('src', 'icon', 'icon_flat.png')
        dst = os.path.join(
            ROOT_DIR, 'ballisticacore-xcode', 'BallisticaCore Shared',
            'Assets.xcassets', 'AppIcon iOS.appiconset',
            'icon_' + str(size[0]) + 'x' + str(size[1]) + '.png')
        cmd = ' '.join(
            [RESIZE_CMD,
             str(res),
             str(res), '"' + src + '"', '"' + dst + '"'])
        targets.append({'src': [src], 'dst': dst, 'cmd': cmd})


def _add_macos_app_icon(targets: List[Dict]) -> None:
    sizes = [(16, 1), (16, 2), (32, 1), (32, 2), (128, 1), (128, 2), (256, 1),
             (256, 2), (512, 1), (512, 2)]
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
            [RESIZE_CMD,
             str(res),
             str(res), '"' + src + '"', '"' + dst + '"'])
        targets.append({'src': [src], 'dst': dst, 'cmd': cmd})


def _add_android_app_icon(targets: List[Dict],
                          src_name: str = 'icon_clipped.png',
                          variant_name: str = 'main') -> None:
    sizes = [('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144),
             ('xxxhdpi', 192)]
    for size in sizes:
        res = size[1]
        src = os.path.join(RES_DIR, 'src', 'icon', src_name)
        dst = os.path.join(ROOT_DIR, 'ballisticacore-android',
                           'BallisticaCore', 'src', variant_name, 'res',
                           'mipmap-' + size[0], 'ic_launcher.png')
        cmd = ' '.join(
            [RESIZE_CMD,
             str(res),
             str(res), '"' + src + '"', '"' + dst + '"'])
        targets.append({'src': [src], 'dst': dst, 'cmd': cmd, 'mkdir': True})


def _add_android_app_icon_new(targets: List[Dict],
                              src_fg_name: str = 'icon_android_layered_fg.png',
                              src_bg_name: str = 'icon_android_layered_bg.png',
                              variant_name: str = 'main') -> None:
    sizes = [('mdpi', 108), ('hdpi', 162), ('xhdpi', 216), ('xxhdpi', 324),
             ('xxxhdpi', 432)]
    for size in sizes:
        res = size[1]

        # Foreground component.
        src = os.path.join(RES_DIR, 'src', 'icon', src_fg_name)
        dst = os.path.join(ROOT_DIR, 'ballisticacore-android',
                           'BallisticaCore', 'src', variant_name, 'res',
                           'mipmap-' + size[0], 'ic_launcher_foreground.png')
        cmd = ' '.join(
            [RESIZE_CMD,
             str(res),
             str(res), '"' + src + '"', '"' + dst + '"'])
        targets.append({'src': [src], 'dst': dst, 'cmd': cmd, 'mkdir': True})

        # Background component.
        src = os.path.join(RES_DIR, 'src', 'icon', src_bg_name)
        dst = os.path.join(ROOT_DIR, 'ballisticacore-android',
                           'BallisticaCore', 'src', variant_name, 'res',
                           'mipmap-' + size[0], 'ic_launcher_background.png')
        cmd = ' '.join(
            [RESIZE_CMD,
             str(res),
             str(res), '"' + src + '"', '"' + dst + '"'])
        targets.append({'src': [src], 'dst': dst, 'cmd': cmd, 'mkdir': True})


def _add_android_cardboard_app_icon(targets: List[Dict]) -> None:
    _add_android_app_icon(targets=targets,
                          src_name='icon_clipped_vr.png',
                          variant_name='cardboard')


def _add_android_cardboard_app_icon_new(targets: List[Dict]) -> None:
    _add_android_app_icon_new(targets=targets,
                              src_fg_name='icon_android_layered_fg_vr.png',
                              variant_name='cardboard')


def _add_android_tv_banner(targets: List[Dict]) -> None:
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
    cmd = ' '.join([
        RESIZE_CMD,
        str(res[0]),
        str(res[1]), '"' + src + '"', '"' + dst + '"'
    ])
    targets.append({'src': [src], 'dst': dst, 'cmd': cmd, 'mkdir': True})


def _add_apple_tv_top_shelf(targets: List[Dict]) -> None:
    instances = [('24x9', '', '', 1920, 720),
                 ('29x9', ' Wide', '_wide', 2320, 720)]
    for instance in instances:
        for scale in [1, 2]:
            res = (instance[3] * scale, instance[4] * scale)
            src = os.path.join(RES_DIR, 'src', 'banner',
                               'banner_' + instance[0] + '.png')
            dst = os.path.join(
                ROOT_DIR,
                'ballisticacore-xcode',
                'BallisticaCore Shared',
                'Assets.xcassets',
                'tvOS App Icon & Top Shelf Image.brandassets',
                'Top Shelf Image' + instance[1] + '.imageset',
                'shelf' + instance[2] + '_' + str(scale) + 'x.png',
            )
            cmd = ' '.join([
                RESIZE_CMD,
                str(res[0]),
                str(res[1]), '"' + src + '"', '"' + dst + '"'
            ])
            targets.append({'src': [src], 'dst': dst, 'cmd': cmd})


def _add_apple_tv_3d_icon(targets: List[Dict]) -> None:
    res = (400, 240)
    for layer in ['Layer1', 'Layer2', 'Layer3', 'Layer4', 'Layer5']:
        for scale in [1, 2]:
            src = os.path.join(RES_DIR, 'src', 'icon_appletv',
                               layer.lower() + '.png')
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
            cmd = ' '.join([
                RESIZE_CMD,
                str(res[0] * scale),
                str(res[1] * scale), '"' + src + '"', '"' + dst + '"'
            ])
            targets.append({'src': [src], 'dst': dst, 'cmd': cmd})


def _add_apple_tv_store_icon(targets: List[Dict]) -> None:
    res = (1280, 768)
    for layer in ['Layer1', 'Layer2', 'Layer3', 'Layer4', 'Layer5']:
        for scale in [1]:
            src = os.path.join(RES_DIR, 'src', 'icon_appletv',
                               layer.lower() + '.png')
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
            cmd = ' '.join([
                RESIZE_CMD,
                str(res[0] * scale),
                str(res[1] * scale), '"' + src + '"', '"' + dst + '"'
            ])
            targets.append({'src': [src], 'dst': dst, 'cmd': cmd})


def _add_google_vr_icon(targets: List[Dict]) -> None:
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
        cmd = ' '.join([
            RESIZE_CMD,
            str(res[0]),
            str(res[1]), '"' + src + '"', '"' + dst + '"'
        ])
        targets.append({'src': [src], 'dst': dst, 'cmd': cmd, 'mkdir': True})


def _write_makefile(fname: str, targets: List[Dict], check: bool) -> None:
    from efrotools import get_public_license
    existing: Optional[str]
    try:
        with open(fname, 'r') as infile:
            existing = infile.read()
    except Exception:
        existing = None

    out = (get_public_license('makefile') +
           f'\n# Generated by {__name__}; do not hand-edit.\n\n')
    all_dsts = set()
    for target in targets:
        all_dsts.add(target['dst'])
    out += 'all: resources\n\nresources: ' + ' \\\n     '.join(
        dst.replace(' ', '\\ ') for dst in sorted(all_dsts)) + '\n\n'

    out += 'clean:\n\trm -f ' + ' \\\n         '.join(
        '"' + dst + '"' for dst in sorted(all_dsts)) + '\n\n'
    var_num = 1
    for target in targets:
        if bool(False) and ' ' in target['dst']:
            out += 'TARGET_' + str(var_num) + ' = ' + target['dst'].replace(
                ' ', '\\ ') + '\n${TARGET_' + str(var_num) + '}'
            var_num += 1
        else:
            out += target['dst'].replace(' ', '\\ ')
        out += ' : ' + ' '.join(s for s in target['src']) + (
            ('\n\t@mkdir -p "' +
             os.path.dirname(target['dst']) + '"') if target.get(
                 'mkdir', False) else '') + '\n\t@' + target['cmd'] + '\n\n'
    if out == existing:
        print('Resources Makefile is up to date.')
    else:
        if check:
            print(Clr.SRED + 'ERROR: file out of date: ' + fname + Clr.RST)
            sys.exit(255)
        print(Clr.SBLU + 'Generating: ' + fname + Clr.RST)
        with open(fname, 'w') as outfile:
            outfile.write(out)


def update(projroot: str, check: bool) -> None:
    """main script entry point"""

    # Operate out of root dist dir for consistency.
    os.chdir(projroot)

    targets: List[Dict] = []

    _add_windows_icon(targets)
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

    # Write makefile (or print if nothing has changed).
    _write_makefile('resources/Makefile', targets, check)
