# Released under the MIT License. See LICENSE for details.
#
"""Language-agnostic complex strings -- the ``LangStrSpec`` authoring model.

"LangStr" is the name for this whole generation of string handling
(formerly working-titled ``Lstr2``); the legacy client translation class
keeps the ``Lstr`` name, which stays reserved for it to avoid ambiguity.
Within that generation the type split is semantic (see
``strings-asset-migration.md`` D28 in ballistica-internal):

- ``LangStrSpec`` (here) is the *authoring spec* form -- a claim about a
  string carrying no guarantee that its asset-package is locally present
  (or even still exists). This is the currency for authoring surfaces and
  wire/model dataclasses; consuming ends verify/resolve before display.
- The native client ``babase.LangStr`` (a later optimized C++ port of
  this proven model) represents a *verified-local* string -- holding one
  implies it is displayable there. Its ``.spec`` property projects back
  to this form (always valid); there is deliberately no public
  unverified->verified conversion.

The model lets us pass around minimal, language-independent representations
of a complex string (substitutions, plurals, nesting) and resolve to a flat
string in a particular language only at display -- so one representation
serves clients of any language.
"""

from bacommon.langstr._core import (
    LangStrSpec,
    WrapParams,
    LangStrSpecResource,
    LangStrSpecValue,
    LangStrSpecResourceIndexed,
    LangStrSpecTypeID,
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
    contains_resource_form,
    collect_apverids,
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
    'LangStrSpec',
    'WrapParams',
    'LangStrSpecResource',
    'LangStrSpecValue',
    'LangStrSpecResourceIndexed',
    'LangStrSpecTypeID',
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
    'contains_resource_form',
    'collect_apverids',
    'LangStrDir',
    'WrapperTree',
    'package_structure',
    'serialize_language_blob',
    'parse_language_blob',
    'LANGUAGE_BLOB_STRINGS_KEY',
]
