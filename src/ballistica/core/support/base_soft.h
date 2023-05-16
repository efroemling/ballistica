// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_SUPPORT_BASE_SOFT_H_
#define BALLISTICA_CORE_SUPPORT_BASE_SOFT_H_

#include "ballistica/core/core.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::core {

/// 'Soft' interface to the base feature-set.
/// Feature-sets listing base as a soft requirement must limit their use of
/// base to these methods and should be prepared to handle the not-present
/// case.
class BaseSoftInterface {
 public:
  virtual void ScreenMessage(const std::string& s, const Vector3f& color) = 0;
  virtual auto IsUnmodifiedBlessedBuild() -> bool = 0;
  virtual void StartApp() = 0;
  virtual auto AppManagesEventLoop() -> bool = 0;
  virtual void RunAppToCompletion() = 0;
  virtual void PrimeAppMainThreadEventPump() = 0;
  virtual auto InAssetsThread() const -> bool = 0;
  virtual auto InLogicThread() const -> bool = 0;
  virtual auto InGraphicsThread() const -> bool = 0;
  virtual auto InAudioThread() const -> bool = 0;
  virtual auto InBGDynamicsThread() const -> bool = 0;
  virtual auto InNetworkWriteThread() const -> bool = 0;
  virtual void PlusDirectSendV1CloudLogs(const std::string& prefix,
                                         const std::string& suffix,
                                         bool instant, int* result) = 0;
  virtual auto CreateFeatureSetData(FeatureSetFrontEnd* featureset)
      -> PyObject* = 0;
  virtual auto FeatureSetFromData(PyObject* obj) -> FeatureSetFrontEnd* = 0;
  virtual void V1CloudLog(const std::string& msg) = 0;
  virtual void PushConsolePrintCall(const std::string& msg) = 0;
  virtual auto GetPyExceptionType(PyExcType exctype) -> PyObject* = 0;
  virtual auto PrintPythonStackTrace() -> bool = 0;
  virtual auto GetPyLString(PyObject* obj) -> std::string = 0;
  virtual auto DoGetContextBaseString() -> std::string = 0;
  virtual void DoPrintContextAuto() = 0;
  virtual void DoPushObjCall(const PythonObjectSetBase* objset, int id) = 0;
  virtual void DoPushObjCall(const PythonObjectSetBase* objset, int id,
                             const std::string& arg) = 0;
  virtual auto IsAppRunning() const -> bool = 0;
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_SUPPORT_BASE_SOFT_H_
