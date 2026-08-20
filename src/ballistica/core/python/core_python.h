// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_
#define BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_

#include <condition_variable>
#include <list>
#include <mutex>
#include <string>
#include <tuple>
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
  /// CoreConfig::expect_log_handler_setup is false, queued logs are
  /// replayed and async delivery begins immediately. If true, dispatch
  /// stays deferred and logs continue to queue until
  /// OnLogHandlerReady() is invoked.
  void EnablePythonLoggingCalls();

  /// Called once any intended LogHandler setup is complete (or has been
  /// explicitly declined), typically right after baenv.configure()
  /// returns. Replays any queued logs to Python with their original
  /// timestamps preserved and begins async delivery. Safe to call more
  /// than once; only the first call does work.
  void OnLogHandlerReady();

  /// Emit any queued held logs directly to stderr and the platform
  /// log without going through Python. Used as a last-resort drain on
  /// abnormal paths (FatalError, etc.) so nothing is silently lost.
  void DrainHeldLogsToStderr();

  /// Ship a log message to Python's logging system (logging.error,
  /// logging.warning, etc.). Can be called from any thread at any time
  /// and never blocks on the GIL: delivery is asynchronous. The message
  /// plus its wall-clock time is queued here (a brief leaf-mutex
  /// append) and a dedicated thread ships queued messages to Python
  /// with their original timestamps preserved, generally within a few
  /// milliseconds. This makes logging safe even under leaf locks such
  /// as Asset locks where blocking on the GIL is forbidden (see the
  /// lock-ordering invariant on Asset::Lock). Messages logged before
  /// Python-side delivery is possible simply accumulate (they replay at
  /// enable time); messages logged after interpreter shutdown fall back
  /// to stderr.
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
  // A queued log call: (logname, loglevel, message, wall-clock
  // seconds-since-epoch captured at log time). The capture time rides
  // along so original timing is reconstructed when the entry is
  // replayed into Python's logging system (see emit_held_log in the
  // pyembed env code).
  using HeldLogEntry_ = std::tuple<LogName, LogLevel, std::string, double>;

  // Flips python_logging_calls_enabled_ true, replays any logs queued
  // so far via the emit_held_log pyembed helper (preserving captured
  // timestamps), and spins up the async delivery thread for everything
  // after. GIL must be held by the caller.
  void BeginPythonLogDelivery_();

  // Deliver a single held log entry to Python's logging system with
  // its captured timestamp. GIL must be held by the caller.
  void EmitHeldLog_(const HeldLogEntry_& entry);

  // Main loop for the async log-delivery thread: waits for queued
  // entries and ships them to Python in batches.
  void LogDeliveryThreadMain_();

  // Park async delivery just before interpreter finalization: delivers
  // anything still queued (caller must hold the GIL) and flips
  // held_log_delivery_parked_ so subsequent log calls fall back to
  // stderr instead of touching Python.
  void ShutdownLogDelivery_();

  PythonObjectSet<ObjID> objs_;

  bool monolithic_init_complete_{};
  bool python_logging_calls_enabled_{};
  bool finalize_called_{};

  // All C++-originated log calls are queued here (under
  // held_log_lock_) and delivered to Python asynchronously: before
  // BeginPythonLogDelivery_ they simply accumulate (to be replayed once
  // Python logging is up), and after it a dedicated delivery thread
  // (woken via held_log_cv_) ships them within milliseconds. This keeps
  // LoggingCall callable from any context - it never blocks on the GIL.
  std::mutex held_log_lock_;
  std::condition_variable held_log_cv_;
  std::list<HeldLogEntry_> held_logs_;
  bool held_log_delivery_started_{};  // Guarded by held_log_lock_.
  bool held_log_delivery_parked_{};   // Guarded by held_log_lock_.
};

}  // namespace ballistica::core

#endif  // BALLISTICA_CORE_PYTHON_CORE_PYTHON_H_
