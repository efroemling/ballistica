# Released under the MIT License. See LICENSE for details.
#
"""Tests for efro.util."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any

FAST_MODE = os.environ.get('EFRO_TEST_FAST_MODE') == '1'


def test_do_once() -> None:
    """Test do_once() fires exactly on the requested iteration."""
    from efro.util import do_once

    # Default (on_iteration=1): True only on the first call.
    results = [do_once() for _ in range(5)]
    assert results == [True, False, False, False, False]

    # on_iteration=3: True only on the third call.
    results2 = [do_once(on_iteration=3) for _ in range(5)]
    assert results2 == [False, False, True, False, False]


def test_do_once_periodically_threshold() -> None:
    """Test do_once_periodically() fires on the right iteration (no sleep)."""
    from efro.util import do_once_periodically

    # on_iteration=2: True only on the second call within the period.
    results = [do_once_periodically(on_iteration=2) for _ in range(5)]
    assert results == [False, True, False, False, False]


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_do_once_periodically_reset() -> None:
    """Test do_once_periodically() count resets after period expires."""
    import time
    from datetime import timedelta
    from efro.util import do_once_periodically

    def call(**kwargs: Any) -> bool:
        return do_once_periodically(**kwargs)  # stable call site

    td = timedelta(seconds=0.05)
    assert not call(on_iteration=2, period=td)  # count=1, False
    assert call(on_iteration=2, period=td)  # count=2, True
    assert not call(on_iteration=2, period=td)  # count=3, False

    time.sleep(0.06)  # let the slice boundary pass

    assert not call(on_iteration=2, period=td)  # count reset to 1, False
    assert call(on_iteration=2, period=td)  # count=2, True again


def test_strip_exception_tracebacks_exception_group() -> None:
    """Tracebacks should be stripped from ExceptionGroup children."""
    from efro.util import strip_exception_tracebacks

    children: list[Exception] = []
    for i in range(3):
        try:
            raise ValueError(f'child {i}')
        except ValueError as exc:
            children.append(exc)

    try:
        raise ExceptionGroup('group', children)
    except ExceptionGroup as group:
        strip_exception_tracebacks(group)
        assert group.__traceback__ is None
        for child in group.exceptions:
            assert child.__traceback__ is None


def test_strip_exception_tracebacks_breaks_reference_cycle() -> None:
    """Without strip, the exc/tb/frame/locals cycle survives refcount.

    The cycle is: ``holder -> exc -> __traceback__ -> tb_frame ->
    f_localsplus['holder'] -> holder``. PEP 3134 auto-clears the
    ``as exc:`` binding at except-exit but not the parameter, so
    the frame keeps a back-reference to the holder.
    """
    import gc
    import weakref
    from efro.util import strip_exception_tracebacks

    class _Holder:
        exc: BaseException | None = None

    def _build(holder: _Holder, *, strip: bool) -> None:
        try:
            raise ValueError('x')
        except ValueError as exc:
            holder.exc = exc
            if strip:
                strip_exception_tracebacks(exc)

    was_enabled = gc.isenabled()
    gc.disable()
    try:
        # Without strip: cycle keeps the holder alive past refcount
        # drop; only cyclic GC reclaims it.
        h1 = _Holder()
        _build(h1, strip=False)
        ref1 = weakref.ref(h1)
        del h1
        assert ref1() is not None, 'cycle should keep holder alive'
        gc.collect()
        assert ref1() is None, 'cyclic GC should reclaim the cycle'

        # With strip: no cycle; refcount alone reclaims it.
        h2 = _Holder()
        _build(h2, strip=True)
        ref2 = weakref.ref(h2)
        del h2
        assert ref2() is None, 'strip should let refcount reclaim it'
    finally:
        if was_enabled:
            gc.enable()


def test_strip_exception_tracebacks_nested_group() -> None:
    """Strip should recurse into nested ExceptionGroups."""
    from efro.util import strip_exception_tracebacks

    try:
        raise ValueError('leaf')
    except ValueError as leaf:
        inner = ExceptionGroup('inner', [leaf])
        try:
            raise ExceptionGroup('outer', [inner]) from leaf
        except ExceptionGroup as outer:
            strip_exception_tracebacks(outer)
            assert outer.__traceback__ is None
            assert inner.__traceback__ is None
            assert leaf.__traceback__ is None
