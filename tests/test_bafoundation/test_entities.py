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
"""Testing tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from enum import Enum, unique

import pytest

from bafoundation import entity
from efrotools.statictest import static_type_equals

if TYPE_CHECKING:
    pass


# A smattering of enum value types...
@unique
class EnumTest(Enum):
    """Testing..."""
    FIRST = 0
    SECOND = 1


class CompoundTest(entity.CompoundValue):
    """Testing..."""
    isubval = entity.Field('i', entity.IntValue(default=34532))


class CompoundTest2(CompoundTest):
    """Testing..."""
    isubval2 = entity.Field('i2', entity.IntValue(default=3453))


class EntityTest(entity.Entity):
    """Testing..."""
    ival = entity.Field('i', entity.IntValue(default=345))
    sval = entity.Field('s', entity.StringValue(default='svvv'))
    bval = entity.Field('b', entity.BoolValue(default=True))
    fval = entity.Field('f', entity.FloatValue(default=1.0))
    grp = entity.CompoundField('g', CompoundTest2())
    grp2 = entity.CompoundField('g2', CompoundTest())
    enumval = entity.Field('e', entity.EnumValue(EnumTest, default=None))
    enumval2 = entity.Field(
        'e2', entity.OptionalEnumValue(EnumTest, default=EnumTest.SECOND))
    compoundlist = entity.CompoundListField('l', CompoundTest())
    slval = entity.ListField('sl', entity.StringValue())
    tval2 = entity.Field('t2', entity.DateTimeValue())
    str_int_dict = entity.DictField('sd', str, entity.IntValue())
    tdval = entity.CompoundDictField('td', str, CompoundTest())
    fval2 = entity.Field('f2', entity.Float3Value())


class EntityTest2(entity.EntityMixin, CompoundTest2):
    """test."""


def test_entity_values() -> None:
    """Test various entity assigns for value and type correctness."""
    ent = EntityTest()

    # Simple int field.
    with pytest.raises(TypeError):
        # noinspection PyTypeHints
        ent.ival = 'strval'  # type: ignore
    assert static_type_equals(ent.ival, int)
    assert isinstance(ent.ival, int)
    assert ent.ival == 345
    ent.ival = 346
    assert ent.ival == 346

    # Simple str/int dict field.
    assert 'foo' not in ent.str_int_dict
    with pytest.raises(TypeError):
        # noinspection PyTypeHints
        ent.str_int_dict[0] = 123  # type: ignore
    with pytest.raises(TypeError):
        # noinspection PyTypeHints
        ent.str_int_dict['foo'] = 'bar'  # type: ignore
    ent.str_int_dict['foo'] = 123
    assert static_type_equals(ent.str_int_dict['foo'], int)
    assert ent.str_int_dict['foo'] == 123

    # Compound list field.
    with pytest.raises(IndexError):
        print(ent.compoundlist[0])
    with pytest.raises(TypeError):
        # noinspection PyTypeHints
        ent.compoundlist[0] = 123  # type: ignore
    assert len(ent.compoundlist) == 0
    assert not ent.compoundlist
    ent.compoundlist.append()
    assert ent.compoundlist
    assert len(ent.compoundlist) == 1
    assert static_type_equals(ent.compoundlist[0], CompoundTest)
