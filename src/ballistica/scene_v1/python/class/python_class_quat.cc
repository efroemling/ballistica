// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/python/class/python_class_quat.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>

#include "ballistica/shared/math/vector3f.h"
#include "ballistica/shared/python/python.h"
#include "ode/ode_rotation.h"

namespace ballistica::scene_v1 {

// Ignore a few things that python macros do.
#pragma clang diagnostic push
#pragma ide diagnostic ignored "hicpp-signed-bitwise"
#pragma ide diagnostic ignored "RedundantCast"

static const int kMemberCount = 4;

PyTypeObject PythonClassQuat::type_obj;
PySequenceMethods PythonClassQuat::as_sequence_;
PyNumberMethods PythonClassQuat::as_number_;

/// Copy one quaternion's values into another.
static void QuatCopy(dQuaternion dst, const dQuaternion src) {
  for (int i = 0; i < kMemberCount; ++i) {
    dst[i] = src[i];
  }
}

/// Scale a quaternion to unit length. Zero-length input yields identity.
static void QuatNormalize(dQuaternion q) {
  float mag = std::sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
  if (mag < 0.00001f) {
    dQSetIdentity(q);
    return;
  }
  for (int i = 0; i < kMemberCount; ++i) {
    q[i] /= mag;
  }
}

auto PythonClassQuat::type_name() -> const char* { return "Quat"; }

void PythonClassQuat::SetupType(PyTypeObject* cls) {
  PythonClass::SetupType(cls);
  // Fully qualified type path we will be exposed as:
  cls->tp_name = "bascenev1.Quat";
  cls->tp_basicsize = sizeof(PythonClassQuat);
  cls->tp_doc =
      "A quaternion representing a rotation in 3d space.\n"
      "\n"
      "These can be created the following ways (checked in this order):\n"
      " - With no args, the identity (no-op) rotation is created.\n"
      " - With a four-member sequence arg, sequence values are copied.\n"
      " - Otherwise assumes individual w/x/y/z args (positional or"
      " keywords).\n"
      "\n"
      "Quats are immutable, and are accepted anywhere a four-float\n"
      "sequence is, so one can be assigned directly to node attrs such as\n"
      ":attr:`bascenev1.Node.rotate`.\n"
      "\n"
      "Note that most rotations are more easily built using\n"
      ":meth:`~bascenev1.Quat.from_angles()` than by passing raw values\n"
      "here.\n"
      "\n"
      "Attributes:\n"
      "   w (float):\n"
      "      The quaternion's real component.\n"
      "\n"
      "   x (float):\n"
      "      The quaternion's X component.\n"
      "\n"
      "   y (float):\n"
      "      The quaternion's Y component.\n"
      "\n"
      "   z (float):\n"
      "      The quaternion's Z component.\n";

  cls->tp_new = tp_new;
  cls->tp_repr = (reprfunc)tp_repr;
  cls->tp_methods = tp_methods;
  cls->tp_getattro = (getattrofunc)tp_getattro;
  cls->tp_richcompare = (richcmpfunc)tp_richcompare;

  // Sequence functionality. Note that we intentionally provide no
  // sq_ass_item; quats are immutable (a half-assigned one would be an
  // invalid rotation).
  memset(&as_sequence_, 0, sizeof(as_sequence_));
  as_sequence_.sq_length = (lenfunc)sq_length;
  as_sequence_.sq_item = (ssizeargfunc)sq_item;
  cls->tp_as_sequence = &as_sequence_;

  // Number functionality (multiplication composes rotations).
  memset(&as_number_, 0, sizeof(as_number_));
  as_number_.nb_multiply = (binaryfunc)nb_multiply;
  cls->tp_as_number = &as_number_;
}

auto PythonClassQuat::Create(const dQuaternion& val) -> PyObject* {
  auto obj =
      reinterpret_cast<PythonClassQuat*>(type_obj.tp_alloc(&type_obj, 0));
  if (obj) {
    QuatCopy(obj->value, val);
  }
  return reinterpret_cast<PyObject*>(obj);
}

auto PythonClassQuat::tp_new(PyTypeObject* type, PyObject* args,
                             PyObject* keywds) -> PyObject* {
  auto self = reinterpret_cast<PythonClassQuat*>(type->tp_alloc(type, 0));
  if (!self) {
    return nullptr;
  }
  BA_PYTHON_TRY;
  assert(args != nullptr);
  assert(PyTuple_Check(args));
  Py_ssize_t numargs = PyTuple_GET_SIZE(args);
  if (numargs == 1 && PySequence_Check(PyTuple_GET_ITEM(args, 0))) {
    auto vals = Python::GetFloats(PyTuple_GET_ITEM(args, 0));
    if (vals.size() != kMemberCount) {
      throw Exception("Expected a 4 member numeric sequence.",
                      PyExcType::kValue);
    }
    for (int i = 0; i < kMemberCount; ++i) {
      self->value[i] = vals[static_cast<size_t>(i)];
    }
  } else {
    // Otherwise interpret as individual w, x, y, z vals defaulting to
    // the identity rotation.
    dQSetIdentity(self->value);
    static const char* kwlist[] = {"w", "x", "y", "z", nullptr};
    if (!PyArg_ParseTupleAndKeywords(
            args, keywds, "|ffff", const_cast<char**>(kwlist), &self->value[0],
            &self->value[1], &self->value[2], &self->value[3])) {
      Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
      return nullptr;
    }
  }
  return reinterpret_cast<PyObject*>(self);
  BA_PYTHON_NEW_CATCH;
}

auto PythonClassQuat::tp_repr(PythonClassQuat* self) -> PyObject* {
  BA_PYTHON_TRY;
  char buffer[128];
  snprintf(buffer, sizeof(buffer), "bascenev1.Quat(%f, %f, %f, %f)",
           self->value[0], self->value[1], self->value[2], self->value[3]);
  return Py_BuildValue("s", buffer);
  BA_PYTHON_CATCH;
}

auto PythonClassQuat::sq_length(PythonClassQuat* self) -> Py_ssize_t {
  return kMemberCount;
}

auto PythonClassQuat::sq_item(PythonClassQuat* self, Py_ssize_t i)
    -> PyObject* {
  if (i < 0 || i >= kMemberCount) {
    PyErr_SetString(PyExc_IndexError, "Quat index out of range");
    return nullptr;
  }
  return PyFloat_FromDouble(self->value[i]);
}

auto PythonClassQuat::nb_multiply(PyObject* l, PyObject* r) -> PyObject* {
  BA_PYTHON_TRY;

  // We can compose if both sides are Quats.
  if (Check(l) && Check(r)) {
    dQuaternion out;
    dQMultiply0(out, reinterpret_cast<PythonClassQuat*>(l)->value,
                reinterpret_cast<PythonClassQuat*>(r)->value);
    return Create(out);
  }

  // Otherwise we got nothin'.
  Py_INCREF(Py_NotImplemented);
  return Py_NotImplemented;
  BA_PYTHON_CATCH;
}

auto PythonClassQuat::tp_richcompare(PythonClassQuat* c1, PyObject* c2, int op)
    -> PyObject* {
  // Always return false against other types.
  if (!Check(c2)) {
    Py_RETURN_FALSE;
  }
  auto* other = reinterpret_cast<PythonClassQuat*>(c2);
  bool eq{true};
  for (int i = 0; i < kMemberCount; ++i) {
    if (c1->value[i] != other->value[i]) {
      eq = false;
      break;
    }
  }
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

auto PythonClassQuat::FromAngles(PyObject* cls, PyObject* args,
                                 PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  double heading{};
  double pitch{};
  double roll{};
  static const char* kwlist[] = {"heading", "pitch", "roll", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "|ddd",
                                   const_cast<char**>(kwlist), &heading, &pitch,
                                   &roll)) {
    return nullptr;
  }
  const float to_radians{kPi / 180.0f};
  dQuaternion q_heading;
  dQuaternion q_pitch;
  dQuaternion q_roll;
  dQuaternion q_hp;
  dQuaternion q;
  dQFromAxisAndAngle(q_heading, 0.0f, 1.0f, 0.0f,
                     static_cast<float>(heading) * to_radians);
  // Positive pitch aims upward, which is a negative rotation about our
  // sideways axis in this right-handed space.
  dQFromAxisAndAngle(q_pitch, 1.0f, 0.0f, 0.0f,
                     static_cast<float>(-pitch) * to_radians);
  // Likewise positive roll banks to the right, which is a negative
  // rotation about our forward axis.
  dQFromAxisAndAngle(q_roll, 0.0f, 0.0f, 1.0f,
                     static_cast<float>(-roll) * to_radians);
  dQMultiply0(q_hp, q_heading, q_pitch);
  dQMultiply0(q, q_hp, q_roll);
  return Create(q);
  BA_PYTHON_CATCH;
}

auto PythonClassQuat::FromDirection(PyObject* cls, PyObject* args,
                                    PyObject* keywds) -> PyObject* {
  BA_PYTHON_TRY;

  PyObject* direction_obj{};
  PyObject* up_obj{};
  static const char* kwlist[] = {"direction", "up", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|O",
                                   const_cast<char**>(kwlist), &direction_obj,
                                   &up_obj)) {
    return nullptr;
  }
  auto direction_vals = Python::GetFloats(direction_obj);
  if (direction_vals.size() != 3) {
    throw Exception("Expected a 3 member numeric sequence for direction.",
                    PyExcType::kValue);
  }
  Vector3f forward{direction_vals[0], direction_vals[1], direction_vals[2]};

  Vector3f up{0.0f, 1.0f, 0.0f};
  if (up_obj != nullptr) {
    auto up_vals = Python::GetFloats(up_obj);
    if (up_vals.size() != 3) {
      throw Exception("Expected a 3 member numeric sequence for up.",
                      PyExcType::kValue);
    }
    up = Vector3f{up_vals[0], up_vals[1], up_vals[2]};
  }

  // A zero-length direction gives us nothing to aim at.
  if (forward.LengthSquared() < 0.000001f) {
    dQuaternion q;
    dQSetIdentity(q);
    return Create(q);
  }
  forward = forward.Normalized();

  if (up.LengthSquared() < 0.000001f) {
    up = Vector3f{0.0f, 1.0f, 0.0f};
  }

  // Right-handed y-up with +z forward means x = y cross z.
  Vector3f right{Vector3f::Cross(up, forward)};

  // An up parallel to our direction leaves no plane to work from; fall
  // back to any axis that isn't, so we still return something sane
  // instead of a pile of NaNs.
  if (right.LengthSquared() < 0.000001f) {
    Vector3f fallback{std::abs(forward.y) > 0.9f ? Vector3f{0.0f, 0.0f, 1.0f}
                                                 : Vector3f{0.0f, 1.0f, 0.0f}};
    right = Vector3f::Cross(fallback, forward);
  }
  right = right.Normalized();

  // Re-derive up so we're guaranteed an orthonormal set even when the
  // up that came in was merely a hint (which is the common case).
  Vector3f up2{Vector3f::Cross(forward, right)};

  // Columns are where our local axes wind up; ODE matrices are row-major
  // 3x4, hence the stride of 4.
  dMatrix3 matrix;
  matrix[0] = right.x;
  matrix[4] = right.y;
  matrix[8] = right.z;
  matrix[1] = up2.x;
  matrix[5] = up2.y;
  matrix[9] = up2.z;
  matrix[2] = forward.x;
  matrix[6] = forward.y;
  matrix[10] = forward.z;
  matrix[3] = matrix[7] = matrix[11] = 0.0f;

  dQuaternion q;
  dQfromR(q, matrix);
  QuatNormalize(q);
  return Create(q);
  BA_PYTHON_CATCH;
}

auto PythonClassQuat::Slerp(PyObject* cls, PyObject* args, PyObject* keywds)
    -> PyObject* {
  BA_PYTHON_TRY;

  PyObject* from_obj{};
  PyObject* to_obj{};
  double amount{};
  static const char* kwlist[] = {"from_quat", "to_quat", "amount", nullptr};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "OOd",
                                   const_cast<char**>(kwlist), &from_obj,
                                   &to_obj, &amount)) {
    return nullptr;
  }
  if (!Check(from_obj) || !Check(to_obj)) {
    throw Exception("Expected Quat values to interpolate between.",
                    PyExcType::kType);
  }
  dQuaternion from;
  dQuaternion to;
  QuatCopy(from, reinterpret_cast<PythonClassQuat*>(from_obj)->value);
  QuatCopy(to, reinterpret_cast<PythonClassQuat*>(to_obj)->value);
  QuatNormalize(from);
  QuatNormalize(to);

  float dot{};
  for (int i = 0; i < kMemberCount; ++i) {
    dot += from[i] * to[i];
  }

  // A quat and its negation are the same rotation, so flip one if needed
  // to be sure we travel the short way around instead of the long one.
  if (dot < 0.0f) {
    for (int i = 0; i < kMemberCount; ++i) {
      to[i] = -to[i];
    }
    dot = -dot;
  }

  dQuaternion out;
  auto t = static_cast<float>(amount);

  // Nearly-coincident inputs make the trig below numerically unstable;
  // plain lerp is indistinguishable from slerp at that point.
  if (dot > 0.9995f) {
    for (int i = 0; i < kMemberCount; ++i) {
      out[i] = from[i] + (to[i] - from[i]) * t;
    }
  } else {
    float theta = std::acos(dot);
    float sin_theta = std::sin(theta);
    float from_scale = std::sin((1.0f - t) * theta) / sin_theta;
    float to_scale = std::sin(t * theta) / sin_theta;
    for (int i = 0; i < kMemberCount; ++i) {
      out[i] = from[i] * from_scale + to[i] * to_scale;
    }
  }
  QuatNormalize(out);
  return Create(out);
  BA_PYTHON_CATCH;
}

auto PythonClassQuat::Inverse(PythonClassQuat* self) -> PyObject* {
  BA_PYTHON_TRY;
  float mag_squared{};
  for (int i = 0; i < kMemberCount; ++i) {
    mag_squared += self->value[i] * self->value[i];
  }
  dQuaternion out;
  if (mag_squared < 0.00001f) {
    dQSetIdentity(out);
  } else {
    // The inverse is the conjugate over the squared magnitude (which is
    // simply the conjugate for the unit quats we normally deal in).
    out[0] = self->value[0] / mag_squared;
    for (int i = 1; i < kMemberCount; ++i) {
      out[i] = -self->value[i] / mag_squared;
    }
  }
  return Create(out);
  BA_PYTHON_CATCH;
}

auto PythonClassQuat::Normalized(PythonClassQuat* self) -> PyObject* {
  BA_PYTHON_TRY;
  dQuaternion out;
  QuatCopy(out, self->value);
  QuatNormalize(out);
  return Create(out);
  BA_PYTHON_CATCH;
}

PyMethodDef PythonClassQuat::tp_methods[] = {
    {"from_angles", (PyCFunction)FromAngles,
     METH_VARARGS | METH_KEYWORDS | METH_STATIC,
     "from_angles(heading: float = 0.0, pitch: float = 0.0,"
     " roll: float = 0.0) -> Quat\n"
     "\n"
     "Create a rotation from Euler angles, in degrees.\n"
     "\n"
     "Heading is a rotation about the up (y) axis, pitch about the\n"
     "sideways (x) axis, and roll about the forward (z) axis. They are\n"
     "applied in that order, each about the axes left by the previous\n"
     "one, so pitch tips an object relative to wherever its heading\n"
     "left it facing.\n"
     "\n"
     "Signs follow the usual aircraft convention: positive heading\n"
     "turns right, positive pitch aims up, and positive roll banks\n"
     "right."},
    {"from_direction", (PyCFunction)FromDirection,
     METH_VARARGS | METH_KEYWORDS | METH_STATIC,
     "from_direction(direction: Sequence[float],"
     " up: Sequence[float] = (0.0, 1.0, 0.0)) -> Quat\n"
     "\n"
     "Create a rotation aiming forward (+z) along a direction.\n"
     "\n"
     "The up vector is only a hint for which way to roll about that\n"
     "direction; it gets squared up against it rather than being\n"
     "followed exactly, so passing a rough one is fine. Aiming straight\n"
     "along up leaves the roll undefined, in which case an arbitrary\n"
     "one is picked rather than failing."},
    {"slerp", (PyCFunction)Slerp, METH_VARARGS | METH_KEYWORDS | METH_STATIC,
     "slerp(from_quat: Quat, to_quat: Quat, amount: float) -> Quat\n"
     "\n"
     "Interpolate between two rotations along the shortest arc.\n"
     "\n"
     "An amount of 0 returns the first rotation and 1 the second, with\n"
     "values between sweeping smoothly from one to the other at a\n"
     "constant rate. Note that interpolating a rotation's individual\n"
     "values (as :func:`bascenev1.animate_array()` would) does not do\n"
     "this correctly, so prefer this call when animating rotations."},
    {"inverse", (PyCFunction)Inverse, METH_NOARGS,
     "inverse() -> Quat\n"
     "\n"
     "Return the rotation undoing this one."},
    {"normalized", (PyCFunction)Normalized, METH_NOARGS,
     "normalized() -> Quat\n"
     "\n"
     "Return a unit-length version of this rotation.\n"
     "\n"
     "Composing many rotations together can accumulate enough error to\n"
     "visibly skew things; this cleans that up."},
    {nullptr}};

auto PythonClassQuat::tp_getattro(PythonClassQuat* self, PyObject* attr)
    -> PyObject* {
  BA_PYTHON_TRY;
  assert(PyUnicode_Check(attr));

  const char* s = PyUnicode_AsUTF8(attr);
  if (!strcmp(s, "w")) {
    return PyFloat_FromDouble(self->value[0]);
  } else if (!strcmp(s, "x")) {
    return PyFloat_FromDouble(self->value[1]);
  } else if (!strcmp(s, "y")) {
    return PyFloat_FromDouble(self->value[2]);
  } else if (!strcmp(s, "z")) {
    return PyFloat_FromDouble(self->value[3]);
  }
  return PyObject_GenericGetAttr(reinterpret_cast<PyObject*>(self), attr);
  BA_PYTHON_CATCH;
}

#pragma clang diagnostic pop

}  // namespace ballistica::scene_v1
