// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_PLAYER_SPEC_H_
#define BALLISTICA_SCENE_V1_SUPPORT_PLAYER_SPEC_H_

#include <string>

namespace ballistica::scene_v1 {

/// a PlayerSpec is a portable description of an entity such as a player or
/// client. It can contain long and short names, optional info linking it to a
/// V1 account, and can be passed around easily in string form.
/// Note: usage of this should be phased out during the V2 era; the C++ layer
/// should not know or care about V2 accounts.
class PlayerSpec {
 public:
  /// Create an invalid player-spec.
  PlayerSpec();
  auto operator==(const PlayerSpec& spec) const -> bool;

  /// Create a player-spec from a given spec-string.
  /// In the case of an error, defaults will be used
  /// (though the error will be reported).
  explicit PlayerSpec(const std::string& s);

  /// Return a full display string for the spec,
  /// which may include the account icon.
  auto GetDisplayString() const -> std::string;

  /// Returns a short version of the player's name.
  /// Ideal for displaying in-game; this includes
  /// no icon and may just be the first name.
  auto GetShortName() const -> std::string;

  /// Return the full string form to be passed around.
  auto GetSpecString() const -> std::string;

  /// Return a PlayerSpec for the currently logged in v1 account.
  /// If there is no current logged in v1 account, a dummy-spec is created
  /// using the current party name or device name (so this always returns
  /// something reasonable).
  static auto GetAccountPlayerSpec() -> PlayerSpec;

  /// Return a 'dummy' PlayerSpec using the given name; can be
  /// used for non-account player profiles, names for non-logged-in
  /// party hosts, etc.
  static auto GetDummyPlayerSpec(const std::string& name) -> PlayerSpec;

  auto valid() const { return valid_; }

 private:
  std::string name_;
  std::string short_name_;
  int v1_account_type_{};
  bool valid_{true};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_PLAYER_SPEC_H_
