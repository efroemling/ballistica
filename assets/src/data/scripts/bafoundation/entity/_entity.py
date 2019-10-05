# Synced from bamaster.
# EFRO_SYNC_HASH=11716656185614230313846373816308841148
#
"""Functionality for the actual Entity types."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, TypeVar

from bafoundation.entity._support import FieldInspector, BoundCompoundValue
from bafoundation.entity._value import CompoundValue
from bafoundation.jsonutils import ExtendedJSONEncoder, ExtendedJSONDecoder

if TYPE_CHECKING:
    from typing import Dict, Any, Type, Union

T = TypeVar('T', bound='EntityMixin')


class EntityMixin:
    """Mixin class to add data-storage to ComplexValue, forming an Entity.

    Distinct Entity types should inherit from this first and a CompoundValue
    (sub)type second. This order ensures that constructor arguments for this
    class are accessible on the new type.
    """

    def __init__(self, d_data: Dict[str, Any] = None,
                 error: bool = False) -> None:
        super().__init__()
        if not isinstance(self, CompoundValue):
            raise RuntimeError('EntityMixin class must be combined'
                               ' with a CompoundValue class.')

        # Underlying data for this entity; fields simply operate on this.
        self.d_data: Dict[str, Any] = {}
        assert isinstance(self, EntityMixin)
        self.set_data(d_data if d_data is not None else {}, error=error)

    def reset(self) -> None:
        """Resets data to default."""
        self.set_data({}, error=True)

    def set_data(self, data: Dict, error: bool = False) -> None:
        """Set the data for this entity and apply all value filters to it.

        Note that it is more efficient to pass data to an Entity's constructor
        than it is to create a default Entity and then call this on it.
        """
        self.d_data = data
        assert isinstance(self, CompoundValue)
        self.apply_fields_to_data(self.d_data, error=error)

    def copy_data(self,
                  target: Union[CompoundValue, BoundCompoundValue]) -> None:
        """Copy data from a target Entity or compound-value.

        This first verifies that the target has a matching set of fields
        and then copies its data into ourself. To copy data into a nested
        compound field, the assignment operator can be used.
        """
        import copy
        from bafoundation.entity.util import have_matching_fields
        tvalue: CompoundValue
        if isinstance(target, CompoundValue):
            tvalue = target
        elif isinstance(target, BoundCompoundValue):
            tvalue = target.d_value
        else:
            raise TypeError(
                'Target must be a CompoundValue or BoundCompoundValue')
        target_data = getattr(target, 'd_data', None)
        if target_data is None:
            raise ValueError('Target is not bound to data.')
        assert isinstance(self, CompoundValue)
        if not have_matching_fields(self, tvalue):
            raise ValueError(
                f"Fields for target {type(tvalue)} do not match ours"
                f" ({type(self)}); can't copy data.")
        self.d_data = copy.deepcopy(target_data)

    def steal_data(self, target: EntityMixin) -> None:
        """Steal data from another entity.

        This is more efficient than copy_data, as data is moved instead
        of copied.  However this leaves the target object in an invalid
        state, and it must no longer be used after this call.
        This can be convenient for entities to use to update themselves
        with the result of a database transaction (which generally return
        fresh entities).
        """
        from bafoundation.entity.util import have_matching_fields
        if not isinstance(target, EntityMixin):
            raise TypeError('EntityMixin is required.')
        assert isinstance(target, CompoundValue)
        assert isinstance(self, CompoundValue)
        if not have_matching_fields(self, target):
            raise ValueError(
                f"Fields for target {type(target)} do not match ours"
                f" ({type(self)}); can't steal data.")
        assert target.d_data is not None
        self.d_data = target.d_data
        target.d_data = None

    def get_pruned_data(self) -> Dict[str, Any]:
        """Return a pruned version of this instance's data.

        This varies from d_data in that values may be stripped out if
        they are equal to defaults (if the field allows such).
        """
        import copy
        data = copy.deepcopy(self.d_data)
        assert isinstance(self, CompoundValue)
        self.prune_fields_data(data)
        return data

    def to_json_str(self, pretty: bool = False) -> str:
        """Convert the entity to a json string.

        This uses bafoundation.jsontools.ExtendedJSONEncoder/Decoder
        to support data types not natively storable in json.
        """
        if pretty:
            return json.dumps(self.d_data,
                              indent=2,
                              sort_keys=True,
                              cls=ExtendedJSONEncoder)
        return json.dumps(self.d_data,
                          separators=(',', ':'),
                          cls=ExtendedJSONEncoder)

    @staticmethod
    def json_loads(s: str) -> Any:
        """Load a json string with our special extended decoder.

        Note that this simply returns loaded json data; no
        Entities are involved.
        """
        return json.loads(s, cls=ExtendedJSONDecoder)

    def load_from_json_str(self, s: str, error: bool = False) -> None:
        """Set the entity's data in-place from a json string.

        The 'error' argument determines whether Exceptions will be raised
        for invalid data values. Values will be reset/conformed to valid ones
        if error is False. Note that Exceptions will always be raised
        in the case of invalid formatted json.
        """
        data = self.json_loads(s)
        self.set_data(data, error=error)

    @classmethod
    def from_json_str(cls: Type[T], s: str, error: bool = False) -> T:
        """Instantiate a new instance with provided json string.

        The 'error' argument determines whether exceptions will be raised
        on invalid data values. Values will be reset/conformed to valid ones
        if error is False. Note that exceptions will always be raised
        in the case of invalid formatted json.
        """
        obj = cls(d_data=cls.json_loads(s), error=error)
        return obj

    # Note: though d_fields actually returns a FieldInspector,
    # in type-checking-land we currently just say it returns self.
    # This allows the type-checker to at least validate subfield access,
    # though the types will be incorrect (values instead of inspectors).
    # This means that anything taking FieldInspectors needs to take 'Any'
    # at the moment. Hopefully we can make this cleaner via a mypy
    # plugin at some point.
    if TYPE_CHECKING:

        @property
        def d_fields(self: T) -> T:
            """For accessing entity field objects (as opposed to values)."""
            ...
    else:

        @property
        def d_fields(self):
            """For accessing entity field objects (as opposed to values)."""
            return FieldInspector(self, self, [], [])


class Entity(EntityMixin, CompoundValue):
    """A data class consisting of Fields and their underlying data.

    Fields and Values simply define a data layout; Entities are concrete
    objects using those layouts.

    Inherit from this class and add Fields to define a simple Entity type.
    Alternately, combine an EntityMixin with any CompoundValue child class
    to accomplish the same. The latter allows sharing CompoundValue
    layouts between different concrete Entity types. For example, a
    'Weapon' CompoundValue could be embedded as part of a 'Character'
    Entity but also exist as a distinct Entity in an armory database.
    """
