// Released under the MIT License. See LICENSE for details.

#include "ballistica/core/module.h"

#include <utility>

#include "ballistica/core/thread.h"

namespace ballistica {

void Module::PushLocalRunnable(Runnable* runnable) {
  assert(std::this_thread::get_id() == thread()->thread_id());
  runnables_.push_back(runnable);
}

void Module::PushRunnable(Runnable* runnable) {
  // If we're being called from the module's thread, just drop it in the list.
  // otherwise send it as a message to the other thread.
  if (std::this_thread::get_id() == thread()->thread_id()) {
    PushLocalRunnable(runnable);
  } else {
    thread_->PushModuleRunnable(runnable, id_);
  }
}

Module::Module(std::string name_in, Thread* thread_in)
    : thread_(thread_in), name_(std::move(name_in)) {
  id_ = thread_->RegisterModule(name_, this);
}

Module::~Module() = default;

auto Module::NewThreadTimer(millisecs_t length, bool repeat,
                            const Object::Ref<Runnable>& runnable) -> Timer* {
  return thread_->NewTimer(length, repeat, runnable);
}

void Module::RunPendingRunnables() {
  // Pull all runnables off the list first (its possible for one of these
  // runnables to add more) and then process them.
  assert(std::this_thread::get_id() == thread()->thread_id());
  std::list<Runnable*> runnables;
  runnables_.swap(runnables);
  for (Runnable* i : runnables) {
    i->Run();
    delete i;
  }
}

}  // namespace ballistica
