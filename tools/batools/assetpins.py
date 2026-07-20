# Released under the MIT License. See LICENSE for details.
#
"""Asset-package pin inspection / update.

``assetpins`` is the single owner of "what asset-package version
are we pinned to" across the source tree. It discovers pins in
two places:

- the ``"assets"`` entry in ``pconfig/projectconfig.json``
  (the construct-mode/bootloader pin),
- per-wrapper ``# ba_meta require asset-package <id>`` lines
  inside Python wrapper modules (server-generated; see the
  ``GET /api/v1/admin/asset-package-versions/{id}/python-wrapper``
  REST endpoint).

Per the global build-system design, this is the only build-flow
step that talks to the cloud and the only one that mutates
checked-in source as part of normal use (other than ``make
update``, which is purely about regenerating bookkeeping derived
from on-disk source state).

Apverid schema (from the third segment of ``<account>.<name>.<seg>``):

- ``<seg>`` starts with a digit → **PROD** (allowed anywhere).
- ``<seg>`` matches ``dev(\\d.*)?`` → **DEV** (allowed in
  private/internal-CI only; blocked from public).
- ``<seg>`` matches ``test\\d.*`` → **TEST** (allowed in
  private/internal-CI only; blocked from public).

Bare ``dev`` (no trailing digit) is an unresolved pseudo-id
meaning "give me the latest dev snapshot". The build refuses to
consume it; ``assetpins update`` resolves it via master and
writes the resolved ``devN`` form back to the pin's source file.

The ``update`` operation takes a TARGET and a VERSION:

- TARGET: ``all``, an asset-package name (e.g. ``bastdassets``)
  matching any pin of that package across accounts, or a file
  path matching exactly one pin.
- VERSION: ``latest`` (current track, newest version),
  ``prod`` / ``test`` / ``dev`` (switch to or stay on that track,
  newest version), or a full third-segment like ``260513a``
  (prod), ``test260512a``, or ``dev260513a`` (exact pin;
  account+package come from the pin's own apverid).

Each pin is independent — moving one pin does not move any
other. Track-switching is an explicit, deliberate operation.
"""

# This module is the single cohesive home for asset-package pin
# inspection/update; it has grown past the default module-size cap but
# splitting it would scatter tightly-related logic.
# pylint: disable=too-many-lines

import re
import enum
import subprocess
import concurrent.futures
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr
from batools.version import get_current_api_version

if TYPE_CHECKING:
    from pathlib import Path

    from bacommon.restapi.v1.accounts import AccountResponse


# Total-width policy for the `assetpins` table output. We
# compute a "natural" width (everything visible, no clipping)
# from the data, then clamp it against an upper bound from the
# environment: terminal width when on a TTY (no narrower than
# ``MIN_TTY_COLS``); a stable fallback otherwise (so logs and
# tests stay deterministic). If the upper bound is below
# natural, the file column clips with leading ``...``.
MIN_TTY_COLS = 60
FALLBACK_COLS = 80


def _max_table_width() -> int:
    """Upper bound on total table width for the current env."""
    import sys
    import shutil

    if not sys.stdout.isatty():
        return FALLBACK_COLS
    return max(shutil.get_terminal_size().columns, MIN_TTY_COLS)


class PinType(enum.Enum):
    """Classification of an apverid by its third-segment shape."""

    PROD = 'prod'
    DEV = 'dev'
    TEST = 'test'


# Anchored regexes on the third segment of an apverid.
_RE_DEV = re.compile(r'^dev(\d.*)?$')
_RE_TEST = re.compile(r'^test\d.*$')


def classify_apverid(apverid: str) -> PinType:
    """Classify an apverid string by its third segment.

    Raises ``CleanError`` if the apverid is structurally
    malformed (wrong segment count, unrecognized third-segment
    shape).
    """
    parts = apverid.split('.')
    if len(parts) != 3:
        raise CleanError(
            f'Malformed apverid {apverid!r}: expected three'
            f' dot-separated segments, got {len(parts)}.'
        )
    seg = parts[2]
    if not seg:
        raise CleanError(
            f'Malformed apverid {apverid!r}: empty version segment.'
        )
    first = seg[0]
    if first.isdigit():
        return PinType.PROD
    if _RE_DEV.fullmatch(seg) is not None:
        return PinType.DEV
    if _RE_TEST.fullmatch(seg) is not None:
        return PinType.TEST
    raise CleanError(
        f'Malformed apverid {apverid!r}: third segment {seg!r}'
        f' does not match prod/dev/test shape.'
    )


def is_unresolved_dev(apverid: str) -> bool:
    """Return True if the apverid is a bare ``<account>.<name>.dev``.

    Bare-dev is a request to "use the latest dev snapshot" and
    must be resolved by ``assetpins update`` before any build
    step can consume it.
    """
    parts = apverid.split('.')
    return len(parts) == 3 and parts[2] == 'dev'


@dataclass
class Pin:
    """One discovered asset-package pin."""

    #: Pin-kind identifier; one of ``projectconfig`` or ``wrapper``.
    kind: str
    #: File the pin lives in, relative to projroot.
    file_path: Path
    #: Current apverid string.
    apverid: str
    pin_type: PinType
    #: ``<account>`` segment from the apverid (e.g. ``a-0``).
    account: str
    #: ``<name>`` segment from the apverid (e.g. ``bastdassets``).
    package: str
    #: For ``wrapper`` pins, which featureset's loader API the
    #: wrapper uses (``bascenev1`` or ``bauiv1``). None for
    #: projectconfig pins.
    wrapper_type: str | None = None
    #: Filled by ``do_list`` (master roundtrip); None if not
    #: queried.
    latest_available: str | None = None
    #: Account tag (e.g. ``efro``) resolved from ``account`` by
    #: ``do_list``. None if the account no longer exists (deleted) or
    #: the lookup failed — rendered as the raw account id in red.
    account_tag: str | None = None


# --------------------------------------------------------------------
# Public ops
# --------------------------------------------------------------------


def do_list(projroot: Path) -> None:
    """Print discovered pins + whether master has newer versions."""
    pins = _discover_pins(projroot)
    if not pins:
        print('No asset-package pins detected.')
        _print_help_pointer()
        return

    # One master roundtrip per *unique* (account, package, track) to
    # find the newest version on each track. Multiple pins commonly
    # reference the same package (e.g. babuiltinassets has a
    # projectconfig pin plus per-feature-set wrapper pins), and for the
    # dev track a resolve has a *write* side-effect on master: it
    # auto-creates/updates the dev version. Resolving the same package
    # concurrently would therefore fire redundant racing writes into a
    # non-transactional read-modify-write on master — exactly how stale
    # duplicate dev versions used to accumulate. So dedupe to one lookup
    # per unique target and share the result across its pins. The unique
    # lookups are independent I/O-bound calls (each shells out to its
    # own bacloud subprocess), so run them in a bounded thread pool —
    # modders may reference many asset-packages and serial lookups would
    # scale linearly. ``map`` returns errors in input order, so output
    # stays deterministic regardless of completion order.
    unique_targets: dict[tuple[str, str, PinType], list[Pin]] = {}
    for pin in pins:
        unique_targets.setdefault(
            (pin.account, pin.package, pin.pin_type), []
        ).append(pin)

    def _lookup(item: tuple[tuple[str, str, PinType], list[Pin]]) -> str | None:
        (_account, _package, track), group = item
        try:
            latest = _query_latest_for_track(projroot, group[0], track)
            for pin in group:
                pin.latest_available = latest
            return None
        except Exception as exc:
            for pin in group:
                pin.latest_available = None
            return f'  {group[0].file_path}: lookup failed: {exc}'

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(len(unique_targets), 16)
    ) as executor:
        errors = list(executor.map(_lookup, unique_targets.items()))

    for error in errors:
        if error is not None:
            print(error)

    # Resolve account ids -> display tags (e.g. ``a-0`` -> ``efro``).
    # Dedupe by account (pins frequently share one) and resolve the
    # unique set in parallel, same as the version lookups above.
    accounts = sorted({pin.account for pin in pins})

    def _tag_lookup(account: str) -> tuple[str, str | None, str | None]:
        try:
            return (account, _query_account_tag(projroot, account), None)
        except Exception as exc:
            return (
                account,
                None,
                f'  account {account}: tag lookup failed: {exc}',
            )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(len(accounts), 16)
    ) as executor:
        tag_results = list(executor.map(_tag_lookup, accounts))

    account_tags: dict[str, str | None] = {}
    for account, tag, tag_error in tag_results:
        account_tags[account] = tag
        if tag_error is not None:
            print(tag_error)
    for pin in pins:
        pin.account_tag = account_tags.get(pin.account)

    _print_pin_table(pins)
    _print_help_pointer()


def _account_cell(pin: Pin) -> tuple[str, str | None]:
    """Return ``(text, color)`` for a pin's ``account`` column.

    The resolved account tag (e.g. ``efro``) in normal color, or — if
    the account couldn't be resolved to a tag (deleted, or the lookup
    failed) — the raw account id (e.g. ``a-0``) in red.
    """
    if pin.account_tag is not None:
        return (pin.account_tag, None)
    return (pin.account, Clr.RED)


def _print_pin_table(pins: list[Pin]) -> None:
    """Render the discovered-pins table within the column budget."""
    # pylint: disable=too-many-locals
    headers = ('file', 'account', 'package', 'version', 'status')
    rows = [
        (
            str(pin.file_path),
            *_account_cell(pin),
            pin.package,
            _format_pin_label(pin),
            _pin_color(pin),
            _format_pin_status(pin),
        )
        for pin in pins
    ]

    # Non-file columns always size to fit their content.
    account_w = max(len(headers[1]), *(len(r[1]) for r in rows))
    pkg_w = max(len(headers[2]), *(len(r[3]) for r in rows))
    pin_w = max(len(headers[3]), *(len(r[4]) for r in rows))
    status_w = max(len(headers[4]), *(len(r[6]) for r in rows))
    # 4 inter-column gaps of 2 spaces each = 8.
    fixed_w = account_w + pkg_w + pin_w + status_w + 8

    # Natural file-column width = enough to show every path
    # unclipped. We cap the total table width at the smaller of
    # (natural total, env upper bound) — never wider than needed,
    # never wider than the terminal. If the env bound is below
    # natural, the file column clips with leading ``...``.
    natural_file_w = max(len(headers[0]), *(len(r[0]) for r in rows))
    natural_total = natural_file_w + fixed_w
    total_w = min(natural_total, _max_table_width())
    file_w = max(len(headers[0]), total_w - fixed_w)

    sep = '-' * total_w

    print(f'{Clr.BLD}{Clr.SBLK}Asset Pins{Clr.RST}')
    print(f'{Clr.SBLK}{sep}{Clr.RST}')
    # Trailing column intentionally not padded — keeps output
    # free of trailing whitespace. Color codes are wrapped
    # around the fully-formatted line so the ``:<{width}}``
    # padding stays based on visible-text length.
    header_line = (
        f'{headers[0]:<{file_w}}  '
        f'{headers[1]:<{account_w}}  '
        f'{headers[2]:<{pkg_w}}  '
        f'{headers[3]:<{pin_w}}  '
        f'{headers[4]}'
    )
    print(f'{Clr.SBLK}{header_line}{Clr.RST}')
    for (
        file_path,
        account_text,
        account_clr,
        package,
        pin_label,
        pin_clr,
        status,
    ) in rows:
        # Pad each cell to width as visible text *first*, then
        # wrap with color codes so column alignment is based on
        # visible width (ANSI codes have zero printable width
        # but the formatter doesn't know that).
        padded_account = f'{account_text:<{account_w}}'
        colored_account = (
            f'{account_clr}{padded_account}{Clr.RST}'
            if account_clr
            else padded_account
        )
        padded_pin = f'{pin_label:<{pin_w}}'
        colored_pin = (
            f'{pin_clr}{padded_pin}{Clr.RST}' if pin_clr else padded_pin
        )
        status_clr = _status_color(status)
        colored_status = (
            f'{status_clr}{status}{Clr.RST}' if status_clr else status
        )
        padded_package = f'{package:<{pkg_w}}'
        print(
            f'{_clip_left(file_path, file_w):<{file_w}}  '
            f'{colored_account}  '
            f'{Clr.BLD}{padded_package}{Clr.RST}  '
            f'{colored_pin}  '
            f'{colored_status}'
        )
    print(f'{Clr.SBLK}{sep}{Clr.RST}')


def _format_pin_label(pin: Pin) -> str:
    """Return the human-readable label form.

    The version segment as-is (``260709`` / ``test260709`` /
    ``dev260709``); the track is additionally conveyed by color in
    the rendered table. (Dev pins used to display as bare ``dev``,
    but dev version ids are first-class in source pins now, so
    hiding the concrete segment just made the table show less than
    the pin files do.)
    """
    parts = pin.apverid.split('.')
    return parts[2] if len(parts) == 3 else ''


def _pin_color(pin: Pin) -> str:
    """Return the ANSI color sequence for a pin's version label.

    All version labels render bold; track is conveyed by hue.
    """
    from typing import assert_never

    match pin.pin_type:
        case PinType.PROD:
            return f'{Clr.BLD}{Clr.SGRN}'
        case PinType.DEV:
            return f'{Clr.BLD}{Clr.SYLW}'
        case PinType.TEST:
            return f'{Clr.BLD}{Clr.SMAG}'
        case _:
            assert_never(pin.pin_type)


def _format_pin_status(pin: Pin) -> str:
    if pin.latest_available is None or pin.latest_available == pin.apverid:
        return 'up-to-date'
    return 'UPDATE-AVAILABLE'


def _status_color(status: str) -> str:
    """Return the ANSI color for a status label, or ``''``."""
    if status == 'UPDATE-AVAILABLE':
        return f'{Clr.BLD}{Clr.CYN}'
    return ''


def _clip_left(text: str, width: int) -> str:
    """Truncate from the left with ``...`` if longer than ``width``."""
    if len(text) <= width:
        return text
    if width <= 3:
        return text[-width:]
    return '...' + text[-(width - 3) :]


def _print_help_pointer() -> None:
    print(
        f'{Clr.SBLK}For pin-wrangling examples, run:'
        f' `make assetpins-help`.{Clr.RST}'
    )


def do_update(
    projroot: Path,
    target_str: str,
    version_str: str,
    force: bool = False,
) -> None:
    """Update one or more pins to a chosen version.

    ``target_str``: ``all``, an asset-package name (e.g.
    ``bastdassets``), or a file path matching exactly one pin.

    ``version_str``: ``latest`` (track-preserving), ``prod`` /
    ``test`` / ``dev`` (track-switching), a full third segment
    (e.g. ``260513a``, ``dev260513a``, ``test260512a``), or a full
    ``<account-or-tag>.<package>.<version>`` spec to *retarget* the
    pin to a different asset-package (e.g.
    ``efro.mynewassets.test260518``).

    ``force``: re-fetch and rewrite wrapper pins even when the resolved
    version is unchanged. Use after a server-side wrapper *format*
    change (which moves no pin) to regenerate every wrapper at its
    current pinned version. Has no effect on the projectconfig pin
    (there's nothing to regenerate — only the apverid string).
    """
    pins = _discover_pins(projroot)
    if not pins:
        raise CleanError('No asset-package pins detected.')

    matched = _match_target(pins, target_str)

    # Multiple matched pins often reference the same package (e.g.
    # babuiltinassets' projectconfig + wrapper pins all resolve to the
    # same version). Resolving once per pin would fire redundant master
    # roundtrips — and for the dev track each is a write that
    # delete-alls-and-recreates the dev version — so memoize the resolve
    # and reuse the resolved apverid. The key includes the pin's current
    # track because ``version_str='latest'`` is track-preserving (it
    # resolves against ``pin.pin_type``); other version specs ignore the
    # current track, so including it is just harmlessly conservative.
    resolve_cache: dict[tuple[str, str, PinType, str], str] = {}

    def _resolve_for(pin: Pin) -> str:
        key = (pin.account, pin.package, pin.pin_type, version_str)
        cached = resolve_cache.get(key)
        if cached is None:
            cached = _compute_new_apverid(projroot, pin, version_str)
            resolve_cache[key] = cached
        return cached

    # ---- Phase 1: resolve + compute all writes (NO disk mutation). ----
    #
    # Everything we intend to write is computed into ``staged`` first and
    # applied only once every resolve / cloud fetch / splice computation
    # has succeeded. A failure partway through (server unreachable, a bad
    # wrapper, etc.) raises before any file is touched, so the tree never
    # ends up half-updated.
    staged: dict[Path, str] = {}
    pin_msgs: list[str] = []
    projectconfig_changed = False

    for pin in matched:
        new_apverid = _resolve_for(pin)
        # --force re-fetches wrappers even when the version is unchanged
        # (for server-side format changes that move no pin).
        regen = force and pin.kind == 'wrapper'
        if new_apverid == pin.apverid and not regen:
            pin_msgs.append(
                f'  {Clr.BLD}{pin.file_path}{Clr.RST}'
                f' is already at {Clr.CYN}{pin.apverid}{Clr.RST}.'
            )
            continue
        path, content = _compute_pin_write(projroot, pin, new_apverid)
        staged[path] = content
        if new_apverid == pin.apverid:
            pin_msgs.append(
                f'  {Clr.BLD}{pin.file_path}{Clr.RST}'
                f' regenerated at {Clr.CYN}{pin.apverid}{Clr.RST}.'
            )
        else:
            pin_msgs.append(
                f'  {Clr.BLD}{pin.file_path}{Clr.RST}'
                f' updated: {Clr.CYN}{pin.apverid}{Clr.RST}'
                f' -> {Clr.GRN}{new_apverid}{Clr.RST}'
            )
        if pin.kind == 'projectconfig':
            projectconfig_changed = True
        pin.apverid = new_apverid

    # Stage the builtin-asset id enum regen (base.h / assets.cc splices)
    # if the projectconfig pin moved or the on-disk splice drifted.
    pc_apverid, enum_selfheal = _stage_enum_splices(
        projroot, matched, projectconfig_changed, staged
    )

    # ---- Phase 2: apply all staged writes at once (skipping no-op
    # writes so timestamp-based builds don't needlessly rebuild). ----
    written = _apply_staged_writes(staged)

    pc_path = projroot / 'pconfig' / 'projectconfig.json'
    if pc_path in written:
        # projectconfig was written behind ``getprojectconfig``'s
        # process-wide cache; clear it so later reads see the new pin.
        from efrotools import project as _project

        _project._g_project_configs.pop(  # pylint: disable=protected-access
            str(projroot), None
        )

    # ---- Report (terse, ordered: pins, then enums). ----
    for msg in pin_msgs:
        print(msg)
    enum_changed = bool(
        written
        & {
            projroot / 'src/ballistica/base/base.h',
            projroot / 'src/ballistica/base/assets/assets.cc',
        }
    )
    if pc_apverid and (projectconfig_changed or enum_changed or enum_selfheal):
        if enum_selfheal:
            print(
                f'{Clr.YLW}Builtin-asset enums were stale vs the pin'
                f' ({pc_apverid}); regenerated.{Clr.RST}'
            )
        verb = 'updated to' if enum_changed else 'already at'
        clr = Clr.GRN if enum_changed else Clr.CYN
        print(
            f'  {Clr.BLD}builtin-asset enums{Clr.RST} (base.h/assets.cc)'
            f' {verb} {clr}{pc_apverid}{Clr.RST}.'
        )


def _stage_enum_splices(
    projroot: Path,
    matched: list[Pin],
    projectconfig_changed: bool,
    staged: dict[Path, str],
) -> tuple[str, bool]:
    """Stage builtin-asset id enum regen into ``staged`` when needed.

    Regenerates the ``base.h`` / ``assets.cc`` autogen splices (plus the
    fully-generated ``builtin_strings.{h,cc}`` accessor files) whenever
    the projectconfig pin moved OR the on-disk splice is out of sync with
    it. (Wrapper pins don't drive this — they're per-package runtime
    references; the construct-mode pin in projectconfig is what the
    builtin enums track.) This is the *real* header update;
    ``update_project --check`` only verifies the splice matches the pin,
    it never regenerates.

    No asset *assembly* happens here — the enums come from the
    assembly-free ``assetpackage _listing`` query (see
    ``batools.builtinassetids``). Bundle manifests + CAS blobs are built
    by the normal asset build (``make cmake-build``), not by pin updates.

    The splice-staleness condition makes this self-healing: the regen
    depends on the master (the listing fetch), so an update that advanced
    the pin but died before regenerating — e.g. the server was briefly
    unreachable — leaves the pin "already at" the target. A bare
    ``projectconfig_changed`` check would then never retry, and the
    half-applied state (pin new, splice stale) sticks until a manual fix.
    Comparing the splice's embedded apverid to the pin lets any re-run of
    ``assetpins update`` converge to a consistent state.

    We compute against ``pc_apverid`` explicitly rather than letting the
    generator read projectconfig: the projectconfig write is still only
    staged at this point, so disk would show the *old* pin.

    Returns ``(pc_apverid, selfheal)`` -- the apverid the enums track
    (``''`` if no projectconfig pin matched) and whether this was a pure
    self-heal (splice stale but pin unchanged).
    """
    projectconfig_pins = [p for p in matched if p.kind == 'projectconfig']
    if not projectconfig_pins:
        return '', False
    pc_apverid = projectconfig_pins[0].apverid
    # The splice embeds the pin as ``kBuiltinAssetsApverid = "<id>";``; a
    # quoted-substring check is insensitive to clang-format wrapping
    # (mirrors check_builtin_asset_ids in batools/project/_checks.py).
    base_h = (projroot / 'src/ballistica/base/base.h').read_text()
    splice_stale = f'"{pc_apverid}"' not in base_h
    if not projectconfig_changed and not splice_stale:
        return pc_apverid, False
    from batools.builtinassetids import compute_splices

    for rel_path, content in compute_splices(projroot, pc_apverid).items():
        staged[projroot / rel_path] = content
    return pc_apverid, splice_stale and not projectconfig_changed


def _apply_staged_writes(staged: dict[Path, str]) -> set[Path]:
    """Write staged ``path -> content`` entries, skipping unchanged ones.

    Returns the set of paths actually written. Skipping no-op writes
    keeps file mtimes stable so timestamp-based builds don't rebuild
    needlessly.
    """
    written: set[Path] = set()
    for path, content in staged.items():
        if path.exists() and path.read_text() == content:
            continue
        path.write_text(content)
        written.add(path)
    return written


def do_check(projroot: Path) -> list[Pin]:
    """Return the list of dev/test pins (empty = clean).

    Used by the pre-pubsync gate (and by ``make assetpins-check``)
    to refuse before any committed-source dev/test pin can flow
    to a public artifact.
    """
    return [
        pin
        for pin in _discover_pins(projroot)
        if pin.pin_type is not PinType.PROD
    ]


# --------------------------------------------------------------------
# Internal: pin discovery
# --------------------------------------------------------------------


def _discover_pins(projroot: Path) -> list[Pin]:
    """Find all asset-package pins in the source tree."""
    from pathlib import Path
    from efrotools.project import getprojectconfig

    pins: list[Pin] = []

    # projectconfig "assets" — the construct-mode/bootloader pin.
    pc_value = getprojectconfig(projroot).get('assets')
    if isinstance(pc_value, str) and pc_value:
        pin_type = (
            PinType.DEV
            if is_unresolved_dev(pc_value)
            else classify_apverid(pc_value)
        )
        account, package = _account_and_package_or_bare_dev(pc_value)
        pins.append(
            Pin(
                kind='projectconfig',
                file_path=Path('pconfig/projectconfig.json'),
                apverid=pc_value,
                pin_type=pin_type,
                account=account,
                package=package,
            )
        )

    # Python wrappers: any file under src/assets/ba_data/python/
    # carrying a ``# ba_meta require asset-package <id>`` line.
    pins.extend(_discover_wrapper_pins(projroot))

    return pins


def _discover_wrapper_pins(projroot: Path) -> list[Pin]:
    """Walk Python source via bacommon.metascan to find wrappers."""
    from pathlib import Path
    from bacommon.metascan import DirectoryScan

    python_root = projroot / 'src/assets/ba_data/python'
    if not python_root.is_dir():
        return []

    scanner = DirectoryScan(paths=[str(python_root)])
    scanner.run()

    pins: list[Pin] = []
    for apverid, modulenames in scanner.results.asset_packages.items():
        for modulename in modulenames:
            file_path = Path(
                'src/assets/ba_data/python',
                *modulename.split('.'),
            ).with_suffix('.py')
            wrapper_type = _detect_wrapper_type(projroot / file_path)
            account, package = _account_and_package_or_bare_dev(apverid)
            pins.append(
                Pin(
                    kind='wrapper',
                    file_path=file_path,
                    apverid=apverid,
                    pin_type=classify_apverid(apverid),
                    account=account,
                    package=package,
                    wrapper_type=wrapper_type,
                )
            )
    return pins


# Wrapper-type tag in the wrapper's module docstring. The
# server emits e.g. ``"""Asset-package wrapper for ``<id>``
# (bascenev1)."""`` as the first line of the docstring; the
# parenthesised value is the wrapper type.
_RE_WRAPPER_DOCSTRING_TYPE = re.compile(
    r'Asset-package wrapper for ``[^`]+`` \((bascenev1|bauiv1|babase)\)'
)


def _detect_wrapper_type(path: Path) -> str:
    """Sniff a wrapper's featureset target from its docstring.

    Server-generated wrappers carry the wrapper type in their
    module docstring (``Asset-package wrapper for ``<id>``
    (<wrapper_type>).``). Extracting from there is more robust
    than parsing imports, which now live under TYPE_CHECKING +
    function-local statements so they don't trip the project's
    "package shouldn't import its own top-level" rule when the
    wrapper sits inside its featureset's own package.
    """
    if not path.is_file():
        raise CleanError(
            f'Wrapper file {path} does not exist on disk;'
            f' metascan and disk disagree.'
        )
    text = path.read_text()
    match = _RE_WRAPPER_DOCSTRING_TYPE.search(text)
    if match is None:
        raise CleanError(
            f'Could not detect wrapper_type in {path};'
            f' expected an ``Asset-package wrapper for ``<id>``'
            f' (bascenev1|bauiv1)`` docstring line.'
        )
    return match.group(1)


def _account_and_package_or_bare_dev(apverid: str) -> tuple[str, str]:
    """Return ``(account, package)`` from an apverid.

    Tolerates bare-dev apverids (``<account>.<name>.dev``).
    """
    parts = apverid.split('.')
    if len(parts) != 3:
        raise CleanError(
            f'Cannot extract account/package from'
            f' malformed apverid {apverid!r}.'
        )
    return parts[0], parts[1]


# --------------------------------------------------------------------
# Internal: target matching
# --------------------------------------------------------------------


def _match_target(pins: list[Pin], target_str: str) -> list[Pin]:
    """Resolve a TARGET string against the discovered pins."""
    from pathlib import Path

    if target_str == 'all':
        return pins

    # Try as package name (matches any pin whose package
    # segment equals the target, possibly across accounts).
    by_package = [p for p in pins if p.package == target_str]
    if by_package:
        return by_package

    # Try as file path. Normalise both to ``Path`` so trailing
    # slash / leading ``./`` shouldn't matter.
    target_path = Path(target_str)
    by_path = [p for p in pins if p.file_path == target_path]
    if by_path:
        return by_path

    known_packages = sorted({p.package for p in pins})
    known_paths = sorted(str(p.file_path) for p in pins)
    raise CleanError(
        f'No pins match target {target_str!r}.'
        f' Known packages: {known_packages}.'
        f' Known files: {known_paths}.'
    )


# --------------------------------------------------------------------
# Internal: version → new apverid
# --------------------------------------------------------------------


def _compute_new_apverid(projroot: Path, pin: Pin, version_str: str) -> str:
    """Compute what apverid ``pin`` should move to.

    Track-preserving (``latest``) and track-switching
    (``prod``/``test``/``dev``) forms query master. Concrete
    third-segment forms (e.g. ``260513``, ``dev260513a``) are
    used as-is, combined with the pin's own account+package. A full
    dotted ``<account-or-tag>.<package>.<version>`` form *retargets*
    the pin to a different asset-package (see
    :func:`_compute_retarget_apverid`).
    """
    # A dotted VERSION is the full retarget form; version segments and
    # track keywords never contain dots, so this is unambiguous.
    if '.' in version_str:
        return _compute_retarget_apverid(projroot, version_str)
    if version_str == 'latest':
        return _query_latest_for_track(projroot, pin, pin.pin_type)
    if version_str == 'prod':
        return _query_latest_for_track(projroot, pin, PinType.PROD)
    if version_str == 'test':
        return _query_latest_for_track(projroot, pin, PinType.TEST)
    if version_str == 'dev':
        return _query_latest_for_track(projroot, pin, PinType.DEV)
    # Concrete third-segment form. Validate by classifying the
    # synthesised apverid; this also rejects malformed inputs
    # like ``dev`` (which would re-introduce the bare-pseudo-id
    # state we just resolved away — users should pass ``dev``
    # as the track-switching form above instead).
    new = f'{pin.account}.{pin.package}.{version_str}'
    if is_unresolved_dev(new):
        raise CleanError(
            f'VERSION {version_str!r} is the bare dev pseudo-id;'
            f' pass `dev` (without the third-segment quotes) as a'
            f' track-switching form to resolve to the current'
            f' devN snapshot.'
        )
    classify_apverid(new)  # raises on malformed
    return new


def _compute_retarget_apverid(projroot: Path, spec: str) -> str:
    """Compute a cross-package apverid from a full retarget spec.

    ``spec`` is ``<account-or-tag>.<package>.<version>`` — used to
    point a pin at a *different* asset-package, not just a new version
    of its current one. The account may be an account id (``a-0``) or
    a tag (``efro``). ``<version>`` is a concrete segment
    (``test260518``) or a ``prod``/``test``/``dev`` track keyword
    resolved against the target package. ``latest`` is not valid here
    (it preserves an existing pin's track; a retarget has none).

    No permission checks: master enforces those when assets are
    actually fetched, so an unauthorized reference simply fails there.
    """
    parts = spec.split('.')
    if len(parts) != 3 or not all(parts):
        raise CleanError(
            f'VERSION {spec!r}: a dotted VERSION must be a full'
            f' <account-or-tag>.<package>.<version> spec'
            f' (e.g. efro.mynewassets.test260518).'
        )
    account_or_tag, package, version_seg = parts
    accountid = _resolve_account_id(projroot, account_or_tag)

    if version_seg == 'latest':
        raise CleanError(
            "VERSION 'latest' is track-preserving and needs an existing"
            ' pin; in the full <account>.<package>.<version> form pass'
            ' prod/test/dev or a concrete version segment instead.'
        )
    if version_seg == 'prod':
        result = _bacloud_version(projroot, accountid, package, prod=True)
        if result is None:
            raise CleanError(
                f'No prod version of {accountid}.{package} found on master.'
            )
        return result
    if version_seg == 'test':
        result = _bacloud_version(projroot, accountid, package, prod=False)
        if result is None:
            raise CleanError(
                f'No test version of {accountid}.{package} found on master.'
            )
        return result
    if version_seg == 'dev':
        return _resolve_bare_dev(projroot, accountid, package)

    # Concrete version segment.
    new = f'{accountid}.{package}.{version_seg}'
    if is_unresolved_dev(new):
        raise CleanError(
            f'VERSION {spec!r}: bare dev pseudo-id; pass the third'
            f' segment as `dev` to resolve the current devN snapshot.'
        )
    classify_apverid(new)  # raises on malformed
    return new


def _query_latest_for_track(projroot: Path, pin: Pin, track: PinType) -> str:
    """Ask master for the latest apverid on ``track`` for pin.

    Always uses the pin's own ``account`` to avoid cross-account
    aliasing — two pins on different accounts but the same
    package name have separate version histories.
    """
    from typing import assert_never

    match track:
        case PinType.DEV:
            return _resolve_bare_dev(projroot, pin.account, pin.package)
        case PinType.PROD:
            result = _bacloud_version(
                projroot, pin.account, pin.package, prod=True
            )
            if result is None:
                raise CleanError(
                    f'No prod version of {pin.account}.{pin.package}'
                    f' found on master.'
                )
            return result
        case PinType.TEST:
            result = _bacloud_version(
                projroot, pin.account, pin.package, prod=False
            )
            if result is None:
                raise CleanError(
                    f'No test version of {pin.account}.{pin.package}'
                    f' found on master.'
                )
            return result
        case _:
            assert_never(track)


# --------------------------------------------------------------------
# Internal: master roundtrips
# --------------------------------------------------------------------


def _bacloud_failure_detail(
    result: subprocess.CompletedProcess[str],
) -> str:
    """Build a diagnostic suffix from a failed bacloud subprocess.

    bacloud prints its ``CleanError`` message to stdout (not stderr),
    so a transient transport/HTTP failure typically leaves stderr
    empty — which historically produced bare, misleading errors that
    read like a missing/format-broken pin. Folding both streams plus
    the exit code in keeps transient transport blips distinguishable
    from a genuine "no such version" / format error.
    """
    bits = [f'exit code {result.returncode}']
    out = result.stdout.strip()
    err = result.stderr.strip()
    if out:
        bits.append(f'stdout: {out}')
    if err:
        bits.append(f'stderr: {err}')
    return '; '.join(bits)


def _resolve_bare_dev(projroot: Path, account: str, package: str) -> str:
    """Ask master to resolve to the current dev snapshot.

    Uses ``bacloud assetpackage version --dev`` which routes
    through the workspace-aware dev-resolve path on master and
    returns just the resolved apverid — no assemble, no
    recipe-cache work, no local manifest side-effects.

    Note ``--dev`` deliberately can't be combined with ``--account``:
    dev resolution always operates on the authenticated account's own
    packages (you can only resolve the ``.dev`` snapshot of a workspace
    you own). ``account`` is therefore used only for messaging here.
    """
    cmd = [
        str(projroot / 'tools' / 'bacloud'),
        'assetpackage',
        'version',
        package,
        '--dev',
    ]
    result = subprocess.run(
        cmd, cwd=projroot, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise CleanError(
            f'Failed to resolve {account}.{package}.dev via'
            f' bacloud assetpackage version --dev'
            f' ({_bacloud_failure_detail(result)}).'
        )
    out = result.stdout.strip()
    if not out:
        raise CleanError(
            f'bacloud assetpackage version --dev returned empty'
            f' output for {account}.{package}.'
        )
    return out


def _bacloud_version(
    projroot: Path, account: str, package: str, *, prod: bool
) -> str | None:
    """Return the newest version id for ``account.package``.

    Wraps ``bacloud assetpackage version --account <X>``. Returns
    None if bacloud reports no matching version.
    """
    cmd = [
        str(projroot / 'tools' / 'bacloud'),
        'assetpackage',
        'version',
        package,
        '--account',
        account,
    ]
    if prod:
        cmd.append('--prod')
    result = subprocess.run(
        cmd, cwd=projroot, capture_output=True, text=True, check=False
    )
    # bacloud convention: exit 0 = found, exit 1 = no match,
    # exit 2 = error.
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise CleanError(
            f'bacloud assetpackage version failed for'
            f' {account}.{package} (prod={prod})'
            f' ({_bacloud_failure_detail(result)}).'
        )
    out = result.stdout.strip()
    return out or None


def _fetch_account_info(
    projroot: Path, account_or_tag: str
) -> AccountResponse | None:
    """Return account info via ``bacloud account info --json``.

    Accepts an account id (``a-0``) or a tag (``efro``) — bacloud
    resolves either, using the caller's own bacloud auth. Returns
    None if no such account exists (bacloud exit 1); raises on any
    other failure.
    """
    from efro.dataclassio import dataclass_from_json

    from bacommon.restapi.v1.accounts import AccountResponse

    result = subprocess.run(
        [
            str(projroot / 'tools' / 'bacloud'),
            'account',
            'info',
            account_or_tag,
            '--json',
        ],
        cwd=projroot,
        capture_output=True,
        text=True,
        check=False,
    )
    # bacloud convention: exit 0 = found, exit 1 = no such account,
    # anything else = error.
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise CleanError(
            f'bacloud account info failed for {account_or_tag}'
            f' ({_bacloud_failure_detail(result)}).'
        )
    return dataclass_from_json(AccountResponse, result.stdout.strip())


def _query_account_tag(projroot: Path, account: str) -> str | None:
    """Return the display tag for ``account`` (e.g. ``efro``).

    None if no such account exists (deleted); raises on lookup
    failure.
    """
    info = _fetch_account_info(projroot, account)
    return None if info is None else info.tag


def _resolve_account_id(projroot: Path, account_or_tag: str) -> str:
    """Resolve an account id or tag to the canonical account id.

    ``a-...`` ids are used as-is (no roundtrip); anything else is
    treated as a tag and resolved to its account id via master.
    """
    if account_or_tag.startswith('a-'):
        return account_or_tag
    info = _fetch_account_info(projroot, account_or_tag)
    if info is None:
        raise CleanError(f'No account found for tag {account_or_tag!r}.')
    return info.id


def _fetch_wrapper(projroot: Path, apverid: str, wrapper_type: str) -> str:
    """Fetch a freshly-generated wrapper module from master.

    Uses ``bacloud assetpackage wrapper``, which authenticates with
    the caller's own bacloud login — uniform with the version
    lookups and requiring no admin Bearer key (so it works for any
    signed-in user, and bacloud handles the not-signed-in case).
    bacloud writes the generated module to a path, so we route it
    through a scratch file under ``build/tmp`` and return the
    contents (the caller compares against the on-disk file and only
    rewrites on change).
    """
    tmpdir = projroot / 'build' / 'tmp'
    tmpdir.mkdir(parents=True, exist_ok=True)
    out_rel = f'build/tmp/assetpins_wrapper_{wrapper_type}.py'
    out_path = projroot / out_rel
    result = subprocess.run(
        [
            str(projroot / 'tools' / 'bacloud'),
            'assetpackage',
            'wrapper',
            apverid,
            wrapper_type,
            out_rel,
        ],
        cwd=projroot,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CleanError(
            f'Failed to fetch wrapper for {apverid}'
            f' (wrapper_type={wrapper_type};'
            f' {_bacloud_failure_detail(result)}).'
        )
    try:
        content = out_path.read_text()
    finally:
        out_path.unlink(missing_ok=True)
    if not content.lstrip().startswith('# Released under'):
        raise CleanError(
            f'Fetched wrapper for {apverid} does not look like a'
            f' valid wrapper source (first chars: {content[:80]!r}).'
        )
    return content


# --------------------------------------------------------------------
# Internal: apply update (writeback)
# --------------------------------------------------------------------


def _compute_pin_write(
    projroot: Path, pin: Pin, new_apverid: str
) -> tuple[Path, str]:
    """Compute ``(abs_path, new_content)`` for a pin update.

    Pure: performs the resolve/fetch work and returns what *should*
    be on disk, but writes nothing. ``do_update`` stages all such
    results and applies them together so a mid-update failure leaves
    the tree untouched.
    """
    if pin.kind == 'projectconfig':
        return _compute_projectconfig_write(projroot, new_apverid)
    if pin.kind == 'wrapper':
        return _compute_wrapper_write(projroot, pin, new_apverid)
    raise CleanError(f'Internal error: unknown pin kind {pin.kind!r}.')


def _compute_projectconfig_write(
    projroot: Path, new_apverid: str
) -> tuple[Path, str]:
    """Compute projectconfig with ``"assets"`` set to ``new_apverid``.

    Uses a string-level edit to preserve formatting (comments, key
    ordering, trailing newline) since the rest of the file may carry
    editorial intent we don't want ``json.dump`` to wash away. Returns
    ``(path, new_text)``; the caller writes (and clears the
    ``getprojectconfig`` cache) when it applies staged writes.
    """
    pc = projroot / 'pconfig' / 'projectconfig.json'
    text = pc.read_text()
    new_text, count = re.subn(
        r'("assets"\s*:\s*)"[^"]*"',
        lambda m: f'{m.group(1)}"{new_apverid}"',
        text,
        count=1,
    )
    if count == 0:
        raise CleanError(
            f'Could not locate "assets" entry in {pc} for writeback.'
        )
    return pc, new_text


def _compute_wrapper_write(
    projroot: Path, pin: Pin, new_apverid: str
) -> tuple[Path, str]:
    """Compute the refreshed wrapper file content for ``new_apverid``.

    Wrappers are server-generated; updating means asking the server for
    a fresh version pointing at ``new_apverid``. We never hand-edit a
    wrapper. Returns ``(path, content)``; nothing is written here.
    """
    assert pin.wrapper_type is not None
    content = _fetch_wrapper(projroot, new_apverid, pin.wrapper_type)
    # The server stamps wrappers with its notion of the current
    # client api version (so they load as standalone mods-dir
    # modules); make sure that matches ours. A mismatch means the
    # server-side constant (bamaster ``src/bamaster/clientapi.py``)
    # needs a bump before wrappers can be refreshed — this is the
    # cross-repo tripwire for api version bumps.
    ourapi = get_current_api_version(str(projroot))
    apimatch = re.search(r'# ba_meta require api (\d+)', content)
    if apimatch is None or int(apimatch.group(1)) != ourapi:
        found = 'no api line' if apimatch is None else apimatch.group(1)
        raise CleanError(
            f'Fetched wrapper for {new_apverid} declares client api'
            f' {found} but this project is on api {ourapi}; bump'
            f' CLIENT_API_VERSION in bamaster src/bamaster/clientapi.py'
            f' (and deploy) before refreshing wrappers.'
        )
    # No local format/line-length pass: the server guarantees
    # format-clean, lint-clean output (formatted via the checkenv
    # black + a line-too-long guard; see bamaster
    # ``assetpackage/_wrappergen._format_and_guard``), and the same
    # 80-col config applies on both sides — so fetched content lands
    # as-is and the no-change comparison (at apply time) stays
    # meaningful.
    return projroot / pin.file_path, content
