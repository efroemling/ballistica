# Custom Glyphs

**Description:** How our custom characters (`SpecialChar`: icons, flags, logos, controller buttons) are defined, drawn and placed, including two-form superscript/full-size icons, and the checklist for adding one.

## What they are

`bacommon.text.SpecialChar` is the one list of the custom characters
the engine can draw: controller buttons, symbols like the close X and
back arrow, currency (tickets, tokens), trophies, and the profile
icons, flags and account/platform logos players show next to their
names. Each member's value is its character, in Unicode's private-use
area from U+E000, ready to drop into any string. The same enum is
available as `babase.SpecialChar` and `bauiv1.SpecialChar`, and servers
use it directly.

The engine's own table is generated from it:
`batools/special_chars.py` writes `base/generated/special_chars.h`
(the C++ enum, each character's UTF-8 form, the icon pairs, and
`kSpecialCharCodepointEnd`). Nothing else lists the characters.

## How they're drawn

- **Art** is on the extras sheets: `font_extras` through
  `font_extras5` in the `babuiltinassets` package, 5x5 cells each.
  Pages 2-5 hold pre-colored art and can't be tinted or flattened.
- **Metrics** are data in `base/graphics/text/font_big_and_extras_data.h`:
  `g_glyphs_extras` (one entry per codepoint from U+E000; fields as in
  `font_glyph_pages_data.h`) and `g_glyphs_extras_page` (which sheet
  each samples; its cell is in its tex coords). A codepoint doesn't
  imply a sheet, so related characters can sit together whatever
  sheet their art is on. Static asserts in `text_graphics.cc` fail the
  build if the table doesn't cover every `SpecialChar`.
- The pen is the baseline, which sits `kTextBaselineHeight` above the
  bottom of a 32-unit text row (chosen so our font's capitals' ink is
  exactly mid-row). There are no placement fudge factors in code: a
  glyph lands where its data says.

## Placement conventions

Measured from the atlas, not by eye (the doc-ui **Glyphs** test page
draws every character large on a crosshair, in a box its measured
size, to check):

- Every custom glyph with an advance has its ink centered in it.
- Symbols meant to work as button labels (arrows, d-pad and face
  buttons, media controls, the close X, the popup icon) are also
  centered on the row's center line, so they sit on a centered
  label's anchor. The popup icon centers the gap between its arrows,
  which is what the eye centers on.
- Overlays drawn under another glyph (the ticket backing) have no
  advance and are placed relative to what they back.

## Two-form icons

Profile icons, flags and account/platform logos come in two forms:

- **Superscript** (the long-standing character, e.g. `FEDORA`): small
  and raised, shown before a player's name. This is what travels in
  names, over the network and in replays.
- **Full-size** (its `_FULL` twin, e.g. `FEDORA_FULL`): emoji-sized
  and centered on the row, for showing framed (the store, the icon
  picker) or as a button label. Newer clients only
  (`SpecialChar.min_engine_build`).

Only the full-size twin has real data. Each superscript entry in the
table is an all-zero placeholder; at startup the engine derives it
from its twin by one transform, `kSuperscriptIconScale` and
`kSuperscriptIconCenterHeight` in `text_graphics.cc`. Tune an icon's
look in its twin (an icon meant to read big is simply calibrated big
there, like the potato); tune how all icons sit before names with
those two constants. The Glyphs page's last section shows sample
icons full-size and superscripted before sample names.

The pairing is `SpecialChar.full_size`, an exhaustive `match`, so a
new member nobody classified fails mypy. `tests/test_bacommon/
test_special_chars.py` checks the pairing is one-to-one and named
`X`/`X_FULL`, that every twin has data and that every superscript's
entry is a placeholder; the engine also refuses to start if a twin's
data is missing.

Full design and history: `docs/initiatives/full-size-icon-glyphs.md`.

## Adding a character

1. **Art:** put it in a free cell on an extras sheet (pre-colored art
   on pages 2-5), publish the `babuiltinassets` package and repin it
   (see `efrohome:docs/global_design/asset-packages.md`). Repin
   bamaster too if it uses the glyph.
2. **Enum:** add a `SpecialChar` member at the next free codepoint,
   with cases in `min_engine_build` (the build that first ships it)
   and `full_size` (`None` for a plain character).
3. **Data:** fill its entry in `g_glyphs_extras` and its sheet in
   `g_glyphs_extras_page`, growing both tables if needed. Center it
   per the conventions above and check it on the Glyphs page.
4. Bump the build (`tools/pcommand version incrementbuild`) so
   `min_engine_build` means something.

## Adding a profile icon (or flag, or logo)

As above, but it's a pair:

1. **Enum:** add `X` and `X_FULL` at consecutive codepoints. In
   `full_size`, give `X` a case returning `X_FULL` and add `X_FULL` to
   the full-size group; give both `min_engine_build` cases.
2. **Data:** fill in `X_FULL`'s entry (sized to read well framed, ink
   centered in its advance and on the row) and its sheet; leave `X`'s
   entry all zeros (it's derived). Give `X` the same sheet as `X_FULL`.
3. Check both on the Glyphs page; add it to the superscript samples
   there if it's an interesting case.
4. **Server:** offering it in the store and icon picker is a separate
   step; see `ballistica-master-server:docs/design/store-icons.md`.
   Only show the `_FULL` form to clients new enough to draw it.
