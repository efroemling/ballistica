# ba_meta require api 9
# ba_meta name Snowfall FX
# ba_meta description Adds snowfall particle effects in all maps.
# ba_meta author KritarthaT

import random
import bascenev1 as bs
import babase

def start_snowfall(activity: bs.Activity) -> None:
    if not hasattr(activity, 'map'):
        return

    try:
        bounds = activity.map.get_def_bound_box('map_bounds')
    except Exception:
        return

    def emit_snow() -> None:
        for i in range(int(bounds[3] * bounds[5])):

            def _emit() -> None:
                bs.emitfx(
                    position=(
                        random.uniform(bounds[0], bounds[3]),
                        random.uniform(bounds[4] * 1.2, bounds[4] * 1.45),
                        random.uniform(bounds[2], bounds[5])
                    ),
                    velocity=(0, 0, 0),
                    scale=random.uniform(1.0, 1.6),
                    count=random.randint(6, 12),
                    spread=random.uniform(0.03, 0.08),
                    chunk_type='ice'  # ❄️ Snowflake particle
                )

            bs.timer(random.uniform(0.01, 0.05) * (i + 1), _emit)

    bs.timer(0.5, emit_snow, repeat=True)

# ba_meta export plugin
class SnowfallFX(babase.Plugin):
    def __init__(self):
        bs.Activity.__init__ = self._wrap_activity_init(bs.Activity.__init__)

    def _wrap_activity_init(self, original_init):
        def new_init(activity_self, settings):
            original_init(activity_self, settings)
            bs.timer(1.0, lambda: start_snowfall(activity_self))
        return new_init
