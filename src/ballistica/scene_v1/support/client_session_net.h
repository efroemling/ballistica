// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_NET_H_
#define BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_NET_H_

#include <vector>

#include "ballistica/scene_v1/support/client_session.h"

namespace ballistica::scene_v1 {

// A client-session fed by a connection to a host.
class ClientSessionNet : public ClientSession {
 public:
  ClientSessionNet();
  ~ClientSessionNet() override;
  auto connection_to_host() const -> ConnectionToHost* {
    return connection_to_host_.get();
  }
  void SetConnectionToHost(ConnectionToHost* c);
  void HandleSessionMessage(const std::vector<uint8_t>& buffer) override;
  void OnCommandBufferUnderrun() override;
  void Update(int time_advance_millisecs, double time_advance) override;
  void OnReset(bool rewind) override;
  void OnBaseTimeStepAdded(int step) override;

 private:
  struct SampleBucket {
    int max_delay_from_projection{};
  };

  auto ProjectedBaseTime(millisecs_t now) const -> millisecs_t {
    return leading_base_time_received_
           + (now - leading_base_time_receive_time_);
  }
  void UpdateBuffering();
  auto GetBucketNum() -> int;

  bool writing_replay_{};
  int delay_sample_counter_{};
  float max_delay_smoothed_{};
  float last_bucket_max_delay_{};
  float current_delay_{};
  millisecs_t base_time_received_{};
  millisecs_t last_base_time_receive_time_{};
  millisecs_t leading_base_time_received_{};
  millisecs_t leading_base_time_receive_time_{};
  Object::WeakRef<ConnectionToHost> connection_to_host_;
  std::vector<SampleBucket> buckets_{5};
  ReplayWriter* replay_writer_{};
};

}  // namespace ballistica::scene_v1

#endif  // BALLISTICA_SCENE_V1_SUPPORT_CLIENT_SESSION_NET_H_
