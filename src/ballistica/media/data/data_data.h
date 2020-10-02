// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_DATA_DATA_DATA_H_
#define BALLISTICA_MEDIA_DATA_DATA_DATA_H_

#include <string>

#include "ballistica/media/data/media_component_data.h"
#include "ballistica/python/python_ref.h"

namespace ballistica {

class DataData : public MediaComponentData {
 public:
  DataData() = default;
  explicit DataData(const std::string& file_name_in);

  void DoPreload() override;
  void DoLoad() override;
  void DoUnload() override;

  auto GetMediaType() const -> MediaType override { return MediaType::kData; }
  auto GetName() const -> std::string override {
    if (!file_name_full_.empty()) {
      return file_name_full_;
    } else {
      return "invalid data";
    }
  }
  auto object() -> const PythonRef& {
    assert(InGameThread());
    assert(loaded());
    return object_;
  }
  auto file_name() const -> const std::string& { return file_name_; }
  auto file_name_full() const -> const std::string& { return file_name_full_; }

 private:
  PythonRef object_;
  std::string file_name_;
  std::string file_name_full_;
  std::string raw_input_;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_DATA_DATA_DATA_H_
