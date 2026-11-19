# Released under the MIT License. See LICENSE for details.
#
"""Tests for the asset-bundle assembled-info sidecar and its checks."""

import json
from pathlib import Path

import pytest

from efro.error import CleanError

from batools import _assetbundlebuild, _bundlestage
from batools.assetbundleprofiles import (
    BundleAssembledInfo,
    read_assembled_info,
    write_assembled_info,
)

_PIN = 'a-0.babuiltinassets.261102a'


def _make_project(root: Path, pin: str = _PIN) -> str:
    """A minimal project dir with a projectconfig and a bundle dir."""
    (root / 'pconfig').mkdir(parents=True)
    (root / 'pconfig/projectconfig.json').write_text(
        json.dumps({'assets': pin}), encoding='utf-8'
    )
    (root / '.cache/asset_bundle/gui-minimal').mkdir(parents=True)
    return str(root)


def _info(pin: str = _PIN, fleet: str | None = 'prod') -> BundleAssembledInfo:
    return BundleAssembledInfo(
        builtin_apverid=pin, apvernums=['1008'], fleet=fleet
    )


def test_sidecar_roundtrip(tmp_path: Path) -> None:
    """What we write is what we read back; absent means None."""
    proj = _make_project(tmp_path)
    assert read_assembled_info(proj, 'gui-minimal') is None
    write_assembled_info(proj, 'gui-minimal', _info(fleet=None))
    info = read_assembled_info(proj, 'gui-minimal')
    assert info is not None
    assert info.builtin_apverid == _PIN
    assert info.apvernums == ['1008']
    assert info.fleet is None


def test_stage_check_matching_passes(tmp_path: Path) -> None:
    """A bundle assembled for the current pin passes staging."""
    proj = _make_project(tmp_path)
    write_assembled_info(proj, 'gui-minimal', _info())
    _bundlestage.verify_bundle_assembled_for_project(proj, 'gui-minimal')


def test_stage_check_stale_pin_names_both(tmp_path: Path) -> None:
    """A bundle assembled for an older pin fails, naming both pins."""
    proj = _make_project(tmp_path)
    old = 'a-0.babuiltinassets.261008'
    write_assembled_info(proj, 'gui-minimal', _info(pin=old))
    with pytest.raises(CleanError) as excinfo:
        _bundlestage.verify_bundle_assembled_for_project(proj, 'gui-minimal')
    msg = str(excinfo.value)
    assert old in msg and _PIN in msg
    assert 'asset_bundle_build gui-minimal' in msg


def test_stage_check_no_sidecar_skips(tmp_path: Path) -> None:
    """Bundles from before the sidecar existed aren't judged by it."""
    proj = _make_project(tmp_path)
    _bundlestage.verify_bundle_assembled_for_project(proj, 'gui-minimal')


def test_store_bundle_from_dev_fleet_refused(tmp_path: Path) -> None:
    """A store bundle assembled against a non-prod fleet can't ship."""
    proj = _make_project(tmp_path)
    (tmp_path / '.cache/asset_bundle/store-desktop').mkdir(parents=True)
    write_assembled_info(proj, 'store-desktop', _info(fleet='dev'))
    with pytest.MonkeyPatch.context() as mp:
        # The store check also scans bundled code; keep it to our set.
        mp.setattr(
            'batools.assetbundleprofiles.current_scanned_apvernums',
            lambda _projroot: ['1008'],
        )
        with pytest.raises(CleanError, match='dev fleet'):
            _bundlestage.verify_bundle_assembled_for_project(
                proj, 'store-desktop'
            )


def test_store_bundle_missing_required_package(tmp_path: Path) -> None:
    """Code requiring a package the store bundle lacks fails clearly."""
    proj = _make_project(tmp_path)
    (tmp_path / '.cache/asset_bundle/store-desktop').mkdir(parents=True)
    write_assembled_info(proj, 'store-desktop', _info())
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            'batools.assetbundleprofiles.current_scanned_apvernums',
            lambda _projroot: ['1008', '1234'],
        )
        with pytest.raises(CleanError, match='1234'):
            _bundlestage.verify_bundle_assembled_for_project(
                proj, 'store-desktop'
            )


def _write_satisfying_manifest(proj: str) -> tuple[str, dict[str, set[str]]]:
    """A bundle manifest that satisfies a trivial expected-coords set."""
    path = f'{proj}/.cache/asset_bundle/gui-minimal/manifest.json'
    coords = {'1008': {'language/eng'}}
    Path(path).write_text(
        json.dumps(
            {
                'asset_package_versions': {
                    '1008': {'flavor_manifests': {'language/eng': 'h'}}
                }
            }
        ),
        encoding='utf-8',
    )
    return path, coords


def test_skip_backfills_sidecar_without_fleet(tmp_path: Path) -> None:
    """An up-to-date bundle with no sidecar is reused and backfilled."""
    proj = _make_project(tmp_path)
    path, coords = _write_satisfying_manifest(proj)
    assert _assetbundlebuild.can_skip_assembly(
        proj, 'gui-minimal', path, coords, _info()
    )
    info = read_assembled_info(proj, 'gui-minimal')
    assert info is not None and info.fleet is None


def test_skip_cross_fleet_rules(tmp_path: Path) -> None:
    """Only non-prod content going into a prod build forces reassembly."""
    proj = _make_project(tmp_path)
    path, coords = _write_satisfying_manifest(proj)

    # A prod bundle may serve non-prod builds (no nodes needed there).
    write_assembled_info(proj, 'gui-minimal', _info(fleet='prod'))
    assert _assetbundlebuild.can_skip_assembly(
        proj, 'gui-minimal', path, coords, _info(fleet='dev')
    )

    # A dev bundle may not serve a prod build...
    write_assembled_info(proj, 'gui-minimal', _info(fleet='dev'))
    assert not _assetbundlebuild.can_skip_assembly(
        proj, 'gui-minimal', path, coords, _info(fleet='prod')
    )
    # ...but may serve another non-prod one.
    assert _assetbundlebuild.can_skip_assembly(
        proj, 'gui-minimal', path, coords, _info(fleet='test_fromini')
    )
