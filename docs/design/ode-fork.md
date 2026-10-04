# The ODE fork and its threading contract

**Description:** Thread-safety rules for our maintained ODE fork, whose worlds run on two threads at once — no mutable statics in colliders, per-mesh Opcode state, thread-confined worlds.

## What the fork is

`src/external/open_dynamics_engine-ef/` is a 2000s-era Open Dynamics
Engine (single precision, Opcode 1.3 trimesh colliders, QuickStep
solver) that has been ours to maintain for the game's whole life. It is
not tracked against upstream and never will be: it carries local
fixes, a stripped feature set, and engine-specific changes, and the
game's feel is tuned against its exact behavior. Treat it as
first-party code that happens to keep ODE's file layout and naming —
internal changes are fine, and the expectation is the same as for any
other engine code: keep them clean, keep them commented (the convention
is an `ericf change:` comment at the site explaining *why*), and record
the durable rules here.

Two consumers drive it, on two threads, each world with its own
`dWorld`, `dSpace`/`TerrainCollider`, and contact joint group:

- The **main sim** (`scene_v1/dynamics/`, logic thread): gameplay
  bodies — spazzes, bombs, props — stepped in lockstep with the game.
  One world per scene.
- **Bg-dynamics** (`base/dynamics/bg/`, its own thread):
  cosmetic physics — shrapnel chunks, tendrils, the attachment channel
  (hair/antenna rigs), shadow/height queries — stepped independently and
  read back asynchronously (see `docs/initiatives/bg-dynamics-channels.md`).
  One world for the main game world plus one per scene drawn through a
  view of its own (`BGDynamicsWorldServer`); all of them run on the one
  bg thread, one step at a time, and are made and unmade there.

Both collide against trimesh terrain, and the bg thread does so with
capsules, spheres, boxes and rays *while* the main sim does the same.
Nothing in stock ODE was written for that, so the fork carries the
rules below.

## The contract

1. **Worlds are thread-confined.** A body, joint, geom, space, or
   contact group belongs to exactly one world and is only ever touched
   from that world's thread. Nothing crosses: the bg attachment rig
   mirrors the main sim's anchor body as a *twin* body it owns
   (`bg_dynamics_attachment.cc`) rather than referencing the real one,
   and bg terrain is a separate `dxTriMesh` geom created by each bg
   world (`bg_dynamics_world_server.cc`) over the asset's mesh data.

2. **Trimesh data is shared read-only; trimesh geoms are not.**
   `CollisionMeshAsset` hands both worlds the same `dxTriMeshData`
   (`kShareTriMeshDataBetweenSims`, single-precision builds only —
   the rationale, including why the double-precision vertex cache
   forbids it, is in the comment above that constant in
   `collision_mesh_asset.cc`). The Opcode `Model`/BVTree is immutable
   after build; every collide query reads it and writes only into the
   *geom's* own state, which is why rule 3 exists.

3. **`dxTriMesh` has no mutable static state.** Stock ODE keeps its
   Opcode colliders (`_PlanesCollider`, `_SphereCollider`,
   `_OBBCollider`, `_RayCollider`, `_AABBTreeCollider`, `_LSSCollider`),
   the ray-hit output container (`Faces`), and the default query caches
   (`defaultSphereCache`, `defaultBoxCache` → our `boxCache`,
   `defaultCCylinderCache`) as statics shared by every mesh. Opcode
   colliders write into themselves (touched-primitive lists, settings,
   temporal-coherence bookkeeping) and into the cache on every query, so
   any two concurrent trimesh queries against *any* two meshes raced.
   All of them are per-mesh members now
   (`ode_collision_trimesh_internal.h`). The OBB pair was converted
   years ago for chunks; the sphere pair and the rest followed on
   2026-09-04 when attachment segments started colliding on the bg
   thread (the symptoms were a bus error in `dCollideSTL` and an abort
   in `dCollideCCTL`, both on the *logic* thread — the victim is
   whichever thread loses the race, not the one that introduced it).

4. **Colliders keep per-query state on the stack.** The capsule-vs-
   trimesh collider (`ode_collision_trimesh_ccylinder.cpp`, CroTeam's
   port) used ~25 file-scope statics for its working set — contacts
   buffer, capsule pose, current triangle, best separating axis. They
   now live in `dxCapsuleTriMeshQuery`, one instance stack-allocated per
   `dCollideCCTL` call, with the former static helpers as its methods
   (so the geometry code is byte-for-byte unchanged). The trimesh-vs-
   trimesh collider's `static BVTCache` became a local the same day.
   **Any new or revived collider must follow suit** — the check is
   mechanical:

   ```
   grep -nE '^\s*static ' src/external/open_dynamics_engine-ef/ode/ode_collision_*.cpp \
     | grep -vE 'static (const|inline|void|int|bool|BOOL|dReal|float) '
   ```

   should list only the kernel's dispatch tables (next section). Anything
   else is a race waiting for a second thread.

5. **A collide query touches only what it was handed.** With 3 and 4
   in place, `dCollide(g1, g2, ...)` reads `g1`, `g2`, their bodies'
   poses, and shared immutable mesh data, and writes the caller's
   contact array plus per-geom scratch. That is the whole reason the
   two-thread model works without a lock, and it is what a parallel
   narrow phase *within* one world would build on (see below).

## Local API additions

- `dBodySetSolverIterations(body, n)` / `dBodyGetSolverIterations`
  (`ode_objects.h`, `ode.cpp`, `ode_quickstep.cpp`): a per-body
  quickstep iteration hint. `dxQuickStepper` solves each island with
  the largest hint among its bodies, or the world's count
  (`dWorldSetQuickStepNumIterations`) when none is set. Stock ODE has
  one count per world; the bg world needs debris cheap (3) and
  character rigs at the main sim's 10 in the same world. Max is the
  merge rule so a demanding body always gets its count even if a cheap
  one ends up in its island.

## Known remaining globals

These are the only cross-world shared state left; each is either
init-once or benign, but they are the list to revisit before any
further threading:

- **Collider dispatch table + user classes**
  (`ode_collision_kernel.cpp`: `colliders[][]`, `user_classes[]`,
  `colliders_initialized`). Filled lazily by the first `dxGeom`
  constructor on any thread and read-only afterwards. In practice the
  logic thread creates geoms long before the bg server has anything,
  so this has never bitten, but it is an unsynchronized lazy init —
  if a future startup path could create a bg geom first, pin it with
  an explicit init on the logic thread.
- **`dRand` seed** (`ode_misc.cpp`). QuickStep shuffles constraint
  order with `dRandInt`, so both worlds' steps hit one global seed. A
  data race in the strict sense, but it only perturbs a value that is
  *meant* to be random — no memory unsafety, just cross-world
  non-determinism. A per-world (or per-step, seeded from the world)
  RNG is the fix if determinism or a sanitizer run ever needs it.
- **Error/debug handlers** (`dSetErrorHandler` and friends) — set once
  at startup, read-only after.

## Verification recipe

The bug class here does not reproduce in headless runs (the bg server
does no work there) or in quiet scenes. What does reproduce it is an
8-player stress test in a GUI build with the debug attachment rigs
active, so that both threads collide capsules/spheres against the same
terrain continuously:

```
tools/pcommand test_game_run --gui --instance stressgui --dynamics-profile \
    --stress-test 8 --log 'ba=INFO' --timeout 90
```

(run unsandboxed like every GUI launch). Before the fixes this aborted
within seconds; a clean 90 s run with the profile lines printing is the
pass criterion. The `--dynamics-profile` breakdown also tells you what
collision costs on each thread, which is the number to watch when
adding bg-side collision.

## Where further threading would go

Both are open; neither is started. The contract above is what makes
them tractable.

- **Parallel narrow phase (within one world).** The kernel's
  `dSpaceCollide` callback model already hands out independent
  `(g1, g2)` pairs; with rule 5 the collide calls themselves are
  independent — *except* that rule 3 makes Opcode state per-*mesh*, not
  per-query, so two threads colliding different geoms against the
  *same* terrain mesh would still race on that mesh's collider and
  cache. That is the one remaining step: make the Opcode colliders and
  caches per-query (or per-thread) the way `dxCapsuleTriMeshQuery`
  already is. Contact-joint creation (`dJointCreateContact` into the
  shared group) also has to be serialized or batched per thread.
- **Parallel island solves (QuickStep).** Islands are independent by
  construction and the main sim's cost is roughly one-third collision,
  two-thirds island solve (`--dynamics-profile`, 8-player stress,
  ~130 bodies), so this is the bigger win. Needs: the `dRand` seed
  made per-thread (above); the step's scratch allocation (`ALLOCA` /
  `dAlloc` in `ode_quickstep.cpp`, `ode_step.cpp`) checked for any
  shared arena; and the island-walk in `dxProcessIslands`
  (`ode_util.cpp`) split so islands are dispatched to workers and
  body/joint writes stay island-local. Measure first — at ~130 bodies
  the per-island work may be too small for threading to pay off on
  mobile, and the profile flag exists to answer that before any code
  is written.
