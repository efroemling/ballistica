# Released under the MIT License. See LICENSE for details.
#
"""Testing dataclasses functionality."""
# pylint: disable=too-many-lines

from __future__ import annotations

from enum import Enum
import datetime
from dataclasses import field, dataclass
from typing import TYPE_CHECKING, Any, Sequence, Annotated

import pytest

from efro.util import utc_now
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
)

if TYPE_CHECKING:
    pass


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
        # This doesn't actually set timezone on the datetime obj.
        dataclass_to_dict(_TestClass(datetimeval=datetime.datetime.utcnow()))


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

    # JSON output doesn't allow bytes or datetime objects
    # included in 'Any' data.
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

    # Define a few nested dataclass types, some of which
    # have storage names differing from their field names.
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

    # Attempting to return fields that aren't there should fail
    # in both type-checking and runtime.
    with pytest.raises(AttributeError):
        lookup.path(lambda obj: obj.sub1.val3)  # type: ignore

    # Returning non-field objects will fail at runtime
    # even if type-checking evaluates them as valid values.
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

    # Now define the same data but give it an adapter
    # so it can work with our incorrectly-formatted data.
    @ioprepped
    @dataclass
    class _TestClass2(IOExtendedData):
        vals: tuple[int, int]

        @classmethod
        def will_input(cls, data: dict) -> None:
            data['vals'] = data['vals'][:2]

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

    # These should succeed because it has a soft-default value to
    # fall back on.
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

    # We disallow passing a few mutable types as soft_defaults
    # just as dataclass does with regular defaults.
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

    # soft_defaults are not static-type-checked, but we do try to
    # catch basic type mismatches at prep time. Make sure that's working.
    # (we also do full value validation during input, but the more we catch
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

    # Make sure Unions/Optionals go through ok.
    # (note that mismatches currently aren't caught at prep time; just
    # checking the negative case here).
    @ioprepped
    @dataclass
    class _TestClassE4:
        lval: Annotated[str | None, IOAttrs(soft_default=None)]

    @ioprepped
    @dataclass
    class _TestClassE5:
        lval: Annotated[str | None, IOAttrs(soft_default='foo')]

    # Now try more in-depth examples: nested type mismatches like this
    # are currently not caught at prep-time but ARE caught during inputting.
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

    # If both a soft_default and regular field default are present,
    # make sure soft_default takes precedence (it applies before
    # data even hits the dataclass constructor).

    @ioprepped
    @dataclass
    class _TestClassE8:
        ival: Annotated[int, IOAttrs(soft_default=1, store_default=False)] = 2

    assert dataclass_from_dict(_TestClassE8, {}).ival == 1

    # Make sure soft_default gets used both when determining when
    # to omit values from output and what to recreate missing values as.
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
