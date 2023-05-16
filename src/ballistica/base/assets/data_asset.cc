// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/data_asset.h"

#include "ballistica/base/assets/assets.h"
#include "ballistica/core/python/core_python.h"
#include "ballistica/shared/generic/utils.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::base {

DataAsset::DataAsset(const std::string& file_name_in)
    : file_name_(file_name_in) {
  file_name_full_ =
      g_base->assets->FindAssetFile(Assets::FileType::kData, file_name_in);
  valid_ = true;
}

auto DataAsset::GetAssetType() const -> AssetType { return AssetType::kData; }

auto DataAsset::GetName() const -> std::string {
  if (!file_name_full_.empty()) {
    return file_name_full_;
  } else {
    return "invalid data";
  }
}

void DataAsset::DoPreload() {
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

void DataAsset::DoLoad() {
  assert(g_base->InLogicThread());
  assert(valid_);
  PythonRef args(Py_BuildValue("(s)", raw_input_.c_str()), PythonRef::kSteal);
  object_ = g_core->python->objs()
                .Get(core::CorePython::ObjID::kJsonLoadsCall)
                .Call(args);
  if (!object_.Exists()) {
    throw Exception("Unable to load data: '" + file_name_ + "'.");
  }
}

void DataAsset::DoUnload() {
  assert(g_base->InLogicThread());
  assert(valid_);
  object_.Release();
}

}  // namespace ballistica::base
