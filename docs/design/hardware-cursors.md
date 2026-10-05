# Hardware cursors

**Description:** How OS hardware cursors (Mac NSCursor + SDL) are built from the bundled fallback cursor texture, the load-bearing engine software-cursor fallback, and the `fallback_high_res` path-val knob.

Shipped 2026-07-07 (bamaster recipe deployed prod, internal push-public'd,
pinned as of `a-0.babuiltinassets.260707`).

## Why

Cursor art is single-sourced from the builtin `textures/cursor.png` asset —
no per-platform cursor resources to keep in sync — while matching the old
64pt/128px-retina asset-catalog setup on every platform.

## Pixel source: the bundled fallback texture

`Assets::LoadBundledFallbackTextureRGBA(name)`
(`src/ballistica/base/assets/assets.cc`) decodes a builtin texture's
*bundled fallback-flavor* KTX2 (uncompressed RGBA8 + premult DFD flag) by
reading the bundled manifest.json chain directly — the runtime registry
can't be used (it holds only the resolved flavor, e.g. desktop_v1 BC7 on
warm starts). It bails (with a warning) if the blob entry carries a `c`
compression marker; bundles store texture blobs raw today, but if
`asset_bundle_build` ever starts compressing blobs this needs a
zstd-decompress step (the OS cursor silently degrades to the stock arrow
until then) — the one open loose end, also tracked in `docs/followups.md`
("Hardware cursor: bundled-blob compression assumption").

## Mac (xcode)

`CocoaSupport.customCursorImage()` builds the NSCursor from engine pixels
via `from_swift.GetCursorImage*`; 64pt logical, hotspot (6,6); mips ≥64px
become NSImage reps (128px @2x + 64px @1x). Retina rendering visually
confirmed 2026-07-06, after which the legacy path was purged: asset-catalog
`Cursor macOS.imageset`, the `useEngineCursorImage` gate,
`NSImage.Name.cursor`, `src/resources/cursor.png`, and
`resourcesmakefile.py::_add_macos_cursor` are all gone.

## SDL

`kUseHardwareCursor` in `app_adapter_sdl.cc` flips `HasHardwareCursor()`
true; `CreateHardwareCursor_` un-premultiplies (SDL wants straight alpha),
base surface = 64px mip (`kHardwareCursorLogicalSize`), larger mips attach
via `SDL_AddSurfaceAlternateImage` (high-DPI).

**The toggle is permanent** (decided 2026-07-06): flipping
`kUseHardwareCursor` off is the desktop test lever for the engine
software-cursor path (`Graphics::DrawCursor`), which stays load-bearing for
hardware-cursor-less platforms (Android-with-pointer, any new platform's
default). Don't remove the software path.

## The `fallback_high_res` path-val knob

`fallback_high_res` (bacommon `AssetsV1PathValsTexV1` + bamaster recipe)
halves the fallback flavor's level0_div (2 instead of 4) per asset, giving
the cursor a 128px top mip; it rides the `AssetsV1TexInputV1` cache key with
`store_default=False` so only flagged assets reprice (no recipe-version
bump). It is set on `textures/cursor.png` in the BaBuiltinAssets workspace.

The knob is deliberately NOT exposed in the workspace web UI (obscure by
design). To change it: edit workspace.json via
`tools/pcommand assetworkspace get/put BaBuiltinAssets`, then
`tools/bacloud assetpackage publish babuiltinassets --prod`, then
`make assetpins-latest` in internal (the 260622→260707 pin bump was this
flow). UI/tuner save paths mutate stored texvals in place, so the flag
survives them.

## Testing the cursor path

Exercise it via GUI `test_game_run` +
`test_game_cmd <inst> 'import _babase; _babase.set_camera_manual(True)'`.
Note that automation `scroll_at` does NOT bump `mouse_move_count_`, so
`IsCursorVisible` stays false without real mouse motion.
