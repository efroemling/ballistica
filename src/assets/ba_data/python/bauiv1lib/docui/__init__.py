# Released under the MIT License. See LICENSE for details.
"""Functionality for using doc-ui on top of bauiv1.

Threading design
================

Doc-ui deliberately offloads as much processing as possible to
background threads, keeping logic-thread work to the bare minimum
(instantiating widgets and running actions/effects). A request's whole
journey — controller fulfillment (including cloud/web round-trips),
response validation, asset-package resolution (marshalled to the logic
thread only for the async resolve await itself), l-string decode, and
full page prep — runs on an :attr:`~babase.App.threadpool` worker via
``DocUIController._process_request_in_bg``. Only the final prepped
page is pushed back to the logic thread for widget instantiation.

Code called from that flow (controller ``fulfill_request`` overrides
especially) should preserve this: do the heavy lifting where you are
called (the bg thread) rather than pushing work to the logic thread,
and never assume logic-thread context without checking.
"""

from bauiv1lib.docui._controller import DocUIController, DocUILocalAction
from bauiv1lib.docui._window import DocUIWindow

__all__ = [
    'DocUIController',
    'DocUIWindow',
    'DocUILocalAction',
]
