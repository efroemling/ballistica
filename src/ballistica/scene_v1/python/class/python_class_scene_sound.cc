// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_scene_sound.h"

#include <string>
#include <vector>

#include "ballistica/scene_v1/support/scene.h"
#include "ballistica/shared/python/python.h"

namespace ballistica::scene_v1 {

auto PythonClassSceneSound::Play(PythonClassSceneSound* self, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;
  BA_PRECONDITION(g_base->InLogicThread());
  float volume = 1.0f;
  int host_only = 0;
  PyObject* pos_obj = Py_None;
  static const char* kwlist[] = {"volume", "position", "host_only", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|fOp",
                                   const_cast<char**>(kwlist), &volume,
                                   &pos_obj, &host_only)) {
    return nullptr;
  }
  auto* sound = self->GetSound();

  // Can play sounds in a host scene context.
  if (Scene* scene = ContextRefSceneV1::FromCurrent().GetMutableScene()) {
    if (sound->scene() != scene) {
      throw Exception("Sound was not loaded in this context_ref.",
                      PyExcType::kContext);
    }
    if (pos_obj != Py_None) {
      std::vector<float> vals = Python::GetFloats(pos_obj);
      if (vals.size() != 3) {
        throw Exception("Expected 3 floats for pos (got "
                            + std::to_string(vals.size()) + ")",
                        PyExcType::kValue);
      }
      scene->PlaySoundAtPosition(sound, volume, vals[0], vals[1], vals[2],
                                 static_cast<bool>(host_only));
    } else {
      scene->PlaySound(sound, volume, static_cast<bool>(host_only));
    }
  } else {
    throw Exception("Can't play sounds in this context_ref.",
                    PyExcType::kContext);
  }

  Py_RETURN_NONE;
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassSceneSound::tp_methods[] = {
    {
        "play",
        (PyCFunction)Play,
        METH_VARARGS | METH_KEYWORDS,
        "play(volume: float = 1.0, position: Sequence[float] | None = None,\n"
        "     host_only: bool = False) -> None\n"
        "\n"
        "Play the sound a single time.\n"
        "\n"
        "If position is not provided, the sound will be at a constant volume\n"
        "everywhere. Position should be a float tuple of size 3.",
    },
    {nullptr}};

}  // namespace ballistica::scene_v1
