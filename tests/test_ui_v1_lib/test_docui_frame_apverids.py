# Released under the MIT License. See LICENSE for details.
#
"""Testing that a frame's asset packages get collected for resolve.

Lives with ui_v1_lib rather than bacommon because the walkers under
test are the client's (``bauiv1lib.docui``, owned by the ui_v1_lib
feature set). A featureset owns ``tests/test_<its name>``, so a spinoff
that omits ui_v1_lib drops these along with the code they cover --
which a bacommon-placed (or ui_v1-placed; that broke the ui_v1-only
spinoff test) home would not have done.

A frame carries a depiction the client did not author, so its children
can reference *any* asset-package -- that is the whole point of frames,
and it is why nothing about the depiction may assume a particular
package. The client resolves every package a page references before
rendering it, which only works if the walk that gathers them descends
into frames.
"""

import importlib.util

import pytest

import bacommon.docui.v2 as dui2
from bacommon.assetspec import TextureSpec
from bacommon.langstr import LangStrSpecValue

# Importing the client's resolve module pulls in bauiv1 -> babase ->
# _babase, the engine's binary module. That is present wherever the
# engine has been built (and where dummy-modules stand in for it), but
# not on CI legs that only run the test suite -- public Windows CI
# being the one that caught this. Skip there rather than fail: the
# walk itself is covered engine-free in test_bacommon/test_docui_walk,
# and what these add is that the *client's* gatherer descends the same
# way.
pytestmark = pytest.mark.skipif(
    importlib.util.find_spec('_babase') is None,
    reason='client ui modules need the engine binary module',
)

#: A package nothing else in the page mentions, so a walk that misses
#: frames comes back without it.
OTHERPKG = 'a-0.someotherpackage.999999'


def _image(pkg: str = OTHERPKG) -> dui2.Image:
    return dui2.Image(
        texture=TextureSpec(pkg, 'textures/whatever'),
        position=(0.0, 0.0),
        size=(1.0, 1.0),
    )


def _page(decorations: list[dui2.Decoration]) -> dui2.Page:
    return dui2.Page(
        title=LangStrSpecValue.literal('t'),
        rows=[
            dui2.ButtonRow(
                buttons=[dui2.Button(size=(1, 1), decorations=decorations)]
            )
        ],
    )


def _collect(page: dui2.Page) -> set[str]:
    """Gather apverids the way the client does before rendering."""
    from bauiv1lib.docui._resolve import collect_apverids

    acc: set[str] = set()
    collect_apverids(page, acc)
    return acc


def test_bare_image_is_collected() -> None:
    """Baseline: a loose image's package is gathered."""
    assert OTHERPKG in _collect(_page([_image()]))


def test_image_inside_frame_is_collected() -> None:
    """A frame's children count too, or their assets never resolve."""
    frame = dui2.Frame(decorations=[_image()], position=(0.0, 0.0))
    assert OTHERPKG in _collect(_page([frame]))


def test_image_inside_nested_frame_is_collected() -> None:
    """Frames nest, so the walk has to recurse rather than peek once."""
    inner = dui2.Frame(decorations=[_image()], position=(0.0, 0.0))
    outer = dui2.Frame(decorations=[inner], position=(0.0, 0.0))
    assert OTHERPKG in _collect(_page([outer]))


def test_sized_frame_children_are_collected() -> None:
    """Fitting does not change what a frame references."""
    frame = dui2.Frame(
        decorations=[_image()], position=(0.0, 0.0), size=(10.0, 10.0)
    )
    assert OTHERPKG in _collect(_page([frame]))


def test_frame_langstrs_are_yielded() -> None:
    """Text inside a frame is a language-string slot like any other."""
    from bauiv1lib.docui._resolve import page_langstrs

    text = dui2.Text(
        text=LangStrSpecValue.literal('inside'),
        position=(0.0, 0.0),
        size=(0.0, 0.0),
    )
    frame = dui2.Frame(decorations=[text], position=(0.0, 0.0))
    found = list(page_langstrs(_page([frame])))
    assert text.text in found
