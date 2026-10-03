# Released under the MIT License. See LICENSE for details.
#
"""Tests for local-display config wire behavior.

The json riding a ``localdisplay`` node's ``config`` attr must decode
gracefully on clients older than the host that wrote it: unknown config
types degrade to :class:`bascenev1.UnknownLocalDisplayConfig` and
unknown fields on known types are ignored, and each client selects the
entry for its own build from the config set. These run under the engine
binary since ``bascenev1`` needs it to import.
"""

import os

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

_SNIPPET = '''
from efro.dataclassio import dataclass_to_json, dataclass_from_json
import bascenev1 as bs

# Round trip of a known type through a config set.
cfg = bs.ClassicControlsLocalDisplayConfig(
    position=(1.0, 2.0), scale=0.5, delay=3.0, lifespan=4.0, bright=True
)
cfgset = dataclass_from_json(
    bs.LocalDisplayConfigSet,
    bs.LocalDisplayConfigSet.single(cfg).to_json(),
    lossy=True,
)
assert cfgset.select(0) == cfg, cfgset
assert cfgset.select(99999) == cfg, cfgset

# A type id from some future build degrades to the unknown placeholder.
cfgset = dataclass_from_json(
    bs.LocalDisplayConfigSet, '{"c": {"0": {"_t": "zz", "x": 1}}}', lossy=True
)
assert isinstance(cfgset.select(1), bs.UnknownLocalDisplayConfig), cfgset

# A future field on a known type is ignored; omitted fields take defaults.
cfgset = dataclass_from_json(
    bs.LocalDisplayConfigSet,
    '{"c": {"0": {"_t": "cc", "s": 2.0, "future": true}}}',
    lossy=True,
)
out = cfgset.select(1)
assert isinstance(out, bs.ClassicControlsLocalDisplayConfig), out
assert out.scale == 2.0 and out.delay == 0.0, out

# Build gating: highest satisfied entry wins; unknown entries are
# skipped in favor of an older recognized one; entries above our
# build are ignored entirely.
cfgset = dataclass_from_json(
    bs.LocalDisplayConfigSet,
    '{"c": {"0": {"_t": "cc", "s": 1.0}, "100": {"_t": "cc", "s": 2.0},'
    ' "200": {"_t": "zz"}, "300": {"_t": "cc", "s": 3.0}}}',
    lossy=True,
)
assert cfgset.select(50).scale == 1.0
assert cfgset.select(150).scale == 2.0
assert cfgset.select(250).scale == 2.0  # 200 is unknown; fall back.
assert cfgset.select(300).scale == 3.0
assert bs.LocalDisplayConfigSet(configs={5: cfg}).select(4) is None
print("LOCALDISPLAY_CONFIG_OK")
'''


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_localdisplay_config_compat() -> None:
    """Known types round-trip; unknown types and fields degrade."""
    apprun.python_command(_SNIPPET, purpose='local-display config test')
