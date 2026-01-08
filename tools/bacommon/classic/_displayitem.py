# Released under the MIT License. See LICENSE for details.
#
"""Display-item bits of classic."""

# from __future__ import annotations

# from enum import Enum
# from typing import assert_never, Annotated, override
# from dataclasses import dataclass

# from efro.dataclassio import ioprepped, IOAttrs
# import bacommon.displayitem as ditm

# @ioprepped
# @dataclass
# class ClassicCharacterDisplayItem(ditm.Item):
#     """Display a character."""

#     : Annotated[ClassicChestAppearance, IOAttrs('a')]

#     @override
#     @classmethod
#     def get_type_id(cls) -> ditm.ItemTypeID:
#         return ditm.ItemTypeID.CHEST

#     @override
#     def get_description(self) -> tuple[str, list[tuple[str, str]]]:
#         return self.appearance.pretty_name, []
