// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/methods/python_methods_assets.h"

#include <string>
#include <vector>

#include "ballistica/base/assets/assets.h"
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
  base::Assets::FailOnAssetPackagePath(name, "gettexture");
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

// ------------------------------ aptextureget ---------------------------------

static auto PyApTextureGet(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  base::Assets::FailOnNonAssetPackagePath(name, "aptextureget");
  return SceneV1Context::Current().GetTexture(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyApTextureGetDef = {
    "aptextureget",                // name
    (PyCFunction)PyApTextureGet,   // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "aptextureget(name: str) -> bascenev1.Texture\n"
    "\n"
    "Load a texture from an asset-package (internal).\n"
    "\n"
    "Do not call this directly; asset-package assets should be accessed\n"
    "through their package's generated Python wrapper module, which routes\n"
    "through this call. Requires a fully-qualified '<apverid>:<path>'\n"
    "asset name.\n"
    "\n"
    ":meta private:"};

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
  base::Assets::FailOnAssetPackagePath(name, "getsound");
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

// ------------------------------- apsoundget ----------------------------------

static auto PyApSoundGet(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  base::Assets::FailOnNonAssetPackagePath(name, "apsoundget");
  return SceneV1Context::Current().GetSound(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyApSoundGetDef = {
    "apsoundget",                  // name
    (PyCFunction)PyApSoundGet,     // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "apsoundget(name: str) -> bascenev1.Sound\n"
    "\n"
    "Load a sound from an asset-package (internal).\n"
    "\n"
    "Do not call this directly; asset-package assets should be accessed\n"
    "through their package's generated Python wrapper module, which routes\n"
    "through this call. Requires a fully-qualified '<apverid>:<path>'\n"
    "asset name.\n"
    "\n"
    ":meta private:"};

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
  base::Assets::FailOnAssetPackagePath(name, "getdata");
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
  base::Assets::FailOnAssetPackagePath(name, "getmesh");
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

// ------------------------------- apmeshget -----------------------------------

static auto PyApMeshGet(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  base::Assets::FailOnNonAssetPackagePath(name, "apmeshget");
  return SceneV1Context::Current().GetMesh(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyApMeshGetDef = {
    "apmeshget",                   // name
    (PyCFunction)PyApMeshGet,      // method
    METH_VARARGS | METH_KEYWORDS,  // flags

    "apmeshget(name: str) -> bascenev1.Mesh\n"
    "\n"
    "Load a mesh from an asset-package (internal).\n"
    "\n"
    "Do not call this directly; asset-package assets should be accessed\n"
    "through their package's generated Python wrapper module, which routes\n"
    "through this call. Requires a fully-qualified '<apverid>:<path>'\n"
    "asset name.\n"
    "\n"
    ":meta private:"};

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
  base::Assets::FailOnAssetPackagePath(name, "getcollisionmesh");
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

// --------------------------- apcollisionmeshget ------------------------------

static auto PyApCollisionMeshGet(PyObject* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  base::Assets::FailOnNonAssetPackagePath(name, "apcollisionmeshget");
  return SceneV1Context::Current().GetCollisionMesh(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

static PyMethodDef PyApCollisionMeshGetDef = {
    "apcollisionmeshget",               // name
    (PyCFunction)PyApCollisionMeshGet,  // method
    METH_VARARGS | METH_KEYWORDS,       // flags

    "apcollisionmeshget(name: str) -> bascenev1.CollisionMesh\n"
    "\n"
    "Load a collision-mesh from an asset-package (internal).\n"
    "\n"
    "Do not call this directly; asset-package assets should be accessed\n"
    "through their package's generated Python wrapper module, which routes\n"
    "through this call. Requires a fully-qualified '<apverid>:<path>'\n"
    "asset name.\n"
    "\n"
    ":meta private:"};

// -----------------------------------------------------------------------------

auto PythonMethodsAssets::GetMethods() -> std::vector<PyMethodDef> {
  return {
      PyGetCollisionMeshDef, PyGetMeshDef,    PyGetSoundDef,
      PyGetDataDef,          PyGetTextureDef, PyApCollisionMeshGetDef,
      PyApMeshGetDef,        PyApSoundGetDef, PyApTextureGetDef,
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica::scene_v1
