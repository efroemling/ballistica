# Released under the MIT License. See LICENSE for details.
#
"""Functionality for dataclassio related to pulling data into dataclasses."""

# Note: We do lots of comparing of exact types here which is normally
# frowned upon (stuff like isinstance() is usually encouraged).
# pylint: disable=unidiomatic-typecheck

from __future__ import annotations

from enum import Enum
import dataclasses
import typing
import types
import datetime
from typing import TYPE_CHECKING, Generic, TypeVar

from efro.util import enum_by_value, check_utc
from efro.dataclassio._base import (
    Codec,
    _parse_annotated,
    EXTRA_ATTRS_ATTR,
    _is_valid_for_codec,
    _get_origin,
    SIMPLE_TYPES,
    _raise_type_error,
    IOExtendedData,
)
from efro.dataclassio._prep import PrepSession

if TYPE_CHECKING:
    from typing import Any

    from efro.dataclassio._base import IOAttrs
    from efro.dataclassio._outputter import _Outputter

T = TypeVar('T')


class _Inputter(Generic[T]):
    def __init__(
        self,
        cls: type[T],
        codec: Codec,
        coerce_to_float: bool,
        allow_unknown_attrs: bool = True,
        discard_unknown_attrs: bool = False,
    ):
        self._cls = cls
        self._codec = codec
        self._coerce_to_float = coerce_to_float
        self._allow_unknown_attrs = allow_unknown_attrs
        self._discard_unknown_attrs = discard_unknown_attrs
        self._soft_default_validator: _Outputter | None = None

        if not allow_unknown_attrs and discard_unknown_attrs:
            raise ValueError(
                'discard_unknown_attrs cannot be True'
                ' when allow_unknown_attrs is False.'
            )

    def run(self, values: dict) -> T:
        """Do the thing."""

        # For special extended data types, call their 'will_output' callback.
        tcls = self._cls
        if issubclass(tcls, IOExtendedData):
            tcls.will_input(values)

        out = self._dataclass_from_input(self._cls, '', values)
        assert isinstance(out, self._cls)
        return out

    def _value_from_input(
        self,
        cls: type,
        fieldpath: str,
        anntype: Any,
        value: Any,
        ioattrs: IOAttrs | None,
    ) -> Any:
        """Convert an assigned value to what a dataclass field expects."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        origin = _get_origin(anntype)

        if origin is typing.Any:
            if not _is_valid_for_codec(value, self._codec):
                raise TypeError(
                    f'Invalid value type for \'{fieldpath}\';'
                    f' \'Any\' typed values must contain only'
                    f' types directly supported by the specified'
                    f' codec ({self._codec.name}); found'
                    f' \'{type(value).__name__}\' which is not.'
                )
            return value

        if origin is typing.Union or origin is types.UnionType:
            # Currently, the only unions we support are None/Value
            # (translated from Optional), which we verified on prep.
            # So let's treat this as a simple optional case.
            if value is None:
                return None
            childanntypes_l = [
                c for c in typing.get_args(anntype) if c is not type(None)
            ]  # noqa (pycodestyle complains about *is* with type)
            assert len(childanntypes_l) == 1
            return self._value_from_input(
                cls, fieldpath, childanntypes_l[0], value, ioattrs
            )

        # Everything below this point assumes the annotation type resolves
        # to a concrete type. (This should have been verified at prep time).
        assert isinstance(origin, type)

        if origin in SIMPLE_TYPES:
            if type(value) is not origin:
                # Special case: if they want to coerce ints to floats, do so.
                if (
                    self._coerce_to_float
                    and origin is float
                    and type(value) is int
                ):
                    return float(value)
                _raise_type_error(fieldpath, type(value), (origin,))
            return value

        if origin in {list, set}:
            return self._sequence_from_input(
                cls, fieldpath, anntype, value, origin, ioattrs
            )

        if origin is tuple:
            return self._tuple_from_input(
                cls, fieldpath, anntype, value, ioattrs
            )

        if origin is dict:
            return self._dict_from_input(
                cls, fieldpath, anntype, value, ioattrs
            )

        if dataclasses.is_dataclass(origin):
            return self._dataclass_from_input(origin, fieldpath, value)

        if issubclass(origin, Enum):
            return enum_by_value(origin, value)

        if issubclass(origin, datetime.datetime):
            return self._datetime_from_input(cls, fieldpath, value, ioattrs)

        if origin is bytes:
            return self._bytes_from_input(origin, fieldpath, value)

        raise TypeError(
            f"Field '{fieldpath}' of type '{anntype}' is unsupported here."
        )

    def _bytes_from_input(self, cls: type, fieldpath: str, value: Any) -> bytes:
        """Given input data, returns bytes."""
        import base64

        # For firestore, bytes are passed as-is. Otherwise, they're encoded
        # as base64.
        if self._codec is Codec.FIRESTORE:
            if not isinstance(value, bytes):
                raise TypeError(
                    f'Expected a bytes object for {fieldpath}'
                    f' on {cls.__name__}; got a {type(value)}.'
                )

            return value

        assert self._codec is Codec.JSON
        if not isinstance(value, str):
            raise TypeError(
                f'Expected a string object for {fieldpath}'
                f' on {cls.__name__}; got a {type(value)}.'
            )
        return base64.b64decode(value)

    def _dataclass_from_input(
        self, cls: type, fieldpath: str, values: dict
    ) -> Any:
        """Given a dict, instantiates a dataclass of the given type.

        The dict must be in the json-friendly format as emitted from
        dataclass_to_dict. This means that sequence values such as tuples or
        sets should be passed as lists, enums should be passed as their
        associated values, and nested dataclasses should be passed as dicts.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        if not isinstance(values, dict):
            raise TypeError(
                f'Expected a dict for {fieldpath} on {cls.__name__};'
                f' got a {type(values)}.'
            )

        prep = PrepSession(explicit=False).prep_dataclass(
            cls, recursion_level=0
        )
        assert prep is not None

        extra_attrs = {}

        # noinspection PyDataclass
        fields = dataclasses.fields(cls)
        fields_by_name = {f.name: f for f in fields}

        # Preprocess all fields to convert Annotated[] to contained types
        # and IOAttrs.
        parsed_field_annotations = {
            f.name: _parse_annotated(prep.annotations[f.name]) for f in fields
        }

        # Go through all data in the input, converting it to either dataclass
        # args or extra data.
        args: dict[str, Any] = {}
        for rawkey, value in values.items():
            key = prep.storage_names_to_attr_names.get(rawkey, rawkey)
            field = fields_by_name.get(key)

            # Store unknown attrs off to the side (or error if desired).
            if field is None:
                if self._allow_unknown_attrs:
                    if self._discard_unknown_attrs:
                        continue

                    # Treat this like 'Any' data; ensure that it is valid
                    # raw json.
                    if not _is_valid_for_codec(value, self._codec):
                        raise TypeError(
                            f'Unknown attr \'{key}\''
                            f' on {fieldpath} contains data type(s)'
                            f' not supported by the specified codec'
                            f' ({self._codec.name}).'
                        )
                    extra_attrs[key] = value
                else:
                    raise AttributeError(
                        f"'{cls.__name__}' has no '{key}' field."
                    )
            else:
                fieldname = field.name
                anntype, ioattrs = parsed_field_annotations[fieldname]
                subfieldpath = (
                    f'{fieldpath}.{fieldname}' if fieldpath else fieldname
                )
                args[key] = self._value_from_input(
                    cls, subfieldpath, anntype, value, ioattrs
                )

        # Go through all fields looking for any not yet present in our data.
        # If we find any such fields with a soft-default value or factory
        # defined, inject that soft value into our args.
        for key, aparsed in parsed_field_annotations.items():
            if key in args:
                continue
            ioattrs = aparsed[1]
            if ioattrs is not None and (
                ioattrs.soft_default is not ioattrs.MISSING
                or ioattrs.soft_default_factory is not ioattrs.MISSING
            ):
                if ioattrs.soft_default is not ioattrs.MISSING:
                    soft_default = ioattrs.soft_default
                else:
                    assert callable(ioattrs.soft_default_factory)
                    soft_default = ioattrs.soft_default_factory()
                args[key] = soft_default

                # Make sure these values are valid since we didn't run
                # them through our normal input type checking.

                self._type_check_soft_default(
                    value=soft_default,
                    anntype=aparsed[0],
                    fieldpath=(f'{fieldpath}.{key}' if fieldpath else key),
                )

        try:
            out = cls(**args)
        except Exception as exc:
            raise ValueError(
                f'Error instantiating class {cls.__name__}'
                f' at {fieldpath}: {exc}'
            ) from exc
        if extra_attrs:
            setattr(out, EXTRA_ATTRS_ATTR, extra_attrs)
        return out

    def _type_check_soft_default(
        self, value: Any, anntype: Any, fieldpath: str
    ) -> None:
        from efro.dataclassio._outputter import _Outputter

        # Counter-intuitively, we create an outputter as part of
        # our inputter. Soft-default values are already internal types;
        # we need to make sure they can go out from there.
        if self._soft_default_validator is None:
            self._soft_default_validator = _Outputter(
                obj=None,
                create=False,
                codec=self._codec,
                coerce_to_float=self._coerce_to_float,
            )
        self._soft_default_validator.soft_default_check(
            value=value, anntype=anntype, fieldpath=fieldpath
        )

    def _dict_from_input(
        self,
        cls: type,
        fieldpath: str,
        anntype: Any,
        value: Any,
        ioattrs: IOAttrs | None,
    ) -> Any:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals

        if not isinstance(value, dict):
            raise TypeError(
                f'Expected a dict for \'{fieldpath}\' on {cls.__name__};'
                f' got a {type(value)}.'
            )

        childtypes = typing.get_args(anntype)
        assert len(childtypes) in (0, 2)

        out: dict

        # We treat 'Any' dicts simply as json; we don't do any translating.
        if not childtypes or childtypes[0] is typing.Any:
            if not isinstance(value, dict) or not _is_valid_for_codec(
                value, self._codec
            ):
                raise TypeError(
                    f'Got invalid value for Dict[Any, Any]'
                    f' at \'{fieldpath}\' on {cls.__name__};'
                    f' all keys and values must be'
                    f' compatible with the specified codec'
                    f' ({self._codec.name}).'
                )
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
                            f' dict key at \'{fieldpath}\' on {cls.__name__};'
                            f' expected a str.'
                        )
                    out[key] = self._value_from_input(
                        cls, fieldpath, valanntype, val, ioattrs
                    )

            # int keys are stored in json as str versions of themselves.
            elif keyanntype is int:
                for key, val in value.items():
                    if not isinstance(key, str):
                        raise TypeError(
                            f'Got invalid key type {type(key)} for'
                            f' dict key at \'{fieldpath}\' on {cls.__name__};'
                            f' expected a str.'
                        )
                    try:
                        keyint = int(key)
                    except ValueError as exc:
                        raise TypeError(
                            f'Got invalid key value {key} for'
                            f' dict key at \'{fieldpath}\' on {cls.__name__};'
                            f' expected an int in string form.'
                        ) from exc
                    out[keyint] = self._value_from_input(
                        cls, fieldpath, valanntype, val, ioattrs
                    )

            elif issubclass(keyanntype, Enum):
                # In prep, we verified that all these enums' values have
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
                                f' dict key at \'{fieldpath}\''
                                f' on {cls.__name__};'
                                f' expected a value corresponding to'
                                f' a {keyanntype}.'
                            ) from exc
                        out[enumval] = self._value_from_input(
                            cls, fieldpath, valanntype, val, ioattrs
                        )
                else:
                    for key, val in value.items():
                        try:
                            enumval = enum_by_value(keyanntype, int(key))
                        except (ValueError, TypeError) as exc:
                            raise ValueError(
                                f'Got invalid key value {key} for'
                                f' dict key at \'{fieldpath}\''
                                f' on {cls.__name__};'
                                f' expected {keyanntype} value (though'
                                f' in string form).'
                            ) from exc
                        out[enumval] = self._value_from_input(
                            cls, fieldpath, valanntype, val, ioattrs
                        )

            else:
                raise RuntimeError(f'Unhandled dict in-key-type {keyanntype}')

        return out

    def _sequence_from_input(
        self,
        cls: type,
        fieldpath: str,
        anntype: Any,
        value: Any,
        seqtype: type,
        ioattrs: IOAttrs | None,
    ) -> Any:

        # Because we are json-centric, we expect a list for all sequences.
        if type(value) is not list:
            raise TypeError(
                f'Invalid input value for "{fieldpath}";'
                f' expected a list, got a {type(value).__name__}'
            )

        childanntypes = typing.get_args(anntype)

        # 'Any' type children; make sure they are valid json values
        # and then just grab them.
        if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
            for i, child in enumerate(value):
                if not _is_valid_for_codec(child, self._codec):
                    raise TypeError(
                        f'Item {i} of {fieldpath} contains'
                        f' data type(s) not supported by json.'
                    )
            return value if type(value) is seqtype else seqtype(value)

        # We contain elements of some specified type.
        assert len(childanntypes) == 1
        childanntype = childanntypes[0]
        return seqtype(
            self._value_from_input(cls, fieldpath, childanntype, i, ioattrs)
            for i in value
        )

    def _datetime_from_input(
        self, cls: type, fieldpath: str, value: Any, ioattrs: IOAttrs | None
    ) -> Any:

        # For firestore we expect a datetime object.
        if self._codec is Codec.FIRESTORE:
            # Don't compare exact type here, as firestore can give us
            # a subclass with extended precision.
            if not isinstance(value, datetime.datetime):
                raise TypeError(
                    f'Invalid input value for "{fieldpath}" on'
                    f' "{cls.__name__}";'
                    f' expected a datetime, got a {type(value).__name__}'
                )
            check_utc(value)
            return value

        assert self._codec is Codec.JSON

        # We expect a list of 7 ints.
        if type(value) is not list:
            raise TypeError(
                f'Invalid input value for "{fieldpath}" on "{cls.__name__}";'
                f' expected a list, got a {type(value).__name__}'
            )
        if len(value) != 7 or not all(isinstance(x, int) for x in value):
            raise ValueError(
                f'Invalid input value for "{fieldpath}" on "{cls.__name__}";'
                f' expected a list of 7 ints, got {[type(v) for v in value]}.'
            )
        out = datetime.datetime(  # type: ignore
            *value, tzinfo=datetime.timezone.utc
        )
        if ioattrs is not None:
            ioattrs.validate_datetime(out, fieldpath)
        return out

    def _tuple_from_input(
        self,
        cls: type,
        fieldpath: str,
        anntype: Any,
        value: Any,
        ioattrs: IOAttrs | None,
    ) -> Any:

        out: list = []

        # Because we are json-centric, we expect a list for all sequences.
        if type(value) is not list:
            raise TypeError(
                f'Invalid input value for "{fieldpath}";'
                f' expected a list, got a {type(value).__name__}'
            )

        childanntypes = typing.get_args(anntype)

        # We should have verified this to be non-zero at prep-time.
        assert childanntypes

        if len(value) != len(childanntypes):
            raise ValueError(
                f'Invalid tuple input for "{fieldpath}";'
                f' expected {len(childanntypes)} values,'
                f' found {len(value)}.'
            )

        for i, childanntype in enumerate(childanntypes):
            childval = value[i]

            # 'Any' type children; make sure they are valid json values
            # and then just grab them.
            if childanntype is typing.Any:
                if not _is_valid_for_codec(childval, self._codec):
                    raise TypeError(
                        f'Item {i} of {fieldpath} contains'
                        f' data type(s) not supported by json.'
                    )
                out.append(childval)
            else:
                out.append(
                    self._value_from_input(
                        cls, fieldpath, childanntype, childval, ioattrs
                    )
                )

        assert len(out) == len(childanntypes)
        return tuple(out)
