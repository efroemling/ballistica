// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/methods/python_methods_assets.h"

#include <string>
#include <vector>

#include "ballistica/scene_v1/assets/scene_collision_mesh.h"
#include "ballistica/scene_v1/assets/scene_data_asset.h"
#include "ballistica/scene_v1/assets/scene_mesh.h"
#include "ballistica/scene_v1/assets/scene_sound.h"
#include "ballistica/scene_v1/assets/scene_texture.h"
#include "ballistica/scene_v1/python/scene_v1_python.h"
#include "ballistica/shared/python/python_macros.h"

namespace ballistica::scene_v1 {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

// ------------------------------- gettexture ----------------------------------

static auto PyGetTexture(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return SceneV1Context::Current().GetTexture(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetTextureDef = {
    "gettexture",                  // name
    (PyCFunction)PyGetTexture,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "gettexture(name: str) -> bascenev1.Texture\n"
    "\n"
    "Return a texture, loading it if necessary.\n"
    "\n"
    "Note that this function returns immediately even if the asset has yet\n"
    "to be loaded. Loading will happen in the background or on-demand. To\n"
    "avoid hitches, try to instantiate asset objects a bit earlier than\n"
    "they are actually needed, giving them time to load gracefully\n"
    "in the background."};

// -------------------------- get_package_texture ------------------------------

static auto PyGetPackageTexture(PyObject* self, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  PyObject* package_obj;
  static const char* kwlist[] = {"package", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os",
                                   const_cast<char**>(kwlist), &package_obj,
                                   &name)) {
    return nullptr;
  }
  auto fullname =
      g_scene_v1->python->ValidatedPackageAssetName(package_obj, name);
  return SceneV1Context::Current().GetTexture(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetPackageTextureDef = {
    "get_package_texture",             // name
    (PyCFunction)PyGetPackageTexture,  // method
    METH_VARARGS | METH_KEYWORDS,      // flags

    "get_package_texture(package: bascenev1.AssetPackage, name: str) -> "
    "bascenev1.Texture\n"
    "\n"
    "(internal)"};

// ------------------------------- getsound ------------------------------------

static auto PyGetSound(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return SceneV1Context::Current().GetSound(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetSoundDef = {
    "getsound",                    // name
    (PyCFunction)PyGetSound,       // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "getsound(name: str) -> bascenev1.Sound\n"
    "\n"
    "Return a sound, loading it if necessary.\n"
    "\n"
    "Note that this function returns immediately even if the asset has yet\n"
    "to be loaded. Loading will happen in the background or on-demand. To\n"
    "avoid hitches, try to instantiate asset objects a bit earlier than\n"
    "they are actually needed, giving them time to load gracefully\n"
    "in the background."};

// --------------------------- get_package_sound -------------------------------

static auto PyGetPackageSound(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  PyObject* package_obj;
  static const char* kwlist[] = {"package", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os",
                                   const_cast<char**>(kwlist), &package_obj,
                                   &name)) {
    return nullptr;
  }
  auto fullname =
      g_scene_v1->python->ValidatedPackageAssetName(package_obj, name);
  return SceneV1Context::Current().GetSound(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetPackageSoundDef = {
    "get_package_sound",             // name
    (PyCFunction)PyGetPackageSound,  // method
    METH_VARARGS | METH_KEYWORDS,    // flags

    "get_package_sound(package: bascenev1.AssetPackage, name: str)"
    " -> bascenev1.Sound\n"
    "\n"
    "(internal).\n"};

// ------------------------------- getdata -------------------------------------

static auto PyGetData(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return SceneV1Context::Current().GetData(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetDataDef = {
    "getdata",                     // name
    (PyCFunction)PyGetData,        // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "getdata(name: str) -> bascenev1.Data\n"
    "\n"
    "Return a data, loading it if necessary.\n"
    "\n"
    "Note that this function returns immediately even if the asset has yet\n"
    "to be loaded. Loading will happen in the background or on-demand. To\n"
    "avoid hitches, try to instantiate asset objects a bit earlier than\n"
    "they are actually needed, giving them time to load gracefully\n"
    "in the background."};

// --------------------------- get_package_data --------------------------------

static auto PyGetPackageData(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  PyObject* package_obj;
  static const char* kwlist[] = {"package", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os",
                                   const_cast<char**>(kwlist), &package_obj,
                                   &name)) {
    return nullptr;
  }
  auto fullname =
      g_scene_v1->python->ValidatedPackageAssetName(package_obj, name);
  return SceneV1Context::Current().GetData(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetPackageDataDef = {
    "get_package_data",             // name
    (PyCFunction)PyGetPackageData,  // method
    METH_VARARGS | METH_KEYWORDS,   // flags

    "get_package_data(package: bascenev1.AssetPackage, name: str)"
    " -> bascenev1.Data\n"
    "\n"
    "(internal).\n"};

// -------------------------------- getmesh ------------------------------------

static auto PyGetMesh(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return SceneV1Context::Current().GetMesh(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetMeshDef = {
    "getmesh",                     // name
    (PyCFunction)PyGetMesh,        // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "getmesh(name: str) -> bascenev1.Mesh\n"
    "\n"
    "Return a mesh, loading it if necessary.\n"
    "\n"
    "Note that this function returns immediately even if the asset has yet\n"
    "to be loaded. Loading will happen in the background or on-demand. To\n"
    "avoid hitches, try to instantiate asset objects a bit earlier than\n"
    "they are actually needed, giving them time to load gracefully\n"
    "in the background."};

// ---------------------------- get_package_mesh -------------------------------

static auto PyGetPackageMesh(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  PyObject* package_obj;
  static const char* kwlist[] = {"package", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os",
                                   const_cast<char**>(kwlist), &package_obj,
                                   &name)) {
    return nullptr;
  }
  auto fullname =
      g_scene_v1->python->ValidatedPackageAssetName(package_obj, name);
  return SceneV1Context::Current().GetMesh(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetPackageMeshDef = {
    "get_package_mesh",             // name
    (PyCFunction)PyGetPackageMesh,  // method

    METH_VARARGS | METH_KEYWORDS,  // flags

    "get_package_mesh(package: bascenev1.AssetPackage, name: str)"
    " -> bascenev1.Mesh\n"
    "\n"
    "(internal)\n"};

// ----------------------------- getcollisionmesh ------------------------------

static auto PyGetCollisionMesh(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return SceneV1Context::Current().GetCollisionMesh(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetCollisionMeshDef = {
    "getcollisionmesh",               // name
    (PyCFunction)PyGetCollisionMesh,  // method
    METH_VARARGS | METH_KEYWORDS,     // flags

    "getcollisionmesh(name: str) -> bascenev1.CollisionMesh\n"
    "\n"
    "Return a collision-mesh, loading it if necessary.\n"
    "\n"
    "Collision-meshes are used in physics calculations for such things as\n"
    "terrain.\n"
    "\n"
    "Note that this function returns immediately even if the asset has yet\n"
    "to be loaded. Loading will happen in the background or on-demand. To\n"
    "avoid hitches, try to instantiate asset objects a bit earlier than\n"
    "they are actually needed, giving them time to load gracefully\n"
    "in the background."};

// ------------------------ get_package_collision_mesh -------------------------

static auto PyGetPackageCollisionMesh(PyObject* self, PyObject* args,
                                      PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  PyObject* package_obj;
  static const char* kwlist[] = {"package", "name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os",
                                   const_cast<char**>(kwlist), &package_obj,
                                   &name)) {
    return nullptr;
  }
  auto fullname =
      g_scene_v1->python->ValidatedPackageAssetName(package_obj, name);
  return SceneV1Context::Current().GetCollisionMesh(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyGetPackageCollisionMeshDef = {
    "get_package_collision_mesh",            // name
    (PyCFunction)PyGetPackageCollisionMesh,  // method

    METH_VARARGS | METH_KEYWORDS,  // flags

    "get_package_collision_mesh(package: bascenev1.AssetPackage, name: "
    "str)\n"
    "-> bascenev1.CollisionMesh\n"
    "\n"
    "(internal)\n"};

// -----------------------------------------------------------------------------

auto PythonMethodsAssets::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyGetCollisionMeshDef, PyGetPackageCollisionMeshDef,
      PyGetMeshDef,          PyGetPackageMeshDef,
      PyGetSoundDef,         PyGetPackageSoundDef,
      PyGetDataDef,          PyGetPackageDataDef,
      PyGetTextureDef,       PyGetPackageTextureDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::scene_v1
