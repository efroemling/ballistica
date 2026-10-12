# Released under the MIT License. See LICENSE for details.
#
"""The allowed span of each numeric value in a character.

The one table of these spans. The game clamps every value it reads to
its span here (its constants are generated from this module), the
cloud checks delivered characters against it, and authoring tools show
and build characters clamped to it, so what an author sees is what
plays.

Physique spans are exactly what the legacy style presets covered. They
are simulation state (every machine in a game derives the same rigid
bodies from them), so widening one changes gameplay. The look spans
are looser than legacy to give characters visual headroom.

Changing a span here changes it everywhere at once, the next time each
side is built. An older game build keeps the spans it shipped with, so
a widened span only takes effect on builds made after the change.
"""

#: An inclusive ``(low, high)`` span. For a value with several
#: components (a color, an offset) it applies to each one.
type Range = tuple[float, float]

#: Spans for a basic spaz's own values, keyed by what the value is.
#: ``highlight`` covers every highlight color and
#: ``team_coloring_strength`` every team-coloring strength.
BASIC_SPAZ_RANGES: dict[str, Range] = {
    'color': (0.0, 1.0),
    'highlight': (0.0, 1.0),
    'team_coloring_strength': (0.0, 1.0),
    'torso_radius': (0.11, 0.3),
    'shoulder_offset': (-0.05, 0.03),
    'thigh_radius': (0.04, 0.06),
    'ankle_radius': (0.045, 0.07),
    'step_separation': (0.03, 0.08),
    'idle_arm_stiffness': (0.2, 1.0),
    'arm_swing': (0.3, 0.6),
    'idle_sway': (0.02, 0.05),
    'eye_scale': (0.5, 2.0),
    'eye_offset': (-0.5, 0.5),
    'eye_color': (0.0, 2.0),
    'eyeball_color': (0.0, 1.0),
    'eyelid_color': (0.0, 1.0),
    'eyelid_angle': (-30.0, 30.0),
    'reflection_scale': (0.0, 2.0),
}

#: Spans for an attachment's values. ``position`` is where a simulated
#: attachment sits on its body part (the classic hair rig peaks at
#: 0.3); the rest are its tuning dials, whose whole useful span this
#: is, so none can be overdriven.
ATTACHMENT_RANGES: dict[str, Range] = {
    'position': (-0.5, 0.5),
    'stiffness': (0.0, 1.0),
    'damping': (0.0, 1.0),
    'drag': (0.0, 1.0),
    'curl': (-1.0, 1.0),
    'length': (0.0, 1.0),
    'radius': (0.0, 1.0),
    'curl_change': (-1.0, 1.0),
    'length_change': (-1.0, 1.0),
    'radius_change': (-1.0, 1.0),
    'stiffness_change': (-1.0, 1.0),
    'damping_change': (-1.0, 1.0),
}


def clamp(value: float, span: Range) -> float:
    """Return a value held within a span."""
    return min(max(value, span[0]), span[1])
