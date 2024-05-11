// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/platform/base_platform.h"

#include <csignal>

#if !BA_OSTYPE_WINDOWS
#include <fcntl.h>
#include <poll.h>
#endif

#include "ballistica/base/base.h"
#include "ballistica/base/input/input.h"
#include "ballistica/base/logic/logic.h"
#include "ballistica/base/python/base_python.h"
#include "ballistica/base/ui/ui.h"
#include "ballistica/core/core.h"
#include "ballistica/core/platform/core_platform.h"
#include "ballistica/shared/foundation/event_loop.h"
#include "ballistica/shared/python/python.h"
#include "ballistica/shared/python/python_sys.h"

namespace ballistica::base {

BasePlatform::BasePlatform() = default;

void BasePlatform::PostInit() {
  // Make sure any overrides remember to call us.
  ran_base_post_init_ = true;
}

BasePlatform::~BasePlatform() = default;

void BasePlatform::LoginAdapterGetSignInToken(const std::string& login_type,
                                              int attempt_id) {
  // Default implementation simply calls completion callback immediately.
  g_base->logic->event_loop()->PushCall([login_type, attempt_id] {
    PythonRef args(Py_BuildValue("(sss)", login_type.c_str(),
                                 std::to_string(attempt_id).c_str(), ""),
                   PythonRef::kSteal);
    g_base->python->objs()
        .Get(BasePython::ObjID::kLoginAdapterGetSignInTokenResponseCall)
        .Call(args);
  });
}

void BasePlatform::LoginAdapterBackEndActiveChange(
    const std::string& login_type, bool active) {
  // Default is no-op.
}

auto BasePlatform::GetPublicDeviceUUID() -> std::string {
  assert(g_core);

  if (public_device_uuid_.empty()) {
    std::list<std::string> inputs{g_core->platform->GetDeviceUUIDInputs()};

    // This UUID is supposed to change periodically, so let's plug in
    // some stuff to enforce that.
    inputs.emplace_back(g_core->platform->GetOSVersionString());

    // This part gets shuffled periodically by my version-increment tools.
    // We used to plug version in directly here, but that caused uuids to
    // shuffle too rapidly during periods of rapid development. This
    // keeps it more constant.
    // __last_rand_uuid_component_shuffle_date__ 2023 12 13
    auto rand_uuid_component{"7YM96RZHN6ZCPZGTQONULZO1JU5NMMC7"};

    inputs.emplace_back(rand_uuid_component);
    auto gil{Python::ScopedInterpreterLock()};
    auto pylist{Python::StringList(inputs)};
    auto args{Python::SingleMemberTuple(pylist)};
    auto result = g_base->python->objs()
                      .Get(base::BasePython::ObjID::kHashStringsCall)
                      .Call(args);
    assert(result.UnicodeCheck());
    public_device_uuid_ = result.Str();
  }
  return public_device_uuid_;
}

void BasePlatform::Purchase(const std::string& item) {
  // We use alternate _c ids for consumables in some cases where
  // we originally used entitlements. We are all consumables now though
  // so we can purchase for different accounts.
  std::string item_filtered{item};
  if (g_buildconfig.amazon_build()) {
    if (item == "bundle_bones" || item == "bundle_bernard"
        || item == "bundle_frosty" || item == "bundle_santa" || item == "pro"
        || item == "pro_sale") {
      item_filtered = item + "_c";
    }
  }
  DoPurchase(item_filtered);
}

void BasePlatform::DoPurchase(const std::string& item) {
  // Just print 'unavailable' by default.
  g_base->python->objs().PushCall(
      base::BasePython::ObjID::kUnavailableMessageCall);
}

void BasePlatform::RestorePurchases() {
  Log(LogLevel::kError, "RestorePurchases() unimplemented");
}

void BasePlatform::PurchaseAck(const std::string& purchase,
                               const std::string& order_id) {
  Log(LogLevel::kError, "PurchaseAck() unimplemented");
}

void BasePlatform::OpenURL(const std::string& url) {
  // DoOpenURL expects to be run in the logic thread.
  g_base->logic->event_loop()->PushCall(
      [url] { g_base->platform->DoOpenURL(url); });
}

void BasePlatform::DoOpenURL(const std::string& url) {
  // As a default, use Python's webbrowser module functionality.
  g_base->python->OpenURLWithWebBrowserModule(url);
}

auto BasePlatform::HaveOverlayWebBrowser() -> bool { return false; }

void BasePlatform::OpenURLInOverlayWebBrowser(const std::string& url) {
  BA_PRECONDITION(HaveOverlayWebBrowser());

  // DoOpenURLInOverlayBrowser expects to be run in the logic thread.
  g_base->logic->event_loop()->PushCall(
      [url] { g_base->platform->DoOpenURLInOverlayBrowser(url); });
}

void BasePlatform::CloseOverlayWebBrowser() {
  BA_PRECONDITION(HaveOverlayWebBrowser());

  // DoCloseOverlayBrowser expects to be run in the logic thread.
  g_base->logic->event_loop()->PushCall(
      [] { g_base->platform->DoCloseOverlayBrowser(); });
}

void BasePlatform::DoOpenURLInOverlayBrowser(const std::string& url) {
  // As a default, use Python's webbrowser module functionality.
  Log(LogLevel::kError, "DoOpenURLInOverlayBrowser unimplemented");
}

void BasePlatform::DoCloseOverlayBrowser() {
  // As a default, use Python's webbrowser module functionality.
  Log(LogLevel::kError, "DoCloseOverlayBrowser unimplemented");
}

#if !BA_OSTYPE_WINDOWS
static void HandleSIGINT(int s) {
  if (g_base && g_base->logic->event_loop()) {
    g_base->logic->event_loop()->PushCall(
        [] { g_base->logic->HandleInterruptSignal(); });
  } else {
    Log(LogLevel::kError,
        "SigInt handler called before g_base->logic->event_loop exists.");
  }
}
static void HandleSIGTERM(int s) {
  if (g_base && g_base->logic->event_loop()) {
    g_base->logic->event_loop()->PushCall(
        [] { g_base->logic->HandleTerminateSignal(); });
  } else {
    Log(LogLevel::kError,
        "SigInt handler called before g_base->logic->event_loop exists.");
  }
}
#endif

void BasePlatform::SetupInterruptHandling() {
// This default implementation covers non-windows platforms.
#if BA_OSTYPE_WINDOWS
  throw Exception();
#else
  {
    struct sigaction handler {};
    handler.sa_handler = HandleSIGINT;
    sigemptyset(&handler.sa_mask);
    handler.sa_flags = 0;
    sigaction(SIGINT, &handler, nullptr);
  }
  {
    struct sigaction handler {};
    handler.sa_handler = HandleSIGTERM;
    sigemptyset(&handler.sa_mask);
    handler.sa_flags = 0;
    sigaction(SIGTERM, &handler, nullptr);
  }
#endif
}

void BasePlatform::OnAppStart() { assert(g_base->InLogicThread()); }
void BasePlatform::OnAppSuspend() { assert(g_base->InLogicThread()); }
void BasePlatform::OnAppUnsuspend() { assert(g_base->InLogicThread()); }
void BasePlatform::OnAppShutdown() { assert(g_base->InLogicThread()); }
void BasePlatform::OnAppShutdownComplete() { assert(g_base->InLogicThread()); }
void BasePlatform::OnScreenSizeChange() { assert(g_base->InLogicThread()); }
void BasePlatform::DoApplyAppConfig() { assert(g_base->InLogicThread()); }

auto BasePlatform::HaveStringEditor() -> bool { return false; }

void BasePlatform::InvokeStringEditor(PyObject* string_edit_adapter) {
  BA_PRECONDITION(HaveStringEditor());
  BA_PRECONDITION(g_base->InLogicThread());

  // We assume there's a single one of these at a time. Hold on to it.
  string_edit_adapter_.Acquire(string_edit_adapter);

  // Pull values from Python and ship them along to our platform
  // implementation.
  auto desc = string_edit_adapter_.GetAttr("description").ValueAsString();
  auto initial_text =
      string_edit_adapter_.GetAttr("initial_text").ValueAsString();
  auto max_length =
      string_edit_adapter_.GetAttr("max_length").ValueAsOptionalInt();
  // TODO(ericf): pass along screen_space_center if its ever useful.

  g_base->platform->DoInvokeStringEditor(desc, initial_text, max_length);
}

/// Should be called by platform StringEditor to apply a value.
void BasePlatform::StringEditorApply(const std::string& val) {
  BA_PRECONDITION(HaveStringEditor());
  BA_PRECONDITION(g_base->InLogicThread());
  BA_PRECONDITION(string_edit_adapter_.Exists());
  auto args = PythonRef::Stolen(Py_BuildValue("(s)", val.c_str()));
  string_edit_adapter_.GetAttr("apply").Call(args);
  string_edit_adapter_.Release();
}

/// Should be called by platform StringEditor to signify a cancel.
void BasePlatform::StringEditorCancel() {
  BA_PRECONDITION(HaveStringEditor());
  BA_PRECONDITION(g_base->InLogicThread());
  BA_PRECONDITION(string_edit_adapter_.Exists());
  string_edit_adapter_.GetAttr("cancel").Call();
  string_edit_adapter_.Release();
}

void BasePlatform::DoInvokeStringEditor(const std::string& title,
                                        const std::string& value,
                                        std::optional<int> max_chars) {
  Log(LogLevel::kError, "FIXME: DoInvokeStringEditor() unimplemented");
}

auto BasePlatform::SupportsOpenDirExternally() -> bool { return false; }

void BasePlatform::OpenDirExternally(const std::string& path) {
  Log(LogLevel::kError, "OpenDirExternally() unimplemented");
}

void BasePlatform::OpenFileExternally(const std::string& path) {
  Log(LogLevel::kError, "OpenFileExternally() unimplemented");
}

void BasePlatform::SafeStdinFGetSInit() {
#if BA_OSTYPE_WINDOWS
  // Do nothing on Windows. We seem to be ok with blocking reads there.
#else

  // Actually should not be necessary now that we're using poll().

  // Set stdin up for non-blocking reads.
  // int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
  // fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);
#endif  // BA_OSTYPE_WINDOWS
}

auto BasePlatform::SafeStdinFGetS(char* s, int n, FILE* iop) -> char* {
#if BA_OSTYPE_WINDOWS
  // Use plain old vanilla fgets on Windows since blocking stdin reads
  // don't seem to prevent the app from exiting there.
  return fgets(s, n, iop);

#else

  // On unixy platforms, plug in a vanilla fgets() implementation (see
  // https://stackoverflow.com/questions/16397832/fgets-implementation-kr)
  // but replace the getc() with a custom version of our own that uses
  // poll() to periodically check if we should bail while waiting for input.
  int c{};
  char* cs{};
  cs = s;

  while (--n > 0 && (c = SmartGetC_(iop)) != EOF) {
    if ((*cs++ = c) == '\n') {
      break;
    }
  }

  *cs = '\0';
  return (c == EOF && cs == s) ? NULL : s;
#endif  // BA_OSTYPE_WINDOWS
}

int BasePlatform::SmartGetC_(FILE* stream) {
#if BA_OSTYPE_WINDOWS
  return -1;
#else
  // Refill our buffer if needed.
  while (stdin_buffer_.empty()) {
    struct pollfd fds[1];

    // Initialize the pollfd structure for stdin
    fds[0].fd = STDIN_FILENO;
    fds[0].events = POLLIN;

    // Let's break approximately 4 times per second to see if we should
    // bail.
    int ret = poll(fds, 1, 287);

    if (ret == 0) {
      // Poll timed out. Check whether we should bail and then do it again.

      // If the app is working on gracefully shutting down OR the engine has
      // died (from a fatal error or whatever else), fake an EOF.
      if (g_base->logic->shutting_down() || g_core->engine_done()) {
        return EOF;
      }

      continue;
    }
    if (ret == -1) {
      // Error in poll
      perror("poll");
      return EOF;
    }

    if (fds[0].revents & POLLIN) {
      // stdin is ready for reading.
      char buffer[256];

      // Read characters from stdin
      ssize_t bytes_read = read(STDIN_FILENO, buffer, sizeof(buffer));

      if (bytes_read == -1) {
        // Error reading from stdin
        perror("read");
        return EOF;
      }

      for (int i = 0; i < bytes_read; ++i) {
        stdin_buffer_.push_back(buffer[i]);
      }
    }
  }
  auto out = stdin_buffer_.front();
  stdin_buffer_.pop_front();
  return out;
#endif  // BA_OSTYPE_WINDOWS
}

}  // namespace ballistica::base
