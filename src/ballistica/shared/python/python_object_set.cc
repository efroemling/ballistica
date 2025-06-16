// Released under the MIT License. See LICENSE for details.

#include "ballistica/shared/python/python_object_set.h"

#include <Python.h>

#include <string>

#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/support/base_soft.h"
#include "ballistica/shared/python/python_command.h"

namespace ballistica {

// Using core stuff implicitly here. Our behavior is undefined if core
// has not yet been imported by anyone.
using core::g_base_soft;
using core::g_core;

PythonObjectSetBase::~PythonObjectSetBase() {
  // We make assumptions that ids remain valid once established.
  // Raise a fuss if that is ever not the case.
  FatalError("PythonObjectSets are expected to live forever.");
}

void PythonObjectSetBase::StoreObj(int id, PyObject* pyobj) {
  BA_PRECONDITION(pyobj);
  assert(id >= 0);
  assert(id < static_cast<int>(objs_.size()));

  if (g_buildconfig.debug_build()) {
    // Assuming we're setting everything once
    // (make sure we don't accidentally overwrite things we don't intend to).
    if (objs_[id].exists()) {
      throw Exception("Python::StoreObj() called twice for id '"
                      + std::to_string(id) + "' (existing val: '"
                      + objs_[id].Str() + "').");
    }

    // Also make sure we're not storing an object that's already been stored.
    for (auto&& i : objs_) {
      if (i.get() != nullptr && i.get() == pyobj) {
        g_core->logging->Log(LogName::kBa, LogLevel::kWarning,
                             "Python::StoreObj() called twice for same ptr; id="
                                 + std::to_string(id) + ".");
      }
    }
  }

  // Note: This used to be optional (and false by default) but now we always
  // acquire a ref to what we're storing. We hold on to this stuff permanently
  // so the worst thing that can happen is a harmless extra refcount increment
  // if someone passes us a new ref; that's better than the opposite case where
  // we are passed a borrowed ref and fail to keep it alive.
  Py_INCREF(pyobj);

  objs_[static_cast<int>(id)].Steal(pyobj);
}

void PythonObjectSetBase::StoreObjCallable(int id, PyObject* pyobj) {
  StoreObj(id, pyobj);
  BA_PRECONDITION(Obj(id).CallableCheck());
}

void PythonObjectSetBase::StoreObj(int id, const char* expr,
                                   PyObject* context) {
  auto obj = PythonCommand(expr, "<PyObj Set>").Eval(false, context, context);
  if (!obj.exists()) {
    FatalError("Unable to get value: '" + std::string(expr) + "'.");
  }
  StoreObj(id, obj.get());
}

void PythonObjectSetBase::StoreObjCallable(int id, const char* expr,
                                           PyObject* context) {
  auto obj = PythonCommand(expr, "<PyObj Set>").Eval(false, context, context);
  if (!obj.exists()) {
    throw Exception("Unable to get value: '" + std::string(expr) + "'.");
  }
  StoreObjCallable(id, obj.get());
}

void PythonObjectSetBase::PushObjCall(int id) const {
  // Easier to debug invalid objs here at the call site.
  assert(ObjExists(id));

  BA_PRECONDITION(g_base_soft);
  g_base_soft->DoPushObjCall(this, id);
}

void PythonObjectSetBase::PushObjCall(int id, const std::string& arg) const {
  // Easier to debug invalid objs here at the call site.
  assert(ObjExists(id));

  BA_PRECONDITION(g_base_soft);
  g_base_soft->DoPushObjCall(this, id, arg);
}

}  // namespace ballistica
