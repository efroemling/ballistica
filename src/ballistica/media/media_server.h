// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_MEDIA_MEDIA_SERVER_H_
#define BALLISTICA_MEDIA_MEDIA_SERVER_H_

#include <list>
#include <vector>

#include "ballistica/core/module.h"

namespace ballistica {

class MediaServer : public Module {
 public:
  explicit MediaServer(Thread* thread);
  ~MediaServer() override;
  void PushBeginWriteReplayCall();
  void PushEndWriteReplayCall();
  void PushAddMessageToReplayCall(const std::vector<uint8_t>& data);

 private:
  void Process();
  void WriteReplayMessages();
  FILE* replay_out_file_{};
  size_t replay_bytes_written_{};
  bool writing_replay_{};
  bool replays_broken_{};
  std::list<std::vector<uint8_t> > replay_messages_;
  size_t replay_message_bytes_{};
  Timer* process_timer_{};
  std::vector<Object::Ref<MediaComponentData>*> pending_preloads_;
  std::vector<Object::Ref<MediaComponentData>*> pending_preloads_audio_;
  friend struct PreloadRunnable;
  friend class Media;
};

}  // namespace ballistica

#endif  // BALLISTICA_MEDIA_MEDIA_SERVER_H_
