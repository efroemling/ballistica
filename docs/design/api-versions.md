# API Versions

**Description:** How we deprecate and remove public Python API across api-version bumps — the overlapping-version lifecycle, the two migration idioms (bool-flag overloads and transitional twins), and the warning mechanics that make deprecations actually reach modders.

## What this doc is (and is not)

`CHANGELOG_API_VERSIONS.md` at the repo root is **modder-facing**: it
lists *what* is changing and what a mod author should do about it. It is
the thing modders read.

This doc is the **engineering side**: *how* we stage a deprecation, which
idiom to reach for, how warnings are emitted so they actually get seen,
and when to switch them on. Read this before deprecating or retyping any
public API; then add the matching bullet to the changelog.

## The lifecycle

Api-version bumps used to force every mod to update at once, which was
painful enough that the ecosystem lagged. The engine is moving to
**overlapping api versions**: for a period, both api N and api N+1 load.
Mods on N keep working but get warnings; once the ecosystem has moved,
N support ends and the scheduled changes take effect.

Two consequences that constrain planning:

- **A change only lands at an api boundary.** Anything that would break
  a mod has to wait for the removal of the version it was scheduled
  against.
- **Once api N+1 ships, nothing further can be scheduled for the N
  removal.** So there is a *window* — while N+1 is still unreleased — in
  which a breaking change must be declared if it is to ride that cycle.
  Miss the window and it waits a full version.

Backwards-compatible additions are not constrained by any of this and
can land whenever.

## The shared shape

Both idioms below are the same underlying pattern: a **transitional
spelling** that exists only to bridge two api removals. It always runs
in three phases.

1. **Now.** The good spelling keeps its old behavior and warns. A
   transitional spelling carries the new behavior. First-party code
   moves to the transitional spelling.
2. **At api N removal.** The good spelling takes on the new behavior.
   The transitional spelling still works but is now **inert** — it no
   longer selects anything — and warns that it is going away.
3. **At api N+1 removal.** The transitional spelling is deleted.

The end state is the original, tidy spelling with the new behavior. The
cost is a **two-hop migration**: call sites move to the transitional
spelling and later move back. Everyone pays it, us included.

What differs between the idioms is only *what the transitional spelling
is* — a keyword flag where the call site can take an argument, a
suffixed twin where it cannot.

## Idiom 1 — bool flag plus overloads (for methods and functions)

When a **method or function** must change its return type, add a keyword
flag defaulting to the old behavior, and describe both shapes to the
type checker with `typing.overload`:

```python
@overload
def get_display_string(cls, settings: dict | None = None, *,
                       langstr: Literal[False] = False) -> babase.Lstr: ...

@overload
def get_display_string(cls, settings: dict | None = None, *,
                       langstr: Literal[True]) -> str | babase.LangStr: ...
```

Phase 1: passing `langstr=False` (or omitting it) warns; `langstr=True`
does not.

Phase 2, at api N removal: the return type becomes unconditional, so the
overloads collapse and the flag goes inert. It is still *accepted* —
mods that dutifully added `langstr=True` must not break the moment they
were proven right — but it selects nothing, and now warns.

To warn only for callers who actually pass it, the inert phase needs a
**sentinel default** rather than `False`; a plain bool default cannot
distinguish `foo()` from `foo(langstr=False)`. Follow the existing
`_Unset` / `_UNSET` pattern in `babase/_simpledialog.py`.

Phase 3, at api N+1 removal: the parameter is deleted.

## Idiom 2 — the transitional twin (for properties)

A property cannot take a flag, so it gets a suffixed twin instead:

1. **Now.** Add `foo_langstr` alongside `foo`. `foo` keeps its old type
   and warns that it is about to change.
2. **At api N removal.** `foo` switches to the new type. Anyone who
   heeded the warning is already on `foo_langstr` and unaffected.
3. **At api N+1 removal.** `foo_langstr` is removed, after warning
   during the N+1/N+2 overlap to move back to `foo`.

The in-flight `Call` migration is this same idiom applied to a whole
class rather than a property: `Call` → explicit
`CallStrict`/`CallPartial` → `Call` with the new behavior, with
`CallStrict` retired later. Worth recognizing, because it means modders
who learn the pattern once can read every migration we ship.

### Choosing between the two

Use the flag for anything that can take an argument, and the twin only
where the call site genuinely cannot (properties, classes). The
asymmetry is deliberate: the flag avoids doubling the API surface, so it
wins wherever it is available. Say so in the docstring, so the
inconsistency reads as a decision rather than an oversight.

### Don't forget the return trip

Both idioms end with first-party code moving *back* to the good
spelling — `foo_langstr` → `foo`, `langstr=True` → nothing. That hop
happens a full api version after the one everyone is thinking about
when the migration is designed, so it is the step most likely to be
forgotten. Record it in the changelog as soon as the N+1 removal
section opens, rather than trusting it to memory.

## Warning mechanics

Use the standard library, not a bespoke logger:

```python
warnings.warn(
    'bauiv1.uicleanupcheck() will be removed when api 9 support ends;'
    ' use ba*.app.ui_v1.add_ui_cleanup_check() instead.',
    DeprecationWarning,
    stacklevel=2,
)
```

Details that matter:

- **`stacklevel=2` attributes the warning to the caller** — the mod's
  line, not ours. Without it the warning points at engine code and tells
  the modder nothing.
- **Python dedups by (message, category, module, lineno)**, so each
  distinct call site warns once per run rather than once per call. This
  is what makes warnings on hot paths tolerable.
- **`babase.do_once()` is the wrong tool here.** It registers the file
  and line *of the `do_once()` call itself*, so a check inside the
  deprecated function fires once globally and hides every caller but the
  first. It is fine for one-off engine log spam, not for per-caller
  deprecation attribution.
- **`_env.py` forces `warnings.simplefilter('default', DeprecationWarning)`
  on for all builds**, deliberately: deprecation warnings are off by
  default in release Python, and most modders run release builds, so
  without this the warnings would reach almost nobody.
- Pair the runtime warning with a `.. deprecated::` directive in the
  docstring, naming the replacement and the version it disappears in.

## Sequencing: build the path before you light the warning

A deprecation warning is only actionable if the replacement already
exists and our own code has stopped tripping it. The order is:

1. Add the new API (flag + overloads, or the twin).
2. Migrate first-party call sites onto it.
3. *Then* switch on the `warnings.warn` in the legacy path.
4. Add the changelog bullet.

Turning warnings on before step 2 spams the log with our own usage,
which trains everyone to ignore them — and the noisiest offenders tend
to be exactly the call sites still blocked on unfinished work.

Where first-party migration is itself blocked (a legacy composite that
cannot accept the new type yet, say), leave the warning off and note the
blocker. A warning nobody can act on is worse than no warning.

## Checklist for a deprecation

- [ ] New API added — flag + `@overload`, or the transitional twin.
- [ ] Docstring carries `.. deprecated::` naming the replacement and the
      removal version.
- [ ] First-party call sites migrated (or blockers recorded).
- [ ] `warnings.warn(..., DeprecationWarning, stacklevel=2)` on the
      legacy path, once first-party usage is clear.
- [ ] Bullet added to `CHANGELOG_API_VERSIONS.md` under the right
      removal section, phrased as *how to prepare*.
- [ ] The return trip is recorded for the following version — the twin's
      removal, or the flag going inert and then away.
