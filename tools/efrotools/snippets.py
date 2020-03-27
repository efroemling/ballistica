# Copyright (c) 2011-2020 Eric Froemling
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
"""Standard snippets that can be pulled into project snippets scripts.

A snippet is a mini-program that directly takes input from stdin and does
some focused task. This module is a repository of common snippets that can
be imported into projects' snippets script for easy reuse.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any, List


class CleanError(Exception):
    """Exception resulting in a clean error string print and exit."""


# Absolute path of the project root.
PROJROOT = Path(__file__).resolve().parents[2]

CLRHDR = '\033[95m'
CLRRED = '\033[91m'
CLRBLU = '\033[94m'
CLREND = '\033[0m'


def snippets_main(globs: Dict[str, Any]) -> None:
    """Run a snippet contained in the snippets script.

    We simply look for all public functions and call
    the one corresponding to the first passed arg.
    """
    import types
    funcs = dict(((name, obj) for name, obj in globs.items()
                  if not name.startswith('_') and name != 'snippets_main'
                  and isinstance(obj, types.FunctionType)))
    show_help = False
    retval = 0
    if len(sys.argv) < 2:
        print("ERROR: command expected.")
        show_help = True
        retval = 255
    else:
        if sys.argv[1] == 'help':
            if len(sys.argv) == 2:
                show_help = True
            elif sys.argv[2] not in funcs:
                print('Invalid help command.')
                retval = 255
            else:
                docs = _trim_docstring(
                    getattr(funcs[sys.argv[2]], '__doc__', '<no docs>'))
                print('\nsnippets ' + sys.argv[2] + ':\n' + docs + '\n')
        elif sys.argv[1] in funcs:
            try:
                funcs[sys.argv[1]]()
            except CleanError as exc:
                print(CLRRED + str(exc) + CLREND)
                sys.exit(-1)
        else:
            print('Unknown snippets command: "' + sys.argv[1] + '"',
                  file=sys.stderr)
            retval = 255

    if show_help:
        print("Snippets contains project related commands too small"
              " to warrant full scripts.")
        print("Run 'snippets help <COMMAND>' for full command documentation.")
        print('Available commands:')
        for func, obj in sorted(funcs.items()):
            doc = getattr(obj, '__doc__', '').splitlines()[0].strip()
            print(f'{CLRHDR}{func}{CLRBLU} - {doc}{CLREND}')
    sys.exit(retval)


def _trim_docstring(docstring: str) -> str:
    """Trim raw doc-strings for pretty printing.

    Taken straight from PEP 257.
    """
    if not docstring:
        return ''

    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines.
    lines = docstring.expandtabs().splitlines()

    # Determine minimum indentation (first line doesn't count).
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))

    # Remove indentation (first line is special).
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())

    # Strip off trailing and leading blank lines.
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)

    # Return a single string.
    return '\n'.join(trimmed)


def _spelling(words: List[str]) -> None:
    fname = '.idea/dictionaries/ericf.xml'
    with open(fname) as infile:
        lines = infile.read().splitlines()
    if lines[2] != '    <words>':
        raise RuntimeError('Unexpected dictionary format.')
    added_count = 0
    for word in words:
        line = f'      <w>{word.lower()}</w>'
        if line not in lines:
            lines.insert(3, line)
            added_count += 1

    with open(fname, 'w') as outfile:
        # Sort lines in the words section.
        assert all(l.startswith('      <w>') for l in lines[3:-3])
        outfile.write('\n'.join(lines[:3] + sorted(lines[3:-3]) + lines[-3:]))
    print('Added', added_count, 'words to the dictionary.')


def spelling_all() -> None:
    """Add all misspellings from a pycharm run."""

    print('Running "make pycharm-full"...')
    lines = [
        line for line in subprocess.run(
            ['make', 'pycharm-full'], check=False,
            capture_output=True).stdout.decode().splitlines()
        if 'Typo: In word' in line
    ]
    words = [
        line.split('Typo: In word')[1].strip().replace("'", "")
        for line in lines
    ]
    _spelling(words)


def spelling() -> None:
    """Add words to the PyCharm dictionary."""
    _spelling(sys.argv[2:])


def check_clean_safety() -> None:
    """Ensure all files are are added to git or in gitignore.

    Use to avoid losing work if we accidentally do a clean without
    adding something.
    """
    if len(sys.argv) != 2:
        raise Exception('invalid arguments')

    # Make sure we wouldn't be deleting anything not tracked by git
    # or ignored.
    output = subprocess.check_output(['git', 'status',
                                      '--porcelain=v2']).decode()
    if any(line.startswith('?') for line in output.splitlines()):
        print('ERROR: untracked file(s) found; aborting.'
              ' (see "git status" from "' + os.getcwd() +
              '")  Either \'git add\' them, add them to .gitignore,'
              ' or remove them and try again.',
              file=sys.stderr)
        sys.exit(255)


def formatcode() -> None:
    """Run clang-format on all of our source code (multithreaded)."""
    from efrotools import code
    full = '-full' in sys.argv
    code.formatcode(PROJROOT, full)


def formatscripts() -> None:
    """Run yapf on all our scripts (multithreaded)."""
    from efrotools import code
    full = '-full' in sys.argv
    code.formatscripts(PROJROOT, full)


def formatmakefile() -> None:
    """Format the main makefile."""
    from efrotools.makefile import Makefile
    with open('Makefile') as infile:
        original = infile.read()

    formatted = Makefile(original).get_output()

    # Only write if it changed.
    if formatted != original:
        with open('Makefile', 'w') as outfile:
            outfile.write(formatted)


def cpplint() -> None:
    """Run lint-checking on all code deemed lint-able."""
    from efrotools import code
    full = '-full' in sys.argv
    code.cpplint(PROJROOT, full)


def scriptfiles() -> None:
    """List project script files.

    Pass -lines to use newlines as separators. The default is spaces.
    """
    from efrotools import code
    paths = code.get_script_filenames(projroot=PROJROOT)
    assert not any(' ' in path for path in paths)
    if '-lines' in sys.argv:
        print('\n'.join(paths))
    else:
        print(' '.join(paths))


def pylint() -> None:
    """Run pylint checks on our scripts."""
    from efrotools import code
    full = ('-full' in sys.argv)
    fast = ('-fast' in sys.argv)
    code.pylint(PROJROOT, full, fast)


def mypy() -> None:
    """Run mypy checks on our scripts."""
    from efrotools import code
    full = ('-full' in sys.argv)
    code.mypy(PROJROOT, full)


def dmypy() -> None:
    """Run mypy checks on our scripts using the mypy daemon."""
    from efrotools import code
    code.dmypy(PROJROOT)


def pycharm() -> None:
    """Run PyCharm checks on our scripts."""
    from efrotools import code
    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    code.pycharm(PROJROOT, full, verbose)


def clioncode() -> None:
    """Run CLion checks on our code."""
    from efrotools import code
    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    code.clioncode(PROJROOT, full, verbose)


def androidstudiocode() -> None:
    """Run Android Studio checks on our code."""
    from efrotools import code
    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    code.androidstudiocode(PROJROOT, full, verbose)


def tool_config_install() -> None:
    """Install a tool config file (with some filtering)."""
    from efrotools import get_config
    import textwrap
    if len(sys.argv) != 4:
        raise Exception("expected 2 args")
    src = Path(sys.argv[2])
    dst = Path(sys.argv[3])
    with src.open() as infile:
        cfg = infile.read()

    # Do a bit of filtering.

    # Stick project-root wherever they want.
    cfg = cfg.replace('__EFRO_PROJECT_ROOT__', str(PROJROOT))

    stdsettings = textwrap.dedent("""
    # We don't want all of our plain scripts complaining
    # about __main__ being redefined.
    scripts_are_modules = True

    # Try to be as strict as we can about using types everywhere.
    warn_unused_ignores = True
    warn_return_any = True
    warn_redundant_casts = True
    disallow_incomplete_defs = True
    disallow_untyped_defs = True
    disallow_untyped_decorators = True
    disallow_untyped_calls = True
    disallow_any_unimported = True
    strict_equality = True
    """).strip()

    cfg = cfg.replace('__EFRO_MYPY_STANDARD_SETTINGS__', stdsettings)

    # Gen a pylint init to set up our python paths:
    pylint_init_tag = '__EFRO_PYLINT_INIT__'
    if pylint_init_tag in cfg:
        pypaths = get_config(PROJROOT).get('python_paths')
        if pypaths is None:
            raise RuntimeError('python_paths not set in project config')
        cstr = "init-hook='import sys;"
        for path in pypaths:
            cstr += f" sys.path.append('{PROJROOT}/{path}');"
        cstr += "'"
        cfg = cfg.replace(pylint_init_tag, cstr)

    # Add an auto-generated notice.
    comment = None
    if dst.name in ['.dir-locals.el']:
        comment = ';;'
    elif dst.name in [
            '.mypy.ini', '.pycheckers', '.pylintrc', '.style.yapf',
            '.clang-format'
    ]:
        comment = '#'
    if comment is not None:
        cfg = (f'{comment} THIS FILE WAS AUTOGENERATED; DO NOT EDIT.\n'
               f'{comment} Source: {src}.\n\n' + cfg)

    with dst.open('w') as outfile:
        outfile.write(cfg)


def sync_all() -> None:
    """Runs full syncs between all efrotools projects.

    This list is defined in the EFROTOOLS_SYNC_PROJECTS env var.
    This assumes that there is a 'sync-full' and 'sync-list' Makefile target
    under each project.
    """
    import concurrent.futures
    print(f'{CLRBLU}Updating formatting for all projects...{CLREND}')
    projects_str = os.environ.get('EFROTOOLS_SYNC_PROJECTS')
    if projects_str is None:
        raise CleanError('EFROTOOL_SYNC_PROJECTS is not defined.')
    projects = projects_str.split(':')

    def _format_project(fproject: str) -> None:
        fcmd = f'cd "{fproject}" && make format'
        print(fcmd)
        subprocess.run(fcmd, shell=True, check=True)

    # No matter what we're doing (even if just listing), run formatting
    # in all projects before beginning. Otherwise if we do a sync and then
    # a preflight we'll often wind up getting out-of-sync errors due to
    # formatting changing after the sync.
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(projects)) as executor:
        # Converting this to a list will propagate any errors.
        list(executor.map(_format_project, projects))

    if len(sys.argv) > 2 and sys.argv[2] == 'list':
        # List mode
        for project in projects_str.split(':'):
            cmd = f'cd "{project}" && make sync-list'
            print(cmd)
            subprocess.run(cmd, shell=True, check=True)

    else:
        # Real mode
        for i in range(2):
            if i == 0:
                print(CLRBLU + "Running sync pass 1:"
                      " (ensures all changes at dsts are pushed to src)" +
                      CLREND)
            else:
                print(CLRBLU + "Running sync pass 2:"
                      " (ensures latest src is pulled to all dsts)" + CLREND)
            for project in projects_str.split(':'):
                cmd = f'cd "{project}" && make sync-full'
                print(cmd)
                subprocess.run(cmd, shell=True, check=True)
        print(CLRBLU + 'Sync-all successful!' + CLREND)


def sync() -> None:
    """Runs standard syncs between this project and others."""
    from efrotools import get_config
    from efrotools.sync import Mode, SyncItem, run_standard_syncs
    mode = Mode(sys.argv[2]) if len(sys.argv) > 2 else Mode.PULL

    # Load sync-items from project config and run them
    sync_items = [
        SyncItem(**i) for i in get_config(PROJROOT).get('sync_items', [])
    ]
    run_standard_syncs(PROJROOT, mode, sync_items)


def compile_python_files() -> None:
    """Compile pyc files for packaging.

    This creates hash-based PYC files in opt level 1 with hash checks
    defaulting to off, so we don't have to worry about timestamps or
    loading speed hits due to hash checks. (see PEP 552).
    We just need to tell modders that they'll need to clear these
    cache files out or turn on debugging mode if they want to tweak
    the built-in scripts.
    """
    import py_compile
    for arg in sys.argv[2:]:
        mode = py_compile.PycInvalidationMode.UNCHECKED_HASH
        py_compile.compile(arg,
                           dfile=os.path.basename(arg),
                           doraise=True,
                           optimize=1,
                           invalidation_mode=mode)


def pytest() -> None:
    """Run pytest with project environment set up properly."""
    import platform
    from efrotools import get_config, PYTHON_BIN

    print('PATH IS', sys.path)
    print('CWD IS', os.getcwd())

    subprocess.run([PYTHON_BIN, '-c', 'import sys; print("FOOO", sys.path)'],
                   check=True)

    # Grab our python paths for the project and stuff them in PYTHONPATH.
    pypaths = get_config(PROJROOT).get('python_paths')
    if pypaths is None:
        raise CleanError('python_paths not found in project config.')

    if platform.system() == 'Windows':
        pypaths = [
            os.path.join(os.getcwd(), s.replace('/', '\\')) for s in pypaths
        ]

    os.environ['PYTHONPATH'] = ':'.join(pypaths)
    print('SET VAL TO', ':'.join(pypaths), flush=True)

    # Also tell Python interpreters not to write __pycache__ dirs everywhere
    # which can screw up our builds.
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

    # Do the thing.
    results = subprocess.run([PYTHON_BIN, '-m', 'pytest'] + sys.argv[2:],
                             check=False)
    if results.returncode != 0:
        sys.exit(results.returncode)


def makefile_target_list() -> None:
    """Prints targets in a makefile.

    Takes a single argument: a path to a Makefile.
    """
    from dataclasses import dataclass

    @dataclass
    class _Entry:
        kind: str
        line: int
        title: str

    if len(sys.argv) != 3:
        raise RuntimeError("Expected exactly one filename arg.")

    with open(sys.argv[2]) as infile:
        lines = infile.readlines()

    def _docstr(lines2: List[str], linenum: int) -> str:
        doc = ''
        j = linenum - 1
        while j >= 0 and lines2[j].startswith('#'):
            doc = lines2[j][1:].strip()
            j -= 1
        if doc != '':
            return ' - ' + doc
        return doc

    print('----------------------\n'
          'Available Make Targets\n'
          '----------------------')

    entries: List[_Entry] = []
    for i, line in enumerate(lines):

        # Targets.
        if ':' in line and line.split(':')[0].replace('-', '').replace(
                '_', '').isalnum() and not line.startswith('_'):
            entries.append(
                _Entry(kind='target', line=i, title=line.split(':')[0]))

        # Section titles.
        if (line.startswith('#  ') and line.endswith('  #\n')
                and len(line.split()) > 2):
            entries.append(
                _Entry(kind='section', line=i, title=line[1:-2].strip()))

    for i, entry in enumerate(entries):
        if entry.kind == 'section':
            # Don't print headers for empty sections.
            if i + 1 >= len(entries) or entries[i + 1].kind == 'section':
                continue
            print('\n' + entry.title + '\n' + '-' * len(entry.title))
        elif entry.kind == 'target':
            print(CLRHDR + entry.title + CLRBLU + _docstr(lines, entry.line) +
                  CLREND)
