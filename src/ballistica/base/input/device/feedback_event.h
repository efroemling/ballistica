// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_INPUT_DEVICE_FEEDBACK_EVENT_H_
#define BALLISTICA_BASE_INPUT_DEVICE_FEEDBACK_EVENT_H_

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iterator>
#include <optional>

namespace ballistica::base {

/// A request for physical feedback (controller rumble, device vibration)
/// on an input device.
///
/// A request says *what happened* and nothing else. Backends then render
/// each event however their platform does it best -- Android primitives,
/// Core Haptics intensity/sharpness, raw motor magnitudes on SDL.
/// Describing the sensation instead would cap every platform at the least
/// common denominator, since the information a good backend needs would
/// already have been thrown away by the time it was asked.
///
/// Note there is deliberately no intensity or duration here. Those are
/// rendering decisions and live in each backend; what a caller cannot
/// express, a caller cannot get wrong, and it keeps the feel of an event
/// tunable in one place per platform rather than drifting across call
/// sites (decision D18).
///
/// This type is app-mode agnostic on purpose. Resolving *who* should feel
/// something is the job of whatever layer owns players and networking
/// (currently scene_v1); by the time a FeedbackEvent reaches an
/// InputDevice the addressing is already done.
///
/// See docs/initiatives/controller-force-feedback.md.
struct FeedbackEvent {
  /// What happened.
  ///
  /// Kept deliberately game-agnostic -- generic enough to stay useful
  /// across game types rather than encoding one game's mechanics. Adding
  /// a type is free on the wire (older clients simply ignore what they do
  /// not know), but each is effectively permanent once shipped, so the
  /// set is worth growing slowly.
  ///
  /// A backend may legitimately render NOTHING for a type it understands
  /// perfectly well, if its hardware cannot do it justice -- a light tap
  /// on heavy ERM flywheels comes out a mushy buzz that reads as noise
  /// rather than as a tap, and silence serves the player better. So
  /// callers must not assume every type produces something on every
  /// device (decision D17).
  enum class Type : uint8_t {
    /// Entered or committed to something -- joining a game, taking a
    /// slot. Should feel substantial and final; this is a moment, not a
    /// nudge.
    kJoin,

    /// Acquired a pickup, powerup or reward. The lightest thing we
    /// emit: a confirmation you notice without it interrupting you.
    kCollect,

    /// Took hold of something. A shade fuller than a collect -- you did
    /// something to the world rather than merely receiving it.
    kGrab,

    /// You struck something. This is *information*: it confirms an
    /// action you took, so it should read as crisp and immediate rather
    /// than heavy. Suppressing it makes a game feel unresponsive.
    kImpactDealt,

    /// Something struck you. An alarm rather than a confirmation, and
    /// the most frequent event in a busy game -- so it wants presence
    /// without becoming wearing.
    kImpactReceived,

    /// Death, destruction, failure. Rare and weighty; one of the few
    /// places worth full strength, which is what makes it read as an
    /// outlier rather than just another hit.
    kDeath,

    kLast  // Sentinel.
  };

  /// Everything about a type that is *not* a rendering decision.
  struct TypeProfile {
    /// Name used by the Python API. Decoupled from the wire code so the
    /// public API stays renameable.
    const char* name;

    /// Wire code. Terse and effectively frozen once shipped.
    char code;

    /// Which event wins when two want the device at once. Higher wins;
    /// equal preempts, so the most recent event of a given importance is
    /// what you feel.
    ///
    /// Deliberately separate from anything a backend renders. When
    /// arbitration keyed off intensity instead, retuning how an event
    /// *felt* silently changed which event *won* -- a pure feel
    /// adjustment could invert the ordering with nothing to flag it.
    /// Values are spaced so new types can slot between.
    int priority;

    /// How long this event holds the device against lower-priority
    /// events, in milliseconds.
    ///
    /// This is an arbitration window, NOT a vibration length. Several
    /// platforms give no control over how long a haptic lasts (iOS
    /// transients, Android predefined effects), so a render duration is
    /// not something we can promise anywhere.
    ///
    /// It is a *minimum*: a backend that needs longer to render says so
    /// (see InputDevice::DoApplyFeedback) and the arbiter extends the
    /// window to cover it. That matters because render lengths are not
    /// comparable across platforms -- an ERM flywheel needs ~150ms
    /// before anything is felt at all, where SDL's direct drive manages
    /// in 60 -- so a single shared number cannot serve as both the
    /// design intent and the truncation guard.
    int hold_millisecs;
  };

  /// Indexed by Type; see the static_assert below.
  static constexpr TypeProfile kTypeProfiles[] = {
      {"join", 'j', 50, 100},
      {"collect", 'c', 10, 100},
      {"grab", 'g', 20, 100},
      {"impact_dealt", 'd', 30, 100},
      {"impact_received", 'r', 30, 100},
      {"death", 'x', 100, 200},
  };

  static_assert(std::size(kTypeProfiles) == static_cast<size_t>(Type::kLast),
                "Every FeedbackEvent::Type needs a profile entry, in"
                " enum order.");

  static auto ProfileForType(Type type) -> const TypeProfile& {
    auto index = static_cast<size_t>(type);
    assert(index < std::size(kTypeProfiles));
    return kTypeProfiles[index];
  }

  /// Resolve a wire code. Unknown codes yield nothing -- callers drop
  /// them rather than guessing (decision D6).
  static auto TypeFromCode(char code) -> std::optional<Type> {
    for (size_t i = 0; i < std::size(kTypeProfiles); ++i) {
      if (kTypeProfiles[i].code == code) {
        return static_cast<Type>(i);
      }
    }
    return {};
  }

  /// Resolve a Python API name.
  static auto TypeFromName(const char* name) -> std::optional<Type> {
    for (size_t i = 0; i < std::size(kTypeProfiles); ++i) {
      if (strcmp(kTypeProfiles[i].name, name) == 0) {
        return static_cast<Type>(i);
      }
    }
    return {};
  }

  /// The type assumed when a payload names none. Chosen as the most
  /// frequent event in play so the common case stays a two-byte '{}' on
  /// the wire.
  static constexpr Type kDefaultType{Type::kImpactReceived};

  Type type{kDefaultType};
};

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_INPUT_DEVICE_FEEDBACK_EVENT_H_
