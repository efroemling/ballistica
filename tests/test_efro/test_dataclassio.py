# Released under the MIT License. See LICENSE for details.
#
"""Testing dataclasses functionality."""
# pylint: disable=too-many-lines

from __future__ import annotations

import copy
import datetime
from enum import Enum
from dataclasses import field, dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Sequence,
    Annotated,
    assert_type,
    assert_never,
    override,
)

import pytest
from efro.util import utc_now, utc_now_naive
from efro.dataclassio import (
    dataclass_validate,
    dataclass_from_dict,
    dataclass_to_dict,
    ioprepped,
    ioprep,
    IOAttrs,
    Codec,
    DataclassFieldLookup,
    IOExtendedData,
    IOMultiType,
)

if TYPE_CHECKING:
    from typing import Self


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
    dval: dict[int, str] = field(default_factory=dict)


def test_assign() -> None:
    """Testing various assignments."""

    # pylint: disable=too-many-statements

    @ioprepped
    @dataclass
    class _TestClass:
        ival: int = 0
        sval: str = ''
        bval: bool = True
        fval: float = 1.0
        nval: _NestedClass = field(default_factory=_NestedClass)
        enval: _EnumTest = _EnumTest.TEST1
        oival: int | None = None
        oival2: int | None = None
        osval: str | None = None
        obval: bool | None = None
        ofval: float | None = None
        oenval: _EnumTest | None = _EnumTest.TEST1
        lsval: list[str] = field(default_factory=list)
        lival: list[int] = field(default_factory=list)
        lbval: list[bool] = field(default_factory=list)
        lfval: list[float] = field(default_factory=list)
        lenval: list[_EnumTest] = field(default_factory=list)
        ssval: set[str] = field(default_factory=set)
        anyval: Any = 1
        dictval: dict[int, str] = field(default_factory=dict)
        tupleval: tuple[int, str, bool] = (1, 'foo', False)
        datetimeval: datetime.datetime | None = None
        timedeltaval: datetime.timedelta | None = None

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
    tdelta = datetime.timedelta(days=123, seconds=456, microseconds=789)

    # A dict containing *ALL* values should exactly match what we get
    # when creating a dataclass and then converting back to a dict.
    dict1 = {
        'ival': 1,
        'sval': 'foo',
        'bval': True,
        'fval': 2.0,
        'nval': {
            'ival': 1,
            'sval': 'bar',
            'dval': {'1': 'foof'},
        },
        'enval': 'test1',
        'oival': 1,
        'oival2': 1,
        'osval': 'foo',
        'obval': True,
        'ofval': 1.0,
        'oenval': 'test2',
        'lsval': ['foo'],
        'lival': [10],
        'lbval': [False],
        'lfval': [1.0],
        'lenval': ['test1', 'test2'],
        'ssval': ['foo'],
        'dval': {'k': 123},
        'anyval': {'foo': [1, 2, {'bar': 'eep', 'rah': 1}]},
        'dictval': {'1': 'foo'},
        'tupleval': [2, 'foof', True],
        'datetimeval': [
            now.year,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second,
            now.microsecond,
        ],
        'timedeltaval': [tdelta.days, tdelta.seconds, tdelta.microseconds],
    }
    dc1 = dataclass_from_dict(_TestClass, dict1)
    assert dataclass_to_dict(dc1) == dict1

    # A few other assignment checks.
    assert isinstance(
        dataclass_from_dict(
            _TestClass,
            {
                'oival': None,
                'oival2': None,
                'osval': None,
                'obval': None,
                'ofval': None,
                'lsval': [],
                'lival': [],
                'lbval': [],
                'lfval': [],
                'ssval': [],
            },
        ),
        _TestClass,
    )
    assert isinstance(
        dataclass_from_dict(
            _TestClass,
            {
                'oival': 1,
                'oival2': 1,
                'osval': 'foo',
                'obval': True,
                'ofval': 2.0,
                'lsval': ['foo', 'bar', 'eep'],
                'lival': [10, 11, 12],
                'lbval': [False, True],
                'lfval': [1.0, 2.0, 3.0],
            },
        ),
        _TestClass,
    )

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
        dataclass_from_dict(_TestClass, {'oival2': 'foo'})
    dataclass_from_dict(_TestClass, {'oival2': None})
    dataclass_from_dict(_TestClass, {'oival2': 123})
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
        dataclass_from_dict(_TestClass, {'lsval': (1,)})
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
    with pytest.raises(ValueError):
        dataclass_from_dict(_TestClass, {'tupleval': []})
    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClass, {'tupleval': [1, 1, 1]})
    with pytest.raises(ValueError):
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
        # This doesn't have a timezone on the datetime obj.
        dataclass_to_dict(_TestClass(datetimeval=utc_now_naive()))


def test_coerce() -> None:
    """Test value coercion."""

    @ioprepped
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

        @ioprepped
        @dataclass
        class _TestClass:
            ival: Sequence[int]

    # We currently only support Unions with exactly 2 members; one of
    # which is None. (Optional types get transformed into this by
    # get_type_hints() so we need to support at least that).
    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass2:
            ival: int | str

    @ioprepped
    @dataclass
    class _TestClass3:
        uval: int | None

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass4:
            ival: int | str

    # This will get simplified down to simply int by get_type_hints so is ok.
    @ioprepped
    @dataclass
    class _TestClass5:
        ival: int | int

    # This will get simplified down to a valid 2 member union so is ok
    @ioprepped
    @dataclass
    class _TestClass6:
        ival: int | None | int | None

    # Disallow dict entries with types other than str, int, or enums
    # having those value types.
    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass7:
            dval: dict[float, int]

    @ioprepped
    @dataclass
    class _TestClass8:
        dval: dict[str, int]

    @ioprepped
    @dataclass
    class _TestClass9:
        dval: dict[_GoodEnum, int]

    @ioprepped
    @dataclass
    class _TestClass10:
        dval: dict[_GoodEnum2, int]

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass11:
            dval: dict[_BadEnum1, int]

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass12:
            dval: dict[_BadEnum2, int]


def test_validate() -> None:
    """Testing validation."""

    @ioprepped
    @dataclass
    class _TestClass:
        ival: int = 0
        sval: str = ''
        bval: bool = True
        fval: float = 1.0
        oival: int | None = None
        osval: str | None = None
        obval: bool | None = None
        ofval: float | None = None

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

    @ioprepped
    @dataclass
    class _TestClass:
        ival: int = 0
        sval: str = ''

    # Passing an attr not in the dataclass should fail if we ask it to.
    with pytest.raises(AttributeError):
        dataclass_from_dict(
            _TestClass, {'nonexistent': 'foo'}, allow_unknown_attrs=False
        )

    # But normally it should be preserved and present in re-export.
    obj = dataclass_from_dict(_TestClass, {'nonexistent': 'foo'})
    assert isinstance(obj, _TestClass)
    out = dataclass_to_dict(obj)
    assert out.get('nonexistent') == 'foo'

    # But not if we ask it to discard unknowns.
    obj = dataclass_from_dict(
        _TestClass, {'nonexistent': 'foo'}, discard_unknown_attrs=True
    )
    assert isinstance(obj, _TestClass)
    out = dataclass_to_dict(obj)
    assert 'nonexistent' not in out


def test_ioattrs() -> None:
    """Testing ioattrs annotations."""

    @ioprepped
    @dataclass
    class _TestClass:
        dval: Annotated[dict, IOAttrs('d')]

    obj = _TestClass(dval={'foo': 'bar'})

    # Make sure key is working.
    assert dataclass_to_dict(obj) == {'d': {'foo': 'bar'}}

    # Setting store_default False without providing a default or
    # default_factory should fail.
    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass2:
            dval: Annotated[dict, IOAttrs('d', store_default=False)]

    @ioprepped
    @dataclass
    class _TestClass3:
        dval: Annotated[dict, IOAttrs('d', store_default=False)] = field(
            default_factory=dict
        )
        ival: Annotated[int, IOAttrs('i', store_default=False)] = 123

    # Both attrs are default; should get stripped out.
    obj3 = _TestClass3()
    assert dataclass_to_dict(obj3) == {}

    # Both attrs are non-default vals; should remain in output.
    obj3 = _TestClass3(dval={'foo': 'bar'}, ival=124)
    assert dataclass_to_dict(obj3) == {'d': {'foo': 'bar'}, 'i': 124}

    # Test going the other way.
    obj3 = dataclass_from_dict(
        _TestClass3,
        {'d': {'foo': 'barf'}, 'i': 125},
        allow_unknown_attrs=False,
    )
    assert obj3.dval == {'foo': 'barf'}
    assert obj3.ival == 125


def test_codecs() -> None:
    """Test differences with codecs."""

    @ioprepped
    @dataclass
    class _TestClass:
        bval: bytes

    # bytes to/from JSON (goes through base64)
    obj = _TestClass(bval=b'foo')
    out = dataclass_to_dict(obj, codec=Codec.JSON)
    assert isinstance(out['bval'], str) and out['bval'] == 'Zm9v'
    obj = dataclass_from_dict(_TestClass, out, codec=Codec.JSON)
    assert obj.bval == b'foo'

    # bytes to/from FIRESTORE (passed as-is)
    obj = _TestClass(bval=b'foo')
    out = dataclass_to_dict(obj, codec=Codec.FIRESTORE)
    assert isinstance(out['bval'], bytes) and out['bval'] == b'foo'
    obj = dataclass_from_dict(_TestClass, out, codec=Codec.FIRESTORE)
    assert obj.bval == b'foo'

    now = utc_now()

    @ioprepped
    @dataclass
    class _TestClass2:
        dval: datetime.datetime

    # datetime to/from JSON (turns into a list of values)
    obj2 = _TestClass2(dval=now)
    out = dataclass_to_dict(obj2, codec=Codec.JSON)
    assert (
        isinstance(out['dval'], list)
        and len(out['dval']) == 7
        and all(isinstance(val, int) for val in out['dval'])
    )
    obj2 = dataclass_from_dict(_TestClass2, out, codec=Codec.JSON)
    assert obj2.dval == now

    # datetime to/from FIRESTORE (passed through as-is)
    obj2 = _TestClass2(dval=now)
    out = dataclass_to_dict(obj2, codec=Codec.FIRESTORE)
    assert isinstance(out['dval'], datetime.datetime)
    obj2 = dataclass_from_dict(_TestClass2, out, codec=Codec.FIRESTORE)
    assert obj2.dval == now


def test_dict() -> None:
    """Test various dict related bits."""

    @ioprepped
    @dataclass
    class _TestClass:
        dval: dict

    obj = _TestClass(dval={})

    # 'Any' dicts should only support values directly compatible with
    # json.
    obj.dval['foo'] = 5
    dataclass_to_dict(obj)
    with pytest.raises(TypeError):
        obj.dval[5] = 5
        dataclass_to_dict(obj)
    with pytest.raises(TypeError):
        obj.dval['foo'] = _GoodEnum.VAL1
        dataclass_to_dict(obj)

    # Int dict-keys should actually be stored as strings internally (for
    # json compatibility).
    @ioprepped
    @dataclass
    class _TestClass2:
        dval: dict[int, float]

    obj2 = _TestClass2(dval={1: 2.34})
    out = dataclass_to_dict(obj2)
    assert '1' in out['dval']
    assert 1 not in out['dval']
    out['dval']['1'] = 2.35
    obj2 = dataclass_from_dict(_TestClass2, out)
    assert isinstance(obj2, _TestClass2)
    assert obj2.dval[1] == 2.35

    # Same with enum keys (we support enums with str and int values)
    @ioprepped
    @dataclass
    class _TestClass3:
        dval: dict[_GoodEnum, int]

    obj3 = _TestClass3(dval={_GoodEnum.VAL1: 123})
    out = dataclass_to_dict(obj3)
    assert out['dval']['val1'] == 123
    out['dval']['val1'] = 124
    obj3 = dataclass_from_dict(_TestClass3, out)
    assert obj3.dval[_GoodEnum.VAL1] == 124

    @ioprepped
    @dataclass
    class _TestClass4:
        dval: dict[_GoodEnum2, int]

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


def test_sets() -> None:
    """Test bits related to sets."""

    @ioprepped
    @dataclass
    class _TestClass:
        sval: set[str]

    obj1 = _TestClass({'a', 'b', 'c', 'd', 'e', 'f'})
    obj2 = _TestClass({'c', 'd', 'a', 'e', 'f', 'b'})

    # Sets get converted to lists; make sure they are getting sorted so
    # that output is deterministic and it is meaningful to compare the
    # output dicts from two sets for equality.
    assert dataclass_to_dict(obj1) == {'sval': ['a', 'b', 'c', 'd', 'e', 'f']}
    assert dataclass_to_dict(obj2) == {'sval': ['a', 'b', 'c', 'd', 'e', 'f']}

    @ioprepped
    @dataclass
    class _TestClass2:
        dtval: set[datetime.datetime]

    # Make sure serialization/deserialization with odd types like
    # datetimes works.
    obj3 = _TestClass2(
        dtval={utc_now(), utc_now() + datetime.timedelta(hours=1)}
    )

    assert (
        dataclass_from_dict(
            _TestClass2,
            dataclass_to_dict(obj3, codec=Codec.FIRESTORE),
            codec=Codec.FIRESTORE,
        )
        == obj3
    )
    assert (
        dataclass_from_dict(
            _TestClass2,
            dataclass_to_dict(obj3, codec=Codec.JSON),
            codec=Codec.JSON,
        )
        == obj3
    )


def test_name_clashes() -> None:
    """Make sure we catch name clashes since we can remap attr names."""

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass:
            ival: Annotated[int, IOAttrs('i')] = 4
            ival2: Annotated[int, IOAttrs('i')] = 5

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass2:
            ival: int = 4
            ival2: Annotated[int, IOAttrs('ival')] = 5

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClass3:
            ival: Annotated[int, IOAttrs(store_default=False)] = 4
            ival2: Annotated[int, IOAttrs('ival')] = 5


@dataclass
class _RecursiveTest:
    val: int
    child: _RecursiveTest | None = None


def test_recursive() -> None:
    """Test recursive classes."""

    # Can't use ioprepped on this since it refers to its own name which
    # doesn't exist yet. Have to explicitly prep it after.
    ioprep(_RecursiveTest)

    rtest = _RecursiveTest(val=1)
    rtest.child = _RecursiveTest(val=2)
    rtest.child.child = _RecursiveTest(val=3)
    expected_output = {
        'val': 1,
        'child': {'val': 2, 'child': {'val': 3, 'child': None}},
    }
    assert dataclass_to_dict(rtest) == expected_output
    assert dataclass_from_dict(_RecursiveTest, expected_output) == rtest


def test_any() -> None:
    """Test data included with type Any."""

    @ioprepped
    @dataclass
    class _TestClass:
        anyval: Any

    obj = _TestClass(anyval=b'bytes')

    # JSON output doesn't allow bytes or datetime objects included in
    # 'Any' data.
    with pytest.raises(TypeError):
        dataclass_validate(obj, codec=Codec.JSON)

    obj.anyval = datetime.datetime.now()
    with pytest.raises(TypeError):
        dataclass_validate(obj, codec=Codec.JSON)

    # Firestore, however, does.
    obj.anyval = b'bytes'
    dataclass_validate(obj, codec=Codec.FIRESTORE)
    obj.anyval = datetime.datetime.now()
    dataclass_validate(obj, codec=Codec.FIRESTORE)


@ioprepped
@dataclass
class _SPTestClass1:
    barf: int = 5
    eep: str = 'blah'
    barf2: Annotated[int, IOAttrs('b')] = 5


@ioprepped
@dataclass
class _SPTestClass2:
    rah: bool = False
    subc: _SPTestClass1 = field(default_factory=_SPTestClass1)
    subc2: Annotated[_SPTestClass1, IOAttrs('s')] = field(
        default_factory=_SPTestClass1
    )


def test_datetime_limits() -> None:
    """Test limiting datetime values in various ways."""
    from efro.util import utc_today, utc_this_hour

    @ioprepped
    @dataclass
    class _TestClass:
        tval: Annotated[datetime.datetime, IOAttrs(whole_hours=True)]

    # Check whole-hour limit when validating/exporting.
    obj = _TestClass(tval=utc_this_hour() + datetime.timedelta(minutes=1))
    with pytest.raises(ValueError):
        dataclass_validate(obj)
    obj.tval = utc_this_hour()
    dataclass_validate(obj)

    # Check whole-days limit when importing.
    out = dataclass_to_dict(obj)
    out['tval'][-1] += 1
    with pytest.raises(ValueError):
        dataclass_from_dict(_TestClass, out)

    # Check whole-days limit when validating/exporting.
    @ioprepped
    @dataclass
    class _TestClass2:
        tval: Annotated[datetime.datetime, IOAttrs(whole_days=True)]

    obj2 = _TestClass2(tval=utc_today() + datetime.timedelta(hours=1))
    with pytest.raises(ValueError):
        dataclass_validate(obj2)
    obj2.tval = utc_today()
    dataclass_validate(obj2)

    # Check whole-days limit when importing.
    out = dataclass_to_dict(obj2)
    out['tval'][-1] += 1
    with pytest.raises(ValueError):
        dataclass_from_dict(_TestClass2, out)


def test_field_paths() -> None:
    """Test type-safe field path evaluations."""

    # Define a few nested dataclass types, some of which have storage
    # names differing from their field names.
    @ioprepped
    @dataclass
    class _TestClass:
        @dataclass
        class _TestSubClass:
            val1: int = 0
            val2: Annotated[int, IOAttrs('v2')] = 0

        sub1: _TestSubClass = field(default_factory=_TestSubClass)
        sub2: Annotated[_TestSubClass, IOAttrs('s2')] = field(
            default_factory=_TestSubClass
        )

    # Now let's lookup various storage paths.
    lookup = DataclassFieldLookup(_TestClass)

    # Make sure lookups are returning correct storage paths.
    assert lookup.path(lambda obj: obj.sub1) == 'sub1'
    assert lookup.path(lambda obj: obj.sub1.val1) == 'sub1.val1'
    assert lookup.path(lambda obj: obj.sub1.val2) == 'sub1.v2'
    assert lookup.path(lambda obj: obj.sub2.val1) == 's2.val1'
    assert lookup.path(lambda obj: obj.sub2.val2) == 's2.v2'

    # Attempting to return fields that aren't there should fail in both
    # type-checking and runtime.
    with pytest.raises(AttributeError):
        lookup.path(lambda obj: obj.sub1.val3)  # type: ignore

    # Returning non-field objects will fail at runtime even if
    # type-checking evaluates them as valid values.
    with pytest.raises(TypeError):
        lookup.path(lambda obj: 1)

    with pytest.raises(TypeError):
        lookup.path(lambda obj: obj.sub1.val1.real)


def test_nested() -> None:
    """Test nesting dataclasses."""

    @ioprepped
    @dataclass
    class _TestClass:
        class _TestEnum(Enum):
            VAL1 = 'val1'
            VAL2 = 'val2'

        @dataclass
        class _TestSubClass:
            ival: int = 0

        subval: _TestSubClass = field(default_factory=_TestSubClass)
        enval: _TestEnum = _TestEnum.VAL1


def test_extended_data() -> None:
    """Test IOExtendedData functionality."""

    @ioprepped
    @dataclass
    class _TestClass:
        vals: tuple[int, int]

    # This data lines up.
    indata = {'vals': [0, 0]}
    _obj = dataclass_from_dict(_TestClass, indata)

    # This data doesn't.
    indata = {'vals': [0, 0, 0]}
    with pytest.raises(ValueError):
        _obj = dataclass_from_dict(_TestClass, indata)

    # Now define the same data but give it an adapter so it can work
    # with our incorrectly-formatted data.
    @ioprepped
    @dataclass
    class _TestClass2(IOExtendedData):
        vals: tuple[int, int]

        @override
        @classmethod
        def will_input(cls, data: dict) -> None:
            data['vals'] = data['vals'][:2]

        @override
        def will_output(self) -> None:
            self.vals = (0, 0)

    # This data lines up.
    indata = {'vals': [0, 0]}
    _obj2 = dataclass_from_dict(_TestClass2, indata)

    # Now this data will too via our custom input filter.
    indata = {'vals': [0, 0, 0]}
    _obj2 = dataclass_from_dict(_TestClass2, indata)

    # Ok, now test output:

    # Does the expected thing.
    assert dataclass_to_dict(_TestClass(vals=(1, 2))) == {'vals': [1, 2]}

    # Uses our output filter.
    assert dataclass_to_dict(_TestClass2(vals=(1, 2))) == {'vals': [0, 0]}


def test_soft_default() -> None:
    """Test soft_default IOAttr value."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # Try both of these with and without storage_name to make sure
    # soft_default interacts correctly with both cases.

    @ioprepped
    @dataclass
    class _TestClassA:
        ival: int

    @ioprepped
    @dataclass
    class _TestClassA2:
        ival: Annotated[int, IOAttrs('i')]

    @ioprepped
    @dataclass
    class _TestClassB:
        ival: Annotated[int, IOAttrs(soft_default=0)]

    @ioprepped
    @dataclass
    class _TestClassB2:
        ival: Annotated[int, IOAttrs('i', soft_default=0)]

    @ioprepped
    @dataclass
    class _TestClassB3:
        ival: Annotated[int, IOAttrs('i', soft_default_factory=lambda: 0)]

    # These should fail because there's no value for ival.
    with pytest.raises(ValueError):
        dataclass_from_dict(_TestClassA, {})

    with pytest.raises(ValueError):
        dataclass_from_dict(_TestClassA2, {})

    # These should succeed because it has a soft-default value to fall
    # back on.
    dataclass_from_dict(_TestClassB, {})
    dataclass_from_dict(_TestClassB2, {})
    dataclass_from_dict(_TestClassB3, {})

    # soft_default should also allow using store_default=False without
    # requiring the dataclass to contain a default or default_factory

    @ioprepped
    @dataclass
    class _TestClassC:
        ival: Annotated[int, IOAttrs(store_default=False)] = 0

    assert dataclass_to_dict(_TestClassC()) == {}

    # This should fail since store_default would be meaningless without
    # any source for the default value.
    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClassC2:
            ival: Annotated[int, IOAttrs(store_default=False)]

    # However with our shiny soft_default it should work.
    @ioprepped
    @dataclass
    class _TestClassC3:
        ival: Annotated[int, IOAttrs(store_default=False, soft_default=0)]

    assert dataclass_to_dict(_TestClassC3(0)) == {}

    @ioprepped
    @dataclass
    class _TestClassC3b:
        ival: Annotated[
            int, IOAttrs(store_default=False, soft_default_factory=lambda: 0)
        ]

    assert dataclass_to_dict(_TestClassC3b(0)) == {}

    # We disallow passing a few mutable types as soft_defaults just as
    # dataclass does with regular defaults.
    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClassD:
            lval: Annotated[list, IOAttrs(soft_default=[])]

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClassD2:
            # noinspection PyTypeHints
            lval: Annotated[set, IOAttrs(soft_default=set())]

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClassD3:
            lval: Annotated[dict, IOAttrs(soft_default={})]

    # soft_defaults are not static-type-checked, but we do try to catch
    # basic type mismatches at prep time. Make sure that's working. (we
    # also do full value validation during input, but the more we catch
    # early the better)
    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClassE:
            lval: Annotated[int, IOAttrs(soft_default='')]

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClassE2:
            lval: Annotated[str, IOAttrs(soft_default=45)]

    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class _TestClassE3:
            lval: Annotated[list, IOAttrs(soft_default_factory=set)]

    # Make sure Unions/Optionals go through ok. Note that mismatches
    # currently aren't caught at prep time; just checking the negative
    # case here.
    @ioprepped
    @dataclass
    class _TestClassE4:
        lval: Annotated[str | None, IOAttrs(soft_default=None)]

    @ioprepped
    @dataclass
    class _TestClassE5:
        lval: Annotated[str | None, IOAttrs(soft_default='foo')]

    # Now try more in-depth examples: nested type mismatches like this
    # are currently not caught at prep-time but ARE caught during
    # inputting.
    @ioprepped
    @dataclass
    class _TestClassE6:
        lval: Annotated[tuple[int, int], IOAttrs(soft_default=('foo', 'bar'))]

    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClassE6, {})

    @ioprepped
    @dataclass
    class _TestClassE7:
        lval: Annotated[bool | None, IOAttrs(soft_default=12)]

    with pytest.raises(TypeError):
        dataclass_from_dict(_TestClassE7, {})

    # If both a soft_default and regular field default are present, make
    # sure soft_default takes precedence (it applies before data even
    # hits the dataclass constructor).

    @ioprepped
    @dataclass
    class _TestClassE8:
        ival: Annotated[int, IOAttrs(soft_default=1, store_default=False)] = 2

    assert dataclass_from_dict(_TestClassE8, {}).ival == 1

    # Make sure soft_default gets used both when determining when to
    # omit values from output and what to recreate missing values as.
    orig = _TestClassE8(ival=1)
    todict = dataclass_to_dict(orig)
    assert todict == {}
    assert dataclass_from_dict(_TestClassE8, todict) == orig

    # Instantiate with the dataclass default and it should still get
    # explicitly despite the store_default=False because soft_default
    # takes precedence.
    orig = _TestClassE8()
    todict = dataclass_to_dict(orig)
    assert todict == {'ival': 2}
    assert dataclass_from_dict(_TestClassE8, todict) == orig


def test_enum_fallback() -> None:
    """Test enum_fallback IOAttr values."""
    # pylint: disable=missing-class-docstring
    # pylint: disable=unused-variable

    @ioprepped
    @dataclass
    class TestClass:

        class TestEnum1(Enum):
            VAL1 = 'val1'
            VAL2 = 'val2'
            VAL3 = 'val3'

        class TestEnum2(Enum):
            VAL1 = 'val1'
            VAL2 = 'val2'
            VAL3 = 'val3'

        enum1val: Annotated[TestEnum1, IOAttrs('e1')]
        enum2val: Annotated[
            TestEnum2, IOAttrs('e2', enum_fallback=TestEnum2.VAL1)
        ]

    # All valid values; should work.
    _obj = dataclass_from_dict(TestClass, {'e1': 'val1', 'e2': 'val1'})

    # Bad Enum1 value; should fail since there's no fallback.
    with pytest.raises(ValueError):
        _obj = dataclass_from_dict(TestClass, {'e1': 'val4', 'e2': 'val1'})

    # Bad Enum2 value; the attr provides a fallback but still should
    # fail since we didn't explicitly specify lossy loading.
    with pytest.raises(ValueError):
        obj = dataclass_from_dict(TestClass, {'e1': 'val1', 'e2': 'val4'})

    # Bad Enum2 value; should successfully substitute our fallback value
    # since we specify lossy loading.
    obj_w_fb = dataclass_from_dict(
        TestClass, {'e1': 'val1', 'e2': 'val4'}, lossy=True
    )
    assert obj_w_fb.enum2val is obj_w_fb.TestEnum2.VAL1

    # Allowing fallbacks means data might be lost on any load, so we
    # disallow writes for such data to be safe.
    with pytest.raises(ValueError):
        dataclass_to_dict(obj_w_fb)

    # Using wrong type as enum_fallback should fail.
    with pytest.raises(TypeError):

        @ioprepped
        @dataclass
        class TestClass2:

            class TestEnum1(Enum):
                VAL1 = 'val1'
                VAL2 = 'val2'

            class TestEnum2(Enum):
                VAL1 = 'val1'
                VAL2 = 'val2'

            enum1val: Annotated[
                TestEnum1, IOAttrs('e1', enum_fallback=TestEnum2.VAL1)
            ]


class MTTestTypeID(Enum):
    """IDs for our multi-type class."""

    CLASS_1 = 'm1'
    CLASS_2 = 'm2'


class MTTestBase(IOMultiType[MTTestTypeID]):
    """Our multi-type class.

    These top level multi-type classes are special parent classes
    that know about all of their child classes and how to serialize
    & deserialize them using explicit type ids. We can then use the
    parent class in annotations and dataclassio will do the right thing.
    Useful for stuff like Message classes where we may want to store a
    bunch of different types of them into one place.
    """

    @override
    @classmethod
    def get_type(cls, type_id: MTTestTypeID) -> type[MTTestBase]:
        """Return the subclass for each of our type-ids."""

        # This uses assert_never() to ensure we cover all cases in the
        # enum. Though this is less efficient than looking up by dict
        # would be. If we had lots of values we could also support lazy
        # loading by importing classes only when their value is being
        # requested.
        val: type[MTTestBase]
        if type_id is MTTestTypeID.CLASS_1:
            val = MTTestClass1
        elif type_id is MTTestTypeID.CLASS_2:
            val = MTTestClass2
        else:
            assert_never(type_id)
        return val

    @override
    @classmethod
    def get_type_id(cls) -> MTTestTypeID:
        """Provide the type-id for this subclass."""
        # If we wanted, we could just maintain a static mapping of
        # types-to-ids here, but there are benefits to letting each
        # child class speak for itself. Namely that we can do
        # lazy-loading and don't need to have all types present here.

        # So we'll let all our child classes override this.
        raise NotImplementedError()


@ioprepped
@dataclass(frozen=True)  # Frozen so we can test in set()
class MTTestClass1(MTTestBase):
    """A test child-class for use with our multi-type class."""

    ival: int

    @override
    @classmethod
    def get_type_id(cls) -> MTTestTypeID:
        return MTTestTypeID.CLASS_1


@ioprepped
@dataclass(frozen=True)  # Frozen so we can test in set()
class MTTestClass2(MTTestBase):
    """Another test child-class for use with our multi-type class."""

    sval: str

    @override
    @classmethod
    def get_type_id(cls) -> MTTestTypeID:
        return MTTestTypeID.CLASS_2


def test_multi_type() -> None:
    """Test IOMultiType stuff."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # Test converting single instances back and forth.
    val1: MTTestBase = MTTestClass1(ival=123)
    tpname = MTTestBase.get_type_id_storage_name()
    outdict = dataclass_to_dict(val1)
    assert outdict == {'ival': 123, tpname: 'm1'}
    val2: MTTestBase = MTTestClass2(sval='whee')
    outdict2 = dataclass_to_dict(val2)
    assert outdict2 == {'sval': 'whee', tpname: 'm2'}

    # Make sure types and values work for both concrete types and the
    # multi-type.
    assert_type(dataclass_from_dict(MTTestClass1, outdict), MTTestClass1)
    assert_type(dataclass_from_dict(MTTestBase, outdict), MTTestBase)

    assert dataclass_from_dict(MTTestClass1, outdict) == val1
    assert dataclass_from_dict(MTTestClass2, outdict2) == val2
    assert dataclass_from_dict(MTTestBase, outdict) == val1
    assert dataclass_from_dict(MTTestBase, outdict2) == val2

    # Trying to load as a multi-type should fail if there is no type
    # value present.
    outdictmod = copy.deepcopy(outdict)
    del outdictmod[tpname]
    with pytest.raises(ValueError):
        dataclass_from_dict(MTTestBase, outdictmod)

    # However it should work when loading an exact type. This can be
    # necessary to gracefully upgrade old data to multi-type form.
    dataclass_from_dict(MTTestClass1, outdictmod)

    # Now test our multi-type embedded in other classes. We should be
    # able to throw a mix of things in there and have them deserialize
    # back the types we started with.

    # Individual values:

    @ioprepped
    @dataclass
    class _TestContainerClass1:
        obj_a: MTTestBase
        obj_b: MTTestBase

    container1 = _TestContainerClass1(
        obj_a=MTTestClass1(234), obj_b=MTTestClass2('987')
    )
    outdict = dataclass_to_dict(container1)
    container1b = dataclass_from_dict(_TestContainerClass1, outdict)
    assert container1 == container1b

    # Lists:

    @ioprepped
    @dataclass
    class _TestContainerClass2:
        objs: list[MTTestBase]

    container2 = _TestContainerClass2(
        objs=[MTTestClass1(111), MTTestClass2('bbb')]
    )
    outdict = dataclass_to_dict(container2)
    container2b = dataclass_from_dict(_TestContainerClass2, outdict)
    assert container2 == container2b

    # Dict values:

    @ioprepped
    @dataclass
    class _TestContainerClass3:
        objs: dict[int, MTTestBase]

    container3 = _TestContainerClass3(
        objs={1: MTTestClass1(456), 2: MTTestClass2('gronk')}
    )
    outdict = dataclass_to_dict(container3)
    container3b = dataclass_from_dict(_TestContainerClass3, outdict)
    assert container3 == container3b

    # Tuples:

    @ioprepped
    @dataclass
    class _TestContainerClass4:
        objs: tuple[MTTestBase, MTTestBase]

    container4 = _TestContainerClass4(
        objs=(MTTestClass1(932), MTTestClass2('potato'))
    )
    outdict = dataclass_to_dict(container4)
    container4b = dataclass_from_dict(_TestContainerClass4, outdict)
    assert container4 == container4b

    # Sets (note: dataclasses must be frozen for this to work):

    @ioprepped
    @dataclass
    class _TestContainerClass5:
        objs: set[MTTestBase]

    container5 = _TestContainerClass5(
        objs={MTTestClass1(424), MTTestClass2('goo')}
    )
    outdict = dataclass_to_dict(container5)
    container5b = dataclass_from_dict(_TestContainerClass5, outdict)
    assert container5 == container5b

    # Optionals.

    @ioprepped
    @dataclass
    class _TestContainerClass6:
        obj: MTTestBase | None

    container6 = _TestContainerClass6(obj=None)
    outdict = dataclass_to_dict(container6)
    container6b = dataclass_from_dict(_TestContainerClass6, outdict)
    assert container6 == container6b

    container6 = _TestContainerClass6(obj=MTTestClass2('fwr'))
    outdict = dataclass_to_dict(container6)
    container6b = dataclass_from_dict(_TestContainerClass6, outdict)
    assert container6 == container6b

    @ioprepped
    @dataclass
    class _TestContainerClass7:
        obj: Annotated[
            MTTestBase | None,
            IOAttrs('o', soft_default=None),
        ]

    container7 = _TestContainerClass7(obj=None)
    outdict = dataclass_to_dict(container7)
    container7b = dataclass_from_dict(_TestContainerClass7, {})
    assert container7 == container7b


class MTTest2TypeID(Enum):
    """IDs for our multi-type class."""

    CLASS_1 = 'm1'
    CLASS_2 = 'm2'
    CLASS_3 = 'm3'


class MTTest2Base(IOMultiType[MTTest2TypeID]):
    """Another multi-type test.

    This one tests overriding type-id-storage-name.
    """

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return 'type'

    @override
    @classmethod
    def get_type(cls, type_id: MTTest2TypeID) -> type[MTTest2Base]:
        val: type[MTTest2Base]
        if type_id is MTTest2TypeID.CLASS_1:
            val = MTTest2Class1
        elif type_id is MTTest2TypeID.CLASS_2:
            val = MTTest2Class2
        elif type_id is MTTest2TypeID.CLASS_3:
            val = MTTest2Class3
        else:
            assert_never(type_id)
        return val

    @override
    @classmethod
    def get_type_id(cls) -> MTTest2TypeID:
        raise NotImplementedError()


@ioprepped
@dataclass
class MTTest2Class1(MTTest2Base):
    """A test child-class for use with our multi-type class."""

    ival: int

    @override
    @classmethod
    def get_type_id(cls) -> MTTest2TypeID:
        return MTTest2TypeID.CLASS_1


@ioprepped
@dataclass
class MTTest2Class2(MTTest2Base):
    """Another test child-class for use with our multi-type class."""

    sval: str

    @override
    @classmethod
    def get_type_id(cls) -> MTTest2TypeID:
        return MTTest2TypeID.CLASS_2


@ioprepped
@dataclass
class MTTest2Class3(MTTest2Base):
    """Another test child-class for use with our multi-type class."""

    type: str = ''

    @override
    @classmethod
    def get_type_id(cls) -> MTTest2TypeID:
        return MTTest2TypeID.CLASS_3


def test_multi_type_2() -> None:
    """Test IOMultiType stuff."""

    # Make sure this serializes correctly with 'test' as a type name.

    val1: MTTest2Base = MTTest2Class1(ival=123)
    outdict = dataclass_to_dict(val1)
    assert outdict == {'ival': 123, 'type': 'm1'}

    val1b = dataclass_from_dict(MTTest2Base, outdict)
    assert val1 == val1b

    val2: MTTest2Base = MTTest2Class2(sval='whee')
    outdict2 = dataclass_to_dict(val2)
    assert outdict2 == {'sval': 'whee', 'type': 'm2'}

    val2b = dataclass_from_dict(MTTest2Base, outdict2)
    assert val2 == val2b

    # If a multi-type class uses 'type' itself, make sure we error
    # instead of letting things break due to the name clash. In an ideal
    # world this would error at prep time, but IOMultiType is built
    # around lazy-loading so it can't actually examine all types at that
    # time.

    # Make sure we error on output...
    val3: MTTest2Base = MTTest2Class3()
    with pytest.raises(RuntimeError):
        outdict = dataclass_to_dict(val3)

    # And input.
    indict3 = {'type': 'm3'}
    with pytest.raises(RuntimeError):
        val3 = dataclass_from_dict(MTTest2Base, indict3)


# Define 2 variations of Test3 - an 'old' and 'new' one - to simulate
# older/newer versions of the same schema.
class MTTest3OldTypeID(Enum):
    """IDs for our multi-type class."""

    CLASS_1 = 'm1'
    CLASS_2 = 'm2'


class MTTest3OldBase(IOMultiType[MTTest3OldTypeID]):
    """Our multi-type class.

    These top level multi-type classes are special parent classes
    that know about all of their child classes and how to serialize
    & deserialize them using explicit type ids. We can then use the
    parent class in annotations and dataclassio will do the right thing.
    Useful for stuff like Message classes where we may want to store a
    bunch of different types of them into one place.
    """

    @override
    @classmethod
    def get_type(cls, type_id: MTTest3OldTypeID) -> type[MTTest3OldBase]:
        """Return the subclass for each of our type-ids."""

        # This uses assert_never() to ensure we cover all cases in the
        # enum. Though this is less efficient than looking up by dict
        # would be. If we had lots of values we could also support lazy
        # loading by importing classes only when their value is being
        # requested.
        val: type[MTTest3OldBase]
        if type_id is MTTest3OldTypeID.CLASS_1:
            val = MTTest3OldClass1
        elif type_id is MTTest3OldTypeID.CLASS_2:
            val = MTTest3OldClass2
        else:
            assert_never(type_id)
        return val

    @override
    @classmethod
    def get_type_id(cls) -> MTTest3OldTypeID:
        """Provide the type-id for this subclass."""
        # If we wanted, we could just maintain a static mapping of
        # types-to-ids here, but there are benefits to letting each
        # child class speak for itself. Namely that we can do
        # lazy-loading and don't need to have all types present here.

        # So we'll let all our child classes override this.
        raise NotImplementedError()

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> MTTest3OldBase | None:
        # Define a fallback here that can be returned in cases of
        # unrecognized types (though only if 'lossy' is enabled for the
        # load).
        return MTTest3OldClass1(ival=42)


@ioprepped
@dataclass
class MTTest3OldClass1(MTTest3OldBase):
    """A test child-class for use with our multi-type class."""

    ival: int

    @override
    @classmethod
    def get_type_id(cls) -> MTTest3OldTypeID:
        return MTTest3OldTypeID.CLASS_1


@ioprepped
@dataclass
class MTTest3OldClass2(MTTest3OldBase):
    """Another test child-class for use with our multi-type class."""

    sval: str

    @override
    @classmethod
    def get_type_id(cls) -> MTTest3OldTypeID:
        return MTTest3OldTypeID.CLASS_2


@ioprepped
@dataclass
class MTTest3OldWrapper:
    """Testing something *containing* a test class instance."""

    child: MTTest3OldBase


@ioprepped
@dataclass
class MTTest3OldListWrapper:
    """Testing something *containing* a test class instance."""

    children: list[MTTest3OldBase]


class MTTest3NewTypeID(Enum):
    """IDs for our multi-type class."""

    CLASS_1 = 'm1'
    CLASS_2 = 'm2'
    CLASS_3 = 'm3'


class MTTest3NewBase(IOMultiType[MTTest3NewTypeID]):
    """Our multi-type class.

    These top level multi-type classes are special parent classes
    that know about all of their child classes and how to serialize
    & deserialize them using explicit type ids. We can then use the
    parent class in annotations and dataclassio will do the right thing.
    Useful for stuff like Message classes where we may want to store a
    bunch of different types of them into one place.
    """

    @override
    @classmethod
    def get_type(cls, type_id: MTTest3NewTypeID) -> type[MTTest3NewBase]:
        """Return the subclass for each of our type-ids."""

        # This uses assert_never() to ensure we cover all cases in the
        # enum. Though this is less efficient than looking up by dict
        # would be. If we had lots of values we could also support lazy
        # loading by importing classes only when their value is being
        # requested.
        val: type[MTTest3NewBase]
        if type_id is MTTest3NewTypeID.CLASS_1:
            val = MTTest3NewClass1
        elif type_id is MTTest3NewTypeID.CLASS_2:
            val = MTTest3NewClass2
        elif type_id is MTTest3NewTypeID.CLASS_3:
            val = MTTest3NewClass3
        else:
            assert_never(type_id)
        return val

    @override
    @classmethod
    def get_type_id(cls) -> MTTest3NewTypeID:
        """Provide the type-id for this subclass."""
        # If we wanted, we could just maintain a static mapping of
        # types-to-ids here, but there are benefits to letting each
        # child class speak for itself. Namely that we can do
        # lazy-loading and don't need to have all types present here.

        # So we'll let all our child classes override this.
        raise NotImplementedError()

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> MTTest3NewBase | None:
        # Define a fallback here that can be returned in cases of
        # unrecognized types (though only if 'lossy' is enabled for the
        # load).
        return MTTest3NewClass1(ival=43)


@ioprepped
@dataclass
class MTTest3NewClass1(MTTest3NewBase):
    """A test child-class for use with our multi-type class."""

    ival: int

    @override
    @classmethod
    def get_type_id(cls) -> MTTest3NewTypeID:
        return MTTest3NewTypeID.CLASS_1


@ioprepped
@dataclass
class MTTest3NewClass2(MTTest3NewBase):
    """Another test child-class for use with our multi-type class."""

    sval: str

    @override
    @classmethod
    def get_type_id(cls) -> MTTest3NewTypeID:
        return MTTest3NewTypeID.CLASS_2


@ioprepped
@dataclass
class MTTest3NewClass3(MTTest3NewBase):
    """Another test child-class for use with our multi-type class."""

    bval: bool

    @override
    @classmethod
    def get_type_id(cls) -> MTTest3NewTypeID:
        return MTTest3NewTypeID.CLASS_3


@ioprepped
@dataclass
class MTTest3NewWrapper:
    """Testing something *containing* a test class instance."""

    child: MTTest3NewBase


@ioprepped
@dataclass
class MTTest3NewListWrapper:
    """Testing something *containing* a test class instance."""

    children: list[MTTest3NewBase]


def test_multi_type_3() -> None:
    """Test IOMultiType stuff."""

    # Define some data using our 'newer' schema and it should load using
    # our 'older' one.
    data2 = dataclass_to_dict(MTTest3NewClass2(sval='foof'))
    obj2 = dataclass_from_dict(MTTest3OldBase, data2)
    assert isinstance(obj2, MTTest3OldClass2)

    # However, this won't work with class 3 which only exists in the
    # 'newer' schema. So this should fail.
    data3 = dataclass_to_dict(MTTest3NewClass3(bval=True))
    with pytest.raises(ValueError):
        obj3 = dataclass_from_dict(MTTest3OldBase, data3)

    # Running in lossy mode should succeed, however, since we define a
    # fallback call on our multitype. The fallback should give us a
    # particular MTTestClass1.
    obj3 = dataclass_from_dict(MTTest3OldBase, data3, lossy=True)
    assert obj3 == MTTest3OldClass1(ival=42)

    # ----------------------------------------------------------------
    # Now do the same tests with a dataclass *containing* one of these
    # dataclasses (since this goes through a different code path).
    # ----------------------------------------------------------------

    # Define some data using our 'newer' schema and it should load using
    # our 'older' one.
    wdata2 = dataclass_to_dict(
        MTTest3NewWrapper(child=MTTest3NewClass2(sval='foof'))
    )
    wobj2 = dataclass_from_dict(MTTest3OldWrapper, wdata2)
    assert isinstance(wobj2, MTTest3OldWrapper)
    assert isinstance(wobj2.child, MTTest3OldClass2)

    # However, this won't work with class 3 which only exists in the
    # 'newer' schema. So this should fail.
    wdata3 = dataclass_to_dict(MTTest3NewWrapper(MTTest3NewClass3(bval=True)))
    with pytest.raises(ValueError):
        wobj3 = dataclass_from_dict(MTTest3OldWrapper, wdata3)

    # Running in lossy mode should succeed, however, since we define a
    # fallback call on our multitype. The fallback should give us a
    # particular MTTestClass1.
    wobj3 = dataclass_from_dict(MTTest3OldWrapper, wdata3, lossy=True)
    assert wobj3 == MTTest3OldWrapper(child=MTTest3OldClass1(ival=42))

    # ----------------------------------------------------------------
    # Once more with a dataclass containing a *sequence* of these, which
    # is a slightly different code path again.
    # ----------------------------------------------------------------

    # Define some data using our 'newer' schema and it should load using
    # our 'older' one.
    wldata2 = dataclass_to_dict(
        MTTest3NewListWrapper(children=[MTTest3NewClass2(sval='foof')])
    )
    wlobj2 = dataclass_from_dict(MTTest3OldListWrapper, wldata2)
    assert isinstance(wlobj2, MTTest3OldListWrapper)
    assert isinstance(wlobj2.children[0], MTTest3OldClass2)

    # However, this won't work with class 3 which only exists in the
    # 'newer' schema. So this should fail.
    wldata3 = dataclass_to_dict(
        MTTest3NewListWrapper([MTTest3NewClass3(bval=True)])
    )
    with pytest.raises(ValueError):
        wlobj3 = dataclass_from_dict(MTTest3OldListWrapper, wldata3)

    # Running in lossy mode should succeed, however, since we define a
    # fallback call on our multitype. The fallback should give us a
    # particular MTTestClass1.
    wlobj3 = dataclass_from_dict(MTTest3OldListWrapper, wldata3, lossy=True)
    assert wlobj3 == MTTest3OldListWrapper(children=[MTTest3OldClass1(ival=42)])


def test_float_timestamps() -> None:
    """Test exporting times as floats instead of int arrays."""

    @ioprepped
    @dataclass
    class _TestClass:
        tmval: Annotated[datetime.datetime, IOAttrs(float_times=True)]
        tmval2: Annotated[datetime.datetime, IOAttrs(float_times=False)]
        tmval3: datetime.datetime

    now = utc_now()
    testclass = _TestClass(tmval=now, tmval2=now, tmval3=now)
    testclass_dict = dataclass_to_dict(testclass)

    # Make sure prefer_timestamps True gives us a float and False (or
    # default) gives us the int list.
    assert isinstance(testclass_dict.get('tmval'), float)
    assert isinstance(testclass_dict.get('tmval2'), list)
    assert isinstance(testclass_dict.get('tmval3'), list)

    # Now convert back to get 3 datetime objs and make sure they are
    # basically the same time (float precision could mean they're not
    # 100% identical).
    testclass2 = dataclass_from_dict(_TestClass, testclass_dict)
    assert abs((testclass2.tmval2 - testclass2.tmval).total_seconds()) < 0.001
    assert abs((testclass2.tmval - testclass.tmval).total_seconds()) < 0.001

    # The restored int based ones should be *exactly* the same as what
    # we started with.
    assert testclass2.tmval2 == testclass.tmval2
    assert testclass2.tmval3 == testclass.tmval3


def test_float_timedeltas() -> None:
    """Test exporting times as floats instead of int arrays."""

    @ioprepped
    @dataclass
    class _TestClass:
        tmval: Annotated[datetime.timedelta, IOAttrs(float_times=True)]
        tmval2: Annotated[datetime.timedelta, IOAttrs(float_times=False)]
        tmval3: datetime.timedelta

    testdelta = datetime.timedelta(days=123, hours=12.3423, seconds=2.345)

    testclass = _TestClass(tmval=testdelta, tmval2=testdelta, tmval3=testdelta)
    testclass_dict = dataclass_to_dict(testclass)

    # Make sure prefer_timestamps True gives us a float and False (or
    # default) gives us the int list.
    assert isinstance(testclass_dict.get('tmval'), float)
    assert isinstance(testclass_dict.get('tmval2'), list)
    assert isinstance(testclass_dict.get('tmval3'), list)

    # Now convert back to get 3 timedelta objs and make sure they are
    # basically the same (float precision could mean they're not 100%
    # identical).
    testclass2 = dataclass_from_dict(_TestClass, testclass_dict)
    assert abs((testclass2.tmval2 - testclass2.tmval).total_seconds()) < 0.001

    # The restored int based ones should be *exactly* the same as what
    # we started with.
    assert testclass2.tmval2 == testclass.tmval2
    assert testclass2.tmval3 == testclass.tmval3
