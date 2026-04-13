// Released under the MIT License. See LICENSE for details.

#include "ballistica/ui_v1/python/class/python_class_ui_texture.h"

#include <string>

#include "ballistica/base/assets/texture_asset.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/ui_v1/ui_v1.h"

namespace ballistica::ui_v1 {

auto PythonClassUITexture::type_name() -> const char* { return "Texture"; }

void PythonClassUITexture::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.Texture";
  cls->tp_basicsize = sizeof(PythonClassUITexture);
  cls->tp_doc = "Texture asset for local user interface purposes.";
  cls->tp_new = tp_new;
  cls->tp_dealloc = (destructor)tp_dealloc;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
}

auto PythonClassUITexture::Create(
    const Object::Ref<base::TextureAsset>& texture) -> PyObject* {
  assert(TypeIsSetUp(&type_obj));
  auto* py_texture = reinterpret_cast<PythonClassUITexture*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  if (!py_texture) {
    throw Exception("Texture creation failed");
  }

  *py_texture->texture_ = texture;
  return reinterpret_cast<PyObject*>(py_texture);
}

auto PythonClassUITexture::tp_repr(PythonClassUITexture* self) -> PyObject* {
  BA_PYTHON_TRY;
  base::TextureAsset* s = self->texture_->get();
  return Py_BuildValue(
      "s", (std::string("<bauiv1.Texture '") + (s->GetName()) + "'>").c_str());
  BA_PYTHON_CATCH;
}

auto PythonClassUITexture::tp_new(PyTypeObject* type, PyObject* args,
                                  PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassUITexture*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  if (!g_base->InLogicThread()) {
    throw Exception(
        "ERROR: " + std::string(type_obj.tp_name)
        + " objects must only be created in the logic thread (current is ("
        + g_core->CurrentThreadName() + ").");
  }
  self->texture_ = new Object::Ref<base::TextureAsset>();
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

void PythonClassUITexture::tp_dealloc(PythonClassUITexture* self) {
  BA_PYTHON_TRY;
  // Our Object::Ref needs to be cleared in the logic thread.
  auto* ptr = self->texture_;
  if (g_base->InLogicThread()) {
    delete ptr;
  } else {
    g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyTypeObject PythonClassUITexture::type_obj;
PyMethodDef PythonClassUITexture::tp_methods[] = {{nullptr}};

}  // namespace ballistica::ui_v1
