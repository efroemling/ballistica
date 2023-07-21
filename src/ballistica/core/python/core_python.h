// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_
#define BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_

#include <list>
#include <mutex>

#include "ballistica/core/core.h"
#include "ballistica/shared/python/python_object_set.h"

namespace ballistica::core {

/// General Python support class for our feature-set.
class CorePython {
 public:
  /// Specific Python objects we hold in objs_.
  enum class ObjID {
    kMainDict,
    kShallowCopyCall,
    kDeepCopyCall,
    kJsonDumpsCall,
    kJsonLoadsCall,
    kEmptyTuple,
    kLoggingDebugCall,
    kLoggingInfoCall,
    kLoggingWarningCall,
    kLoggingErrorCall,
    kLoggingCriticalCall,
    kPrependSysPathCall,
    kBaEnvConfigureCall,
    kBaEnvGetConfigCall,
    kLast  // Sentinel; must be at end.
  };

  /// Bring up Python itself. Only needed in Monolithic builds.
  void InitPython();

  /// Run baenv.configure() with all of our monolithic-mode paths/etc.
  void MonolithicModeBaEnvConfigure();

  /// Call once we should start forwarding our Log calls (along with all
  /// pent up ones) to Python.
  void EnablePythonLoggingCalls();

  /// Should be called just before base feature set import; locks in the
  /// baenv environment and runs some checks.
  void ApplyBaEnvConfig();

  /// Calls Python logging function (logging.error, logging.warning, etc.)
  /// Can be called from any thread at any time. If called before Python
  /// logging is available, logs locally using Logging::DisplayLog()
  /// (with an added warning).
  void LoggingCall(LogLevel loglevel, const std::string& msg);
  void ImportPythonObjs();
  void VerifyPythonEnvironment();
  void SoftImportBase();

  const auto& objs() { return objs_; }

 private:
  PythonObjectSet<ObjID> objs_;

  // Log calls we make before we're set up to ship logs through Python
  // go here. They all get shipped at once as soon as it is possible.
  bool python_logging_calls_enabled_{};
  std::mutex early_log_lock_;
  std::list<std::pair<LogLevel, std::string>> early_logs_;
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_
