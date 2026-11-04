// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_NETWORKING_NEARBY_SERVICES_H_
#define BALLISTICA_BASE_NETWORKING_NEARBY_SERVICES_H_

#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace ballistica::base {

/// Bonjour-style service type for joinable games.
extern const char* const kNearbyGameServiceType;

/// Bonjour-style service type for games accepting remote-app controllers.
extern const char* const kNearbyRemoteServiceType;

/// What StartBrowse() returns when browsing works but there's nothing to
/// wait on: the caller just calls ProcessBrowse() every so often.
constexpr int kNearbyBrowseNoDescriptor = -2;

/// Something a service browse learned.
struct NearbyServiceEvent {
  /// True: an address for the instance; false: the instance went away.
  bool added{};
  std::string service_type;

  /// Identifies the instance (unique per type and interface); a removal
  /// carries the same value as its additions.
  std::string instance;

  /// The instance's human-readable name.
  std::string name;

  /// Additions only.
  std::string address;
  int port{};
  std::vector<std::pair<std::string, std::string>> txt;
};

/// The OS's DNS-SD (Bonjour/mDNS) layer: advertises our game socket
/// and browses for other games.
///
/// This is discovery only; what it finds are plain addresses that the
/// normal sockets talk to. Python's nearby-discovery verifies and ranks
/// them (see babase/_nearbyimpl.py). Platforms without support get a
/// no-op version.
class NearbyServices {
 public:
  /// The single shared instance (created on first use).
  static auto Get() -> NearbyServices&;

  virtual ~NearbyServices();

  /// Set what we advertise for our game socket's port. A port of 0
  /// advertises nothing. Callable from any thread.
  virtual void SetAdvertised(int port, bool game, bool remote);

  /// Whether browsing works here at all.
  virtual auto BrowseSupported() -> bool;

  /// Start browsing for the given service types, returning a file
  /// descriptor that becomes readable when ProcessBrowse() has
  /// something for us, kNearbyBrowseNoDescriptor where there's none to
  /// offer (poll instead), or -1 on failure. One browse runs at a time;
  /// call these from a single thread.
  virtual auto StartBrowse(const std::vector<std::string>& service_types)
      -> int;

  /// Handle whatever is pending on the browse descriptor.
  virtual auto ProcessBrowse() -> std::vector<NearbyServiceEvent>;

  virtual void StopBrowse();

  /// For platform glue whose OS delivers browse results asynchronously
  /// on its own threads (Android's NsdManager): hand one over. Any
  /// thread.
  virtual void PushPlatformEvent(NearbyServiceEvent event);
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_NETWORKING_NEARBY_SERVICES_H_
