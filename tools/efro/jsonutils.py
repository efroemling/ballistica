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
"""Custom json compressor/decompressor with support for more data times/etc."""

from __future__ import annotations

import datetime
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

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

    def default(self, obj: Any) -> Any:  # pylint: disable=W0221
        if isinstance(obj, datetime.datetime):

            # We only support timezone-aware utc times.
            if (obj.tzinfo is not datetime.timezone.utc
                    and (_pytz_utc is None or obj.tzinfo is not _pytz_utc)):
                raise ValueError(
                    'datetime values must have timezone set as timezone.utc')
            return {
                TYPE_TAG:
                    'dt',
                'v': [
                    obj.year, obj.month, obj.day, obj.hour, obj.minute,
                    obj.second, obj.microsecond
                ],
            }
        return super().default(obj)


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
