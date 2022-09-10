// Released under the MIT License. See LICENSE for details.

#include "ballistica/assets/assets_server.h"

#include "ballistica/assets/assets.h"
#include "ballistica/assets/data/asset_component_data.h"
#include "ballistica/core/thread.h"
#include "ballistica/generic/huffman.h"
#include "ballistica/generic/timer.h"
#include "ballistica/generic/utils.h"
#include "ballistica/graphics/graphics_server.h"

namespace ballistica {

AssetsServer::AssetsServer(Thread* thread)
    : thread_(thread),
      writing_replay_(false),
      replay_message_bytes_(0),
      replays_broken_(false),
      replay_out_file_(nullptr) {
  assert(g_assets_server == nullptr);
  g_assets_server = this;

  // get our thread to give us periodic processing time...
  process_timer_ = this->thread()->NewTimer(
      1000, true, NewLambdaRunnable([this] { Process(); }));
}

AssetsServer::~AssetsServer() = default;

void AssetsServer::PushBeginWriteReplayCall() {
  thread()->PushCall([this] {
    if (replays_broken_) {
      return;
    }

    // we only allow writing one replay at once; make sure that's actually the
    // case
    if (writing_replay_) {
      Log("AssetsServer got BeginWriteReplayCall while already writing");
      WriteReplayMessages();
      if (replay_out_file_) {
        fclose(replay_out_file_);
      }
      replay_out_file_ = nullptr;
      replays_broken_ = true;
      return;
    }
    writing_replay_ = true;

    std::string f_name = "__lastReplay";
    assert(g_platform);
    std::string file_path =
        g_platform->GetReplaysDir() + BA_DIRSLASH + f_name + ".brp";
    replay_out_file_ = g_platform->FOpen(file_path.c_str(), "wb");
    replay_bytes_written_ = 0;

    if (!replay_out_file_) {
      Log("ERROR: unable to open output-stream file: '" + file_path + "'");
    } else {
      // write file id and protocol-version
      // NOTE - we always write replays in our host protocol version
      // no matter what the client stream is
      uint32_t file_id = kBrpFileID;
      uint16_t version = kProtocolVersion;
      if ((fwrite(&file_id, sizeof(file_id), 1, replay_out_file_) != 1)
          || (fwrite(&version, sizeof(version), 1, replay_out_file_) != 1)) {
        fclose(replay_out_file_);
        replay_out_file_ = nullptr;
        Log("error writing replay file header: "
            + g_platform->GetErrnoString());
      }
      replay_bytes_written_ = 5;
    }

    // trigger our process timer to go off immediately
    // (we may need to wake it up)
    g_assets_server->process_timer_->SetLength(0);
  });
}

void AssetsServer::PushAddMessageToReplayCall(
    const std::vector<uint8_t>& data) {
  thread()->PushCall([this, data] {
    if (replays_broken_) {
      return;
    }

    // sanity check..
    if (!writing_replay_) {
      Log("AssetsServer got AddMessageToReplayCall while not writing replay");
      replays_broken_ = true;
      return;
    }

    // just add it to our list
    if (replay_out_file_) {
      // if we've got too much data built up (lets go with 10 megs for now),
      // abort
      if (replay_message_bytes_ > 10000000) {
        Log("replay output buffer exceeded 10 megs; aborting replay");
        fclose(replay_out_file_);
        replay_out_file_ = nullptr;
        replay_message_bytes_ = 0;
        replay_messages_.clear();
        return;
      }
      replay_message_bytes_ += data.size();
      replay_messages_.push_back(data);
    }
  });
}

void AssetsServer::PushEndWriteReplayCall() {
  thread()->PushCall([this] {
    if (replays_broken_) {
      return;
    }

    // sanity check..
    if (!writing_replay_) {
      Log("_finishWritingReplay called while not writing");
      replays_broken_ = true;
      return;
    }
    WriteReplayMessages();

    // whether or not we actually have a file has no impact on our
    // writing_replay_ status..
    if (replay_out_file_) {
      fclose(replay_out_file_);
      replay_out_file_ = nullptr;
    }
    writing_replay_ = false;
  });
}

void AssetsServer::WriteReplayMessages() {
  if (replay_out_file_) {
    for (auto&& i : replay_messages_) {
      std::vector<uint8_t> data_compressed = g_utils->huffman()->compress(i);

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
          Log("error writing replay file: " + g_platform->GetErrnoString());
          return;
        }
      }
      // write 16 bit val if need be..
      if (len32 >= 254) {
        if (len32 <= 65535) {
          auto len16 = static_cast_check_fit<uint16_t>(len32);
          if (fwrite(&len16, 2, 1, replay_out_file_) != 1) {
            fclose(replay_out_file_);
            replay_out_file_ = nullptr;
            Log("error writing replay file: " + g_platform->GetErrnoString());
            return;
          }
        } else {
          if (fwrite(&len32, 4, 1, replay_out_file_) != 1) {
            fclose(replay_out_file_);
            replay_out_file_ = nullptr;
            Log("error writing replay file: " + g_platform->GetErrnoString());
            return;
          }
        }
      }
      // write buffer
      size_t result = fwrite(&(data_compressed[0]), data_compressed.size(), 1,
                             replay_out_file_);
      if (result != 1) {
        fclose(replay_out_file_);
        replay_out_file_ = nullptr;
        Log("error writing replay file: " + g_platform->GetErrnoString());
        return;
      }
      replay_bytes_written_ += data_compressed.size() + 2;
    }
    replay_messages_.clear();
    replay_message_bytes_ = 0;
  }
}

void AssetsServer::Process() {
  // make sure we don't do any loading until we know what kind/quality of
  // textures we'll be loading
  if (!g_assets || !g_graphics_server
      || !g_graphics_server->texture_compression_types_are_set()  // NOLINT
      || !g_graphics_server->texture_quality_set()) {
    return;
  }

  // process exactly 1 preload item.. empty out our non-audio list first
  // (audio is less likely to cause noticeable hitches if it needs to be loaded
  // on-demand, so that's a lower priority for us)
  if (!pending_preloads_.empty()) {
    (**pending_preloads_.back()).Preload();
    // pass the ref-pointer along to the load queue
    g_assets->AddPendingLoad(pending_preloads_.back());
    pending_preloads_.pop_back();
  } else if (!pending_preloads_audio_.empty()) {
    (**pending_preloads_audio_.back()).Preload();
    // pass the ref-pointer along to the load queue
    g_assets->AddPendingLoad(pending_preloads_audio_.back());
    pending_preloads_audio_.pop_back();
  }

  // if we're writing a replay, dump anything we've got built up..
  if (writing_replay_) {
    WriteReplayMessages();
  }

  // if we've got nothing left, set our timer to go off every now and then if
  // we're writing a replay.. otherwise just sleep indefinitely.
  if (pending_preloads_.empty() && pending_preloads_audio_.empty()) {
    if (writing_replay_) {
      process_timer_->SetLength(1000);
    } else {
      process_timer_->SetLength(-1);
    }
  }
}

}  // namespace ballistica
