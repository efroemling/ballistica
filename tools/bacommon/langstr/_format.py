# Released under the MIT License. See LICENSE for details.
#
"""Display-time rendering for spec'd language-string params.

A brief may mark a param with a rendering spec (``{size|data_size}``);
the translated text that comes out the other side holds only a
``{size}`` token, so the *kind* travels separately in the language blob
(see ``display_param_kinds`` / ``parse_language_param_kinds``) and the
value is rendered here, at decode time, in the viewer's locale.

Rendering at display time rather than at construction is what keeps a
language-string a **template with a slot** rather than a function of its
value: the same spec re-renders as the value changes (a live counter
crossing 999 MB -> 1.0 GB is a different render, not a different
string), and the value stays a plain ``int`` on the wire.

Two ingredients, deliberately split by what kind of thing they are:

* **Unit words** ("bytes", "KB", "Go") are translated content, authored
  in the components asset package and reaching us through the same
  per-locale values every other string uses.
* **The decimal mark** is locale *data*, curated on
  :attr:`~bacommon.locale.LocaleResolved.decimal_mark` -- never asked
  of a translation model, which would answer confidently and sometimes
  wrongly.
"""

from typing import TYPE_CHECKING

from bacommon.loctext import evaluate

if TYPE_CHECKING:
    from bacommon.locale import Locale
    from bacommon.loctext import StringSelector

#: Key prefix for the data-size units within a package's embedded
#: components. Authored in BaComponentAssets (see the asset-packages
#: design doc's package catalog) and copied into each consuming
#: package's blob at build time, so rendering never depends on another
#: package being resolvable in the environment.
#:
#: These live under the blob's own top-level ``components`` key rather
#: than as paths inside ``strings``. That is load-bearing, not tidiness:
#: string indices are assigned in sorted-name order over the ``strings``
#: map, and the producer derives them from briefs (which have no
#: components) while the consumer derives them from the blob. Adding
#: component *paths* to ``strings`` would shift every authored string's
#: index on one side only, and the indexed wire form would decode to the
#: wrong string.
DATA_SIZE_GROUP = 'data_size'

#: Key prefix for the duration units within a package's embedded
#: components: abbreviated unit labels ("{amount}h") for the composed
#: form ``duration_str`` renders ("1h 23m"). Abbreviations don't
#: inflect, which is what makes composition (and sentence-side
#: direction words, per D12) safe across languages.
DURATION_GROUP = 'duration'

#: Which component group each display-param kind renders through --
#: i.e. what a producer embedding components for a package must
#: include when that package uses the kind. Grows alongside the
#: ``render_display_param`` dispatch as formatters are added; a kind a
#: producer encounters that is absent here is a hard error there, not
#: a silent display-time ``LANGSTR_ERROR``.
COMPONENT_GROUP_BY_KIND: dict[str, str] = {
    'bytes': DATA_SIZE_GROUP,
    'millis': DURATION_GROUP,
}

#: The size ladder, smallest first: ``(entry, bytes-per-unit)``. Mirrors
#: ``efro.util.data_size_str`` and extends it by one rung to terabytes.
#: The ``bytes`` rung is a plural entry (its count is the pivot); every
#: other rung takes a preformatted ``{amount}`` text sub, so each locale
#: controls its own spacing and word order ("1,2 Go", "1.2 GB").
_LADDER: tuple[tuple[str, int], ...] = (
    ('bytes', 1),
    ('kilobytes', 1024),
    ('megabytes', 1024**2),
    ('gigabytes', 1024**3),
    ('terabytes', 1024**4),
)


#: The duration ladder, largest first: ``(entry, seconds-per-unit)``.
#: Mirrors ``efro.util.timedelta_str`` (years are 365 days; no
#: months/weeks rungs).
_DURATION_LADDER: tuple[tuple[str, int], ...] = (
    ('years', 365 * 24 * 3600),
    ('days', 24 * 3600),
    ('hours', 3600),
    ('minutes', 60),
    ('seconds', 1),
)


def duration_str(
    millis: int,
    locale: 'Locale',
    values: 'dict[str, str | StringSelector]',
    *,
    maxparts: int = 2,
    decimals: int = 0,
    direction: str | None = None,
    clamp: bool = False,
) -> str:
    """Render a length of time as composed abbreviated units.

    Mirrors ``efro.util.timedelta_str`` ("1h 23m"; ``maxparts`` caps
    the composed units largest-first, ``decimals`` applies fractional
    places to the last one), rendering each part through the
    components package's per-locale ``duration/`` unit templates and
    joining with the curated
    :attr:`~bacommon.locale.LocaleResolved.duration_separator`.

    ``millis`` follows the signed ``target - now`` convention (D12),
    in integer milliseconds -- the sub wire type must stay ``int``,
    and ms precision is what keeps ``decimals`` meaningful.
    ``direction`` (``'past'`` / ``'future'``) renders the magnitude of
    that sign and floors the other to ``0s`` -- countdown-safe by
    construction; ``clamp`` floors negatives for an undirected length;
    with neither, negatives render as magnitude plus a leading ``-``
    (D-neg, same caveats).

    Raises :class:`KeyError` if the components package is missing an
    entry -- the decode path turns that into the usual fail-visible
    ``LANGSTR_ERROR`` sentinel rather than letting it escape.
    """
    if direction == 'future':
        millis = max(0, millis)
    elif direction == 'past':
        millis = max(0, -millis)
    elif clamp:
        millis = max(0, millis)
    elif millis < 0:
        rendered = duration_str(
            -millis, locale, values, maxparts=maxparts, decimals=decimals
        )
        return f'-{rendered}'
    seconds = millis / 1000.0

    def _render(entry: str, amount: str) -> str:
        return evaluate(
            values[f'{DURATION_GROUP}/{entry}'], locale, amount=amount
        )

    # Whole units, largest first (each remainder feeds the next rung),
    # plus each rung's fractional total (everything to its left
    # excluded) for the decimals case -- the same decomposition
    # ``efro.util.timedelta_str`` does.
    remainder = int(seconds)
    covered = 0.0
    parts: list[str] = []
    for i, (entry, scale) in enumerate(_DURATION_LADDER):
        whole = remainder // scale
        remainder = remainder % scale
        frac_total = seconds / scale - (covered / scale)
        covered += whole * scale
        is_seconds_rung = i == len(_DURATION_LADDER) - 1
        # Emit once a nonzero rung starts the sequence (mid-zeros are
        # kept: "1h 0m 32s"); the seconds rung backstops an all-zero
        # value so "0s" always shows.
        if not (whole or parts or is_seconds_rung):
            continue
        if decimals and (len(parts) >= maxparts - 1 or is_seconds_rung):
            amount = format_number(frac_total, decimals, locale)
        else:
            amount = str(whole)
        parts.append(_render(entry, amount))
        if len(parts) >= maxparts:
            break
    return locale.resolved.duration_separator.join(parts)


def render_display_param(
    kindexpr: str,
    value: str | int | float,
    locale: 'Locale',
    components: 'dict[str, str | StringSelector]',
) -> str:
    """Render one spec'd param value for a locale -- the shared dispatch.

    ``kindexpr`` is the display-kind expression a blob's ``k`` carrier
    (or a wrapper's baked kinds map) holds -- the bare kind or kind
    plus spec args (``'bytes(compact=true)'``); see
    :attr:`~bacommon.strbrief.BriefTag.display_kind`. The single
    render-dispatch both the server-side decode context and the client
    wrapper runtime route through, so the two sides can't drift.

    Raises on a malformed expression, an unknown kind, or a missing
    component entry; callers apply their own fail-visible or fail-soft
    policy.
    """
    from bacommon.strbrief import parse_display_kind

    kind, args = parse_display_kind(kindexpr)
    if kind == 'bytes':
        return data_size_str(
            int(value),
            locale,
            components,
            compact=bool(args.get('compact', False)),
        )
    if kind == 'millis':
        rawdir = args.get('dir')
        return duration_str(
            int(value),
            locale,
            components,
            maxparts=int(args.get('maxparts', 2)),
            decimals=int(args.get('decimals', 0)),
            direction=str(rawdir) if rawdir is not None else None,
            clamp=bool(args.get('clamp', False)),
        )
    raise ValueError(f'unknown display param kind {kind!r}')


def format_number(value: float, decimals: int, locale: 'Locale') -> str:
    """Render a number with fixed decimals and the locale's mark.

    Rounding happens first and the mark is swapped last, on a known
    ASCII rendering -- never format-then-reparse, which would have to
    guess which of ``.``/``,`` it was looking at.
    """
    text = f'{value:.{decimals}f}'
    mark = locale.resolved.decimal_mark
    return text if mark == '.' else text.replace('.', mark)


def data_size_str(
    bytecount: int,
    locale: 'Locale',
    values: 'dict[str, str | StringSelector]',
    *,
    compact: bool = False,
) -> str:
    """Render a byte count as human-readable size in ``locale``.

    ``values`` is the components package's per-locale value map. The
    ladder and the adaptive decimals (one place below ten units, none
    above) mirror :func:`efro.util.data_size_str`, as does ``compact``
    for width-constrained slots: the only rung it changes is bytes,
    which renders through the abbreviated ``bytes_compact`` entry
    ("37 B") instead of pluralizing ("37 bytes") -- larger rungs are
    already abbreviated. Abbreviations don't inflect, so that entry is
    a plain ``{amount}`` template like the larger rungs, not a plural.

    Raises :class:`KeyError` if the components package is missing an
    entry -- the decode path turns that into the usual fail-visible
    ``LANGSTR_ERROR`` sentinel rather than letting it escape.
    """
    if bytecount < 0:
        return f'-{data_size_str(-bytecount, locale, values, compact=compact)}'

    # Bytes are counted, not measured, so this rung pluralizes rather
    # than taking a formatted value ("1 byte" / "2 bytes"). Note the
    # English helper this ports from says "1 bytes"; being a real
    # plural entry fixes that for every language including English.
    if bytecount <= 999:
        if compact:
            return evaluate(
                values[f'{DATA_SIZE_GROUP}/bytes_compact'],
                locale,
                amount=str(bytecount),
            )
        return evaluate(values[f'{DATA_SIZE_GROUP}/bytes'], locale, n=bytecount)

    def _render(entry: str, scaled: float, decimals: int) -> str:
        return evaluate(
            values[f'{DATA_SIZE_GROUP}/{entry}'],
            locale,
            amount=format_number(scaled, decimals, locale),
        )

    # Smallest rung first, promoting to the next unit once the mantissa
    # grows past it -- one decimal place while that place still carries
    # information, none after.
    last = len(_LADDER) - 1
    for i in range(1, len(_LADDER)):
        entry, scale = _LADDER[i]
        scaled = bytecount / scale
        if round(scaled, 1) < 10.0:
            return _render(entry, scaled, 1)
        # The top rung has nothing to promote to, so it absorbs
        # everything above it however large.
        if i == last or round(scaled, 0) < 999:
            return _render(entry, scaled, 0)

    # Unreachable: the top rung above returns for any remaining value.
    raise AssertionError(f'no ladder rung for {bytecount}')
