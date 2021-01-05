# Released under the MIT License. See LICENSE for details.
#
"""Standard snippets that can be pulled into project pcommand scripts.

A snippet is a mini-program that directly takes input from stdin and does
some focused task. This module is a repository of common snippets that can
be imported into projects' pcommand script for easy reuse.
"""
from __future__ import annotations

# Note: import as little as possible here at the module level to keep
# launch times fast for small snippets.
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any, List

# Absolute path of the project root.
PROJROOT = Path(__file__).resolve().parents[2]


def pcommand_main(globs: Dict[str, Any]) -> None:
    """Run a snippet contained in the pcommand script.

    We simply look for all public functions and call
    the one corresponding to the first passed arg.
    """
    import types
    from efro.error import CleanError
    from efro.terminal import Clr
    funcs = dict(((name, obj) for name, obj in globs.items()
                  if not name.startswith('_') and name != 'pcommand_main'
                  and isinstance(obj, types.FunctionType)))
    show_help = False
    retval = 0
    if len(sys.argv) < 2:
        print(f'{Clr.RED}ERROR: command expected.{Clr.RST}')
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
                print(f'\n{Clr.MAG}{Clr.BLD}pcommand {sys.argv[2]}:{Clr.RST}\n'
                      f'{Clr.MAG}{docs}{Clr.RST}\n')
        elif sys.argv[1] in funcs:
            try:
                funcs[sys.argv[1]]()
            except KeyboardInterrupt as exc:
                print(f'{Clr.RED}{exc}{Clr.RST}')
                sys.exit(1)
            except CleanError as exc:
                exc.pretty_print()
                sys.exit(1)
        else:
            print(f'{Clr.RED}Unknown pcommand: "{sys.argv[1]}"{Clr.RST}',
                  file=sys.stderr)
            retval = 255

    if show_help:
        print(f'The {Clr.MAG}{Clr.BLD}pcommand{Clr.RST} script encapsulates'
              f' a collection of project-related commands.')
        print(f"Run {Clr.MAG}{Clr.BLD}'pcommand [COMMAND] ...'"
              f'{Clr.RST} to run a command.')
        print(f"Run {Clr.MAG}{Clr.BLD}'pcommand help [COMMAND]'"
              f'{Clr.RST} for full documentation for a command.')
        print('Available commands:')
        for func, obj in sorted(funcs.items()):
            doc = getattr(obj, '__doc__', '').splitlines()[0].strip()
            print(f'{Clr.MAG}{func}{Clr.BLU} - {doc}{Clr.RST}')
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
    import os
    num_modded_dictionaries = 0
    for fname in [
            '.idea/dictionaries/ericf.xml',
            'ballisticacore-cmake/.idea/dictionaries/ericf.xml'
    ]:
        if not os.path.exists(fname):
            continue
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

            # Note: need to pull the </w> off the end of the line when sorting
            # or it messes with the order and we get different results than
            # Jetbrains stuff.
            outfile.write('\n'.join(
                lines[:3] +
                sorted(lines[3:-3], key=lambda x: x.replace('</w>', '')) +
                lines[-3:]))
        print(f'Added {added_count} words to {fname}.')
        num_modded_dictionaries += 1
    print(f'Modified {num_modded_dictionaries} dictionaries.')


def spelling_all() -> None:
    """Add all misspellings from a pycharm run."""
    import subprocess

    print('Running "make pycharm-full"...')
    lines = [
        line for line in subprocess.run(
            ['make', 'pycharm-full'], check=False,
            capture_output=True).stdout.decode().splitlines()
        if 'Typo: In word' in line
    ]
    words = [line.split('Typo: In word')[1].strip() for line in lines]

    # Strip enclosing quotes but not internal ones.
    for i, word in enumerate(words):
        assert word[0] == "'"
        assert word[-1] == "'"
        words[i] = word[1:-1]

    _spelling(words)


def spelling() -> None:
    """Add words to the PyCharm dictionary."""
    _spelling(sys.argv[2:])


def pyver() -> None:
    """Prints the Python version used by this project."""
    from efrotools import PYVER
    print(PYVER, end='')


def check_clean_safety() -> None:
    """Ensure all files are are added to git or in gitignore.

    Use to avoid losing work if we accidentally do a clean without
    adding something.
    """
    import os
    import subprocess
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
    """Format all of our C/C++/etc. code."""
    import efrotools.code
    full = '-full' in sys.argv
    efrotools.code.format_clang_format(PROJROOT, full)


def formatscripts() -> None:
    """Format all of our Python/etc. code."""
    import efrotools.code
    full = '-full' in sys.argv
    efrotools.code.format_yapf(PROJROOT, full)


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
    import efrotools.code
    full = '-full' in sys.argv
    efrotools.code.check_cpplint(PROJROOT, full)


def scriptfiles() -> None:
    """List project script files.

    Pass -lines to use newlines as separators. The default is spaces.
    """
    import efrotools.code
    paths = efrotools.code.get_script_filenames(projroot=PROJROOT)
    assert not any(' ' in path for path in paths)
    if '-lines' in sys.argv:
        print('\n'.join(paths))
    else:
        print(' '.join(paths))


def pylint() -> None:
    """Run pylint checks on our scripts."""
    import efrotools.code
    full = ('-full' in sys.argv)
    fast = ('-fast' in sys.argv)
    efrotools.code.pylint(PROJROOT, full, fast)


def runpylint() -> None:
    """Run pylint checks on provided filenames."""
    from efro.terminal import Clr
    from efro.error import CleanError
    import efrotools.code
    if len(sys.argv) < 3:
        raise CleanError('Expected at least 1 filename arg.')
    filenames = sys.argv[2:]
    efrotools.code.runpylint(PROJROOT, filenames)
    print(f'{Clr.GRN}Pylint Passed.{Clr.RST}')


def mypy() -> None:
    """Run mypy checks on our scripts."""
    import efrotools.code
    full = ('-full' in sys.argv)
    efrotools.code.mypy(PROJROOT, full)


def runmypy() -> None:
    """Run mypy checks on provided filenames."""
    from efro.terminal import Clr
    from efro.error import CleanError
    import efrotools.code
    if len(sys.argv) < 3:
        raise CleanError('Expected at least 1 filename arg.')
    filenames = sys.argv[2:]
    try:
        efrotools.code.runmypy(PROJROOT, filenames)
        print(f'{Clr.GRN}Mypy Passed.{Clr.RST}')
    except Exception as exc:
        raise CleanError('Mypy Failed.') from exc


def dmypy() -> None:
    """Run mypy checks on our scripts using the mypy daemon."""
    import efrotools.code
    efrotools.code.dmypy(PROJROOT)


def pycharm() -> None:
    """Run PyCharm checks on our scripts."""
    import efrotools.code
    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    efrotools.code.check_pycharm(PROJROOT, full, verbose)


def clioncode() -> None:
    """Run CLion checks on our code."""
    import efrotools.code
    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    efrotools.code.check_clioncode(PROJROOT, full, verbose)


def androidstudiocode() -> None:
    """Run Android Studio checks on our code."""
    import efrotools.code
    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    efrotools.code.check_android_studio(PROJROOT, full, verbose)


def tool_config_install() -> None:
    """Install a tool config file (with some filtering)."""
    from efro.terminal import Clr
    if len(sys.argv) != 4:
        raise Exception('expected 2 args')
    src = Path(sys.argv[2])
    dst = Path(sys.argv[3])

    print(f'Creating tool config: {Clr.BLD}{dst}{Clr.RST}')

    with src.open() as infile:
        cfg = infile.read()

    # Rome substitutions, etc.
    cfg = _filter_tool_config(cfg)

    # Add an auto-generated notice.
    comment = None
    if dst.name in ['.dir-locals.el']:
        comment = ';;'
    elif dst.name in [
            '.mypy.ini', '.pycheckers', '.pylintrc', '.style.yapf',
            '.clang-format', '.editorconfig'
    ]:
        comment = '#'
    if comment is not None:
        cfg = (f'{comment} THIS FILE WAS AUTOGENERATED; DO NOT EDIT.\n'
               f'{comment} Source: {src}.\n\n' + cfg)

    with dst.open('w') as outfile:
        outfile.write(cfg)


def _filter_tool_config(cfg: str) -> str:
    import textwrap
    from efrotools import getconfig

    # Stick project-root wherever they want.
    cfg = cfg.replace('__EFRO_PROJECT_ROOT__', str(PROJROOT))

    # Short project name.
    short_names = {
        'ballistica-internal': 'ba-int',
        'ballistica': 'ba',
        'ballistica-master-server-2.0': 'bamaster2',
        'ballistica-master-server': 'bamaster',
        'ballistica-server-node': 'baservnode',
    }
    shortname = short_names.get(PROJROOT.name, PROJROOT.name)
    cfg = cfg.replace('__EFRO_PROJECT_SHORTNAME__', shortname)

    mypy_standard_settings = textwrap.dedent("""
    # We don't want all of our plain scripts complaining
    # about __main__ being redefined.
    scripts_are_modules = True

    # Try to be as strict as we can about using types everywhere.
    warn_unused_ignores = True
    warn_no_return = True
    warn_return_any = True
    warn_redundant_casts = True
    warn_unreachable = True
    warn_unused_configs = True
    disallow_incomplete_defs = True
    disallow_untyped_defs = True
    disallow_untyped_decorators = True
    disallow_untyped_calls = True
    disallow_any_unimported = True
    disallow_subclassing_any = True
    strict_equality = True
    local_partial_types = True
    no_implicit_reexport = True
    """).strip()

    cfg = cfg.replace('__EFRO_MYPY_STANDARD_SETTINGS__',
                      mypy_standard_settings)

    # Gen a pylint init to set up our python paths:
    pylint_init_tag = '__EFRO_PYLINT_INIT__'
    if pylint_init_tag in cfg:
        pypaths = getconfig(PROJROOT).get('python_paths')
        if pypaths is None:
            raise RuntimeError('python_paths not set in project config')
        cstr = "init-hook='import sys;"
        for path in pypaths:
            cstr += f" sys.path.append('{PROJROOT}/{path}');"
        cstr += "'"
        cfg = cfg.replace(pylint_init_tag, cstr)
    return cfg


def sync_all() -> None:
    """Runs full syncs between all efrotools projects.

    This list is defined in the EFROTOOLS_SYNC_PROJECTS env var.
    This assumes that there is a 'sync-full' and 'sync-list' Makefile target
    under each project.
    """
    import os
    import subprocess
    import concurrent.futures
    from efro.error import CleanError
    from efro.terminal import Clr
    print(f'{Clr.BLD}Updating formatting for all projects...{Clr.RST}')
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
                print(Clr.BLD + 'Running sync pass 1:'
                      ' (ensures all changes at dsts are pushed to src)' +
                      Clr.RST)
            else:
                print(Clr.BLD + 'Running sync pass 2:'
                      ' (ensures latest src is pulled to all dsts)' + Clr.RST)
            for project in projects_str.split(':'):
                cmd = f'cd "{project}" && make sync-full'
                print(cmd)
                subprocess.run(cmd, shell=True, check=True)
        print(Clr.BLD + 'Sync-all successful!' + Clr.RST)


def sync() -> None:
    """Runs standard syncs between this project and others."""
    from efrotools import getconfig
    from efrotools.sync import Mode, SyncItem, run_standard_syncs
    mode = Mode(sys.argv[2]) if len(sys.argv) > 2 else Mode.PULL

    # Load sync-items from project config and run them
    sync_items = [
        SyncItem(**i) for i in getconfig(PROJROOT).get('sync_items', [])
    ]
    run_standard_syncs(PROJROOT, mode, sync_items)


def compile_python_files() -> None:
    """Compile pyc files for packaging.

    This creates hash-based PYC files in opt level 1 with hash checks
    defaulting to off, so we don't have to worry about timestamps or
    loading speed hits due to hash checks. (see PEP 552).
    We just need to tell modders that they'll need to clear these
    cache files out or turn on debugging mode if they want to tweak
    the built-in scripts directly (or go through the asset build system which
    properly recreates the .pyc files).
    """
    import os
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
    import os
    import platform
    import subprocess
    from efrotools import getconfig, PYTHON_BIN
    from efro.error import CleanError

    # Grab our python paths for the project and stuff them in PYTHONPATH.
    pypaths = getconfig(PROJROOT).get('python_paths')
    if pypaths is None:
        raise CleanError('python_paths not found in project config.')

    separator = ';' if platform.system() == 'Windows' else ':'
    os.environ['PYTHONPATH'] = separator.join(pypaths)

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
    from efro.terminal import Clr

    @dataclass
    class _Entry:
        kind: str
        line: int
        title: str

    if len(sys.argv) != 3:
        raise RuntimeError('Expected exactly one filename arg.')

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
            print(Clr.MAG + entry.title + Clr.BLU +
                  _docstr(lines, entry.line) + Clr.RST)


def echo() -> None:
    """Echo with support for efro.terminal.Clr args (RED, GRN, BLU, etc).

    Prints a Clr.RST at the end so that can be omitted.
    """
    from efro.terminal import Clr
    clrnames = {n for n in dir(Clr) if n.isupper() and not n.startswith('_')}
    first = True
    out: List[str] = []
    for arg in sys.argv[2:]:
        if arg in clrnames:
            out.append(getattr(Clr, arg))
        else:
            if not first:
                out.append(' ')
            first = False
            out.append(arg)
    out.append(Clr.RST)
    print(''.join(out))
