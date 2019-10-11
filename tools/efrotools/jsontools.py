# Copyright (c) 2011-2019 Eric Froemling
"""Json related tools functionality."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any


class NoIndent:
    """Used to prevent indenting in our custom json encoder.

    Wrap values in this before passing to encoder and all child
    values will be a single line in the json output."""

    def __init__(self, value: Any) -> None:
        self.value = value


class NoIndentEncoder(json.JSONEncoder):
    """Our custom encoder implementing selective indentation."""

    def __init__(self, *args: Any, **kwargs: Any):
        super(NoIndentEncoder, self).__init__(*args, **kwargs)
        self.kwargs = dict(kwargs)
        del self.kwargs['indent']
        self._replacement_map: Dict = {}

    def default(self, o: Any) -> Any:  # pylint: disable=method-hidden
        import uuid

        if isinstance(o, NoIndent):
            key = uuid.uuid4().hex
            self._replacement_map[key] = json.dumps(o.value, **self.kwargs)
            return "@@%s@@" % (key, )
        return super(NoIndentEncoder, self).default(o)

    def encode(self, o: Any) -> Any:
        result = super(NoIndentEncoder, self).encode(o)
        for k, v in self._replacement_map.items():
            result = result.replace('"@@%s@@"' % (k, ), v)
        return result
