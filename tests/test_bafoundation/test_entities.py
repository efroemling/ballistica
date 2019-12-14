# Copyright (c) 2011-2019 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Testing tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Sequence

from efrotools.statictest import static_type_equals

if TYPE_CHECKING:
    pass


def inc(x: int) -> int:
    """Testing inc."""
    return x + 1


def test_answer() -> None:
    """Testing answer."""
    fooval: List[int] = [3, 4]
    assert static_type_equals(fooval[0], int)
    assert static_type_equals(fooval, List[int])
    somevar: Sequence[int] = []
    assert static_type_equals(somevar, Sequence[int])
    assert isinstance(fooval, list)
    assert inc(3) == 4


def test_answer2() -> None:
    """Testing answer."""
    assert inc(3) == 4
