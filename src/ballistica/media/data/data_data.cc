// Copyright (c) 2011-2020 Eric Froemling

#include "ballistica/media/data/data_data.h"

#include "ballistica/media/media.h"
#include "ballistica/python/python.h"
#include "ballistica/python/python_sys.h"

namespace ballistica {

DataData::DataData(const std::string& file_name_in) : file_name_(file_name_in) {
  file_name_full_ =
      g_media->FindMediaFile(Media::FileType::kData, file_name_in);
  valid_ = true;
}

void DataData::DoPreload() {
  // NOTE TO SELF: originally I tried to grab the GIL here and do our actual
  // Python loading in Preload().  However this resulted in deadlock
  // in the following case:
  // - asset thread grabs payload lock for Preload()
  // - asset thread tries to grab GIL in Preload(); spins.
  // - meanwhile, something in game thread has called Load()
  // - game thread holds GIL by default and now spins waiting on payload lock.
  // - deadlock :-(

  // ...so the new plan is to simply load the file into a string in Preload()
  // and then do the Python work in Load(). This should still avoid the nastiest
  // IO-related hitches at least..

  raw_input_ = Utils::FileToString(file_name_full_);
}

void DataData::DoLoad() {
  assert(InGameThread());
  assert(valid_);
  PythonRef args(Py_BuildValue("(s)", raw_input_.c_str()), PythonRef::kSteal);
  object_ = g_python->obj(Python::ObjID::kJsonLoadsCall).Call(args);
  if (!object_.exists()) {
    throw Exception("Unable to load data: '" + file_name_ + "'.");
  }
}

void DataData::DoUnload() {
  assert(InGameThread());
  assert(valid_);
  object_.Release();
}

}  // namespace ballistica
