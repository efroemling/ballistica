// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_GAME_SCORE_TO_BEAT_H_
#define BALLISTICA_GAME_SCORE_TO_BEAT_H_

#include <string>
#include <utility>

namespace ballistica {

// Do we still need this?
class ScoreToBeat {
 public:
  ScoreToBeat(std::string player_in, std::string type_in, std::string value_in,
              double timeIn)
      : player(std::move(player_in)),
        type(std::move(type_in)),
        value(std::move(value_in)),
        time(timeIn) {}
  std::string player;
  std::string type;
  std::string value;
  double time;
};

}  // namespace ballistica

#endif  // BALLISTICA_GAME_SCORE_TO_BEAT_H_
