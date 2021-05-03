# Released under the MIT License. See LICENSE for details.
#
"""Testing dataclasses functionality."""

from __future__ import annotations

from enum import Enum
import datetime
from dataclasses import field, dataclass
from typing import TYPE_CHECKING

import pytest

from efro.util import utc_now
from efro.dataclassio import (dataclass_validate, dataclass_from_dict,
                              dataclass_to_dict, prepped)

if TYPE_CHECKING:
    from typing import Optional, List, Set, Any, Dict, Sequence, Union, Tuple


class _EnumTest(Enum):
    TEST1 = 'test1'
    TEST2 = 'test2'


class _GoodEnum(Enum):
    VAL1 = 'val1'
    VAL2 = 'val2'


class _GoodEnum2(Enum):
    VAL1 = 1
    VAL2 = 2


class _BadEnum1(Enum):
    VAL1 = 1.23


class _BadEnum2(Enum):
    VAL1 = 1
    VAL2 = 'val2'


@dataclass
class _NestedClass:
    ival: int = 0
    sval: str = 'foo'
    dval: Dict[int, str] = field(default_factory=dict)


def test_assign() -> None:
    """Testing various assignments."""

    # pylint: disable=too-many-statements

    @prepped
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
        anyval: Any = 1
        dictval: Dict[int, str] = field(default_factory=dict)
        tupleval: Tuple[int, str, bool] = (1, 'foo', False)
        datetimeval: Optional[datetime.datetime] = None

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

    now = utc_now()

    # A dict containing *ALL* values should match what we
    # get when creating a dataclass and then converting back
    # to a dict.
    dict1 = {
        'ival':
            1,
        'sval':
            'foo',
        'bval':
            True,
        'fval':
            2.0,
        'nval': {
            'ival': 1,
            'sval': 'bar',
            'dval': {
                '1': 'foof'
            },
        },
        'enval':
            'test1',
        'oival':
            1,
        'osval':
            'foo',
        'obval':
            True,
        'ofval':
            1.0,
        'oenval':
            'test2',
        'lsval': ['foo'],
        'lival': [10],
        'lbval': [False],
        'lfval': [1.0],
        'lenval': ['test1', 'test2'],
        'ssval': ['foo'],
        'dval': {
            'k': 123
        },
        'anyval': {
            'foo': [1, 2, {
                'bar': 'eep',
                'rah': 1
            }]
        },
        'dictval': {
            '1': 'foo'
        },
        'tupleval': [2, 'foof', True],
        'datetimeval': [
            now.year, now.month, now.day, now.hour, now.minute, now.second,
            now.microsecond
        ],
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
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'tupleval': []})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'tupleval': [1, 1, 1]})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'tupleval': [2, 'foof', True, True]})

    # Fields with type Any should accept all types which are directly
    # supported by json, but not ones such as tuples or non-string dict keys
    # which get implicitly translated by python's json module.
    dataclass_from_dict(_TestClass, {'anyval': {}})
    dataclass_from_dict(_TestClass, {'anyval': None})
    dataclass_from_dict(_TestClass, {'anyval': []})
    dataclass_from_dict(_TestClass, {'anyval': [True, {'foo': 'bar'}, None]})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'anyval': {1: 'foo'}})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'anyval': set()})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'anyval': (1, 2, 3)})

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

    # Coerce-to-float should only work on ints; not bools or other types.
    dataclass_from_dict(_TestClass, {'fval': 1}, coerce_to_float=True)
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'fval': 1}, coerce_to_float=False)
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'fval': True}, coerce_to_float=True)
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'fval': None}, coerce_to_float=True)
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'fval': []}, coerce_to_float=True)

    # Datetime values should only be allowed with timezone set as utc.
    dataclass_to_dict(_TestClass(datetimeval=utc_now()))
    with pytest.raises(ValueError):
        dataclass_to_dict(_TestClass(datetimeval=datetime.datetime.now()))
    with pytest.raises(ValueError):
        # This doesn't actually set timezone on the datetime obj.
        dataclass_to_dict(_TestClass(datetimeval=datetime.datetime.utcnow()))


def test_coerce() -> None:
    """Test value coercion."""

    @prepped
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


def test_prep() -> None:
    """Test the prepping process."""

    # We currently don't support Sequence; can revisit if there is
    # a strong use case.
    with pytest.raises(TypeError):

        @prepped
        @dataclass
        class _TestClass:
            ival: Sequence[int]

    # We currently only support Unions with exactly 2 members; one of
    # which is None. (Optional types get transformed into this by
    # get_type_hints() so we need to support at least that).
    with pytest.raises(TypeError):

        @prepped
        @dataclass
        class _TestClass2:
            ival: Union[int, str]

    @prepped
    @dataclass
    class _TestClass3:
        uval: Union[int, None]

    with pytest.raises(TypeError):

        @prepped
        @dataclass
        class _TestClass4:
            ival: Union[int, str]

    # This will get simplified down to simply int by get_type_hints so is ok.
    @prepped
    @dataclass
    class _TestClass5:
        ival: Union[int]

    # This will get simplified down to a valid 2 member union so is ok
    @prepped
    @dataclass
    class _TestClass6:
        ival: Union[int, None, int, None]

    # Disallow dict entries with types other than str, int, or enums
    # having those value types.
    with pytest.raises(TypeError):

        @prepped
        @dataclass
        class _TestClass7:
            dval: Dict[float, int]

    @prepped
    @dataclass
    class _TestClass8:
        dval: Dict[str, int]

    @prepped
    @dataclass
    class _TestClass9:
        dval: Dict[_GoodEnum, int]

    @prepped
    @dataclass
    class _TestClass10:
        dval: Dict[_GoodEnum2, int]

    with pytest.raises(TypeError):

        @prepped
        @dataclass
        class _TestClass11:
            dval: Dict[_BadEnum1, int]

    with pytest.raises(TypeError):

        @prepped
        @dataclass
        class _TestClass12:
            dval: Dict[_BadEnum2, int]


def test_validate() -> None:
    """Testing validation."""

    @prepped
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


def test_extra_data() -> None:
    """Test handling of data that doesn't map to dataclass attrs."""

    @prepped
    @dataclass
    class _TestClass:
        ival: int = 0
        sval: str = ''

    # Passing an attr not in the dataclass should fail if we ask it to.
    with pytest.raises(AttributeError):
        dataclass_from_dict(_TestClass, {'nonexistent': 'foo'},
                            allow_unknown_attrs=False)

    # But normally it should be preserved and present in re-export.
    obj = dataclass_from_dict(_TestClass, {'nonexistent': 'foo'})
    assert isinstance(obj, _TestClass)
    out = dataclass_to_dict(obj)
    assert out.get('nonexistent') == 'foo'

    # But not if we ask it to discard unknowns.
    obj = dataclass_from_dict(_TestClass, {'nonexistent': 'foo'},
                              discard_unknown_attrs=True)
    assert isinstance(obj, _TestClass)
    out = dataclass_to_dict(obj)
    assert 'nonexistent' not in out


def test_dict() -> None:
    """Test various dict related bits."""

    @prepped
    @dataclass
    class _TestClass:
        dval: dict

    obj = _TestClass(dval={})

    # 'Any' dicts should only support values directly compatible with json.
    obj.dval['foo'] = 5
    dataclass_to_dict(obj)
    with pytest.raises(TypeError):
        obj.dval[5] = 5
        dataclass_to_dict(obj)
    with pytest.raises(TypeError):
        obj.dval['foo'] = _GoodEnum.VAL1
        dataclass_to_dict(obj)

    # Int dict-keys should actually be stored as strings internally
    # (for json compatibility).
    @prepped
    @dataclass
    class _TestClass2:
        dval: Dict[int, float]

    obj2 = _TestClass2(dval={1: 2.34})
    out = dataclass_to_dict(obj2)
    assert '1' in out['dval']
    assert 1 not in out['dval']
    out['dval']['1'] = 2.35
    obj2 = dataclass_from_dict(_TestClass2, out)
    assert isinstance(obj2, _TestClass2)
    assert obj2.dval[1] == 2.35

    # Same with enum keys (we support enums with str and int values)
    @prepped
    @dataclass
    class _TestClass3:
        dval: Dict[_GoodEnum, int]

    obj3 = _TestClass3(dval={_GoodEnum.VAL1: 123})
    out = dataclass_to_dict(obj3)
    assert out['dval']['val1'] == 123
    out['dval']['val1'] = 124
    obj3 = dataclass_from_dict(_TestClass3, out)
    assert obj3.dval[_GoodEnum.VAL1] == 124

    @prepped
    @dataclass
    class _TestClass4:
        dval: Dict[_GoodEnum2, int]

    obj4 = _TestClass4(dval={_GoodEnum2.VAL1: 125})
    out = dataclass_to_dict(obj4)
    assert out['dval']['1'] == 125
    out['dval']['1'] = 126
    obj4 = dataclass_from_dict(_TestClass4, out)
    assert obj4.dval[_GoodEnum2.VAL1] == 126

    # The wrong enum type as a key should error.
    obj4.dval = {_GoodEnum.VAL1: 999}  # type: ignore
    with pytest.raises(TypeError):
        dataclass_to_dict(obj4)
