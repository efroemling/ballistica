# Released under the MIT License. See LICENSE for details.
#
"""Snippets of code for use by the c++ layer."""
# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring
from __future__ import annotations

import _baplus


def submit_analytics_counts(sval: str) -> None:
    _baplus.add_v1_account_transaction(
        {'type': 'ANALYTICS_COUNTS', 'values': sval}
    )
    _baplus.run_v1_account_transactions()
