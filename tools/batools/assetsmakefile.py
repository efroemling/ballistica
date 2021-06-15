#!/usr/bin/env python3.8
# Released under the MIT License. See LICENSE for details.
#
"""Updates assets/Makefile based on source assets present."""

from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING

from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import List, Set

PYC_SUFFIX = '.cpython-38.opt-1.pyc'


def _get_targets(varname: str,
                 inext: str,
                 outext: str,
                 all_targets: Set,
                 limit_to_prefix: str = None) -> str:
    """Generic function to map source extension to dst files."""

    src = 'assets/src'
    dst = 'assets/build'
    targets = []

    # Create outext targets for all inext files we find.
    for root, _dname, fnames in os.walk(src):
        if (limit_to_prefix is not None
                and not root.startswith(os.path.join(src, limit_to_prefix))):
            continue

        # Write the target to make sense from within assets/
        assert root.startswith(src)
        dstrootvar = 'build' + root[len(src):]
        dstfin = dst + root[len(src):]
        for fname in fnames:
            outname = fname[:-len(inext)] + outext
            if fname.endswith(inext):
                all_targets.add(os.path.join(dstfin, outname))
                targets.append(os.path.join(dstrootvar, outname))

    return '\n' + varname + ' = \\\n  ' + ' \\\n  '.join(sorted(targets))


def _get_py_targets(src: str, dst: str, py_targets: List[str],
                    pyc_targets: List[str], all_targets: Set[str],
                    subset: str) -> None:
    # pylint: disable=too-many-branches

    # Create py and pyc targets for all scripts in src.
    for root, _dname, fnames in os.walk(src):

        # Special case: ignore temp py files in data src.
        if root == 'assets/src/ba_data/data/maps':
            continue
        assert root.startswith(src)
        dstrootvar = dst[len('assets') + 1:] + root[len(src):]
        dstfin = dst + root[len(src):]
        for fname in fnames:

            # Ignore flycheck temp files as well as our _ba dummy module.
            if (not fname.endswith('.py') or fname.startswith('flycheck_')
                    or fname.startswith('.#') or fname == '_ba.py'):
                continue

            if root.startswith('assets/src/ba_data/python-site-packages'):
                in_subset = 'private-common'
            elif (root.startswith('assets/src/ba_data')
                  or root.startswith('assets/src/server')):
                in_subset = 'public'
            elif (root.startswith('tools/efro')
                  and not root.startswith('tools/efrotools')):
                # We want to pull just 'efro' out of tools; not efrotools.
                in_subset = 'public_tools'
            elif root.startswith('tools/bacommon'):
                in_subset = 'public_tools'
            elif root.startswith('assets/src/windows/x64'):
                in_subset = 'private-windows-x64'
            elif root.startswith('assets/src/windows/Win32'):
                in_subset = 'private-windows-Win32'
            elif root.startswith('assets/src/pylib-apple'):
                in_subset = 'private-apple'
            elif root.startswith('assets/src/pylib-android'):
                in_subset = 'private-android'
            else:
                in_subset = 'private-common'

            if subset == 'all':
                pass
            elif subset != in_subset:
                continue

            # gamedata pass includes only data; otherwise do all else

            # .py:
            all_targets.add(os.path.join(dstfin, fname))
            py_targets.append(os.path.join(dstrootvar, fname))

            # and .pyc:
            fname_pyc = fname[:-3] + PYC_SUFFIX
            all_targets.add(os.path.join(dstfin, '__pycache__', fname_pyc))
            pyc_targets.append(
                os.path.join(dstrootvar, '__pycache__', fname_pyc))


def _get_py_targets_subset(all_targets: Set[str], subset: str,
                           suffix: str) -> str:
    if subset == 'public_tools':
        src = 'tools'
        dst = 'assets/build/ba_data/python'
        copyrule = 'build/ba_data/python/%.py : ../tools/%.py'
    else:
        src = 'assets/src'
        dst = 'assets/build'
        copyrule = 'build/%.py : src/%.py'

    # Separate these into '1' and '2'.
    py_targets: List[str] = []
    pyc_targets: List[str] = []

    _get_py_targets(src,
                    dst,
                    py_targets,
                    pyc_targets,
                    all_targets,
                    subset=subset)

    # Need to sort these combined to keep pairs together.
    combined_targets = [(py_targets[i], pyc_targets[i])
                        for i in range(len(py_targets))]
    combined_targets.sort()
    py_targets = [t[0] for t in combined_targets]
    pyc_targets = [t[1] for t in combined_targets]

    out = (f'\nSCRIPT_TARGETS_PY{suffix} = \\\n  ' +
           ' \\\n  '.join(py_targets) + '\n')

    out += (f'\nSCRIPT_TARGETS_PYC{suffix} = \\\n  ' +
            ' \\\n  '.join(pyc_targets) + '\n')

    # We transform all non-public targets into efrocache-fetches in public.
    efc = '' if subset.startswith('public') else '#__EFROCACHE_TARGET__\n'
    out += ('\n# Rule to copy src asset scripts to dst.\n'
            '# (and make non-writable so I\'m less likely to '
            'accidentally edit them there)\n'
            f'{efc}$(SCRIPT_TARGETS_PY{suffix}) : {copyrule}\n'
            '\t@echo Copying script: $@\n'
            '\t@mkdir -p $(dir $@)\n'
            '\t@rm -f $@\n'
            '\t@cp $^ $@\n'
            '\t@chmod 444 $@\n')

    # Fancy new simple loop-based target generation.
    out += (f'\n# These are too complex to define in a pattern rule;\n'
            f'# Instead we generate individual targets in a loop.\n'
            f'$(foreach element,$(SCRIPT_TARGETS_PYC{suffix}),\\\n'
            f'$(eval $(call make-opt-pyc-target,$(element))))')

    # Old code to explicitly emit individual targets.
    if bool(False):
        out += (
            '\n# Looks like path mangling from py to pyc is too complex for'
            ' pattern rules so\n# just generating explicit targets'
            ' for each. Could perhaps look into using a\n# fancy for-loop'
            ' instead, but perhaps listing these explicitly isn\'t so bad.\n')
        for i, target in enumerate(pyc_targets):
            # Note: there's currently a bug which can cause python bytecode
            # generation to be non-deterministic. This can break our blessing
            # process since we bless in core but then regenerate bytecode in
            # spinoffs. See https://bugs.python.org/issue34722
            # For now setting PYTHONHASHSEED=1 is a workaround.
            out += ('\n' + target + ': \\\n      ' + py_targets[i] +
                    '\n\t@echo Compiling script: $^\n'
                    '\t@rm -rf $@ && PYTHONHASHSEED=1 $(TOOLS_DIR)/pcommand'
                    ' compile_python_files $^'
                    ' && chmod 444 $@\n')

    return out


def _get_extras_targets_win(all_targets: Set[str], platform: str) -> str:
    targets: List[str] = []
    base = 'assets/src/windows'
    dstbase = 'build/windows'
    for root, _dnames, fnames in os.walk(base):
        for fname in fnames:

            # Only include the platform we were passed.
            if not root.startswith('assets/src/windows/' + platform):
                continue

            ext = os.path.splitext(fname)[-1]

            # "I don't like .DS_Store files. They're coarse and rough and
            # irritating and they get everywhere."
            if fname == '.DS_Store':
                continue

            # Ignore python files as they're handled separately.
            if ext in ['.py', '.pyc']:
                continue

            # Various stuff we expect to be there...
            if ext in [
                    '.exe', '.dll', '.bat', '.txt', '.whl', '.ps1', '.css',
                    '.sample', '.ico', '.pyd', '.ctypes', '.rst', '.fish',
                    '.csh', '.cat', '.pdb', '.lib', '.html'
            ] or fname in [
                    'activate', 'README', 'command_template', 'fetch_macholib'
            ]:
                targetpath = os.path.join(dstbase + root[len(base):], fname)
                targets.append(targetpath)
                all_targets.add('assets/' + targetpath)
                continue

            # Complain if something new shows up instead of blindly
            # including it.
            raise RuntimeError(f'Unexpected extras file: {fname}')

    targets.sort()
    p_up = platform.upper()
    out = (f'\nEXTRAS_TARGETS_WIN_{p_up} = \\\n  ' + ' \\\n  '.join(targets) +
           '\n')

    # We transform all these targets into efrocache-fetches in public.
    out += ('\n# Rule to copy src extras to build.\n'
            f'#__EFROCACHE_TARGET__\n'
            f'$(EXTRAS_TARGETS_WIN_{p_up}) : build/% :'
            ' src/%\n'
            '\t@echo Copying file: $@\n'
            '\t@mkdir -p $(dir $@)\n'
            '\t@rm -f $@\n'
            '\t@cp $^ $@\n')

    return out


def update_assets_makefile(projroot: str, check: bool) -> None:
    """Main script entry point."""
    # pylint: disable=too-many-locals
    from efrotools import getconfig
    from pathlib import Path

    # Always operate out of dist root dir.
    os.chdir(projroot)

    public = getconfig(Path('.'))['public']
    assert isinstance(public, bool)

    fname = 'assets/Makefile'
    with open(fname) as infile:
        original = infile.read()
    lines = original.splitlines()

    auto_start_public = lines.index('#__AUTOGENERATED_BEGIN_PUBLIC__')
    auto_end_public = lines.index('#__AUTOGENERATED_END_PUBLIC__')
    auto_start_private = lines.index('#__AUTOGENERATED_BEGIN_PRIVATE__')
    auto_end_private = lines.index('#__AUTOGENERATED_END_PRIVATE__')

    all_targets_public: Set[str] = set()
    all_targets_private: Set[str] = set()

    # We always auto-generate the public section.
    our_lines_public = [
        _get_py_targets_subset(all_targets_public,
                               subset='public',
                               suffix='_PUBLIC'),
        _get_py_targets_subset(all_targets_public,
                               subset='public_tools',
                               suffix='_PUBLIC_TOOLS')
    ]

    # Only auto-generate the private section in the private repo.
    if public:
        our_lines_private = lines[auto_start_private + 1:auto_end_private]
    else:
        our_lines_private = [
            _get_py_targets_subset(all_targets_private,
                                   subset='private-apple',
                                   suffix='_PRIVATE_APPLE'),
            _get_py_targets_subset(all_targets_private,
                                   subset='private-android',
                                   suffix='_PRIVATE_ANDROID'),
            _get_py_targets_subset(all_targets_private,
                                   subset='private-common',
                                   suffix='_PRIVATE_COMMON'),
            _get_py_targets_subset(all_targets_private,
                                   subset='private-windows-Win32',
                                   suffix='_PRIVATE_WIN_WIN32'),
            _get_py_targets_subset(all_targets_private,
                                   subset='private-windows-x64',
                                   suffix='_PRIVATE_WIN_X64'),
            _get_targets('COB_TARGETS', '.collidemodel.obj', '.cob',
                         all_targets_private),
            _get_targets('BOB_TARGETS', '.model.obj', '.bob',
                         all_targets_private),
            _get_targets('FONT_TARGETS', '.fdata', '.fdata',
                         all_targets_private),
            _get_targets('DATA_TARGETS',
                         '.json',
                         '.json',
                         all_targets_private,
                         limit_to_prefix='ba_data/data'),
            _get_targets('AUDIO_TARGETS', '.wav', '.ogg', all_targets_private),
            _get_targets('TEX2D_DDS_TARGETS', '.tex2d.png', '.dds',
                         all_targets_private),
            _get_targets('TEX2D_PVR_TARGETS', '.tex2d.png', '.pvr',
                         all_targets_private),
            _get_targets('TEX2D_KTX_TARGETS', '.tex2d.png', '.ktx',
                         all_targets_private),
            _get_targets('TEX2D_PREVIEW_PNG_TARGETS', '.tex2d.png',
                         '_preview.png', all_targets_private),
            _get_extras_targets_win(all_targets_private, 'Win32'),
            _get_extras_targets_win(all_targets_private, 'x64'),
        ]
    filtered = (lines[:auto_start_public + 1] + our_lines_public +
                lines[auto_end_public:auto_start_private + 1] +
                our_lines_private + lines[auto_end_private:])
    out = '\n'.join(filtered) + '\n'

    if out == original:
        print(f'{fname} is up to date.')
    else:
        if check:
            print(f"{Clr.SRED}ERROR: file is out of date: '{fname}'.{Clr.RST}")

            # Print exact contents if we need to debug:
            if bool(False):
                print(f'EXPECTED ===========================================\n'
                      f'{out}\n'
                      f'FOUND ==============================================\n'
                      f'{original}\n'
                      f'END COMPARE ========================================')
            sys.exit(255)
        print(f'{Clr.SBLU}Updating: {fname}{Clr.RST}')
        with open(fname, 'w') as outfile:
            outfile.write(out)

    # Lastly, write a simple manifest of the things we expect to have
    # in build. We can use this to clear out orphaned files as part of builds.
    _write_manifest('assets/.asset_manifest_public.json', all_targets_public,
                    check)
    if not public:
        _write_manifest('assets/.asset_manifest_private.json',
                        all_targets_private, check)


def _write_manifest(manifest_path: str, all_targets: Set[str],
                    check: bool) -> None:
    # Lastly, write a simple manifest of the things we expect to have
    # in build. We can use this to clear out orphaned files as part of builds.
    assert all(t.startswith('assets/build/') for t in all_targets)
    if not os.path.exists(manifest_path):
        existing_manifest = None
    else:
        with open(manifest_path) as infile:
            existing_manifest = json.loads(infile.read())
    manifest = sorted(t[13:] for t in all_targets)
    if manifest == existing_manifest:
        print(f'{manifest_path} is up to date.')
    else:
        if check:
            print(f'{Clr.SRED}ERROR: file is out of date:'
                  f" '{manifest_path}'.{Clr.RST}")
            sys.exit(255)
        print(f'{Clr.SBLU}Updating: {manifest_path}{Clr.RST}')
        with open(manifest_path, 'w') as outfile:
            outfile.write(json.dumps(manifest, indent=1))
