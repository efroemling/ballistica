// Released under the MIT License. See LICENSE for details.

#ifndef BALLISTICA_LOGIC_FRIEND_SCORE_SET_H_
#define BALLISTICA_LOGIC_FRIEND_SCORE_SET_H_

#include <list>
#include <string>
#include <utility>

namespace ballistica {

// Used by game-center/etc when reporting friend scores to the game.
struct FriendScoreSet {
  FriendScoreSet(bool success, void* user_data)
      : success(success), user_data(user_data) {}
  struct Entry {
    Entry(int score, std::string name, bool is_me)
        : score(score), name(std::move(name)), is_me(is_me) {}
    int score;
    std::string name;
    bool is_me;
  };
  std::list<Entry> entries;
  bool success;
  void* user_data;
};

}  // namespace ballistica

#endif  // BALLISTICA_LOGIC_FRIEND_SCORE_SET_H_
