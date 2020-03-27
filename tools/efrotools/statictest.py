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
"""Functionality for harnessing mypy for static type checking in unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
import tempfile
import os
import subprocess
import logging

if TYPE_CHECKING:
    from typing import Any, Type, Dict, Optional, List, Union

# Global state:
# We maintain a single temp dir where our mypy cache and our temp
# test files live. Every time we are asked to static-check a line
# in a file we haven't seen yet, we copy it into the temp dir,
# filter it a bit to add reveal_type() statements, and run mypy on it.
# The temp dir should tear itself down when Python exits.
_tempdir: Optional[tempfile.TemporaryDirectory] = None
_statictestfiles: Dict[str, StaticTestFile] = {}
_nextfilenum: int = 1


class StaticTestFile:
    """A file which has been statically tested via mypy."""

    def __init__(self, filename: str):
        # pylint: disable=global-statement, invalid-name
        global _tempdir, _nextfilenum
        # pylint: enable=global-statement, invalid-name

        from efrotools import PYTHON_BIN

        self._filename = filename
        self.modulename = f'temp{_nextfilenum}'
        _nextfilenum += 1

        # Types we *want* for lines
        self.linetypes_wanted: Dict[int, str] = {}

        # Types Mypy gave us for lines
        self.linetypes_mypy: Dict[int, str] = {}

        print(f"Running Mypy static testing on \"{filename}\"...")
        with open(filename, 'r') as infile:
            fdata = infile.read()

        # Make sure we're running where the config is..
        if not os.path.isfile('.mypy.ini'):
            raise RuntimeError('.mypy.ini not found where expected.')

        # Create a single shared temp dir
        # (so that we can recycle our mypy cache).
        if _tempdir is None:
            _tempdir = tempfile.TemporaryDirectory()
            # print(f"Created temp dir at {_tempdir.name}")

        # Copy our file into the temp dir with a unique name, find all
        # instances of static_type_equals(), and run mypy type checks
        # in those places to get static types.
        tempfilepath = os.path.join(_tempdir.name, self.modulename + '.py')
        with open(tempfilepath, 'w') as outfile:
            outfile.write(self.filter_file_contents(fdata))
        results = subprocess.run(
            [
                PYTHON_BIN, '-m', 'mypy', '--no-error-summary',
                '--config-file', '.mypy.ini', '--cache-dir',
                os.path.join(_tempdir.name, '.mypy_cache'), tempfilepath
            ],
            capture_output=True,
            check=False,
        )

        # HMM; it seems we always get an errored return code due to
        # our use of reveal_type() so we can't look at that.
        # However we can look for error notices in the output and fail there.
        lines = results.stdout.decode().splitlines()
        for line in lines:
            if ': error: ' in line:
                print("Full mypy output:\n", results.stdout.decode())
                raise RuntimeError('Errors detected in mypy output.')
            if 'Revealed type is ' in line:
                finfo = line.split(' ')[0]
                fparts = finfo.split(':')
                assert len(fparts) == 3
                linenumber = int(fparts[1])
                linetype = line.split('Revealed type is ')[-1][1:-1]
                self.linetypes_mypy[linenumber] = linetype

    def filter_file_contents(self, contents: str) -> str:
        """Filter the provided file contents and take note of type checks."""
        import ast
        lines = contents.splitlines()
        lines_out: List[str] = []
        for lineno, line in enumerate(lines):
            if 'static_type_equals(' not in line:
                lines_out.append(line)
            else:

                # Find the location of the end parentheses.
                assert ')' in line
                endparen = len(line) - 1
                while line[endparen] != ')':
                    endparen -= 1

                # Find the offset to the start of the line.
                offset = 0
                while line[offset] == ' ':
                    offset += 1

                # Parse this line as AST - we should find an assert
                # statement containing a static_type_equals() call
                # with 2 args.
                try:
                    tree = ast.parse(line[offset:])
                except Exception:
                    raise RuntimeError(
                        f"{self._filename} line {lineno+1}: unable to "
                        f"parse line (static_type_equals() call cannot"
                        f" be split across lines).") from None
                assert isinstance(tree, ast.Module)
                if (len(tree.body) != 1
                        or not isinstance(tree.body[0], ast.Assert)):
                    raise RuntimeError(
                        f"{self._filename} line {lineno+1}: expected "
                        f" a single assert statement.")
                assertnode = tree.body[0]
                callnode = assertnode.test
                if (not isinstance(callnode, ast.Call)
                        or not isinstance(callnode.func, ast.Name)
                        or callnode.func.id != 'static_type_equals'
                        or len(callnode.args) != 2):
                    raise RuntimeError(
                        f"{self._filename} line {lineno+1}: expected "
                        f" a single static_type_equals() call with 2 args.")

                # Use the column offsets for the 2 args along with our end
                # paren offset to cut out the substrings representing the args.
                arg1 = line[callnode.args[0].col_offset +
                            offset:callnode.args[1].col_offset + offset]
                while arg1[-1] in (' ', ','):
                    arg1 = arg1[:-1]
                arg2 = line[callnode.args[1].col_offset + offset:endparen]

                # In our filtered file, replace the assert statement with
                # a reveal_type() for the var, and also take note of the
                # type they want it to equal.
                self.linetypes_wanted[lineno + 1] = arg2
                lines_out.append(' ' * offset + f'reveal_type({arg1})')

        return '\n'.join(lines_out) + '\n'


def static_type_equals(value: Any, statictype: Union[Type, str]) -> bool:
    """Check a type statically using mypy.

    If a string is passed as statictype, it is checked against the mypy
    output for an exact match.
    If a type is passed, various filtering may apply when searching for
    a match (for instance, if mypy outputs 'builtins.int*' it will match
    the 'int' type passed in as statictype).
    """
    import platform
    from inspect import getframeinfo, stack

    # NOTE: don't currently support windows here; just going to always
    # pass so we don't have to conditionalize all our individual test
    # locations.
    if platform.system() == 'Windows':
        logging.debug('static_type_equals not supported on windows;'
                      ' will always pass...')
        return True

    # We don't actually use there here; we pull them as strings from the src.
    del value

    # Get the filename and line number of the calling function.
    caller = getframeinfo(stack()[1][0])
    filename = caller.filename
    linenumber = caller.lineno

    if filename not in _statictestfiles:
        _statictestfiles[filename] = StaticTestFile(filename)
    testfile = _statictestfiles[filename]

    mypytype = testfile.linetypes_mypy[linenumber]

    if isinstance(statictype, str):
        # If they passed a string value as the statictype,
        # do a comparison with the exact mypy value.
        wanttype = statictype
    else:
        # If they passed a type object, things are a bit trickier because
        # mypy's name for the type might not match the name we pass it in with.
        # Try to do some filtering to minimize these differences...
        wanttype = testfile.linetypes_wanted[linenumber]
        del statictype

        # Do some filtering of Mypy types so we can compare
        # to simple python ones.

        # (ie: 'builtins.list[builtins.int*]' -> int)
        # Note to self: perhaps we'd want a fallback form where we can pass a
        # type as a string if we want to match the exact mypy value?...
        mypytype = mypytype.replace('*', '')
        mypytype = mypytype.replace('?', '')
        mypytype = mypytype.replace('builtins.int', 'int')
        mypytype = mypytype.replace('builtins.float', 'float')
        mypytype = mypytype.replace('builtins.list', 'List')
        mypytype = mypytype.replace('builtins.bool', 'bool')
        mypytype = mypytype.replace('typing.Sequence', 'Sequence')

        # So classes declared in the test file can be passed using base names.
        # ie: temp3.FooClass -> FooClass
        mypytype = mypytype.replace(testfile.modulename + '.', '')

    if wanttype != mypytype:
        print(f'Mypy type "{mypytype}" does not match '
              f'the desired type "{wanttype}" on line {linenumber}.')
        return False

    return True
