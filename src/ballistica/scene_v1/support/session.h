// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_SESSION_H_
#define BALLISTICA_SCENE_V1_SUPPORT_SESSION_H_

#include "ballistica/base/base.h"
#include "ballistica/base/support/context.h"
#include "ballistica/scene_v1/support/scene_v1_context.h"
#include "ballistica/shared/foundation/object.h"

namespace ballistica::scene_v1 {

class Session : public SceneV1Context {
 public:
  Session();
  ~Session() override;

  /// Update the session. Passed a legacy millisecs advance and
  /// a modern seconds advance.
  virtual void Update(int time_advance_millisecs, double time_advance);

  /// Note: this should be returned in microsecs.
  virtual auto TimeToNextEvent() -> std::optional<microsecs_t>;

  // If this returns false, the screen will be cleared as part of rendering.
  virtual auto DoesFillScreen() const -> bool = 0;

  // Draw!!!
  virtual void Draw(base::FrameDef* f);

  // Return the 'frontmost' context in the session.
  // This is used for executing console command or other UI hotkeys that should
  // apply to whatever the user is seeing.
  virtual auto GetForegroundContext() -> base::ContextRef;
  virtual void OnScreenSizeChange();
  virtual void LanguageChanged();
  virtual void DebugSpeedMultChanged();
  auto benchmark_type() const -> base::BenchmarkType { return benchmark_type_; }
  void set_benchmark_type(base::BenchmarkType val) { benchmark_type_ = val; }
  virtual void DumpFullState(SessionStream* s);

 private:
  base::BenchmarkType benchmark_type_ = base::BenchmarkType::kNone;
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SESSION_H_
