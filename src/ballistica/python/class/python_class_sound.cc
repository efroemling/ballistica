// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_sound.h"

#include "ballistica/assets/component/sound.h"
#include "ballistica/core/thread.h"
#include "ballistica/logic/logic.h"
#include "ballistica/python/python.h"

namespace ballistica {

auto PythonClassSound::tp_repr(PythonClassSound* self) -> PyObject* {
  BA_PYTHON_TRY;
  Object::Ref<Sound> m = *(self->sound_);
  return Py_BuildValue(
      "s", (std::string("<ba.Sound ")
            + (m.exists() ? ("\"" + m->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

void PythonClassSound::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.Sound";
  obj->tp_basicsize = sizeof(PythonClassSound);
  obj->tp_doc =
      "A reference to a sound.\n"
      "\n"
      "Category: **Asset Classes**\n"
      "\n"
      "Use ba.getsound() to instantiate one.";
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassSound::Create(Sound* sound) -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  auto* t = reinterpret_cast<PythonClassSound*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("ba.Sound creation failed.");
  }
  *(t->sound_) = sound;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassSound::GetSound(bool doraise) const -> Sound* {
  Sound* sound = sound_->get();
  if (!sound && doraise) {
    throw Exception("Invalid Sound.", PyExcType::kNotFound);
  }
  return sound;
}

// Clion makes some incorrect inferences here.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "UnreachableCode"
#pragma ide diagnostic ignored "ConstantConditionsOC"
#pragma ide diagnostic ignored "ConstantFunctionResult"

auto PythonClassSound::tp_new(PyTypeObject* type, PyObject* args,
                              PyObject* kwds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassSound*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    if (!InLogicThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }
    if (!s_create_empty_) {
      throw Exception(
          "Can't instantiate Sounds directly; use ba.getsound() to get "
          "them.");
    }
    self->sound_ = new Object::Ref<Sound>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

#pragma clang diagnostic pop

void PythonClassSound::Delete(Object::Ref<Sound>* ref) {
  assert(InLogicThread());

  // if we're the py-object for a sound, clear them out
  // (FIXME - wej should pass the old pointer in here to sanity-test that we
  // were their ref)
  if (ref->exists()) {
    (*ref)->ClearPyObject();
  }
  delete ref;
}

void PythonClassSound::tp_dealloc(PythonClassSound* self) {
  BA_PYTHON_TRY;
  // these have to be deleted in the game thread - send the ptr along if need
  // be; otherwise do it immediately
  if (!InLogicThread()) {
    Object::Ref<Sound>* s = self->sound_;
    g_logic->thread()->PushCall([s] { Delete(s); });
  } else {
    Delete(self->sound_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

bool PythonClassSound::s_create_empty_ = false;
PyTypeObject PythonClassSound::type_obj;

}  // namespace ballistica
