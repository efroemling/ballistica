# Released under the MIT License. See LICENSE for details.
#
"""Main thread bootstrapping for Python monolithic builds."""

# This code runs in the main thread just after the interpreter comes up.
# It should *ONLY* do things that must be done in the main thread and
# should not import any ballistica stuff.

from __future__ import annotations

import signal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Tell Python to not handle SIGINT itself (it normally generates
# KeyboardInterrupts which make a mess; we want to intercept them
# for simple clean exit). We have to do this part here because it must
# run in the main thread. We add our own handler later in the logic thread
# alongside our other ba bootstrapping.
signal.signal(signal.SIGINT, signal.SIG_DFL)  # Do default handling.
