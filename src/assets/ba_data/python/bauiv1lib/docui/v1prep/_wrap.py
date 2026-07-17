# Released under the MIT License. See LICENSE for details.
#
"""Deferred line-splitting for prepped widget calls.

v1 documents carrying :class:`~bacommon.docui.WrapParams` (set only by
the client-local v2→v1 transcode) get their text split into lines at
widget-creation time rather than during prep: prep runs in a background
thread, while the engine's line-break analysis
(:func:`babase.split_text_into_lines`) must run on the logic thread.
The split itself is microseconds per label, so deferring it adds no
meaningful logic-thread cost.
"""

from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    from typing import Any, Callable

    from bacommon.docui import WrapParams
    import bauiv1


def split_wrapped_text(text: str, wrap: WrapParams | None) -> str:
    """Apply optional wrap-params line-splitting to a text value.

    Logic thread only (the underlying line-break analysis requires it).
    """
    if wrap is None:
        return text
    return babase.split_text_into_lines(
        text,
        min_lines=wrap.min_lines,
        max_lines=wrap.max_lines,
        max_chars_per_line=wrap.max_chars_per_line,
    )


def wrapped_widget_call(
    call: Callable[..., bauiv1.Widget],
    textkw: str,
    wrap: WrapParams | None,
    **kwargs: Any,
) -> bauiv1.Widget:
    """Make a widget-construction call, line-splitting one text kwarg.

    Preps bake this shim — the widget call, the name of its text kwarg,
    and the wrap params — into their construction partials so the split
    runs at widget-creation time on the logic thread. ``kwargs`` pass
    through to ``call`` untouched (hence the ``Any`` typing).
    """
    if wrap is not None:
        text = kwargs[textkw]
        assert isinstance(text, str)
        kwargs[textkw] = split_wrapped_text(text, wrap)
    return call(**kwargs)
