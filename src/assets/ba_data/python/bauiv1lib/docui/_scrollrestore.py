# Released under the MIT License. See LICENSE for details.
#
"""Saving and restoring where a doc-ui window's content is scrolled."""

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import bauiv1

#: Where each of a window's scrolling widgets is scrolled to, keyed as
#: :func:`page_scrollers` keys them; values are
#: :meth:`bauiv1.Widget.get_scroll_state` tuples.
type ScrollSnapshot = dict[str, tuple[float, float, float]]

#: How a rebuild relates to what was shown before it; see
#: :func:`apply_scroll`.
type ScrollRestoreMode = Literal['same_page', 'new_page', 'returning', 'reflow']


def page_scrollers(
    scrollwidget: bauiv1.Widget, subcontainer: bauiv1.Widget | None
) -> dict[str, bauiv1.Widget]:
    """A window's scrolling widgets, keyed for save/restore.

    'page' is the window's own scroll-widget; each button row's h-scroll
    is keyed by its order on the page ('row0', 'row1', ...). Order is
    only a guess at identity -- :func:`apply_scroll` also requires a
    widget's extents to match before trusting a saved offset.

    :meta private:
    """
    out = {'page': scrollwidget}
    if subcontainer:
        rows = [
            w
            for w in subcontainer.get_children()
            if w.get_widget_type() == 'hscroll'
        ]
        for i, row in enumerate(rows):
            out[f'row{i}'] = row
    return out


def capture_scroll(scrollers: dict[str, bauiv1.Widget]) -> ScrollSnapshot:
    """Where each of the given scrolling widgets is scrolled to.

    :meta private:
    """
    out: ScrollSnapshot = {}
    for key, widget in scrollers.items():
        state = widget.get_scroll_state()
        if state is not None:
            out[key] = state
    return out


def apply_scroll(
    scrollers: dict[str, bauiv1.Widget],
    saved: ScrollSnapshot | None,
    *,
    mode: ScrollRestoreMode,
) -> list[bauiv1.Widget]:
    """Put freshly built ui back where ``saved`` says it was.

    Rows are rebuilt from scratch, so without this each would start
    from its left end and restoring selection would then drag the
    selected button just into view -- visibly jumping a row the user
    had scrolled. A saved offset is applied to a scroller only if its
    content and visible extents both match exactly, which is what makes
    key-by-order safe: a row that changed shape simply keeps its
    default.

    Modes:

    - ``'same_page'`` (a rebuild of the page being shown): rows as
      above; the window's own scroll-widget, which outlives its
      contents, holds its position even if the page changed size --
      snapped, rather than left to glide as it clamps.
    - ``'new_page'`` (a different page replaced it): nothing carries
      over; the scroll-widget snaps to the top.
    - ``'returning'`` (a window coming back via back-navigation,
      ``saved`` being where it was left): everything as rows are.
    - ``'reflow'`` (a window recreated for a new screen size or ui
      scale): as ``'same_page'``, except the page counts as put back
      even though its extents changed. The reflowed page is where the
      user left it, as near as it can be, and that should win over
      scrolling a restored selection into view -- a selection the user
      had scrolled away from would otherwise yank the page back to it.

    Returns the scrollers put back exactly (offset applied, extents
    matching). This runs before selection restore; a restored
    selection inside only those is back where it was, so needn't be
    scrolled to (whose show buffers would otherwise nudge a selection
    near an edge toward the center).

    :meta private:
    """
    restored: list[bauiv1.Widget] = []
    for key, widget in scrollers.items():
        if mode == 'new_page':
            if key == 'page':
                widget.set_scroll_offset(0.0)
            continue
        prev = None if saved is None else saved.get(key)
        if prev is None:
            continue
        current = widget.get_scroll_state()
        matches = current is not None and current[1:] == prev[1:]
        if key == 'page' and mode in ('same_page', 'reflow'):
            # Held even if the page changed size, but only exact if it
            # didn't (content may have moved otherwise) -- unless this
            # is a reflow, where near enough is the point.
            widget.set_scroll_offset(prev[0])
            if matches or mode == 'reflow':
                restored.append(widget)
            continue
        if matches:
            widget.set_scroll_offset(prev[0])
            restored.append(widget)
    return restored


def containing_scrollers(
    scrollers: dict[str, bauiv1.Widget],
    subcontainer: bauiv1.Widget | None,
    widget: bauiv1.Widget,
) -> list[bauiv1.Widget]:
    """The scrolling widgets (of ``scrollers``) that ``widget`` sits in.

    Button-row buttons live in their row's h-scroll (via its
    sub-container) as well as the page's scroll-widget; control-row
    controls sit straight in the page content. Anything else (the back
    button, say) sits in none.

    :meta private:
    """
    if not subcontainer:
        return []
    page = scrollers['page']
    for key, scroller in scrollers.items():
        if key == 'page':
            continue
        for hsub in scroller.get_children():
            if any(child is widget for child in hsub.get_children()):
                return [page, scroller]
    if any(child is widget for child in subcontainer.get_children()):
        return [page]
    return []
