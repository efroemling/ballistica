// Released under the MIT License. See LICENSE for details.

#include "ballistica/base/networking/nearby_services.h"

#include <map>
#include <memory>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "ballistica/shared/ballistica.h"

#if BA_PLATFORM_MACOS || BA_PLATFORM_IOS_TVOS
#define BA_NEARBY_SERVICES_DNS_SD 1
#else
#define BA_NEARBY_SERVICES_DNS_SD 0
#endif

#include <mutex>

#include "ballistica/base/base.h"
#include "ballistica/core/core.h"
#include "ballistica/core/logging/logging.h"
#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/core/platform/platform.h"
#include "ballistica/shared/generic/utils.h"

#if BA_NEARBY_SERVICES_DNS_SD
#include <arpa/inet.h>
#include <dns_sd.h>
#include <net/if.h>
#include <netinet/in.h>
#include <poll.h>
#endif

#if BA_PLATFORM_ANDROID
#include <fcntl.h>
#include <unistd.h>

#include "ballistica/base/platform/android/android_message_bus.h"
#endif

#if BA_PLATFORM_WINDOWS
// (need includes to stay in this order to disabling formatting)
// clang-format off
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <windns.h>
// clang-format on

#include "ballistica/core/platform/windows/platform_windows.h"

#pragma comment(lib, "dnsapi.lib")
#endif

namespace ballistica::base {

const char* const kNearbyGameServiceType = "_bagame._udp";
const char* const kNearbyRemoteServiceType = "_baremote._udp";

namespace {

/// The instance name we advertise under: a single DNS label (63 bytes
/// max). Collisions get renamed by the OS ('Name (2)'), so two of us
/// on one device both get listed.
[[maybe_unused]] auto AdvertisedName() -> std::string {
  std::string name = g_core->platform->GetDeviceName();
  if (name.size() > 63) {
    name.resize(63);
    name = Utils::GetValidUTF8(name.c_str(), "nsdn");
  }
  if (name.empty()) {
    name = "BallisticaKit";
  }
  return name;
}

/// Our TXT record: format version, app-instance-uuid (so browsers can
/// skip themselves), and engine build.
[[maybe_unused]] auto AdvertisedTXT()
    -> std::vector<std::pair<std::string, std::string>> {
  return {{"v", "1"},
          {"i", g_base->LocalAppInstanceUUID()},
          {"b", std::to_string(kEngineBuildNumber)}};
}

}  // namespace

NearbyServices::~NearbyServices() = default;

void NearbyServices::SetAdvertised(int port, bool game, bool remote) {}

auto NearbyServices::BrowseSupported() -> bool { return false; }

auto NearbyServices::StartBrowse(const std::vector<std::string>& service_types)
    -> int {
  return -1;
}

auto NearbyServices::ProcessBrowse() -> std::vector<NearbyServiceEvent> {
  return {};
}

void NearbyServices::StopBrowse() {}

void NearbyServices::PushPlatformEvent(NearbyServiceEvent event) {}

#if BA_NEARBY_SERVICES_DNS_SD

namespace {

// Service types come back from the daemon with a trailing dot.
auto TrimDot(const char* s) -> std::string {
  std::string out{s ? s : ""};
  if (!out.empty() && out.back() == '.') {
    out.pop_back();
  }
  return out;
}

auto ParseTXT(uint16_t len, const unsigned char* bytes)
    -> std::vector<std::pair<std::string, std::string>> {
  std::vector<std::pair<std::string, std::string>> out;
  uint16_t count = TXTRecordGetCount(len, bytes);
  for (uint16_t i = 0; i < count; ++i) {
    char key[256];
    uint8_t value_len{};
    const void* value{};
    if (TXTRecordGetItemAtIndex(len, bytes, i, sizeof(key), key, &value_len,
                                &value)
        == kDNSServiceErr_NoError) {
      out.emplace_back(
          key, value ? std::string(static_cast<const char*>(value), value_len)
                     : std::string());
    }
  }
  return out;
}

/// DNS-SD via Apple's dns_sd API (mDNSResponder).
///
/// Browsing shares one daemon connection between all its operations, so
/// a single descriptor covers everything and all callbacks fire inside
/// ProcessBrowse() on the calling thread.
class NearbyServicesDNSSD : public NearbyServices {
 public:
  void SetAdvertised(int port, bool game, bool remote) override {
    std::scoped_lock lock(advertise_mutex_);
    UpdateRegistration_(&game_reg_, game ? port : 0, kNearbyGameServiceType);
    UpdateRegistration_(&remote_reg_, remote ? port : 0,
                        kNearbyRemoteServiceType);
  }

  auto BrowseSupported() -> bool override { return true; }

  auto StartBrowse(const std::vector<std::string>& service_types)
      -> int override {
    StopBrowse();
    auto err = DNSServiceCreateConnection(&conn_);
    if (err != kDNSServiceErr_NoError) {
      conn_ = nullptr;
      BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                  "Unable to reach the DNS-SD daemon (error "
                      + std::to_string(err) + "); browsing disabled.");
      return -1;
    }
    for (auto&& service_type : service_types) {
      DNSServiceRef ref{conn_};
      err = DNSServiceBrowse(&ref, kDNSServiceFlagsShareConnection,
                             kDNSServiceInterfaceIndexAny, service_type.c_str(),
                             nullptr, BrowseReply_, this);
      if (err != kDNSServiceErr_NoError) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kWarning,
                             "DNS-SD browse for " + service_type
                                 + " failed (error " + std::to_string(err)
                                 + ").");
        continue;
      }
      browse_refs_.push_back(ref);
    }
    return DNSServiceRefSockFD(conn_);
  }

  auto ProcessBrowse() -> std::vector<NearbyServiceEvent> override {
    if (conn_ == nullptr) {
      return {};
    }
    int fd = DNSServiceRefSockFD(conn_);

    // Each call handles one reply; keep going while more are waiting.
    for (int i = 0; i < 64; ++i) {
      auto err = DNSServiceProcessResult(conn_);
      if (err != kDNSServiceErr_NoError) {
        StopBrowse();
        throw Exception("DNS-SD connection failed (error " + std::to_string(err)
                        + ").");
      }
      pollfd pfd{fd, POLLIN, 0};
      if (poll(&pfd, 1, 0) <= 0 || !(pfd.revents & POLLIN)) {
        break;
      }
    }
    std::vector<NearbyServiceEvent> out;
    out.swap(events_);
    return out;
  }

  void StopBrowse() override {
    if (conn_ == nullptr) {
      return;
    }
    // Subordinate refs go before the connection they share.
    for (auto&& i : instances_) {
      DeallocateInstanceRefs_(i.second.get());
    }
    instances_.clear();
    for (auto&& ref : browse_refs_) {
      DNSServiceRefDeallocate(ref);
    }
    browse_refs_.clear();
    DNSServiceRefDeallocate(conn_);
    conn_ = nullptr;
    events_.clear();
  }

 private:
  struct Instance_ {
    NearbyServicesDNSSD* owner{};
    std::string key;
    std::string service_type;
    std::string name;
    uint32_t interface_index{};
    DNSServiceRef resolve_ref{};
    DNSServiceRef addr_ref{};
    std::string host_target;
    int port{};
    std::vector<std::pair<std::string, std::string>> txt;
    std::set<std::string> addresses;
  };

  void UpdateRegistration_(DNSServiceRef* ref, int port, const char* type) {
    int* current = (ref == &game_reg_) ? &game_port_ : &remote_port_;
    if (*current == port) {
      return;
    }
    if (*ref != nullptr) {
      DNSServiceRefDeallocate(*ref);
      *ref = nullptr;
    }
    *current = 0;
    if (port <= 0) {
      return;
    }
    TXTRecordRef txt;
    TXTRecordCreate(&txt, 0, nullptr);
    for (auto&& [key, value] : AdvertisedTXT()) {
      TXTRecordSetValue(&txt, key.c_str(), static_cast<uint8_t>(value.size()),
                        value.c_str());
    }
    std::string name = AdvertisedName();

    // No callback; we don't need to hear how it goes (a renamed or
    // failed registration just means fewer finds).
    auto err = DNSServiceRegister(
        ref, 0, kDNSServiceInterfaceIndexAny, name.c_str(), type, nullptr,
        nullptr, htons(static_cast<uint16_t>(port)), TXTRecordGetLength(&txt),
        TXTRecordGetBytesPtr(&txt), nullptr, nullptr);
    TXTRecordDeallocate(&txt);
    if (err != kDNSServiceErr_NoError) {
      *ref = nullptr;
      BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                  std::string("DNS-SD registration of ") + type
                      + " failed (error " + std::to_string(err) + ").");
      return;
    }
    *current = port;
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [=] {
      return std::string("Advertising ") + type + " on port "
             + std::to_string(port) + ".";
    });
  }

  static void DNSSD_API BrowseReply_(DNSServiceRef ref, DNSServiceFlags flags,
                                     uint32_t interface_index,
                                     DNSServiceErrorType err, const char* name,
                                     const char* regtype, const char* domain,
                                     void* context) {
    auto* self = static_cast<NearbyServicesDNSSD*>(context);
    if (err != kDNSServiceErr_NoError || name == nullptr) {
      return;
    }
    std::string service_type = TrimDot(regtype);
    std::string key =
        service_type + "|" + name + "|" + std::to_string(interface_index);

    if (!(flags & kDNSServiceFlagsAdd)) {
      auto i = self->instances_.find(key);
      if (i != self->instances_.end()) {
        self->DeallocateInstanceRefs_(i->second.get());
        self->instances_.erase(i);
      }
      NearbyServiceEvent event;
      event.added = false;
      event.service_type = service_type;
      event.instance = key;
      event.name = name;
      self->events_.push_back(std::move(event));
      return;
    }
    if (self->instances_.count(key)) {
      return;
    }
    auto instance = std::make_unique<Instance_>();
    instance->owner = self;
    instance->key = key;
    instance->service_type = service_type;
    instance->name = name;
    instance->interface_index = interface_index;
    instance->resolve_ref = self->conn_;
    auto rerr = DNSServiceResolve(
        &instance->resolve_ref, kDNSServiceFlagsShareConnection,
        interface_index, name, regtype, domain, ResolveReply_, instance.get());
    if (rerr != kDNSServiceErr_NoError) {
      instance->resolve_ref = nullptr;
      return;
    }
    self->instances_[key] = std::move(instance);
  }

  static void DNSSD_API ResolveReply_(
      DNSServiceRef ref, DNSServiceFlags flags, uint32_t interface_index,
      DNSServiceErrorType err, const char* fullname, const char* host_target,
      uint16_t port, uint16_t txt_len, const unsigned char* txt_record,
      void* context) {
    auto* instance = static_cast<Instance_*>(context);
    if (err != kDNSServiceErr_NoError || host_target == nullptr) {
      return;
    }
    auto* self = instance->owner;
    instance->port = ntohs(port);
    instance->txt = ParseTXT(txt_len, txt_record);

    if (instance->addr_ref == nullptr || instance->host_target != host_target) {
      if (instance->addr_ref != nullptr) {
        DNSServiceRefDeallocate(instance->addr_ref);
        instance->addr_ref = nullptr;
      }
      instance->addresses.clear();
      instance->host_target = host_target;
      instance->addr_ref = self->conn_;
      auto aerr = DNSServiceGetAddrInfo(
          &instance->addr_ref, kDNSServiceFlagsShareConnection,
          instance->interface_index,
          kDNSServiceProtocol_IPv4 | kDNSServiceProtocol_IPv6, host_target,
          AddrReply_, instance);
      if (aerr != kDNSServiceErr_NoError) {
        instance->addr_ref = nullptr;
      }
    } else {
      // Same host; port/txt may have changed, so re-report addresses.
      for (auto&& addr : instance->addresses) {
        self->PushAdd_(*instance, addr);
      }
    }
  }

  static void DNSSD_API AddrReply_(DNSServiceRef ref, DNSServiceFlags flags,
                                   uint32_t interface_index,
                                   DNSServiceErrorType err,
                                   const char* hostname,
                                   const struct sockaddr* address, uint32_t ttl,
                                   void* context) {
    auto* instance = static_cast<Instance_*>(context);
    if (err != kDNSServiceErr_NoError || address == nullptr) {
      return;
    }
    char buffer[INET6_ADDRSTRLEN];
    std::string addr;
    if (address->sa_family == AF_INET) {
      if (!inet_ntop(AF_INET,
                     &(reinterpret_cast<const sockaddr_in*>(address)->sin_addr),
                     buffer, sizeof(buffer))) {
        return;
      }
      addr = buffer;
    } else if (address->sa_family == AF_INET6) {
      auto* addr6 = reinterpret_cast<const sockaddr_in6*>(address);
      if (!inet_ntop(AF_INET6, &addr6->sin6_addr, buffer, sizeof(buffer))) {
        return;
      }
      addr = buffer;
      // Link-local addresses only mean something on one interface, so
      // carry it along ('fe80::1%en0').
      if (IN6_IS_ADDR_LINKLOCAL(&addr6->sin6_addr)) {
        char ifname[IF_NAMESIZE];
        if (if_indextoname(interface_index, ifname) == nullptr) {
          return;
        }
        addr += std::string("%") + ifname;
      }
    } else {
      return;
    }
    if (flags & kDNSServiceFlagsAdd) {
      instance->addresses.insert(addr);
      instance->owner->PushAdd_(*instance, addr);
    } else {
      // An address going away just stops being re-reported; the prober
      // notices it going quiet.
      instance->addresses.erase(addr);
    }
  }

  void PushAdd_(const Instance_& instance, const std::string& addr) {
    NearbyServiceEvent event;
    event.added = true;
    event.service_type = instance.service_type;
    event.instance = instance.key;
    event.name = instance.name;
    event.address = addr;
    event.port = instance.port;
    event.txt = instance.txt;
    events_.push_back(std::move(event));
  }

  void DeallocateInstanceRefs_(Instance_* instance) {
    if (instance->addr_ref != nullptr) {
      DNSServiceRefDeallocate(instance->addr_ref);
      instance->addr_ref = nullptr;
    }
    if (instance->resolve_ref != nullptr) {
      DNSServiceRefDeallocate(instance->resolve_ref);
      instance->resolve_ref = nullptr;
    }
  }

  // Advertising (any thread; under advertise_mutex_).
  std::mutex advertise_mutex_;
  DNSServiceRef game_reg_{};
  DNSServiceRef remote_reg_{};
  int game_port_{};
  int remote_port_{};

  // Browsing (one thread at a time).
  DNSServiceRef conn_{};
  std::vector<DNSServiceRef> browse_refs_;
  std::map<std::string, std::unique_ptr<Instance_>> instances_;
  std::vector<NearbyServiceEvent> events_;
};

}  // namespace

#endif  // BA_NEARBY_SERVICES_DNS_SD

#if BA_PLATFORM_ANDROID

namespace {

/// DNS-SD via Android's NsdManager (Java side: BallisticaContext).
///
/// NsdManager reports results on its own threads; they queue here and a
/// byte written to a pipe makes the browse descriptor readable.
class NearbyServicesAndroid : public NearbyServices {
 public:
  // Locking note: Java calls PushPlatformEvent() while holding its own
  // lock, so we must never call into Java while holding events_mutex_
  // (that would deadlock against a browse() call). Advertising has its
  // own mutex, which Java never touches.

  void SetAdvertised(int port, bool game, bool remote) override {
    std::scoped_lock lock(advertise_mutex_);
    UpdateAdvertisement_(kNearbyGameServiceType, &game_port_, game ? port : 0);
    UpdateAdvertisement_(kNearbyRemoteServiceType, &remote_port_,
                         remote ? port : 0);
  }

  auto BrowseSupported() -> bool override { return true; }

  auto StartBrowse(const std::vector<std::string>& service_types)
      -> int override {
    int fd{};
    {
      std::scoped_lock lock(events_mutex_);
      if (pipe_read_ == -1) {
        int fds[2];
        if (pipe2(fds, O_NONBLOCK | O_CLOEXEC) != 0) {
          return -1;
        }
        pipe_read_ = fds[0];
        pipe_write_ = fds[1];
      }
      events_.clear();
      browsing_ = true;
      fd = pipe_read_;
    }
    GetAndroidMessageSender()->SendNearbyBrowse(service_types);
    return fd;
  }

  auto ProcessBrowse() -> std::vector<NearbyServiceEvent> override {
    std::scoped_lock lock(events_mutex_);
    char buffer[256];
    while (pipe_read_ != -1 && read(pipe_read_, buffer, sizeof(buffer)) > 0) {
    }
    std::vector<NearbyServiceEvent> out;
    out.swap(events_);
    return out;
  }

  void StopBrowse() override {
    {
      std::scoped_lock lock(events_mutex_);
      if (!browsing_) {
        return;
      }
      browsing_ = false;
      events_.clear();
    }
    GetAndroidMessageSender()->SendNearbyBrowse({});
  }

  void PushPlatformEvent(NearbyServiceEvent event) override {
    std::scoped_lock lock(events_mutex_);
    // (Stragglers from a stopped browse are dropped.)
    if (!browsing_) {
      return;
    }
    events_.push_back(std::move(event));
    char byte{};
    // A full pipe just means a wakeup is already pending.
    [[maybe_unused]] auto result = write(pipe_write_, &byte, 1);
  }

 private:
  void UpdateAdvertisement_(const char* type, int* current, int port) {
    if (*current == port) {
      return;
    }
    *current = port;
    std::vector<std::string> keys;
    std::vector<std::string> values;
    for (auto&& [key, value] : AdvertisedTXT()) {
      keys.push_back(key);
      values.push_back(value);
    }
    GetAndroidMessageSender()->SendNearbyAdvertise(type, port, AdvertisedName(),
                                                   keys, values);
  }

  std::mutex advertise_mutex_;
  int game_port_{};
  int remote_port_{};

  std::mutex events_mutex_;
  bool browsing_{};
  int pipe_read_{-1};
  int pipe_write_{-1};
  std::vector<NearbyServiceEvent> events_;
};

}  // namespace

#endif  // BA_PLATFORM_ANDROID

#if BA_PLATFORM_WINDOWS

namespace {

using core::PlatformWindows;

/// DNS-SD via the Windows DNS client's mDNS support (windns.h;
/// Windows 10 1903+).
///
/// Results arrive on OS thread-pool threads and queue here; there is no
/// descriptor to wait on, so StartBrowse() returns
/// kNearbyBrowseNoDescriptor and the caller polls ProcessBrowse().
///
/// Lifetimes: the OS may call back after a cancel, so every context it
/// holds outlives that. Browse contexts are one per service type and
/// live as long as we do (this singleton is never destroyed); a
/// generation number makes stragglers from an earlier browse harmless.
/// Resolve contexts belong to their single completion callback, which
/// the OS always makes, and which frees them.
class NearbyServicesWindows : public NearbyServices {
 public:
  void SetAdvertised(int port, bool game, bool remote) override {
    std::scoped_lock lock(advertise_mutex_);
    UpdateRegistration_(&game_reg_, game ? port : 0, kNearbyGameServiceType);
    UpdateRegistration_(&remote_reg_, remote ? port : 0,
                        kNearbyRemoteServiceType);
  }

  auto BrowseSupported() -> bool override { return true; }

  auto StartBrowse(const std::vector<std::string>& service_types)
      -> int override {
    StopBrowse();
    std::vector<BrowseContext_*> to_start;
    {
      std::scoped_lock lock(mutex_);
      ++generation_;
      browsing_ = true;
      events_.clear();
      for (auto&& service_type : service_types) {
        auto& ctx = browse_contexts_[service_type];
        if (!ctx) {
          ctx = std::make_unique<BrowseContext_>();
          ctx->owner = this;
          ctx->service_type = service_type;
          ctx->query_name =
              PlatformWindows::UTF8Decode(service_type + ".local");
        }
        ctx->generation = generation_;
        to_start.push_back(ctx.get());
      }
    }
    // (Outside the lock: the OS may call back on another thread before
    // these return.)
    bool any{};
    for (auto* ctx : to_start) {
      DNS_SERVICE_BROWSE_REQUEST request{};
      request.Version = DNS_QUERY_REQUEST_VERSION1;
      request.InterfaceIndex = 0;
      request.QueryName = ctx->query_name.c_str();
      request.pBrowseCallback = BrowseCallback_;
      request.pQueryContext = ctx;
      ctx->cancel = {};
      auto status = DnsServiceBrowse(&request, &ctx->cancel);
      if (status != DNS_REQUEST_PENDING) {
        g_core->logging->Log(LogName::kBaNetworking, LogLevel::kWarning,
                             "DNS-SD browse for " + ctx->service_type
                                 + " failed (error " + std::to_string(status)
                                 + ").");
        continue;
      }
      ctx->active = true;
      any = true;
    }
    if (!any) {
      StopBrowse();
      return -1;
    }
    return kNearbyBrowseNoDescriptor;
  }

  auto ProcessBrowse() -> std::vector<NearbyServiceEvent> override {
    std::scoped_lock lock(mutex_);
    std::vector<NearbyServiceEvent> out;
    out.swap(events_);
    return out;
  }

  void StopBrowse() override {
    std::vector<BrowseContext_*> to_cancel;
    {
      std::scoped_lock lock(mutex_);
      if (!browsing_) {
        return;
      }
      browsing_ = false;
      ++generation_;
      events_.clear();
      resolving_.clear();
      for (auto&& [_, ctx] : browse_contexts_) {
        if (ctx->active) {
          ctx->active = false;
          to_cancel.push_back(ctx.get());
        }
      }
    }
    // (Outside the lock: a cancel can call back synchronously.)
    for (auto* ctx : to_cancel) {
      DnsServiceBrowseCancel(&ctx->cancel);
    }
  }

 private:
  static constexpr millisecs_t kResolveRetryMillisecs{10000};

  struct BrowseContext_ {
    NearbyServicesWindows* owner{};
    std::string service_type;
    std::wstring query_name;
    DNS_SERVICE_CANCEL cancel{};
    uint64_t generation{};
    bool active{};
  };

  struct ResolveContext_ {
    NearbyServicesWindows* owner{};
    uint64_t generation{};
    std::string key;
    std::string service_type;
    std::string name;
    std::wstring query_name;
    DNS_SERVICE_CANCEL cancel{};
  };

  struct Registration_ {
    DNS_SERVICE_INSTANCE* instance{};
    DNS_SERVICE_CANCEL cancel{};
    int port{};
  };

  void UpdateRegistration_(Registration_* reg, int port, const char* type) {
    if (reg->port == port) {
      return;
    }
    if (reg->instance != nullptr) {
      DNS_SERVICE_REGISTER_REQUEST request{};
      request.Version = DNS_QUERY_REQUEST_VERSION1;
      request.pServiceInstance = reg->instance;
      request.pRegisterCompletionCallback = RegisterCallback_;
      // The OS is done with the instance once this returns.
      DnsServiceDeRegister(&request, nullptr);
      DnsServiceFreeInstance(reg->instance);
      reg->instance = nullptr;
    }
    reg->port = 0;
    if (port <= 0) {
      return;
    }
    std::wstring host = HostName_();
    if (host.empty()) {
      BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                  "DNS-SD: unable to get this machine's host name;"
                  " not advertising.");
      return;
    }
    std::wstring service_name =
        PlatformWindows::UTF8Decode(AdvertisedName() + "." + type + ".local");
    std::vector<std::wstring> keys;
    std::vector<std::wstring> values;
    for (auto&& [key, value] : AdvertisedTXT()) {
      keys.push_back(PlatformWindows::UTF8Decode(key));
      values.push_back(PlatformWindows::UTF8Decode(value));
    }
    std::vector<PCWSTR> key_ptrs;
    std::vector<PCWSTR> value_ptrs;
    for (size_t i = 0; i < keys.size(); ++i) {
      key_ptrs.push_back(keys[i].c_str());
      value_ptrs.push_back(values[i].c_str());
    }
    // No addresses given: the OS answers with this machine's own.
    reg->instance = DnsServiceConstructInstance(
        service_name.c_str(), host.c_str(), nullptr, nullptr,
        static_cast<WORD>(port), 0, 0, static_cast<DWORD>(key_ptrs.size()),
        key_ptrs.data(), value_ptrs.data());
    if (reg->instance == nullptr) {
      BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                  std::string("DNS-SD: unable to describe ") + type
                      + "; not advertising.");
      return;
    }
    DNS_SERVICE_REGISTER_REQUEST request{};
    request.Version = DNS_QUERY_REQUEST_VERSION1;
    request.InterfaceIndex = 0;
    request.pServiceInstance = reg->instance;
    request.pRegisterCompletionCallback = RegisterCallback_;
    request.pQueryContext = nullptr;
    request.unicastEnabled = FALSE;
    reg->cancel = {};
    auto status = DnsServiceRegister(&request, &reg->cancel);
    if (status != DNS_REQUEST_PENDING) {
      DnsServiceFreeInstance(reg->instance);
      reg->instance = nullptr;
      BA_LOG_ONCE(LogName::kBaNetworking, LogLevel::kWarning,
                  std::string("DNS-SD registration of ") + type
                      + " failed (error " + std::to_string(status) + ").");
      return;
    }
    reg->port = port;
    g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [=] {
      return std::string("Advertising ") + type + " on port "
             + std::to_string(port) + ".";
    });
  }

  static auto HostName_() -> std::wstring {
    wchar_t buffer[256];
    DWORD size = sizeof(buffer) / sizeof(buffer[0]);
    if (!GetComputerNameExW(ComputerNameDnsHostname, buffer, &size)
        || size == 0) {
      return {};
    }
    return std::wstring(buffer, size) + L".local";
  }

  static void WINAPI RegisterCallback_(DWORD status, PVOID context,
                                       PDNS_SERVICE_INSTANCE instance) {
    // (Ours stays with us; this is the OS's copy.)
    if (instance != nullptr) {
      DnsServiceFreeInstance(instance);
    }
    if (status != ERROR_SUCCESS) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [=] {
        return "DNS-SD registration completed with status "
               + std::to_string(status) + ".";
      });
    }
  }

  static void WINAPI BrowseCallback_(DWORD status, PVOID context,
                                     PDNS_RECORD records) {
    auto* ctx = static_cast<BrowseContext_*>(context);
    if (status != ERROR_SUCCESS && status != ERROR_CANCELLED) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [=] {
        return "DNS-SD browse for " + ctx->service_type + " reported status "
               + std::to_string(status) + ".";
      });
    }
    if (status == ERROR_SUCCESS && records != nullptr) {
      ctx->owner->HandleBrowseRecords_(ctx,
                                       reinterpret_cast<DNS_RECORDW*>(records));
    }
    if (records != nullptr) {
      DnsRecordListFree(records, DnsFreeRecordList);
    }
  }

  /// What a browse answer's extra records say about one instance.
  struct Answer_ {
    int port{};
    std::vector<std::pair<std::string, std::string>> txt;
    std::vector<std::string> addresses;
  };

  /// Gather an answer's SRV, TXT, and address records (mDNS responders
  /// send them along with the PTR, saving a resolve) by owner name.
  static auto CollectAnswers_(DNS_RECORDW* records)
      -> std::map<std::string, Answer_> {
    std::map<std::string, std::pair<std::string, int>> srv;  // -> host, port
    std::map<std::string, std::vector<std::pair<std::string, std::string>>> txt;
    std::map<std::string, std::vector<std::string>> host_addrs;
    for (auto* rec = records; rec != nullptr; rec = rec->pNext) {
      if (rec->pName == nullptr || rec->dwTtl == 0) {
        continue;
      }
      std::string owner = Lower_(PlatformWindows::UTF8Encode(rec->pName));
      switch (rec->wType) {
        case DNS_TYPE_SRV:
          if (rec->Data.SRV.pNameTarget != nullptr) {
            srv[owner] = {
                Lower_(PlatformWindows::UTF8Encode(rec->Data.SRV.pNameTarget)),
                rec->Data.SRV.wPort};
          }
          break;
        case DNS_TYPE_TEXT: {
          auto& items = txt[owner];
          for (DWORD i = 0; i < rec->Data.TXT.dwStringCount; ++i) {
            if (rec->Data.TXT.pStringArray[i] == nullptr) {
              continue;
            }
            std::string item =
                PlatformWindows::UTF8Encode(rec->Data.TXT.pStringArray[i]);
            auto eq = item.find('=');
            if (eq == std::string::npos) {
              items.emplace_back(item, std::string());
            } else {
              items.emplace_back(item.substr(0, eq), item.substr(eq + 1));
            }
          }
          break;
        }
        case DNS_TYPE_A: {
          in_addr addr4{};
          addr4.s_addr = rec->Data.A.IpAddress;  // (Network order.)
          char buffer[INET_ADDRSTRLEN];
          if (inet_ntop(AF_INET, &addr4, buffer, sizeof(buffer))) {
            host_addrs[owner].emplace_back(buffer);
          }
          break;
        }
        case DNS_TYPE_AAAA: {
          in6_addr addr6{};
          memcpy(&addr6, rec->Data.AAAA.Ip6Address.IP6Byte, sizeof(addr6));
          // (Records don't say which interface they came in on, which a
          // link-local address needs; a resolve fills those in.)
          char buffer[INET6_ADDRSTRLEN];
          if (!IN6_IS_ADDR_LINKLOCAL(&addr6)
              && inet_ntop(AF_INET6, &addr6, buffer, sizeof(buffer))) {
            host_addrs[owner].emplace_back(buffer);
          }
          break;
        }
        default:
          break;
      }
    }
    std::map<std::string, Answer_> out;
    for (auto&& [owner, target] : srv) {
      auto& answer = out[owner];
      answer.port = target.second;
      answer.txt = txt[owner];
      answer.addresses = host_addrs[target.first];
    }
    return out;
  }

  static auto Lower_(std::string s) -> std::string {
    for (auto& c : s) {
      if (c >= 'A' && c <= 'Z') {
        c = static_cast<char>(c - 'A' + 'a');
      }
    }
    return s;
  }

  void HandleBrowseRecords_(BrowseContext_* ctx, DNS_RECORDW* records) {
    auto answers = CollectAnswers_(records);
    std::vector<ResolveContext_*> to_resolve;
    {
      std::scoped_lock lock(mutex_);
      if (!browsing_ || ctx->generation != generation_) {
        return;  // A straggler from an earlier browse.
      }
      auto now = g_core->AppTimeMillisecs();
      std::string query_name = Lower_(ctx->service_type + ".local");
      for (auto* rec = records; rec != nullptr; rec = rec->pNext) {
        if (rec->wType != DNS_TYPE_PTR || rec->Data.PTR.pNameHost == nullptr
            || rec->pName == nullptr) {
          continue;
        }
        // Answers for other services land here too; only take ours.
        if (Lower_(PlatformWindows::UTF8Encode(rec->pName)) != query_name) {
          continue;
        }
        std::string full = PlatformWindows::UTF8Encode(rec->Data.PTR.pNameHost);
        std::string key = ctx->service_type + "|" + Lower_(full);
        std::string name = InstanceName_(full, ctx->service_type);

        // A zero TTL is a goodbye.
        if (rec->dwTtl == 0) {
          NearbyServiceEvent event;
          event.added = false;
          event.service_type = ctx->service_type;
          event.instance = key;
          event.name = name;
          events_.push_back(std::move(event));
          continue;
        }

        // Report whatever addresses came along in this answer.
        auto answer = answers.find(Lower_(full));
        if (answer != answers.end()) {
          for (auto&& addr : answer->second.addresses) {
            NearbyServiceEvent event;
            event.added = true;
            event.service_type = ctx->service_type;
            event.instance = key;
            event.name = name;
            event.address = addr;
            event.port = answer->second.port;
            event.txt = answer->second.txt;
            events_.push_back(std::move(event));
          }
        }

        // And resolve it every so often, which fills in link-local
        // addresses and covers answers that came without extras.
        // (Gated on time alone, so a resolve that never completes
        // doesn't block later ones.)
        auto pending = resolving_.find(key);
        if (pending != resolving_.end()
            && now - pending->second < kResolveRetryMillisecs) {
          continue;
        }
        resolving_[key] = now;
        auto* rctx = new ResolveContext_();
        rctx->owner = this;
        rctx->generation = generation_;
        rctx->key = key;
        rctx->service_type = ctx->service_type;
        rctx->name = name;
        rctx->query_name = rec->Data.PTR.pNameHost;
        to_resolve.push_back(rctx);
      }
    }
    for (auto* rctx : to_resolve) {
      DNS_SERVICE_RESOLVE_REQUEST request{};
      request.Version = DNS_QUERY_REQUEST_VERSION1;
      request.InterfaceIndex = 0;
      request.QueryName = rctx->query_name.data();
      request.pResolveCompletionCallback = ResolveCallback_;
      request.pQueryContext = rctx;
      auto status = DnsServiceResolve(&request, &rctx->cancel);
      if (status != DNS_REQUEST_PENDING) {
        // No callback is coming, so it's ours to clean up.
        {
          std::scoped_lock lock(mutex_);
          resolving_.erase(rctx->key);
        }
        delete rctx;
      }
    }
  }

  static void WINAPI ResolveCallback_(DWORD status, PVOID context,
                                      PDNS_SERVICE_INSTANCE instance) {
    std::unique_ptr<ResolveContext_> rctx{
        static_cast<ResolveContext_*>(context)};
    if (status != ERROR_SUCCESS) {
      g_core->logging->Log(LogName::kBaNetworking, LogLevel::kDebug, [&] {
        return "DNS-SD resolve of " + rctx->key + " failed (status "
               + std::to_string(status) + ").";
      });
    }
    if (status == ERROR_SUCCESS && instance != nullptr) {
      rctx->owner->HandleResolved_(*rctx, *instance);
    }
    if (instance != nullptr) {
      DnsServiceFreeInstance(instance);
    }
  }

  void HandleResolved_(const ResolveContext_& rctx,
                       const DNS_SERVICE_INSTANCE& instance) {
    std::vector<std::string> addresses;
    if (instance.ip4Address != nullptr) {
      in_addr addr4{};
      addr4.s_addr = *instance.ip4Address;  // (Already network order.)
      char buffer[INET_ADDRSTRLEN];
      if (inet_ntop(AF_INET, &addr4, buffer, sizeof(buffer))) {
        addresses.emplace_back(buffer);
      }
    }
    if (instance.ip6Address != nullptr) {
      in6_addr addr6{};
      memcpy(&addr6, instance.ip6Address->IP6Byte, sizeof(addr6));
      char buffer[INET6_ADDRSTRLEN];
      if (inet_ntop(AF_INET6, &addr6, buffer, sizeof(buffer))) {
        std::string addr{buffer};
        // Link-local addresses only mean something on one interface;
        // Windows names interfaces by number ('fe80::1%12').
        if (IN6_IS_ADDR_LINKLOCAL(&addr6)) {
          if (instance.dwInterfaceIndex != 0) {
            addresses.push_back(addr + "%"
                                + std::to_string(instance.dwInterfaceIndex));
          }
        } else {
          addresses.push_back(std::move(addr));
        }
      }
    }
    std::vector<std::pair<std::string, std::string>> txt;
    for (DWORD i = 0; i < instance.dwPropertyCount; ++i) {
      if (instance.keys == nullptr || instance.keys[i] == nullptr) {
        continue;
      }
      txt.emplace_back(PlatformWindows::UTF8Encode(instance.keys[i]),
                       (instance.values && instance.values[i])
                           ? PlatformWindows::UTF8Encode(instance.values[i])
                           : std::string());
    }

    std::scoped_lock lock(mutex_);
    if (rctx.generation != generation_) {
      return;
    }
    for (auto&& addr : addresses) {
      NearbyServiceEvent event;
      event.added = true;
      event.service_type = rctx.service_type;
      event.instance = rctx.key;
      event.name = rctx.name;
      event.address = addr;
      event.port = instance.wPort;
      event.txt = txt;
      events_.push_back(std::move(event));
    }
  }

  /// 'My Game._bagame._udp.local' -> 'My Game'.
  static auto InstanceName_(const std::string& full,
                            const std::string& service_type) -> std::string {
    auto pos = full.rfind("." + service_type);
    return pos == std::string::npos ? full : full.substr(0, pos);
  }

  // Advertising (any thread; under advertise_mutex_).
  std::mutex advertise_mutex_;
  Registration_ game_reg_;
  Registration_ remote_reg_;

  // Browsing state, shared with OS callback threads (under mutex_).
  std::mutex mutex_;
  bool browsing_{};
  uint64_t generation_{};
  std::map<std::string, std::unique_ptr<BrowseContext_>> browse_contexts_;
  // When each instance was last resolved (see kResolveRetryMillisecs).
  std::map<std::string, millisecs_t> resolving_;
  std::vector<NearbyServiceEvent> events_;
};

}  // namespace

#endif  // BA_PLATFORM_WINDOWS

auto NearbyServices::Get() -> NearbyServices& {
#if BA_NEARBY_SERVICES_DNS_SD
  static auto* instance = new NearbyServicesDNSSD();
#elif BA_PLATFORM_ANDROID
  static auto* instance = new NearbyServicesAndroid();
#elif BA_PLATFORM_WINDOWS
  static auto* instance = new NearbyServicesWindows();
#else
  static auto* instance = new NearbyServices();
#endif
  return *instance;
}

}  // namespace ballistica::base
