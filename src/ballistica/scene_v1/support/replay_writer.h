// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_REPLAY_WRITER_H_
#define BALLISTICA_SCENE_V1_SUPPORT_REPLAY_WRITER_H_

#include <cstdio>
#include <list>
#include <vector>

#include "ballistica/base/assets/assets_server.h"

namespace ballistica::scene_v1 {

class ReplayWriter : public base::AssetsServer::Processor {
 public:
  ReplayWriter();
  void Finish();

  void PushAddMessageToReplayCall(const std::vector<uint8_t>& message);

  void Process() override;

 private:
  void WriteReplayMessages_();
  std::list<std::vector<uint8_t> > replay_messages_;
  FILE* replay_out_file_{};
  size_t replay_bytes_written_{};
  size_t replay_message_bytes_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_REPLAY_WRITER_H_
