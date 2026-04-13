// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/assets/assets_server.h"

#include <vector>

#include "ballistica/base/assets/asset.h"
#include "ballistica/base/assets/assets.h"
#include "ballistica/base/graphics/graphics.h"
#include "ballistica/core/core.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/foundation/macros.h"

namespace ballistica::base {

AssetsServer::AssetsServer() = default;

void AssetsServer::OnMainThreadStartApp() {
  // Spin up our thread.
  event_loop_ = new EventLoop(EventLoopID::kAssets);
  g_core->suspendable_event_loops.push_back(event_loop_);

  event_loop_->PushCallSynchronous([this] { OnAppStartInThread_(); });
}

void AssetsServer::OnAppStartInThread_() {
  assert(g_base->InAssetsThread());
  // Ask our thread to give us periodic processing time (close to but not
  // *exactly* one second; try to avoid aliasing with similar updates).
  process_timer_ = event_loop()->NewTimer(
      987 * 1000, true, NewLambdaRunnable([this] { Process_(); }).get());
}

void AssetsServer::PushPendingPreload(Object::Ref<Asset>* asset_ref_ptr) {
  event_loop()->PushCall([this, asset_ref_ptr] {
    assert(g_base->InAssetsThread());

    // Add our pointer to one of the preload lists and shake our preload
    // thread to wake it up.
    if ((**asset_ref_ptr).GetAssetType() == AssetType::kSound) {
      pending_preloads_audio_.push_back(asset_ref_ptr);
    } else {
      pending_preloads_.push_back(asset_ref_ptr);
    }
    process_timer_->SetLength(0);
  });
}

void AssetsServer::AddProcessor(Processor* processor) {
  std::scoped_lock lock(processors_mutex_);
  processors_.push_back(processor);

  g_base->assets_server->event_loop()->PushCall(
      [this] { g_base->assets_server->process_timer_->SetLength(0); });
}

void AssetsServer::RemoveProcessor(Processor* processor) {
  std::scoped_lock lock(processors_mutex_);

  bool found{};
  for (auto&& i = processors_.begin(); i != processors_.end(); ++i) {
    if (*i == processor) {
      found = true;
      processors_.erase(i);
      break;
    }
  }
  BA_PRECONDITION_FATAL(found);
}

void AssetsServer::Process_() {
  // Make sure we don't do any loading until we know what kind/quality of
  // textures we'll be loading.

  // FIXME - we'll need to revisit this when adding support for renderer
  // switches, since this is not especially thread-safe.

  if (!g_base->graphics->has_client_context()) {
    return;
  }

  // Process exactly 1 preload item. Empty out our non-audio list first
  // (audio is less likely to cause noticeable hitches if it needs to be
  // loaded on-demand, so that's a lower priority for us).
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

  // Give all attached processors processing time.
  bool have_processors{};
  {
    std::scoped_lock lock(processors_mutex_);
    if (!processors_.empty()) {
      have_processors = true;
    }
    for (auto&& p : processors_) {
      p->Process();
    }
  }

  // If we've got nothing left, set our timer to go off every now and then
  // if we've got any processors doing work. Otherwise just sleep
  // indefinitely.
  if (pending_preloads_.empty() && pending_preloads_audio_.empty()) {
    if (have_processors) {
      process_timer_->SetLength(1000 * 1000);
    } else {
      process_timer_->SetLength(-1);
    }
  }
}

}  // namespace ballistica::base
