# Released under the MIT License. See LICENSE for details.
#
"""Text related functionality."""

import time
import logging
from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    import babase


def timestring(
    timeval: float | int,
    centi: bool = True,
) -> babase.Lstr:
    """Generate a localized string for displaying a time value.

    Given a time value, returns a localized string with:
    (hours if > 0 ) : minutes : seconds : (centiseconds if centi=True).

    .. warning::

      the underlying localized-string value is somewhat large, so don't
      use this to rapidly update text values for an in-game timer or you
      may consume significant network bandwidth. For that sort of thing
      you should use things like 'timedisplay' nodes and attribute
      connections.
    """
    from babase._language import Lstr

    # We take float seconds but operate on int milliseconds internally.
    timeval = int(1000 * timeval)
    bits = []
    subs = []
    hval = (timeval // 1000) // (60 * 60)
    if hval != 0:
        bits.append('${H}')
        subs.append(
            (
                '${H}',
                Lstr(
                    resource='timeSuffixHoursText',
                    subs=[('${COUNT}', str(hval))],
                ),
            )
        )
    mval = ((timeval // 1000) // 60) % 60
    if mval != 0:
        bits.append('${M}')
        subs.append(
            (
                '${M}',
                Lstr(
                    resource='timeSuffixMinutesText',
                    subs=[('${COUNT}', str(mval))],
                ),
            )
        )

    # We add seconds if its non-zero *or* we haven't added anything else.
    if centi:
        # pylint: disable=consider-using-f-string
        sval = timeval / 1000.0 % 60.0
        if sval >= 0.005 or not bits:
            bits.append('${S}')
            subs.append(
                (
                    '${S}',
                    Lstr(
                        resource='timeSuffixSecondsText',
                        subs=[('${COUNT}', ('%.2f' % sval))],
                    ),
                )
            )
    else:
        sval = timeval // 1000 % 60
        if sval != 0 or not bits:
            bits.append('${S}')
            subs.append(
                (
                    '${S}',
                    Lstr(
                        resource='timeSuffixSecondsText',
                        subs=[('${COUNT}', str(sval))],
                    ),
                )
            )
    return Lstr(value=' '.join(bits), subs=subs)


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
