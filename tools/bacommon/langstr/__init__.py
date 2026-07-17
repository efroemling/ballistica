# Released under the MIT License. See LICENSE for details.
#
"""Language-agnostic complex strings -- the ``LangStr`` runtime model.

Pure-Python prototype of the language-string-context system (see
``docs/initiatives/language-string-context.md`` in ballistica-internal). The
C++ ``LangStr`` is a later optimized port of this proven model.

``LangStr`` is the name for this whole new generation of string handling
(formerly working-titled ``Lstr2``); the legacy client translation class
keeps the ``Lstr`` name, which stays reserved for it to avoid ambiguity.

The model lets us pass around minimal, language-independent representations
of a complex string (substitutions, plurals, nesting) and resolve to a flat
string in a particular language only at display -- so one representation
serves clients of any language.
"""

from bacommon.langstr._core import (
    LangStr,
    LangStrResource,
    LangStrValue,
    LangStrResourceIndexed,
    LangStrTypeID,
    LANGSTR_EXT_MIN_BUILD,
    MAX_NESTING_DEPTH,
    StringDef,
    PackageDef,
    PackageStructure,
    LanguageStringEncodeContext,
    LanguageStringDecodeContext,
    LanguageStringNameDecodeContext,
    LangStrError,
    EncodedLangStr,
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
    'LangStr',
    'LangStrResource',
    'LangStrValue',
    'LangStrResourceIndexed',
    'LangStrTypeID',
    'LANGSTR_EXT_MIN_BUILD',
    'MAX_NESTING_DEPTH',
    'StringDef',
    'PackageDef',
    'PackageStructure',
    'LanguageStringEncodeContext',
    'LanguageStringDecodeContext',
    'LanguageStringNameDecodeContext',
    'LangStrError',
    'EncodedLangStr',
    'LangStrDir',
    'WrapperTree',
    'package_structure',
    'serialize_language_blob',
    'parse_language_blob',
    'LANGUAGE_BLOB_STRINGS_KEY',
]
