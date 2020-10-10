cmake_minimum_required(VERSION 3.12)
project(BallisticaCore)
include(CheckIncludeFile)

option(HEADLESS "build headless server" OFF)
option(TEST_BUILD "include testing features" OFF)

# Requiring minimum of C++17 currently.
set(CMAKE_CXX_STANDARD 17)

if (APPLE)
  # Seems as of Mojave we need to explicitly pull in /usr/local stuff.
  include_directories("/usr/local/include")
  link_directories("/usr/local/lib")

  # On Mac with homebrew it seems that Requesting 3.7 when we've got
  # 3.8 installed will point us at the 3.8 framework but will attempt
  # to load a 3.7 library from within it which doesn't exist. So we need
  # to be a bit more explicit telling it where to look. This is no longer
  # necessary since we're using 3.8 now but may be once 3.9 becomes available
  # through homebrew.
  execute_process(COMMAND "python3.8-config" "--prefix"
    OUTPUT_VARIABLE Python_ROOT_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE)

endif ()
find_package (Python 3.8 REQUIRED EXACT COMPONENTS Development)
  

if (HEADLESS)
  add_definitions(-DBA_HEADLESS_BUILD=1)
 else ()
  find_package(SDL2 QUIET)
  if (SDL2_FOUND)
    # Getting complaint about space at the end of this on ubuntu16.
    string(STRIP ${SDL2_LIBRARIES} SDL2_LIBRARIES)
  else ()
    message(FATAL_ERROR "SDL2 not found")
  endif ()
  find_package(OpenGL REQUIRED)
  find_package(OpenAL REQUIRED)
  if (APPLE)
    # On mac this sets an include path that we don't need since
    # we're using the system framework... should clean this up.
    set(OPENAL_INCLUDE_DIR "")
  endif ()
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
  add_definitions(-DBA_TEST_BUILD=1)
endif ()

# Currently seeing warnings about parameter order changing in GCC 7.1
# on Raspberry Pi builds. We never need to care about C++ abi compatibility
# so just silencing them for now. Can maybe remove this later if they stop.
if (CMAKE_COMPILER_IS_GNUCXX)
  set(CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} -Wno-psabi")
endif()

# message("GOT SDL INC ${SDL2_INCLUDE_DIRS}")
# message(FATAL_ERROR "SO FAR SO GOOD")

set(BA_SRC_ROOT src)
include_directories(${BA_SRC_ROOT})
add_compile_options(-include ballistica/config/config_cmake.h)

if (CMAKE_BUILD_TYPE MATCHES Debug)
  add_definitions(-DBA_DEBUG_BUILD=1)
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

# EWWW; GCC gives us bad mesh collisions with -O3 (and maybe -O2)
# need to finally get to the bottom of this but limiting to -01 for now.
# (-O2 might be safe??... or what about -Os?  Should test again.)
if (CMAKE_BUILD_TYPE MATCHES Release)
  target_compile_options(ode PRIVATE -O1)
endif ()

# BallisticaCore binary.
add_executable(ballisticacore
  ${BA_SRC_ROOT}/external/qr_code_generator/QrCode.cpp
  # AUTOGENERATED_PUBLIC_BEGIN (this section is managed by the "update_project" tool)
  ${BA_SRC_ROOT}/ballistica/app/app.cc
  # AUTOGENERATED_PUBLIC_END
  )

target_include_directories(ballisticacore PRIVATE
  ${Python_INCLUDE_DIRS}
  ${BA_SRC_ROOT}/external/open_dynamics_engine-ef
  ${EXTRA_INCLUDE_DIRS}
  )

# NOTE: seems we need to add 'dl' here for raspberry pi with a manually
# built Python 3.8. Might be able to remove later.
target_link_libraries(ballisticacore PRIVATE
  ballisticacore_private ode pthread ${Python_LIBRARIES}
  ${SDL2_LIBRARIES} ${EXTRA_LIBRARIES} dl)
