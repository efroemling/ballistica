// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/python/class/python_class_vec3.h"

#include <cstdio>
#include <string>

#include "ballistica/base/python/base_python.h"
#include "ballistica/shared/python/python.h"

// FIXME:
//  We currently call abc.Sequence.register(_babase.Vec3) which registers us as
//  a Sequence type (so that isinstance(ba.Vec3(), abc.Sequence) == True).
//  However the abc module lists a few things as part of the Sequence interface
//  that we don't currently provide: index() and count()

namespace ballistica::base {

// Ignore a few things that python macros do.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

static const int kMemberCount = 3;

PyTypeObject PythonClassVec3::type_obj;
PySequenceMethods PythonClassVec3::as_sequence_;
PyNumberMethods PythonClassVec3::as_number_;

auto PythonClassVec3::type_name() -> const char* { return "Vec3"; }

void PythonClassVec3::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "babase.Vec3";
  cls->tp_basicsize = sizeof(PythonClassVec3);
  cls->tp_doc =
      "A vector of 3 floats.\n"
      "\n"
      "These can be created the following ways (checked in this order):\n"
      " - With no args, all values are set to 0.\n"
      " - With a single numeric arg, all values are set to that value.\n"
      " - With a three-member sequence arg, sequence values are copied.\n"
      " - Otherwise assumes individual x/y/z args (positional or keywords)."
      "\n"
      "Attributes:\n"
      "   x (float):\n"
      "      The vector's X component.\n"
      "\n"
      "   y (float):\n"
      "      The vector's Y component.\n"
      "\n"
      "   z (float):\n"
      "      The vector's Z component.\n";

  cls->tp_new = tp_new;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
  cls->tp_getattro = (getattrofunc)tp_getattro;
  cls->tp_setattro = (setattrofunc)tp_setattro;
  cls->tp_richcompare = (richcmpfunc)tp_richcompare;

  // Sequence functionality.
  memset(&as_sequence_, 0, sizeof(as_sequence_));
  as_sequence_.sq_length = (lenfunc)sq_length;
  as_sequence_.sq_item = (ssizeargfunc)sq_item;
  as_sequence_.sq_ass_item = (ssizeobjargproc)sq_ass_item;
  cls->tp_as_sequence = &as_sequence_;

  // Number functionality.
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_add = (binaryfunc)nb_add;
  as_number_.nb_subtract = (binaryfunc)nb_subtract;
  as_number_.nb_multiply = (binaryfunc)nb_multiply;
  as_number_.nb_negative = (unaryfunc)nb_negative;
  cls->tp_as_number = &as_number_;

  // Note: We could fill out the in-place versions of these if we're not
  // going for immutability.
}

auto PythonClassVec3::Create(const Vector3f& val) -> PyObject* {
  auto obj =
      reinterpret_cast<PythonClassVec3*>(type_obj.tp_alloc(&type_obj, 0));
  if (obj) {
    obj->value = val;
  }
  return reinterpret_cast<PyObject*>(obj);
}

auto PythonClassVec3::tp_new(PyTypeObject* type, PyObject* args,
                             PyObject* keywds) -> PyObject* {
  auto self = reinterpret_cast<PythonClassVec3*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  // Accept a numeric sequence of length 3.
  assert(args != nullptr);
  assert(PyTuple_Check(args));
  Py_ssize_t numargs = PyTuple_GET_SIZE(args);
  if (numargs == 1 && PySequence_Check(PyTuple_GET_ITEM(args, 0))) {
    auto vals = Python::GetFloats(PyTuple_GET_ITEM(args, 0));
    if (vals.size() != 3) {
      throw Exception("Expected a 3 member numeric sequence.",
                      PyExcType::kValue);
    }
    self->value.x = vals[0];
    self->value.y = vals[1];
    self->value.z = vals[2];
  } else if (numargs == 1 && Python::IsNumber(PyTuple_GET_ITEM(args, 0))) {
    float val = Python::GetFloat(PyTuple_GET_ITEM(args, 0));
    self->value.x = self->value.y = self->value.z = val;
  } else {
    // Otherwise interpret as individual x, y, z float vals defaulting to 0.
    static const char* kwlist[] = {"x", "y", "z", nullptr};
    if (!PyArg_ParseTupleAndKeywords(args, keywds, "|fff",
                                     const_cast<char**>(kwlist), &self->value.x,
                                     &self->value.y, &self->value.z)) {
      Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
      return nullptr;
    }
  }
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

auto PythonClassVec3::tp_repr(PythonClassVec3* self) -> PyObject* {
  BA_PYTHON_TRY;
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "babase.Vec3(%f, %f, %f)", self->value.x,
           self->value.y, self->value.z);
  return Py_BuildValue("s", buffer);
  BA_PYTHON_CATCH;
}

auto PythonClassVec3::sq_length(PythonClassVec3* self) -> Py_ssize_t {
  return kMemberCount;
}

auto PythonClassVec3::sq_item(PythonClassVec3* self, Py_ssize_t i)
    -> PyObject* {
  if (i < 0 || i >= kMemberCount) {
    PyErr_SetString(PyExc_IndexError, "Vec3 index out of range");
    return nullptr;
  }
  return PyFloat_FromDouble(self->value.v[i]);
}

auto PythonClassVec3::sq_ass_item(PythonClassVec3* self, Py_ssize_t i,
                                  PyObject* valobj) -> int {
  BA_PYTHON_TRY;
  if (i < 0 || i >= kMemberCount) {
    throw Exception("Vec3 index out of range.", PyExcType::kValue);
  }
  float val = Python::GetFloat(valobj);
  self->value.v[i] = val;
  return 0;
  BA_PYTHON_INT_CATCH;
}

auto PythonClassVec3::nb_add(PythonClassVec3* l, PythonClassVec3* r)
    -> PyObject* {
  BA_PYTHON_TRY;

  // We can add if both sides are Vec3.
  if (Check(reinterpret_cast<PyObject*>(l))
      && Check(reinterpret_cast<PyObject*>(r))) {
    return Create(l->value + r->value);
  }

  // Otherwise we got nothin'.
  Py_INCREF(Py_NotImplemented);
  return Py_NotImplemented;
  BA_PYTHON_CATCH;
}

auto PythonClassVec3::nb_subtract(PythonClassVec3* l, PythonClassVec3* r)
    -> PyObject* {
  BA_PYTHON_TRY;

  // We can subtract if both sides are Vec3.
  if (Check(reinterpret_cast<PyObject*>(l))
      && Check(reinterpret_cast<PyObject*>(r))) {
    return Create(l->value - r->value);
  }

  // Otherwise we got nothin'.
  Py_INCREF(Py_NotImplemented);
  return Py_NotImplemented;
  BA_PYTHON_CATCH;
}

auto PythonClassVec3::nb_negative(PythonClassVec3* self) -> PyObject* {
  return Create(-self->value);
}

auto PythonClassVec3::nb_multiply(PyObject* l, PyObject* r) -> PyObject* {
  BA_PYTHON_TRY;

  // If left side is vec3.
  if (Check(l)) {
    // Try right as single number.
    if (Python::IsNumber(r)) {
      assert(Check(l));
      return Create(reinterpret_cast<PythonClassVec3*>(l)->value
                    * Python::GetFloat(r));
    }

    // Try right as a vec3-able value.
    if (BasePython::CanGetPyVector3f(r)) {
      Vector3f& lvec(reinterpret_cast<PythonClassVec3*>(l)->value);
      Vector3f rvec(BasePython::GetPyVector3f(r));
      return Create(
          Vector3f(lvec.x * rvec.x, lvec.y * rvec.y, lvec.z * rvec.z));
    }
  } else {
    // Ok, right must be vec3 (by definition).
    assert(Check(r));

    // Try left as single value.
    if (Python::IsNumber(l)) {
      assert(Check(r));
      return Create(Python::GetFloat(l)
                    * reinterpret_cast<PythonClassVec3*>(r)->value);
    }

    // Try left as a vec3-able value.
    if (BasePython::CanGetPyVector3f(l)) {
      Vector3f lvec(BasePython::GetPyVector3f(l));
      Vector3f& rvec(reinterpret_cast<PythonClassVec3*>(r)->value);
      return Create(
          Vector3f(lvec.x * rvec.x, lvec.y * rvec.y, lvec.z * rvec.z));
    }
  }

  // Ok we got nothin'.
  Py_INCREF(Py_NotImplemented);
  return Py_NotImplemented;
  BA_PYTHON_CATCH;
}

auto PythonClassVec3::tp_richcompare(PythonClassVec3* c1, PyObject* c2, int op)
    -> PyObject* {
  // Always return false against other types.
  if (!Check(c2)) {
    Py_RETURN_FALSE;
  }
  bool eq = (c1->value == (reinterpret_cast<PythonClassVec3*>(c2))->value);
  if (op == Py_EQ) {
    if (eq) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else if (op == Py_NE) {
    if (!eq) {
      Py_RETURN_TRUE;
    } else {
      Py_RETURN_FALSE;
    }
  } else {
    // Don't support other ops.
    Py_RETURN_NOTIMPLEMENTED;
  }
}

auto PythonClassVec3::Length(PythonClassVec3* self) -> PyObject* {
  BA_PYTHON_TRY;
  return PyFloat_FromDouble(self->value.Length());
  BA_PYTHON_CATCH;
}

auto PythonClassVec3::Normalized(PythonClassVec3* self) -> PyObject* {
  BA_PYTHON_TRY;
  return Create(self->value.Normalized());
  BA_PYTHON_CATCH;
}

auto PythonClassVec3::Dot(PythonClassVec3* self, PyObject* other) -> PyObject* {
  BA_PYTHON_TRY;
  return PyFloat_FromDouble(self->value.Dot(BasePython::GetPyVector3f(other)));
  BA_PYTHON_CATCH;
}

auto PythonClassVec3::Cross(PythonClassVec3* self, PyObject* other)
    -> PyObject* {
  BA_PYTHON_TRY;
  return Create(Vector3f::Cross(self->value, BasePython::GetPyVector3f(other)));
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassVec3::tp_methods[] = {
    {"length", (PyCFunction)Length, METH_NOARGS,
     "length() -> float\n"
     "\n"
     "Returns the length of the vector."},
    {"normalized", (PyCFunction)Normalized, METH_NOARGS,
     "normalized() -> Vec3\n"
     "\n"
     "Returns a normalized version of the vector."},
    {"dot", (PyCFunction)Dot, METH_O,
     "dot(other: Vec3) -> float\n"
     "\n"
     "Returns the dot product of this vector and another."},
    {"cross", (PyCFunction)Cross, METH_O,
     "cross(other: Vec3) -> Vec3\n"
     "\n"
     "Returns the cross product of this vector and another."},
    {nullptr}};

auto PythonClassVec3::tp_getattro(PythonClassVec3* self, PyObject* attr)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(PyUnicode_Check(attr));

  const char* s = PyUnicode_AsUTF8(attr);
  if (!strcmp(s, "x")) {
    return PyFloat_FromDouble(self->value.x);
  } else if (!strcmp(s, "y")) {
    return PyFloat_FromDouble(self->value.y);
  } else if (!strcmp(s, "z")) {
    return PyFloat_FromDouble(self->value.z);
  }
  return PyObject_GenericGetAttr(reinterpret_cast<PyObject*>(self), attr);
  BA_PYTHON_CATCH;
}

auto PythonClassVec3::tp_setattro(PythonClassVec3* self, PyObject* attrobj,
                                  PyObject* valobj) -> int {
  BA_PYTHON_TRY;
  assert(PyUnicode_Check(attrobj));
  const char* attr = PyUnicode_AsUTF8(attrobj);
  float val = Python::GetFloat(valobj);
  if (!strcmp(attr, "x")) {
    self->value.x = val;
  } else if (!strcmp(attr, "y")) {
    self->value.y = val;
  } else if (!strcmp(attr, "z")) {
    self->value.z = val;
  } else {
    throw Exception("Attr '" + std::string(attr) + "' is not settable.",
                    PyExcType::kAttribute);
  }
  return 0;
  BA_PYTHON_INT_CATCH;
}

#pragma clang diagnostic pop

}  // namespace ballistica::base
