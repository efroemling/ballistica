// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/methods/python_methods_assets.h"

#include <list>
#if 0  // Cpplint errs w/o this, CLion errs with it. Hard to please everybody.
#include <string>
#endif

#include "ballistica/assets/component/collide_model.h"
#include "ballistica/assets/component/data.h"
#include "ballistica/assets/component/model.h"
#include "ballistica/assets/component/sound.h"
#include "ballistica/assets/component/texture.h"
#include "ballistica/game/host_activity.h"
#include "ballistica/graphics/graphics_server.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"
#include "ballistica/ui/ui.h"

namespace ballistica {

// Ignore signed bitwise stuff; python macros do it quite a bit.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"

auto PyGetTexture(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return Context::current_target().GetTexture(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetPackageTexture(PyObject* self, PyObject* args, PyObject* keywds)
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
  auto fullname = g_python->ValidatedPackageAssetName(package_obj, name);
  return Context::current_target().GetTexture(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetSound(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return Context::current_target().GetSound(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetPackageSound(PyObject* self, PyObject* args, PyObject* keywds)
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
  auto fullname = g_python->ValidatedPackageAssetName(package_obj, name);
  return Context::current_target().GetSound(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetData(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return Context::current_target().GetData(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetPackageData(PyObject* self, PyObject* args, PyObject* keywds)
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
  auto fullname = g_python->ValidatedPackageAssetName(package_obj, name);
  return Context::current_target().GetData(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetModel(PyObject* self, PyObject* args, PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return Context::current_target().GetModel(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetPackageModel(PyObject* self, PyObject* args, PyObject* keywds)
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
  auto fullname = g_python->ValidatedPackageAssetName(package_obj, name);
  return Context::current_target().GetTexture(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetCollideModel(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* name;
  static const char* kwlist[] = {"name", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &name)) {
    return nullptr;
  }
  return Context::current_target().GetCollideModel(name)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyGetPackageCollideModel(PyObject* self, PyObject* args, PyObject* keywds)
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
  auto fullname = g_python->ValidatedPackageAssetName(package_obj, name);
  return Context::current_target().GetCollideModel(fullname)->NewPyRef();
  BA_PYTHON_CATCH;
}

auto PyMusicPlayerStop(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_platform->MusicPlayerStop();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyMusicPlayerPlay(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* files_obj;
  static const char* kwlist[] = {"files", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &files_obj)) {
    return nullptr;
  }
  g_platform->MusicPlayerPlay(files_obj);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyMusicPlayerSetVolume(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  float volume;
  static const char* kwlist[] = {"volume", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "f",
                                   const_cast<char**>(kwlist), &volume)) {
    return nullptr;
  }
  g_platform->MusicPlayerSetVolume(volume);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyMusicPlayerShutdown(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  static const char* kwlist[] = {nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "",
                                   const_cast<char**>(kwlist))) {
    return nullptr;
  }
  g_platform->MusicPlayerShutdown();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyReloadMedia(PyObject* self, PyObject* args) -> PyObject* {
  BA_PYTHON_TRY;
  assert(g_graphics_server);
  g_graphics_server->PushReloadMediaCall();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyGetQRCodeTexture(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  const char* url;
  static const char* kwlist[] = {"url", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s",
                                   const_cast<char**>(kwlist), &url)) {
    return nullptr;
  }
  // FIXME - should add this to context; for now just hard-coded for UI though
  if (Context::current().GetUIContext() != nullptr) {
    // these textures aren't actually stored in the UI context;
    // we just make sure we're here so we're not corrupting a game/session.
    return Object::New<Texture>(url)->NewPyRef();
  } else {
    throw Exception("QR-Code textures can only be created in the UI context.",
                    PyExcType::kContext);
  }
  BA_PYTHON_CATCH;
}

auto PyMacMusicAppInit(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  g_platform->MacMusicAppInit();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyMacMusicAppGetVolume(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  return PyLong_FromLong(g_platform->MacMusicAppGetVolume());
  BA_PYTHON_CATCH;
}

auto PyMacMusicAppSetVolume(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  int volume;
  static const char* kwlist[] = {"volume", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "i",
                                   const_cast<char**>(kwlist), &volume)) {
    return nullptr;
  }
  g_platform->MacMusicAppSetVolume(volume);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyMacMusicAppGetLibrarySource(PyObject* self, PyObject* args,
                                   PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  g_platform->MacMusicAppGetLibrarySource();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyMacMusicAppStop(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  g_platform->MacMusicAppStop();
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

auto PyMacMusicAppPlayPlaylist(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  std::string playlist;
  PyObject* playlist_obj;
  static const char* kwlist[] = {"playlist", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O",
                                   const_cast<char**>(kwlist), &playlist_obj)) {
    return nullptr;
  }
  playlist = Python::GetPyString(playlist_obj);
  if (g_platform->MacMusicAppPlayPlaylist(playlist)) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PyMacMusicAppGetPlaylists(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  PyObject* py_list = PyList_New(0);
  std::list<std::string> playlists = g_platform->MacMusicAppGetPlaylists();
  for (auto&& i : playlists) {
    PyObject* str_obj = PyUnicode_FromString(i.c_str());
    PyList_Append(py_list, str_obj);
    Py_DECREF(str_obj);
  }
  return py_list;
  BA_PYTHON_CATCH;
}

auto PyIsOSPlayingMusic(PyObject* self, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;
  if (g_platform->IsOSPlayingMusic()) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
  BA_PYTHON_CATCH;
}

auto PythonMethodsMedia::GetMethods() -> std::vector<PyMethodDef> {
  return {
      {"is_os_playing_music", (PyCFunction)PyIsOSPlayingMusic,
       METH_VARARGS | METH_KEYWORDS,
       "is_os_playing_music() -> bool\n"
       "\n"
       "(internal)\n"
       "\n"
       "Tells whether the OS is currently playing music of some sort.\n"
       "\n"
       "(Used to determine whether the game should avoid playing its own)"},

      {"mac_music_app_init", (PyCFunction)PyMacMusicAppInit,
       METH_VARARGS | METH_KEYWORDS,
       "mac_music_app_init() -> None\n"
       "\n"
       "(internal)"},

      {"mac_music_app_get_volume", (PyCFunction)PyMacMusicAppGetVolume,
       METH_VARARGS | METH_KEYWORDS,
       "mac_music_app_get_volume() -> int\n"
       "\n"
       "(internal)"},

      {"mac_music_app_set_volume", (PyCFunction)PyMacMusicAppSetVolume,
       METH_VARARGS | METH_KEYWORDS,
       "mac_music_app_set_volume(volume: int) -> None\n"
       "\n"
       "(internal)"},

      {"mac_music_app_get_library_source",
       (PyCFunction)PyMacMusicAppGetLibrarySource, METH_VARARGS | METH_KEYWORDS,
       "mac_music_app_get_library_source() -> None\n"
       "\n"
       "(internal)"},

      {"mac_music_app_stop", (PyCFunction)PyMacMusicAppStop,
       METH_VARARGS | METH_KEYWORDS,
       "mac_music_app_stop() -> None\n"
       "\n"
       "(internal)"},

      {"mac_music_app_play_playlist", (PyCFunction)PyMacMusicAppPlayPlaylist,
       METH_VARARGS | METH_KEYWORDS,
       "mac_music_app_play_playlist(playlist: str) -> bool\n"
       "\n"
       "(internal)"},

      {"mac_music_app_get_playlists", (PyCFunction)PyMacMusicAppGetPlaylists,
       METH_VARARGS | METH_KEYWORDS,
       "mac_music_app_get_playlists() -> list[str]\n"
       "\n"
       "(internal)"},

      {"get_qrcode_texture", (PyCFunction)PyGetQRCodeTexture,
       METH_VARARGS | METH_KEYWORDS,
       "get_qrcode_texture(url: str) -> ba.Texture\n"
       "\n"
       "(internal)"},

      {"reload_media", PyReloadMedia, METH_VARARGS,
       "reload_media() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Reload all currently loaded game media; useful for\n"
       "development/debugging."},

      {"music_player_shutdown", (PyCFunction)PyMusicPlayerShutdown,
       METH_VARARGS | METH_KEYWORDS,
       "music_player_shutdown() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Finalizes internal music file playback (for internal use)"},

      {"music_player_set_volume", (PyCFunction)PyMusicPlayerSetVolume,
       METH_VARARGS | METH_KEYWORDS,
       "music_player_set_volume(volume: float) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Sets internal music player volume (for internal use)"},

      {"music_player_play", (PyCFunction)PyMusicPlayerPlay,
       METH_VARARGS | METH_KEYWORDS,
       "music_player_play(files: Any) -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Starts internal music file playback (for internal use)"},

      {"music_player_stop", (PyCFunction)PyMusicPlayerStop,
       METH_VARARGS | METH_KEYWORDS,
       "music_player_stop() -> None\n"
       "\n"
       "(internal)\n"
       "\n"
       "Stops internal music file playback (for internal use)"},

      {"getcollidemodel", (PyCFunction)PyGetCollideModel,
       METH_VARARGS | METH_KEYWORDS,
       "getcollidemodel(name: str) -> ba.CollideModel\n"
       "\n"
       "Return a collide-model, loading it if necessary.\n"
       "\n"
       "Category: **Asset Functions**\n"
       "\n"
       "Collide-models are used in physics calculations for such things as\n"
       "terrain.\n"
       "\n"
       "Note that this function returns immediately even if the media has yet\n"
       "to be loaded. To avoid hitches, instantiate your media objects in\n"
       "advance of when you will be using them, allowing time for them to "
       "load\n"
       "in the background if necessary."},

      {"get_package_collide_model", (PyCFunction)PyGetPackageCollideModel,
       METH_VARARGS | METH_KEYWORDS,
       "get_package_collide_model(package: ba.AssetPackage, name: str)\n"
       "-> ba.CollideModel\n"
       "\n"
       "(internal)\n"},

      {"getmodel", (PyCFunction)PyGetModel, METH_VARARGS | METH_KEYWORDS,
       "getmodel(name: str) -> ba.Model\n"
       "\n"
       "Return a model, loading it if necessary.\n"
       "\n"
       "Category: **Asset Functions**\n"
       "\n"
       "Note that this function returns immediately even if the media has yet\n"
       "to be loaded. To avoid hitches, instantiate your media objects in\n"
       "advance of when you will be using them, allowing time for them to "
       "load\n"
       "in the background if necessary."},

      {"get_package_model", (PyCFunction)PyGetPackageModel,
       METH_VARARGS | METH_KEYWORDS,
       "get_package_model(package: ba.AssetPackage, name: str) -> ba.Model\n"
       "\n"
       "(internal)\n"},

      {"getsound", (PyCFunction)PyGetSound, METH_VARARGS | METH_KEYWORDS,
       "getsound(name: str) -> ba.Sound\n"
       "\n"
       "Return a sound, loading it if necessary.\n"
       "\n"
       "Category: **Asset Functions**\n"
       "\n"
       "Note that this function returns immediately even if the media has yet\n"
       "to be loaded. To avoid hitches, instantiate your media objects in\n"
       "advance of when you will be using them, allowing time for them to "
       "load\n"
       "in the background if necessary."},

      {"get_package_sound", (PyCFunction)PyGetPackageSound,
       METH_VARARGS | METH_KEYWORDS,
       "get_package_sound(package: ba.AssetPackage, name: str) -> ba.Sound\n"
       "\n"
       "(internal).\n"},

      {"getdata", (PyCFunction)PyGetData, METH_VARARGS | METH_KEYWORDS,
       "getdata(name: str) -> ba.Data\n"
       "\n"
       "Return a data, loading it if necessary.\n"
       "\n"
       "Category: **Asset Functions**\n"
       "\n"
       "Note that this function returns immediately even if the media has yet\n"
       "to be loaded. To avoid hitches, instantiate your media objects in\n"
       "advance of when you will be using them, allowing time for them to "
       "load\n"
       "in the background if necessary."},

      {"get_package_data", (PyCFunction)PyGetPackageData,
       METH_VARARGS | METH_KEYWORDS,
       "get_package_data(package: ba.AssetPackage, name: str) -> ba.Data\n"
       "\n"
       "(internal).\n"},

      {"gettexture", (PyCFunction)PyGetTexture, METH_VARARGS | METH_KEYWORDS,
       "gettexture(name: str) -> ba.Texture\n"
       "\n"
       "Return a texture, loading it if necessary.\n"
       "\n"
       "Category: **Asset Functions**\n"
       "\n"
       "Note that this function returns immediately even if the media has yet\n"
       "to be loaded. To avoid hitches, instantiate your media objects in\n"
       "advance of when you will be using them, allowing time for them to "
       "load\n"
       "in the background if necessary."},

      {"get_package_texture", (PyCFunction)PyGetPackageTexture,
       METH_VARARGS | METH_KEYWORDS,
       "get_package_texture(package: ba.AssetPackage, name: str) -> "
       "ba.Texture\n"
       "\n"
       "(internal)"},
  };
}

#pragma clang diagnostic pop

}  // namespace ballistica
