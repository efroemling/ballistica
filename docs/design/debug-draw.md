# Debug-draw mode

**Description:** How debug-draw mode (F10) renders physics geometry in place of display meshes, and the render-pass registration traps that silently drop a new shading type.

Debug-draw mode was resurrected in September 2026 (commits `0aa5a366f0`
through `ab2058b0e9`) from a years-dead immediate-mode implementation.
It draws what the physics sim actually collides with, lit and shadowed
like the real scene, so collider/display mismatches are visible.

## Toggling

- **F10** (`Input` → `Graphics::ToggleDebugDraw()`) or the **Gameplay**
  dev-console tab's *Debug Drawing OFF/ON* button
  (`babase/_devconsoletabs.py::DevConsoleTabGameplay`).
- State lives on `Graphics` (logic thread): `debug_draw()` /
  `set_debug_draw()`, mirrored to the renderer's `debug_draw_mode()` for
  the graphics thread. Python: `_babase.get_debug_draw()` /
  `set_debug_draw()`. **Nodes should read `g_base->graphics->debug_draw()`**
  (logic thread), not the renderer copy.
- Bg-dynamics worlds get the flag per step via
  `BGDynamicsWorldServer::StepData::debug_draw` (they run on their own
  thread and can't read `Graphics`).

## What it draws

- **World clear** goes to a mid grey (`kDebugDrawClearColor`,
  `renderer.cc`) since terrain visuals are skipped.
- **Terrain nodes** (`TerrainNode::DrawDebug_`): the collision mesh,
  flat-shaded, receiving lights *and* shadows (`LightShadowType::kTerrain`),
  single-sided — a flipped face shows as a hole. Plus a transparent black
  wireframe of every unique edge (alpha 0.5), drawn in the pass's
  transparent section (depth-tested, no depth write) so the edges of culled
  back faces show through where nothing covers them. Both meshes are built
  lazily on `CollisionMeshAsset` (`GetDebugMesh()` / `GetDebugWireMesh()`)
  from the *preload* payload — gate on `preloaded()`, not `loaded()`;
  collision meshes may never reach the loaded state.
- **Rigid bodies** (`RigidBody::DrawDebug(pass, r, g, b)`): the physics
  shape with lighting only (`kObject`, no self-shadowing). Box, sphere,
  capsule (cylinder + two hemisphere caps, since radius and length scale
  independently), and cylinder (the real sub-sphere ring read straight from
  the ODE geoms). Trimesh returns false. Hooked up for prop nodes (every
  body type), the flag pole, and all spaz bodies (display meshes, eyes,
  wings, gloves off; blob shadows and overlay decorations stay). The
  spaz's hand-placed orientation/stand/punch/IK-anchor fins from the
  original implementation are kept in `SpazNode::DrawDebugBodies_`
  (`kDebugDrawStandBody` gates the stand sphere itself).
- **Regions** (`RigidBody::DrawDebugWireframe`): transparent yellow box
  edges / three great circles, so trigger volumes don't occlude.
- **bg-dynamics chunks** (`BGDynamics::DrawChunks`): all box bodies; the
  snapshot matrices already bake in the box size, so it's the unit debug
  box under each instance matrix. The server skips its display-only
  shrink/sink/flicker matrix effects while debug draw is on. Flag stands
  have no body and draw nothing.

## The facing-ratio shading

`SHD_FACING_RATIO` on `ProgramObjectGL` (one instance,
`obj_lightshad_facing_prog_`, always with `SHD_LIGHT_SHADOW`): a `flat`
varying of `abs(dot(world normal, view dir))` computed per vertex, mapped
to grey `mix(0.1, 0.425, facing)` in place of the texture sample, then the
normal light/shadow projection and vignette. Reached via
`ObjectComponent::SetFacingRatio(true)` →
`ShadingType::kObjectLightShadowFacingRatio` (opaque, single-sided; the
renderer forces culling on). Flat look comes from the *meshes*: every
debug primitive uses unshared verts with one face normal per triangle.

Primitives live on `Graphics` and are built lazily: `debug_box_mesh()`
(unit cube), `debug_sphere_mesh()` (6 stacks × 12 slices; coarse on
purpose so rotation reads), `debug_hemisphere_mesh()` /
`debug_cylinder_mesh()` (capsule parts, axis along z per ODE). The shared
`AppendFlatTri` helper flips winding to face outward, which the culled
draw relies on.

## Debug triangles and lines

`RenderComponent::BeginDebugDrawTriangles()/BeginDebugDrawLines()`,
`Vertex()`, `End()` still exist; the GL renderer now accumulates the
verts and uploads them to small streaming meshes at `End`
(`RendererGL::FlushDebugDraw_`, `mesh_data_debug_gl.h`). Triangles get a
computed face normal and are emitted **twice** (second copy reversed) so
free-form fins read from both sides under the single-sided program. Lines
draw as `GL_LINES` (1 px on GLES/ANGLE — emit thin quads if you ever need
fat lines). Whatever program the component configured is what draws them.
`DrawMesh` also gained `kMeshDrawFlagLines` for indexed line meshes.

## Traps (each cost a round)

- **A new `ShadingType` draws nothing until registered in three places:**
  the renderer's `kShader` switch, the per-pass draw-order tables in
  `render_pass.cc` (`component_types_opaque` / `_transparent`), and
  `Graphics::IsShaderTransparent`. Missing the pass table fails silently.
- **Overlay-3d, light and light-shadow passes accept only transparent
  shadings** (debug-build FatalError). Opaque debug geometry goes in the
  beauty pass.
- **Double-sided is an opt-in per shading type**, not a component flag on
  its own; the debug tri path sidesteps this by doubling geometry.
- The old fins looked like "stray axis lines" to someone who didn't know
  them (green stand-body fins rising from the head, red head fin, yellow
  punch fin); they're intentional.
