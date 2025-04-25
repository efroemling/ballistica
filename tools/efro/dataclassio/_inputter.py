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
from typing import TYPE_CHECKING

from efro.util import check_utc
from efro.dataclassio._base import (
    Codec,
    _parse_annotated,
    EXTRA_ATTRS_ATTR,
    LOSSY_ATTR,
    _is_valid_for_codec,
    _get_origin,
    SIMPLE_TYPES,
    _raise_type_error,
    IOExtendedData,
    _get_multitype_type,
    IOMultiType,
)
from efro.dataclassio._prep import PrepSession

if TYPE_CHECKING:
    from typing import Any

    from efro.dataclassio._base import IOAttrs
    from efro.dataclassio._outputter import _Outputter


class _Inputter:
    def __init__(
        self,
        cls: type[Any],
        *,
        codec: Codec,
        coerce_to_float: bool,
        allow_unknown_attrs: bool = True,
        discard_unknown_attrs: bool = False,
        lossy: bool = False,
    ):
        self._cls = cls
        self._codec = codec
        self._coerce_to_float = coerce_to_float
        self._allow_unknown_attrs = allow_unknown_attrs
        self._discard_unknown_attrs = discard_unknown_attrs
        self._soft_default_validator: _Outputter | None = None
        self._lossy = lossy

        if not allow_unknown_attrs and discard_unknown_attrs:
            raise ValueError(
                'discard_unknown_attrs cannot be True'
                ' when allow_unknown_attrs is False.'
            )

    def run(self, values: dict) -> Any:
        """Do the thing."""

        outcls: type[Any]

        # If we're dealing with a multi-type subclass which is NOT a
        # dataclass (generally a custom multitype base class), then we
        # must rely on its stored type enum to figure out what type of
        # dataclass we're going to create. If we *are* dealing with a
        # dataclass then we already know what type we're going to so we
        # can survive without this, which is often necessary when
        # reading old data that doesn't have a type id attr yet.
        if issubclass(self._cls, IOMultiType) and not dataclasses.is_dataclass(
            self._cls
        ):
            type_id_val = values.get(self._cls.get_type_id_storage_name())
            if type_id_val is None:
                raise ValueError(
                    f'No type id value present for multi-type object:'
                    f' {values}.'
                )
            type_id_enum = self._cls.get_type_id_type()
            try:
                enum_val = type_id_enum(type_id_val)
            except ValueError as exc:

                # Check the fallback even if not in lossy mode, as we
                # inform the user of its existence in errors in that
                # case.
                fallback = self._cls.get_unknown_type_fallback()

                # Sanity check that fallback is correct type.
                assert isinstance(fallback, self._cls | None)

                # If we're in lossy mode, provide the fallback value.
                if self._lossy:
                    if fallback is not None:
                        # Ok; they provided a fallback. Flag it as lossy
                        # to prevent it from being written back out by
                        # default, and return it.
                        setattr(fallback, LOSSY_ATTR, True)
                        return fallback
                else:
                    # If we're *not* in lossy mode, inform the user if
                    # we *would* have succeeded if we were. This is
                    # useful for debugging these sorts of situations.
                    if fallback is not None:
                        raise ValueError(
                            'Failed loading unrecognized multitype object.'
                            ' Note that the multitype provides a fallback'
                            ' and thus would succeed in lossy mode.'
                        ) from exc

                # Otherwise the error stands as-is.
                raise

            outcls = self._cls.get_type(enum_val)
        else:
            outcls = self._cls

        # FIXME - should probably move this into _dataclass_from_input
        # so it can work on nested values.
        if issubclass(outcls, IOExtendedData):
            is_ext = True
            outcls.will_input(values)
        else:
            is_ext = False

        out = self._dataclass_from_input(outcls, '', values)
        assert isinstance(out, outcls)

        if is_ext:
            out.did_input()

        # If we're running in lossy mode, flag the object as such so we
        # don't allow writing it back out and potentially accidentally
        # losing data.
        #
        # FIXME - We are currently only flagging this at the top level,
        # but this will not prevent sub-objects from being written out.
        # Is that worth worrying about? Though perfect is the enemy of
        # good I suppose.
        if self._lossy:
            setattr(out, LOSSY_ATTR, True)

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
        # pylint: disable=too-many-positional-arguments
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

        # noinspection PyPep8
        if origin is typing.Union or origin is types.UnionType:
            # Currently, the only unions we support are None/Value
            # (translated from Optional), which we verified on prep. So
            # let's treat this as a simple optional case.
            if value is None:
                return None
            childanntypes_l = [
                c for c in typing.get_args(anntype) if c is not type(None)
            ]  # noqa (pycodestyle complains about *is* with type)
            assert len(childanntypes_l) == 1
            return self._value_from_input(
                cls, fieldpath, childanntypes_l[0], value, ioattrs
            )

        # Everything below this point assumes the annotation type
        # resolves to a concrete type. (This should have been verified
        # at prep time).
        assert isinstance(origin, type)

        if origin in SIMPLE_TYPES:
            if type(value) is not origin:
                # Special case: if they want to coerce ints to floats,
                # do so.
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

        # ONLY consider something as a multi-type when it's not a
        # dataclass (all dataclasses inheriting from the multi-type
        # should just be processed as dataclasses).
        if issubclass(origin, IOMultiType):
            return self._multitype_obj(anntype, fieldpath, value)

        if issubclass(origin, Enum):
            try:
                return origin(value)
            except ValueError as exc:
                # If a fallback enum was provided in ioattrs AND we're
                # in lossy mode, return that for unrecognized values. If
                # one was provided but we're *not* in lossy mode, note
                # that we could have loaded it if lossy mode was
                # enabled.
                if ioattrs is not None and ioattrs.enum_fallback is not None:
                    # Sanity check; make sure fallback is valid.
                    assert type(ioattrs.enum_fallback) is origin
                    if self._lossy:
                        return ioattrs.enum_fallback
                    raise ValueError(
                        'Failed to load Enum.  Note that it has a fallback'
                        ' value and thus would succeed in lossy mode.'
                    ) from exc

                # Otherwise the error stands as-is.
                raise

        if issubclass(origin, datetime.datetime):
            return self._datetime_from_input(cls, fieldpath, value, ioattrs)

        if issubclass(origin, datetime.timedelta):
            return self._timedelta_from_input(cls, fieldpath, value, ioattrs)

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
        dataclass_to_dict. This means that sequence values such as
        tuples or sets should be passed as lists, enums should be passed
        as their associated values, and nested dataclasses should be
        passed as dicts.
        """
        try:
            return self._do_dataclass_from_input(cls, fieldpath, values)
        except Exception as exc:
            # Extended data types can choose to substitute default data
            # in case of failures (generally not a good idea but
            # occasionally useful).
            if issubclass(cls, IOExtendedData):
                fallback = cls.handle_input_error(exc)
                if fallback is None:
                    raise
                # Make sure fallback gave us the right type.
                if not isinstance(fallback, cls):
                    raise RuntimeError(
                        f'handle_input_error() was expected to return a {cls}'
                        f' but returned a {type(fallback)}.'
                    ) from exc
                return fallback
            raise

    def _do_dataclass_from_input(
        self, cls: type, fieldpath: str, values: dict
    ) -> Any:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
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

        # Preprocess all fields to convert Annotated[] to contained
        # types and IOAttrs.
        parsed_field_annotations = {
            f.name: _parse_annotated(prep.annotations[f.name]) for f in fields
        }

        # Special case: if this is a multi-type class it probably has a
        # type attr. Ignore that while parsing since we already have a
        # definite type and it will just pollute extra-attrs otherwise.
        if issubclass(cls, IOMultiType):
            type_id_store_name = cls.get_type_id_storage_name()

            # However we do want to make sure the class we're loading
            # doesn't itself use this same name, as this could lead to
            # tricky breakage. We can't verify this for types at prep
            # time because IOMultiTypes are lazy-loaded, so this is the
            # best we can do.
            if type_id_store_name in fields_by_name:
                raise RuntimeError(
                    f"{cls} contains a '{type_id_store_name}' field"
                    ' which clashes with the type-id-storage-name of'
                    ' the IOMultiType it inherits from.'
                )

        else:
            type_id_store_name = None

        # Go through all data in the input, converting it to either
        # dataclass args or extra data.
        args: dict[str, Any] = {}
        for rawkey, value in values.items():

            # Ignore _dciotype or whatnot.
            if type_id_store_name is not None and rawkey == type_id_store_name:
                continue

            key = prep.storage_names_to_attr_names.get(rawkey, rawkey)
            field = fields_by_name.get(key)

            # Store unknown attrs off to the side (or error if desired).
            if field is None:
                if self._allow_unknown_attrs:
                    if self._discard_unknown_attrs:
                        continue

                    # Treat this like 'Any' data; ensure that it is
                    # valid raw json.
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
                discard_extra_attrs=False,
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
        # pylint: disable=too-many-positional-arguments
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
            value_any: Any = value
            if not isinstance(value_any, dict) or not _is_valid_for_codec(
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
                            enumval = keyanntype(key)
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
                            enumval = keyanntype(int(key))
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
        # pylint: disable=too-many-positional-arguments
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

        # If our annotation type inherits from IOMultiType, use type-id
        # values to determine which type to load for each element.
        if issubclass(childanntype, IOMultiType):
            return seqtype(
                self._multitype_obj(childanntype, fieldpath, i) for i in value
            )

        return seqtype(
            self._value_from_input(cls, fieldpath, childanntype, i, ioattrs)
            for i in value
        )

    def _multitype_obj(self, anntype: Any, fieldpath: str, value: Any) -> Any:
        try:
            mttype = _get_multitype_type(anntype, fieldpath, value)
        except ValueError:
            if self._lossy:
                out = anntype.get_unknown_type_fallback()
                if out is not None:
                    # Ok; they provided a fallback. Make sure its of our
                    # expected type and return it.
                    assert isinstance(out, anntype)
                    return out
            raise

        return self._dataclass_from_input(mttype, fieldpath, value)

    def _tuple_from_input(
        self,
        cls: type,
        fieldpath: str,
        anntype: Any,
        value: Any,
        ioattrs: IOAttrs | None,
    ) -> Any:
        # pylint: disable=too-many-positional-arguments
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

    def _timedelta_from_input(
        self, cls: type, fieldpath: str, value: Any, ioattrs: IOAttrs | None
    ) -> Any:
        del ioattrs  # Unused.
        # We expect a list of 3 ints.
        if type(value) is not list:
            raise TypeError(
                f'Invalid input value for "{fieldpath}" on "{cls.__name__}";'
                f' expected a list, got a {type(value).__name__}'
            )
        if len(value) != 3 or not all(isinstance(x, int) for x in value):
            raise ValueError(
                f'Invalid input value for "{fieldpath}" on "{cls.__name__}";'
                f' expected a list of 3 ints, got {[type(v) for v in value]}.'
            )
        out = datetime.timedelta(
            days=value[0], seconds=value[1], microseconds=value[2]
        )
        return out
