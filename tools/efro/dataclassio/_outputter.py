# Released under the MIT License. See LICENSE for details.
#
"""Functionality for dataclassio related to exporting data from dataclasses."""

# Note: We do lots of comparing of exact types here which is normally
# frowned upon (stuff like isinstance() is usually encouraged).
# pylint: disable=unidiomatic-typecheck

from __future__ import annotations

from enum import Enum
import dataclasses
import typing
import types
import datetime
from typing import TYPE_CHECKING, cast, Any

from efro.util import check_utc
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
    from efro.dataclassio._base import IOAttrs


class _Outputter:
    """Validates or exports data contained in a dataclass instance."""

    def __init__(
        self, obj: Any, create: bool, codec: Codec, coerce_to_float: bool
    ) -> None:
        self._obj = obj
        self._create = create
        self._codec = codec
        self._coerce_to_float = coerce_to_float

    def run(self) -> Any:
        """Do the thing."""

        assert dataclasses.is_dataclass(self._obj)

        # For special extended data types, call their 'will_output' callback.
        if isinstance(self._obj, IOExtendedData):
            self._obj.will_output()

        return self._process_dataclass(type(self._obj), self._obj, '')

    def soft_default_check(
        self, value: Any, anntype: Any, fieldpath: str
    ) -> None:
        """(internal)"""
        self._process_value(
            type(value),
            fieldpath=fieldpath,
            anntype=anntype,
            value=value,
            ioattrs=None,
        )

    def _process_dataclass(self, cls: type, obj: Any, fieldpath: str) -> Any:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        prep = PrepSession(explicit=False).prep_dataclass(
            type(obj), recursion_level=0
        )
        assert prep is not None
        fields = dataclasses.fields(obj)
        out: dict[str, Any] | None = {} if self._create else None
        for field in fields:
            fieldname = field.name
            if fieldpath:
                subfieldpath = f'{fieldpath}.{fieldname}'
            else:
                subfieldpath = fieldname
            anntype = prep.annotations[fieldname]
            value = getattr(obj, fieldname)

            anntype, ioattrs = _parse_annotated(anntype)

            # If we're not storing default values for this fella,
            # we can skip all output processing if we've got a default value.
            if ioattrs is not None and not ioattrs.store_default:
                # If both soft_defaults and regular field defaults
                # are present we want to go with soft_defaults since
                # those same values would be re-injected when reading
                # the same data back in if we've omitted the field.
                default_factory: Any = field.default_factory
                if ioattrs.soft_default is not ioattrs.MISSING:
                    if ioattrs.soft_default == value:
                        continue
                elif ioattrs.soft_default_factory is not ioattrs.MISSING:
                    assert callable(ioattrs.soft_default_factory)
                    if ioattrs.soft_default_factory() == value:
                        continue
                elif field.default is not dataclasses.MISSING:
                    if field.default == value:
                        continue
                elif default_factory is not dataclasses.MISSING:
                    if default_factory() == value:
                        continue
                else:
                    raise RuntimeError(
                        f'Field {fieldname} of {cls.__name__} has'
                        f' no source of default values; store_default=False'
                        f' cannot be set for it. (AND THIS SHOULD HAVE BEEN'
                        f' CAUGHT IN PREP!)'
                    )

            outvalue = self._process_value(
                cls, subfieldpath, anntype, value, ioattrs
            )
            if self._create:
                assert out is not None
                storagename = (
                    fieldname
                    if (ioattrs is None or ioattrs.storagename is None)
                    else ioattrs.storagename
                )
                out[storagename] = outvalue

        # If there's extra-attrs stored on us, check/include them.
        extra_attrs = getattr(obj, EXTRA_ATTRS_ATTR, None)
        if isinstance(extra_attrs, dict):
            if not _is_valid_for_codec(extra_attrs, self._codec):
                raise TypeError(
                    f'Extra attrs on \'{fieldpath}\' contains data type(s)'
                    f' not supported by \'{self._codec.value}\' codec:'
                    f' {extra_attrs}.'
                )
            if self._create:
                assert out is not None
                out.update(extra_attrs)
        return out

    def _process_value(
        self,
        cls: type,
        fieldpath: str,
        anntype: Any,
        value: Any,
        ioattrs: IOAttrs | None,
    ) -> Any:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        origin = _get_origin(anntype)

        if origin is typing.Any:
            if not _is_valid_for_codec(value, self._codec):
                raise TypeError(
                    f'Invalid value type for \'{fieldpath}\';'
                    f" 'Any' typed values must contain types directly"
                    f' supported by the specified codec ({self._codec.name});'
                    f' found \'{type(value).__name__}\' which is not.'
                )
            return value if self._create else None

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
            return self._process_value(
                cls, fieldpath, childanntypes_l[0], value, ioattrs
            )

        # Everything below this point assumes the annotation type resolves
        # to a concrete type. (This should have been verified at prep time).
        assert isinstance(origin, type)

        # For simple flat types, look for exact matches:
        if origin in SIMPLE_TYPES:
            if type(value) is not origin:
                # Special case: if they want to coerce ints to floats, do so.
                if (
                    self._coerce_to_float
                    and origin is float
                    and type(value) is int
                ):
                    return float(value) if self._create else None
                _raise_type_error(fieldpath, type(value), (origin,))
            return value if self._create else None

        if origin is tuple:
            if not isinstance(value, tuple):
                raise TypeError(
                    f'Expected a tuple for {fieldpath};'
                    f' found a {type(value)}'
                )
            childanntypes = typing.get_args(anntype)

            # We should have verified this was non-zero at prep-time
            assert childanntypes
            if len(value) != len(childanntypes):
                raise TypeError(
                    f'Tuple at {fieldpath} contains'
                    f' {len(value)} values; type specifies'
                    f' {len(childanntypes)}.'
                )
            if self._create:
                return [
                    self._process_value(
                        cls, fieldpath, childanntypes[i], x, ioattrs
                    )
                    for i, x in enumerate(value)
                ]
            for i, x in enumerate(value):
                self._process_value(
                    cls, fieldpath, childanntypes[i], x, ioattrs
                )
            return None

        if origin is list:
            if not isinstance(value, list):
                raise TypeError(
                    f'Expected a list for {fieldpath};'
                    f' found a {type(value)}'
                )
            childanntypes = typing.get_args(anntype)

            # 'Any' type children; make sure they are valid values for
            # the specified codec.
            if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
                for i, child in enumerate(value):
                    if not _is_valid_for_codec(child, self._codec):
                        raise TypeError(
                            f'Item {i} of {fieldpath} contains'
                            f' data type(s) not supported by the specified'
                            f' codec ({self._codec.name}).'
                        )
                # Hmm; should we do a copy here?
                return value if self._create else None

            # We contain elements of some specified type.
            assert len(childanntypes) == 1
            if self._create:
                return [
                    self._process_value(
                        cls, fieldpath, childanntypes[0], x, ioattrs
                    )
                    for x in value
                ]
            for x in value:
                self._process_value(
                    cls, fieldpath, childanntypes[0], x, ioattrs
                )
            return None

        if origin is set:
            if not isinstance(value, set):
                raise TypeError(
                    f'Expected a set for {fieldpath};' f' found a {type(value)}'
                )
            childanntypes = typing.get_args(anntype)

            # 'Any' type children; make sure they are valid Any values.
            if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
                for child in value:
                    if not _is_valid_for_codec(child, self._codec):
                        raise TypeError(
                            f'Set at {fieldpath} contains'
                            f' data type(s) not supported by the'
                            f' specified codec ({self._codec.name}).'
                        )
                return list(value) if self._create else None

            # We contain elements of some specified type.
            assert len(childanntypes) == 1
            if self._create:
                # Note: we output json-friendly values so this becomes
                # a list.
                return [
                    self._process_value(
                        cls, fieldpath, childanntypes[0], x, ioattrs
                    )
                    for x in value
                ]
            for x in value:
                self._process_value(
                    cls, fieldpath, childanntypes[0], x, ioattrs
                )
            return None

        if origin is dict:
            return self._process_dict(cls, fieldpath, anntype, value, ioattrs)

        if dataclasses.is_dataclass(origin):
            if not isinstance(value, cast(Any, origin)):
                raise TypeError(
                    f'Expected a {origin} for {fieldpath};'
                    f' found a {type(value)}.'
                )
            return self._process_dataclass(cls, value, fieldpath)

        if issubclass(origin, Enum):
            if not isinstance(value, origin):
                raise TypeError(
                    f'Expected a {origin} for {fieldpath};'
                    f' found a {type(value)}.'
                )
            # At prep-time we verified that these enums had valid value
            # types, so we can blindly return it here.
            return value.value if self._create else None

        if issubclass(origin, datetime.datetime):
            if not isinstance(value, origin):
                raise TypeError(
                    f'Expected a {origin} for {fieldpath};'
                    f' found a {type(value)}.'
                )
            check_utc(value)
            if ioattrs is not None:
                ioattrs.validate_datetime(value, fieldpath)
            if self._codec is Codec.FIRESTORE:
                return value
            assert self._codec is Codec.JSON
            return (
                [
                    value.year,
                    value.month,
                    value.day,
                    value.hour,
                    value.minute,
                    value.second,
                    value.microsecond,
                ]
                if self._create
                else None
            )

        if origin is bytes:
            return self._process_bytes(cls, fieldpath, value)

        raise TypeError(
            f"Field '{fieldpath}' of type '{anntype}' is unsupported here."
        )

    def _process_bytes(self, cls: type, fieldpath: str, value: bytes) -> Any:
        import base64

        if not isinstance(value, bytes):
            raise TypeError(
                f'Expected bytes for {fieldpath} on {cls.__name__};'
                f' found a {type(value)}.'
            )

        if not self._create:
            return None

        # In JSON we convert to base64, but firestore directly supports bytes.
        if self._codec is Codec.JSON:
            return base64.b64encode(value).decode()

        assert self._codec is Codec.FIRESTORE
        return value

    def _process_dict(
        self,
        cls: type,
        fieldpath: str,
        anntype: Any,
        value: dict,
        ioattrs: IOAttrs | None,
    ) -> Any:
        # pylint: disable=too-many-branches
        if not isinstance(value, dict):
            raise TypeError(
                f'Expected a dict for {fieldpath};' f' found a {type(value)}.'
            )
        childtypes = typing.get_args(anntype)
        assert len(childtypes) in (0, 2)

        # We treat 'Any' dicts simply as json; we don't do any translating.
        value_any: Any = value
        if not childtypes or childtypes[0] is typing.Any:
            if not isinstance(value_any, dict) or not _is_valid_for_codec(
                value, self._codec
            ):
                raise TypeError(
                    f'Invalid value for Dict[Any, Any]'
                    f' at \'{fieldpath}\' on {cls.__name__};'
                    f' all keys and values must be directly compatible'
                    f' with the specified codec ({self._codec.name})'
                    f' when dict type is Any.'
                )
            return value if self._create else None

        # Ok; we've got a definite key type (which we verified as valid
        # during prep). Make sure all keys match it.
        out: dict | None = {} if self._create else None
        keyanntype, valanntype = childtypes

        # str keys we just export directly since that's supported by json.
        if keyanntype is str:
            for key, val in value.items():
                if not isinstance(key, str):
                    raise TypeError(
                        f'Got invalid key type {type(key)} for'
                        f' dict key at \'{fieldpath}\' on {cls.__name__};'
                        f' expected {keyanntype}.'
                    )
                outval = self._process_value(
                    cls, fieldpath, valanntype, val, ioattrs
                )
                if self._create:
                    assert out is not None
                    out[key] = outval

        # int keys are stored as str versions of themselves.
        elif keyanntype is int:
            for key, val in value.items():
                if not isinstance(key, int):
                    raise TypeError(
                        f'Got invalid key type {type(key)} for'
                        f' dict key at \'{fieldpath}\' on {cls.__name__};'
                        f' expected an int.'
                    )
                outval = self._process_value(
                    cls, fieldpath, valanntype, val, ioattrs
                )
                if self._create:
                    assert out is not None
                    out[str(key)] = outval

        elif issubclass(keyanntype, Enum):
            for key, val in value.items():
                if not isinstance(key, keyanntype):
                    raise TypeError(
                        f'Got invalid key type {type(key)} for'
                        f' dict key at \'{fieldpath}\' on {cls.__name__};'
                        f' expected a {keyanntype}.'
                    )
                outval = self._process_value(
                    cls, fieldpath, valanntype, val, ioattrs
                )
                if self._create:
                    assert out is not None
                    out[str(key.value)] = outval
        else:
            raise RuntimeError(f'Unhandled dict out-key-type {keyanntype}')

        return out
