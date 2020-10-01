// Copyright (c) 2011-2020 Eric Froemling
#if BA_HEADLESS_BUILD

#include "ballistica/app/headless_app.h"

#include "ballistica/ballistica.h"

namespace ballistica {

// We could technically use the vanilla App class here since we're not
// changing anything.
HeadlessApp::HeadlessApp(Thread* thread) : App(thread) {
  //  NewThreadTimer(10, true, NewLambdaRunnable([this] {
  //                   assert(g_app);
  //                   g_app->RunEvents();
  //                 }));
}

}  // namespace ballistica

#endif  // BA_HEADLESS_BUILD
