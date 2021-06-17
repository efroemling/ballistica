# Released under the MIT License. See LICENSE for details.
#
"""Procedurally regenerates our code Makefile.

This Makefiles builds our generated code such as encrypted python strings,
node types, etc).
"""
from __future__ import annotations

import os
import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from dataclasses import dataclass

from efro.error import CleanError
from efro.terminal import Clr
from efrotools import getconfig

if TYPE_CHECKING:
    from typing import Optional, Set, List, Dict, Any, Tuple

# These paths need to be relative to the dir we're writing the Makefile to.
TOOLS_DIR = '../../tools'
ROOT_DIR = '../..'
OUT_DIR_CPP = '../ballistica/generated'


@dataclass
class Target:
    """A target to be added to the Makefile."""
    src: List[str]
    dst: str
    cmd: str
    mkdir: bool = False

    def emit(self) -> str:
        """Gen a Makefile target."""
        out: str = self.dst.replace(' ', '\\ ')
        out += ' : ' + ' '.join(s for s in self.src) + (
            ('\n\t@mkdir -p "' + os.path.dirname(self.dst) +
             '"') if self.mkdir else '') + '\n\t@' + self.cmd + '\n'
        return out


def _emit_group_build_lines(targets: List[Target], basename: str) -> List[str]:
    """Gen a group build target."""
    del basename  # Unused.
    out: List[str] = []
    if not targets:
        return out
    all_dsts = set()
    for target in targets:
        all_dsts.add(target.dst)
    out.append('sources: \\\n  ' + ' \\\n  '.join(
        dst.replace(' ', '\\ ') for dst in sorted(all_dsts)) + '\n')
    return out


def _emit_group_efrocache_lines(targets: List[Target]) -> List[str]:
    """Gen a group clean target."""
    out: List[str] = []
    if not targets:
        return out
    all_dsts = set()
    for target in targets:

        # We may need to make pipeline adjustments if/when we get filenames
        # with spaces in them.
        if ' ' in target.dst:
            raise CleanError('FIXME: need to account for spaces in filename'
                             f' "{target.dst}".')
        all_dsts.add(target.dst)
    out.append('efrocache-list:\n\t@echo ' +
               ' \\\n        '.join('"' + dst + '"'
                                    for dst in sorted(all_dsts)) + '\n')
    out.append('efrocache-build: sources\n')

    return out


def _add_python_embedded_targets(targets: List[Target]) -> None:
    pkg = 'bameta'
    # Note: sort to keep things deterministic.
    for fname in sorted(os.listdir(f'src/meta/{pkg}/python_embedded')):
        if (not fname.endswith('.py') or fname == '__init__.py'
                or 'flycheck' in fname):
            continue
        name = os.path.splitext(fname)[0]
        src = [
            f'{pkg}/python_embedded/{name}.py',
            os.path.join(TOOLS_DIR, 'batools', 'meta.py')
        ]
        dst = os.path.join(OUT_DIR_CPP, 'python_embedded', f'{name}.inc')
        if name == 'binding':
            targets.append(
                Target(src=src,
                       dst=dst,
                       cmd='$(PCOMMAND) gen_binding_code $< $@'))
        else:
            targets.append(
                Target(
                    src=src,
                    dst=dst,
                    cmd=f'$(PCOMMAND) gen_flat_data_code $< $@ {name}_code'))


def _add_python_embedded_targets_internal(targets: List[Target]) -> None:
    pkg = 'bametainternal'
    # Note: sort to keep things deterministic.
    for fname in sorted(os.listdir(f'src/meta/{pkg}/python_embedded')):
        if (not fname.endswith('.py') or fname == '__init__.py'
                or 'flycheck' in fname):
            continue
        name = os.path.splitext(fname)[0]
        src = [
            f'{pkg}/python_embedded/{name}.py',
            os.path.join(TOOLS_DIR, 'batoolsinternal', 'meta.py')
        ]
        dst = os.path.join(OUT_DIR_CPP, 'python_embedded', f'{name}.inc')
        targets.append(
            Target(src=src,
                   dst=dst,
                   cmd='$(PCOMMAND) gen_encrypted_python_code $< $@'))


def _empty_line_if(condition: bool) -> List[str]:
    return [''] if condition else []


def _project_centric_path(path: str) -> str:
    projpath = f'{os.getcwd()}/'
    assert '\\' not in projpath  # Don't expect to work on windows.
    abspath = os.path.abspath(os.path.join('src/meta', path))
    if not abspath.startswith(projpath):
        raise RuntimeError(
            f'Path "{abspath}" is not under project root "{projpath}"')
    return abspath[len(projpath):]


def update(projroot: str, check: bool) -> None:
    """Update the project meta Makefile."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # Operate out of root dist dir for consistency.
    os.chdir(projroot)

    public = getconfig(Path('.'))['public']
    assert isinstance(public, bool)

    fname = 'src/meta/Makefile'
    fname_pub_man = 'src/meta/.meta_manifest_public.json'
    fname_priv_man = 'src/meta/.meta_manifest_private.json'

    with open(fname) as infile:
        original = infile.read()
    lines = original.splitlines()

    with open(fname_pub_man) as infile:
        original_pub_man = infile.read()

    with open(fname_priv_man) as infile:
        original_priv_man = infile.read()

    # We'll generate manifests of all public/private files we generate
    # (not private-internal though).
    all_dsts_public: Set[str] = set()
    all_dsts_private: Set[str] = set()

    auto_start_public = lines.index('#__AUTOGENERATED_PUBLIC_BEGIN__')
    auto_end_public = lines.index('#__AUTOGENERATED_PUBLIC_END__')
    auto_start_private = lines.index('#__AUTOGENERATED_PRIVATE_BEGIN__')
    auto_end_private = lines.index('#__AUTOGENERATED_PRIVATE_END__')

    # Public targets (full sources available in public)
    targets: List[Target] = []
    pubtargets = targets
    basename = 'public'
    _add_python_embedded_targets(targets)
    our_lines_public = (_empty_line_if(bool(targets)) +
                        _emit_group_build_lines(targets, basename) +
                        [t.emit() for t in targets])
    all_dsts_public.update(t.dst for t in targets)

    # Only rewrite the private section in the private repo; otherwise
    # keep the existing one intact.
    if public:
        our_lines_private = lines[auto_start_private + 1:auto_end_private]
    else:
        # Private targets (available in public through efrocache)
        targets = []
        basename = 'private'
        our_lines_private_1 = (
            _empty_line_if(bool(targets)) +
            _emit_group_build_lines(targets, basename) +
            ['#__EFROCACHE_TARGET__\n' + t.emit() for t in targets] + [
                '\n# Note: we include our public targets in efrocache even\n'
                '# though they are buildable in public. This allows us to\n'
                '# fetch them on Windows to bootstrap binary CI builds in\n'
                '# cases where we can\'t use our full Makefiles.\n'
            ] + _emit_group_efrocache_lines(pubtargets + targets))
        all_dsts_private.update(t.dst for t in targets)

        # Private-internal targets (not available at all in public)
        targets = []
        basename = 'private-internal'
        _add_python_embedded_targets_internal(targets)
        our_lines_private_2 = (['#__PUBSYNC_STRIP_BEGIN__'] +
                               _empty_line_if(bool(targets)) +
                               _emit_group_build_lines(targets, basename) +
                               [t.emit()
                                for t in targets] + ['#__PUBSYNC_STRIP_END__'])
        our_lines_private = our_lines_private_1 + our_lines_private_2

    filtered = (lines[:auto_start_public + 1] + our_lines_public +
                lines[auto_end_public:auto_start_private + 1] +
                our_lines_private + lines[auto_end_private:])
    out = '\n'.join(filtered) + '\n'

    out_pub_man = json.dumps(sorted(
        _project_centric_path(p) for p in all_dsts_public),
                             indent=1)
    out_priv_man = json.dumps(sorted(
        _project_centric_path(p) for p in all_dsts_private),
                              indent=1)

    if (out == original and out_pub_man == original_pub_man
            and out_priv_man == original_priv_man):
        print(f'{fname} (and manifests) are up to date.')
    else:
        if check:
            errname = (fname if out != original else fname_pub_man
                       if out_pub_man != original_pub_man else fname_priv_man
                       if out_priv_man != original_priv_man else 'unknown')
            raise CleanError(f"ERROR: file is out of date: '{errname}'.")
        print(f'{Clr.SBLU}Updating {fname} (and cleaning existing output).'
              f'{Clr.RST}')

        if out != original:
            with open(fname, 'w') as outfile:
                outfile.write(out)

        # Also write our output file manifests every time we write the
        # Makefile (technically should check them individually in case
        # they're out of date but the Makefile isn't, though that should not
        # happen normally).
        if out_pub_man != fname_pub_man:
            with open(fname_pub_man, 'w') as outfile:
                outfile.write(out_pub_man)
        if out_priv_man != fname_priv_man:
            with open(fname_priv_man, 'w') as outfile:
                outfile.write(out_priv_man)

        # Also clean existing meta output every time the Makefile changes;
        # this should minimize the chance of orphan outputs hanging around
        # causing trouble.
        subprocess.run(['make', 'clean'], cwd='src/meta', check=True)
