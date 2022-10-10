# Released under the MIT License. See LICENSE for details.
#
"""Json related tools functionality."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class NoIndent:
    """Used to prevent indenting in our custom json encoder.

    Wrap values in this before passing to encoder and all child
    values will be a single line in the json output."""

    def __init__(self, value: Any) -> None:
        self.value = value


class NoIndentEncoder(json.JSONEncoder):
    """Our custom encoder implementing selective indentation."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.kwargs = dict(kwargs)
        del self.kwargs['indent']
        self._replacement_map: dict = {}

    def default(self, o: Any) -> Any:
        import uuid

        if isinstance(o, NoIndent):
            key = uuid.uuid4().hex
            self._replacement_map[key] = json.dumps(o.value, **self.kwargs)
            # pylint: disable=consider-using-f-string
            return '@@%s@@' % (key,)
        return super().default(o)

    def encode(self, o: Any) -> Any:
        result = super().encode(o)
        for k, v in self._replacement_map.items():
            # pylint: disable=consider-using-f-string
            result = result.replace('"@@%s@@"' % (k,), v)
        return result
