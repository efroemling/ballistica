// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_ASSET_REF_H_
#define BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_ASSET_REF_H_

#include <string>

#include "ballistica/base/base.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/exception.h"
#include "ballistica/shared/foundation/object.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_class.h"

namespace ballistica::base {

/// CRTP base for Python classes wrapping a ref to a native asset(-like)
/// object (textures, sounds, meshes, etc. at both the engine-asset and
/// scene-asset layers). Provides the full shared machinery: a per-class
/// static type object, factory-only creation (direct instantiation from
/// Python raises), logic-thread-only construction, dealloc that ships the
/// held Object::Ref back to the logic thread for release, a null-safe
/// repr, and typed access helpers.
///
/// A derived class supplies:
/// - `static auto type_name() -> const char*` -- unqualified name used as
///   the module attr (e.g. "Texture").
/// - `static constexpr const char* kTpName` -- fully qualified Python
///   name (e.g. "bascenev1.Texture").
/// - `static constexpr const char* kTpDoc` -- the type's docstring.
/// - `static constexpr const char* kFactoryCall` -- the call users should
///   make to get instances (used in error messages).
/// - optionally `static PyMethodDef tp_methods[]` (must be public) for
///   extra methods, plus thin typed aliases over GetAsset()/asset().
///
/// Wrapper lifetime models (IMPORTANT): wrappers here are either minted
/// per acquisition (the ui/base pattern -- wrapper lifetime is purely
/// Python-refcounted) or cached one-per-object by the wrapped native
/// object (the scene pattern -- see SceneAsset::GetPyRef()). The cached
/// model creates a native<->Python ref cycle that neither GC can see, so
/// it is ONLY legal for objects with an explicit teardown moment that
/// breaks the cycle (scene assets: session teardown -> MarkDead() ->
/// ReleasePyObj()). Never add wrapper caching to engine-global assets
/// (textures/sounds/meshes); they have no such moment and the cycle
/// would pin them (and the wrapper) forever.
template <typename Derived, typename AssetT>
class PythonClassAssetRef : public PythonClass {
 public:
  static PyTypeObject type_obj;

  static void SetupType(PyTypeObject* cls) {
    PythonClass::SetupType(cls);
    cls->tp_name = Derived::kTpName;
    cls->tp_basicsize = sizeof(Derived);
    cls->tp_doc = Derived::kTpDoc;
    cls->tp_repr = (reprfunc)tp_repr;
    cls->tp_new = tp_new;
    cls->tp_dealloc = (destructor)tp_dealloc;
    if constexpr (requires { Derived::tp_methods; }) {
      cls->tp_methods = Derived::tp_methods;
    }
  }

  /// Create a wrapper pointing at the provided object (must not be
  /// nullptr).
  static auto Create(AssetT* asset) -> PyObject* {
    assert(asset != nullptr);
    assert(TypeIsSetUp(&type_obj));
    s_create_empty_ = true;  // Prevent tp_new from erroring.
    auto* obj = reinterpret_cast<Derived*>(
        PyObject_CallObject(reinterpret_cast<PyObject*>(&type_obj), nullptr));
    s_create_empty_ = false;
    if (!obj) {
      throw Exception(std::string(Derived::kTpName) + " creation failed.");
    }
    *obj->ref_ = asset;
    return reinterpret_cast<PyObject*>(obj);
  }
  static auto Create(const Object::Ref<AssetT>& asset) -> PyObject* {
    return Create(asset.get());
  }

  static auto Check(PyObject* o) -> bool {
    return PyObject_TypeCheck(o, &type_obj);
  }

  /// Cast raw Python pointer to our type; throws an exception on wrong
  /// types.
  static auto FromPyObj(PyObject* o) -> Derived& {
    if (Check(o)) {
      return *reinterpret_cast<Derived*>(o);
    }
    throw Exception(std::string("Expected a ") + Derived::kTpName + "; got a "
                        + Python::ObjTypeToString(o),
                    PyExcType::kType);
  }

  /// Return the wrapped object; raises a Python-friendly exception (or
  /// returns nullptr with doraise=false) if the ref is empty.
  auto GetAsset(bool doraise = true) const -> AssetT* {
    AssetT* asset = ref_ ? ref_->get() : nullptr;
    if (!asset && doraise) {
      throw Exception(std::string("Invalid ") + Derived::type_name() + ".",
                      PyExcType::kNotFound);
    }
    return asset;
  }

  /// Assert-checked reference access for contexts where emptiness is a
  /// bug, not a runtime condition.
  auto asset() const -> AssetT& {
    assert(ref_ && ref_->exists());
    return **ref_;
  }

 protected:
  static auto tp_repr(Derived* self) -> PyObject* {
    BA_PYTHON_TRY;
    AssetT* asset = self->ref_ ? self->ref_->get() : nullptr;
    return Py_BuildValue(
        "s",
        (std::string("<") + Derived::kTpName + " "
         + (asset ? ("\"" + AssetName_(asset) + "\"") : "(empty ref)") + ">")
            .c_str());
    BA_PYTHON_CATCH;
  }

  static auto tp_new(PyTypeObject* type, PyObject* args, PyObject* keywds)
      -> PyObject* {
    auto* self = reinterpret_cast<Derived*>(type->tp_alloc(type, 0));
    if (!self) {
      return nullptr;
    }
    BA_PYTHON_TRY;
    if (!g_base->InLogicThread()) {
      throw Exception(
          std::string(Derived::kTpName)
          + " objects must only be created in the logic thread (current is "
          + g_core->CurrentThreadName() + ").");
    }
    if (!s_create_empty_) {
      throw Exception(std::string("Can't instantiate ") + Derived::kTpName
                      + " objects directly; use " + Derived::kFactoryCall
                      + " to get them.");
    }
    self->ref_ = new Object::Ref<AssetT>();
    return reinterpret_cast<PyObject*>(self);
    BA_PYTHON_NEW_CATCH;
  }

  static void tp_dealloc(Derived* self) {
    BA_PYTHON_TRY;
    // Our Object::Ref needs to be released in the logic thread; ship it
    // there if that's not where we are.
    auto* ptr = self->ref_;
    if (g_base->InLogicThread()) {
      delete ptr;
    } else {
      g_base->logic->event_loop()->PushCall([ptr] { delete ptr; });
    }
    BA_PYTHON_DEALLOC_CATCH;
    Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
  }

  // NOTE: no in-class initializer here on purpose; instances come from
  // tp_alloc (zero-filled) and C++ constructors never run.
  Object::Ref<AssetT>* ref_;

 private:
  static auto AssetName_(AssetT* asset) -> std::string {
    // Engine assets expose GetName(); scene assets expose name().
    if constexpr (requires { asset->name(); }) {
      return asset->name();
    } else {
      return asset->GetName();
    }
  }

  static bool s_create_empty_;
};

template <typename Derived, typename AssetT>
PyTypeObject PythonClassAssetRef<Derived, AssetT>::type_obj;

template <typename Derived, typename AssetT>
bool PythonClassAssetRef<Derived, AssetT>::s_create_empty_ = false;

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_PYTHON_CLASS_PYTHON_CLASS_ASSET_REF_H_
