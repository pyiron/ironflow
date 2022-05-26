# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

"""
Quality-of-life access to the underlying Ryven graph.
"""

__author__ = "Liam Huber"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "development"
__date__ = "May 26, 2022"

from abc import ABC
from ryvencore import Session, Script, Flow, Node
from ryvencore.Connection import Connection
from typing import List, Type


class HasSession(ABC):
    """
    A convenience parent for classes that interact with a single-script Ryven session.
    """

    def __init__(self, session):
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    @property
    def script(self) -> Script:
        return self.session.scripts[0]

    @property
    def flow(self) -> Flow:
        return self.script.flow

    @property
    def nodes(self) -> List[Type[Node]]:
        return self.flow.nodes

    @property
    def connections(self) -> List[Type[Connection]]:
        return self.flow.connections
