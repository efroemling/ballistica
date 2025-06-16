// Released under the MIT License. See LICENSE for details.

#include "ballistica/scene_v1/support/replay_writer.h"

#include <cstdio>
#include <string>
#include <vector>

#include "ballistica/base/assets/assets_server.h"
#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/scene_v1/scene_v1.h"
#include "ballistica/scene_v1/support/huffman.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::scene_v1 {

ReplayWriter::ReplayWriter() {
  g_base->assets_server->AddProcessor(this);
  g_base->assets_server->event_loop()->PushCall([this] {
    std::string f_name = "__lastReplay";
    assert(g_core);
    std::string file_path =
        g_core->platform->GetReplaysDir() + BA_DIRSLASH + f_name + ".brp";
    replay_out_file_ = g_core->platform->FOpen(file_path.c_str(), "wb");
    replay_bytes_written_ = 0;

    if (!replay_out_file_) {
      g_core->logging->Log(
          LogName::kBa, LogLevel::kError,
          "unable to open output-stream file: '" + file_path + "'");
    } else {
      // Write file id and protocol-version.
      //
      // NOTE: We always write replays in our host protocol version no
      // matter what the client stream is.
      uint32_t file_id = kBrpFileID;
      uint16_t version = kProtocolVersionMax;
      if ((fwrite(&file_id, sizeof(file_id), 1, replay_out_file_) != 1)
          || (fwrite(&version, sizeof(version), 1, replay_out_file_) != 1)) {
        fclose(replay_out_file_);
        replay_out_file_ = nullptr;
        g_core->logging->Log(LogName::kBa, LogLevel::kError,
                             "error writing replay file header: "
                                 + g_core->platform->GetErrnoString());
      }
      replay_bytes_written_ = 5;
    }
  });
}

void ReplayWriter::WriteReplayMessages_() {
  if (replay_out_file_) {
    for (auto&& i : replay_messages_) {
      std::vector<uint8_t> data_compressed = g_scene_v1->huffman->compress(i);

      // If message length is < 254, write length as one byte.
      // If its between 254 and 65535, write 254 and then 2 length bytes
      // otherwise write 255 and then 4 length bytes.
      auto len32 = static_cast<uint32_t>(data_compressed.size());
      {
        uint8_t len8;
        if (len32 < 254) {
          len8 = static_cast_check_fit<uint8_t>(len32);
        } else if (len32 < 65535) {
          len8 = 254;
        } else {
          len8 = 255;
        }
        if (fwrite(&len8, 1, 1, replay_out_file_) != 1) {
          fclose(replay_out_file_);
          replay_out_file_ = nullptr;
          g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                               "Error writing replay file: "
                                   + g_core->platform->GetErrnoString());
          return;
        }
      }
      // write 16 bit val if need be.
      if (len32 >= 254) {
        if (len32 <= 65535) {
          auto len16 = static_cast_check_fit<uint16_t>(len32);
          if (fwrite(&len16, 2, 1, replay_out_file_) != 1) {
            fclose(replay_out_file_);
            replay_out_file_ = nullptr;
            g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                                 "Error writing replay file: "
                                     + g_core->platform->GetErrnoString());
            return;
          }
        } else {
          if (fwrite(&len32, 4, 1, replay_out_file_) != 1) {
            fclose(replay_out_file_);
            replay_out_file_ = nullptr;
            g_core->logging->Log(LogName::kBaAudio, LogLevel::kError,
                                 "Error writing replay file: "
                                     + g_core->platform->GetErrnoString());
            return;
          }
        }
      }
      // Write buffer.
      size_t result = fwrite(&(data_compressed[0]), data_compressed.size(), 1,
                             replay_out_file_);
      if (result != 1) {
        fclose(replay_out_file_);
        replay_out_file_ = nullptr;
        g_core->logging->Log(
            LogName::kBaAudio, LogLevel::kError,
            "Error writing replay file: " + g_core->platform->GetErrnoString());
        return;
      }
      replay_bytes_written_ += data_compressed.size() + 2;
    }
    replay_messages_.clear();
    replay_message_bytes_ = 0;
  }
}

void ReplayWriter::Finish() {
  g_base->assets_server->RemoveProcessor(this);
  g_base->assets_server->event_loop()->PushCall([this] {
    WriteReplayMessages_();

    if (replay_out_file_) {
      fclose(replay_out_file_);
      replay_out_file_ = nullptr;
    }
    delete this;
  });
}

void ReplayWriter::PushAddMessageToReplayCall(
    const std::vector<uint8_t>& message) {
  g_base->assets_server->event_loop()->PushCall([this, message] {
    // Just add it to our list.
    if (replay_out_file_) {
      // If we've got too much data built up (lets go with 10 megs for now),
      // abort.
      if (replay_message_bytes_ > 10000000) {
        g_core->logging->Log(
            LogName::kBa, LogLevel::kError,
            "replay output buffer exceeded 10 megs; aborting replay");
        fclose(replay_out_file_);
        replay_out_file_ = nullptr;
        replay_message_bytes_ = 0;
        replay_messages_.clear();
        return;
      }
      replay_message_bytes_ += message.size();
      replay_messages_.push_back(message);
    }
  });
}

void ReplayWriter::Process() { WriteReplayMessages_(); }

}  // namespace ballistica::scene_v1
