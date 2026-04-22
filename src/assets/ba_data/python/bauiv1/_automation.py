# Released under the MIT License. See LICENSE for details.
"""In-game UI automation helpers for the opt-in FIFO control channel.

.. warning::

   **Unstable, unsupported API.** May change or be removed without
   notice. No backward-compatibility guarantees across versions.
   Use at your own risk.

Companion to :mod:`babase._automation`. Holds the helpers that drive
the live widget tree — press/scroll by id or label, wait for widgets,
inspect / dump widgets. These live here rather than in babase
because they reach into ``bauiv1``, which isn't present in base-only
spinoffs.

Gating is the same as the babase side (compile-time
``BA_ENABLE_AUTOMATION``; runtime ``BA_AUTOMATION_FIFO``); emission
format is identical (``[automation] <tag> <status> <payload>`` via
``ba.app``). The :func:`inspect` helper here bridges back to
:func:`babase._automation.screenshot`.
"""

from __future__ import annotations

import babase
import _bauiv1

from babase._automation import _badev, _emit, _evaluate_lstr_json, screenshot

# Toolbar special-widget names exposed by ``bauiv1.get_special_widget``.
# Enumerated here so automation can reach buttons outside the main-window
# subtree (account, settings, store, chests, etc.). Keep in sync with the
# list in python_methods_ui_v1.cc (PyGetSpecialWidget docstring).
_SPECIAL_WIDGET_NAMES = (
    'squad_button',
    'back_button',
    'menu_button',
    'account_button',
    'achievements_button',
    'settings_button',
    'inbox_button',
    'store_button',
    'get_tokens_button',
    'inventory_button',
    'tickets_meter',
    'tokens_meter',
    'trophy_meter',
    'level_meter',
    'overlay_stack',
    'chest_0_button',
    'chest_1_button',
    'chest_2_button',
    'chest_3_button',
)


def _bauiv1_screen_virtual_size() -> tuple[float, float]:
    """Pull the current virtual screen size from babase."""
    sz = babase.get_virtual_screen_size()
    return float(sz[0]), float(sz[1])


def _click_widget(widget: object, tag: str, label: str) -> None:
    """Synthesize a click at the screen-space center of the given widget.

    Emits ``[automation] <tag> fail not_compiled_in`` when the build
    was made without ``BA_ENABLE_AUTOMATION``.
    """
    if not hasattr(_badev, 'automation_press_at_virtual'):
        _emit(tag, 'fail', 'not_compiled_in')
        return
    cx, cy = widget.get_screen_space_center()  # type: ignore[attr-defined]
    # get_screen_space_center returns coords relative to screen *center*;
    # convert to absolute virtual coords.
    sw_value, sh_value = _bauiv1_screen_virtual_size()
    vx = cx + sw_value * 0.5
    vy = cy + sh_value * 0.5
    _badev.automation_press_at_virtual(button=1, x=vx, y=vy)
    _emit(tag, 'ok', f'{label} @ {vx:.0f},{vy:.0f}')


def press_by_id(widget_id: str, tag: str = 'press') -> None:
    """Click the (first) widget with the given string ID.

    Fails the operation (``[automation] <tag> fail no_widget:<id>``)
    if no widget with the ID is currently in the UI tree. Note that
    not every widget in the codebase has an ID — for those, use
    :func:`press_by_label` or add an ``id=`` to the widget's
    construction site.
    """
    w = _bauiv1.widget_by_id(widget_id)
    if w is None:
        _emit(tag, 'fail', f'no_widget:{widget_id}')
        return
    _click_widget(w, tag, widget_id)


def press_by_label(label_text: str, tag: str = 'press') -> None:
    """Click the button visually represented by a label.

    Walks the live widget tree for textwidgets whose visible text
    matches ``label_text``. For each match, follows the textwidget's
    ``draw_controller`` link (set by UI code that overlays a label
    textwidget on top of a buttonwidget) to find the underlying
    buttonwidget. Presses that.

    Falls back to clicking the textwidget directly if no
    draw_controller is set — useful for actually-clickable
    textwidgets (rare but possible).

    Fails with:
      * ``no_label:<text>`` — no textwidget with that text exists.
      * ``ambiguous_label:<text> count=N`` — multiple textwidgets
        match. Use :func:`dump_widgets` to disambiguate, or use
        :func:`press_by_id` instead.

    For ambiguity-resolution we could later add label+location
    or label+container filters, but exact-match is simplest for now.
    """
    candidates = _find_widgets(
        predicate=lambda w: _label_text(w) == label_text,
    )
    if not candidates:
        _emit(tag, 'fail', f'no_label:{label_text!r}')
        return

    # Resolve each textwidget candidate to its draw_controller (the
    # actual underlying button to press) where one exists. Textwidgets
    # without a draw_controller fall back to themselves.
    resolved: list[tuple[object, str]] = []
    for tw in candidates:
        dc = getattr(tw, 'draw_controller', None)
        if dc is not None:
            resolved.append((dc, 'via draw_controller'))
        else:
            resolved.append((tw, 'no draw_controller; pressing label'))

    # De-dup by widget identity (multiple textwidgets pointing at the
    # same button — e.g. main label + subtitle — should resolve to a
    # single press target).
    unique: list[tuple[object, str]] = []
    seen_ids: set[int] = set()
    for w, how in resolved:
        if id(w) in seen_ids:
            continue
        seen_ids.add(id(w))
        unique.append((w, how))

    if len(unique) > 1:
        _emit(
            tag,
            'fail',
            f'ambiguous_label:{label_text!r} count={len(unique)}',
        )
        return
    target, how = unique[0]
    _click_widget(target, tag, f'label:{label_text!r} ({how})')


def scroll_by_id(
    widget_id: str,
    dx: float = 0.0,
    dy: float = 0.0,
    *,
    tag: str = 'scroll',
) -> None:
    """Scroll at the screen-center of the widget with the given ID.

    Convenience wrapper that positions the synthetic cursor over the
    given widget's center before issuing the wheel event — useful when
    the thing you want to scroll has an ID (e.g. a named scrollwidget
    or a container row) and you want the event routed to it
    regardless of current selection.

    Emits ``[automation] <tag> fail not_compiled_in`` when the build
    was made without ``BA_ENABLE_AUTOMATION``.
    """
    w = _bauiv1.widget_by_id(widget_id)
    if w is None:
        _emit(tag, 'fail', f'no_widget:{widget_id}')
        return
    if not hasattr(_badev, 'automation_scroll_at_virtual'):
        _emit(tag, 'fail', 'not_compiled_in')
        return
    cx, cy = w.get_screen_space_center()
    sw_value, sh_value = _bauiv1_screen_virtual_size()
    vx = cx + sw_value * 0.5
    vy = cy + sh_value * 0.5
    _badev.automation_scroll_at_virtual(x=vx, y=vy, dx=dx, dy=dy)
    _emit(
        tag,
        'ok',
        f'{widget_id} @ {vx:.0f},{vy:.0f} d=({dx:+.2f},{dy:+.2f})',
    )


def wait_for_widget(
    widget_id: str | None = None,
    label_text: str | None = None,
    timeout_seconds: float = 5.0,
    tag: str = 'wait',
) -> None:
    """Poll until a matching widget appears, or timeout.

    Specify exactly one of ``widget_id`` or ``label_text``. Emits
    ``ok`` once found (with elapsed time), ``fail`` after timeout.
    Polls every 100 ms via apptimer; non-blocking.
    """
    if (widget_id is None) == (label_text is None):
        _emit(tag, 'fail', 'specify_one_of:widget_id|label_text')
        return

    import time

    start = time.monotonic()

    def _check() -> None:
        if widget_id is not None:
            found = _bauiv1.widget_by_id(widget_id) is not None
            ident = f'id:{widget_id}'
        else:
            found = bool(
                _find_widgets(predicate=lambda w: _label_text(w) == label_text)
            )
            ident = f'label:{label_text!r}'

        elapsed = time.monotonic() - start
        if found:
            _emit(tag, 'ok', f'{ident} after {elapsed:.2f}s')
        elif elapsed >= timeout_seconds:
            _emit(tag, 'fail', f'timeout {ident} after {elapsed:.2f}s')
        else:
            babase.apptimer(0.1, _check)

    _check()


def inspect(tag: str = 'inspect') -> None:
    """Capture current UI state for analysis.

    Shorthand for "I'm about to do something and want to see what's
    on screen right now." Fires in order:

    1. A screenshot to ``<silo>/screenshots/<tag>.png``.
    2. A widget-tree dump tagged ``<tag>_widgets``.

    Typical usage before writing an automation sequence:

    >>> auto.inspect()
    # Look at the screenshot and widget dump to find the right
    # IDs or labels to drive the next step.

    The screenshot filename uses the tag so calling ``inspect`` with
    different tags through a session produces a labeled history
    (``inspect.png``, ``after_signin.png``, etc.).
    """
    screenshot(f'{tag}.png', tag=tag)
    dump_widgets(tag=f'{tag}_widgets')


def dump_widgets(
    tag: str = 'dump',
    *,
    show_no_id: bool = True,
) -> None:
    """Walk the widget tree and log a summary line for each widget.

    Each widget gets one log line of the form
    ``[automation] <tag> entry <type> id=<id-or-->
    label=<repr-of-label> @ <x>,<y> sz=<w>x<h>``,
    followed by a final ``[automation] <tag> ok count=<n>`` line.

    Useful for discovering which widgets exist on screen and what IDs
    or labels they have, so you can write further automation steps.
    """
    widgets = _find_widgets(predicate=lambda w: True)
    count = 0
    for w in widgets:
        wid = _widget_id(w)
        if not show_no_id and not wid:
            continue
        wtype = type(w).__name__
        # Best-effort label extraction (only buttonwidgets / textwidgets
        # have one).
        label = _label_text(w)
        try:
            cx, cy = w.get_screen_space_center()  # type: ignore[attr-defined]
        except Exception:  # pylint: disable=broad-except
            cx = cy = 0.0
        try:
            sx, sy = w.get_size()  # type: ignore[attr-defined]
        except Exception:  # pylint: disable=broad-except
            sx = sy = 0.0
        wid_disp = repr(wid or '-')
        _emit(
            tag,
            'entry',
            f'{wtype} id={wid_disp} label={label!r}'
            f' @ {cx:.0f},{cy:.0f} sz={sx:.0f}x{sy:.0f}',
        )
        count += 1
    _emit(tag, 'ok', f'count={count}')


# ---------------------------- internal helpers -----------------------------


def _widget_id(widget: object) -> str:
    """Return a widget's string ID, or empty string if unset."""
    try:
        return str(widget.id)  # type: ignore[attr-defined]
    except Exception:  # pylint: disable=broad-except
        return ''


def _label_text(widget: object) -> str:
    """Best-effort extraction of a widget's visible text.

    Tries ``bui.textwidget(query=widget)`` first, which works for any
    widget that's actually a TextWidget. Returns empty string for
    widgets that aren't textwidgets (the query raises) — including
    ButtonWidgets, whose visible labels typically live in a separate
    overlaid TextWidget (with ``draw_controller`` pointing back to
    the button).

    If the raw text is a JSON-encoded ``Lstr`` (the common case for
    localized labels — they look like ``{"r":"someResourceKey"}``),
    we evaluate it to its translated form so callers can match
    against display text rather than the JSON blob.
    """
    try:
        # Cast through Any since we accept opaque widget refs.
        raw = str(_bauiv1.textwidget(query=widget))  # type: ignore[arg-type]
    except Exception:  # pylint: disable=broad-except
        return ''
    if raw.startswith('{') and raw.endswith('}'):
        try:
            return _evaluate_lstr_json(raw)
        except Exception:  # pylint: disable=broad-except
            return raw
    return raw


def _find_widgets(predicate: object) -> list[object]:
    """Walk the live widget tree from the root and return matches.

    ``predicate`` is a single-arg callable returning True for widgets
    to include. Recurses from two entry points:

    * The current main-window's root widget (primary UI).
    * Each toolbar special widget (account/settings/store/etc.) —
      these live outside the main-window subtree but are where many
      "always visible" buttons live (sign-in/out, overlay popups).

    ``overlay_stack`` is the parent of transient popups (dialogs,
    confirmation windows, the keyboard), so walking it picks up
    modal content too.

    Widgets are de-duplicated by identity since an ``overlay_stack``
    walk may re-reach content reachable via other roots.
    """
    roots: list[object] = []
    main_window = babase.app.ui_v1.get_main_window()
    if main_window is not None:
        try:
            roots.append(main_window.get_root_widget())
        except Exception:  # pylint: disable=broad-except
            pass
    for name in _SPECIAL_WIDGET_NAMES:
        try:
            sw = _bauiv1.get_special_widget(name)  # type: ignore[arg-type]
        except Exception:  # pylint: disable=broad-except
            continue
        if sw is not None:
            roots.append(sw)

    out: list[object] = []
    seen: set[int] = set()
    stack: list[object] = list(roots)
    while stack:
        w = stack.pop()
        if id(w) in seen:
            continue
        seen.add(id(w))
        try:
            if predicate(w):  # type: ignore[operator]
                out.append(w)
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            children = w.get_children()  # type: ignore[attr-defined]
        except Exception:  # pylint: disable=broad-except
            children = []
        stack.extend(children)
    return out
