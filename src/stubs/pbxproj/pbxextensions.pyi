# Everything resolves to Any.
from typing import Any

def __getattr__(name) -> Any:
    ...
