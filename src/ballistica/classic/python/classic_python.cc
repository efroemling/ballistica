// Released under the MIT License. See LICENSE for details.

#include "ballistica/classic/python/classic_python.h"

#include "ballistica/classic/python/methods/python_methods_classic.h"
#include "ballistica/scene_v1/support/scene_v1_app_mode.h"
#include "ballistica/shared/python/python_command.h"
#include "ballistica/shared/python/python_module_builder.h"

namespace ballistica::classic {

ClassicPython::ClassicPython() = default;

// Need to declare a plain c PyInit_XXX function with our module name in it so
// we're discoverable when compiled as a standalone binary Python module.
extern "C" auto PyInit__baclassic() -> PyObject* {
  auto* builder = new PythonModuleBuilder(
      "_baclassic", {PythonMethodsClassic::GetMethods()},
      [](PyObject* module) -> int {
        BA_PYTHON_TRY;
        ClassicFeatureSet::OnModuleExec(module);
        return 0;
        BA_PYTHON_INT_CATCH;
      });
  return builder->Build();
}

void ClassicPython::ImportPythonObjs() {
#include "ballistica/classic/mgen/pyembed/binding_classic.inc"
}

void ClassicPython::PlayMusic(const std::string& music_type, bool continuous) {
  BA_PRECONDITION(g_base->InLogicThread());
  if (music_type.empty()) {
    PythonRef args(
        Py_BuildValue("(OO)", Py_None, continuous ? Py_True : Py_False),
        PythonRef::kSteal);
    objs().Get(ObjID::kDoPlayMusicCall).Call(args);
  } else {
    PythonRef args(Py_BuildValue("(sO)", music_type.c_str(),
                                 continuous ? Py_True : Py_False),
                   PythonRef::kSteal);
    objs().Get(ObjID::kDoPlayMusicCall).Call(args);
  }
}

auto ClassicPython::GetControllerValue(base::InputDevice* device,
                                       const std::string& value_name) -> int {
  assert(device);
  assert(objs().Exists(ObjID::kGetInputDeviceMappedValueCall));

  PythonRef args(Py_BuildValue("(sss)", device->GetDeviceName().c_str(),
                               device->GetPersistentIdentifier().c_str(),
                               value_name.c_str()),
                 PythonRef::kSteal);
  PythonRef ret_val;
  {
    Python::ScopedCallLabel label("get_device_value");
    ret_val = objs().Get(ObjID::kGetInputDeviceMappedValueCall).Call(args);
  }
  BA_PRECONDITION(ret_val.Exists());
  if (!PyLong_Check(ret_val.Get())) {
    throw Exception("Non-int returned from get_device_value call.",
                    PyExcType::kType);
  }
  return static_cast<int>(PyLong_AsLong(ret_val.Get()));
}

auto ClassicPython::GetControllerFloatValue(
    base::InputDevice* device, const std::string& value_name) -> float {
  assert(device);
  assert(objs().Exists(ObjID::kGetInputDeviceMappedValueCall));

  PythonRef args(Py_BuildValue("(sss)", device->GetDeviceName().c_str(),
                               device->GetPersistentIdentifier().c_str(),
                               value_name.c_str()),
                 PythonRef::kSteal);
  PythonRef ret_val =
      objs().Get(ObjID::kGetInputDeviceMappedValueCall).Call(args);
  BA_PRECONDITION(ret_val.Exists());
  if (!PyFloat_Check(ret_val.Get())) {
    if (PyLong_Check(ret_val.Get())) {
      return static_cast<float>(PyLong_AsLong(ret_val.Get()));
    } else {
      throw Exception(
          "Non float/int returned from GetControllerFloatValue call.",
          PyExcType::kType);
    }
  }
  return static_cast<float>(PyFloat_AsDouble(ret_val.Get()));
}

auto ClassicPython::BuildPublicPartyStateVal() -> PyObject* {
  auto* appmode = scene_v1::SceneV1AppMode::GetActiveOrThrow();

  auto&& public_ipv4 = appmode->public_party_public_address_ipv4();
  PyObject* ipv4obj;
  if (public_ipv4.has_value()) {
    ipv4obj = PyUnicode_FromString(public_ipv4->c_str());
  } else {
    ipv4obj = Py_None;
    Py_INCREF(ipv4obj);
  }

  auto&& public_ipv6 = appmode->public_party_public_address_ipv6();
  PyObject* ipv6obj;
  if (public_ipv6.has_value()) {
    ipv6obj = PyUnicode_FromString(public_ipv6->c_str());
  } else {
    ipv6obj = Py_None;
    Py_INCREF(ipv6obj);
  }

  return Py_BuildValue(
      "(iiiiisssiOO)", static_cast<int>(appmode->public_party_enabled()),
      appmode->public_party_size(), appmode->public_party_max_size(),
      appmode->public_party_player_count(),
      appmode->public_party_max_player_count(),
      appmode->public_party_name().c_str(),
      appmode->public_party_min_league().c_str(),
      appmode->public_party_stats_url().c_str(),
      static_cast<int>(appmode->public_party_queue_enabled()), ipv4obj,
      ipv6obj);
}

}  // namespace ballistica::classic
