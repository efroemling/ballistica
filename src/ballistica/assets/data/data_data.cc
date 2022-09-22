// Released under the MIT License. See LICENSE for details.

#include "ballistica/assets/data/data_data.h"

#include "ballistica/assets/assets.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

DataData::DataData(const std::string& file_name_in) : file_name_(file_name_in) {
  file_name_full_ =
      g_assets->FindAssetFile(Assets::FileType::kData, file_name_in);
  valid_ = true;
}

void DataData::DoPreload() {
  // NOTE TO SELF: originally I tried to grab the GIL here and do our actual
  // Python loading in Preload().  However this resulted in deadlock
  // in the following case:
  // - asset thread grabs payload lock for Preload()
  // - asset thread tries to grab GIL in Preload(); spins.
  // - meanwhile, something in logic thread has called Load()
  // - logic thread holds GIL by default and now spins waiting on payload lock.
  // - deadlock :-(

  // ...so the new plan is to simply load the file into a string in Preload()
  // and then do the Python work in Load(). This should still avoid the nastiest
  // IO-related hitches at least..

  raw_input_ = Utils::FileToString(file_name_full_);
}

void DataData::DoLoad() {
  assert(InLogicThread());
  assert(valid_);
  PythonRef args(Py_BuildValue("(s)", raw_input_.c_str()), PythonRef::kSteal);
  object_ = g_python->obj(Python::ObjID::kJsonLoadsCall).Call(args);
  if (!object_.exists()) {
    throw Exception("Unable to load data: '" + file_name_ + "'.");
  }
}

void DataData::DoUnload() {
  assert(InLogicThread());
  assert(valid_);
  object_.Release();
}

}  // namespace ballistica
