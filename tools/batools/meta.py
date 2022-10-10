# Released under the MIT License. See LICENSE for details.
#
"""Functionality used in meta-builds (dynamically generated sources)."""
from __future__ import annotations

import os
import json
from typing import TYPE_CHECKING

from efro.terminal import Clr

if TYPE_CHECKING:
    pass


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
    """Generate binding.inc file."""

    out_dir = os.path.dirname(out_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # Pull all lines in the embedded list and split into py and c++ names.
    with open(in_path, encoding='utf-8') as infile:
        pycode = infile.read()

    # Double quotes cause errors.
    if '"' in pycode:
        raise Exception('bindings file can\'t contain double quotes.')
    lines = [
        l.strip().split(',  # ')
        for l in pycode.splitlines()
        if l.startswith('        ')
    ]
    if not all(len(l) == 2 for l in lines):
        raise Exception('malformatted data')

    # Our C++ code first execs our input as a string.
    ccode = '{const char* bindcode = ' + repr(pycode).replace("'", '"') + ';'
    ccode += (
        '\nPyObject* result = PyRun_String(bindcode, Py_file_input,'
        ' bootstrap_context.get(), bootstrap_context.get());\n'
        'if (result == nullptr) {\n'
        '  PyErr_PrintEx(0);\n'
        '  // Use a standard error to avoid a useless stack trace.\n'
        '  throw std::logic_error("Error fetching required Python'
        ' objects.");\n'
        '}\n'
    )

    # Then it grabs the function that was defined and runs it.
    ccode += (
        'PyObject* bindvals = PythonCommand("get_binding_values()",'
        ' "<get_binding_values>")'
        '.RunReturnObj(true, bootstrap_context.get());\n'
        'if (bindvals == nullptr) {\n'
        '  // Use a standard error to avoid a useless stack trace.\n'
        '  throw std::logic_error("Error binding required Python'
        ' objects.");\n'
        '}\n'
    )

    # Then it pulls the individual values out of the returned tuple.
    for i, line in enumerate(lines):
        storecmd = (
            'StoreObjCallable'
            if line[1].endswith('Class') or line[1].endswith('Call')
            else 'StoreObj'
        )
        ccode += (
            f'{storecmd}(ObjID::{line[1]},'
            f' PyTuple_GET_ITEM(bindvals, {i}), true);\n'
        )

    ccode += 'Py_DECREF(bindvals);\n}\n'
    pretty_path = os.path.abspath(out_path)
    if pretty_path.startswith(projroot + '/'):
        pretty_path = pretty_path[len(projroot) + 1 :]
    print(f'Meta-building {Clr.BLD}{pretty_path}{Clr.RST}')
    with open(out_path, 'w', encoding='utf-8') as outfile:
        outfile.write(ccode)
