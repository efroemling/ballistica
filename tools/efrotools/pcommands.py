# Released under the MIT License. See LICENSE for details.
#
"""A set of lovely pcommands ready for use."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from efrotools import pcommand

if TYPE_CHECKING:
    pass


def _spelling(words: list[str]) -> None:
    from efrotools.code import sort_jetbrains_dict
    import os

    pcommand.disallow_in_batch()

    num_modded_dictionaries = 0
    for fname in [
        '.idea/dictionaries/ericf.xml',
        'ballisticakit-cmake/.idea/dictionaries/ericf.xml',
    ]:
        if not os.path.exists(fname):
            continue
        with open(fname, encoding='utf-8') as infile:
            lines = infile.read().splitlines()
        if lines[2] != '    <words>':
            raise RuntimeError('Unexpected dictionary format.')
        added_count = 0
        for word in words:
            line = f'      <w>{word.lower()}</w>'
            if line not in lines:
                lines.insert(3, line)
                added_count += 1

        with open(fname, 'w', encoding='utf-8') as outfile:
            outfile.write(sort_jetbrains_dict('\n'.join(lines)))

        print(f'Added {added_count} words to {fname}.')
        num_modded_dictionaries += 1
    print(f'Modified {num_modded_dictionaries} dictionaries.')


def requirements_upgrade() -> None:
    """Upgrade project requirements."""
    import os
    import tempfile
    import subprocess

    from efro.error import CleanError

    pcommand.disallow_in_batch()

    args = pcommand.get_args()

    if len(args) != 1:
        raise CleanError('Expected a single arg.')
    reqpath = args[0]

    with open(reqpath, encoding='utf-8') as infile:
        reqs = infile.read()

    # Operate on a temp file and compare against our existing so we don't
    # write unless it has changed.
    with tempfile.TemporaryDirectory() as tempdir:
        fname = os.path.join(tempdir, 'reqs')
        with open(fname, 'w', encoding='utf-8') as outfile:
            outfile.write(reqs)

        subprocess.run([sys.executable, '-m', 'pur', '-r', fname], check=True)

        # Sort lines.
        with open(fname, encoding='utf-8') as infile:
            reqs2 = infile.read().strip()
        reqs_new = (
            '\n'.join(sorted(reqs2.splitlines(), key=lambda l: l.lower()))
            + '\n'
        )

        if reqs_new != reqs:
            with open(reqpath, 'w', encoding='utf-8') as outfile:
                outfile.write(reqs_new)


def spelling_all() -> None:
    """Add all misspellings from a pycharm run."""
    import subprocess

    pcommand.disallow_in_batch()

    print('Running "make pycharm-full"...')
    lines = [
        line
        for line in subprocess.run(
            ['make', 'pycharm-full'], check=False, capture_output=True
        )
        .stdout.decode()
        .splitlines()
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

    pcommand.disallow_in_batch()

    _spelling(sys.argv[2:])


def xcodebuild() -> None:
    """Run xcodebuild with added smarts."""
    from efrotools.xcodebuild import XCodeBuild

    pcommand.disallow_in_batch()

    XCodeBuild(projroot=str(pcommand.PROJROOT), args=sys.argv[2:]).run()


def _xcodepath(executable: bool) -> str:
    import os
    from efro.error import CleanError
    from efrotools.xcodebuild import project_build_path

    pcommand.disallow_in_batch()

    if len(sys.argv) != 5:
        raise CleanError(
            'Expected 3 args: <xcode project path> <configuration name>'
        )
    project_path = os.path.abspath(sys.argv[2])
    scheme = sys.argv[3]
    configuration = sys.argv[4]
    return project_build_path(
        projroot=str(pcommand.PROJROOT),
        project_path=project_path,
        scheme=scheme,
        configuration=configuration,
        executable=executable,
    )


def xcodeshow() -> None:
    """Open folder containing xcode build in the finder."""
    import subprocess

    subprocess.run(['open', _xcodepath(executable=False)], check=True)


def xcoderun() -> None:
    """Run an xcode build in the terminal."""
    import subprocess

    path = _xcodepath(executable=True)
    subprocess.run(path, check=True)


def pyver() -> None:
    """Prints the Python version used by this project."""
    from efrotools.pyver import PYVER

    pcommand.disallow_in_batch()

    print(PYVER, end='')


def try_repeat() -> None:
    """Run a command with repeat attempts on failure.

    First arg is the number of retries; remaining args are the command.
    """
    import subprocess
    from efro.error import CleanError

    pcommand.disallow_in_batch()

    # We require one number arg and at least one command arg.
    if len(sys.argv) < 4:
        raise CleanError(
            'Expected a retry-count arg and at least one command arg'
        )
    try:
        repeats = int(sys.argv[2])
    except Exception:
        raise CleanError('Expected int as first arg') from None
    if repeats < 0:
        raise CleanError('Retries must be >= 0')
    cmd = sys.argv[3:]
    for i in range(repeats + 1):
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            return
        print(
            f'try_repeat attempt {i + 1} of {repeats + 1} failed for {cmd}.',
            file=sys.stderr,
            flush=True,
        )
    raise CleanError(f'Command failed {repeats + 1} time(s): {cmd}')


def check_clean_safety() -> None:
    """Ensure all files are are added to git or in gitignore.

    Use to avoid losing work if we accidentally do a clean without
    adding something.
    """
    import os
    import subprocess
    from efro.error import CleanError

    pcommand.disallow_in_batch()

    if len(sys.argv) != 2:
        raise CleanError('invalid arguments')

    # Make sure we wouldn't be deleting anything not tracked by git
    # or ignored.
    output = subprocess.check_output(
        ['git', 'status', '--porcelain=v2']
    ).decode()
    if any(line.startswith('?') for line in output.splitlines()):
        raise CleanError(
            'Untracked file(s) found; aborting.'
            ' (see "git status" from "'
            + os.getcwd()
            + '")  Either \'git add\' them, add them to .gitignore,'
            ' or remove them and try again.'
        )


def gen_empty_py_init() -> None:
    """Generate an empty __init__.py for a package dir.

    Used as part of meta builds.
    """
    from pathlib import Path

    from efro.terminal import Clr
    from efro.error import CleanError

    pcommand.disallow_in_batch()

    if len(sys.argv) != 3:
        raise CleanError('Expected a single path arg.')

    outpath = Path(sys.argv[2])
    outpath.parent.mkdir(parents=True, exist_ok=True)
    print(f'Meta-building {Clr.BLD}{outpath}{Clr.RST}')
    with open(outpath, 'w', encoding='utf-8') as outfile:
        outfile.write('# This file is autogenerated; do not hand-edit.\n')


def formatcode() -> None:
    """Format all of our C/C++/etc. code."""
    import efrotools.code

    pcommand.disallow_in_batch()

    full = '-full' in sys.argv
    efrotools.code.format_project_cpp_files(pcommand.PROJROOT, full)


def formatscripts() -> None:
    """Format all of our Python/etc. code."""
    import efrotools.code

    pcommand.disallow_in_batch()

    full = '-full' in sys.argv
    efrotools.code.format_project_python_files(pcommand.PROJROOT, full)


def formatmakefile() -> None:
    """Format the main makefile."""
    from efrotools.makefile import Makefile

    with open('Makefile', encoding='utf-8') as infile:
        original = infile.read()

    pcommand.disallow_in_batch()

    formatted = Makefile(original).get_output()

    # Only write if it changed.
    if formatted != original:
        with open('Makefile', 'w', encoding='utf-8') as outfile:
            outfile.write(formatted)


def cpplint() -> None:
    """Run lint-checking on all code deemed lint-able."""
    import efrotools.code

    pcommand.disallow_in_batch()

    full = '-full' in sys.argv
    efrotools.code.check_cpplint(pcommand.PROJROOT, full)


def scriptfiles() -> None:
    """List project script files.

    Pass -lines to use newlines as separators. The default is spaces.
    """
    import efrotools.code

    pcommand.disallow_in_batch()

    paths = efrotools.code.get_script_filenames(projroot=pcommand.PROJROOT)
    assert not any(' ' in path for path in paths)
    if '-lines' in sys.argv:
        print('\n'.join(paths))
    else:
        print(' '.join(paths))


def pylint() -> None:
    """Run pylint checks on our scripts."""
    import efrotools.code

    pcommand.disallow_in_batch()

    full = '-full' in sys.argv
    fast = '-fast' in sys.argv
    efrotools.code.pylint(pcommand.PROJROOT, full, fast)


def pylint_files() -> None:
    """Run pylint checks on provided filenames."""
    from efro.terminal import Clr
    from efro.error import CleanError
    import efrotools.code

    pcommand.disallow_in_batch()

    if len(sys.argv) < 3:
        raise CleanError('Expected at least 1 filename arg.')

    filenames = sys.argv[2:]
    efrotools.code.runpylint(pcommand.PROJROOT, filenames)
    print(f'{Clr.GRN}Pylint Passed.{Clr.RST}')


def mypy() -> None:
    """Run mypy checks on our scripts."""
    import efrotools.code

    pcommand.disallow_in_batch()

    full = '-full' in sys.argv
    efrotools.code.mypy(pcommand.PROJROOT, full)


def mypy_files() -> None:
    """Run mypy checks on provided filenames."""
    from efro.terminal import Clr
    from efro.error import CleanError
    import efrotools.code

    pcommand.disallow_in_batch()

    if len(sys.argv) < 3:
        raise CleanError('Expected at least 1 filename arg.')

    filenames = sys.argv[2:]
    try:
        efrotools.code.mypy_files(pcommand.PROJROOT, filenames)
        print(f'{Clr.GRN}Mypy Passed.{Clr.RST}')
    except Exception as exc:
        raise CleanError('Mypy Failed.') from exc


def dmypy() -> None:
    """Run mypy checks on our scripts using the mypy daemon."""
    import efrotools.code

    pcommand.disallow_in_batch()

    efrotools.code.dmypy(pcommand.PROJROOT)


def pycharm() -> None:
    """Run PyCharm checks on our scripts."""
    import efrotools.code

    pcommand.disallow_in_batch()

    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    efrotools.code.check_pycharm(pcommand.PROJROOT, full, verbose)


def clioncode() -> None:
    """Run CLion checks on our code."""
    import efrotools.code

    pcommand.disallow_in_batch()

    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    efrotools.code.check_clioncode(pcommand.PROJROOT, full, verbose)


def androidstudiocode() -> None:
    """Run Android Studio checks on our code."""
    import efrotools.code

    pcommand.disallow_in_batch()

    full = '-full' in sys.argv
    verbose = '-v' in sys.argv
    efrotools.code.check_android_studio(pcommand.PROJROOT, full, verbose)


def tool_config_install() -> None:
    """Install a tool config file (with some filtering)."""
    from pathlib import Path

    from efro.error import CleanError

    import efrotools.toolconfig

    pcommand.disallow_in_batch()

    if len(sys.argv) != 4:
        raise CleanError('expected 2 args')

    src = Path(sys.argv[2])
    dst = Path(sys.argv[3])

    efrotools.toolconfig.install_tool_config(pcommand.PROJROOT, src, dst)


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

    pcommand.disallow_in_batch()

    print(f'{Clr.BLD}Updating formatting for all projects...{Clr.RST}')
    projects_str = os.environ.get('EFROTOOLS_SYNC_PROJECTS')
    if projects_str is None:
        raise CleanError('EFROTOOL_SYNC_PROJECTS is not defined.')
    projects = projects_str.split(':')

    def _format_project(fproject: str) -> None:
        fcmd = f'cd "{fproject}" && make format'
        # print(fcmd)
        subprocess.run(fcmd, shell=True, check=True)

    # No matter what we're doing (even if just listing), run formatting
    # in all projects before beginning. Otherwise if we do a sync and then
    # a preflight we'll often wind up getting out-of-sync errors due to
    # formatting changing after the sync.
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(projects)
    ) as executor:
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
                print(
                    f'{Clr.BLD}Running sync pass 1'
                    f' (ensures all changes at dsts are pushed to src):'
                    f'{Clr.RST}'
                )
            else:
                print(
                    f'{Clr.BLD}Running sync pass 2'
                    f' (ensures latest src is pulled to all dsts):{Clr.RST}'
                )
            for project in projects_str.split(':'):
                cmd = f'cd "{project}" && make sync-full'
                subprocess.run(cmd, shell=True, check=True)
        print(Clr.BLD + 'Sync-all successful!' + Clr.RST)


def sync() -> None:
    """Runs standard syncs between this project and others."""
    from efrotools.project import getprojectconfig
    from efrotools.sync import Mode, SyncItem, run_standard_syncs

    pcommand.disallow_in_batch()

    mode = Mode(sys.argv[2]) if len(sys.argv) > 2 else Mode.PULL

    # Load sync-items from project config and run them
    sync_items = [
        SyncItem(**i)
        for i in getprojectconfig(pcommand.PROJROOT).get('sync_items', [])
    ]
    run_standard_syncs(pcommand.PROJROOT, mode, sync_items)


def copy_win_extra_file() -> None:
    """Copy a windows extra file."""
    _simple_file_copy('Copying file')


def compile_language_file() -> None:
    """Compile a language file."""
    _simple_file_copy('Compiling language json')


def compile_mesh_file() -> None:
    """Compile a mesh file."""
    import os
    import subprocess
    from efro.error import CleanError

    args = pcommand.get_args()
    if len(args) != 3:
        raise CleanError('Expected 3 args.')

    src, dst, makebob = args

    # Show project-relative paths when possible.
    relpath = os.path.abspath(dst).removeprefix(f'{pcommand.PROJROOT}/')
    pcommand.clientprint(f'Compiling mesh: {relpath}')

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run([makebob, src, dst], check=True)

    assert os.path.exists(dst)


def compile_collision_mesh_file() -> None:
    """Compile a mesh file."""
    import os
    import subprocess
    from efro.error import CleanError

    args = pcommand.get_args()
    if len(args) != 3:
        raise CleanError('Expected 3 args.')

    src, dst, makebob = args

    # Show project-relative paths when possible.
    relpath = os.path.abspath(dst).removeprefix(f'{pcommand.PROJROOT}/')
    pcommand.clientprint(f'Compiling collision mesh: {relpath}')

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.run([makebob, src, dst], check=True)

    assert os.path.exists(dst)


def compile_python_file() -> None:
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

    from efro.error import CleanError

    args = pcommand.get_args()
    if len(args) != 1:
        raise CleanError('Expected a single arg.')
    fname = args[0]

    # Show project-relative path when possible.
    relpath = os.path.abspath(fname).removeprefix(f'{pcommand.PROJROOT}/')
    pcommand.clientprint(f'Compiling script: {relpath}')

    py_compile.compile(
        fname,
        doraise=True,
        optimize=1,
        invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
    )


def copy_python_file() -> None:
    """Copy Python files for packaging."""
    _simple_file_copy('Copying python file', make_unwritable=True)


def _simple_file_copy(msg: str, make_unwritable: bool = False) -> None:
    import os
    import shutil
    from efro.error import CleanError

    args = pcommand.get_args()
    if len(args) != 2:
        raise CleanError('Expected 2 args.')

    src, dst = args

    relpath = os.path.abspath(dst).removeprefix(f'{pcommand.PROJROOT}/')
    pcommand.clientprint(f'{msg}: {relpath}')

    # If we're making built files unwritable, we need to blow
    # away exiting ones to allow this to succeed.
    if make_unwritable:
        if os.path.exists(dst):
            os.unlink(dst)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)

    assert os.path.exists(dst)

    # Make built files unwritable to save myself from accidentally
    # doing editing there and then blowing away my work.
    if make_unwritable:
        os.chmod(dst, 0o444)


def compile_font_file() -> None:
    """Compile a font file."""
    _simple_file_copy('Compiling font')


def pytest() -> None:
    """Run pytest with project environment set up properly."""
    import os
    import platform
    import subprocess
    from efrotools.project import getprojectconfig
    from efro.error import CleanError

    pcommand.disallow_in_batch()

    # Grab our python paths for the project and stuff them in PYTHONPATH.
    pypaths = getprojectconfig(pcommand.PROJROOT).get('python_paths')
    if pypaths is None:
        raise CleanError('python_paths not found in project config.')

    separator = ';' if platform.system() == 'Windows' else ':'
    os.environ['PYTHONPATH'] = separator.join(pypaths)

    # Also tell Python interpreters not to write __pycache__ dirs everywhere
    # which can screw up our builds.
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

    # Let's flip on dev mode to hopefully be informed on more bad stuff
    # happening.  https://docs.python.org/3/library/devmode.html
    os.environ['PYTHONDEVMODE'] = '1'

    # Do the thing.
    results = subprocess.run(
        [sys.executable, '-m', 'pytest'] + sys.argv[2:], check=False
    )
    if results.returncode != 0:
        sys.exit(results.returncode)


def makefile_target_list() -> None:
    """Prints targets in a makefile.

    Takes a single argument: a path to a Makefile.
    """
    from dataclasses import dataclass
    from efro.error import CleanError
    from efro.terminal import Clr

    pcommand.disallow_in_batch()

    @dataclass
    class _Entry:
        kind: str
        line: int
        title: str

    if len(sys.argv) != 3:
        raise CleanError('Expected exactly one filename arg.')

    with open(sys.argv[2], encoding='utf-8') as infile:
        lines = infile.readlines()

    def _docstr(lines2: list[str], linenum: int) -> str:
        doc = ''
        j = linenum - 1
        while j >= 0 and lines2[j].startswith('#'):
            doc = lines2[j][1:].strip()
            j -= 1
        if doc != '':
            return ' - ' + doc
        return doc

    print(
        '----------------------\n'
        'Available Make Targets\n'
        '----------------------'
    )

    entries: list[_Entry] = []
    for i, line in enumerate(lines):
        # Targets.
        if (
            ':' in line
            and line.split(':')[0].replace('-', '').replace('_', '').isalnum()
            and not line.startswith('_')
        ):
            entries.append(
                _Entry(kind='target', line=i, title=line.split(':')[0])
            )

        # Section titles.
        if (
            line.startswith('#  ')
            and line.endswith('  #\n')
            and len(line.split()) > 2
        ):
            entries.append(
                _Entry(kind='section', line=i, title=line[1:-2].strip())
            )

    for i, entry in enumerate(entries):
        if entry.kind == 'section':
            # Don't print headers for empty sections.
            if i + 1 >= len(entries) or entries[i + 1].kind == 'section':
                continue
            print('\n' + entry.title + '\n' + '-' * len(entry.title))
        elif entry.kind == 'target':
            print(
                Clr.MAG
                + entry.title
                + Clr.BLU
                + _docstr(lines, entry.line)
                + Clr.RST
            )


def echo() -> None:
    """Echo with support for efro.terminal.Clr args (RED, GRN, BLU, etc).

    Prints a Clr.RST at the end so that can be omitted.
    """
    clr = pcommand.clr()

    clrnames = {n for n in dir(clr) if n.isupper() and not n.startswith('_')}
    first = True
    out: list[str] = []
    last_was_tag = False
    for arg in pcommand.get_args():
        if arg in clrnames:
            out.append(getattr(clr, arg))
            last_was_tag = True
        else:
            # Special case: punctuation by itself after a tag doesn't
            # get a space before it.
            if not first and not (last_was_tag and arg in ('.', '?', '!')):
                out.append(' ')
            first = False
            last_was_tag = False
            out.append(arg)
    out.append(clr.RST)
    pcommand.clientprint(''.join(out))


def urandom_pretty() -> None:
    """Spits out urandom bytes formatted for source files."""
    # Note; this is not especially efficient. It should probably be rewritten
    # if ever needed in a performance-sensitive context.
    import os
    from efro.error import CleanError

    pcommand.disallow_in_batch()

    if len(sys.argv) not in (3, 4):
        raise CleanError(
            'Expected one arg (count) and possibly two (line len).'
        )
    size = int(sys.argv[2])
    linemax = 72 if len(sys.argv) < 4 else int(sys.argv[3])

    val = os.urandom(size)
    lines: list[str] = []
    line = b''

    for i in range(len(val)):
        char = val[i : i + 1]
        thislinelen = len(repr(line + char))
        if thislinelen > linemax:
            lines.append(repr(line))
            line = b''
        line += char
    if line:
        lines.append(repr(line))

    bstr = '\n'.join(str(l) for l in lines)
    print(f'({bstr})')


def tweak_empty_py_files() -> None:
    """Find any zero-length Python files and make them length 1."""
    from efro.error import CleanError
    import efrotools.pybuild

    pcommand.disallow_in_batch()

    if len(sys.argv) != 3:
        raise CleanError('Expected exactly 1 path arg.')
    efrotools.pybuild.tweak_empty_py_files(sys.argv[2])


def make_ensure() -> None:
    """Make sure a makefile target is up-to-date.

    This can technically be done by simply `make --question`, but this
    has some extra bells and whistles such as printing some of the commands
    that would run.
    Can be useful to run after cloud-builds to ensure the local results
    consider themselves up-to-date.
    """
    # pylint: disable=too-many-locals
    from efro.error import CleanError
    from efro.terminal import Clr
    import subprocess

    pcommand.disallow_in_batch()

    dirpath: str | None = None
    args = sys.argv[2:]
    if '--dir' in args:
        argindex = args.index('--dir')
        dirpath = args[argindex + 1]
        del args[argindex : argindex + 2]

    if len(args) not in (0, 1):
        raise CleanError('Expected zero or one target args.')
    target = args[0] if args else None

    cmd = ['make', '--no-print-directory', '--dry-run']
    if target is not None:
        cmd.append(target)
    results = subprocess.run(cmd, check=False, capture_output=True, cwd=dirpath)
    out = results.stdout.decode()
    err = results.stderr.decode()
    if results.returncode != 0:
        print(f'Failed command stdout:\n{out}\nFailed command stderr:\n{err}')
        raise CleanError(f"Command failed during make_ensure: '{cmd}'.")

    targetname: str = '<default>' if target is None else target
    lines = out.splitlines()
    in_str = '' if dirpath is None else f"in directory '{dirpath}' "
    if len(lines) == 1 and 'Nothing to be done for ' in lines[0]:
        print(f"make_ensure: '{targetname}' target {in_str}is up to date.")
    else:
        maxlines = 20
        if len(lines) > maxlines:
            outlines = '\n'.join(
                lines[:maxlines] + [f'(plus {len(lines)-maxlines} more lines)']
            )
        else:
            outlines = '\n'.join(lines)

        print(
            f"make_ensure: '{targetname}' target {in_str}"
            f'is out of date; would run:\n\n'
            '-------------------------- MAKE-ENSURE COMMANDS BEGIN '
            f'--------------------------\n{Clr.YLW}'
            f'{outlines}{Clr.RST}\n'
            '--------------------------- MAKE-ENSURE COMMANDS END '
            '---------------------------\n'
        )
        raise CleanError(
            f"make_ensure: '{targetname}' target {in_str}is out of date."
        )


def make_target_debug() -> None:
    """Debug makefile src/target mod times given src and dst path.

    Built to debug stubborn Makefile targets that insist on being
    rebuilt just after being built via a cloud target.
    """
    import os
    import datetime

    from efro.error import CleanError

    pcommand.disallow_in_batch()

    # from efro.util import ago_str, utc_now

    args = sys.argv[2:]
    if len(args) != 2:
        raise CleanError('Expected 2 args.')

    def _utc_mod_time(path: str) -> datetime.datetime:
        mtime = os.path.getmtime(path)
        mdtime = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc)
        # mdtime.replace(tzinfo=datetime.timezone.utc)
        return mdtime

    # srcname = os.path.basename(args[0])
    # dstname = os.path.basename(args[1])
    srctime = _utc_mod_time(args[0])
    dsttime = _utc_mod_time(args[1])
    # now = utc_now()
    # src_ago = ago_str(srctime, maxparts=3, decimals=2, now=now)
    # dst_ago = ago_str(dsttime, maxparts=3, decimals=2, now=now)
    srctimestr = (
        f'{srctime.hour}:{srctime.minute}:{srctime.second}:'
        f'{srctime.microsecond}'
    )
    dsttimestr = (
        f'{dsttime.hour}:{dsttime.minute}:{dsttime.second}:'
        f'{dsttime.microsecond}'
    )
    print(f'SRC modified at {srctimestr}.')
    print(f'DST modified at {dsttimestr}.')
