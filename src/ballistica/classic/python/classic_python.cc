// Released under the MIT License. See LICENSE for details.

#include "ballistica/classic/python/classic_python.h"

#include <string>

#include "ballistica/base/python/base_python.h"
#include "ballistica/classic/python/methods/python_methods_classic.h"
#include "ballistica/classic/support/classic_app_mode.h"
#include "ballistica/shared/python/python_command.h"  // IWYU pragma: keep.
#include "ballistica/shared/python/python_macros.h"
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

  // Cache some basic display values for chests from the Python layer. This
  // way C++ UI stuff doesn't have to call out to Python when drawing the
  // root UI/etc.

  // Pull default chest display info.
  chest_display_default_ = {ChestDisplayFromPython(
      objs().Get(ObjID::kChestAppearanceDisplayInfoDefault))};

  // And overrides.
  for (auto&& item :
       objs().Get(ObjID::kChestAppearanceDisplayInfos).DictItems()) {
    chest_displays_[item.first.GetAttr("value").ValueAsString()] =
        ChestDisplayFromPython(item.second);
  }
}

auto ClassicPython::ChestDisplayFromPython(const PythonRef& ref)
    -> ChestDisplay_ {
  ChestDisplay_ out;

  out.texclosed = ref.GetAttr("texclosed").ValueAsString().c_str();
  out.texclosedtint = ref.GetAttr("texclosedtint").ValueAsString().c_str();
  out.color = base::BasePython::GetPyVector3f(ref.GetAttr("color").get());
  out.tint = base::BasePython::GetPyVector3f(ref.GetAttr("tint").get());
  out.tint2 = base::BasePython::GetPyVector3f(ref.GetAttr("tint2").get());

  return out;
}

void ClassicPython::GetClassicChestDisplayInfo(const std::string& id,
                                               std::string* texclosed,
                                               std::string* texclosedtint,
                                               Vector3f* color, Vector3f* tint,
                                               Vector3f* tint2) {
  assert(texclosed);
  assert(texclosedtint);
  assert(color);
  assert(tint);
  assert(tint2);
  auto&& display{chest_displays_.find(id)};
  if (display != chest_displays_.end()) {
    *texclosed = display->second.texclosed;
    *texclosedtint = display->second.texclosedtint;
    *color = display->second.color;
    *tint = display->second.tint;
    *tint2 = display->second.tint2;
  } else {
    *texclosed = chest_display_default_.texclosed;
    *texclosedtint = chest_display_default_.texclosedtint;
    *color = chest_display_default_.color;
    *tint = chest_display_default_.tint;
    *tint2 = chest_display_default_.tint2;
  }
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
  BA_PRECONDITION(ret_val.exists());
  if (!PyLong_Check(ret_val.get())) {
    throw Exception("Non-int returned from get_device_value call.",
                    PyExcType::kType);
  }
  return static_cast<int>(PyLong_AsLong(ret_val.get()));
}

auto ClassicPython::GetControllerFloatValue(base::InputDevice* device,
                                            const std::string& value_name)
    -> float {
  assert(device);
  assert(objs().Exists(ObjID::kGetInputDeviceMappedValueCall));

  PythonRef args(Py_BuildValue("(sss)", device->GetDeviceName().c_str(),
                               device->GetPersistentIdentifier().c_str(),
                               value_name.c_str()),
                 PythonRef::kSteal);
  PythonRef ret_val =
      objs().Get(ObjID::kGetInputDeviceMappedValueCall).Call(args);
  BA_PRECONDITION(ret_val.exists());
  if (!PyFloat_Check(ret_val.get())) {
    if (PyLong_Check(ret_val.get())) {
      return static_cast<float>(PyLong_AsLong(ret_val.get()));
    } else {
      throw Exception(
          "Non float/int returned from GetControllerFloatValue call.",
          PyExcType::kType);
    }
  }
  return static_cast<float>(PyFloat_AsDouble(ret_val.get()));
}

auto ClassicPython::BuildPublicPartyStateVal() -> PyObject* {
  auto* appmode = ClassicAppMode::GetActiveOrThrow();

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
