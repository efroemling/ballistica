# Released under the MIT License. See LICENSE for details.
#
"""Declarative UI system.

A high level way to build UIs that lives as a layer on top of engine
apis such as :mod:`bauiv1`. UIs can easily be serialized to json data
and be provided by webservers or other local or remote sources.
"""

from bacommon.docui._docui import (
    DocUIRequest,
    DocUIRequestTypeID,
    UnknownDocUIRequest,
    DocUIResponse,
    DocUIResponseTypeID,
    UnknownDocUIResponse,
    DocUIWebRequest,
    DocUIWebResponse,
)

__all__ = [
    'DocUIRequest',
    'DocUIRequestTypeID',
    'UnknownDocUIRequest',
    'DocUIResponse',
    'DocUIResponseTypeID',
    'UnknownDocUIResponse',
    'DocUIWebRequest',
    'DocUIWebResponse',
]
