# Released under the MIT License. See LICENSE for details.
#
"""Language-agnostic complex strings -- the ``Lstr2`` runtime model.

Pure-Python prototype of the language-string-context system (see
``docs/initiatives/language-string-context.md`` in ballistica-internal). The
C++ ``Lstr2`` is a later optimized port of this proven model.

The model lets us pass around minimal, language-independent representations
of a complex string (substitutions, plurals, nesting) and resolve to a flat
string in a particular language only at display -- so one representation
serves clients of any language.
"""

from bacommon.langstr._core import (
    Lstr,
    StringDef,
    PackageDef,
    PackageStructure,
    LanguageStringEncodeContext,
    LanguageStringDecodeContext,
    LanguageStringNameDecodeContext,
    LangStrError,
    EncodedLstr,
)
from bacommon.langstr._wrapper import (
    LangStrDir,
    WrapperTree,
    package_structure,
)
from bacommon.langstr._blob import (
    serialize_language_blob,
    parse_language_blob,
    LANGUAGE_BLOB_STRINGS_KEY,
)

__all__ = [
    'Lstr',
    'StringDef',
    'PackageDef',
    'PackageStructure',
    'LanguageStringEncodeContext',
    'LanguageStringDecodeContext',
    'LanguageStringNameDecodeContext',
    'LangStrError',
    'EncodedLstr',
    'LangStrDir',
    'WrapperTree',
    'package_structure',
    'serialize_language_blob',
    'parse_language_blob',
    'LANGUAGE_BLOB_STRINGS_KEY',
]
