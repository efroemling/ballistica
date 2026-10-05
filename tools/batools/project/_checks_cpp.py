# Released under the MIT License. See LICENSE for details.
#
"""Checks we can run on C++ engine source files.

Split out from ``_checks.py`` (which covers Python and project-level
checks) to keep both modules a manageable size. Everything here operates
on ``src/ballistica`` sources and headers.
"""

from typing import TYPE_CHECKING
import os

from efro.error import CleanError
from efrotools.project import (
    get_public_legal_notice,
    get_non_public_legal_notice,
    get_non_public_legal_notice_prev,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from batools.project._updater import ProjectUpdater


# The JSON facade (``src/ballistica/shared/generic/json_facade.h``) is the
# engine's one sanctioned JSON interface (initiative:
# strings-asset-migration, decision D7). Engine code must go through it
# (``JsonDoc``/``JsonRef``/``JsonBuilder``) rather than touch the underlying
# yyjson C API or the legacy cJSON C API directly; that is what makes the
# crash-the-server-on-bad-JSON exploit class structurally unreachable rather
# than merely mitigated.
#
# yyjson is born facade-only: it is banned everywhere outside the facade's
# own translation unit from day one (no allowlist needed -- the vendored
# library lives under src/external and is never scanned here). cJSON is
# retired incrementally; the set below names the not-yet-migrated files still
# permitted to use the raw cJSON C API. It only ever SHRINKS -- migrate a
# file onto the facade and delete its entry (the check then guards the file
# against cJSON creeping back in).
#
# The set is now EMPTY: every engine consumer is on the facade and no new raw
# cJSON use is permitted anywhere. The remaining cleanup is to delete the
# vendored cJSON library itself (shared/generic/json.{h,cc}) and the
# now-unused JsonDict/JsonObject veneer, after which _JSON_FACADE_EXEMPT_FILES
# can drop its json.{h,cc} entries too.
JSON_FACADE_CJSON_ALLOWLIST: set[str] = set()

# The facade's own translation unit: this is the one place the raw yyjson API
# legitimately lives, so it is exempt from the ban below. (The vendored cJSON
# library that used to share this directory has been retired.)
_JSON_FACADE_EXEMPT_FILES: set[str] = {
    'src/ballistica/shared/generic/json_facade.h',
    'src/ballistica/shared/generic/json_facade.cc',
}


def check_source_files(self: ProjectUpdater) -> None:
    """Check project source files."""
    for fsrc in self.source_files:
        if fsrc.endswith('.cpp') or fsrc.endswith('.cxx'):
            raise RuntimeError('please use .cc for c++ files; found ' + fsrc)

        # Watch out for in-progress emacs edits.
        # Could just ignore these but it probably means I intended
        # to save something and forgot.
        if '/.#' in fsrc:
            raise CleanError(f'Found an unsaved emacs file: "{fsrc}".')

        fname = 'src/ballistica' + fsrc
        _check_source_file(self, fname)


def _check_source_file(self: ProjectUpdater, fname: str) -> None:
    with open(os.path.join(self.projroot, fname), encoding='utf-8') as infile:
        lines = infile.read().splitlines()

    if self.license_line_checks:
        _check_c_license(self, fname, lines)

    _source_file_feature_set_namespace_check(self, fname, lines)
    _source_file_json_facade_check(fname, lines)


def _source_file_feature_set_namespace_check(
    self: ProjectUpdater, fname: str, lines: list[str]
) -> None:
    """Make sure C++ code uses correct namespaces based on its location."""

    # Extensions we know we're skipping.
    if any(fname.endswith(x) for x in ['.c', '.swift']):
        return

    if not any(fname.endswith(x) for x in ['.cc', '.h', '.mm']):
        raise CleanError(f"Unrecognized source file type: '{fname}'.")

    # Anonymous namespaces are fine in source files but never in headers.
    # Checked up front, before any of the feature-set exemptions below
    # can waive it: this is a one-definition-rule matter, not a naming
    # convention, so 'this file is exempt from our namespace layout
    # rules' must not also mean 'this file may quietly hand every
    # including translation unit its own private copy of things'.
    _check_no_anonymous_namespace_in_header(fname, lines)

    splits = fname.split('/')
    assert len(splits) >= 3  # should be at least src, ballistica, foo
    toplevelname = splits[2]

    # Make sure FOO in src/ballistica/FOO corresponds to a feature-set.
    # (or one of our reserved names).
    reserved_names = {'shared'}
    feature_set = self.feature_sets.get(toplevelname)

    if toplevelname not in reserved_names and feature_set is None:
        raise CleanError(
            f"{toplevelname} in path '{fname}' does not correspond"
            ' to a feature-set.'
        )

    # If the feature-set lists these files as to-be-ignored, ignore.
    if (
        feature_set is not None
        and fname in feature_set.cpp_namespace_check_disable_files
    ):
        return

    # Ignore ballistica.h/cc for now
    if len(splits) == 3:
        return

    # Anything under shared should only use ballistica namespace.
    if splits[2] == 'shared':
        for i, line, namespace, predecs_only in _iter_named_namespaces(lines):
            if namespace != 'ballistica' and not predecs_only:
                raise CleanError(
                    f'Invalid line "{line}" at {fname} line {i+1}.\n'
                    f"Files under 'shared' should use only ballistica"
                    f' namespace.'
                )
        return

    # Anything else should use only the featureset namespace.
    for i, line, namespace, predecs_only in _iter_named_namespaces(lines):
        if namespace != f'ballistica::{toplevelname}' and not predecs_only:

            # Special case - allow our 'from_swift' namespace.
            if line == 'namespace from_swift {' and (
                fname.endswith('/from_swift.h')
                or fname.endswith('/from_swift.cc')
            ):
                pass
            else:
                raise CleanError(
                    f'Invalid line "{line}" at {fname} line {i+1}.\n'
                    f"This file is associated with the '{toplevelname}'"
                    ' FeatureSet so should be using the'
                    f" 'ballistica::{toplevelname}' namespace."
                )


def _source_file_json_facade_check(fname: str, lines: list[str]) -> None:
    """Enforce JSON-facade-only access to JSON (initiative D7).

    Engine code must use the facade in ``shared/generic/json_facade.h``
    (``JsonDoc``/``JsonRef``/``JsonBuilder``); raw ``yyjson_*`` is banned
    outside the facade TU, and raw ``cJSON_*`` is permitted only in the
    shrinking ``JSON_FACADE_CJSON_ALLOWLIST`` of not-yet-migrated files. A
    single line may opt out with a ``// __JSON_FACADE_ALLOW_RAW__`` marker for
    genuinely exceptional cases (rare, and to be justified in a comment).
    """
    # Skip extensions we don't scan (matches the namespace check). The
    # vendored yyjson.c is a .c file under src/external and never reaches
    # here anyway.
    if any(fname.endswith(x) for x in ('.c', '.swift')):
        return
    if not any(fname.endswith(x) for x in ('.cc', '.h', '.mm')):
        return

    # The facade TU (and the vendored cJSON lib beside it) legitimately use
    # the raw APIs.
    if fname in _JSON_FACADE_EXEMPT_FILES:
        return

    cjson_allowed = fname in JSON_FACADE_CJSON_ALLOWLIST
    found_cjson = False

    for i, line in enumerate(lines):
        stripped = line.lstrip()

        # Skip comment lines (naive, in the spirit of the namespace check).
        if stripped.startswith(('//', '*', '/*')):
            continue

        # Per-line escape hatch for genuinely exceptional cases.
        if '__JSON_FACADE_ALLOW_RAW__' in line:
            continue

        if 'yyjson_' in line:
            raise CleanError(
                f'Raw yyjson use at {fname} line {i + 1}:\n'
                f'  {line.strip()}\n'
                'yyjson is reachable only through the JSON facade'
                ' (shared/generic/json_facade.h); use JsonDoc/JsonRef/'
                'JsonBuilder, or extend the facade if it lacks something'
                ' you need (initiative: strings-asset-migration, D7).'
            )

        if 'cJSON_' in line:
            found_cjson = True
            if not cjson_allowed:
                raise CleanError(
                    f'Raw cJSON use at {fname} line {i + 1}:\n'
                    f'  {line.strip()}\n'
                    'The legacy cJSON C API is being retired in favor of the'
                    ' JSON facade (shared/generic/json_facade.h); use'
                    ' JsonDoc/JsonRef/JsonBuilder for new code (initiative:'
                    ' strings-asset-migration, D7).'
                )

    # Keep the allowlist honest: an allowlisted file that no longer uses
    # cJSON should be removed so the list keeps shrinking toward empty.
    if cjson_allowed and not found_cjson:
        raise CleanError(
            f"'{fname}' is in JSON_FACADE_CJSON_ALLOWLIST but no longer uses"
            ' the cJSON C API; remove it from the allowlist (initiative:'
            ' strings-asset-migration, D7).'
        )


def _iter_named_namespaces(
    lines: list[str],
) -> Iterator[tuple[int, str, str, bool]]:
    """Yield (index, line, namespace, predecs_only) per named namespace.

    Anonymous namespaces are skipped: they introduce no name, so the
    feature-set namespace rules have nothing to say about them.
    """
    for i, line in enumerate(lines):
        if not line.startswith('namespace '):
            continue
        if _is_anonymous_namespace_line(line):
            continue
        namespace, predecs_only = _get_namespace_info(lines, i)
        yield i, line, namespace, predecs_only


def _is_anonymous_namespace_line(line: str) -> bool:
    """Is this line an anonymous-namespace declaration?"""
    splits = line.split()
    return len(splits) >= 2 and splits[0] == 'namespace' and splits[1][0] == '{'


def _check_no_anonymous_namespace_in_header(
    fname: str, lines: list[str]
) -> None:
    """Reject anonymous namespaces in headers.

    They are welcome in source files -- unlike ``static`` they can give
    internal linkage to *types*, and they add no name to reason about. In
    a header they are a trap: every including translation unit gets its
    own private copy of everything inside, so what looks like one shared
    helper or one shared counter silently becomes N independent ones.
    """
    if not fname.endswith('.h'):
        return
    for i, line in enumerate(lines):
        if line.startswith('namespace ') and _is_anonymous_namespace_line(line):
            raise CleanError(
                f'Invalid line "{line}" at {fname} line {i+1}.\n'
                'Anonymous namespaces are not allowed in headers; each'
                ' including translation unit would wind up with its own'
                ' copy of the contents. Use them in source files only.'
            )


def _get_namespace_info(lines: list[str], index: int) -> tuple[str, bool]:
    """Given a line no, return name of namespace declared and whether it
    is only predeclares."""
    assert lines[index].startswith('namespace ')
    # Special case: single-line empty declaration.
    splits = lines[index].split()
    assert splits[0] == 'namespace'
    if '{}' in lines[index]:
        assert splits[2] == '{}'
        # Not considering this a predeclare statement since it doesn't need to
        # be there.
        return splits[1], False
    assert splits[2] == '{'
    name = splits[1]
    # Now scan lines until we find the close or a non-predeclare statement
    index += 1
    while True:
        if lines[index].startswith('}'):
            return name, True
        if not (
            (
                lines[index].startswith('class ')
                or lines[index].startswith('struct ')
            )
            and lines[index].endswith(';')
        ):
            # Found a non-predeclare statement
            return name, False
        index += 1


def check_headers(self: ProjectUpdater) -> None:
    """Check all project headers."""
    for header_file_raw in self.header_files:
        assert header_file_raw[0] == '/'
        header_file = f'src/ballistica{header_file_raw}'
        if header_file.endswith('.h'):
            _check_header(self, header_file)


def _check_header(self: ProjectUpdater, fname: str) -> None:
    # Make sure its define guard is correct.
    guard = fname[4:].upper().replace('/', '_').replace('.', '_') + '_'
    with open(os.path.join(self.projroot, fname), encoding='utf-8') as fhdr:
        lines = fhdr.read().splitlines()

    if self.license_line_checks:
        _check_c_license(self, fname, lines)

    _source_file_feature_set_namespace_check(self, fname, lines)
    _source_file_json_facade_check(fname, lines)

    # Check for header guard lines at top
    line = f'#ifndef {guard}'
    lnum = 2
    if lines[lnum] != line:
        # Allow auto-correcting if it looks close already
        # (don't want to blow away an unrelated line)
        allow_auto = lines[lnum].startswith('#ifndef BALLISTICA_')
        self.add_line_correction(
            fname,
            line_number=lnum,
            expected=line,
            can_auto_update=allow_auto,
        )
    line = f'#define {guard}'
    lnum = 3
    if lines[lnum] != line:
        # Allow auto-correcting if it looks close already
        # (don't want to blow away an unrelated line)
        allow_auto = lines[lnum].startswith('#define BALLISTICA_')
        self.add_line_correction(
            fname,
            line_number=lnum,
            expected=line,
            can_auto_update=allow_auto,
        )

    # Check for header guard at bottom
    line = f'#endif  // {guard}'
    lnum = len(lines) - 1
    if lines[lnum] != line:
        # Allow auto-correcting if it looks close already
        # (don't want to blow away an unrelated line)
        allow_auto = lines[lnum].startswith('#endif  // BALLISTICA_')
        self.add_line_correction(
            fname,
            line_number=lnum,
            expected=line,
            can_auto_update=allow_auto,
        )


def _check_c_license(
    self: ProjectUpdater, fname: str, lines: list[str]
) -> None:
    # Look for public license line (public or private repo) or private
    # license line (private repo only)
    line_private = '// ' + get_non_public_legal_notice()
    line_private_prev = '// ' + get_non_public_legal_notice_prev()
    line_public = get_public_legal_notice('c++')
    lnum = 0

    if self.public:
        if lines[lnum] != line_public:
            # Allow auto-correcting from private to public line
            allow_auto = lines[lnum] == line_private
            self.add_line_correction(
                fname,
                line_number=lnum,
                expected=line_public,
                can_auto_update=allow_auto,
            )
    else:
        if lines[lnum] not in [line_public, line_private]:
            self.add_line_correction(
                fname,
                line_number=lnum,
                expected=line_private,
                can_auto_update=(lines[lnum] == line_private_prev),
            )
