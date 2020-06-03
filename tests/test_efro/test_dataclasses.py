# Copyright (c) 2011-2020 Eric Froemling
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
"""Testing dataclasses functionality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

from efro.dataclasses import dataclass_assign, dataclass_validate

if TYPE_CHECKING:
    from typing import Optional, List


def test_assign() -> None:
    """Testing various assignments."""
    # pylint: disable=too-many-statements

    @dataclass
    class _TestClass:
        ival: int = 0
        sval: str = ''
        bval: bool = True
        fval: float = 1.0
        oival: Optional[int] = None
        osval: Optional[str] = None
        obval: Optional[bool] = None
        ofval: Optional[float] = None
        lsval: List[str] = field(default_factory=list)
        lival: List[int] = field(default_factory=list)
        lbval: List[bool] = field(default_factory=list)
        lfval: List[float] = field(default_factory=list)

    tclass = _TestClass()

    class _TestClass2:
        pass

    tclass2 = _TestClass2()

    # Arg types:
    with pytest.raises(TypeError):
        dataclass_assign(tclass2, {})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, [])  # type: ignore

    # Invalid attrs.
    with pytest.raises(AttributeError):
        dataclass_assign(tclass, {'nonexistent': 'foo'})

    # Correct types.
    dataclass_assign(
        tclass, {
            'ival': 1,
            'sval': 'foo',
            'bval': True,
            'fval': 2.0,
            'lsval': ['foo'],
            'lival': [10],
            'lbval': [False],
            'lfval': [1.0]
        })
    dataclass_assign(
        tclass, {
            'oival': None,
            'osval': None,
            'obval': None,
            'ofval': None,
            'lsval': [],
            'lival': [],
            'lbval': [],
            'lfval': []
        })
    dataclass_assign(
        tclass, {
            'oival': 1,
            'osval': 'foo',
            'obval': True,
            'ofval': 2.0,
            'lsval': ['foo', 'bar', 'eep'],
            'lival': [10, 11, 12],
            'lbval': [False, True],
            'lfval': [1.0, 2.0, 3.0]
        })

    # Type mismatches.
    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'ival': 'foo'})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'sval': 1})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'bval': 2})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'oival': 'foo'})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'osval': 1})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'obval': 2})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'ofval': 'blah'})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'lsval': 'blah'})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'lsval': [1]})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'lbval': [None]})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'lival': ['foo']})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'lfval': [True]})

    # More subtle ones (we currently require EXACT type matches)
    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'ival': True})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'fval': 2})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'bval': 1})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'ofval': 1})

    with pytest.raises(TypeError):
        dataclass_assign(tclass, {'lfval': [1]})


# noinspection PyTypeHints
def test_validate() -> None:
    """Testing validation."""

    @dataclass
    class _TestClass:
        ival: int = 0
        sval: str = ''
        bval: bool = True
        fval: float = 1.0
        oival: Optional[int] = None
        osval: Optional[str] = None
        obval: Optional[bool] = None
        ofval: Optional[float] = None

    # Should pass by default.
    tclass = _TestClass()
    dataclass_validate(tclass)

    # No longer valid.
    tclass.fval = 1
    with pytest.raises(TypeError):
        dataclass_validate(tclass)

    # Should pass by default.
    tclass = _TestClass()
    dataclass_validate(tclass)

    # No longer valid.
    tclass.ival = None  # type: ignore
    with pytest.raises(TypeError):
        dataclass_validate(tclass)
