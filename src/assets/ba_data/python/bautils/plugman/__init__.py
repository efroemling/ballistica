# Released under the MIT License. See LICENSE for details.
#
"""Package that handles plugin management for server."""

# ba_meta require api 9
import babase as ba

def _load_plugins() -> None:
    try:
        from . import powerups as _powerups
        # print(f"[PLUGMAN] powerups plugin loaded ({_powerups.__file__})")
    except Exception as exc:
        print(f"[PLUGMAN] failed to load powerups plugin: {exc}")

ba.pushcall(_load_plugins)
