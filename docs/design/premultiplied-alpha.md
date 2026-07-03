# Premultiplied-alpha rendering

**Description:** The premultiplied-alpha convention: callers premultiply straight modulate colors by alpha when drawing premult textures, else faded content stays full-bright.

Migrated asset-package textures (KTX2) store their RGB **premultiplied by
alpha** and carry the `KHR_DF_FLAG_ALPHA_PREMULTIPLIED` flag in their DFD
(asset-packages "decision #23"). OS-rendered text is premultiplied too. This
note explains the one convention you have to keep in mind when drawing them,
because getting it wrong produces subtle "too bright / won't fade out" bugs.

## How a texture's premult state reaches the blender

`TextureAsset::premultiplied()` is read from the DFD flag at load. In the draw
components (`SimpleComponent`, `ObjectComponent`):

```
premult_blend = premultiplied_ || (texture && texture->premultiplied())
```

- `premult_blend == true`  → `glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)`
  (premultiplied / "over"): the source RGB is **added directly**, weighted only
  by the destination's `1 - srcAlpha`.
- `premult_blend == false` → `glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)`
  (straight alpha): the hardware multiplies source RGB by source alpha for you.

Both paths are kept on purpose — legacy/modder textures (DDS/KTX/PVR) are
straight-alpha and must keep working. The cost of supporting both is
negligible.

## The convention

> **When you draw a premultiplied texture with a *straight* modulate color,
> premultiply the color's RGB by its alpha yourself, at the call site.**

Under premult blend the hardware does **not** weight RGB by alpha — so if you
hand it `(r, g, b, a)` with `a < 1`, the full-brightness `(r, g, b)` is added
and the thing never dims or fades out. Multiplying RGB by `a` at the call site
makes premult blend composite "over" correctly. At `a == 1` it's a no-op, so
fully-opaque content is unaffected — **only faded/semi-transparent content is
sensitive to this.**

Do it per-element, gated on `texture->premultiplied()`, so straight-alpha
textures keep their raw RGB (straight blend already weights them):

```cpp
float cmul = texture->premultiplied() ? alpha : 1.0f;
c.SetColor(r * cmul, g * cmul, b * cmul, alpha);
```

`SetColor(...)` carries this through both its normal config path and its inline
fast-path (`kSimpleComponentInlineColor`), which a centralized premultiply in
`WriteConfig` would not — so the premultiply belongs at the caller, not buried
in the renderer.

Callers that follow this: `text_node`, `text_widget`, `screen_messages`,
`image_widget`, the dev-console caret glow.

## `SetPremultiplied(true)` means "I manage premult myself"

Additive / glow effects (shields, explosions, the text-widget gradient
highlight, etc.) call `SetPremultiplied(true)` to force premult blend
regardless of texture, and supply their colors already in the form they want
(typically additive, RGB > alpha). **Do not** auto-premultiply those — they are
intentionally not "over" composites. The convention above applies only to the
straight-color case (`premultiplied_` not set, texture premultiplied).

## Source art that is genuinely premultiplied

A few sprites (`glow`, `scrollWidgetGlow`) are authored/stored *already
premultiplied* so they can carry RGB brighter than alpha (a real glow that
straight-alpha can't represent). Those get the `SOURCE_PREMULTIPLIED` texture
role: the asset pipeline must **not** re-premultiply them, and their workspace
source PNG must contain premultiplied pixels (not a straight master that the
pipeline premultiplies — a straight white+alpha master can never produce
RGB > alpha).

## Text drop-shadows

The `SHD_SHADOW` fragment path in `program_simple_gl.h` composites the glyph
over a soft black drop-shadow. It branches on a `texPremultiplied` uniform:

- straight textures: premultiply → composite shadow → un-premultiply → emit
  straight (straight blend).
- premultiplied textures: the incoming color is already premultiplied (per the
  convention above), so just composite the shadow into alpha and emit
  premultiplied — no premultiply, no divide.
