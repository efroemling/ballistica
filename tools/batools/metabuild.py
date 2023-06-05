# Released under the MIT License. See LICENSE for details.
#
"""Functionality used in meta-builds (dynamically generated sources)."""
from __future__ import annotations

import os
import json

from efro.terminal import Clr

# Can be plugged into hashes/etc to give us a convenient way to blow away
# all built meta output on CI/etc. (by incrementing this value).
META_BUILD_MAGIC_NUMBER = 1


def gen_flat_data_code(
    projroot: str, in_path: str, out_path: str, var_name: str
) -> None:
    """Generate a C++ include file from a Python file."""

    out_dir = os.path.dirname(out_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(in_path, 'rb') as infileb:
        svalin = infileb.read()

    # JSON should do the trick for us here as far as char escaping/etc.
    # There's corner cases where it can differ from C strings but in this
    # simple case we shouldn't run into them.
    sval_out = f'const char* {var_name} ='

    # Store in ballistica's simple xor encryption to at least
    # slightly slow down hackers.
    sval = svalin

    sval1: bytes | None
    sval1 = sval
    while sval1:
        sval_out += ' ' + json.dumps(sval1[:1000].decode())
        sval1 = sval1[1000:]
    sval_out += ';\n'

    pretty_path = os.path.abspath(out_path)
    if pretty_path.startswith(projroot + '/'):
        pretty_path = pretty_path[len(projroot) + 1 :]
    print(f'Meta-building {Clr.BLD}{pretty_path}{Clr.RST}')
    with open(out_path, 'w', encoding='utf-8') as outfile:
        outfile.write(sval_out)


def gen_binding_code(projroot: str, in_path: str, out_path: str) -> None:
    """Generate binding_foo.inc file."""

    out_dir = os.path.dirname(out_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(in_path, encoding='utf-8') as infile:
        pycode = infile.read()

    # Double quotes cause errors.
    if '"' in pycode:
        raise RuntimeError('bindings file can\'t contain double quotes.')

    # Look for all lines associating some Python value with a constant.
    entries = [
        l.strip().split(',  # ')
        for l in pycode.splitlines()
        if l.startswith('    ') and '#' in l
    ]
    if not all(len(l) == 2 for l in entries):
        raise RuntimeError('malformatted data.')

    # Our C++ code first execs our input as a string.
    ccode = '{\n' f'// Python code from {in_path}:\n' 'const char* bindcode ='

    for line in pycode.splitlines():
        ccode += f'\n  "{line}\\n"'
    ccode += (
        ';\n'
        '\n'
        '// Exec the Python code in an empty context.\n'
        'auto ctx = PythonRef::Stolen(PyDict_New());\n'
    )

    ccode += (
        'bool success = PythonCommand(bindcode, "'
        + os.path.basename(in_path)
        + '").Exec(true,'
        ' *ctx, *ctx);\n'
        'if (!success) {\n'
        '  FatalError("Error fetching required Python objects.");\n'
        '}\n'
    )

    # Then it grabs the 'values' var that should have been defined.
    ccode += (
        '\n'
        "// Grab the 'values' list that the binding code created.\n"
        'auto bindvals = ctx.DictGetItem("values");\n'
        'if (!bindvals.Exists() || !PyList_Check(*bindvals)) {\n'
        '  FatalError("Error binding required Python objects.");\n'
        '}\n'
        '\n'
        '// Pull our various obj_ values from the values list.\n'
    )

    # Then it pulls the individual values out of the returned tuple.
    for i, entry in enumerate(entries):
        storecmd = (
            'objs_.StoreCallable'
            if entry[1].endswith('Class') or entry[1].endswith('Call')
            else 'objs_.Store'
        )
        ccode += (
            f'{storecmd}(ObjID::{entry[1]},'
            f' PyList_GET_ITEM(bindvals.Get(), {i}));\n'
        )

    ccode += '}\n'
    pretty_path = os.path.abspath(out_path)
    if pretty_path.startswith(projroot + '/'):
        pretty_path = pretty_path[len(projroot) + 1 :]
    print(f'Meta-building {Clr.BLD}{pretty_path}{Clr.RST}')
    with open(out_path, 'w', encoding='utf-8') as outfile:
        outfile.write(ccode)
