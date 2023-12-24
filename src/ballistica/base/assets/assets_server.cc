// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/assets_server.h"

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/base/support/huffman.h"
#include "ballistica/shared/foundation/event_loop.h"

namespace ballistica::base {

AssetsServer::AssetsServer() = default;

void AssetsServer::OnMainThreadStartApp() {
  // Spin up our thread.
  event_loop_ = new EventLoop(EventLoopID::kAssets);
  g_core->suspendable_event_loops.push_back(event_loop_);

  event_loop_->PushCallSynchronous([this] { OnAppStartInThread(); });
}

void AssetsServer::OnAppStartInThread() {
  assert(g_base->InAssetsThread());
  // Ask our thread to give us periodic processing time (close to but
  // not *exactly* one second; try to avoid aliasing with similar updates).
  process_timer_ = event_loop()->NewTimer(
      987 * 1000, true, NewLambdaRunnable([this] { Process(); }).Get());
}

void AssetsServer::PushPendingPreload(Object::Ref<Asset>* asset_ref_ptr) {
  event_loop()->PushCall([this, asset_ref_ptr] {
    assert(g_base->InAssetsThread());

    // Add our pointer to one of the preload lists and shake our preload thread
    // to wake it up
    if ((**asset_ref_ptr).GetAssetType() == AssetType::kSound) {
      pending_preloads_audio_.push_back(asset_ref_ptr);
    } else {
      pending_preloads_.push_back(asset_ref_ptr);
    }
    process_timer_->SetLength(0);
  });
}

void AssetsServer::PushBeginWriteReplayCall(uint16_t protocol_version) {
  event_loop()->PushCall([this, protocol_version] {
    if (replays_broken_) {
      return;
    }

    // We only allow writing one replay at once; make sure that's actually
    // the case.
    if (writing_replay_) {
      Log(LogLevel::kError,
          "AssetsServer got BeginWriteReplayCall while already writing");
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
    assert(g_core);
    std::string file_path =
        g_core->platform->GetReplaysDir() + BA_DIRSLASH + f_name + ".brp";
    replay_out_file_ = g_core->platform->FOpen(file_path.c_str(), "wb");
    replay_bytes_written_ = 0;

    if (!replay_out_file_) {
      Log(LogLevel::kError,
          "unable to open output-stream file: '" + file_path + "'");
    } else {
      // Write file id and protocol-version.
      // NOTE: We always write replays in our host protocol version
      // no matter what the client stream is.
      uint32_t file_id = kBrpFileID;
      uint16_t version = protocol_version;
      if ((fwrite(&file_id, sizeof(file_id), 1, replay_out_file_) != 1)
          || (fwrite(&version, sizeof(version), 1, replay_out_file_) != 1)) {
        fclose(replay_out_file_);
        replay_out_file_ = nullptr;
        Log(LogLevel::kError, "error writing replay file header: "
                                  + g_core->platform->GetErrnoString());
      }
      replay_bytes_written_ = 5;
    }

    // Trigger our process timer to go off immediately
    // (we may need to wake it up).
    g_base->assets_server->process_timer_->SetLength(0);
  });
}

void AssetsServer::PushAddMessageToReplayCall(
    const std::vector<uint8_t>& data) {
  event_loop()->PushCall([this, data] {
    if (replays_broken_) {
      return;
    }

    // Sanity check.
    if (!writing_replay_) {
      Log(LogLevel::kError,
          "AssetsServer got AddMessageToReplayCall while not writing replay");
      replays_broken_ = true;
      return;
    }

    // Just add it to our list.
    if (replay_out_file_) {
      // If we've got too much data built up (lets go with 10 megs for now),
      // abort.
      if (replay_message_bytes_ > 10000000) {
        Log(LogLevel::kError,
            "replay output buffer exceeded 10 megs; aborting replay");
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
  event_loop()->PushCall([this] {
    if (replays_broken_) {
      return;
    }

    // Sanity check.
    if (!writing_replay_) {
      Log(LogLevel::kError, "_finishWritingReplay called while not writing");
      replays_broken_ = true;
      return;
    }
    WriteReplayMessages();

    // Whether or not we actually have a file has no impact on our
    // writing_replay_ status.
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
      std::vector<uint8_t> data_compressed = g_base->huffman->compress(i);

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
          Log(LogLevel::kError, "error writing replay file: "
                                    + g_core->platform->GetErrnoString());
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
            Log(LogLevel::kError, "error writing replay file: "
                                      + g_core->platform->GetErrnoString());
            return;
          }
        } else {
          if (fwrite(&len32, 4, 1, replay_out_file_) != 1) {
            fclose(replay_out_file_);
            replay_out_file_ = nullptr;
            Log(LogLevel::kError, "error writing replay file: "
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
        Log(LogLevel::kError,
            "error writing replay file: " + g_core->platform->GetErrnoString());
        return;
      }
      replay_bytes_written_ += data_compressed.size() + 2;
    }
    replay_messages_.clear();
    replay_message_bytes_ = 0;
  }
}

void AssetsServer::Process() {
  // Make sure we don't do any loading until we know what kind/quality of
  // textures we'll be loading.

  // FIXME - we'll need to revisit this when adding support for
  // renderer switches, since this is not especially thread-safe.

  if (!g_base->graphics->has_client_context()) {
    return;
  }
  // if (!g_base->assets ||
  //     || !g_base->graphics->texture_compression_types_are_set()  // NOLINT
  //     || !g_base->graphics_server->texture_quality_set()) {
  //   return;
  // }

  // Process exactly 1 preload item. Empty out our non-audio list first
  // (audio is less likely to cause noticeable hitches if it needs to be loaded
  // on-demand, so that's a lower priority for us).
  if (!pending_preloads_.empty()) {
    (**pending_preloads_.back()).Preload();
    // Pass the ref-pointer along to the load queue.
    g_base->assets->AddPendingLoad(pending_preloads_.back());
    pending_preloads_.pop_back();
  } else if (!pending_preloads_audio_.empty()) {
    (**pending_preloads_audio_.back()).Preload();
    // Pass the ref-pointer along to the load queue.
    g_base->assets->AddPendingLoad(pending_preloads_audio_.back());
    pending_preloads_audio_.pop_back();
  }

  // If we're writing a replay, dump anything we've got built up.
  if (writing_replay_) {
    WriteReplayMessages();
  }

  // If we've got nothing left, set our timer to go off every now and then if
  // we're writing a replay.. otherwise just sleep indefinitely.
  if (pending_preloads_.empty() && pending_preloads_audio_.empty()) {
    if (writing_replay_) {
      process_timer_->SetLength(1000 * 1000);
    } else {
      process_timer_->SetLength(-1);
    }
  }
}

}  // namespace ballistica::base
