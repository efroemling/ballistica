// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_SUPPORT_BASE_SOFT_H_
#define BALLISTICA_CORE_SUPPORT_BASE_SOFT_H_

#include <string>
#include <string_view>
#include <vector>

#include "ballistica/shared/foundation/feature_set_native_component.h"
#include "ballistica/shared/math/vector3f.h"
#include "ballistica/shared/math/vector4f.h"

namespace ballistica::core {

/// One log entry's worth of dev-console output: a single text line plus its
/// scale and color. A log message expands to a few of these (a spacer, a
/// prefix line, the message body) which are pushed together so the whole
/// entry costs one cross-thread call instead of one per line. See
/// :cpp:func:`BaseSoftInterface::PushDevConsolePrintCall`.
struct DevConsolePrintEntry {
  std::string msg;
  float scale;
  Vector4f color;
};

/// 'Soft' interface to the base feature-set. Feature-sets listing base as a
/// soft requirement must limit their use of base to these methods and
/// should be prepared to handle the not-present case.
class BaseSoftInterface {
 public:
  virtual void ScreenMessage(const std::string& s,
                             const Vector3f& color = {1.0f, 1.0f, 1.0f},
                             bool literal = false) = 0;
  virtual auto IsUnmodifiedBlessedBuild() -> bool = 0;
  virtual void StartApp() = 0;
  virtual auto AppManagesMainThreadEventLoop() -> bool = 0;
  virtual void RunAppToCompletion() = 0;

  /// Process exit code to return from a clean app shutdown. Defaults to
  /// 0; a clean-but-failing exit (e.g. a headless construct-mode asset
  /// bring-up failure) sets a specific nonzero code. Distinct from a
  /// fatal-error/abort exit.
  virtual auto AppExitCode() const -> int = 0;
  virtual auto InAssetsThread() const -> bool = 0;
  virtual auto InLogicThread() const -> bool = 0;
  virtual auto InAudioThread() const -> bool = 0;
  virtual auto InGraphicsContext() const -> bool = 0;
  virtual auto InBGDynamicsThread() const -> bool = 0;
  virtual auto InNetworkWriteThread() const -> bool = 0;
  virtual void PlusDirectSendV1CloudLogs(const std::string& prefix,
                                         const std::string& suffix,
                                         bool instant, int* result) = 0;
  virtual auto CreateFeatureSetData(FeatureSetNativeComponent* featureset)
      -> PyObject* = 0;
  virtual auto FeatureSetFromData(PyObject* obj)
      -> FeatureSetNativeComponent* = 0;
  virtual void DoV1CloudLog(const std::string& msg) = 0;
  /// Print one log entry's worth of dev-console lines in a SINGLE
  /// cross-thread call. The batching is load-bearing: the dev-console
  /// mirror runs one logic-thread PushCall per call, so a per-line call
  /// lets a logging burst flood the logic thread's message queue (tripping
  /// the >1000 ThreadMessage ERROR and, at >10000, a FatalError). Group all
  /// lines of one entry into a single call.
  virtual void PushDevConsolePrintCall(
      std::vector<DevConsolePrintEntry> entries) = 0;
  virtual auto GetPyExceptionType(PyExcType exctype) -> PyObject* = 0;
  virtual auto PrintPythonStackTrace() -> bool = 0;
  virtual auto GetPyLString(PyObject* obj) -> std::string = 0;
  virtual auto DoContextBaseString() -> std::string = 0;
  virtual void DoPrintContextAuto() = 0;
  virtual void DoPushObjCall(const PythonObjectSetBase* objset, int id) = 0;
  virtual void DoPushObjCall(const PythonObjectSetBase* objset, int id,
                             const std::string& arg) = 0;
  virtual auto IsAppStarted() const -> bool = 0;
  virtual auto IsAppBootstrapped() const -> bool = 0;
  virtual void PushMainThreadRunnable(Runnable* runnable) = 0;
  virtual void HandleInterruptSignal() = 0;
  virtual void HandleTerminateSignal() = 0;
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_SUPPORT_BASE_SOFT_H_
