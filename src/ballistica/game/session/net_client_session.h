// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_SESSION_NET_CLIENT_SESSION_H_
#define BALLISTICA_GAME_SESSION_NET_CLIENT_SESSION_H_

#include <vector>

#include "ballistica/game/session/client_session.h"

namespace ballistica {

// A client-session fed by a connection to a host.
class NetClientSession : public ClientSession {
 public:
  NetClientSession();
  ~NetClientSession() override;
  auto connection_to_host() const -> ConnectionToHost* {
    return connection_to_host_.get();
  }
  auto SetConnectionToHost(ConnectionToHost* c) -> void;
  auto HandleSessionMessage(const std::vector<uint8_t>& buffer)
      -> void override;
  auto OnCommandBufferUnderrun() -> void override;
  auto Update(int time_advance) -> void override;
  auto OnReset(bool rewind) -> void override;
  auto OnBaseTimeStepAdded(int step) -> void override;

 private:
  struct SampleBucket {
    //    int least_buffered_count{};
    //    int most_buffered_count{};
    int max_delay_from_projection{};
  };

  auto ProjectedBaseTime(millisecs_t now) const -> millisecs_t {
    return leading_base_time_received_
           + (now - leading_base_time_receive_time_);
  }
  auto UpdateBuffering() -> void;
  auto GetBucketNum() -> int;

  bool writing_replay_{};
  millisecs_t base_time_received_{};
  millisecs_t last_base_time_receive_time_{};
  millisecs_t leading_base_time_received_{};
  millisecs_t leading_base_time_receive_time_{};
  Object::WeakRef<ConnectionToHost> connection_to_host_;
  std::vector<SampleBucket> buckets_{5};

  //  float bucket_max_smoothed_{};
  //  float bucket_min_smoothed_{};
  float max_delay_smoothed_{};
  float last_bucket_max_delay_{};
  float current_delay_{};

  int delay_sample_counter_{};
  int adjust_counter_{};
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_SESSION_NET_CLIENT_SESSION_H_
