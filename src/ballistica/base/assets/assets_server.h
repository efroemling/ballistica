// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_ASSETS_ASSETS_SERVER_H_
#define BALLISTICA_BASE_ASSETS_ASSETS_SERVER_H_

// #include <cstdio>
// #include <list>
#include <vector>

#include "ballistica/base/base.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::base {

class AssetsServer {
 public:
  /// Something that uses the asset-server thread to do some background
  /// processing (writing replay files, etc).
  class Processor {
   public:
    virtual void Process() = 0;
  };

  AssetsServer();
  void OnMainThreadStartApp();
  void PushPendingPreload(Object::Ref<Asset>* asset_ref_ptr);
  auto event_loop() const -> EventLoop* { return event_loop_; }

  void AddProcessor(Processor* processor);
  void RemoveProcessor(Processor* processor);

 private:
  void OnAppStartInThread_();
  void Process_();
  void WriteReplayMessages_();

  std::vector<Object::Ref<Asset>*> pending_preloads_;
  std::vector<Object::Ref<Asset>*> pending_preloads_audio_;
  std::mutex processors_mutex_;
  std::vector<Processor*> processors_;
  EventLoop* event_loop_{};
  Timer* process_timer_{};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_ASSETS_ASSETS_SERVER_H_
