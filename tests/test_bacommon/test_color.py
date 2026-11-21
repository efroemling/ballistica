# Released under the MIT License. See LICENSE for details.
"""Checks that bacommon.color matches the engine's color functions.

``bacommon.color.safe_color`` is a pure-Python twin of the engine's
``babase.safecolor`` (C++ ``Graphics::GetSafeColor``), for code that
can't call into the engine. Both must give the same results; this runs
the engine's over a spread of colors and compares.

Needs the engine binary, so it's gated on
``apprun.test_runs_disabled()`` like the other engine-run tests.
"""

import os
import json
import subprocess

import pytest

from batools import apprun
from bacommon.color import safe_color

#: Colors and target intensities to compare: darks, saturated
#: primaries (where clamping bites), greys, already-bright colors, and
#: the team colors the game uses.
_COLORS: list[tuple[float, float, float]] = [
    (0.0, 0.0, 0.0),
    (0.05, 0.05, 0.05),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.1, 0.25, 1.0),
    (1.0, 0.25, 0.2),
    (0.2, 0.2, 0.6),
    (0.5, 0.5, 0.5),
    (1.0, 1.0, 1.0),
    (0.9, 0.8, 0.1),
    (0.3, 0.0, 0.4),
]
_TARGETS = [0.0, 0.4, 0.6, 0.75, 0.85, 1.0]


def test_safe_color_range() -> None:
    """Target 0 changes nothing; nothing ever comes back darker."""
    for color in _COLORS:
        assert safe_color(color, target_intensity=0.0) == color
        for target in _TARGETS:
            out = safe_color(color, target_intensity=target)
            assert sum(out) >= sum(color) - 1e-6, (color, target, out)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_safe_color_matches_engine() -> None:
    """bacommon.color.safe_color() == babase.safecolor() everywhere."""
    cases = [(c, t) for c in _COLORS for t in _TARGETS]
    code = (
        'import json, _babase\n'
        f'cases = json.loads({json.dumps(cases)!r})\n'
        'out = [list(_babase.safecolor(c, target_intensity=t))'
        ' for c, t in cases]\n'
        "print('COLORRESULT' + json.dumps(out))\n"
    )
    binpath = apprun.acquire_binary(purpose='safe-color parity test')
    bindir = os.path.dirname(binpath)
    env = dict(os.environ)
    env['PYTHONPATH'] = (
        f'{bindir}/ba_data/python:{bindir}/ba_data/python-site-packages'
    )
    result = subprocess.run(
        [binpath, '--command', code],
        capture_output=True,
        check=False,
        env=env,
    )
    out = result.stdout.decode(errors='replace')
    line = next(
        (ln for ln in out.splitlines() if ln.startswith('COLORRESULT')), None
    )
    if line is None:
        err = result.stderr.decode(errors='replace')
        pytest.fail(
            f'engine produced no result (exit {result.returncode}):\n'
            f'stdout:\n{out}\nstderr:\n{err}'
        )
    engine = json.loads(line[len('COLORRESULT') :])
    for (color, target), ecolor in zip(cases, engine):
        ours = safe_color(color, target_intensity=target)
        # (The engine works in 32-bit floats.)
        assert ours == pytest.approx(tuple(ecolor), abs=1e-5), (
            f'safe_color({color}, {target}) = {ours};'
            f' engine says {tuple(ecolor)}'
        )
