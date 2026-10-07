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

Callers that follow this: `text_node`, `image_node`, `text_widget`,
`screen_messages` (both text passes, plus — missed until a 2026-08 fix for
a fade-end pop — the bottom-message shadow nine-patch and top-message
icons; a "follower" here can still be only partial, so when hunting a
fade bug check every `SetColor` in the file, not just this list),
`image_widget`, `button_widget` (background + icon),
`spinner_widget`, `scroll_widget` / `h_scroll_widget` (troughs, page
buttons, outlines), `container_widget`, `touch_input` (on-screen joystick +
action buttons), `locator_node`, `scorch_node`, `spaz_node` (name text,
billboards, radial meters), the dev-console (`DrawRect`/`DrawText` helpers,
drop shadow, output lines, caret glow), and the on-screen dev-console toggle
button in `ui.cc`. `ObjectComponent` does the same premultiply centrally in
its `WriteConfig` (transparent, non-`SetPremultiplied` case), so its callers
(e.g. `terrain_node`, mesh fades) get it for free.

## The masked-draw additive frame term

The `SHD_MASKED` path in `program_simple_gl.h` (character icons: an icon
texture + colorize tint + `characterIconMask`) *adds* a frame term with zero
alpha on top of the modulated texture:

```glsl
... * vec4(vec3(mask.r), mask.a)
    + vec4(vec3(mask.g) * colorizeColor.rgb + vec3(mask.b), 0.0)
```

Under straight blend the hardware weights all source RGB by fragment alpha at
blend time, so that frame faded with the modulate alpha for free. Under
premult blend (`GL_ONE`) nothing weights it — so faded icons kept a
full-brightness frame ring until the very end (screen-message icons,
elimination scoreboard icons; fixed 2026-08). The shader now scales the
additive term by `mix(1.0, color.a, texPremultiplied)`, with the uniform fed
from the masked shading types in `renderer_gl.cc` (the opaque masked case
sets 0 explicitly since the program object is shared). Callers need no
changes for this term — but their base `SetColor` premultiply (the convention
above) is still required for the texture part of the draw.

### Masks that are not premultiplied

The reasoning above assumes the mask texture itself is premultiplied
(`mask.rgb` already scaled by `mask.a`), which is what the pipeline's
default texture role produces. A mask authored with the **data** role is
not premultiplied — its channels are independent values — and neither is a
straight-alpha mask from a mod. Under straight blending the hardware applied
`mask.a` to the color at blend time; under premult blend nothing does, so
such a mask would draw full-brightness color where its alpha fades.

The masked program therefore has a `maskStraight` uniform (0/1). The
renderer sets it to 1 for a premult-blended draw whose mask texture reports
`premultiplied() == false`, and the shader scales both the `mask.r` term and
the additive frame term by `mix(1.0, mask.a, maskStraight)`. A premultiplied
mask leaves it at 0 and renders exactly as before.

### Texture roles are checked at the slot

Asset-package textures carry their authored role in the file
(`baTextureRole` in the KTX2 key/value data; absent means the default
picture role), surfaced as `TextureAsset::role()`. The render components'
texture setters note what each slot expects — `SetTexture` a picture,
`SetColorizeTexture` / `SetMaskTexture` / `SetMaskUV2Texture` data — and a
mismatch logs one warning per texture, in release builds too. Textures of
unknown role (legacy formats, OS-decoded images, text, render targets) are
never flagged. A texture needed in both kinds of slot gets a data twin
rather than a role change (`black_data`, `white_data`, `soft_rect_mask`,
`soft_rect2_mask` in the builtin package).

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
