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
"""Testing entity functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from enum import Enum, unique

import pytest

from bafoundation import entity
from efrotools.statictest import static_type_equals

if TYPE_CHECKING:
    pass


@unique
class EnumTest(Enum):
    """Testing..."""
    FIRST = 0
    SECOND = 1


class SubCompoundTest(entity.CompoundValue):
    """Testing..."""
    subval = entity.Field('b', entity.BoolValue())


class CompoundTest(entity.CompoundValue):
    """Testing..."""
    isubval = entity.Field('i', entity.IntValue(default=34532))
    compoundlist = entity.CompoundListField('l', SubCompoundTest())


class CompoundTest2(CompoundTest):
    """Testing..."""
    isubval2 = entity.Field('i2', entity.IntValue(default=3453))


class EntityTest(entity.Entity):
    """Testing..."""
    ival = entity.Field('i', entity.IntValue(default=345))
    sval = entity.Field('s', entity.StringValue(default='svvv'))
    bval = entity.Field('b', entity.BoolValue(default=True))
    fval = entity.Field('f', entity.FloatValue(default=1.0))
    grp = entity.CompoundField('g', CompoundTest())
    grp2 = entity.CompoundField('g2', CompoundTest2())
    enumval = entity.Field('e', entity.EnumValue(EnumTest, default=None))
    enumval2 = entity.Field(
        'e2', entity.OptionalEnumValue(EnumTest, default=EnumTest.SECOND))
    compoundlist = entity.CompoundListField('l', CompoundTest())
    slval = entity.ListField('sl', entity.StringValue())
    tval2 = entity.Field('t2', entity.DateTimeValue())
    str_int_dict = entity.DictField('sd', str, entity.IntValue())
    tdval = entity.CompoundDictField('td', str, CompoundTest())
    fval2 = entity.Field('f2', entity.Float3Value())


# noinspection PyTypeHints
def test_entity_values() -> None:
    """Test various entity assigns for value and type correctness."""
    ent = EntityTest()

    # Simple int field.
    with pytest.raises(TypeError):
        ent.ival = 'strval'  # type: ignore
    assert static_type_equals(ent.ival, int)
    assert isinstance(ent.ival, int)
    assert ent.ival == 345
    ent.ival = 346
    assert ent.ival == 346

    # Simple float field.
    with pytest.raises(TypeError):
        ent.fval = "foo"  # type: ignore
    assert static_type_equals(ent.fval, float)
    ent.fval = 2
    ent.fval = True
    ent.fval = 1.0

    # Simple str/int dict field.
    assert 'foo' not in ent.str_int_dict
    with pytest.raises(TypeError):
        ent.str_int_dict[0] = 123  # type: ignore
    with pytest.raises(TypeError):
        ent.str_int_dict['foo'] = 'bar'  # type: ignore
    ent.str_int_dict['foo'] = 123
    assert static_type_equals(ent.str_int_dict['foo'], int)
    assert ent.str_int_dict['foo'] == 123

    # Compound value inheritance.
    assert ent.grp2.isubval2 == 3453
    assert ent.grp2.isubval == 34532

    # Compound list field.
    with pytest.raises(IndexError):
        print(ent.compoundlist[0])
    with pytest.raises(TypeError):
        ent.compoundlist[0] = 123  # type: ignore
    assert len(ent.compoundlist) == 0
    assert not ent.compoundlist
    ent.compoundlist.append()
    assert ent.compoundlist
    assert len(ent.compoundlist) == 1
    assert static_type_equals(ent.compoundlist[0], CompoundTest)

    # Enum value
    with pytest.raises(ValueError):
        ent.enumval = None  # type: ignore
    assert ent.enumval == EnumTest.FIRST

    # Optional Enum value
    ent.enumval2 = None
    assert ent.enumval2 is None

    # Nested compound values
    assert not ent.grp.compoundlist
    val = ent.grp.compoundlist.append()
    assert static_type_equals(val, SubCompoundTest)
    assert static_type_equals(ent.grp.compoundlist[0], SubCompoundTest)
    assert static_type_equals(ent.grp.compoundlist[0].subval, bool)


class EntityTestMixin(entity.EntityMixin, CompoundTest2):
    """A test entity created from a compound using a mixin class."""


def test_entity_mixin() -> None:
    """Testing our mixin entity variety."""
    ent = EntityTestMixin()
    assert static_type_equals(ent.isubval2, int)
    assert ent.isubval2 == 3453


def test_key_uniqueness() -> None:
    """Make sure entities reject multiple fields with the same key."""

    # Make sure a single entity with dup keys fails:
    with pytest.raises(RuntimeError):

        class EntityKeyTest(entity.Entity):
            """Test entity with invalid duplicate keys."""
            ival = entity.Field('i', entity.IntValue())
            sval = entity.Field('i', entity.StringValue())

        _ent = EntityKeyTest()

    # Make sure we still get an error if the duplicate keys come from
    # different places in the class hierarchy.
    with pytest.raises(RuntimeError):

        class EntityKeyTest2(entity.Entity):
            """Test entity with invalid duplicate keys."""
            ival = entity.Field('i', entity.IntValue())

        class EntityKeyTest3(EntityKeyTest2):
            """Test entity with invalid duplicate keys."""
            sval = entity.Field('i', entity.StringValue())

        _ent2 = EntityKeyTest3()


def test_data_storage_and_fetching() -> None:
    """Test store_default option for entities."""

    class EntityTestD(entity.Entity):
        """Testing store_default off."""
        ival = entity.Field('i', entity.IntValue(default=3,
                                                 store_default=False))

    class EntityTestD2(entity.Entity):
        """Testing store_default on (the default)."""
        ival = entity.Field('i', entity.IntValue(default=3))

    # This guy should get pruned when its got a default value.
    testd = EntityTestD()
    assert testd.ival == 3
    assert testd.pruned_data() == {}
    testd.ival = 4
    assert testd.pruned_data() == {'i': 4}
    testd.ival = 3
    assert testd.pruned_data() == {}

    # Make sure our pretty/prune json options work.
    assert testd.to_json_str() == '{}'
    assert testd.to_json_str(prune=False) == '{"i":3}'
    assert testd.to_json_str(prune=False, pretty=True) == ('{\n'
                                                           '  "i": 3\n'
                                                           '}')
    # This guy should never get pruned...
    testd2 = EntityTestD2()
    assert testd2.ival == 3
    assert testd2.pruned_data() == {'i': 3}
    testd2.ival = 4
    assert testd2.pruned_data() == {'i': 4}
    testd2.ival = 3
    assert testd2.to_json_str(prune=True) == '{"i":3}'
