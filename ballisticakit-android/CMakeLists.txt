# For more information about using CMake with Android Studio, read the
# documentation: https://d.android.com/studio/projects/add-native-code.html

# Sets the minimum version of CMake required to build the native library.

cmake_minimum_required(VERSION 3.18.1)
project(BallisticaKit)

set(BA_SRC_ROOT src)

# Prebuilt Python and its support libs.
if (CMAKE_BUILD_TYPE MATCHES Debug)
  set(BA_PY_LIB_ROOT ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/python-android-debug/lib/android_${ANDROID_ABI})
  set(BA_PY_LIB_NAME libpython3.13d.a)
  set(BA_PY_INCLUDE_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/python-android-debug/include)
else ()
  set(BA_PY_LIB_ROOT ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/python-android/lib/android_${ANDROID_ABI})
  set(BA_PY_LIB_NAME libpython3.13.a)
  set(BA_PY_INCLUDE_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/python-android/include)
endif ()

# Prebuilt OpenAL
if (CMAKE_BUILD_TYPE MATCHES Debug)
  set(BA_OPENAL_LIB ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/openal-android/lib/${ANDROID_ABI}_debug/libopenal.a)
else ()
  set(BA_OPENAL_LIB ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/openal-android/lib/${ANDROID_ABI}_release/libopenal.a)
endif ()
set(BA_OPENAL_INCLUDE_DIR ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/openal-android/include/AL)

# Prebuilt Oboe (used by OpenAL)
if (CMAKE_BUILD_TYPE MATCHES Debug)
  set(BA_OBOE_LIB ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/openal-android/lib/${ANDROID_ABI}_debug/liboboe.a)
else ()
  set(BA_OBOE_LIB ${CMAKE_CURRENT_LIST_DIR}/../../../../../src/external/openal-android/lib/${ANDROID_ABI}_release/liboboe.a)
endif ()

add_library(python STATIC IMPORTED)
set_target_properties(python PROPERTIES IMPORTED_LOCATION ${BA_PY_LIB_ROOT}/${BA_PY_LIB_NAME})

add_library(pycrypto STATIC IMPORTED)
set_target_properties(pycrypto PROPERTIES IMPORTED_LOCATION ${BA_PY_LIB_ROOT}/libcrypto.a)

add_library(pyssl STATIC IMPORTED)
set_target_properties(pyssl PROPERTIES IMPORTED_LOCATION ${BA_PY_LIB_ROOT}/libssl.a)

add_library(pylzma STATIC IMPORTED)
set_target_properties(pylzma PROPERTIES IMPORTED_LOCATION ${BA_PY_LIB_ROOT}/liblzma.a)

add_library(pysqlite STATIC IMPORTED)
set_target_properties(pysqlite PROPERTIES IMPORTED_LOCATION ${BA_PY_LIB_ROOT}/libsqlite3.a)

add_library(pybz2 STATIC IMPORTED)
set_target_properties(pybz2 PROPERTIES IMPORTED_LOCATION ${BA_PY_LIB_ROOT}/libbz2.a)

add_library(pyuuid STATIC IMPORTED)
set_target_properties(pyuuid PROPERTIES IMPORTED_LOCATION ${BA_PY_LIB_ROOT}/libuuid.a)

add_library(pyffi STATIC IMPORTED)
set_target_properties(pyffi PROPERTIES IMPORTED_LOCATION ${BA_PY_LIB_ROOT}/libffi.a)

add_library(openal STATIC IMPORTED)
set_target_properties(openal PROPERTIES IMPORTED_LOCATION ${BA_OPENAL_LIB})

add_library(oboe STATIC IMPORTED)
set_target_properties(oboe PROPERTIES IMPORTED_LOCATION ${BA_OBOE_LIB})

# Note to self: why do we set C++ version differently here than in our standalone cmake build?
add_compile_options($<$<COMPILE_LANGUAGE:CXX>:-std=c++20> -ffast-math -include ballistica/shared/buildconfig/buildconfig_android_${BA_ANDROID_BUILDCONFIG}.h)

if (CMAKE_BUILD_TYPE MATCHES Debug)
  add_definitions(-DBA_DEBUG_BUILD=1)
  # Write patterns on temp stack memory to try and intercept bad usage.
  add_compile_options(-ftrivial-auto-var-init=pattern)
else ()
  # It seems that cmake can choose -O2 sometimes and -O3 sometimes
  # for release builds (depending on Release vs RelWithDebInfo, etc).
  # (Or perhaps that is a android/gradle thing). 
  # Regardless, let's keep all our non-debug builds consistent at -O3 for
  # now; can revisit if it causes problems.
  add_definitions(-O3)
endif ()

set(ODE_ROOT ${BA_SRC_ROOT}/external/open_dynamics_engine-ef)
set(BA_OGG_ROOT ${BA_SRC_ROOT}/external/libogg-1.2.2)
set(BA_TREMOR_ROOT ${BA_SRC_ROOT}/external/tremor)

include_directories(
  ${BA_SRC_ROOT}
  ${ODE_ROOT}
  ${BA_PY_INCLUDE_DIR}
  ${BA_OGG_ROOT}/include
  ${BA_TREMOR_ROOT}
  ${BA_OPENAL_INCLUDE_DIR}
)

# Auxiliary static lib to be linked in with our main lib.
# (and bundled precompiled in public releases)
add_library(internal STATIC
  ${ODE_ROOT}/ode/IceAABB.cpp
  ${ODE_ROOT}/ode/IceContainer.cpp
  ${ODE_ROOT}/ode/IceHPoint.cpp
  ${ODE_ROOT}/ode/IceIndexedTriangle.cpp
  ${ODE_ROOT}/ode/IceMatrix3x3.cpp
  ${ODE_ROOT}/ode/IceMatrix4x4.cpp
  ${ODE_ROOT}/ode/IceOBB.cpp
  ${ODE_ROOT}/ode/IcePlane.cpp
  ${ODE_ROOT}/ode/IcePoint.cpp
  ${ODE_ROOT}/ode/IceRandom.cpp
  ${ODE_ROOT}/ode/IceRay.cpp
  ${ODE_ROOT}/ode/IceRevisitedRadix.cpp
  ${ODE_ROOT}/ode/IceSegment.cpp
  ${ODE_ROOT}/ode/IceTriangle.cpp
  ${ODE_ROOT}/ode/IceUtils.cpp
  ${ODE_ROOT}/ode/ode.cpp
  ${ODE_ROOT}/ode/ode_array.cpp
  ${ODE_ROOT}/ode/ode_collision_cylinder_box.cpp
  ${ODE_ROOT}/ode/ode_collision_cylinder_plane.cpp
  ${ODE_ROOT}/ode/ode_collision_cylinder_sphere.cpp
  ${ODE_ROOT}/ode/ode_collision_cylinder_trimesh.cpp
  ${ODE_ROOT}/ode/ode_collision_kernel.cpp
  ${ODE_ROOT}/ode/ode_collision_quadtreespace.cpp
  ${ODE_ROOT}/ode/ode_collision_sapspace.cpp
  ${ODE_ROOT}/ode/ode_collision_space.cpp
  ${ODE_ROOT}/ode/ode_collision_std.cpp
  ${ODE_ROOT}/ode/ode_collision_transform.cpp
  ${ODE_ROOT}/ode/ode_collision_trimesh.cpp
  ${ODE_ROOT}/ode/ode_collision_trimesh_box.cpp
  ${ODE_ROOT}/ode/ode_collision_trimesh_ccylinder.cpp
  ${ODE_ROOT}/ode/ode_collision_trimesh_distance.cpp
  ${ODE_ROOT}/ode/ode_collision_trimesh_plane.cpp
  ${ODE_ROOT}/ode/ode_collision_trimesh_ray.cpp
  ${ODE_ROOT}/ode/ode_collision_trimesh_sphere.cpp
  ${ODE_ROOT}/ode/ode_collision_trimesh_trimesh.cpp
  ${ODE_ROOT}/ode/ode_collision_util.cpp
  ${ODE_ROOT}/ode/ode_error.cpp
  ${ODE_ROOT}/ode/ode_export-diff.cpp
  ${ODE_ROOT}/ode/ode_fastdot.cpp
  ${ODE_ROOT}/ode/ode_fastldlt.cpp
  ${ODE_ROOT}/ode/ode_fastlsolve.cpp
  ${ODE_ROOT}/ode/ode_fastltsolve.cpp
  ${ODE_ROOT}/ode/ode_joint.cpp
  ${ODE_ROOT}/ode/ode_lcp.cpp
  ${ODE_ROOT}/ode/ode_mass.cpp
  ${ODE_ROOT}/ode/ode_mat.cpp
  ${ODE_ROOT}/ode/ode_math.cpp
  ${ODE_ROOT}/ode/ode_matrix.cpp
  ${ODE_ROOT}/ode/ode_memory.cpp
  ${ODE_ROOT}/ode/ode_misc.cpp
  ${ODE_ROOT}/ode/ode_obstack.cpp
  ${ODE_ROOT}/ode/ode_quickstep.cpp
  ${ODE_ROOT}/ode/ode_rotation.cpp
  ${ODE_ROOT}/ode/ode_step.cpp
  ${ODE_ROOT}/ode/ode_stepfast.cpp
  ${ODE_ROOT}/ode/ode_timer.cpp
  ${ODE_ROOT}/ode/ode_util.cpp
  ${ODE_ROOT}/ode/OPC_AABBCollider.cpp
  ${ODE_ROOT}/ode/OPC_AABBTree.cpp
  ${ODE_ROOT}/ode/OPC_BaseModel.cpp
  ${ODE_ROOT}/ode/OPC_BoxPruning.cpp
  ${ODE_ROOT}/ode/OPC_Collider.cpp
  ${ODE_ROOT}/ode/OPC_HybridModel.cpp
  ${ODE_ROOT}/ode/OPC_LSSCollider.cpp
  ${ODE_ROOT}/ode/OPC_MeshInterface.cpp
  ${ODE_ROOT}/ode/OPC_Model.cpp
  ${ODE_ROOT}/ode/OPC_OBBCollider.cpp
  ${ODE_ROOT}/ode/OPC_OptimizedTree.cpp
  ${ODE_ROOT}/ode/OPC_PlanesCollider.cpp
  ${ODE_ROOT}/ode/OPC_RayCollider.cpp
  ${ODE_ROOT}/ode/OPC_SphereCollider.cpp
  ${ODE_ROOT}/ode/OPC_SweepAndPrune.cpp
  ${ODE_ROOT}/ode/OPC_TreeBuilders.cpp
  ${ODE_ROOT}/ode/OPC_TreeCollider.cpp
  ${ODE_ROOT}/ode/OPC_VolumeCollider.cpp
  ${ODE_ROOT}/ode/Opcode.cpp
  )

# Our main shared lib to be included in the app.
add_library(
  main SHARED
  
  ${BA_SRC_ROOT}/external/qr_code_generator/QrCode.cpp
  
  ${BA_OGG_ROOT}/bitwise.c
  ${BA_OGG_ROOT}/framing.c
  
  ${BA_TREMOR_ROOT}/block.c
  ${BA_TREMOR_ROOT}/codebook.c
  ${BA_TREMOR_ROOT}/floor0.c
  ${BA_TREMOR_ROOT}/floor1.c
  ${BA_TREMOR_ROOT}/info.c
  ${BA_TREMOR_ROOT}/mapping0.c
  ${BA_TREMOR_ROOT}/mdct.c
  ${BA_TREMOR_ROOT}/registry.c
  ${BA_TREMOR_ROOT}/res012.c
  ${BA_TREMOR_ROOT}/sharedbook.c
  ${BA_TREMOR_ROOT}/synthesis.c
  ${BA_TREMOR_ROOT}/vorbisfile.c
  ${BA_TREMOR_ROOT}/window.c
  
  # AUTOGENERATED_PRIVATE_BEGIN (this section is managed by the "update_project" tool)
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_android.cc
  ${BA_SRC_ROOT}/ballistica/base/app_adapter/app_adapter_android.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/android/amazon/app_platform_android_amazon.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/android/amazon/app_platform_android_amazon.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/android/app_platform_android.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/android/app_platform_android.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/android/cardboard/app_platform_android_cardboard.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/android/cardboard/app_platform_android_cardboard.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/android/google/app_platform_android_google.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/android/google/app_platform_android_google.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/apple/MacMusicApp.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/apple/MacMusicAppScriptingBridge.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/apple/from_swift.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/apple/from_swift.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/oculus/main_rift.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/oculus/oculus_utils.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/oculus/oculus_utils.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/windows/app_platform_windows_oculus.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/windows/app_platform_windows_oculus.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/amazon/platform_android_amazon.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/android/amazon/platform_android_amazon.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/android_utils.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/android/android_utils.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/cardboard/platform_android_cardboard.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/android/cardboard/platform_android_cardboard.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/execinfo.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/android/execinfo.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/from_java.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/android/from_java.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/google/platform_android_google.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/android/google/platform_android_google.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/ifaddrs_android_ext.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/android/ifaddrs_android_ext.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/platform_android.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/android/platform_android.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/utf8/checked.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/utf8/core.h
  ${BA_SRC_ROOT}/ballistica/core/platform/android/utf8/unchecked.h
  ${BA_SRC_ROOT}/ballistica/core/platform/windows/platform_windows_oculus.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/windows/platform_windows_oculus.h
  ${BA_SRC_ROOT}/ballistica/plus/plus.cc
  ${BA_SRC_ROOT}/ballistica/plus/plus.h
  ${BA_SRC_ROOT}/ballistica/plus/python/methods/python_methods_plus.cc
  ${BA_SRC_ROOT}/ballistica/plus/python/methods/python_methods_plus.h
  ${BA_SRC_ROOT}/ballistica/plus/python/plus_python.cc
  ${BA_SRC_ROOT}/ballistica/plus/python/plus_python.h
  ${BA_SRC_ROOT}/ballistica/plus/support/master_server_config.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_amazon.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_arcade.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_cardboard.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_common.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_demo.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_generic.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_google.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_meta.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_android_template.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_windows_meta.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_xcode_common.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_xcode_ios.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_xcode_mac_appstore.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_xcode_mac_common.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_xcode_mac_steam.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_xcode_mac_testbuild.h
  ${BA_SRC_ROOT}/ballistica/shared/buildconfig/buildconfig_xcode_tvos.h
  # AUTOGENERATED_PRIVATE_END
  
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
  ${BA_SRC_ROOT}/ballistica/base/app_platform/app_platform.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/app_platform.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/apple/app_platform_apple.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/apple/app_platform_apple.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/linux/app_platform_linux.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/linux/app_platform_linux.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/support/min_sdl_key_names.h
  ${BA_SRC_ROOT}/ballistica/base/app_platform/windows/app_platform_windows.cc
  ${BA_SRC_ROOT}/ballistica/base/app_platform/windows/app_platform_windows.h
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
  ${BA_SRC_ROOT}/ballistica/core/platform/apple/platform_apple.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/apple/platform_apple.h
  ${BA_SRC_ROOT}/ballistica/core/platform/linux/platform_linux.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/linux/platform_linux.h
  ${BA_SRC_ROOT}/ballistica/core/platform/platform.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/platform.h
  ${BA_SRC_ROOT}/ballistica/core/platform/support/min_sdl.h
  ${BA_SRC_ROOT}/ballistica/core/platform/support/platform_pango.h
  ${BA_SRC_ROOT}/ballistica/core/platform/windows/platform_windows.cc
  ${BA_SRC_ROOT}/ballistica/core/platform/windows/platform_windows.h
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
  ${BA_SRC_ROOT}/ballistica/shared/math/lerp.h
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

# Search for specific system libs we use.
find_library(gl-lib GLESv3)
find_library(opensl-lib OpenSLES)
find_library(log-lib log)
find_library(egl-lib EGL)
find_library(jnigraphics-lib jnigraphics)
find_library(z-lib z)

target_link_libraries( main
  python pyssl pycrypto pylzma pysqlite pybz2 pyuuid pyffi openal oboe internal
  ${z-lib} ${jnigraphics-lib} ${egl-lib} ${log-lib} ${gl-lib} ${opensl-lib})

# testing
# add_executable(readlinktest ${BA_SRC_ROOT}/external/readlinktest.c)
