# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui text-wrapping test page.

Row and section titles, subtitles and footnotes word-wrap to their
columns: in background prep each is evaluated (ignoring the string's
own wrap hints) and wrapped with the engine's own text measure at the
width and scale its text widget gets, so every line fits and nothing
shrinks to fit. Lines break only where the OS's line-break rules
allow, and each line fills as far as it will go before the next
starts (so only the last runs short). With debug on, each row's outline
shows its column; text should reach close to its right edge but never
past it, and rows grow taller to fit their wrapped text.

The live-time row is the one deliberate exception: time-varying text
can't be wrapped once up front, so its subtitle stays a single line
(squished to fit, as unwrapped text always was) and the client logs
one ``ba.ui`` warning about it.
"""

import datetime
from dataclasses import replace
from typing import TYPE_CHECKING

from bacommon.langstr import LangStrSpecTimeTarget, LangStrSpecValue
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.routes.docuitest
    import bacommon.docui.v2

_LONG_EN = (
    'The quick brown fox jumps over the lazy dog while the cat watches'
    ' from a sunny windowsill nearby, entirely unimpressed by the whole'
    ' display and wondering what all the fuss is about.'
)
_LONG_JA = (
    '日本語のテキストは、ほとんどの場所で改行できます。'
    '句読点が行頭に来ないように、禁則処理も行われます。'
    'これは長いタイトルのテストです。'
)
_LONG_ZH = (
    '这是一个很长的中文副标题，可以在大多数字符之间换行，'
    '但标点符号不应该出现在行首。我们再多写一点文字，'
    '让它在较窄的栏中换成好几行。'
)
_LONG_TH = (
    'ภาษาไทยไม่มีช่องว่างระหว่างคำแต่ต้องตัดคำให้ถูกต้อง'
    'ตามพจนานุกรมของระบบปฏิบัติการ ดังนั้นบรรทัดนี้จะถูกตัด'
    'เฉพาะระหว่างคำเท่านั้น'
)
_LONG_MIXED = (
    'Player Bob说了hello แล้วก็ไป home, then said 日本語 and 🎉🎊 a few'
    ' more English words so that this mixed-script footnote wraps onto'
    ' several lines of its own.'
)


def _lit(text: str) -> LangStrSpecValue:
    # Dev-only page, so baked literals.
    return LangStrSpecValue.literal(text)


def _btn(label: str) -> bacommon.docui.v2.Button:
    """A do-nothing button for rows to hold."""
    return dui2.Button(
        label=_lit(label),
        style=dui2.ButtonStyle.MEDIUM,
        size=(180.0, 50.0),
        action=dui2.Local(),
    )


def test_page_text_wrapping(
    route: bacommon.docui.routes.docuitest.TextWrapping,
) -> bacommon.docui.v2.Response:
    """Testing word-wrapped titles, subtitles and footnotes."""
    import babase

    debug = route.debug

    def _row(
        button: str,
        *,
        title: str | None = None,
        subtitle: str | LangStrSpecValue | None = None,
        footnote: str | None = None,
        align: dui2.HAlign | None = None,
    ) -> bacommon.docui.v2.ButtonRow:
        return dui2.ButtonRow(
            title=None if title is None else _lit(title),
            subtitle=(
                _lit(subtitle) if isinstance(subtitle, str) else subtitle
            ),
            footnote=None if footnote is None else _lit(footnote),
            title_align=align,
            buttons=[_btn(button)],
            debug=debug,
        )

    soon = LangStrSpecTimeTarget.at(
        babase.utc_now_cloud() + datetime.timedelta(minutes=10)
    )

    return dui2.Response(
        page=dui2.Page(
            title=_lit('Text Wrapping'),
            rows=[
                _row(
                    'English',
                    title=_LONG_EN,
                    subtitle=_LONG_EN,
                    footnote=_LONG_EN,
                ),
                _row(
                    'CJK + Thai',
                    title=_LONG_JA,
                    subtitle=_LONG_ZH,
                    footnote=_LONG_TH,
                ),
                _row(
                    'Mixed',
                    title='Short titles stay on one line',
                    footnote=_LONG_MIXED,
                ),
                _row(
                    'Centered',
                    title=_LONG_EN,
                    subtitle=_LONG_EN,
                    align=dui2.HAlign.CENTER,
                ),
                _row(
                    'Right',
                    title=_LONG_EN,
                    subtitle=_LONG_EN,
                    align=dui2.HAlign.RIGHT,
                ),
                _row(
                    'Newlines',
                    title='Authored line breaks are kept:',
                    subtitle=(
                        'This first paragraph is long enough that it'
                        ' wraps on its own before its authored break,'
                        ' even in the widest windows, because it just'
                        ' keeps going and going for quite a while.'
                        '\n\nAnd this paragraph comes after a blank line,'
                        ' which stays exactly where it was written.'
                    ),
                ),
                _row(
                    'Long word',
                    title=(
                        'Pneumonoultramicroscopicsilicovolcanoconiosis'
                        'Supercalifragilisticexpialidocious'
                        'Antidisestablishmentarianism'
                    ),
                    subtitle=(
                        'A word too wide for any line breaks between'
                        ' characters instead.'
                    ),
                ),
                dui2.ButtonControlRow(
                    button=_btn('Control'),
                    label=_lit('A control row label'),
                    title=_lit(_LONG_EN),
                    subtitle=_lit(_LONG_EN),
                    footnote=_lit(_LONG_EN),
                    debug=debug,
                ),
                dui2.Section(
                    title=_lit(_LONG_EN),
                    subtitle=_lit(_LONG_EN),
                    footnote=_lit(_LONG_EN),
                    backing=dui2.SectionBacking(
                        color=(0.35, 0.55, 1.0, 0.3),
                        content_inset=28.0,
                        max_width=700.0,
                    ),
                    debug=debug,
                    rows=[
                        _row(
                            'In a card',
                            title=_LONG_JA,
                            subtitle=_LONG_EN,
                            footnote=_LONG_MIXED,
                        ),
                    ],
                ),
                _row(
                    'Live time',
                    title='Live text is not wrapped',
                    subtitle=LangStrSpecValue(
                        'This subtitle holds a live countdown, ending in'
                        ' {t|duration(dir=future)}, so wrapping it up'
                        ' front would freeze it; it stays one line instead'
                        ' (squished to fit) and the client logs a warning.',
                        {'t': soon},
                    ),
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=_lit('Hide Debug' if debug else 'Show Debug'),
                            style=dui2.ButtonStyle.MEDIUM,
                            size=(240, 60),
                            color=(0.6, 0.4, 0.8, 1.0),
                            action=replace(route, debug=not debug).replace(),
                        )
                    ],
                ),
            ],
        )
    )
