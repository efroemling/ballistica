# Released under the MIT License. See LICENSE for details.
#
"""Color helpers usable anywhere (client, servers, tools).

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.

Pure-Python counterparts of engine color functions, for code that can't
call into the engine (server-side doc-ui pages, say); game code uses
the engine's own (``babase.safecolor``). They must match the engine's
results; a test checks them against it.
"""

import math


def safe_color(
    color: tuple[float, float, float], target_intensity: float = 0.6
) -> tuple[float, float, float]:
    """Make a color read well as text over typical game backgrounds.

    Lifts its perceptual lightness (OKLab L) to a floor, keeping its
    hue, and takes away only as much chroma as it takes to stay a
    displayable color. Never darkens; colors already light enough come
    back untouched. The floor eases out from 0 at a
    ``target_intensity`` of 0 (no change) to 0.755 at 1.0 (higher goes
    pastel): quick at first, flattening toward the top, so low targets
    differ visibly and high ones don't wash out. About 0.63 at the
    default 0.6.

    The same as the engine's ``babase.safecolor`` (C++
    ``Graphics::GetSafeColor``); keep the two in step.
    """
    target = min(1.0, max(0.0, target_intensity))
    min_lightness = 0.755 * target * (2.0 - target)
    lab = _srgb_to_oklab(color)
    if lab[0] >= min_lightness:
        return color
    chroma = math.hypot(lab[1], lab[2])
    hue = math.atan2(lab[2], lab[1])

    # Binary-search the most chroma that fits at the new lightness.
    lo, hi = 0.0, chroma
    best = (min_lightness, 0.0, 0.0)
    for _ in range(20):
        mid = (lo + hi) * 0.5
        trial = (min_lightness, mid * math.cos(hue), mid * math.sin(hue))
        if _in_gamut(_oklab_to_linear(trial)):
            best, lo = trial, mid
        else:
            hi = mid
    lin = _oklab_to_linear(best)
    return (
        _linear_to_srgb(min(1.0, max(0.0, lin[0]))),
        _linear_to_srgb(min(1.0, max(0.0, lin[1]))),
        _linear_to_srgb(min(1.0, max(0.0, lin[2]))),
    )


def _srgb_to_linear(val: float) -> float:
    return val / 12.92 if val <= 0.04045 else ((val + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(val: float) -> float:
    return 12.92 * val if val <= 0.0031308 else 1.055 * val ** (1 / 2.4) - 0.055


def _srgb_to_oklab(
    rgb: tuple[float, float, float],
) -> tuple[float, float, float]:
    red, green, blue = (_srgb_to_linear(min(1.0, max(0.0, v))) for v in rgb)
    lval = math.cbrt(
        0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue
    )
    mval = math.cbrt(
        0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue
    )
    sval = math.cbrt(
        0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue
    )
    return (
        0.2104542553 * lval + 0.7936177850 * mval - 0.0040720468 * sval,
        1.9779984951 * lval - 2.4285922050 * mval + 0.4505937099 * sval,
        0.0259040371 * lval + 0.7827717662 * mval - 0.8086757660 * sval,
    )


def _oklab_to_linear(
    lab: tuple[float, float, float],
) -> tuple[float, float, float]:
    lval = (lab[0] + 0.3963377774 * lab[1] + 0.2158037573 * lab[2]) ** 3
    mval = (lab[0] - 0.1055613458 * lab[1] - 0.0638541728 * lab[2]) ** 3
    sval = (lab[0] - 0.0894841775 * lab[1] - 1.2914855480 * lab[2]) ** 3
    return (
        4.0767416621 * lval - 3.3077115913 * mval + 0.2309699292 * sval,
        -1.2684380046 * lval + 2.6097574011 * mval - 0.3413193965 * sval,
        -0.0041960863 * lval - 0.7034186147 * mval + 1.7076147010 * sval,
    )


def _in_gamut(rgb: tuple[float, float, float]) -> bool:
    return all(-0.0001 <= v <= 1.0001 for v in rgb)
