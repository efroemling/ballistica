# Copyright (c) 2011-2019 Eric Froemling
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
