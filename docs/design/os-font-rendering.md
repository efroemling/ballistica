# OS font rendering

**Description:** Dynamic text is rendered and line-broken (UAX #14) via each OS's native text stack behind one small platform interface, so the engine ships no huge Unicode fonts or line-break tables.

The engine ships pre-baked glyph pages covering a core character set, but the
full Unicode range is far too large to pre-bake. Everything outside the baked
set is rendered at runtime by the host OS's native text stack — CoreText on
Apple, Java Canvas on Android, DirectWrite/Direct2D on Windows, Pango+Cairo on
Linux — through a small platform-virtual interface. This keeps text looking
native-quality everywhere (CJK, Arabic, emoji-adjacent symbols, etc.) without
bundling gigantic fonts.

## Key files

- `src/ballistica/base/graphics/text/text_graphics.h/cc` — glyph management,
  LRU text-bounds cache.
- `src/ballistica/base/graphics/text/text_group.h/cc` — high-level text
  orchestration.
- `src/ballistica/base/graphics/text/text_packer.h/cc` — bin-packing layout of
  OS-rendered spans into textures (32–2048px).
- `src/ballistica/base/graphics/text/font_page_map_data.h` — Unicode →
  glyph-page lookup.
- `src/ballistica/base/graphics/mesh/text_mesh.h/cc` — GPU quad generation per
  character.
- `src/ballistica/core/platform/platform.h` — the platform virtual interface.
- `src/ballistica/core/platform/apple/platform_apple.h/cc` — CoreText impl
  (plus the Pango path for Apple cmake builds).
- `src/ballistica/core/platform/android/platform_android.h/cc` — JNI impl.
- `src/ballistica/core/platform/windows/platform_windows.h/cc` —
  DirectWrite/D2D impl.
- `src/ballistica/core/platform/support/platform_pango.h` — shared inline
  Pango/Cairo helpers used by the Linux (and Apple-cmake) impls.
- `src/ballistica/base/app_platform/apple/TextTextureData.swift` — Swift
  CoreText wrapper.

## The platform virtual interface

Each platform implements five virtuals on `CorePlatform`
(`src/ballistica/core/platform/platform.h`):

```cpp
virtual void GetTextBoundsAndWidth(const std::string& text, Rect* r,
                                   float* width);
virtual void* CreateTextTexture(int width, int height,
                                const std::vector<std::string>& strings,
                                const std::vector<float>& positions,
                                const std::vector<float>& widths, float scale);
virtual uint8_t* GetTextTextureData(void* tex);
virtual void FreeTextTexture(void* tex);
virtual std::vector<int> GetTextLineBreakOffsets(const std::string& text);
```

The graphics layer measures text (`GetTextBoundsAndWidth`), bin-packs the
spans it needs into a texture layout (`text_packer`), asks the platform to
render them all into one texture (`CreateTextTexture`), reads the pixels back
(`GetTextTextureData`), and frees the platform object when done.

`GetTextLineBreakOffsets` is a sibling concern (line *breaking*, not
rendering): it returns utf-8 byte offsets where a new line may begin, per
the OS text stack's Unicode UAX #14 analysis — including dictionary-based
word segmentation for Thai and friends — so the engine never ships Unicode
break tables or word dictionaries. Logic thread only, like measuring. The
base-class fallback (headless etc.) breaks at spaces/newlines only.
Per-backend sources: CFStringTokenizer's `kCFStringTokenizerUnitLineBreak`
(Apple Xcode builds), `android.icu.text.BreakIterator.getLineInstance` over
sync JNI (Android), `IDWriteTextAnalyzer::AnalyzeLineBreakpoints` (Windows),
`pango_get_log_attrs` (Linux + Apple cmake builds). Verified on all four
2026-07-11 at 3–60µs per call (behavior probe + timings:
`babase._text.run_line_break_selftest`, via the private
`_babase.get_text_line_break_offsets` binding). Backends differ slightly
in Thai word choices (ICU vs libthai dictionaries) — cosmetic; don't
golden-test exact offsets cross-platform.

## Per-platform implementations

- **Apple (Xcode builds)** — CoreText drawing into a `CGContext`, wrapped by
  `TextTextureData.swift` and reached over Swift/C++ interop. 26pt system
  font, regular weight (`useBoldFont=false`). Output is RGBA8 premultiplied.
- **Android** — JNI bridge to the Java `Canvas`/`Bitmap` APIs. Note the
  UTF-8 → modified-UTF-16 conversion required at the JNI boundary.
- **Windows** — DirectWrite for layout plus Direct2D for rasterization into a
  D3D11 texture, read back through a staging texture. Pixels arrive as BGRA8
  (swizzled to RGBA on readback); uses a semi-bold weight.
- **Linux (and Apple cmake builds)** — Pango+Cairo, shared via the inline
  helpers in `platform_pango.h`. REQUIRED by default for gui-flavor cmake
  builds as of 2026-07-12 (`REQUIRE_OS_FONT_RENDERING` defaults ON): a
  missing pangocairo fails the configure loudly rather than silently
  producing a build with the internal fallback text handling — pass
  `-DREQUIRE_OS_FONT_RENDERING=OFF` to opt out. On Ubuntu the dependency is
  `libpango1.0-dev` (installed by the public CI build-env action). The
  check lives inside the `else()` of `if(HEADLESS)`, so headless server
  builds never require or link it.

Two Pango details worth keeping:

- Font is "Sans" at `PANGO_WEIGHT_MEDIUM`, sized via
  `pango_font_description_set_absolute_size` — the absolute-size call
  **bypasses system DPI**, keeping metrics consistent with CoreText's 72-DPI
  behavior regardless of how the host configures DPI.
- Cairo's `CAIRO_FORMAT_ARGB32` is little-endian BGRA in memory, so the same
  B↔R swizzle used on Windows is applied on readback.

## Font pages

Characters map to *font pages* via `font_page_map_data.h`:

- **Pages 0–7** — pre-baked regular fonts (~1,280 glyphs total), lazy-loaded
  from `.fdata` files.
- **Page 9989 (kOSRendered)** — the dynamic OS-rendered page; everything not
  covered by the baked pages lands here and goes through the platform
  interface above.
- **Pages 9990–9994 (kExtras)** — custom icons in the Unicode private-use
  area (U+E000–U+F8FF).

## Output convention

All OS renderers produce **white-on-transparent RGBA8 with premultiplied
alpha**; colorization happens in the shader. Because the textures are
premultiplied, drawing them is subject to the caller-premultiply convention —
see `docs/design/premultiplied-alpha.md` (the text drop-shadow shader path
there also branches on this).

## Caching tiers

- **Text bounds** — LRU cache (300 entries) on the logic thread in
  `text_graphics`, since measuring via the OS is comparatively expensive.
- **Generated textures** — hash-keyed in the asset system and shared across
  `TextGroup`s, so identical strings rendered in multiple places reuse one
  texture.
- **Glyph pages** — lazy-loaded on first use and never evicted.
