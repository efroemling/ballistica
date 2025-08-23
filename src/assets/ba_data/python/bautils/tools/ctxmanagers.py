# Released under the MIT License. See LICENSE for details.
#
"""Collection of various context managers."""

# ba_meta require api 9

import time

from typing import Generator, Any
from contextlib import contextmanager

from efro.terminal import Clr


@contextmanager
def package_loading_context(name: str) -> Generator[None, Any, None]:
    """A context manager securing to load all files in this package."""

    print(f"{Clr.YLW}🚀 Initializing {name}...")
    start = time.time()
    try:
        yield
        elapsed = time.time() - start
        print(f"{Clr.GRN} ✅ All modules for {name} loaded in {elapsed:.2f}s.")
    except Exception as e:
        print(f"{Clr.RED}❌ Failed to load module {name}: {e}")
        raise
