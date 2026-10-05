# Boot Config Availability

**Description:** When config.json / babase.app.config becomes readable during engine startup relative to StartApp and SDL init — and the three traps around it.

`config.json` is read **two phases before** SDL init in both build
modes, so anything needing a stored value before SDL/graphics come up
can read the regular app config. There is no "too early for the
config" window.

Ordering (verified 2026-08-07):

1. `baenv.configure()` reads `config.json` →
   `EnvConfig.initial_app_config` (`baenv.py`). Monolithic:
   `MonolithicModeBaEnvConfigure()` from `MonolithicMain`
   (`shared/ballistica.cc`). Modular: `configure()` before
   `import babase` in `_modular_main` (`baenv.py`).
2. `_babase` module exec → `g_core->ApplyBaEnvConfig()` (`base.cc` →
   `core.cc`) pulls the dict into `initial_app_config_`;
   `ImportPythonObjs()` imports `babase`, whose module-level
   `app = App()` does `AppConfig(_babase.get_initial_app_config())`.
3. `StartApp()` → `app_adapter->OnMainThreadStartApp()` →
   **`SDL_Init`** (only call site, `app_adapter_sdl.cc`).
4. apply-app-config is pushed to the logic thread — *after* SDL init.

Traps:

- **`g_core->initial_app_config_` is null by SDL-init time** —
  `HandOverInitialAppConfig()` transfers the ref away on the first
  `get_initial_app_config()` call (step 2).
- **`StartApp()` releases the GIL** for the whole subsystem-start
  sequence, so `OnMainThreadStartApp()` implementations run GIL-free;
  reading Python config there needs a `Python::ScopedInterpreterLock`
  (see `BasePython::OnMainThreadStartApp`). Cleaner: snapshot the value
  into a plain C++ member in `ApplyBaEnvConfig()` — the
  `app_config_enable_xinput_` pattern.
- **Values consumed at step 3 are restart-required** —
  apply-app-config (step 4) runs later.
