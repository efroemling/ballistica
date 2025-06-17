cmake_minimum_required(VERSION 3.12)
project(BallisticaKit)
include(CheckIncludeFile)

option(HEADLESS "build headless server" OFF)
option(TEST_BUILD "include testing features" OFF)
option(DISCORD "enable Discord" OFF)

# Requiring minimum of C++20 currently.
set(CMAKE_CXX_STANDARD 20)

if (APPLE)
  # Seems as of Mojave we need to explicitly pull in homebrew paths.
  # Just hard-coding recommended homebrew install paths for now.
  # Is there a more elegant way to do this?
  if (CMAKE_SYSTEM_PROCESSOR MATCHES arm64)
    list(APPEND CMAKE_PREFIX_PATH /opt/homebrew)
    include_directories("/opt/homebrew/include")
    link_directories("/opt/homebrew/lib")
  else()
    list(APPEND CMAKE_PREFIX_PATH /usr/local)
    include_directories("/usr/local/include")
    link_directories("/usr/local/lib")
  endif()

  # On Mac with homebrew it seems that Requesting 3.X when we've got
  # 3.(X+1) installed will point us at the 3.(X+1) framework but will attempt
  # to load a 3.X library from within it which doesn't exist. So we need
  # to be a bit more explicit telling it where to look. Note: this was last
  # tested with 3.7; should revisit sometime to make sure still applies.
  execute_process(COMMAND "python3.13-config" "--prefix"
    OUTPUT_VARIABLE Python_ROOT_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE)

endif ()
find_package (Python 3.13 REQUIRED EXACT COMPONENTS Development)
  

if (HEADLESS)
  add_definitions(-DBA_HEADLESS_BUILD=1)
 else ()
  find_package(SDL2 QUIET)
  if (SDL2_FOUND)
    if ("${SDL2_LIBRARIES}" STREQUAL "")
      message(WARNING "SDL2_LIBRARIES wasn't set, manually setting to SDL2::SDL2")
      set(SDL2_LIBRARIES "SDL2::SDL2")
    endif ()
    # Getting complaint about space at the end of this on ubuntu16.
    string(STRIP "${SDL2_LIBRARIES}" SDL2_LIBRARIES)
  else ()
    message(FATAL_ERROR "SDL2 not found")
  endif ()
  find_package(OpenGL REQUIRED)
  find_package(OpenAL REQUIRED)
  find_library(OGG_LIBRARY ogg)
  find_library(VORBISFILE_LIBRARY vorbisfile)
  if (NOT OGG_LIBRARY)
    message(FATAL_ERROR "ogg library not found")
  endif ()
  if (NOT VORBISFILE_LIBRARY)
    message(FATAL_ERROR "vorbisfile library not found")
  endif ()
  set(EXTRA_INCLUDE_DIRS ${OPENGL_INCLUDE_DIRS}
    ${OPENAL_INCLUDE_DIR} ${SDL2_INCLUDE_DIRS})
  set(EXTRA_LIBRARIES ogg vorbisfile ${OPENGL_LIBRARIES} ${OPENAL_LIBRARY})
endif ()

if (TEST_BUILD)
  add_definitions(-DBA_VARIANT_TEST_BUILD=1)
endif ()

# Currently seeing warnings about parameter order changing in GCC 7.1
# on Raspberry Pi builds. We never need to care about C++ abi compatibility
# so just silencing them for now. Can maybe remove this later if they stop.
if (CMAKE_CXX_COMPILER_ID MATCHES GNU)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-psabi")
endif()

set(BA_SRC_ROOT ../src)
include_directories(${BA_SRC_ROOT})
add_compile_options(-include ballistica/shared/buildconfig/buildconfig_cmake.h)

if (CMAKE_BUILD_TYPE MATCHES Debug)
  add_definitions(-DBA_DEBUG_BUILD=1)
else ()
  # It seems that cmake can choose -O2 sometimes and -O3 sometimes
  # for release builds (depending on Release vs RelWithDebInfo, etc).
  # Let's keep all our non-debug builds consistent at -O3 for now; can
  # revisit if it causes problems.
  add_definitions(-O3)
endif ()

set(ODE_SRC_ROOT ${BA_SRC_ROOT}/external/open_dynamics_engine-ef)

add_library(ode
  ${ODE_SRC_ROOT}/ode/IceAABB.cpp
  ${ODE_SRC_ROOT}/ode/IceContainer.cpp
  ${ODE_SRC_ROOT}/ode/IceHPoint.cpp
  ${ODE_SRC_ROOT}/ode/IceIndexedTriangle.cpp
  ${ODE_SRC_ROOT}/ode/IceMatrix3x3.cpp
  ${ODE_SRC_ROOT}/ode/IceMatrix4x4.cpp
  ${ODE_SRC_ROOT}/ode/IceOBB.cpp
  ${ODE_SRC_ROOT}/ode/IcePlane.cpp
  ${ODE_SRC_ROOT}/ode/IcePoint.cpp
  ${ODE_SRC_ROOT}/ode/IceRandom.cpp
  ${ODE_SRC_ROOT}/ode/IceRay.cpp
  ${ODE_SRC_ROOT}/ode/IceRevisitedRadix.cpp
  ${ODE_SRC_ROOT}/ode/IceSegment.cpp
  ${ODE_SRC_ROOT}/ode/IceTriangle.cpp
  ${ODE_SRC_ROOT}/ode/IceUtils.cpp
  ${ODE_SRC_ROOT}/ode/ode.cpp
  ${ODE_SRC_ROOT}/ode/ode_array.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_cylinder_box.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_cylinder_plane.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_cylinder_sphere.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_cylinder_trimesh.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_kernel.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_quadtreespace.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_sapspace.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_space.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_std.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_transform.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_trimesh.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_trimesh_box.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_trimesh_ccylinder.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_trimesh_distance.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_trimesh_plane.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_trimesh_ray.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_trimesh_sphere.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_trimesh_trimesh.cpp
  ${ODE_SRC_ROOT}/ode/ode_collision_util.cpp
  ${ODE_SRC_ROOT}/ode/ode_error.cpp
  ${ODE_SRC_ROOT}/ode/ode_export-diff.cpp
  ${ODE_SRC_ROOT}/ode/ode_fastdot.cpp
  ${ODE_SRC_ROOT}/ode/ode_fastldlt.cpp
  ${ODE_SRC_ROOT}/ode/ode_fastlsolve.cpp
  ${ODE_SRC_ROOT}/ode/ode_fastltsolve.cpp
  ${ODE_SRC_ROOT}/ode/ode_joint.cpp
  ${ODE_SRC_ROOT}/ode/ode_lcp.cpp
  ${ODE_SRC_ROOT}/ode/ode_mass.cpp
  ${ODE_SRC_ROOT}/ode/ode_mat.cpp
  ${ODE_SRC_ROOT}/ode/ode_math.cpp
  ${ODE_SRC_ROOT}/ode/ode_matrix.cpp
  ${ODE_SRC_ROOT}/ode/ode_memory.cpp
  ${ODE_SRC_ROOT}/ode/ode_misc.cpp
  ${ODE_SRC_ROOT}/ode/ode_obstack.cpp
  ${ODE_SRC_ROOT}/ode/ode_quickstep.cpp
  ${ODE_SRC_ROOT}/ode/ode_rotation.cpp
  ${ODE_SRC_ROOT}/ode/ode_step.cpp
  ${ODE_SRC_ROOT}/ode/ode_stepfast.cpp
  ${ODE_SRC_ROOT}/ode/ode_timer.cpp
  ${ODE_SRC_ROOT}/ode/ode_util.cpp
  ${ODE_SRC_ROOT}/ode/OPC_AABBCollider.cpp
  ${ODE_SRC_ROOT}/ode/OPC_AABBTree.cpp
  ${ODE_SRC_ROOT}/ode/OPC_BaseModel.cpp
  ${ODE_SRC_ROOT}/ode/OPC_BoxPruning.cpp
  ${ODE_SRC_ROOT}/ode/OPC_Collider.cpp
  ${ODE_SRC_ROOT}/ode/OPC_HybridModel.cpp
  ${ODE_SRC_ROOT}/ode/OPC_LSSCollider.cpp
  ${ODE_SRC_ROOT}/ode/OPC_MeshInterface.cpp
  ${ODE_SRC_ROOT}/ode/OPC_Model.cpp
  ${ODE_SRC_ROOT}/ode/OPC_OBBCollider.cpp
  ${ODE_SRC_ROOT}/ode/OPC_OptimizedTree.cpp
  ${ODE_SRC_ROOT}/ode/OPC_PlanesCollider.cpp
  ${ODE_SRC_ROOT}/ode/OPC_RayCollider.cpp
  ${ODE_SRC_ROOT}/ode/OPC_SphereCollider.cpp
  ${ODE_SRC_ROOT}/ode/OPC_SweepAndPrune.cpp
  ${ODE_SRC_ROOT}/ode/OPC_TreeBuilders.cpp
  ${ODE_SRC_ROOT}/ode/OPC_TreeCollider.cpp
  ${ODE_SRC_ROOT}/ode/OPC_VolumeCollider.cpp
  ${ODE_SRC_ROOT}/ode/Opcode.cpp
  )
target_include_directories(ode PRIVATE ${ODE_SRC_ROOT})

# Necessary on GCC to allow linking in to our .so version.
# (but disabling semantic-interposition should lessen the associated speed hit).
if (CMAKE_CXX_COMPILER_ID MATCHES GNU)
  target_compile_options(ode PRIVATE -fPIC -fno-semantic-interposition)
endif ()

# NOTE: There used to be an issue with optimized GCC builds where mesh
# collisions would fail randomly, leading to characters falling through
# floors somewhat regularly. For this reason I was limiting optimization to
# -O1 for the rigid body library. However, as of April 2021, all seems
# well when testing on arm64 and x86-64 linux builds. (I think)
# The last time I remember seeing this bug was around 2016 I believe, but I
# haven't looked for it since. Perhaps GCC was fixed or perhaps the error
# was limited to 32 bit x86 builds; in either case we should be good, as
# we're no longer building any 32 bit x86 builds using GCC.
# Keeping this in here commented out just in case it rears its ugly head
# again though.
# if (CMAKE_BUILD_TYPE MATCHES Release)
#   if (CMAKE_CXX_COMPILER_ID MATCHES GNU)
#     target_compile_options(ode PRIVATE -O1)
#   endif()
# endif ()

set(BALLISTICA_SOURCES
  ${BA_SRC_ROOT}/external/qr_code_generator/QrCode.cpp
  # AUTOGENERATED_PUBLIC_BEGIN (this section is managed by the "update_project" tool)
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter.cc
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter.h
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_apple.cc
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_apple.h
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_headless.cc
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_headless.h
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_sdl.cc
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_sdl.h
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_vr.cc
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_vr.h
  ${BA_SRC_ROOT}/ballistica/base/app_mode/app_mode.cc
  ${BA_SRC_ROOT}/ballistica/base/app_mode/app_mode.h
  ${BA_SRC_ROOT}/ballistica/base/app_mode/empty_app_mode.cc
  ${BA_SRC_ROOT}/ballistica/base/app_mode/empty_app_mode.h
  ${BA_SRC_ROOT}/ballistica/base/assets/asset.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/asset.h
  ${BA_SRC_ROOT}/ballistica/base/assets/assets.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/assets.h
  ${BA_SRC_ROOT}/ballistica/base/assets/assets_server.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/assets_server.h
  ${BA_SRC_ROOT}/ballistica/base/assets/collision_mesh_asset.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/collision_mesh_asset.h
  ${BA_SRC_ROOT}/ballistica/base/assets/data_asset.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/data_asset.h
  ${BA_SRC_ROOT}/ballistica/base/assets/mesh_asset.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/mesh_asset.h
  ${BA_SRC_ROOT}/ballistica/base/assets/mesh_asset_renderer_data.h
  ${BA_SRC_ROOT}/ballistica/base/assets/sound_asset.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/sound_asset.h
  ${BA_SRC_ROOT}/ballistica/base/assets/texture_asset.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/texture_asset.h
  ${BA_SRC_ROOT}/ballistica/base/assets/texture_asset_preload_data.cc
  ${BA_SRC_ROOT}/ballistica/base/assets/texture_asset_preload_data.h
  ${BA_SRC_ROOT}/ballistica/base/assets/texture_asset_renderer_data.h
  ${BA_SRC_ROOT}/ballistica/base/audio/al_sys.cc
  ${BA_SRC_ROOT}/ballistica/base/audio/al_sys.h
  ${BA_SRC_ROOT}/ballistica/base/audio/audio.cc
  ${BA_SRC_ROOT}/ballistica/base/audio/audio.h
  ${BA_SRC_ROOT}/ballistica/base/audio/audio_server.cc
  ${BA_SRC_ROOT}/ballistica/base/audio/audio_server.h
  ${BA_SRC_ROOT}/ballistica/base/audio/audio_source.cc
  ${BA_SRC_ROOT}/ballistica/base/audio/audio_source.h
  ${BA_SRC_ROOT}/ballistica/base/audio/audio_streamer.cc
  ${BA_SRC_ROOT}/ballistica/base/audio/audio_streamer.h
  ${BA_SRC_ROOT}/ballistica/base/audio/ogg_stream.cc
  ${BA_SRC_ROOT}/ballistica/base/audio/ogg_stream.h
  ${BA_SRC_ROOT}/ballistica/base/base.cc
  ${BA_SRC_ROOT}/ballistica/base/base.h
  ${BA_SRC_ROOT}/ballistica/base/discord/discord.cc
  ${BA_SRC_ROOT}/ballistica/base/discord/discord.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics.cc
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_draw_snapshot.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_fuse.cc
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_fuse.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_fuse_data.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_height_cache.cc
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_height_cache.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_server.cc
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_server.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_shadow.cc
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_shadow.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_shadow_data.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_volume_light.cc
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_volume_light.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/bg/bg_dynamics_volume_light_data.h
  ${BA_SRC_ROOT}/ballistica/base/dynamics/collision_cache.cc
  ${BA_SRC_ROOT}/ballistica/base/dynamics/collision_cache.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/empty_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/object_component.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/object_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/post_process_component.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/post_process_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/render_component.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/render_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/shield_component.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/shield_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/simple_component.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/simple_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/smoke_component.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/smoke_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/special_component.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/special_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/sprite_component.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/component/sprite_component.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/framebuffer_object_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/gl_sys.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/gl_sys.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/gl_sys_windows.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/gl_sys_windows.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/mesh/mesh_asset_data_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/mesh/mesh_data_dual_texture_full_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/mesh/mesh_data_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/mesh/mesh_data_object_split_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/mesh/mesh_data_simple_full_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/mesh/mesh_data_simple_split_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/mesh/mesh_data_smoke_full_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/mesh/mesh_data_sprite_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/program/program_blur_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/program/program_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/program/program_object_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/program/program_post_process_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/program/program_shield_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/program/program_simple_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/program/program_smoke_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/program/program_sprite_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/render_target_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/renderer_gl.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/renderer_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/gl/texture_data_gl.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/graphics.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/graphics.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/graphics_server.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/graphics_server.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/graphics_vr.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/graphics_vr.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/image_mesh.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/image_mesh.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_buffer.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_buffer_base.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_buffer_vertex_simple_full.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_buffer_vertex_smoke_full.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_buffer_vertex_sprite.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_data.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_data.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_data_client_handle.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_data_client_handle.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_index_buffer_16.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_index_buffer_32.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_indexed.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_indexed_base.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_indexed_dual_texture_full.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_indexed_object_split.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_indexed_simple_full.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_indexed_simple_split.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_indexed_smoke_full.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_indexed_static_dynamic.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_non_indexed.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/mesh_renderer_data.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/nine_patch_mesh.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/nine_patch_mesh.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/sprite_mesh.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/text_mesh.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/mesh/text_mesh.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/renderer/framebuffer.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/renderer/render_pass.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/renderer/render_pass.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/renderer/render_target.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/renderer/render_target.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/renderer/renderer.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/renderer/renderer.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/area_of_interest.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/area_of_interest.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/camera.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/camera.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/frame_def.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/frame_def.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/graphics_client_context.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/graphics_client_context.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/graphics_settings.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/graphics_settings.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/net_graph.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/net_graph.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/render_command_buffer.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/screen_messages.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/support/screen_messages.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/text/font_page_map_data.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/text/text_graphics.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/text/text_graphics.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/text/text_group.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/text/text_group.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/text/text_packer.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/text/text_packer.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/texture/dds.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/texture/dds.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/texture/ktx.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/texture/ktx.h
  ${BA_SRC_ROOT}/ballistica/base/graphics/texture/pvr.cc
  ${BA_SRC_ROOT}/ballistica/base/graphics/texture/pvr.h
  ${BA_SRC_ROOT}/ballistica/base/input/device/input_device.cc
  ${BA_SRC_ROOT}/ballistica/base/input/device/input_device.h
  ${BA_SRC_ROOT}/ballistica/base/input/device/input_device_delegate.cc
  ${BA_SRC_ROOT}/ballistica/base/input/device/input_device_delegate.h
  ${BA_SRC_ROOT}/ballistica/base/input/device/joystick_input.cc
  ${BA_SRC_ROOT}/ballistica/base/input/device/joystick_input.h
  ${BA_SRC_ROOT}/ballistica/base/input/device/keyboard_input.cc
  ${BA_SRC_ROOT}/ballistica/base/input/device/keyboard_input.h
  ${BA_SRC_ROOT}/ballistica/base/input/device/test_input.cc
  ${BA_SRC_ROOT}/ballistica/base/input/device/test_input.h
  ${BA_SRC_ROOT}/ballistica/base/input/device/touch_input.cc
  ${BA_SRC_ROOT}/ballistica/base/input/device/touch_input.h
  ${BA_SRC_ROOT}/ballistica/base/input/input.cc
  ${BA_SRC_ROOT}/ballistica/base/input/input.h
  ${BA_SRC_ROOT}/ballistica/base/input/support/remote_app_server.cc
  ${BA_SRC_ROOT}/ballistica/base/input/support/remote_app_server.h
  ${BA_SRC_ROOT}/ballistica/base/logic/logic.cc
  ${BA_SRC_ROOT}/ballistica/base/logic/logic.h
  ${BA_SRC_ROOT}/ballistica/base/networking/network_reader.cc
  ${BA_SRC_ROOT}/ballistica/base/networking/network_reader.h
  ${BA_SRC_ROOT}/ballistica/base/networking/network_writer.cc
  ${BA_SRC_ROOT}/ballistica/base/networking/network_writer.h
  ${BA_SRC_ROOT}/ballistica/base/networking/networking.cc
  ${BA_SRC_ROOT}/ballistica/base/networking/networking.h
  ${BA_SRC_ROOT}/ballistica/base/platform/apple/base_platform_apple.cc
  ${BA_SRC_ROOT}/ballistica/base/platform/apple/base_platform_apple.h
  ${BA_SRC_ROOT}/ballistica/base/platform/base_platform.cc
  ${BA_SRC_ROOT}/ballistica/base/platform/base_platform.h
  ${BA_SRC_ROOT}/ballistica/base/platform/linux/base_platform_linux.cc
  ${BA_SRC_ROOT}/ballistica/base/platform/linux/base_platform_linux.h
  ${BA_SRC_ROOT}/ballistica/base/platform/support/min_sdl_key_names.h
  ${BA_SRC_ROOT}/ballistica/base/platform/windows/base_platform_windows.cc
  ${BA_SRC_ROOT}/ballistica/base/platform/windows/base_platform_windows.h
  ${BA_SRC_ROOT}/ballistica/base/python/base_python.cc
  ${BA_SRC_ROOT}/ballistica/base/python/base_python.h
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_app_timer.cc
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_app_timer.h
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_context_call.cc
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_context_call.h
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_context_ref.cc
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_context_ref.h
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_display_timer.cc
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_display_timer.h
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_env.cc
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_env.h
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_feature_set_data.cc
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_feature_set_data.h
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_simple_sound.cc
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_simple_sound.h
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_vec3.cc
  ${BA_SRC_ROOT}/ballistica/base/python/class/python_class_vec3.h
  ${BA_SRC_ROOT}/ballistica/base/python/methods/python_methods_base_1.cc
  ${BA_SRC_ROOT}/ballistica/base/python/methods/python_methods_base_1.h
  ${BA_SRC_ROOT}/ballistica/base/python/methods/python_methods_base_2.cc
  ${BA_SRC_ROOT}/ballistica/base/python/methods/python_methods_base_2.h
  ${BA_SRC_ROOT}/ballistica/base/python/methods/python_methods_base_3.cc
  ${BA_SRC_ROOT}/ballistica/base/python/methods/python_methods_base_3.h
  ${BA_SRC_ROOT}/ballistica/base/python/support/python_context_call.cc
  ${BA_SRC_ROOT}/ballistica/base/python/support/python_context_call.h
  ${BA_SRC_ROOT}/ballistica/base/python/support/python_context_call_runnable.h
  ${BA_SRC_ROOT}/ballistica/base/support/app_config.cc
  ${BA_SRC_ROOT}/ballistica/base/support/app_config.h
  ${BA_SRC_ROOT}/ballistica/base/support/app_timer.h
  ${BA_SRC_ROOT}/ballistica/base/support/base_build_switches.cc
  ${BA_SRC_ROOT}/ballistica/base/support/base_build_switches.h
  ${BA_SRC_ROOT}/ballistica/base/support/classic_soft.h
  ${BA_SRC_ROOT}/ballistica/base/support/context.cc
  ${BA_SRC_ROOT}/ballistica/base/support/context.h
  ${BA_SRC_ROOT}/ballistica/base/support/display_timer.h
  ${BA_SRC_ROOT}/ballistica/base/support/plus_soft.h
  ${BA_SRC_ROOT}/ballistica/base/support/repeater.cc
  ${BA_SRC_ROOT}/ballistica/base/support/repeater.h
  ${BA_SRC_ROOT}/ballistica/base/support/stdio_console.cc
  ${BA_SRC_ROOT}/ballistica/base/support/stdio_console.h
  ${BA_SRC_ROOT}/ballistica/base/ui/dev_console.cc
  ${BA_SRC_ROOT}/ballistica/base/ui/dev_console.h
  ${BA_SRC_ROOT}/ballistica/base/ui/ui.cc
  ${BA_SRC_ROOT}/ballistica/base/ui/ui.h
  ${BA_SRC_ROOT}/ballistica/base/ui/ui_delegate.h
  ${BA_SRC_ROOT}/ballistica/base/ui/widget_message.h
  ${BA_SRC_ROOT}/ballistica/classic/classic.cc
  ${BA_SRC_ROOT}/ballistica/classic/classic.h
  ${BA_SRC_ROOT}/ballistica/classic/python/classic_python.cc
  ${BA_SRC_ROOT}/ballistica/classic/python/classic_python.h
  ${BA_SRC_ROOT}/ballistica/classic/python/methods/python_methods_classic.cc
  ${BA_SRC_ROOT}/ballistica/classic/python/methods/python_methods_classic.h
  ${BA_SRC_ROOT}/ballistica/classic/support/classic_app_mode.cc
  ${BA_SRC_ROOT}/ballistica/classic/support/classic_app_mode.h
  ${BA_SRC_ROOT}/ballistica/classic/support/stress_test.cc
  ${BA_SRC_ROOT}/ballistica/classic/support/stress_test.h
  ${BA_SRC_ROOT}/ballistica/classic/support/v1_account.cc
  ${BA_SRC_ROOT}/ballistica/classic/support/v1_account.h
  ${BA_SRC_ROOT}/ballistica/core/core.cc
  ${BA_SRC_ROOT}/ballistica/core/core.h
  ${BA_SRC_ROOT}/ballistica/core/logging/logging.cc
  ${BA_SRC_ROOT}/ballistica/core/logging/logging.h
  ${BA_SRC_ROOT}/ballistica/core/logging/logging_macros.h
  ${BA_SRC_ROOT}/ballistica/core/platform/apple/core_platform_apple.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/apple/core_platform_apple.h
  ${BA_SRC_ROOT}/ballistica/core/platform/core_platform.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/core_platform.h
  ${BA_SRC_ROOT}/ballistica/core/platform/linux/core_platform_linux.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/linux/core_platform_linux.h
  ${BA_SRC_ROOT}/ballistica/core/platform/support/min_sdl.h
  ${BA_SRC_ROOT}/ballistica/core/platform/windows/core_platform_windows.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/windows/core_platform_windows.h
  ${BA_SRC_ROOT}/ballistica/core/python/core_python.cc
  ${BA_SRC_ROOT}/ballistica/core/python/core_python.h
  ${BA_SRC_ROOT}/ballistica/core/support/base_soft.h
  ${BA_SRC_ROOT}/ballistica/core/support/core_config.cc
  ${BA_SRC_ROOT}/ballistica/core/support/core_config.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_asset.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_asset.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_collision_mesh.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_collision_mesh.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_cube_map_texture.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_cube_map_texture.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_data_asset.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_data_asset.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_mesh.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_mesh.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_sound.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_sound.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_texture.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/assets/scene_texture.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_set.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_set.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_to_client.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_to_client.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_to_client_udp.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_to_client_udp.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_to_host.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_to_host.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_to_host_udp.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/connection/connection_to_host_udp.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/collision.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/dynamics.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/dynamics.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/impact_sound_material_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/impact_sound_material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material_component.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material_component.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material_condition_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material_condition_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material_context.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/material_context.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/node_message_material_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/node_message_material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/node_mod_material_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/node_mod_material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/node_user_msg_mat_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/node_user_msg_mat_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/part_mod_material_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/part_mod_material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/python_call_material_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/python_call_material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/roll_sound_material_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/roll_sound_material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/skid_sound_material_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/skid_sound_material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/sound_material_action.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/material/sound_material_action.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/part.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/part.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/rigid_body.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/dynamics/rigid_body.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/anim_curve_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/anim_curve_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/bomb_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/bomb_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/combine_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/combine_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/explosion_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/explosion_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/flag_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/flag_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/flash_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/flash_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/globals_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/globals_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/image_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/image_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/light_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/light_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/locator_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/locator_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/math_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/math_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/node_attribute.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/node_attribute.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/node_attribute_connection.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/node_attribute_connection.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/node_type.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/null_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/null_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/player_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/player_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/prop_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/prop_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/region_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/region_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/scorch_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/scorch_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/session_globals_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/session_globals_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/shield_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/shield_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/sound_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/sound_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/spaz_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/spaz_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/terrain_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/terrain_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/text_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/text_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/texture_sequence_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/texture_sequence_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/time_display_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/node/time_display_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_activity_data.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_activity_data.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_base_timer.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_base_timer.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_input_device.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_input_device.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_material.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_material.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_node.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_node.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_collision_mesh.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_collision_mesh.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_data_asset.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_data_asset.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_mesh.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_mesh.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_sound.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_sound.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_texture.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_texture.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_timer.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_scene_timer.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_session_data.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_session_data.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_session_player.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/class/python_class_session_player.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/methods/python_methods_assets.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/methods/python_methods_assets.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/methods/python_methods_input.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/methods/python_methods_input.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/methods/python_methods_networking.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/methods/python_methods_networking.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/methods/python_methods_scene.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/methods/python_methods_scene.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/scene_v1_python.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/python/scene_v1_python.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/scene_v1.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/scene_v1.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_controller_interface.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_input_device.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_input_device.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_input_device_delegate.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_input_device_delegate.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_session.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_session.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_session_net.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_session_net.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_session_replay.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/client_session_replay.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/host_activity.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/host_activity.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/host_session.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/host_session.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/huffman.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/huffman.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/player.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/player.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/player_spec.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/player_spec.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/replay_writer.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/replay_writer.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/scene.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/scene.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/scene_v1_context.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/scene_v1_context.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/scene_v1_input_device_delegate.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/scene_v1_input_device_delegate.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/session.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/session.h
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/session_stream.cc
  ${BA_SRC_ROOT}/ballistica/scene_v1/support/session_stream.h
  ${BA_SRC_ROOT}/ballistica/shared/ballistica.cc
  ${BA_SRC_ROOT}/ballistica/shared/ballistica.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_cmake.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_common.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_windows_common.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_windows_headless.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_windows_testbuild.h
  ${BA_SRC_ROOT}/ballistica/shared/foundation/event_loop.cc
  ${BA_SRC_ROOT}/ballistica/shared/foundation/event_loop.h
  ${BA_SRC_ROOT}/ballistica/shared/foundation/exception.cc
  ${BA_SRC_ROOT}/ballistica/shared/foundation/exception.h
  ${BA_SRC_ROOT}/ballistica/shared/foundation/fatal_error.cc
  ${BA_SRC_ROOT}/ballistica/shared/foundation/fatal_error.h
  ${BA_SRC_ROOT}/ballistica/shared/foundation/feature_set_native_component.cc
  ${BA_SRC_ROOT}/ballistica/shared/foundation/feature_set_native_component.h
  ${BA_SRC_ROOT}/ballistica/shared/foundation/inline.cc
  ${BA_SRC_ROOT}/ballistica/shared/foundation/macros.cc
  ${BA_SRC_ROOT}/ballistica/shared/foundation/macros.h
  ${BA_SRC_ROOT}/ballistica/shared/foundation/object.cc
  ${BA_SRC_ROOT}/ballistica/shared/foundation/object.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/base64.cc
  ${BA_SRC_ROOT}/ballistica/shared/generic/base64.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/buffer.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/json.cc
  ${BA_SRC_ROOT}/ballistica/shared/generic/json.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/lambda_runnable.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/native_stack_trace.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/runnable.cc
  ${BA_SRC_ROOT}/ballistica/shared/generic/runnable.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/snapshot.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/timer_list.cc
  ${BA_SRC_ROOT}/ballistica/shared/generic/timer_list.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/utf8.cc
  ${BA_SRC_ROOT}/ballistica/shared/generic/utf8.h
  ${BA_SRC_ROOT}/ballistica/shared/generic/utils.cc
  ${BA_SRC_ROOT}/ballistica/shared/generic/utils.h
  ${BA_SRC_ROOT}/ballistica/shared/math/matrix44f.cc
  ${BA_SRC_ROOT}/ballistica/shared/math/matrix44f.h
  ${BA_SRC_ROOT}/ballistica/shared/math/point2d.h
  ${BA_SRC_ROOT}/ballistica/shared/math/random.cc
  ${BA_SRC_ROOT}/ballistica/shared/math/random.h
  ${BA_SRC_ROOT}/ballistica/shared/math/rect.h
  ${BA_SRC_ROOT}/ballistica/shared/math/vector2f.h
  ${BA_SRC_ROOT}/ballistica/shared/math/vector3f.cc
  ${BA_SRC_ROOT}/ballistica/shared/math/vector3f.h
  ${BA_SRC_ROOT}/ballistica/shared/math/vector4f.h
  ${BA_SRC_ROOT}/ballistica/shared/networking/networking_sys.h
  ${BA_SRC_ROOT}/ballistica/shared/networking/sockaddr.cc
  ${BA_SRC_ROOT}/ballistica/shared/networking/sockaddr.h
  ${BA_SRC_ROOT}/ballistica/shared/python/python.cc
  ${BA_SRC_ROOT}/ballistica/shared/python/python.h
  ${BA_SRC_ROOT}/ballistica/shared/python/python_class.cc
  ${BA_SRC_ROOT}/ballistica/shared/python/python_class.h
  ${BA_SRC_ROOT}/ballistica/shared/python/python_command.cc
  ${BA_SRC_ROOT}/ballistica/shared/python/python_command.h
  ${BA_SRC_ROOT}/ballistica/shared/python/python_macros.h
  ${BA_SRC_ROOT}/ballistica/shared/python/python_module_builder.h
  ${BA_SRC_ROOT}/ballistica/shared/python/python_object_set.cc
  ${BA_SRC_ROOT}/ballistica/shared/python/python_object_set.h
  ${BA_SRC_ROOT}/ballistica/shared/python/python_ref.cc
  ${BA_SRC_ROOT}/ballistica/shared/python/python_ref.h
  ${BA_SRC_ROOT}/ballistica/template_fs/python/class/python_class_hello.cc
  ${BA_SRC_ROOT}/ballistica/template_fs/python/class/python_class_hello.h
  ${BA_SRC_ROOT}/ballistica/template_fs/python/methods/python_methods_template_fs.cc
  ${BA_SRC_ROOT}/ballistica/template_fs/python/methods/python_methods_template_fs.h
  ${BA_SRC_ROOT}/ballistica/template_fs/python/template_fs_python.cc
  ${BA_SRC_ROOT}/ballistica/template_fs/python/template_fs_python.h
  ${BA_SRC_ROOT}/ballistica/template_fs/template_fs.cc
  ${BA_SRC_ROOT}/ballistica/template_fs/template_fs.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/class/python_class_ui_mesh.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/class/python_class_ui_mesh.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/class/python_class_ui_sound.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/class/python_class_ui_sound.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/class/python_class_ui_texture.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/class/python_class_ui_texture.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/class/python_class_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/class/python_class_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/methods/python_methods_ui_v1.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/methods/python_methods_ui_v1.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/ui_v1_python.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/python/ui_v1_python.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/ui_v1.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/ui_v1.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/button_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/button_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/check_box_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/check_box_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/column_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/column_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/container_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/container_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/h_scroll_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/h_scroll_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/image_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/image_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/root_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/root_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/row_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/row_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/scroll_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/scroll_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/spinner_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/spinner_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/stack_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/stack_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/text_widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/text_widget.h
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/widget.cc
  ${BA_SRC_ROOT}/ballistica/ui_v1/widget/widget.h
  # AUTOGENERATED_PUBLIC_END
)

# BallisticaKit monolithic binary.
add_executable(ballisticakitbin ${BALLISTICA_SOURCES})

#++++++++++++++++++++++++discord_sdk+++++++++++++++++++++++++++++++
if (DISCORD)
set(DISCORD_SDK_ROOT "${CMAKE_SOURCE_DIR}/../src/external/discord_social_sdk")
set(DISCORD_SDK_INCLUDE_DIR "${DISCORD_SDK_ROOT}/include")
set(DISCORD_SDK_LIB_DIR "${DISCORD_SDK_ROOT}/lib/release")
set(DISCORD_SDK_BIN_DIR "${DISCORD_SDK_ROOT}/bin/release")

# Include Discord SDK headers
include_directories(${DISCORD_SDK_INCLUDE_DIR})

# Platform-specific Social SDK library paths
if(WIN32)
    set(DISCORD_LIB_PATH "${DISCORD_SDK_LIB_DIR}/discord_partner_sdk.lib")
    set(DISCORD_SHARED_LIB "${DISCORD_SDK_BIN_DIR}/discord_partner_sdk.dll")
elseif(APPLE)
    set(DISCORD_LIB_PATH "${DISCORD_SDK_LIB_DIR}/libdiscord_partner_sdk.dylib")
    set(DISCORD_SHARED_LIB "${DISCORD_SDK_LIB_DIR}/libdiscord_partner_sdk.dylib")
else() # Linux
    set(DISCORD_LIB_PATH "${DISCORD_SDK_LIB_DIR}/libdiscord_partner_sdk.so")
    set(DISCORD_SHARED_LIB "${DISCORD_SDK_LIB_DIR}/libdiscord_partner_sdk.so")
endif()

# need to link to this instead
# Copy the Discord shared library to the output directory
add_custom_command(TARGET ballisticakitbin
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${DISCORD_SHARED_LIB}"
        $<TARGET_FILE_DIR:ballisticakitbin>)

set(EXTRA_INCLUDE_DIRS ${EXTRA_INCLUDE_DIRS} ${DISCORD_SDK_INCLUDE_DIR})
set(EXTRA_LIBRARIES ${EXTRA_LIBRARIES} ${DISCORD_LIB_PATH})
endif() #DISCORD

# Gets -rdynamic added when linking gcc builds which exports all symbols
# which gives us more meaningful stack traces using backtrace_symbols().  
set_target_properties(ballisticakitbin PROPERTIES ENABLE_EXPORTS 1)
  
if (HEADLESS)
  set_target_properties(ballisticakitbin
    PROPERTIES OUTPUT_NAME "ballisticakit_headless")
else ()
  set_target_properties(ballisticakitbin
    PROPERTIES OUTPUT_NAME "ballisticakit")
endif ()

target_include_directories(ballisticakitbin PRIVATE
  ${Python_INCLUDE_DIRS}
  ${BA_SRC_ROOT}/external/open_dynamics_engine-ef
  ${EXTRA_INCLUDE_DIRS})

target_link_libraries(ballisticakitbin PRIVATE
  ${CMAKE_CURRENT_BINARY_DIR}/prefablib/libballisticaplus.a ode pthread ${Python_LIBRARIES}
  ${SDL2_LIBRARIES} ${EXTRA_LIBRARIES} dl)


# BallisticaKit modular shared library
# (for use with vanilla Python interpreters).
add_library(ballisticakitso SHARED ${BALLISTICA_SOURCES})

# This is a 'modular' build.
target_compile_definitions(ballisticakitso PRIVATE BA_MONOLITHIC_BUILD=0)

# Gets -rdynamic added when linking gcc builds which exports all symbols
# which gives us more meaningful stack traces using backtrace_symbols().  
set_target_properties(ballisticakitso PROPERTIES ENABLE_EXPORTS 1)

set_target_properties(ballisticakitso
  PROPERTIES PREFIX "")
set_target_properties(ballisticakitso
  PROPERTIES SUFFIX ".so")

if (HEADLESS)
  set_target_properties(ballisticakitso
    PROPERTIES OUTPUT_NAME "ballisticakit_headless")
else ()
  set_target_properties(ballisticakitso
    PROPERTIES OUTPUT_NAME "ballisticakit")
endif ()

target_include_directories(ballisticakitso PRIVATE
  ${Python_INCLUDE_DIRS}
  ${BA_SRC_ROOT}/external/open_dynamics_engine-ef
  ${EXTRA_INCLUDE_DIRS})

target_link_libraries(ballisticakitso PRIVATE
  ${CMAKE_CURRENT_BINARY_DIR}/prefablib/libballisticaplus.a ode pthread ${Python_LIBRARIES}
  ${SDL2_LIBRARIES} ${EXTRA_LIBRARIES} dl)

