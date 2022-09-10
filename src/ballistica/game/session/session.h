// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_SESSION_SESSION_H_
#define BALLISTICA_GAME_SESSION_SESSION_H_

#include "ballistica/core/context.h"
#include "ballistica/core/object.h"

namespace ballistica {

class Session : public ContextTarget {
 public:
  Session();
  ~Session() override;

  // Update the session. Should return real milliseconds until next
  // update is needed.
  virtual void Update(int time_advance);

  // If this returns false, the screen will be cleared as part of rendering.
  virtual auto DoesFillScreen() const -> bool = 0;

  // Draw!!!
  virtual void Draw(FrameDef* f);

  // Return the 'frontmost' context in the session.
  // This is used for executing console command or other UI hotkeys that should
  // apply to whatever the user is seeing.
  virtual auto GetForegroundContext() -> Context;
  virtual void ScreenSizeChanged();
  virtual void LanguageChanged();
  virtual void GraphicsQualityChanged(GraphicsQuality q);
  virtual void DebugSpeedMultChanged();
  auto benchmark_type() const -> BenchmarkType { return benchmark_type_; }
  void set_benchmark_type(BenchmarkType val) { benchmark_type_ = val; }
  virtual void DumpFullState(SceneStream* s);

 private:
  BenchmarkType benchmark_type_ = BenchmarkType::kNone;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_SESSION_SESSION_H_
