# Released under the MIT License. See LICENSE for details.
#
"""Apply small text patches to packages installed in a venv.

Some Python projects need targeted modifications to third-party
packages installed via ``pip`` — bug fixes pending upstream review,
small project-specific customizations, or workarounds for
upstream-rejected behaviour. This module provides a simple,
declarative way to manage such patches.

Patches are described in a JSON file (commonly
``pconfig/venv_patches.json``) using the :class:`VenvPatches` schema
below. Each entry is a literal-string find-and-replace, validated
by an exact occurrence count so silent drift across upstream
versions surfaces immediately as a hard error.

Two operations are supported:

* :func:`apply_patches` — typically called once at the end of venv
  construction (after ``pip install``). Replaces ``srctxt`` with
  ``replacetxt`` in each target file.

* :func:`check_patches` — verifies all patches are present in the
  current venv. Designed to be called at app startup so a venv that
  was assembled without the patches (e.g. an installer that ran
  with ``allow_mismatches=True`` and skipped a broken patch) gets
  flagged via a CRITICAL log entry.

The string-search approach (rather than SHA256 of full files or
unified-diff matching) is intentional: small targeted patches stay
robust as upstream files evolve around them, as long as the
specific lines we touch don't change.
"""

from __future__ import annotations

import logging
import sysconfig
from pathlib import Path
from dataclasses import dataclass, field
from typing import Annotated, TYPE_CHECKING

from efro.dataclassio import ioprepped, IOAttrs, dataclass_from_json
from efro.error import CleanError

if TYPE_CHECKING:
    pass


_log = logging.getLogger(__name__)


@ioprepped
@dataclass
class VenvPatch:
    """A single string-replacement patch against a venv site-packages file."""

    #: Short human-readable identifier. Used in log/error messages so
    #: a failure points at the right patch.
    description: Annotated[str, IOAttrs('description')]

    #: Path to the target file relative to ``site-packages`` (e.g.
    #: ``google/cloud/firestore_v1/watch.py``).
    path: Annotated[str, IOAttrs('path')]

    #: Exact text to find. Must appear ``count`` times in the target.
    srctxt: Annotated[str, IOAttrs('srctxt')]

    #: Text to replace ``srctxt`` with.
    replacetxt: Annotated[str, IOAttrs('replacetxt')]

    #: Number of expected occurrences of ``srctxt``. Defaults to 1.
    #: When ``> 1``, every occurrence is replaced (so all become
    #: ``replacetxt``). To replace different occurrences with
    #: different text, split into separate patch entries with
    #: distinguishing surrounding context in ``srctxt``.
    count: Annotated[int, IOAttrs('count', soft_default=1)] = 1


@ioprepped
@dataclass
class VenvPatches:
    """Top-level container for a list of venv patches.

    This is the schema for ``pconfig/venv_patches.json``.
    """

    patches: Annotated[list[VenvPatch], IOAttrs('patches')] = field(
        default_factory=list
    )


def _validate(patches: list[VenvPatch]) -> None:
    """Validate inter-patch invariants.

    Currently checks that ``srctxt`` is non-empty and does not appear
    inside its own ``replacetxt`` (which would cause re-application
    on every run to grow indefinitely). Also disallows ``count <= 0``.
    """
    for p in patches:
        if not p.srctxt:
            raise CleanError(
                f'venv-patch {p.description!r}: srctxt must be non-empty.'
            )
        if p.count <= 0:
            raise CleanError(
                f'venv-patch {p.description!r}:'
                f' count must be positive (got {p.count}).'
            )
        if p.srctxt in p.replacetxt:
            raise CleanError(
                f'venv-patch {p.description!r}: srctxt appears'
                ' inside replacetxt; this would cause re-application'
                ' to grow without bound. Add disambiguating context'
                ' to srctxt or restructure replacetxt.'
            )


def _site_packages() -> Path:
    """Return the site-packages dir of the current Python interpreter."""
    purelib = sysconfig.get_paths().get('purelib')
    if not purelib:
        raise CleanError(
            'Could not determine site-packages location from sysconfig.'
        )
    return Path(purelib)


def load_patches_from_file(path: str | Path) -> VenvPatches:
    """Load and validate a :class:`VenvPatches` JSON file."""
    src = Path(path).read_text(encoding='utf-8')
    out: VenvPatches = dataclass_from_json(VenvPatches, src)
    _validate(out.patches)
    return out


def apply_patches(
    patches: list[VenvPatch],
    *,
    site_packages: Path | None = None,
    allow_mismatches: bool = False,
) -> int:
    """Apply each patch in order to the current venv's site-packages.

    Args:
      patches: Patches to apply.
      site_packages: Optional override. If ``None``, uses the
        current interpreter's ``site-packages`` directory.
      allow_mismatches: If ``True``, mismatched or missing patches
        are logged at ERROR level and skipped instead of raising.
        Use this during installer flows on production nodes where
        a partial venv is preferable to a broken boot. The default
        ``False`` is the right choice for dev ``make env`` flows.

    Returns the number of patches that were either successfully
    applied or already present (i.e. the number that ended in the
    desired state). Errors/skips are not counted.
    """
    if site_packages is None:
        site_packages = _site_packages()
    succeeded = 0
    for p in patches:
        target = site_packages / p.path
        try:
            _apply_one(target, p)
            succeeded += 1
        except CleanError as exc:
            if allow_mismatches:
                _log.error('%s', exc)
            else:
                raise
    return succeeded


def _apply_one(target: Path, p: VenvPatch) -> None:
    if not target.exists():
        raise CleanError(
            f'venv-patch for {p.path!r}: target file does not exist.'
            ' Either remove this patch (if no longer needed) or'
            ' update path to match the current upstream layout.'
        )
    text = target.read_text(encoding='utf-8')
    src_count = text.count(p.srctxt)
    repl_count = text.count(p.replacetxt)

    # Already-applied detection: replacetxt appears the expected
    # number of times AND srctxt is gone. Idempotent re-runs are a
    # no-op in this case.
    if src_count == 0 and repl_count >= p.count:
        _log.debug('venv-patch already applied in %s; skipping.', p.path)
        return

    if src_count != p.count:
        raise CleanError(
            f'venv-patch for {p.path!r}: expected {p.count}'
            f' occurrence(s) of srctxt, found {src_count}.'
            ' Upstream may have changed; update or remove the patch.'
        )

    new_text = text.replace(p.srctxt, p.replacetxt)
    target.write_text(new_text, encoding='utf-8')
    _log.info('Applied venv-patch in %s.', p.path)


def find_patch_mismatches(
    patches: list[VenvPatch],
    *,
    site_packages: Path | None = None,
) -> list[str]:
    """Return the paths of patches not fully applied.

    Empty list means everything is in the desired state. No
    logging — callers decide severity and message format.
    """
    if site_packages is None:
        site_packages = _site_packages()
    out: list[str] = []
    for p in patches:
        target = site_packages / p.path
        if not target.exists():
            out.append(p.path)
            continue
        text = target.read_text(encoding='utf-8')
        if text.count(p.srctxt) != 0 or text.count(p.replacetxt) < p.count:
            out.append(p.path)
    return out


def check_patches(
    patches: list[VenvPatch],
    *,
    site_packages: Path | None = None,
) -> int:
    """Verify that all patches are present in the current venv.

    Logs CRITICAL for each mismatched patch. Returns the count;
    callers that want to abort on any mismatch can check the return
    value. Use :func:`find_patch_mismatches` directly if you need
    to control logging severity or message format.
    """
    paths = find_patch_mismatches(patches, site_packages=site_packages)
    for path in paths:
        _log.critical(
            'venv-patch not applied in %s. The patch may have failed'
            ' to apply during venv setup, or upstream may have'
            ' changed underneath us.',
            path,
        )
    return len(paths)
