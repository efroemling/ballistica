# Released under the MIT License. See LICENSE for details.
"""Functionality related to prepping a doc-ui page for display.

Consumes native (v2 / language-agnostic) doc-ui documents: text rides
as :class:`bacommon.langstr.LangStrSpec` (handed to widgets as native
handles that re-evaluate on language changes) and assets as typed refs.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

from bauiv1lib.docui.prep._types import (
    DecorationPrep,
    MenuPrep,
    ButtonPrep,
    ButtonControlPrep,
    CheckboxPrep,
    TextInputPrep,
    ChoicePrep,
    ColorPrep,
    SliderPrep,
    NumberPrep,
    RowPrep,
    PagePrep,
)
from bauiv1lib.docui.prep._calls import prep_page
from bauiv1lib.docui.prep._decorations import (
    instantiate_decorations,
    prep_decorations_for_container,
)
from bauiv1lib.docui.prep._instantiate import instantiate_page_prep
from bauiv1lib.docui.prep._calls2 import (
    prep_text,
    prep_decorations,
    prep_image,
    prep_row_debug,
    prep_row_debug_button,
    prep_button_debug,
)

__all__ = [
    'DecorationPrep',
    'MenuPrep',
    'ButtonPrep',
    'ButtonControlPrep',
    'CheckboxPrep',
    'TextInputPrep',
    'ChoicePrep',
    'ColorPrep',
    'SliderPrep',
    'NumberPrep',
    'RowPrep',
    'PagePrep',
    'prep_page',
    'instantiate_page_prep',
    'instantiate_decorations',
    'prep_decorations_for_container',
    'prep_text',
    'prep_decorations',
    'prep_image',
    'prep_row_debug',
    'prep_row_debug_button',
    'prep_button_debug',
]
