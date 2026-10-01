# Python API Packages

**Description:** Feature-set Python packages (babase, bauiv1, ...) are curated API surfaces that re-export shared names; API-walking tools must honor __all__, not __module__.

The Python packages exposed by feature-sets — `babase`, `bauiv1`,
`bascenev1`, `baclassic`, `baplus`, `bauiv1lib`, `bascenev1lib`,
`batemplatefs`, and so on — are curated **user-facing API
surfaces**, not raw implementation modules. Each one is meant to be
a complete entry point for the kind of code its consumers write: a
plugin targeting `bauiv1` should be able to import everything it
needs from `bauiv1`, without reaching into `babase` for things like
the app singleton, logging helpers, or shared types.

## The kitchen-sink principle

`babase` collects general engine plumbing (logging, app state,
async helpers, math types, common subsystems). Higher-level
packages — `bauiv1` for UI code, `bascenev1` for in-game scene
code — explicitly **re-export the parts of `babase` their consumers
need**, alongside their own additions:

```python
# bauiv1/__init__.py
from babase import (
    app, App, AppMode, AppState, AppTimer,
    apptime, apptimer, balog, ...
)
```

So `bauiv1.app`, `bauiv1.App`, and `bauiv1.AppMode` all forward to
the originals in `babase`. They are the *same* object, exposed at
two namespaces simultaneously. There is no single "canonical home"
for these re-exports — both locations are legitimate.

This pattern is common in Python — `numpy` re-exports things from
`numpy.random.mtrand` under `numpy.random`, for example — but we
lean on it more aggressively because feature-sets are designed to
be drop-in API targets for plugin authors.

## Consuming the packages: facade discipline

The flip side of the kitchen-sink principle is a rule for code
*inside* the repo: consumers go through their layer's facade, never
past it. UI code (`bauiv1lib/`) gets its engine/app API exclusively
through `bauiv1`; gameplay code (`bascenev1lib/`) through
`bascenev1`. Never reach past these facades into `babase` or
`babase._*` directly — the facades are deliberately curated to be
the complete API surface for their layer, and preflight enforces
this with a real error (e.g. `import of private module babase._login
not allowed from this featureset package (bauiv1lib)`).

When an API you need appears to be missing from the facade, the fix
is to *extend the facade*, not bypass it: first add the name to
that package's `__init__.py` re-exports (both the `from babase
import (...)` block and the `__all__` list), then consume it
through the facade (`bui.X` / `bs.X`). For truly internal
(`babase._*`) symbols the right answer is usually not to consume
them from UI/gameplay code at all — consider whether the work
belongs behind the facade instead.

## `__all__` is the contract

A package's `__all__` declares its public API surface. **Tools
consuming the API — Sphinx, completion indexers, anything else
walking module members for documentation or tooling purposes — must
honor `__all__` rather than chasing `__module__`.**

Because the same object lives in multiple packages, following
`__module__` will incorrectly attribute re-exports to one place
only — typically `babase`, which then breaks the user-facing-surface
philosophy: a plugin author looking at `bauiv1` docs or completions
sees an incomplete API and has to know to also look elsewhere.

The rule of thumb when writing or reviewing an API-consuming tool:

> If a name appears in `module.__all__`, it is part of that
> module's public surface, regardless of where its underlying
> object happens to live.

## Marking internal api

Anything that shows up in the Sphinx docs counts as public api. Some
code has to live in a documented place even though it's ours alone:
`bacommon` holds wire types and plumbing shared between the client
and the servers, and `bacommon` as a whole is documented. There are
three ways to keep such code from reading as a supported api:

- **An `_underscore` module** — the docs build skips it entirely. Best
  for implementation behind a public package's re-exports.
- **The internal-api warning block** — for a whole documented module
  or package that is ours alone. Its page stays in the docs but shows
  only the module docstring: the warning, plus whatever explanation
  surrounds it, with no members listed. (A page that says "internal,
  don't use this" beats a missing one, which reads as broken docs.)
  Put this exact text in the module docstring (usually right after the
  summary line):

  ```
  .. warning::

    This is an internal api and subject to change at any time. Do not use
    it in mod code.
  ```

  Flagging a package's `__init__.py` does NOT flag its public
  submodules, since each gets its own docs page; flag them too, or
  make them `_underscore` modules. Since the module's members aren't
  documented, its docstring can't link to them: write their names as
  ``` ``literals`` ```.
- **`:meta private:`** — for an individual function, class, or `#:`
  attribute inside an otherwise public module. It drops out of the
  docs entirely. (Mechanics: the `/rst-docstrings` skill.) A dataclass
  field marked this way is also dropped from its class's rendered
  constructor signature.

How it's enforced:

- **The docs build** (`batools.docs`, `src/assets/sphinx/static/conf.py`)
  finds flagged modules via `batools.apidocs` and strips their pages
  to the docstring. Since the docs build is strict about
  cross-references, any public signature or docstring that refers to
  an internal type then fails `make docs` as an unresolved reference;
  that is the main leak detector. It also fails the build if a public
  page would show an internal object (a re-export through `__all__`).
  Never add internal types to `nitpick_ignore` / `nitpick_ignore_regex`
  to quiet one of these: fix the leak (make the public thing private,
  or the internal type public).
- **The project check** `batools.project._checks_apidocs` (part of
  `make update` / `update-check`, so preflight and CI) catches flag
  mistakes early: a docstring mentioning an internal api must use the
  exact text, every public submodule of a flagged package must be
  flagged too, and a public module's `__all__` must not re-export a
  name from an internal module.

Note `make docs` runs only in `ballistica-internal.smoke` CI, not
preflight; run it by hand after touching public signatures.

Modules deliberately left public despite looking like plumbing:
`bacommon.workspace` (a reference for hand-editing workspace config)
and `bacommon.strbrief` (the `.bstr` brief tag vocabulary workspace
authors write).

## Why not just fix `__module__`?

The `efro.util` package provides a `set_canonical_module_names()`
helper that walks a module's globals and rewrites each class's /
instance's `__module__` attribute to point at the importing
module. If called from `bauiv1/__init__.py`, it would make
`bauiv1.App.__module__ == 'bauiv1'`, after which Sphinx, our
completion indexer, and any other `__module__`-following tool would
"just work" without special-casing.

It was tried and backed out. The call site is preserved (commented
out) in `babase/__init__.py` with the note:

> Trying without this for now. Seems like this might cause more
> harm than good. Can flip it back on if it is missed.

The "harm" came from global side-effects: `__module__` is used by
`pickle` for class lookup, by `repr()` for error messages, by
introspection libraries deciding what's a "third-party" type, and
so on. Rewriting it globally per importing package created subtle
breakage in those places. The chosen path is:

1. Let `__module__` reflect the *source* location of each object.
2. Have consumer tools respect `__all__` instead.

`__all__` is the right signal anyway — it's an explicit
package-author statement of "this is the public surface here",
whereas `__module__` is an implementation detail of where the
object was defined.

## Implementation notes

Tools that walk Ballistica API packages should follow this rule.
Known sites:

- `tools/batools/vanillacompletions.py` (vanilla completion JSON
  generator consumed by sibling code editors) — emits any name
  listed in a module's `__all__`, bypassing the `__module__`-based
  owner check.
- `src/assets/sphinx/static/conf.py` (documentation generation) —
  the `autodoc-skip-member` hook un-skips members listed in the
  importing module's `__all__` so they show up in that module's
  docs page, not only in `babase`'s.

When adding new tooling that walks the API surface, the simplest
sanity check is: pick a name like `bauiv1.app`, and confirm it
appears in your tool's output for `bauiv1`. If it only appears
under `babase`, the tool is chasing `__module__` and needs to be
updated.
