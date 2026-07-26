# Released under the MIT License. See LICENSE for details.
#
"""Text related functionality."""

import time
import logging
from typing import TYPE_CHECKING, overload

import _babase

if TYPE_CHECKING:
    from typing import Literal

    import babase


def _timestring_parts(
    timeval: float | int, centi: bool
) -> list[tuple[str, str]]:
    """Split a time value into (unit, count-text) pieces, largest first.

    Units are ``'h'``/``'m'``/``'s'``. Always returns at least one piece
    (seconds stand in when everything larger is zero).
    """
    # We take float seconds but operate on int milliseconds internally.
    timeval = int(1000 * timeval)
    parts: list[tuple[str, str]] = []

    hval = (timeval // 1000) // (60 * 60)
    if hval != 0:
        parts.append(('h', str(hval)))

    mval = ((timeval // 1000) // 60) % 60
    if mval != 0:
        parts.append(('m', str(mval)))

    # We add seconds if its non-zero *or* we haven't added anything else.
    if centi:
        sval = timeval / 1000.0 % 60.0
        if sval >= 0.005 or not parts:
            parts.append(('s', f'{sval:.2f}'))
    else:
        svalint = timeval // 1000 % 60
        if svalint != 0 or not parts:
            parts.append(('s', str(svalint)))

    assert parts
    return parts


@overload
def timestring(
    timeval: float | int,
    centi: bool = True,
    *,
    langstr: Literal[False] = False,
) -> babase.Lstr: ...


@overload
def timestring(
    timeval: float | int,
    centi: bool = True,
    *,
    langstr: Literal[True],
) -> babase.LangStr: ...


def timestring(
    timeval: float | int,
    centi: bool = True,
    *,
    langstr: bool = False,
) -> babase.Lstr | babase.LangStr:
    """Generate a localized string for displaying a time value.

    Given a time value, returns a localized string with:
    (hours if > 0 ) : minutes : seconds : (centiseconds if centi=True).

    Pass ``langstr=True`` to receive a :class:`~babase.LangStr`. The
    legacy :class:`~babase.Lstr` form goes away when api 9 support ends.

    .. warning::

      the underlying localized-string value is somewhat large, so don't
      use this to rapidly update text values for an in-game timer or you
      may consume significant network bandwidth. For that sort of thing
      you should use things like 'timedisplay' nodes and attribute
      connections.
    """
    parts = _timestring_parts(timeval, centi)

    if langstr:
        # Safe up-call: babase is fully imported by the time this runs;
        # the cycle pylint sees is structural only.
        # pylint: disable-next=cyclic-import
        from babase import builtinassets

        tstrs = builtinassets.strings.time
        accessors = {
            'h': tstrs.suffix_hours,
            'm': tstrs.suffix_minutes,
            's': tstrs.suffix_seconds,
        }
        vals = [accessors[unit](count=count) for unit, count in parts]

        # LangStr has no concatenation, so fold the pieces through the
        # join template (at most three deep for h/m/s).
        out = vals[0]
        for val in vals[1:]:
            out = builtinassets.strings.ui.spaced_pair(first=out, second=val)
        return out

    from babase._language import Lstr

    resources = {
        'h': 'timeSuffixHoursText',
        'm': 'timeSuffixMinutesText',
        's': 'timeSuffixSecondsText',
    }
    tokens = {'h': '${H}', 'm': '${M}', 's': '${S}'}
    return Lstr(
        value=' '.join(tokens[unit] for unit, _count in parts),
        subs=[
            (
                tokens[unit],
                Lstr(resource=resources[unit], subs=[('${COUNT}', count)]),
            )
            for unit, count in parts
        ],
    )


def run_line_break_selftest(iterations: int = 500) -> None:
    """Exercise OS line-break analysis; log behavior and timing.

    Feeds sample strings in various scripts through the platform's
    line-break-opportunity analysis (UAX #14 via the OS text stack where
    implemented), sanity-checks the returned offsets, logs each result
    with break opportunities rendered as ``|``, and reports average
    per-call time. Logs at warning level so results show up under
    default log levels on all platforms. Logic thread only.
    """
    samples: list[tuple[str, str]] = [
        ('english', 'Hello there world, how are you today?'),
        ('english-hyphen', 'A well-known state-of-the-art solution.'),
        ('newlines', 'First line.\nSecond line here.'),
        ('japanese', '日本語のテキストは、ほとんどの場所で改行できます。'),
        (
            'japanese-kinsoku',
            'これは「禁則処理」のテストです。ラーメンとカレー。',
        ),
        ('chinese', '这是一个中文句子，可以在大多数字符之间换行。'),
        ('korean', '한국어 텍스트는 공백에서 줄바꿈됩니다.'),
        ('thai', 'ภาษาไทยไม่มีช่องว่างระหว่างคำแต่ต้องตัดคำให้ถูกต้อง'),
        ('mixed-scripts', 'Player Bob说了hello แล้วก็ไป home.'),
        ('emoji', 'Nice 🎉🎊 party 🥳 time!'),
        ('empty', ''),
        ('single-word', 'Hello'),
    ]
    logger = logging.getLogger('ba.gfx')
    logger.warning('line-break-selftest: starting.')
    problems = 0
    for name, text in samples:
        offsets = _babase.get_text_line_break_offsets(text)
        data = text.encode()

        # Sanity: offsets strictly increasing, in range, and always on
        # utf-8 sequence boundaries.
        valid = all(
            0 < off < len(data) and (data[off] & 0xC0) != 0x80
            for off in offsets
        ) and offsets == sorted(set(offsets))
        if not valid:
            problems += 1

        # Render break opportunities as '|' between segments.
        splits = [0, *offsets, len(data)]
        segments = [
            data[splits[i] : splits[i + 1]].decode()
            for i in range(len(splits) - 1)
        ]
        logger.warning(
            'line-break-selftest: %s%s: %s',
            name,
            '' if valid else ' (INVALID OFFSETS)',
            '|'.join(segments).replace('\n', '\\n'),
        )

    # Timing: a short string and a longer paragraph.
    para = (
        'The quick brown fox jumps over the lazy dog while '
        '日本語のテキストも含まれていますし、'
        'ภาษาไทยก็มีอยู่ในย่อหน้านี้ด้วย and then some more '
        'English to round things out nicely with a few extra words.'
    )
    for name, text in [('short', samples[0][1]), ('paragraph', para)]:
        start = time.monotonic()
        for _ in range(iterations):
            _babase.get_text_line_break_offsets(text)
        duration = time.monotonic() - start
        logger.warning(
            'line-break-selftest: timing %s (%d chars): %.1f us per call.',
            name,
            len(text),
            duration / iterations * 1_000_000,
        )
    logger.warning(
        'line-break-selftest: complete; %d problem(s).',
        problems,
    )
