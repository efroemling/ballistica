# Released under the MIT License. See LICENSE for details.
#
"""Localized-text evaluation (structured plural/select + substitutions).

The value delivered for a locale is either a plain ``str`` or a
:class:`StringSelector`. :func:`evaluate` resolves either against a locale
and caller-supplied arguments to a final ``str``:

* A plain ``str`` has its ``{name}`` placeholders replaced by
  ``str(args['name'])``.
* A :class:`StringSelector` picks one *leaf* string at render time -- by
  CLDR plural category of an integer arg (``kind=PLURAL``) or by the string
  value of an arg (``kind=SELECT``) -- then substitutes ``{name}`` and (for
  plurals) ``#`` (the count) in the chosen leaf.

We use our own small structured form rather than parsing a message-format
string: the runtime decisions are few and closed, the data is
self-describing (it can only express what we support), and a struct is far
safer to port than a hand-rolled string parser. This is the prototype of
the native ``Lstr2`` runtime -- keeping it in ``bacommon`` gives pure-Python
consumers (the client's embedded Python, server-side resolution in
bamaster/basn) the same evaluator, and the :class:`StringSelector`
``IOAttrs`` keys are the on-the-wire schema the C++ port implements.

Scope: cardinal plural selection for non-negative integers, string
``select``, ``{name}`` substitution, and ``#`` for the plural count.
``=N`` keys match an exact count before the category rule. Not (yet):
ordinals/selectordinal, decimal operands, plural offsets, nested selectors.
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs
from bacommon.locale import Locale

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

#: A ``{name}`` substitution placeholder (lowercase snake_case arg name).
_SUB_RE = re.compile(r'\{([a-z][a-z0-9_]*)\}')


class PluralCategory(Enum):
    """A CLDR plural category."""

    ZERO = 'zero'
    ONE = 'one'
    TWO = 'two'
    FEW = 'few'
    MANY = 'many'
    OTHER = 'other'


# --- CLDR cardinal plural rules (integer-only) -----------------------------
#
# Scope: cardinal selection for NON-NEGATIVE INTEGER counts ("3 boxes",
# "1 kill") -- the only case the string system needs. For an integer every
# CLDR fraction operand (v/w/f/t) is zero, so each rule collapses to a
# function of n alone (with n % 10 / n % 100). Decimals, ordinals
# (``selectordinal``), and compact/scientific are intentionally
# unsupported.
#
# These compact functions are cross-checked against ICU's authoritative
# ``PluralRules`` for every shipped locale by the producer-side
# ``test_loctext_cldr`` test (where ``pyicu`` lives) -- so this table is
# provably CLDR-correct for integers without carrying any CLDR data or a
# rule-expression parser at runtime, and it ports trivially to the native
# ``Lstr2``.
#
# One deliberate gap, bounded above 1,000,000: a handful of West-European
# locales (es/it/pt/fr/vec) put EXACT millions in a distinct ``many`` form
# (e.g. Spanish "un millón DE puntos"). We don't model that -- counts at or
# above 1,000,000 in those locales get ``other`` where CLDR says ``many``.
# Adding it later is a one-line ``n % 1_000_000 == 0`` clause plus widening
# the cross-check range; it's omitted now since game counts stay well below
# a million and it would force an extra translated form for those locales.


def _rule_other_only(n: int) -> PluralCategory:
    """Always ``other`` -- no count distinction (zh, ja, ko, th, vi, id, ms)."""
    del n  # Unused.
    return PluralCategory.OTHER


def _rule_one_other(n: int) -> PluralCategory:
    """``one`` for 1, else ``other``.

    The common Germanic/Romance rule (en, de, nl, da, sv, el, hu, tr, ta,
    kk, eo, ...). Also covers es/it/vec below the deferred millions-``many``
    threshold (see the module-level note).
    """
    return PluralCategory.ONE if n == 1 else PluralCategory.OTHER


def _rule_zero_one_other(n: int) -> PluralCategory:
    """``one`` for 0 and 1, else ``other`` (fr, pt, fa, hi).

    (fr/pt also have the deferred millions-``many``; below that threshold
    they match this rule.)
    """
    return PluralCategory.ONE if n in (0, 1) else PluralCategory.OTHER


def _rule_russian(n: int) -> PluralCategory:
    """East-Slavic rule (ru, uk, be): one/few/many."""
    mod10 = n % 10
    mod100 = n % 100
    if mod10 == 1 and mod100 != 11:
        return PluralCategory.ONE
    if 2 <= mod10 <= 4 and not 12 <= mod100 <= 14:
        return PluralCategory.FEW
    return PluralCategory.MANY


def _rule_polish(n: int) -> PluralCategory:
    """Polish rule (pl): one/few/many."""
    if n == 1:
        return PluralCategory.ONE
    mod10 = n % 10
    mod100 = n % 100
    if 2 <= mod10 <= 4 and not 12 <= mod100 <= 14:
        return PluralCategory.FEW
    return PluralCategory.MANY


def _rule_czech(n: int) -> PluralCategory:
    """West-Slavic rule (cs, sk): one/few/other for integers.

    (CLDR's ``many`` for cs/sk only occurs for decimals, so integers never
    select it.)
    """
    if n == 1:
        return PluralCategory.ONE
    if 2 <= n <= 4:
        return PluralCategory.FEW
    return PluralCategory.OTHER


def _rule_croatian(n: int) -> PluralCategory:
    """South-Slavic rule (hr, sr): one/few/other for integers.

    Like East-Slavic but ``many`` (decimal-only here) folds into ``other``.
    """
    mod10 = n % 10
    mod100 = n % 100
    if mod10 == 1 and mod100 != 11:
        return PluralCategory.ONE
    if 2 <= mod10 <= 4 and not 12 <= mod100 <= 14:
        return PluralCategory.FEW
    return PluralCategory.OTHER


def _rule_romanian(n: int) -> PluralCategory:
    """Romanian rule (ro): one/few/other."""
    if n == 1:
        return PluralCategory.ONE
    if n == 0 or 1 <= n % 100 <= 19:
        return PluralCategory.FEW
    return PluralCategory.OTHER


def _rule_arabic(n: int) -> PluralCategory:
    """Arabic rule (ar): zero/one/two/few/many/other."""
    mod100 = n % 100
    if n == 0:
        return PluralCategory.ZERO
    if n == 1:
        return PluralCategory.ONE
    if n == 2:
        return PluralCategory.TWO
    if 3 <= mod100 <= 10:
        return PluralCategory.FEW
    if 11 <= mod100 <= 99:
        return PluralCategory.MANY
    return PluralCategory.OTHER


def _rule_filipino(n: int) -> PluralCategory:
    """Filipino/Tagalog rule (fil): ``other`` only for integers ending 4/6/9."""
    return PluralCategory.OTHER if n % 10 in (4, 6, 9) else PluralCategory.ONE


# Total ``Locale -> rule`` map over every resolved (canonical) locale we
# ship; the completeness + correctness of this table is enforced by the
# producer-side ``test_loctext_cldr`` test. Obsolete aliases resolve to
# their canonical form before lookup (see ``plural_category``). Grouped by
# rule family for readability.
_RULE_FOR_LOCALE: dict[Locale, Callable[[int], PluralCategory]] = {
    # other-only (no count distinction).
    Locale.CHINESE_TRADITIONAL: _rule_other_only,
    Locale.CHINESE_SIMPLIFIED: _rule_other_only,
    Locale.JAPANESE: _rule_other_only,
    Locale.KOREAN: _rule_other_only,
    Locale.THAI: _rule_other_only,
    Locale.VIETNAMESE: _rule_other_only,
    Locale.INDONESIAN: _rule_other_only,
    Locale.MALAY: _rule_other_only,
    # one/other (n == 1).
    Locale.ENGLISH: _rule_one_other,
    Locale.GERMAN: _rule_one_other,
    Locale.DUTCH: _rule_one_other,
    Locale.DANISH: _rule_one_other,
    Locale.SWEDISH: _rule_one_other,
    Locale.GREEK: _rule_one_other,
    Locale.HUNGARIAN: _rule_one_other,
    Locale.TURKISH: _rule_one_other,
    Locale.ESPERANTO: _rule_one_other,
    Locale.TAMIL: _rule_one_other,
    Locale.KAZAKH: _rule_one_other,
    Locale.SPANISH_SPAIN: _rule_one_other,
    Locale.SPANISH_LATIN_AMERICA: _rule_one_other,
    Locale.ITALIAN: _rule_one_other,
    Locale.VENETIAN: _rule_one_other,
    # European Portuguese is one-for-1 (unlike Brazilian, which is 0,1).
    Locale.PORTUGUESE_PORTUGAL: _rule_one_other,
    # Novelty/English-derived locales with no CLDR entry -> English's rule.
    Locale.PIRATE_SPEAK: _rule_one_other,
    Locale.GIBBERISH: _rule_one_other,
    # 0,1 -> one.
    Locale.FRENCH: _rule_zero_one_other,
    Locale.PORTUGUESE_BRAZIL: _rule_zero_one_other,
    Locale.PERSIAN: _rule_zero_one_other,
    Locale.HINDI: _rule_zero_one_other,
    # East-Slavic one/few/many.
    Locale.RUSSIAN: _rule_russian,
    Locale.UKRAINIAN: _rule_russian,
    Locale.BELARUSSIAN: _rule_russian,
    # Polish one/few/many.
    Locale.POLISH: _rule_polish,
    # West-Slavic one/few/other.
    Locale.CZECH: _rule_czech,
    Locale.SLOVAK: _rule_czech,
    # South-Slavic one/few/other.
    Locale.CROATIAN: _rule_croatian,
    Locale.SERBIAN: _rule_croatian,
    # Romanian one/few/other.
    Locale.ROMANIAN: _rule_romanian,
    # Arabic zero/one/two/few/many/other.
    Locale.ARABIC: _rule_arabic,
    # Filipino.
    Locale.FILIPINO: _rule_filipino,
}


def plural_category(locale: Locale, n: int) -> PluralCategory:
    """Return the CLDR cardinal plural category for an integer in a locale.

    ``n`` is treated as a non-negative integer count (its absolute value is
    used). Uses the locale's resolved form so obsolete aliases (e.g. the
    bare ``SPANISH``) follow their modern locale's rule. Every shipped
    locale is mapped explicitly; a genuinely-unknown locale falls back to
    the ``one``-for-1 rule. See the module note for the integer-only scope.
    """
    resolved = locale.resolved.locale
    rule = _RULE_FOR_LOCALE.get(resolved, _rule_one_other)
    return rule(abs(n))


#: Canonical CLDR category order, for stable presentation.
_CATEGORY_ORDER = [
    PluralCategory.ZERO,
    PluralCategory.ONE,
    PluralCategory.TWO,
    PluralCategory.FEW,
    PluralCategory.MANY,
    PluralCategory.OTHER,
]


def required_plural_categories(locale: Locale) -> list[PluralCategory]:
    """The plural categories a ``plural`` message must cover for a locale.

    The set the locale's rule can produce over the integers, plus the
    mandatory ``other`` fallback (ICU requires it), in canonical order.
    Used to tell a translation model exactly which plural forms to emit
    for the target locale -- derived from the same rules
    :func:`plural_category` evaluates with, so producer and client agree.

    The integer sample (0..200) spans every modulo cycle the rules use;
    under the integer-only scope (see the module note) this is the exact
    set of categories the locale can select.
    """
    present = {plural_category(locale, n) for n in range(201)}
    present.add(PluralCategory.OTHER)
    return [c for c in _CATEGORY_ORDER if c in present]


# --- Structured selectors + evaluation -------------------------------------


class LocTextError(Exception):
    """A malformed localized value or a missing/bad argument."""


class SelectorKind(Enum):
    """How a :class:`StringSelector` chooses among its forms."""

    #: Choose by the CLDR plural category of an integer argument.
    PLURAL = 'p'
    #: Choose by the string value of an argument (e.g. gender).
    SELECT = 's'


@ioprepped
@dataclass
class StringSelector:
    """A localized string whose final form is chosen at render time.

    The structured alternative to a plain ``str`` value: ``forms`` maps a
    form key to its leaf text (which may carry ``{name}`` substitutions and,
    for plurals, ``#`` for the count). For ``PLURAL`` the keys are CLDR
    category names (``one``/``few``/…/``other``) or ``=N`` exact-count
    matches; for ``SELECT`` they are the possible string values of ``arg``.
    ``other`` is the fallback. The ``IOAttrs`` keys are the on-the-wire
    schema shared with the native ``Lstr2`` port.
    """

    kind: Annotated[SelectorKind, IOAttrs('t')]
    arg: Annotated[str, IOAttrs('a')]
    forms: Annotated[dict[str, str], IOAttrs('f')]


def substitution_names(value: str | StringSelector) -> set[str]:
    """Return the substitution-argument names a value consumes.

    For a plain string these are its ``{name}`` tokens; for a
    :class:`StringSelector` its pivot ``arg`` plus any ``{name}``
    tokens in its forms. This is the single source consumers use to
    derive a string's parameter set from its value (e.g. rebuilding
    positional-substitution order client-side) -- the producer-side
    round-trip validation guarantees every parameter's token survives
    into every stored output, so the derivation is total.
    """
    if isinstance(value, StringSelector):
        names = {value.arg}
        for form in value.forms.values():
            names.update(_SUB_RE.findall(form))
        return names
    return set(_SUB_RE.findall(value))


def evaluate(
    value: 'str | StringSelector', locale: Locale, **args: object
) -> str:
    """Resolve a localized ``value`` to a final string.

    ``value`` is a plain ``str`` (``{name}`` substitutions only) or a
    :class:`StringSelector` (plural/select choice, then substitution).
    ``args`` supplies the named arguments; plural selection uses
    ``locale``'s CLDR rule (see :func:`plural_category`). Raises
    :class:`LocTextError` on a missing/ill-typed argument or a selector
    with no matching form and no ``other``.
    """
    if isinstance(value, StringSelector):
        return _eval_selector(value, locale, args)
    return _substitute(value, args, pound=None)


def _substitute(
    text: str, args: 'Mapping[str, object]', pound: int | None
) -> str:
    """Expand ``{name}`` placeholders (and ``#`` when ``pound`` is set)."""
    # ``#`` first, on the template, so a substituted value that happens to
    # contain ``#`` is left untouched.
    if pound is not None:
        text = text.replace('#', str(pound))

    def _repl(match: 're.Match[str]') -> str:
        name = match.group(1)
        if name not in args:
            raise LocTextError(f'Missing argument {name!r}.')
        return str(args[name])

    return _SUB_RE.sub(_repl, text)


def _eval_selector(
    sel: StringSelector, locale: Locale, args: 'Mapping[str, object]'
) -> str:
    """Pick ``sel``'s form for the args, then substitute its leaf text."""
    if sel.arg not in args:
        raise LocTextError(f'Missing argument {sel.arg!r}.')
    raw = args[sel.arg]

    if sel.kind is SelectorKind.PLURAL:
        # ``bool`` is an ``int`` subclass but never a meaningful count.
        if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
            raise LocTextError(
                f'Plural argument {sel.arg!r} must be a number; got {raw!r}.'
            )
        try:
            value = int(raw)
        except ValueError as exc:
            raise LocTextError(
                f'Plural argument {sel.arg!r} must be an integer;'
                f' got {raw!r}.'
            ) from exc
        # Exact ``=N`` matches win over the category rule.
        form = sel.forms.get(f'={value}')
        if form is None:
            category = plural_category(locale, value)
            form = sel.forms.get(category.value) or sel.forms.get('other')
        if form is None:
            raise LocTextError(
                f'Plural for {sel.arg!r} has no matching form and no'
                " 'other'."
            )
        return _substitute(form, args, pound=value)

    # SELECT: key by the argument's string value.
    key = str(raw)
    form = sel.forms.get(key) or sel.forms.get('other')
    if form is None:
        raise LocTextError(
            f'Select for {sel.arg!r} has no matching key {key!r} and no'
            " 'other'."
        )
    return _substitute(form, args, pound=None)
