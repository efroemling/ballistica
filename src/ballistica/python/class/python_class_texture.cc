// Released under the MIT License. See LICENSE for details.

#include "ballistica/python/class/python_class_texture.h"

#include <string>

#include "ballistica/game/game.h"
#include "ballistica/media/component/texture.h"

namespace ballistica {

auto PythonClassTexture::tp_repr(PythonClassTexture* self) -> PyObject* {
  BA_PYTHON_TRY;
  Object::Ref<Texture> t = *(self->texture_);
  return Py_BuildValue(
      "s", (std::string("<ba.Texture ")
            + (t.exists() ? ("\"" + t->name() + "\"") : "(empty ref)") + ">")
               .c_str());
  BA_PYTHON_CATCH;
}

void PythonClassTexture::SetupType(PyTypeObject* obj) {
  PythonClass::SetupType(obj);
  obj->tp_name = "ba.Texture";
  obj->tp_basicsize = sizeof(PythonClassTexture);
  obj->tp_doc =
      "A reference to a texture.\n"
      "\n"
      "Category: Asset Classes\n"
      "\n"
      "Use ba.gettexture() to instantiate one.";
  obj->tp_repr = (reprfunc)tp_repr;
  obj->tp_new = tp_new;
  obj->tp_dealloc = (destructor)tp_dealloc;
}

auto PythonClassTexture::Create(Texture* texture) -> PyObject* {
  s_create_empty_ = true;  // prevent class from erroring on create
  assert(texture != nullptr);
  auto* t = reinterpret_cast<PythonClassTexture*>(
      PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
  s_create_empty_ = false;
  if (!t) {
    throw Exception("ba.Texture creation failed.");
  }
  *(t->texture_) = texture;
  return reinterpret_cast<PyObject*>(t);
}

auto PythonClassTexture::GetTexture(bool doraise) const -> Texture* {
  Texture* texture = texture_->get();
  if (!texture && doraise) {
    throw Exception("Invalid Texture.", PyExcType::kNotFound);
  }
  return texture;
}

auto PythonClassTexture::tp_new(PyTypeObject* type, PyObject* args,
                                PyObject* keywds) -> PyObject* {
  auto* self = reinterpret_cast<PythonClassTexture*>(type->tp_alloc(type, 0));
  if (self) {
    BA_PYTHON_TRY;
    if (!InGameThread()) {
      throw Exception(
          "ERROR: " + std::string(type_obj.tp_name)
          + " objects must only be created in the game thread (current is ("
          + GetCurrentThreadName() + ").");
    }
    if (!s_create_empty_) {
      throw Exception(
          "Can't instantiate Textures directly; use ba.gettexture() to get "
          "them.");
    }
    self->texture_ = new Object::Ref<Texture>();
    BA_PYTHON_NEW_CATCH;
  }
  return reinterpret_cast<PyObject*>(self);
}

void PythonClassTexture::Delete(Object::Ref<Texture>* ref) {
  assert(InGameThread());

  // If we're the py-object for a texture, kill our reference to it.
  // (FIXME - we should pass the old py obj pointer in here to
  //  make sure that we were their python obj as a sanity test)
  if (ref->exists()) {
    (*ref)->ClearPyObject();
  }
  delete ref;
}

void PythonClassTexture::tp_dealloc(PythonClassTexture* self) {
  BA_PYTHON_TRY;
  // These have to be deleted in the game thread - send the ptr along if need
  // be; otherwise do it immediately.
  if (!InGameThread()) {
    Object::Ref<Texture>* t = self->texture_;
    g_game->PushCall([t] { Delete(t); });
  } else {
    Delete(self->texture_);
  }
  BA_PYTHON_DEALLOC_CATCH;
  Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

bool PythonClassTexture::s_create_empty_ = false;
PyTypeObject PythonClassTexture::type_obj;

}  // namespace ballistica
