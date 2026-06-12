# Spinoff & Feature-Sets

How `ballistica-internal` produces downstream projects (e.g.
`bombsquad`, `spinoff-template`) by stripping and substituting
source. Feature-sets are the modular units the spinoff system
operates on.

For the user-facing intro (naming conventions, directory layout)
see [`pconfig/featuresets/README.md`](../../pconfig/featuresets/README.md).
This doc covers the deeper mechanics — what gets stripped, when,
and how to structure new code so it survives spinoff correctly.

## The two pieces

**Feature-sets** are logical groupings of functionality declared in
`pconfig/featuresets/featureset_<name>.py`. Each one owns a fixed
set of directory paths by convention (see the README). The system
treats a feature-set as a unit that can be present or absent in a
given spinoff target.

**Spinoff** is the mechanism that takes the source repo, applies
text substitutions (e.g. `BallisticaKit` → `SpinoffTest`) and
strip rules (omit paths, delete code blocks marked with strip
tags), and produces a derived project at a target path. The
target's `--featuresets` flag controls which feature-sets are
included; everything else is omitted.

## Strip mechanics

There are three independent strip mechanisms. They compose: a file
that passes the path filter can still have inline content stripped
by markers, and an entirely-public file can still be omitted from a
public spinoff if a marker says so.

### 1. Path-based omission by feature-set

When a spinoff omits feature-set `foo`, the following paths are
automatically excluded from the copied tree (see
`tools/batools/spinoff/_context.py:_add_feature_set_omit_paths`):

- `pconfig/featuresets/featureset_foo.py`
- `src/assets/ba_data/python/bafoo/` (Python package)
- `src/ballistica/foo/` (C++ source)
- `src/codegen/bafoocodegen/` (codegen specs)
- `tests/test_foo/`

These are mechanical, name-based mappings — same conventions as
the README's "Locations" section.

**Implication:** files outside these paths are NOT automatically
omitted, even if they semantically belong to `foo`. Anything under
`tools/`, `ballisticakit-android/`, `ballisticakit-cmake/`, etc.
is copied wholesale.

### 2. Public/private split

A separate axis from feature-sets. Some directories are marked
"internal" and excluded from public spinoffs regardless of feature-
set selection. Standard examples:

- `tools/batoolsinternal/` (vs. public `tools/batools/`)
- `tools/efrotoolsinternal/` (vs. public `tools/efrotools/`)

Internal code is included only when the spinoff target itself is
private (`spinoffconfig.json` → `"public": false`). Spinofftests
of this repo are private-equivalent, so internal tools come along.

The two axes are orthogonal: a `core`-only spinoff that is also
private will include `tools/batoolsinternal/` but exclude
`src/ballistica/base/`, `src/codegen/babasecodegen/`, etc.

### 3. Inline strip markers

Pairs of magic comments that delete content between them during
the spinoff copy:

- `__SPINOFF_STRIP_BEGIN__` / `__SPINOFF_STRIP_END__` —
  unconditional. Always stripped on copy.
- `__SPINOFF_REQUIRE_<FEATURESET>_BEGIN__` / `_END__` — conditional.
  Stripped only if `<FEATURESET>` is omitted in this spinoff.
- `__PUBSYNC_STRIP_BEGIN__` / `_END__` — stripped only in public
  spinoffs (a private/internal escape hatch).

Strip-tag generation lives in
`tools/batools/spinoff/_context.py` (line ~122–141).

**Use case:** when a feature-set has a small island of code in
another file (a per-platform call site, an enum entry, an import)
that should disappear with the feature-set, wrap it in
`__SPINOFF_REQUIRE_FOO_BEGIN__` … `_END__`. Don't relocate the
host file just to satisfy the strip.

## Structuring code that crosses boundaries

The spinoff system's most subtle rule: **a file's location is its
strip class**. Code under `src/ballistica/foo/` IS feature-set
`foo`. Code under `tools/` is shared infrastructure that is NOT
feature-set-specific by default.

This matters when a tool processes spec data owned by a feature-set
— e.g. codegen libraries that read spec files. The codegen lib lives
in `tools/` (always present) but the spec lives in
`src/codegen/<fs>codegen/` (omitted when `<fs>` is). If the codegen lib
has a *static* reference to the spec — even a TYPE_CHECKING import
for an annotation — mypy fails in any spinoff that strips the
owning feature-set.

### Pattern: invert the type dependency

When a codegen library and its spec share data types (e.g. a
`Message` dataclass), define the types in the **codegen library**
(under `tools/`), and have the spec **import them from there**.
The spec then defines only the data instances.

```text
tools/batoolsinternal/foo_codegen.py        ← owns Message, Field, Dir
src/codegen/<fs>codegen/foo_spec.py         ← imports those types, declares MESSAGES
```

- `tools/` is always present → mypy always finds the types.
- The spec is stripped along with its feature-set's codegen dir →
  no dangling reference to a missing module.
- The codegen lib stays statically valid even when its spec
  doesn't exist (because there are no static references TO it).
- At runtime the codegen lib uses `importlib.import_module` to
  load the spec dynamically — invisible to mypy.

### Pattern: feature-set guard in codegen targets

`tools/batools/codegenmakefile.py` generates `src/codegen/Makefile`.
Add targets for a feature-set behind a runtime check:

```python
if os.path.exists(
    f'{self._projroot}/pconfig/featuresets/featureset_foo.py'
):
    targets.append(Target(src=[...], dst=[...], cmd='...'))
```

The featureset config file is itself path-stripped along with the
feature-set, so its absence is the canonical "this feature-set
isn't in this spinoff" signal at update time. The matching pcommand
function and its imports stay defined in `tools/batoolsinternal/`
unconditionally — they're just never called when no targets reference
them.

### Pattern: pcommand function with cross-featureset deps

A pcommand function in `tools/batoolsinternal/pcommands.py` that
delegates to a codegen lib needs no special markers. The function
itself is harmless to define always; what matters is whether it's
ever called. The codegenmakefile gate above handles that.

If the function body has *static* imports from a feature-set's
modules, those static imports are the problem — refactor them away
(invert the type dependency, or use `importlib.import_module`).

## Verifying with spinofftest

`make spinoff-test-core` (and `-base`, `-plus`, etc.) materializes
a spinoff under `build/spinofftest/<fs>/` with only the named
feature-set included, then runs the full `make check` against it.
This is how CI catches "code references a missing feature-set"
issues that local `make mypy` won't surface (since the local repo
always has everything).

The smoke job runs at least `spinoff-test-core`; failures there
typically mean a static cross-feature-set reference. The fix is one
of the patterns above, depending on whether the dangling reference
is in types (invert), generation rules (gate), or call sites (mark
inline).

## Propagating changes to dst projects

How a real dst project receives src changes — a standalone
operation, independent of any other pipeline.

A dst project pins its parent via a git submodule at
`submodules/ballistica`; `tools/spinoff` in the dst is a symlink
into that submodule (not into any sibling checkout). The sync
targets, all run **in the dst**:

- `make spinoff-update` — sync from the parent at the currently
  pinned submodule commit. Deterministic; what CI and fresh
  checkouts use.
- `make spinoff-upgrade` — move the pin to the latest parent
  `main` (`git checkout main && git pull` in the submodule), then
  sync.
- `make spinoff-upgrade-push` — `spinoff-upgrade`, then commit and
  push the dst.

Both upgrade flavors read the parent's **pushed origin `main`** —
never a local working tree. To exercise uncommitted parent changes,
use spinofftest (above) rather than upgrading a real dst.

Every sync ends with an automatic `make update-check` to verify
the dst landed in a consistent state.

## Reference

- `pconfig/featuresets/README.md` — naming + locations.
- `pconfig/featuresets/featureset_*.py` — feature-set declarations.
- `tools/batools/featureset.py` — `FeatureSet` dataclass (full
  docstrings on every property).
- `tools/batools/spinoff/_context.py` — strip logic core.
- `tools/batools/spinoff/_test.py` — spinofftest driver.
- `tools/spinoff` — the user-facing spinoff CLI.
