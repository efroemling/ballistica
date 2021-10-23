# Released under the MIT License. See LICENSE for details.
#
"""Functionality for prepping types for use with dataclassio."""

# Note: We do lots of comparing of exact types here which is normally
# frowned upon (stuff like isinstance() is usually encouraged).
# pylint: disable=unidiomatic-typecheck

from __future__ import annotations

import logging
from enum import Enum
import dataclasses
import typing
import datetime
from typing import TYPE_CHECKING, TypeVar, get_type_hints

# noinspection PyProtectedMember
from efro.dataclassio._base import _parse_annotated, _get_origin, SIMPLE_TYPES

if TYPE_CHECKING:
    from typing import Any

T = TypeVar('T')

# How deep we go when prepping nested types
# (basically for detecting recursive types)
MAX_RECURSION = 10

# Attr name for data we store on dataclass types as part of prep.
PREP_ATTR = '_DCIOPREP'


def ioprep(cls: type) -> None:
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
    must be defined at that level.
    """
    PrepSession(explicit=True).prep_dataclass(cls, recursion_level=0)


def ioprepped(cls: type[T]) -> type[T]:
    """Class decorator for easily prepping a dataclass at definition time.

    Note that in some cases it may not be possible to prep a dataclass
    immediately (such as when its type annotations refer to forward-declared
    types). In these cases, dataclass_prep() should be explicitly called for
    the class as soon as possible; ideally at module import time to expose any
    errors as early as possible in execution.
    """
    ioprep(cls)
    return cls


def is_ioprepped_dataclass(obj: Any) -> bool:
    """Return whether the obj is an ioprepped dataclass type or instance."""
    cls = obj if isinstance(obj, type) else type(obj)
    return dataclasses.is_dataclass(cls) and hasattr(cls, PREP_ATTR)


@dataclasses.dataclass
class PrepData:
    """Data we prepare and cache for a class during prep.

    This data is used as part of the encoding/decoding/validating process.
    """

    # Resolved annotation data with 'live' classes.
    annotations: dict[str, Any]

    # Map of storage names to attr names.
    storage_names_to_attr_names: dict[str, str]


class PrepSession:
    """Context for a prep."""

    def __init__(self, explicit: bool):
        self.explicit = explicit

    def prep_dataclass(self, cls: type, recursion_level: int) -> PrepData:
        """Run prep on a dataclass if necessary and return its prep data."""

        # We should only need to do this once per dataclass.
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
                ' efro.dataclassio.ioprep() or the'
                ' @efro.dataclassio.ioprepped decorator).', cls)

        try:
            # NOTE: Now passing the class' __dict__ (vars()) as locals
            # which allows us to pick up nested classes, etc.
            resolved_annotations = get_type_hints(cls,
                                                  localns=vars(cls),
                                                  include_extras=True)
            # pylint: enable=unexpected-keyword-arg
        except Exception as exc:
            print('GOT', cls.__dict__)
            raise TypeError(
                f'dataclassio prep for {cls} failed with error: {exc}.'
                f' Make sure all types used in annotations are defined'
                f' at the module or class level or add them as part of an'
                f' explicit prep call.') from exc

        # noinspection PyDataclass
        fields = dataclasses.fields(cls)
        fields_by_name = {f.name: f for f in fields}

        all_storage_names: set[str] = set()
        storage_names_to_attr_names: dict[str, str] = {}

        # Ok; we've resolved actual types for this dataclass.
        # now recurse through them, verifying that we support all contained
        # types and prepping any contained dataclass types.
        for attrname, anntype in resolved_annotations.items():

            anntype, ioattrs = _parse_annotated(anntype)

            # If we found attached IOAttrs data, make sure it contains
            # valid values for the field it is attached to.
            if ioattrs is not None:
                ioattrs.validate_for_field(cls, fields_by_name[attrname])
                if ioattrs.storagename is not None:
                    storagename = ioattrs.storagename
                    storage_names_to_attr_names[ioattrs.storagename] = attrname
                else:
                    storagename = attrname
            else:
                storagename = attrname

            # Make sure we don't have any clashes in our storage names.
            if storagename in all_storage_names:
                raise TypeError(f'Multiple attrs on {cls} are using'
                                f' storage-name \'{storagename}\'')
            all_storage_names.add(storagename)

            self.prep_type(cls,
                           attrname,
                           anntype,
                           recursion_level=recursion_level + 1)

        # Success! Store our resolved stuff with the class and we're done.
        prepdata = PrepData(
            annotations=resolved_annotations,
            storage_names_to_attr_names=storage_names_to_attr_names)
        setattr(cls, PREP_ATTR, prepdata)
        return prepdata

    def prep_type(self, cls: type, attrname: str, anntype: Any,
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
                    f' on {cls.__name__} is not supported by dataclassio.')

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

        # For Tuples, simply check individual member types.
        # (and, for now, explicitly disallow zero member types or usage
        # of ellipsis)
        if origin is tuple:
            childtypes = typing.get_args(anntype)
            if not childtypes:
                raise TypeError(
                    f'Tuple at \'{attrname}\''
                    f' has no type args; dataclassio requires type args.')
            if childtypes[-1] is ...:
                raise TypeError(f'Found ellipsis as part of type for'
                                f' \'{attrname}\' on {cls.__name__};'
                                f' these are not'
                                f' supported by dataclassio.')
            for childtype in childtypes:
                self.prep_type(cls,
                               attrname,
                               childtype,
                               recursion_level=recursion_level + 1)
            return

        if issubclass(origin, Enum):
            self.prep_enum(origin)
            return

        # We allow datetime objects (and google's extended subclass of them
        # used in firestore, which is why we don't look for exact type here).
        if issubclass(origin, datetime.datetime):
            return

        if dataclasses.is_dataclass(origin):
            self.prep_dataclass(origin, recursion_level=recursion_level + 1)
            return

        if origin is bytes:
            return

        raise TypeError(f"Attr '{attrname}' on {cls.__name__} contains"
                        f" type '{anntype}'"
                        f' which is not supported by dataclassio.')

    def prep_union(self, cls: type, attrname: str, anntype: Any,
                   recursion_level: int) -> None:
        """Run prep on a Union type."""
        typeargs = typing.get_args(anntype)
        if (len(typeargs) != 2
                or len([c for c in typeargs if c is type(None)]) != 1):
            raise TypeError(f'Union {anntype} for attr \'{attrname}\' on'
                            f' {cls.__name__} is not supported by dataclassio;'
                            f' only 2 member Unions with one type being None'
                            f' are supported.')
        for childtype in typeargs:
            self.prep_type(cls,
                           attrname,
                           childtype,
                           recursion_level=recursion_level + 1)

    def prep_enum(self, enumtype: type[Enum]) -> None:
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
