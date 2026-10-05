// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_CHANNEL_H_
#define BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_CHANNEL_H_

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include "ballistica/core/logging/logging_macros.h"
#include "ballistica/shared/ballistica.h"

namespace ballistica::base {

class BGDynamicsWorldServer;

// Typed channels are how per-entity state crosses between the logic
// thread and the bg-dynamics thread. There is no shared mutable state:
// the logic side owns inputs, the worker side owns simulation state,
// and everything moves as messages -- inputs plus in-band
// create/destroy deltas ride each StepData; outputs come back as
// whole-buffer bundles the logic side adopts. So the worker's world is
// always consistent with exactly one step, the worker never sees
// logic-side memory, and readers can never observe a torn write.
//
// A Kind declares:
//   struct Config;   immutable per entity, sent at create
//   struct Input;    POD, logic -> worker, every step
//   struct Output;   POD, worker -> logic, every step
//   class Sim {      worker-side state
//     Sim(const Config&, BGDynamicsWorldServer*);
//     void SetInput(const Input&);
//     void Step(BGDynamicsWorldServer*);   // before the world step
//     void GetOutput(Output*) const;  // after the world step
//   };
// and is listed in BGDynamicsKinds (bg_dynamics_kinds.h).

/// Identifies one live entity in a channel: a dense slot index plus a
/// generation that bumps on every reuse of the slot, so stale outputs
/// (or a bundle computed before a re-created slot existed) are never
/// mistaken for current ones.
struct BGDynamicsSlot {
  uint32_t index{};
  uint32_t generation{};
};

/// One channel's slice of a StepData: that step's create/destroy
/// deltas in order, plus a snapshot of every slot's input.
template <typename Kind>
struct BGDynamicsChannelStepData {
  struct Delta {
    bool create{};  // false = destroy
    BGDynamicsSlot slot;
    typename Kind::Config config{};  // Create only.
  };
  std::vector<Delta> deltas;
  std::vector<typename Kind::Input> inputs;
};

/// One channel's slice of an output bundle: per-slot outputs stamped
/// with the generation they were computed for (0 = no entity).
template <typename Kind>
struct BGDynamicsChannelOutputs {
  std::vector<typename Kind::Output> outputs;
  std::vector<uint32_t> generations;
};

/// Logic-thread side of a channel: slot allocation, input storage,
/// per-step gather, and lock-free access to the last adopted outputs.
/// Everything here runs on the logic thread only.
template <typename Kind>
class BGDynamicsChannel {
 public:
  using Config = typename Kind::Config;
  using Input = typename Kind::Input;
  using Output = typename Kind::Output;

  auto Create(const Config& config) -> BGDynamicsSlot {
    BGDynamicsSlot slot;
    if (!free_.empty()) {
      slot.index = free_.back();
      free_.pop_back();
    } else {
      slot.index = static_cast<uint32_t>(inputs_.size());
      inputs_.emplace_back();
      generations_.push_back(0);
    }
    slot.generation = ++generations_[slot.index];
    inputs_[slot.index] = Input{};
    deltas_.push_back({true, slot, config});
    CheckPendingDeltas_();
    return slot;
  }

  /// Slots may be reused within the same step; deltas stay ordered so
  /// the worker destroys the old entity before creating the new one.
  /// A destroy whose create is still pending cancels both instead:
  /// the worker never hears of the entity, and pending deltas stay
  /// bounded by the live-entity count however long feeds are paused
  /// (no foreground scene stepping, backpressure skips, etc).
  void Destroy(BGDynamicsSlot slot) {
    assert(slot.index < generations_.size()
           && generations_[slot.index] == slot.generation);
    bool cancelled = false;
    for (auto i = deltas_.begin(); i != deltas_.end(); ++i) {
      if (i->create && i->slot.index == slot.index
          && i->slot.generation == slot.generation) {
        deltas_.erase(i);
        cancelled = true;
        break;
      }
    }
    if (!cancelled) {
      deltas_.push_back({false, slot, Config{}});
      CheckPendingDeltas_();
    }
    free_.push_back(slot.index);
  }

  auto input(BGDynamicsSlot slot) -> Input& {
    assert(generations_[slot.index] == slot.generation);
    return inputs_[slot.index];
  }
  auto input(BGDynamicsSlot slot) const -> const Input& {
    assert(generations_[slot.index] == slot.generation);
    return inputs_[slot.index];
  }

  /// The latest adopted output for the slot, or nullptr if none has
  /// arrived for this generation yet.
  auto output(BGDynamicsSlot slot) const -> const Output* {
    if (slot.index < adopted_.generations.size()
        && adopted_.generations[slot.index] == slot.generation) {
      return &adopted_.outputs[slot.index];
    }
    return nullptr;
  }

  /// Move pending deltas and copy inputs into a step payload. Only
  /// this drains deltas, so a skipped feed (backpressure) simply
  /// leaves them to ride the next one.
  void Gather(BGDynamicsChannelStepData<Kind>* out) {
    out->deltas = std::move(deltas_);
    deltas_.clear();
    out->inputs = inputs_;
  }

  void Adopt(BGDynamicsChannelOutputs<Kind>* outputs) {
    // Swap rather than move: the bundle then carries our previous
    // buffers back to the worker for reuse (see
    // BGDynamicsWorldServer::RecycleBundle).
    std::swap(adopted_, *outputs);
  }

 private:
  /// Pending deltas are bounded by the live-entity count (destroys
  /// annihilate pending creates), so a runaway count means feeds have
  /// stopped draining them -- a bug worth hearing about once. A full
  /// 8-player respawn wave is ~100 creates in one step (a spaz carries
  /// 13 shadows) and a busy game holds a few hundred live entities, so
  /// this sits an order of magnitude above any legitimate burst.
  void CheckPendingDeltas_() {
    static constexpr size_t kPendingDeltaWarnCount{2000};
    if (deltas_.size() == kPendingDeltaWarnCount) {
      BA_LOG_ONCE(LogName::kBa, LogLevel::kError,
                  "BGDynamics channel has "
                      + std::to_string(kPendingDeltaWarnCount)
                      + " pending deltas; feeds are not draining them.");
    }
  }

  std::vector<Input> inputs_;
  std::vector<uint32_t> generations_;
  std::vector<uint32_t> free_;
  std::vector<typename BGDynamicsChannelStepData<Kind>::Delta> deltas_;
  BGDynamicsChannelOutputs<Kind> adopted_;
};

/// Worker-thread side of a channel: owns the per-slot Sim states.
/// Everything here runs on the bg-dynamics thread only.
template <typename Kind>
class BGDynamicsChannelWorker {
 public:
  using Sim = typename Kind::Sim;

  void Apply(const BGDynamicsChannelStepData<Kind>& data,
             BGDynamicsWorldServer* server) {
    for (const auto& delta : data.deltas) {
      if (delta.slot.index >= sims_.size()) {
        sims_.resize(delta.slot.index + 1);
        generations_.resize(delta.slot.index + 1, 0);
      }
      if (delta.create) {
        sims_[delta.slot.index] = std::make_unique<Sim>(delta.config, server);
        generations_[delta.slot.index] = delta.slot.generation;
      } else {
        sims_[delta.slot.index].reset();
        generations_[delta.slot.index] = 0;
      }
    }
    size_t count = std::min(data.inputs.size(), sims_.size());
    for (size_t i = 0; i < count; ++i) {
      if (sims_[i]) {
        sims_[i]->SetInput(data.inputs[i]);
      }
    }
  }

  void Step(BGDynamicsWorldServer* server) {
    for (auto& sim : sims_) {
      if (sim) {
        sim->Step(server);
      }
    }
  }

  /// Visit every live Sim (for worker-side consumers such as the draw
  /// snapshot builder).
  template <typename F>
  void ForEachSim(F&& f) const {
    for (const auto& sim : sims_) {
      if (sim) {
        f(*sim);
      }
    }
  }

  /// Do away with every Sim. For a world being taken down: Sims hold
  /// bodies and such in the world, so they have to go before it does.
  void Clear() {
    sims_.clear();
    generations_.clear();
  }

  void Publish(BGDynamicsChannelOutputs<Kind>* out) const {
    // Bundles are recycled, so this normally has the capacity already
    // and only a grown slot count allocates. Let go of a burst's worth
    // of slots once it has passed.
    out->outputs.resize(sims_.size());
    if (out->outputs.capacity() > 2 * sims_.size() + 16) {
      out->outputs.shrink_to_fit();
    }
    out->generations.assign(sims_.size(), 0);
    for (size_t i = 0; i < sims_.size(); ++i) {
      if (sims_[i]) {
        sims_[i]->GetOutput(&out->outputs[i]);
        out->generations[i] = generations_[i];
      }
    }
  }

 private:
  std::vector<std::unique_ptr<Sim>> sims_;
  std::vector<uint32_t> generations_;
};

/// Apply f(a_i, b_i) across two same-shaped tuples.
template <typename F, typename... A, typename... B, size_t... I>
void BGDynamicsForEachPairImpl(std::tuple<A...>& a, std::tuple<B...>& b, F&& f,
                               std::index_sequence<I...>) {
  (f(std::get<I>(a), std::get<I>(b)), ...);
}
template <typename F, typename... A, typename... B>
void BGDynamicsForEachPair(std::tuple<A...>& a, std::tuple<B...>& b, F&& f) {
  static_assert(sizeof...(A) == sizeof...(B));
  BGDynamicsForEachPairImpl(a, b, std::forward<F>(f),
                            std::index_sequence_for<A...>{});
}

}  // namespace ballistica::base

#endif  // BALLISTICA_BASE_DYNAMICS_BG_BG_DYNAMICS_CHANNEL_H_
