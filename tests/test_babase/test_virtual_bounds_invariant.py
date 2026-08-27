# Released under the MIT License. See LICENSE for details.
"""Tests for the virtual-bounds projection invariant.

Virtual bounds promise one thing: an inset render rect with no bounds
inset must look *exactly* the same as a full-window render rect with a
matching bounds inset. The only difference is what fills the outside --
black in the first case, real drawn content in the second. Everything
inside the bounds must land on identical pixels.

These assert that in coordinates rather than pixels, which is the
lesson of how the bug that motivated them was found: two rounds of
screenshot comparison reported "no difference" (one scanned only for
translation, so a scale error hid as a false zero; both averaged over
regions where aligned UI and shift-insensitive sky outvoted the
geometry actually under test), while logging where fixed points land
in window coordinates found it immediately and unambiguously.

The bug in question was a latent sign error in ``Matrix44fFrustum``'s
horizontal off-center term, invisible for as long as every caller
passed a symmetric frustum. ``test_offcenter_frustum_not_mirrored``
covers it directly, since an asymmetric frustum is otherwise only
built on the VR path where nobody would notice.

Needs the engine binary (the probe runs the renderer's own frustum
math rather than a copy of it), so everything here is gated on
``apprun.test_runs_disabled()`` -- without it these fail on the
Windows CI runner, which can't assemble a complete build without WSL.
"""

import os
import json
import subprocess

import pytest

from batools import apprun

#: A window, and an asymmetric inset within it. Asymmetric on all four
#: edges on purpose: a symmetric inset hides a transposed or
#: sign-flipped axis, which is exactly the failure class here.
_WINDOW = (0.0, 0.0, 2048.0, 1152.0)
_INSET_L = 0.06
_INSET_R = 0.02
_INSET_B = 0.10
_INSET_T = 0.035

#: Eye-space probe points. Spread off-axis in both directions so a
#: mirrored or rescaled projection cannot coincidentally agree; z is
#: negative since that is in front of the camera.
_POINTS = [
    (0.0, 0.0, -30.0),
    (8.0, 0.0, -30.0),
    (-8.0, 0.0, -30.0),
    (0.0, 5.0, -30.0),
    (0.0, -5.0, -30.0),
    (6.0, 4.0, -50.0),
    (-6.0, -4.0, -18.0),
]


def _inset_rect(
    rect: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """The bounds rect: `rect` inset by the fixed asymmetric amounts."""
    left, bottom, right, top = rect
    width = right - left
    height = top - bottom
    return (
        left + width * _INSET_L,
        bottom + height * _INSET_B,
        right - width * _INSET_R,
        top - height * _INSET_T,
    )


def _run_python(code: str) -> str:
    """Run a snippet under the engine binary and return its output.

    Mirrors :func:`batools.apprun.python_command`, which does not
    capture output, since these assertions are all about what the
    snippet printed.
    """
    binpath = apprun.acquire_binary(purpose='virtual-bounds invariant test')
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
    err = result.stderr.decode(errors='replace')
    if 'PROBERESULT' not in out:
        pytest.fail(
            f'probe produced no result (exit {result.returncode}):\n'
            f'stdout:\n{out}\nstderr:\n{err}'
        )
    return out + err


def _probe(
    cases: list[tuple[str, tuple, tuple]],
) -> dict[str, list[list[float]]]:
    """Run the projection probe under the engine for each case."""
    payload = json.dumps([(name, list(rr), list(br)) for name, rr, br in cases])
    points = json.dumps([list(p) for p in _POINTS])
    code = (
        'import json, _babase\n'
        f'cases = json.loads({payload!r})\n'
        f'points = json.loads({points!r})\n'
        'out = {}\n'
        'for name, rr, br in cases:\n'
        '    out[name] = [\n'
        '        list(p)\n'
        '        for p in _babase.virtual_bounds_project_probe(\n'
        '            render_rect=rr, bounds_rect=br, points=points\n'
        '        )\n'
        '    ]\n'
        "print('PROBERESULT' + json.dumps(out))\n"
    )
    text = _run_python(code)
    for line in text.splitlines():
        if line.startswith('PROBERESULT'):
            parsed: dict[str, list[list[float]]] = json.loads(
                line[len('PROBERESULT') :]
            )
            return parsed
    raise AssertionError(f'probe produced no result. Output:\n{text[-3000:]}')


def _calc(
    cases: list[tuple[str, dict]],
    probe: str = 'virtual_bounds_calc_probe',
) -> dict[str, list[float]]:
    """Run a bounds-derivation probe under the engine for each case."""
    payload = json.dumps(list(cases))
    code = (
        'import json, _babase\n'
        f'cases = json.loads({payload!r})\n'
        'out = {}\n'
        'for name, kwargs in cases:\n'
        '    out[name] = list(\n'
        f'        _babase.{probe}(**kwargs)\n'
        '    )\n'
        "print('PROBERESULT' + json.dumps(out))\n"
    )
    text = _run_python(code)
    for line in text.splitlines():
        if line.startswith('PROBERESULT'):
            parsed: dict[str, list[float]] = json.loads(
                line[len('PROBERESULT') :]
            )
            return parsed
    raise AssertionError(f'probe produced no result. Output:\n{text[-3000:]}')


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_insets_do_not_stack_with_an_already_inset_rect() -> None:
    """A rect already clear of the cutout gets no further inset.

    tv-mode's border and the aspect clamp both pull the render rect in
    before we ever see it. Insetting that rect by the OS values would
    double-count, so the two are intersected instead: whichever
    constraint reaches further in wins, and neither adds to the other.

    Worth pinning because it only misbehaves in a combination nobody
    routinely runs -- a cutout device with tv-mode switched on -- so a
    regression here would sit unnoticed.
    """
    res_x = 1000.0
    res_y = 500.0
    # A cutout covering the leftmost 8% of the screen.
    inset_l = 0.08

    # Render rect at full screen: bounds pull in to clear the cutout.
    full = _calc(
        [
            (
                'full',
                {
                    'render_rect': [0.0, 0.0, res_x, res_y],
                    'res_x': res_x,
                    'res_y': res_y,
                    'inset_l': inset_l,
                },
            )
        ]
    )['full']
    assert full[0] == pytest.approx(80.0, abs=0.01), (
        f'expected the bounds to start at the cutout edge (80.0),'
        f' got {full[0]}'
    )

    # Now a render rect already starting past the cutout (as tv-mode
    # would produce). Nothing further may be given up.
    for start in (80.0, 100.0, 150.0):
        name = f'inset{int(start)}'
        got = _calc(
            [
                (
                    name,
                    {
                        'render_rect': [start, 0.0, res_x, res_y],
                        'res_x': res_x,
                        'res_y': res_y,
                        'inset_l': inset_l,
                    },
                )
            ]
        )[name]
        assert got[0] == pytest.approx(start, abs=0.01), (
            f'a render rect starting at {start} is already clear of a'
            f' cutout ending at 80.0, so its bounds must start at'
            f' {start}; got {got[0]}. Insets are stacking rather than'
            ' intersecting.'
        )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_bleed_gives_back_exactly_its_virtual_size() -> None:
    """A bleed of N gives back N virtual units of overhang.

    That is the bleed's defining property rather than an incidental
    one: it is specified in the units we draw in so that a rect of
    that size, drawn in virtual coords, matches the overhang exactly.
    Pinning it in pixels here means converting through the same
    virtual scale the renderer uses.
    """
    # A landscape rect wider than the base aspect, so virtual res pins
    # height to 720 and the scale is px_per_unit = height / 720.
    res_x = 2000.0
    res_y = 800.0
    rect = [0.0, 0.0, res_x, res_y]
    px_per_unit = res_y / 720.0

    inset_l = 0.10  # 200px
    bleed_units = 40.0
    res = _calc(
        [
            (
                'plain',
                {
                    'render_rect': rect,
                    'res_x': res_x,
                    'res_y': res_y,
                    'inset_l': inset_l,
                },
            ),
            (
                'bled',
                {
                    'render_rect': rect,
                    'res_x': res_x,
                    'res_y': res_y,
                    'inset_l': inset_l,
                    'bleed': bleed_units,
                },
            ),
        ]
    )
    given_back = res['plain'][0] - res['bled'][0]
    assert given_back == pytest.approx(bleed_units * px_per_unit, abs=0.01), (
        f'a {bleed_units}-unit bleed should give back'
        f' {bleed_units * px_per_unit} px at this scale; got {given_back}'
    )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_bleed_never_escapes_the_render_rect() -> None:
    """Bleed past a small inset stops at the render rect, not beyond.

    Otherwise an obstruction shallower than the bleed would push the
    bounds off the edge of what we actually draw into.
    """
    res_x = 2000.0
    res_y = 800.0
    rect = [0.0, 0.0, res_x, res_y]
    res = _calc(
        [
            (
                'tiny',
                {
                    'render_rect': rect,
                    'res_x': res_x,
                    'res_y': res_y,
                    'inset_l': 0.001,
                    'bleed': 400.0,
                },
            ),
        ]
    )['tiny']
    assert res[0] == pytest.approx(
        0.0, abs=0.01
    ), f'bleed should stop at the render rect edge (0.0); got {res[0]}'


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_inset_clamp_limits_what_we_give_up() -> None:
    """An absurd inset costs a corner, not the play area."""
    res_x = 1000.0
    res_y = 500.0
    got = _calc(
        [
            (
                'absurd',
                {
                    'render_rect': [0.0, 0.0, res_x, res_y],
                    'res_x': res_x,
                    'res_y': res_y,
                    'inset_l': 0.9,
                },
            )
        ]
    )['absurd']
    # Clamped to kMaxVirtualBoundsInsetFraction (0.15) of the rect.
    assert got[0] == pytest.approx(150.0, abs=0.01), (
        f'a 90% inset should clamp to 15% of the rect (150.0);' f' got {got[0]}'
    )
    assert got[2] == pytest.approx(res_x, abs=0.01)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_no_insets_leaves_the_rect_alone() -> None:
    """Zero insets -- every build without cutouts -- changes nothing."""
    res_x = 1000.0
    res_y = 500.0
    for name, rect in (
        ('full', [0.0, 0.0, res_x, res_y]),
        ('tvmode', [35.0, 17.5, res_x - 35.0, res_y - 17.5]),
    ):
        got = _calc(
            [(name, {'render_rect': rect, 'res_x': res_x, 'res_y': res_y})]
        )[name]
        assert got == pytest.approx(rect, abs=0.01)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_top_bottom_insets_are_ignored_for_now() -> None:
    """Only left/right are honored; the other axis is dropped.

    Pins the *policy* rather than the mechanism -- the calc accepts all
    four so honoring the rest later is a change in one place. If that
    day comes this test should be updated, not deleted.
    """
    res_x = 1000.0
    res_y = 500.0
    got = _calc(
        [
            (
                'tb',
                {
                    'render_rect': [0.0, 0.0, res_x, res_y],
                    'res_x': res_x,
                    'res_y': res_y,
                    'inset_b': 0.1,
                    'inset_t': 0.1,
                },
            )
        ]
    )['tb']
    assert got == pytest.approx([0.0, 0.0, res_x, res_y], abs=0.01)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_max_margins_are_exact_virtual_units() -> None:
    """Forced max margins measure exactly N virtual units on every edge.

    The margins are specified in virtual units while the virtual scale
    derives from the bounds being computed; the calc solves that fixed
    point exactly rather than approximating it. So whatever the window
    shape or pin branch, converting the resulting pixel margins back
    through the bounds' own virtual scale must give exactly the
    requested values -- that constancy across devices is the whole
    point of the mode (a stable margin target to calibrate UIs
    against).
    """
    base_x, base_y = 1280.0, 720.0
    margin_x, margin_y = 80.0, 40.0
    cases = {
        # Wider than the base aspect: virtual res pins height.
        'wide': [0.0, 0.0, 2560.0, 1080.0],
        # Narrower than the base aspect: pins width.
        'narrow': [0.0, 0.0, 1000.0, 900.0],
        # Offset origin (as tv-border produces), near the base aspect
        # so the pin-branch choice is not a foregone conclusion.
        'offset': [100.0, 50.0, 2148.0, 1202.0],
    }
    got = _calc(
        [
            (
                name,
                {
                    'render_rect': rect,
                    'base_res_x': base_x,
                    'base_res_y': base_y,
                    'margin_x': margin_x,
                    'margin_y': margin_y,
                },
            )
            for name, rect in cases.items()
        ],
        probe='virtual_bounds_max_margins_probe',
    )
    for name, rect in cases.items():
        left, bottom, right, top = got[name]
        bwidth = right - left
        bheight = top - bottom
        assert bwidth > 0.0 and bheight > 0.0
        # Derive the virtual scale the way CalcVirtualRes_ will: pin
        # height to the base res when the bounds are wider than the
        # base aspect, else pin width.
        if bwidth / bheight > base_x / base_y:
            scale = bheight / base_y
        else:
            scale = bwidth / base_x
        margins = {
            'left': (left - rect[0]) / scale,
            'bottom': (bottom - rect[1]) / scale,
            'right': (rect[2] - right) / scale,
            'top': (rect[3] - top) / scale,
        }
        for edge, expected in (
            ('left', margin_x),
            ('right', margin_x),
            ('bottom', margin_y),
            ('top', margin_y),
        ):
            assert margins[edge] == pytest.approx(expected, abs=0.01), (
                f'case {name!r}: expected exactly {expected} virtual'
                f' units of {edge} margin; got {margins[edge]}'
            )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_max_margins_zero_is_a_no_op() -> None:
    """Zero margins hand back the render rect untouched."""
    rect = [0.0, 0.0, 2000.0, 800.0]
    got = _calc(
        [
            (
                'zero',
                {
                    'render_rect': rect,
                    'base_res_x': 1280.0,
                    'base_res_y': 720.0,
                    'margin_x': 0.0,
                    'margin_y': 0.0,
                },
            )
        ],
        probe='virtual_bounds_max_margins_probe',
    )['zero']
    assert got == pytest.approx(rect, abs=0.01)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_inset_render_rect_matches_inset_bounds() -> None:
    """The core promise: config A and config B agree, pixel for pixel.

    A: render rect inset to the bounds (black outside).
    B: render rect left full (drawn content outside).
    Same bounds rect in both, so anything inside it must match.
    """
    bounds = _inset_rect(_WINDOW)
    res = _probe(
        [
            ('a', bounds, bounds),
            ('b', _WINDOW, bounds),
        ]
    )

    for idx, (pa, pb) in enumerate(zip(res['a'], res['b'])):
        assert pa[0] == pytest.approx(pb[0], abs=0.01), (
            f'point {idx} {_POINTS[idx]} lands at x={pa[0]:.3f} with an'
            f' inset render rect but x={pb[0]:.3f} with an inset bounds;'
            ' these must be identical.'
        )
        assert pa[1] == pytest.approx(pb[1], abs=0.01), (
            f'point {idx} {_POINTS[idx]} lands at y={pa[1]:.3f} with an'
            f' inset render rect but y={pb[1]:.3f} with an inset bounds;'
            ' these must be identical.'
        )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_offcenter_frustum_not_mirrored() -> None:
    """An off-center frustum must not mirror about the view axis.

    Regression test for the ``Matrix44fFrustum`` horizontal sign bug.
    The view axis (an eye-space point straight ahead) has to land at
    the *centre of the bounds*, since that is what the composition is
    built around. Under the old sign it landed mirrored across the
    render rect's centre instead, off by twice the off-centeredness.
    """
    bounds = _inset_rect(_WINDOW)
    res = _probe([('b', _WINDOW, bounds)])
    axis_x, axis_y = res['b'][0]

    want_x = 0.5 * (bounds[0] + bounds[2])
    want_y = 0.5 * (bounds[1] + bounds[3])
    assert axis_x == pytest.approx(want_x, abs=0.01), (
        f'view axis landed at x={axis_x:.3f}; expected the bounds centre'
        f' x={want_x:.3f}. An off-center frustum is being mirrored.'
    )
    assert axis_y == pytest.approx(want_y, abs=0.01), (
        f'view axis landed at y={axis_y:.3f}; expected the bounds centre'
        f' y={want_y:.3f}. An off-center frustum is being mirrored.'
    )


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_no_inset_is_a_no_op() -> None:
    """With bounds equal to the render rect nothing may move.

    The steady state for every build that has no cutouts, so a
    regression here would be far more visible than one in the inset
    case -- worth pinning explicitly rather than assuming.
    """
    res = _probe(
        [
            ('plain', _WINDOW, _WINDOW),
            ('same', _WINDOW, _WINDOW),
        ]
    )
    assert res['plain'] == res['same']

    # And the view axis sits dead centre, as it must with a symmetric
    # frustum filling the whole rect.
    axis_x, axis_y = res['plain'][0]
    assert axis_x == pytest.approx(0.5 * (_WINDOW[0] + _WINDOW[2]), abs=0.01)
    assert axis_y == pytest.approx(0.5 * (_WINDOW[1] + _WINDOW[3]), abs=0.01)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_invariant_holds_for_lopsided_insets() -> None:
    """One-sided and extreme insets keep the invariant too.

    The fixed inset above is asymmetric but modest. These are the
    shapes where an axis mix-up or a wrong denominator stops being
    subtle -- an inset on one edge only leaves nothing to cancel a
    sign error against.
    """
    left, bottom, right, top = _WINDOW
    width = right - left
    height = top - bottom
    variants = {
        'left_only': (left + width * 0.25, bottom, right, top),
        'bottom_only': (left, bottom + height * 0.30, right, top),
        'top_only': (left, bottom, right, top - height * 0.30),
        'lopsided': (
            left + width * 0.18,
            bottom + height * 0.02,
            right - width * 0.01,
            top - height * 0.22,
        ),
    }
    cases: list[tuple[str, tuple, tuple]] = []
    for name, bounds in variants.items():
        cases.append((f'{name}_a', bounds, bounds))
        cases.append((f'{name}_b', _WINDOW, bounds))
    res = _probe(cases)

    for name in variants:
        for idx, (pa, pb) in enumerate(zip(res[f'{name}_a'], res[f'{name}_b'])):
            assert pa[0] == pytest.approx(pb[0], abs=0.01), (
                f'{name}: point {idx} x mismatch'
                f' ({pa[0]:.3f} vs {pb[0]:.3f})'
            )
            assert pa[1] == pytest.approx(pb[1], abs=0.01), (
                f'{name}: point {idx} y mismatch'
                f' ({pa[1]:.3f} vs {pb[1]:.3f})'
            )
