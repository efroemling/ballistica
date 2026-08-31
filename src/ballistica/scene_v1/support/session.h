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

  /// A suspended session is frozen but kept alive: it is skipped by the
  /// app-mode's update loop (so its scene time stops dead) and is exempt
  /// from the usual "not foreground means reap it" rule. This is what
  /// lets an instant replay take over the screen mid-match and hand it
  /// back afterwards with the match exactly as it was.
  auto suspended() const -> bool { return suspended_; }
  void set_suspended(bool val) { suspended_ = val; }

 private:
  base::BenchmarkType benchmark_type_ = base::BenchmarkType::kNone;
  bool suspended_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_SESSION_H_
