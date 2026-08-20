// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_simple_sound.h"

#include "ballistica/base/assets/sound_asset.h"
#include "ballistica/base/audio/audio.h"

namespace ballistica::base {

auto PythonClassSimpleSound::Play(PythonClassSimpleSound* self, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  float volume{1.0f};
  static const char* kwlist[] = {"volume", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|f",
                                   const_cast<char**>(kwlist), &volume)) {
    return nullptr;
  }
  g_base->audio->PlaySound(self->GetAsset(), volume);
  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassSimpleSound::tp_methods[] = {
    {"play", (PyCFunction)PythonClassSimpleSound::Play,
     METH_VARARGS | METH_KEYWORDS,
     "play() -> None\n"
     "\n"
     "Play the sound locally.\n"
     ""},

    {nullptr}};

}  // namespace ballistica::base
