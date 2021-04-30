# Released under the MIT License. See LICENSE for details.
#
"""Functionality for importing, exporting, and validating dataclasses.

This allows complex nested dataclasses to be flattened to json-compatible
data and restored from said data. It also gracefully handles and preserves
unrecognized attribute data, allowing older clients to interact with newer
data formats in a nondestructive manner.
"""

# Note: We do lots of comparing of exact types here which is normally
# frowned upon (stuff like isinstance() is usually encouraged).
# pylint: disable=unidiomatic-typecheck

from __future__ import annotations

import logging
from enum import Enum
import dataclasses
import typing
from typing import TYPE_CHECKING, TypeVar, Generic, get_type_hints

from efro.util import enum_by_value

if TYPE_CHECKING:
    from typing import Any, Dict, Type, Tuple, Optional

T = TypeVar('T')

# Types which we can pass through as-is.
SIMPLE_TYPES = {int, bool, str, float, type(None)}

# How deep we go when prepping nested types
# (basically for detecting recursive types)
MAX_RECURSION = 10

# Attr name for data we store on dataclass types as part of prep.
PREP_ATTR = '_DCIOPREP'

# Attr name for dict of extra attributes included on dataclass instances.
# Note that this is only added if extra attributes are present.
EXTRA_ATTRS_ATTR = '_DCIOEXATTRS'


def dataclass_to_dict(obj: Any, coerce_to_float: bool = True) -> dict:
    """Given a dataclass object, return a json-friendly dict.

    All values will be checked to ensure they match the types specified
    on fields. Note that a limited set of types and data configurations is
    supported.

    Values with type Any will be checked to ensure they match types supported
    directly by json. This does not include types such as tuples which are
    implicitly translated by Python's json module (as this would break
    the ability to do a lossless round-trip with data).

    If coerce_to_float is True, integer values present on float typed fields
    will be converted to floats in the dict output. If False, a TypeError
    will be triggered.
    """

    out = _Outputter(obj, create=True, coerce_to_float=coerce_to_float).run()
    assert isinstance(out, dict)
    return out


def dataclass_from_dict(cls: Type[T],
                        values: dict,
                        coerce_to_float: bool = True,
                        allow_unknown_attrs: bool = True,
                        discard_unknown_attrs: bool = False) -> T:
    """Given a dict, return a dataclass of a given type.

    The dict must be in the json-friendly format as emitted from
    dataclass_to_dict. This means that sequence values such as tuples or
    sets should be passed as lists, enums should be passed as their
    associated values, nested dataclasses should be passed as dicts, etc.

    All values are checked to ensure their types/values are valid.

    Data for attributes of type Any will be checked to ensure they match
    types supported directly by json. This does not include types such
    as tuples which are implicitly translated by Python's json module
    (as this would break the ability to do a lossless round-trip with data).

    If coerce_to_float is True, int values passed for float typed fields
    will be converted to float values. Otherwise a TypeError is raised.

    If allow_unknown_attrs is False, AttributeErrors will be raised for
    attributes present in the dict but not on the data class. Otherwise they
    will be preserved as part of the instance and included if it is
    exported back to a dict, unless discard_unknown_attrs is True, in which
    case they will simply be discarded.
    """
    return _Inputter(cls,
                     coerce_to_float=coerce_to_float,
                     allow_unknown_attrs=allow_unknown_attrs,
                     discard_unknown_attrs=discard_unknown_attrs).run(values)


def dataclass_validate(obj: Any, coerce_to_float: bool = True) -> None:
    """Ensure that values in a dataclass instance are the correct types."""

    # Simply run an output pass but tell it not to generate data;
    # only run validation.
    _Outputter(obj, create=False, coerce_to_float=coerce_to_float).run()


def dataclass_prep(cls: Type, extra_types: Dict[str, Type] = None) -> None:
    """Prep a dataclass type for use with this module's functionality.

    Prepping ensures that all types contained in a data class as well as
    the usage of said types are supported by this module and pre-builds
    necessary constructs needed for encoding/decoding/etc.

    Prepping will happen on-the-fly as needed, but a warning will be
    emitted in such cases, as it is better to explicitly prep all used types
    early in a process to ensure any invalid types or configuration are caught
    immediately.

    Prepping a dataclass involves evaluating its type annotations, which,
    as of PEP 563, are stored simply as strings. This evaluation is done
    in the module namespace containing the class, so all referenced types
    must be defined at that level. The exception is Typing types (Optional,
    Union, etc.) which are often defined under an 'if TYPE_CHECKING'
    conditional and thus not available at runtime, so are explicitly made
    available during annotation evaluation.
    """
    PrepSession(explicit=True,
                extra_types=extra_types).prep_dataclass(cls, recursion_level=0)


def prepped(cls: Type[T]) -> Type[T]:
    """Class decorator to easily prep a dataclass at definition time.

    Note that in some cases it may not be possible to prep a dataclass
    immediately (such as when its type annotations refer to forward-declared
    types). In these cases, dataclass_prep() should be explicitly called for
    the class once it is safe to do so.
    """
    dataclass_prep(cls)
    return cls


@dataclasses.dataclass
class PrepData:
    """Data we prepare and cache for a class during prep.

    This data is used as part of the encoding/decoding/validating process.
    """

    # Resolved annotation data with 'live' classes.
    annotations: Dict[str, Any]


class PrepSession:
    """Context for a prep."""

    def __init__(self, explicit: bool, extra_types: Optional[Dict[str, Type]]):
        self.explicit = explicit
        self.extra_types = extra_types

    def prep_dataclass(self, cls: Type, recursion_level: int) -> PrepData:
        """Run prep on a dataclass if necessary and return its prep data."""

        existing_data = getattr(cls, PREP_ATTR, None)
        if existing_data is not None:
            assert isinstance(existing_data, PrepData)
            return existing_data

        # If we run into classes containing themselves, we may have
        # to do something smarter to handle it.
        if recursion_level > MAX_RECURSION:
            raise RuntimeError('Max recursion exceeded.')

        # We should only be passed classes which are dataclasses.
        if not isinstance(cls, type) or not dataclasses.is_dataclass(cls):
            raise TypeError(f'Passed arg {cls} is not a dataclass type.')

        # Generate a warning on non-explicit preps; we prefer prep to
        # happen explicitly at runtime so errors can be detected early on.
        if not self.explicit:
            logging.warning(
                'efro.dataclassio: implicitly prepping dataclass: %s.'
                ' It is highly recommended to explicitly prep dataclasses'
                ' as soon as possible after definition (via'
                ' efro.dataclassio.dataclass_prep() or the'
                ' @efro.dataclassio.prepped decorator).', cls)

        localns: Dict[str, Any] = {
            'Optional': typing.Optional,
            'Union': typing.Union,
            'List': typing.List,
            'Tuple': typing.Tuple,
            'Sequence': typing.Sequence,
            'Set': typing.Set,
            'Any': typing.Any,
            'Dict': typing.Dict,
        }
        if self.extra_types is not None:
            localns.update(self.extra_types)

        try:
            # Use default globalns which should be the class' module,
            # but provide our own locals to cover things like typing.*
            # which are generally not actually present at runtime for us.
            resolved_annotations = get_type_hints(cls, localns=localns)
        except Exception as exc:
            raise RuntimeError(
                f'Dataclass prep failed with error: {exc}.') from exc

        # Ok; we've resolved actual types for this dataclass.
        # now recurse through them, verifying that we support all contained
        # types and prepping any contained dataclass types.
        for attrname, attrtype in resolved_annotations.items():
            self.prep_type(cls,
                           attrname,
                           attrtype,
                           recursion_level=recursion_level + 1)

        # Success! Store our resolved stuff with the class and we're done.
        prepdata = PrepData(annotations=resolved_annotations)
        setattr(cls, PREP_ATTR, prepdata)
        return prepdata

    def prep_type(self, cls: Type, attrname: str, anntype: Any,
                  recursion_level: int) -> None:
        """Run prep on a dataclass."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        # If we run into classes containing themselves, we may have
        # to do something smarter to handle it.
        if recursion_level > MAX_RECURSION:
            raise RuntimeError('Max recursion exceeded.')

        origin = _get_origin(anntype)

        if origin is typing.Union:
            self.prep_union(cls,
                            attrname,
                            anntype,
                            recursion_level=recursion_level + 1)
            return

        if anntype is typing.Any:
            return

        # Everything below this point assumes the annotation type resolves
        # to a concrete type.
        if not isinstance(origin, type):
            raise TypeError(
                f'Unsupported type found for \'{attrname}\' on {cls}:'
                f' {anntype}')

        if origin in SIMPLE_TYPES:
            return

        # For sets and lists, check out their single contained type (if any).
        if origin in (list, set):
            childtypes = typing.get_args(anntype)
            if len(childtypes) == 0:
                # This is equivalent to Any; nothing else needs checking.
                return
            if len(childtypes) > 1:
                raise TypeError(
                    f'Unrecognized typing arg count {len(childtypes)}'
                    f" for {anntype} attr '{attrname}' on {cls}")
            self.prep_type(cls,
                           attrname,
                           childtypes[0],
                           recursion_level=recursion_level + 1)
            return

        if origin is dict:
            childtypes = typing.get_args(anntype)
            assert len(childtypes) in (0, 2)

            # For key types we support Any, str, int,
            # and Enums with uniform str/int values.
            if not childtypes or childtypes[0] is typing.Any:
                # 'Any' needs no further checks (just checked per-instance).
                pass
            elif childtypes[0] in (str, int):
                # str and int are all good as keys.
                pass
            elif issubclass(childtypes[0], Enum):
                # Allow our usual str or int enum types as keys.
                self.prep_enum(childtypes[0])
            else:
                raise TypeError(
                    f'Dict key type {childtypes[0]} for \'{attrname}\''
                    f' on {cls} is not supported by dataclassio.')

            # For value types we support any of our normal types.
            if not childtypes or _get_origin(childtypes[1]) is typing.Any:
                # 'Any' needs no further checks (just checked per-instance).
                pass
            else:
                self.prep_type(cls,
                               attrname,
                               childtypes[1],
                               recursion_level=recursion_level + 1)
            return

        if issubclass(origin, Enum):
            self.prep_enum(origin)
            return

        if dataclasses.is_dataclass(origin):
            self.prep_dataclass(origin, recursion_level=recursion_level + 1)
            return

        raise TypeError(f"Attr '{attrname}' on {cls} contains type '{anntype}'"
                        f' which is not supported by dataclassio.')

    def prep_union(self, cls: Type, attrname: str, anntype: Any,
                   recursion_level: int) -> None:
        """Run prep on a Union type."""
        typeargs = typing.get_args(anntype)
        if (len(typeargs) != 2
                or len([c for c in typeargs if c is type(None)]) != 1):
            raise TypeError(f'Union {anntype} for attr \'{attrname}\' on'
                            f' {cls} is not supported by dataclassio;'
                            f' only 2 member Unions with one type being None'
                            f' are supported.')
        for childtype in typeargs:
            self.prep_type(cls,
                           attrname,
                           childtype,
                           recursion_level=recursion_level + 1)

    def prep_enum(self, enumtype: Type[Enum]) -> None:
        """Run prep on an enum type."""

        valtype: Any = None

        # We currently support enums with str or int values; fail if we
        # find any others.
        for enumval in enumtype:
            if not isinstance(enumval.value, (str, int)):
                raise TypeError(f'Enum value {enumval} has value type'
                                f' {type(enumval.value)}; only str and int is'
                                f' supported by dataclassio.')
            if valtype is None:
                valtype = type(enumval.value)
            else:
                if type(enumval.value) is not valtype:
                    raise TypeError(f'Enum type {enumtype} has multiple'
                                    f' value types; dataclassio requires'
                                    f' them to be uniform.')


def _is_valid_json(obj: Any) -> bool:
    """Return whether a value consists solely of json-supported types.

    Note that this does not include things like tuples which are
    implicitly translated to lists by python's json module.
    """
    if obj is None:
        return True

    objtype = type(obj)
    if objtype in (int, float, str, bool):
        return True
    if objtype is dict:
        # JSON 'objects' supports only string dict keys, but all value types.
        return all(
            type(k) is str and _is_valid_json(v) for k, v in obj.items())
    if objtype is list:
        return all(_is_valid_json(elem) for elem in obj)
    return False


def _raise_type_error(fieldpath: str, valuetype: Type,
                      expected: Tuple[Type, ...]) -> None:
    """Raise an error when a field value's type does not match expected."""
    assert isinstance(expected, tuple)
    assert all(isinstance(e, type) for e in expected)
    if len(expected) == 1:
        expected_str = expected[0].__name__
    else:
        names = ', '.join(t.__name__ for t in expected)
        expected_str = f'Union[{names}]'
    raise TypeError(f'Invalid value type for "{fieldpath}";'
                    f' expected "{expected_str}", got'
                    f' "{valuetype.__name__}".')


def _get_origin(anntype: Any) -> Any:
    """Given a type annotation, return its origin or itself if there is none.

    This differs from typing.get_origin in that it will never return None.
    This lets us use the same code path for handling typing.List
    that we do for handling list, which is good since they can be used
    interchangeably in annotations.
    """
    origin = typing.get_origin(anntype)
    return anntype if origin is None else origin


class _Outputter:
    """Validates or exports data contained in a dataclass instance."""

    def __init__(self, obj: Any, create: bool, coerce_to_float: bool) -> None:
        self._obj = obj
        self._create = create
        self._coerce_to_float = coerce_to_float

    def run(self) -> Any:
        """Do the thing."""
        return self._process_dataclass(type(self._obj), self._obj, '')

    def _process_dataclass(self, cls: Type, obj: Any, fieldpath: str) -> Any:
        prep = PrepSession(explicit=False,
                           extra_types=None).prep_dataclass(type(obj),
                                                            recursion_level=0)
        fields = dataclasses.fields(obj)
        out: Optional[Dict[str, Any]] = {} if self._create else None
        for field in fields:
            fieldname = field.name
            if fieldpath:
                subfieldpath = f'{fieldpath}.{fieldname}'
            else:
                subfieldpath = fieldname
            fieldtype = prep.annotations[fieldname]
            value = getattr(obj, fieldname)
            outvalue = self._process_value(cls, subfieldpath, fieldtype, value)
            if self._create:
                assert out is not None
                out[fieldname] = outvalue

        # If there's extra-attrs stored on us, check/include them.
        extra_attrs = getattr(obj, EXTRA_ATTRS_ATTR, None)
        if isinstance(extra_attrs, dict):
            if not _is_valid_json(extra_attrs):
                raise TypeError(
                    f'Extra attrs on {fieldpath} contains data type(s)'
                    f' not supported by json.')
            if self._create:
                assert out is not None
                out.update(extra_attrs)
        return out

    def _process_value(self, cls: Type, fieldpath: str, anntype: Any,
                       value: Any) -> Any:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        origin = _get_origin(anntype)

        if origin is typing.Any:
            if not _is_valid_json(value):
                raise TypeError(f'Invalid value type for \'{fieldpath}\';'
                                f" 'Any' typed values must be types directly"
                                f' supported by json; got'
                                f" '{type(value).__name__}'.")
            return value if self._create else None

        if origin is typing.Union:
            # Currently the only unions we support are None/Value
            # (translated from Optional), which we verified on prep.
            # So let's treat this as a simple optional case.
            if value is None:
                return None
            childanntypes_l = [
                c for c in typing.get_args(anntype) if c is not type(None)
            ]
            assert len(childanntypes_l) == 1
            return self._process_value(cls, fieldpath, childanntypes_l[0],
                                       value)

        # Everything below this point assumes the annotation type resolves
        # to a concrete type. (This should have been verified at prep time).
        assert isinstance(origin, type)

        # For simple flat types, look for exact matches:
        if origin in SIMPLE_TYPES:
            if type(value) is not origin:
                # Special case: if they want to coerce ints to floats, do so.
                if (self._coerce_to_float and origin is float
                        and type(value) is int):
                    return float(value) if self._create else None
                _raise_type_error(fieldpath, type(value), (origin, ))
            return value if self._create else None

        if origin is list:
            if not isinstance(value, list):
                raise TypeError(f'Expected a list for {fieldpath};'
                                f' found a {type(value)}')
            childanntypes = typing.get_args(anntype)

            # 'Any' type children; make sure they are valid json values.
            if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
                for i, child in enumerate(value):
                    if not _is_valid_json(child):
                        raise TypeError(
                            f'Item {i} of {fieldpath} contains'
                            f' data type(s) not supported by json.')
                # Hmm; should we do a copy here?
                return value if self._create else None

            # We contain elements of some specified type.
            assert len(childanntypes) == 1
            if self._create:
                return [
                    self._process_value(cls, fieldpath, childanntypes[0], x)
                    for x in value
                ]
            for x in value:
                self._process_value(cls, fieldpath, childanntypes[0], x)
            return None

        if origin is set:
            if not isinstance(value, set):
                raise TypeError(f'Expected a set for {fieldpath};'
                                f' found a {type(value)}')
            childanntypes = typing.get_args(anntype)

            # 'Any' type children; make sure they are valid Any values.
            if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
                for child in value:
                    if not _is_valid_json(child):
                        raise TypeError(
                            f'Set at {fieldpath} contains'
                            f' data type(s) not supported by json.')
                return list(value) if self._create else None

            # We contain elements of some specified type.
            assert len(childanntypes) == 1
            if self._create:
                # Note: we output json-friendly values so this becomes
                # a list.
                return [
                    self._process_value(cls, fieldpath, childanntypes[0], x)
                    for x in value
                ]
            for x in value:
                self._process_value(cls, fieldpath, childanntypes[0], x)
            return None

        if origin is dict:
            return self._process_dict(cls, fieldpath, anntype, value)

        if dataclasses.is_dataclass(origin):
            if not isinstance(value, origin):
                raise TypeError(f'Expected a {origin} for {fieldpath};'
                                f' found a {type(value)}.')
            return self._process_dataclass(cls, value, fieldpath)

        if issubclass(origin, Enum):
            if not isinstance(value, origin):
                raise TypeError(f'Expected a {origin} for {fieldpath};'
                                f' found a {type(value)}.')
            # At prep-time we verified that these enums had valid value
            # types, so we can blindly return it here.
            return value.value if self._create else None

        raise TypeError(
            f"Field '{fieldpath}' of type '{anntype}' is unsupported here.")

    def _process_dict(self, cls: Type, fieldpath: str, anntype: Any,
                      value: dict) -> Any:
        # pylint: disable=too-many-branches
        if not isinstance(value, dict):
            raise TypeError(f'Expected a dict for {fieldpath};'
                            f' found a {type(value)}.')
        childtypes = typing.get_args(anntype)
        assert len(childtypes) in (0, 2)

        # We treat 'Any' dicts simply as json; we don't do any translating.
        if not childtypes or childtypes[0] is typing.Any:
            if not isinstance(value, dict) or not _is_valid_json(value):
                raise TypeError(
                    f'Invalid value for Dict[Any, Any]'
                    f' at \'{fieldpath}\' on {cls}; all keys and values'
                    f' must be json-compatible when dict type is Any.')
            return value if self._create else None

        # Ok; we've got a definite key type (which we verified as valid
        # during prep). Make sure all keys match it.
        out: Optional[Dict] = {} if self._create else None
        keyanntype, valanntype = childtypes

        # str keys we just export directly since that's supported by json.
        if keyanntype is str:
            for key, val in value.items():
                if not isinstance(key, str):
                    raise TypeError(f'Got invalid key type {type(key)} for'
                                    f' dict key at \'{fieldpath}\' on {cls};'
                                    f' expected {keyanntype}.')
                outval = self._process_value(cls, fieldpath, valanntype, val)
                if self._create:
                    assert out is not None
                    out[key] = outval

        # int keys are stored in json as str versions of themselves.
        elif keyanntype is int:
            for key, val in value.items():
                if not isinstance(key, int):
                    raise TypeError(f'Got invalid key type {type(key)} for'
                                    f' dict key at \'{fieldpath}\' on {cls};'
                                    f' expected an int.')
                outval = self._process_value(cls, fieldpath, valanntype, val)
                if self._create:
                    assert out is not None
                    out[str(key)] = outval

        elif issubclass(keyanntype, Enum):
            for key, val in value.items():
                if not isinstance(key, keyanntype):
                    raise TypeError(f'Got invalid key type {type(key)} for'
                                    f' dict key at \'{fieldpath}\' on {cls};'
                                    f' expected a {keyanntype}.')
                outval = self._process_value(cls, fieldpath, valanntype, val)
                if self._create:
                    assert out is not None
                    out[str(key.value)] = outval
        else:
            raise RuntimeError(f'Unhandled dict out-key-type {keyanntype}')

        return out


class _Inputter(Generic[T]):

    def __init__(self,
                 cls: Type[T],
                 coerce_to_float: bool,
                 allow_unknown_attrs: bool = True,
                 discard_unknown_attrs: bool = False):
        self._cls = cls
        self._coerce_to_float = coerce_to_float
        self._allow_unknown_attrs = allow_unknown_attrs
        self._discard_unknown_attrs = discard_unknown_attrs

        if not allow_unknown_attrs and discard_unknown_attrs:
            raise ValueError('discard_unknown_attrs cannot be True'
                             ' when allow_unknown_attrs is False.')

    def run(self, values: dict) -> T:
        """Do the thing."""
        out = self._dataclass_from_input(self._cls, '', values)
        assert isinstance(out, self._cls)
        return out

    def _value_from_input(self, cls: Type, fieldpath: str, anntype: Any,
                          value: Any) -> Any:
        """Convert an assigned value to what a dataclass field expects."""
        # pylint: disable=too-many-return-statements

        origin = _get_origin(anntype)

        if origin is typing.Any:
            if not _is_valid_json(value):
                raise TypeError(f'Invalid value type for \'{fieldpath}\';'
                                f' \'Any\' typed values must be types directly'
                                f' supported by json; got'
                                f' \'{type(value).__name__}\'.')
            return value

        if origin is typing.Union:
            # Currently the only unions we support are None/Value
            # (translated from Optional), which we verified on prep.
            # So let's treat this as a simple optional case.
            if value is None:
                return None
            childanntypes_l = [
                c for c in typing.get_args(anntype) if c is not type(None)
            ]
            assert len(childanntypes_l) == 1
            return self._value_from_input(cls, fieldpath, childanntypes_l[0],
                                          value)

        # Everything below this point assumes the annotation type resolves
        # to a concrete type. (This should have been verified at prep time).
        assert isinstance(origin, type)

        if origin in SIMPLE_TYPES:
            if type(value) is not origin:
                # Special case: if they want to coerce ints to floats, do so.
                if (self._coerce_to_float and origin is float
                        and type(value) is int):
                    return float(value)
                _raise_type_error(fieldpath, type(value), (origin, ))
            return value

        if origin in {list, set}:
            return self._sequence_from_input(cls, fieldpath, anntype, value,
                                             origin)

        if origin is dict:
            return self._dict_from_input(cls, fieldpath, anntype, value)

        if dataclasses.is_dataclass(origin):
            return self._dataclass_from_input(origin, fieldpath, value)

        if issubclass(origin, Enum):
            return enum_by_value(origin, value)

        raise TypeError(
            f"Field '{fieldpath}' of type '{anntype}' is unsupported here.")

    def _dataclass_from_input(self, cls: Type, fieldpath: str,
                              values: dict) -> Any:
        """Given a dict, instantiates a dataclass of the given type.

        The dict must be in the json-friendly format as emitted from
        dataclass_to_dict. This means that sequence values such as tuples or
        sets should be passed as lists, enums should be passed as their
        associated values, and nested dataclasses should be passed as dicts.
        """
        # pylint: disable=too-many-locals
        if not isinstance(values, dict):
            raise TypeError("Expected a dict for 'values' arg.")

        prep = PrepSession(explicit=False,
                           extra_types=None).prep_dataclass(cls,
                                                            recursion_level=0)

        extra_attrs = {}

        # noinspection PyDataclass
        fields = dataclasses.fields(cls)
        fields_by_name = {f.name: f for f in fields}
        args: Dict[str, Any] = {}
        for key, value in values.items():
            field = fields_by_name.get(key)
            if field is None:
                if self._allow_unknown_attrs:
                    if self._discard_unknown_attrs:
                        continue

                    # Treat this like 'Any' data; ensure that it is valid
                    # raw json.
                    if not _is_valid_json(value):
                        raise TypeError(
                            f'Unknown attr {key}'
                            f' on {fieldpath} contains data type(s)'
                            f' not supported by json.')
                    extra_attrs[key] = value
                else:
                    raise AttributeError(
                        f"'{cls.__name__}' has no '{key}' field.")
            else:
                fieldname = field.name
                fieldtype = prep.annotations[fieldname]
                subfieldpath = (f'{fieldpath}.{fieldname}'
                                if fieldpath else fieldname)
                args[key] = self._value_from_input(cls, subfieldpath,
                                                   fieldtype, value)
        out = cls(**args)
        if extra_attrs:
            setattr(out, EXTRA_ATTRS_ATTR, extra_attrs)
        return out

    def _dict_from_input(self, cls: Type, fieldpath: str, anntype: Any,
                         value: Any) -> Any:
        # pylint: disable=too-many-branches

        if not isinstance(value, dict):
            raise TypeError(f'Expected a dict for \'{fieldpath}\' on {cls};'
                            f' got a {type(value)}.')

        childtypes = typing.get_args(anntype)
        assert len(childtypes) in (0, 2)

        out: Dict

        # We treat 'Any' dicts simply as json; we don't do any translating.
        if not childtypes or childtypes[0] is typing.Any:
            if not isinstance(value, dict) or not _is_valid_json(value):
                raise TypeError(f'Got invalid value for Dict[Any, Any]'
                                f' at \'{fieldpath}\' on {cls};'
                                f' all keys and values must be'
                                f' json-compatible.')
            out = value
        else:
            out = {}
            keyanntype, valanntype = childtypes

            # Ok; we've got definite key/value types (which we verified as
            # valid during prep). Run all keys/values through it.

            # str keys we just take directly since that's supported by json.
            if keyanntype is str:
                for key, val in value.items():
                    if not isinstance(key, str):
                        raise TypeError(
                            f'Got invalid key type {type(key)} for'
                            f' dict key at \'{fieldpath}\' on {cls};'
                            f' expected a str.')
                    out[key] = self._value_from_input(cls, fieldpath,
                                                      valanntype, val)

            # int keys are stored in json as str versions of themselves.
            elif keyanntype is int:
                for key, val in value.items():
                    if not isinstance(key, str):
                        raise TypeError(
                            f'Got invalid key type {type(key)} for'
                            f' dict key at \'{fieldpath}\' on {cls};'
                            f' expected a str.')
                    try:
                        keyint = int(key)
                    except ValueError as exc:
                        raise TypeError(
                            f'Got invalid key value {key} for'
                            f' dict key at \'{fieldpath}\' on {cls};'
                            f' expected an int in string form.') from exc
                    out[keyint] = self._value_from_input(
                        cls, fieldpath, valanntype, val)

            elif issubclass(keyanntype, Enum):
                # In prep we verified that all these enums' values have
                # the same type, so we can just look at the first to see if
                # this is a string enum or an int enum.
                enumvaltype = type(next(iter(keyanntype)).value)
                assert enumvaltype in (int, str)
                if enumvaltype is str:
                    for key, val in value.items():
                        try:
                            enumval = enum_by_value(keyanntype, key)
                        except ValueError as exc:
                            raise ValueError(
                                f'Got invalid key value {key} for'
                                f' dict key at \'{fieldpath}\' on {cls};'
                                f' expected a value corresponding to'
                                f' a {keyanntype}.') from exc
                        out[enumval] = self._value_from_input(
                            cls, fieldpath, valanntype, val)
                else:
                    for key, val in value.items():
                        try:
                            enumval = enum_by_value(keyanntype, int(key))
                        except (ValueError, TypeError) as exc:
                            raise ValueError(
                                f'Got invalid key value {key} for'
                                f' dict key at \'{fieldpath}\' on {cls};'
                                f' expected {keyanntype} value (though'
                                f' in string form).') from exc
                        out[enumval] = self._value_from_input(
                            cls, fieldpath, valanntype, val)

            else:
                raise RuntimeError(f'Unhandled dict in-key-type {keyanntype}')

        return out

    def _sequence_from_input(self, cls: Type, fieldpath: str, anntype: Any,
                             value: Any, seqtype: Type) -> Any:

        # Because we are json-centric, we expect a list for all sequences.
        if type(value) is not list:
            raise TypeError(f'Invalid input value for "{fieldpath}";'
                            f' expected a list, got a {type(value).__name__}')

        childanntypes = typing.get_args(anntype)

        # 'Any' type children; make sure they are valid json values
        # and then just grab them.
        if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
            for i, child in enumerate(value):
                if not _is_valid_json(child):
                    raise TypeError(f'Item {i} of {fieldpath} contains'
                                    f' data type(s) not supported by json.')
            return value if type(value) is seqtype else seqtype(value)

        # We contain elements of some specified type.
        assert len(childanntypes) == 1
        childanntype = childanntypes[0]
        return seqtype(
            self._value_from_input(cls, fieldpath, childanntype, i)
            for i in value)
