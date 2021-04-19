# Released under the MIT License. See LICENSE for details.
#
"""Testing dataclasses functionality."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

from efro.dataclasses import (dataclass_validate, dataclass_from_dict,
                              dataclass_to_dict)

if TYPE_CHECKING:
    from typing import Optional, List, Set


class _EnumTest(Enum):
    TEST1 = 'test1'
    TEST2 = 'test2'


@dataclass
class _NestedClass:
    ival: int = 0
    sval: str = 'foo'


def test_assign() -> None:
    """Testing various assignments."""

    # pylint: disable=too-many-statements

    @dataclass
    class _TestClass:
        ival: int = 0
        sval: str = ''
        bval: bool = True
        fval: float = 1.0
        nval: _NestedClass = field(default_factory=_NestedClass)
        enval: _EnumTest = _EnumTest.TEST1
        oival: Optional[int] = None
        osval: Optional[str] = None
        obval: Optional[bool] = None
        ofval: Optional[float] = None
        oenval: Optional[_EnumTest] = _EnumTest.TEST1
        lsval: List[str] = field(default_factory=list)
        lival: List[int] = field(default_factory=list)
        lbval: List[bool] = field(default_factory=list)
        lfval: List[float] = field(default_factory=list)
        lenval: List[_EnumTest] = field(default_factory=list)
        ssval: Set[str] = field(default_factory=set)

    class _TestClass2:
        pass

    # Attempting to use with non-dataclass should fail.
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass2, {})

    # Attempting to pass non-dicts should fail.
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, [])  # type: ignore
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, None)  # type: ignore

    # Passing an attr not in the dataclass should fail.
    with pytest.raises(AttributeError):
        dataclass_from_dict(_TestClass, {'nonexistent': 'foo'})

    # A dict containing *ALL* values should match what we
    # get when creating a dataclass and then converting back
    # to a dict.
    dict1 = {
        'ival': 1,
        'sval': 'foo',
        'bval': True,
        'fval': 2.0,
        'nval': {
            'ival': 1,
            'sval': 'bar'
        },
        'enval': 'test1',
        'oival': 1,
        'osval': 'foo',
        'obval': True,
        'ofval': 1.0,
        'oenval': 'test2',
        'lsval': ['foo'],
        'lival': [10],
        'lbval': [False],
        'lfval': [1.0],
        'lenval': ['test1', 'test2'],
        'ssval': ['foo']
    }
    dc1 = dataclass_from_dict(_TestClass, dict1)
    assert dataclass_to_dict(dc1) == dict1

    # A few other assignment checks.
    assert isinstance(
        dataclass_from_dict(
            _TestClass, {
                'oival': None,
                'osval': None,
                'obval': None,
                'ofval': None,
                'lsval': [],
                'lival': [],
                'lbval': [],
                'lfval': [],
                'ssval': []
            }), _TestClass)
    assert isinstance(
        dataclass_from_dict(
            _TestClass, {
                'oival': 1,
                'osval': 'foo',
                'obval': True,
                'ofval': 2.0,
                'lsval': ['foo', 'bar', 'eep'],
                'lival': [10, 11, 12],
                'lbval': [False, True],
                'lfval': [1.0, 2.0, 3.0]
            }), _TestClass)

    # Attr assigns mismatched with their value types should fail.
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ival': 'foo'})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'sval': 1})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'bval': 2})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'oival': 'foo'})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'osval': 1})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'obval': 2})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ofval': 'blah'})
    with pytest.raises(ValueError):
        dataclass_from_dict(_TestClass, {'oenval': 'test3'})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'lsval': 'blah'})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'lsval': ['blah', None]})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'lsval': [1]})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'lsval': (1, )})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'lbval': [None]})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'lival': ['foo']})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'lfval': [True]})
    with pytest.raises(ValueError):
        dataclass_from_dict(_TestClass, {'lenval': ['test1', 'test3']})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ssval': [True]})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ssval': {}})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ssval': set()})

    # More subtle attr/type mismatches that should fail
    # (we currently require EXACT type matches).
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ival': True})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'fval': 2}, coerce_to_float=False)
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'bval': 1})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ofval': 1}, coerce_to_float=False)
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'lfval': [1]}, coerce_to_float=False)


def test_coerce() -> None:
    """Test value coercion."""

    @dataclass
    class _TestClass:
        ival: int = 0
        fval: float = 0.0

    # Float value present for int should never work.
    obj = _TestClass()
    # noinspection PyTypeHints
    obj.ival = 1.0  # type: ignore
    with pytest.raises(TypeError):
        dataclass_validate(obj, coerce_to_float=True)
    with pytest.raises(TypeError):
        dataclass_validate(obj, coerce_to_float=False)

    # Int value present for float should work only with coerce on.
    obj = _TestClass()
    obj.fval = 1
    dataclass_validate(obj, coerce_to_float=True)
    with pytest.raises(TypeError):
        dataclass_validate(obj, coerce_to_float=False)

    # Likewise, passing in an int for a float field should work only
    # with coerce on.
    dataclass_from_dict(_TestClass, {'fval': 1}, coerce_to_float=True)
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'fval': 1}, coerce_to_float=False)

    # Passing in floats for an int field should never work.
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ival': 1.0}, coerce_to_float=True)
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'ival': 1.0}, coerce_to_float=False)


def test_validate() -> None:
    """Testing validation."""

    @dataclass
    class _TestClass:
        ival: int = 0
        sval: str = ''
        bval: bool = True
        fval: float = 1.0
        oival: Optional[int] = None
        osval: Optional[str] = None
        obval: Optional[bool] = None
        ofval: Optional[float] = None

    # Should pass by default.
    tclass = _TestClass()
    dataclass_validate(tclass)

    # No longer valid (without coerce)
    tclass.fval = 1
    with pytest.raises(TypeError):
        dataclass_validate(tclass, coerce_to_float=False)

    # Should pass by default.
    tclass = _TestClass()
    dataclass_validate(tclass)

    # No longer valid.
    # noinspection PyTypeHints
    tclass.ival = None  # type: ignore
    with pytest.raises(TypeError):
        dataclass_validate(tclass)
