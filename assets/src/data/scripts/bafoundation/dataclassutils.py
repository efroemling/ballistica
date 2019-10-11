# Copyright (c) 2011-2019 Eric Froemling
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
"""Utilities for working with dataclasses."""

from __future__ import annotations

# import dataclasses

# def dataclass_from_dict(cls, data):
#     print("Creating dataclass from dict", cls, data, type(cls))
#     try:
#         print("FLDTYPES", [field.type for field in dataclasses.fields(cls)])
#         fieldtypes = {
#             field.name: field.type
#             for field in dataclasses.fields(cls)
#         }
#         print("GOT FIELDTYPES", fieldtypes)
#         # print("GOT", cls.__name__, fieldtypes, data)
#         args = {
#                 field: dataclass_from_dict(fieldtypes[field], data[field])
#                 for field in data
#             }
#         print("CALCED ARGS", args)
#         val = cls(
#             **{
#                 field: dataclass_from_dict(fieldtypes[field], data[field])
#                 for field in data
#             })
#         print("CREATED", val)
#         return val
#     except Exception as exc:
#         print("GOT EXC", exc)
#         return data  # Not a dataclass field
