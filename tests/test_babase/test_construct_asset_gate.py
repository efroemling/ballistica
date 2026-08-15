# Released under the MIT License. See LICENSE for details.
"""Tests for the construct-mode asset-access gate.

The gate complains when a non-builtin asset-package is touched before
construct-mode has finished resolving every package the meta-scan
requires. It exists because that access *happens to work* whenever the
package is bundled into the build at hand, which makes the failure
build-profile-dependent: silently fine for a developer, blank textures
for a player.

Every case here needs the engine binary -- even the "in-process"
ones run their snippet under it -- so all are gated on
``apprun.test_runs_disabled()``. Without that they fail on the
Windows CI runner, which can't assemble a complete build without
WSL (caught by public CI on 2026-07-30).

These tests are mostly about the mechanism staying armed. A gate that
has quietly stopped firing looks exactly like a codebase with no
violations, so the positive controls here matter more than the negative
ones.
"""

import os
import re
import tempfile
import subprocess

import pytest

from batools import apprun


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_python_gate_blocks_non_builtin() -> None:
    """A non-builtin package access pre-hand-off is refused."""
    # Run in-process: the gate is pure Python bookkeeping, so it needs
    # no engine. Fresh interpreter per case so module state is clean.
    code = (
        'import babase._asset_packages as ap\n'
        # Pretend we are still in bring-up.
        'ap._g_construct_complete = False\n'
        'ap._g_construct_apverid = "a-0.babuiltinassets.1"\n'
        'try:\n'
        '    ap.check_asset_package_load("a-0.bacommonassets.1", "s/ok")\n'
        '    print("NOT-BLOCKED")\n'
        'except RuntimeError as exc:\n'
        '    assert "before construct-mode" in str(exc), exc\n'
        '    print("BLOCKED")\n'
    )
    out = _run_python(code)
    assert 'BLOCKED' in out, out


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_python_gate_allows_builtin() -> None:
    """The construct/builtin package stays loadable during bring-up."""
    code = (
        'import babase._asset_packages as ap\n'
        'ap._g_construct_complete = False\n'
        'ap._g_construct_apverid = "a-0.babuiltinassets.1"\n'
        'ap.check_asset_package_load("a-0.babuiltinassets.1", "s/ok")\n'
        'print("ALLOWED")\n'
    )
    out = _run_python(code)
    assert 'ALLOWED' in out, out


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_python_gate_opens_after_handoff() -> None:
    """Once construct-mode completes, any package is fair game."""
    code = (
        'import babase._asset_packages as ap\n'
        'ap._g_construct_complete = True\n'
        'ap.check_asset_package_load("a-0.bacommonassets.1", "s/ok")\n'
        'print("ALLOWED")\n'
    )
    out = _run_python(code)
    assert 'ALLOWED' in out, out


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_langstr_leaf_access_is_gated() -> None:
    """String leaves go through the gate, not just loadable assets.

    Strings resolve via the native language table rather than
    ``FindAssetFile``, so the native asset gate never sees them; this is
    the check that covers them. Guarding it explicitly because the
    wrapper's accessor is generated code -- a regeneration that dropped
    the check would otherwise be invisible.
    """
    code = (
        'import babase._asset_packages as ap\n'
        'from babase._language import LangStrDir\n'
        'ap._g_construct_complete = False\n'
        'ap._g_construct_apverid = "a-0.babuiltinassets.1"\n'
        'd = LangStrDir("a-0.bacommonassets.1", {"actions": {"ok": ()}},\n'
        '               "strings")\n'
        'try:\n'
        '    _ = d.actions.ok\n'
        '    print("NOT-BLOCKED")\n'
        'except RuntimeError as exc:\n'
        '    assert "before construct-mode" in str(exc), exc\n'
        '    print("BLOCKED")\n'
    )
    out = _run_python(code)
    assert 'BLOCKED' in out, out


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_simple_sound_handle_access_is_gated() -> None:
    """babase sound leaves go through the gate like every other leaf.

    ``SimpleSoundHandle`` is what lets pre-construct code (plugin scan,
    account/workspace paths) play a sound through a typed wrapper, so it
    is precisely the tier most likely to be pointed at a package that
    is not up yet. The gate must fire before the native load, not after
    -- a miss here means an asset that goes permanently ``kFailed``.
    """
    code = (
        'import babase._asset_packages as ap\n'
        'from babase._assetref import SimpleSoundHandle\n'
        'ap._g_construct_complete = False\n'
        'ap._g_construct_apverid = "a-0.babuiltinassets.1"\n'
        'try:\n'
        '    SimpleSoundHandle("a-0.baclassicassets.1", "audio/gong").get()\n'
        '    print("NOT-BLOCKED")\n'
        'except RuntimeError as exc:\n'
        '    assert "before construct-mode" in str(exc), exc\n'
        '    print("BLOCKED")\n'
    )
    out = _run_python(code)
    assert 'BLOCKED' in out, out


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_devconsole_appmodes_tab_gated() -> None:
    """The dev-console AppModes tab refuses to run during construct mode.

    It is the one known way to *circumvent* the gate rather than trip it:
    its refresh execs the modules exporting app-modes (wrapper modules
    among them) and can then force-switch into a mode whose packages were
    never acquired. So the guard has to sit before that load, not on the
    switch buttons -- which is what this asserts, by checking the load is
    never kicked off.
    """
    code = (
        'import babase._asset_packages as ap\n'
        'from babase._devconsoletabs import DevConsoleTabAppModes\n'
        'ap._g_construct_complete = False\n'
        'calls = []\n'
        'tab = DevConsoleTabAppModes()\n'
        # Stub the two surfaces refresh() touches so this needs no live
        # dev console: record text, and record any attempt to load.
        'tab.text = lambda *a, **kw: calls.append(("text", a and a[0]))\n'
        'import _babase\n'
        'class _Meta:\n'
        '    def load_exported_classes(self, *a, **kw):\n'
        '        calls.append(("load", None))\n'
        'class _App:\n'
        '    meta = _Meta()\n'
        '_babase.app = _App()\n'
        'tab.refresh()\n'
        'loaded = any(c[0] == "load" for c in calls)\n'
        'texts = [c[1] for c in calls if c[0] == "text"]\n'
        'assert not loaded, "kicked off app-mode load during construct mode"\n'
        'assert any("Unavailable until asset" in t for t in texts), texts\n'
        'print("BLOCKED")\n'
    )
    out = _run_python(code)
    assert 'BLOCKED' in out, out


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_devconsole_appmodes_tab_works_after_handoff() -> None:
    """...and does its normal job once assets are acquired.

    The complement of the test above, so the guard can't be "fixed" into
    gating the tab permanently -- which would look like a pass on the
    blocked-case test alone.
    """
    code = (
        'import babase._asset_packages as ap\n'
        'from babase._devconsoletabs import DevConsoleTabAppModes\n'
        'ap._g_construct_complete = True\n'
        'calls = []\n'
        'tab = DevConsoleTabAppModes()\n'
        'tab.text = lambda *a, **kw: calls.append(("text", a and a[0]))\n'
        'import _babase\n'
        'class _Meta:\n'
        '    def load_exported_classes(self, *a, **kw):\n'
        '        calls.append(("load", None))\n'
        'class _App:\n'
        '    meta = _Meta()\n'
        '_babase.app = _App()\n'
        'tab.refresh()\n'
        'assert any(c[0] == "load" for c in calls), calls\n'
        'print("ALLOWED")\n'
    )
    out = _run_python(code)
    assert 'ALLOWED' in out, out


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_real_app_run_has_no_violations() -> None:
    """A real headless boot reaches hand-off without tripping the gate.

    The regression test for the invariant itself: if someone adds a
    too-early access, this fails. Headless is deliberately the harness --
    it is what CI runs, and the gate is meant to be visible there rather
    than only in a GUI build that happens to bundle more.
    """
    proc = apprun.run_headless_capture(
        purpose='construct-mode asset-gate check',
        env={'BA_LOG_LEVELS': 'ba.lifecycle=DEBUG'},
        timeout=90.0,
        stop_pattern=re.compile(r'Construct-mode asset gate opened'),
    )
    out = proc.stdout.decode(errors='replace')

    # Prove we actually got far enough for the test to mean anything --
    # a boot that died early would trivially log no violations. (Keyed on
    # the gate-opened line rather than construct-mode's hand-off log: the
    # latter sits on ba.assetmanager, which this run does not enable.)
    assert 'Construct-mode asset gate opened' in out, (
        'run never opened the construct-mode asset gate; the'
        f' no-violations assertion below would be vacuous.'
        f' Output:\n{out[-3000:]}'
    )
    assert 'accessed before construct-mode' not in out, out
    assert 'loaded before construct-mode' not in out, out


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_plugins_run_after_construct_handoff() -> None:
    """Plugin code runs only once the asset gate has opened.

    Plugins used to load in the ordinary ``on_app_running`` subsystem
    pass, which happens *before* construct-mode resolves anything -- so
    a plugin touching a non-builtin package tripped the gate through no
    fault of its own. They now load out of construct-mode's hand-off
    instead (``App.on_construct_complete``).

    Asserted two ways because each catches a different regression: the
    in-plugin ``construct_assets_complete()`` reading catches the gate
    being opened late, and the log ordering catches the plugin phase
    being moved back ahead of it.
    """
    apiver = _api_version()

    with tempfile.TemporaryDirectory() as cfgdir:
        _write_test_plugin(cfgdir, apiver)
        proc = apprun.run_headless_capture(
            purpose='plugin construct-mode ordering check',
            config_dir=cfgdir,
            env={'BA_LOG_LEVELS': 'ba.lifecycle=DEBUG'},
            timeout=90.0,
            stop_pattern=re.compile(r'GATETESTPLUG-RAN'),
        )
    out = proc.stdout.decode(errors='replace')

    assert 'GATETESTPLUG-RAN' in out, (
        'test plugin never ran; the ordering assertions below would be'
        f' vacuous. Output:\n{out[-3000:]}'
    )
    assert 'GATETESTPLUG-RAN construct_assets_complete=True' in out, (
        'plugin ran before construct-mode finished resolving'
        f' asset-packages. Output:\n{out[-3000:]}'
    )

    gate_pos = out.find('Construct-mode asset gate opened')
    plug_pos = out.find('GATETESTPLUG-RAN')
    assert gate_pos != -1, out[-3000:]
    assert (
        gate_pos < plug_pos
    ), f'asset gate opened after the plugin ran. Output:\n{out[-3000:]}'


def _write_test_plugin(cfgdir: str, apiver: int) -> None:
    """Drop a marker-logging plugin into *cfgdir*'s mods dir.

    A fresh config dir has no 'Plugins' config entry, and new plugins
    auto-enable by default, so dropping the file in is all it takes to
    get it loaded.
    """
    mods_dir = os.path.join(cfgdir, 'mods')
    os.makedirs(mods_dir, exist_ok=True)
    with open(
        os.path.join(mods_dir, 'gatetestplug.py'), 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(
            '# Released under the MIT License. See LICENSE for details.\n'
            '"""Plugin used by the construct-mode asset-gate tests."""\n'
            '\n'
            'import logging\n'
            'from typing import override\n'
            '\n'
            'import babase\n'
            'from babase._asset_packages import construct_assets_complete\n'
            '\n'
            '\n'
            f'# ba_meta require api {apiver}\n'
            '# ba_meta export babase.Plugin\n'
            'class GateTestPlugin(babase.Plugin):\n'
            '    """Reports whether assets were ready when it was run."""\n'
            '\n'
            '    @override\n'
            '    def on_app_running(self) -> None:\n'
            '        logging.warning(\n'
            "            'GATETESTPLUG-RAN construct_assets_complete=%s',\n"
            '            construct_assets_complete(),\n'
            '        )\n'
        )


def _api_version() -> int:
    """Ask the engine binary what api version plugins must declare.

    Read from the binary rather than hardcoded so this test keeps
    working across api bumps (a mismatched ``ba_meta require api`` line
    makes the meta-scan skip the module entirely, which would show up
    here as a plugin that simply never ran).
    """
    out = _run_python(
        'import babase\n'
        'print("APIVER", babase.app.env.api_version)\n'
        'print("ALLOWED")\n'
    )
    match = re.search(r'APIVER (\d+)', out)
    assert match is not None, out
    return int(match.group(1))


def _run_python(code: str) -> str:
    """Run a snippet under the engine binary and return its output.

    Mirrors :func:`batools.apprun.python_command` but captures output and
    tolerates a nonzero exit (a gate violation is an exception by
    design), so the assertions can inspect what happened.
    """
    binpath = apprun.acquire_binary(purpose='construct-mode asset-gate test')
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
    if 'NOT-BLOCKED' not in out and not ('BLOCKED' in out or 'ALLOWED' in out):
        pytest.fail(
            f'snippet produced no verdict (exit {result.returncode}):\n'
            f'stdout:\n{out}\nstderr:\n{err}'
        )
    return out + err
