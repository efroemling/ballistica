# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Base classes for the entity system."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class DataHandler:
    """Base class for anything that can wrangle entity data.

    This contains common functionality shared by Fields and Values.
    """

    def get_default_data(self) -> Any:
        """Return the default internal data value for this object.

        This will be inserted when initing nonexistent entity data.
        """
        raise RuntimeError(f'get_default_data() unimplemented for {self}')

    def filter_input(self, data: Any, error: bool) -> Any:
        """Given arbitrary input data, return valid internal data.

        If error is True, exceptions should be thrown for any non-trivial
        mismatch (more than just int vs float/etc.). Otherwise the invalid
        data should be replaced with valid defaults and the problem noted
        via the logging module.
        The passed-in data can be modified in-place or returned as-is, or
        completely new data can be returned. Compound types are responsible
        for setting defaults and/or calling this recursively for their
        children. Data that is not used by the field (such as orphaned values
        in a dict field) can be left alone.

        Supported types for internal data are:
           - anything that works with json (lists, dicts, bools, floats, ints,
             strings, None) - no tuples!
           - datetime.datetime objects
        """
        del error  # unused
        return data

    def filter_output(self, data: Any) -> Any:
        """Given valid internal data, return user-facing data.

        Note that entity data is expected to be filtered to correctness on
        input, so if internal and extra entity data are the same type
        Value types such as Vec3 may store data internally as simple float
        tuples but return Vec3 objects to the user/etc. this is the mechanism
        by which they do so.
        """
        return data

    def prune_data(self, data: Any) -> bool:
        """Prune internal data to strip out default values/etc.

        Should return a bool indicating whether root data itself can be pruned.
        The object is responsible for pruning any sub-fields before returning.
        """


class BaseField(DataHandler):
    """Base class for all field types."""

    def __init__(self, d_key: str = None) -> None:

        # Key for this field's data in parent dict/list (when applicable;
        # some fields such as the child field under a list field represent
        # more than a single field entry so this is unused)
        self.d_key = d_key

    # IMPORTANT: this method should only be overridden in the eyes of the
    # type-checker (to specify exact return types). Subclasses should instead
    # override get_with_data() for doing the actual work, since that method
    # may sometimes be called explicitly instead of through __get__
    def __get__(self, obj: Any, type_in: Any = None) -> Any:
        if obj is None:
            # when called on the type, we return the field
            return self
        return self.get_with_data(obj.d_data)

    # IMPORTANT: same deal as __get__() (see note above)
    def __set__(self, obj: Any, value: Any) -> None:
        assert obj is not None
        self.set_with_data(obj.d_data, value, error=True)

    def get_with_data(self, data: Any) -> Any:
        """Get the field value given an explicit data source."""
        assert self.d_key is not None
        return self.filter_output(data[self.d_key])

    def set_with_data(self, data: Any, value: Any, error: bool) -> Any:
        """Set the field value given an explicit data target.

        If error is True, exceptions should be thrown for invalid data;
        otherwise the problem should be logged but corrected.
        """
        assert self.d_key is not None
        data[self.d_key] = self.filter_input(value, error=error)
