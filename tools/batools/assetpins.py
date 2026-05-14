# Released under the MIT License. See LICENSE for details.
#
"""Asset-package pin inspection / upgrade.

``assetpins`` is the single owner of "what asset-package version
are we pinned to" — it discovers wrappers in the source tree
(currently just the hardcoded C++ wrapper in ``base.h`` /
``assets.cc``; Python wrappers will be added via ``ba_meta``
discovery in a follow-up), reads their embedded apverids, and
either lists them or refreshes them against the cloud.

Per the global build-system design, this is the only build-flow
step that talks to the cloud and the only one that mutates
checked-in source as part of normal use (other than ``make
update``, which is purely about regenerating bookkeeping derived
from on-disk source state).
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from pathlib import Path


def do_list(projroot: Path) -> None:
    """Print the list of detected pins + state."""
    pins = _discover_pins(projroot)
    if not pins:
        print('No asset-package wrappers detected.')
        return
    for pin in pins:
        marker = ''
        if pin.wrapper_apverid != pin.projectconfig_apverid:
            marker = (
                f'  {Clr.RED}(wrapper / projectconfig disagree —'
                f' run assetpins upgrade){Clr.RST}'
            )
        print(
            f'  {Clr.BLD}{pin.kind}{Clr.RST}'
            f'  apverid={Clr.CYN}{pin.wrapper_apverid}{Clr.RST}'
            f'{marker}'
        )


def do_upgrade(projroot: Path) -> None:
    """Re-resolve pins, refetch manifests, rewrite wrappers.

    Current implementation upgrades everything in lockstep (which
    today is just the single C++ wrapper). When Python wrappers
    land, this will iterate through all discovered wrappers.
    """
    # The current model uses ``projectconfig.json``'s ``"assets"``
    # field as the single pin source. ``asset_bundle_resolve`` reads
    # it; ``asset_bundle_build`` fetches the manifest + blobs for
    # the resolved version. Both variants get refreshed because
    # ``make cmake-build`` may pull one, ``make cmake-server-build``
    # the other.
    _run_pcommand(
        projroot, 'asset_bundle_resolve', '.cache/asset_bundle/resolved'
    )
    for variant in ('gui', 'headless'):
        _run_pcommand(
            projroot,
            'asset_bundle_build',
            '.cache/asset_bundle/resolved',
            variant,
        )

    # Refresh the C++ wrapper splice now that the manifest is current.
    from batools.builtinassetids import generate

    changed = generate(projroot, check=False)
    if changed:
        print(f'{Clr.GRN}Wrapper updated.{Clr.RST}')
    else:
        print(f'{Clr.BLU}Wrappers already up to date.{Clr.RST}')


# --------------------------------------------------------------------
# Internal: pin discovery
# --------------------------------------------------------------------


class _Pin:
    """One discovered wrapper / pin."""

    def __init__(
        self,
        kind: str,
        wrapper_apverid: str,
        projectconfig_apverid: str | None,
    ) -> None:
        self.kind = kind
        self.wrapper_apverid = wrapper_apverid
        self.projectconfig_apverid = projectconfig_apverid


def _discover_pins(projroot: Path) -> list[_Pin]:
    """Find all asset-package wrappers in the source tree."""
    from efrotools.project import getprojectconfig

    pins: list[_Pin] = []

    # The C++ wrapper sits at a fixed location (the autogen
    # section in base.h); read its embedded apverid.
    cpp_apverid = _read_cpp_wrapper_apverid(projroot)
    if cpp_apverid is not None:
        projectconfig_apverid = getprojectconfig(projroot).get('assets')
        if not isinstance(projectconfig_apverid, str):
            projectconfig_apverid = None
        pins.append(
            _Pin(
                kind='cpp:builtin-assets',
                wrapper_apverid=cpp_apverid,
                projectconfig_apverid=projectconfig_apverid,
            )
        )

    # Python wrappers (via ba_meta require asset-package <id>) will
    # be discovered here once that scanner extension lands. Stage 2
    # of the asset-packages initiative covers this; for now there
    # are none in the source tree.

    return pins


def _read_cpp_wrapper_apverid(projroot: Path) -> str | None:
    """Pull ``kBuiltinAssetsApverid`` out of base.h's autogen section."""
    import re

    base_h = projroot / 'src/ballistica/base/base.h'
    if not base_h.is_file():
        return None
    text = base_h.read_text()
    match = re.search(
        r'inline\s+constexpr\s+const\s+char\*\s+kBuiltinAssetsApverid\s*=\s*'
        r'"([^"]*)";',
        text,
    )
    if match is None:
        raise CleanError(
            f'Could not find kBuiltinAssetsApverid in {base_h}; '
            'autogen section missing or malformed?'
        )
    return match.group(1)


# --------------------------------------------------------------------
# Internal: pcommand invocation
# --------------------------------------------------------------------


def _run_pcommand(projroot: Path, name: str, *args: str) -> None:
    """Subprocess-invoke a sibling pcommand."""
    cmd = [str(projroot / 'tools' / 'pcommand'), name, *args]
    subprocess.run(cmd, cwd=projroot, check=True)
