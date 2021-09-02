# Released under the MIT License. See LICENSE for details.
#
"""Custom json compressor/decompressor with support for more data times/etc."""

from __future__ import annotations

import datetime
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# NOTE: This functionality is duplicated in a newer, cleaner way in
# dataclassio. We should consider deprecating this along with entity at
# some point.

# Special attr we included for our extended type information
# (extended-json-type)
TYPE_TAG = '_xjtp'

_pytz_utc: Any

# We don't *require* pytz since it must be installed through pip
# but it is used by firestore client for its utc tzinfos.
# (in which case it should be installed as a dependency anyway)
try:
    import pytz
    _pytz_utc = pytz.utc
except ModuleNotFoundError:
    _pytz_utc = None  # pylint: disable=invalid-name


class ExtendedJSONEncoder(json.JSONEncoder):
    """Custom json encoder supporting additional types."""

    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):

            # We only support timezone-aware utc times.
            if (o.tzinfo is not datetime.timezone.utc
                    and (_pytz_utc is None or o.tzinfo is not _pytz_utc)):
                raise ValueError(
                    'datetime values must have timezone set as timezone.utc')
            return {
                TYPE_TAG:
                    'dt',
                'v': [
                    o.year, o.month, o.day, o.hour, o.minute, o.second,
                    o.microsecond
                ],
            }
        return super().default(o)


class ExtendedJSONDecoder(json.JSONDecoder):
    """Custom json decoder supporting extended types."""

    def __init__(self, *args: Any, **kwargs: Any):
        json.JSONDecoder.__init__(self,
                                  object_hook=self.object_hook,
                                  *args,
                                  **kwargs)

    def object_hook(self, obj: Any) -> Any:  # pylint: disable=E0202
        """Custom hook."""
        if TYPE_TAG not in obj:
            return obj
        objtype = obj[TYPE_TAG]
        if objtype == 'dt':
            vals = obj.get('v', [])
            if len(vals) != 7:
                raise ValueError('malformed datetime value')
            return datetime.datetime(  # type: ignore
                *vals, tzinfo=datetime.timezone.utc)
        return obj
