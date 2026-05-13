# Code Generation & the `mgen/` Convention

This codebase has several code generators that emit C++, Python,
and Java alongside the hand-written source. By convention,
generated files live in `mgen/` (C++/Java) or `_mgen/` (Python)
subdirectories per feature-set, not scattered alongside hand-
written code. This doc explains why that convention exists and
how new generators should fit into it.

## What lives where

**C++** — each feature-set has its own `mgen/` directory:

```
src/ballistica/base/mgen/        # base featureset
src/ballistica/classic/mgen/     # classic featureset
src/ballistica/scene_v1/mgen/    # scene_v1 featureset
src/ballistica/ui_v1/mgen/       # ui_v1 featureset
... etc.
src/meta/baplusmeta/mgen/        # meta-side codegen outputs
```

These hold generated `.h` and `.inc` files (e.g.,
`pyembed/binding_base.inc` — Python-source-as-C-string-literal
embedded for the runtime).

**Python** — `_mgen/` subdirectories under each Python package
namespace:

```
src/assets/ba_data/python/babase/_mgen/
src/assets/ba_data/python/bascenev1/_mgen/
... etc.
```

These hold generated `.py` modules (e.g., `babase/_mgen/enums.py`
— enum classes mirroring the C++ enum values).

The Python underscore prefix is the conventional "private package"
marker; the C++ side has no equivalent need for it.

## Why centralized rather than scattered

Three converging mechanisms in the build/tooling pipeline all rely
on the directory name pattern `mgen` / `_mgen` to identify
generated content. Scattering generated files alongside hand-
written code would require inventing per-file exclusion rules in
each of these places. Centralizing them in `mgen/` lets one path
pattern do the work in all three.

### 1. Gitignored by directory name

`.gitignore` excludes generated dirs via a small set of glob
patterns:

```
/src/ballistica/mgen
/src/ballistica/*/mgen
/src/assets/ba_data/python/*/_mgen
/src/meta/*/mgen
```

Generated files never accumulate as commits, never pollute
`git status`, never need per-generator `.gitignore` entries.

### 2. Spinoff strips them as cruft

`tools/batools/spinoff/_main.py` filters `mgen` / `_mgen`
directory names when copying src to dst:

```python
cruft_names = ['.DS_Store', 'mgen', '_mgen']
```

Spinoff projects (bombsquad, spinoff-template) don't inherit
generated files — they regenerate their own during their own
`make update` / `make meta`. This keeps src and dst clean: the
spinoff's generated content reflects the spinoff's own state, not
a stale snapshot from src.

### 3. File-list updater excludes `/mgen/` paths

`tools/batools/project/_updater.py` excludes generated files when
regenerating CMake/Makefile source-file lists:

```python
self._source_files = sorted(s for s in src_files if '/mgen/' not in s)
self._header_files = sorted(h for h in header_files if '/mgen/' not in h)
```

Without this, every `make update` would pick up generated headers
into the "hand-written source" lists, causing churn in committed
file lists every time generation runs.

## Adding a new generator

Output to the appropriate `mgen/` or `_mgen/` directory under the
feature-set that owns the generated content. The three
mechanisms above pick it up automatically — no edits to
`.gitignore`, spinoff filters, or `_updater.py` needed.

For Python modules where a clean public name is wanted, re-export
from the package's `__init__.py`:

```python
# babase/__init__.py
from babase._mgen.enums import (
    InputType,
    Permission,
    QuitType,
    SpecialChar,
    UIScale,
)
```

Consumers then see `babase.InputType` rather than
`babase._mgen.enums.InputType`. The generated module stays inside
`_mgen` (and inherits its gitignore/spinoff/file-list treatment);
the public surface is curated through `__init__.py`.

## Caveat: `.cc` generation

The current `_updater.py` exclusion treats `mgen/` files as
generated-headers-and-includes only. From the code comment:

> "For now these just consist of headers so its ok to completely
> ignore their existence here, but at some point if we start
> generating `.cc` files that need to be compiled we'll have to
> ask the meta system which files it *will* be generating and add
> THAT list (not what we see on disk) to projects."

If a future generator emits `.cc` files that need to be compiled,
the file-list logic has to enumerate what *will* exist (queried
from the generator's meta-spec) rather than what's on disk at
update time — otherwise the source-file list races the generator.
Existing pattern for generated includes (`.inc`) avoids this
because they're `#include`d from hand-written `.cc` files, so the
build system already knows about them via the hand-written file's
inclusion graph.

## Related but distinct: `build/dummymodules/`

Dummy modules at `build/dummymodules/_babase.py` etc. are also
generated, but follow a different placement convention — they
live in `build/`, not `src/`. The reason: dummy modules exist
*only* for static analysis (mypy/pylint) outside of a running
engine, and must *never* appear in any directory the runtime
sees, or they'd shadow the real compiled extension modules.
Putting them in `build/` keeps them off the Python import path at
runtime; the static-analysis tools find them via `mypy_path` /
pylint sys.path entries.

So the rule of thumb:

- Code shipped to runtime + only-generated → `mgen/` / `_mgen/`
  inside `src/`.
- Static-analysis-only artifact, never seen by runtime →
  `build/<name>/`.
