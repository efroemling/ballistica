# Released under the MIT License. See LICENSE for details.
#
"""Package that handles plugin management for server."""

# ba_meta require api 9
import os


def _load_plugins() -> None:
    try:
        from . import powerups as _powerups

        # Ensure patch applied even if importer cached an old reference.
        if hasattr(_powerups, "_apply_patch"):
            _powerups._apply_patch()  # type: ignore[attr-defined]
        # print(f"[PLUGMAN] powerups plugin loaded ({_powerups.__file__})")
    except Exception as exc:
        print(f"[PLUGMAN] failed to load powerups plugin: {exc}")


# Skip plugins during prefab/dummy runs or when explicitly disabled.
if os.environ.get("BAUTILS_DISABLE_PLUGINS", "0") != "1":
    _load_plugins()
