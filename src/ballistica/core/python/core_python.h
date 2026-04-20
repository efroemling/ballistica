// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_
#define BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_

#include <list>
#include <mutex>
#include <string>
#include <vector>

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
    kLoggingLevelNotSet,
    kLoggingLevelDebug,
    kLoggingLevelInfo,
    kLoggingLevelWarning,
    kLoggingLevelError,
    kLoggingLevelCritical,
    kLoggerRoot,
    kLoggerRootLogCall,
    kLoggerBa,
    kLoggerBaLogCall,
    kLoggerBaAccount,
    kLoggerBaAccountLogCall,
    kLoggerBaApp,
    kLoggerBaAppLogCall,
    kLoggerBaAudio,
    kLoggerBaAudioLogCall,
    kLoggerBaDisplayTime,
    kLoggerBaDisplayTimeLogCall,
    kLoggerBaGraphics,
    kLoggerBaGraphicsLogCall,
    kLoggerBaPerformance,
    kLoggerBaPerformanceLogCall,
    kLoggerBaLifecycle,
    kLoggerBaLifecycleLogCall,
    kLoggerBaAssets,
    kLoggerBaAssetsLogCall,
    kLoggerBaInput,
    kLoggerBaInputLogCall,
    kLoggerBaUI,
    kLoggerBaUILogCall,
    kLoggerBaNetworking,
    kLoggerBaNetworkingLogCall,
    kLoggerBaDiscord,
    kLoggerBaDiscordLogCall,
    kPrependSysPathCall,
    kWarmStart1Call,
    kWarmStart1CompletedCall,
    kBaEnvConfigureCall,
    kBaEnvGetConfigCall,
    kBaEnvAtExitCall,
    kBaEnvPreFinalizeCall,
    kEmitHeldLogCall,
    kUUIDStrCall,
    kLast  // Sentinel; must be at end.
  };

  /// Bring up Python itself. Only applicable to monolithic builds.
  void InitPython();

  /// Finalize Python itself. Only applicable to monolithic builds. This
  /// will block waiting for all remaining (non-daemon) Python threads to
  /// join. Any further Python use must be avoided after calling this.
  void FinalizePython();

  /// Run baenv.configure() with all of our monolithic-mode paths/etc.
  void MonolithicModeBaEnvImport();
  void MonolithicModeBaEnvConfigure();

  /// Enables Python-side log dispatch. If
  /// CoreConfig::expect_log_handler_setup is false, any buffered early
  /// logs are flushed immediately. If true, dispatch stays deferred and
  /// logs continue to buffer until OnLogHandlerReady() is invoked.
  void EnablePythonLoggingCalls();

  /// Called once any intended LogHandler setup is complete (or has been
  /// explicitly declined), typically right after baenv.configure()
  /// returns. Flushes any buffered early logs to Python with their
  /// original timestamps preserved. Safe to call more than once; only
  /// the first call does work.
  void OnLogHandlerReady();

  /// Emit any buffered early logs directly to stderr and the platform
  /// log without going through Python. Used as a last-resort drain on
  /// abnormal paths (FatalError, etc.) so nothing is silently lost.
  void DrainEarlyLogsToStderr();

  /// Calls Python logging function (logging.error, logging.warning, etc.)
  /// Can be called from any thread at any time. If called before Python
  /// logging is available, logs locally using Logging::EmitPlatformLog()
  /// (with an added warning).
  void LoggingCall(LogName logname, LogLevel loglevel, const char* msg);
  void ImportPythonObjs();
  void VerifyPythonEnvironment();
  void SoftImportBase();
  void UpdateInternalLoggerLevels(LogLevel* log_levels);
  void AtExit(PyObject*);

  static auto WasModularMainCalled() -> bool;

  /// Builds a vector of strings out of Python's sys.argv. Returns an argv
  /// array pointing to them.
  static auto FetchPythonArgs(std::vector<std::string>* buffer)
      -> std::vector<char*>;

  const auto& objs() { return objs_; }

  void WarmStart1();
  auto WarmStart1Completed() -> bool;

 private:
  // Internal helper: flips python_logging_calls_enabled_ true and
  // replays any buffered early logs via the emit_held_log pyembed
  // helper, preserving their captured timestamps. GIL must be held by
  // the caller.
  void FlushEarlyLogs_();

  PythonObjectSet<ObjID> objs_;

  bool monolithic_init_complete_{};
  bool python_logging_calls_enabled_{};
  bool finalize_called_{};

  // Log calls we make before we're set up to ship logs through Python
  // go here. They all get shipped at once as soon as it is possible.
  // The trailing double is the wall-clock seconds-since-epoch captured
  // at log time so that the original timing can be reconstructed when
  // these get replayed into Python's logging system.
  std::mutex early_log_lock_;
  std::list<std::tuple<LogName, LogLevel, std::string, double>> early_logs_;
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_
