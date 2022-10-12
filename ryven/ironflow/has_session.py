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
from ryvencore import Session, Script, Flow
import warnings
from typing import Dict


class HasSession(ABC):
    """
    Methods and attributes to make it more convenient to interact with the underlying model, i.e. a Ryven session.
    """

    def __init__(self, session: Session):
        self._session = session
        self._active_script_index = 0

    @property
    def session(self) -> Session:
        return self._session

    @property
    def script(self) -> Script:
        return self.session.scripts[self._active_script_index]

    @property
    def flow(self) -> Flow:
        return self.script.flow

    def activate_script(self, i: int) -> None:
        if i > len(self.session.scripts):
            warnings.warn(
                f"Attempted to activate script {i}, but there are only {len(self.session.scripts)} available."
            )
        else:
            self._active_script_index = i

    def create_script(
            self,
            title: str = None,
            create_default_logs: bool = True,
            data: Dict = None):
        self.session.create_script(title=title, create_default_logs=create_default_logs, data=data)
        self.activate_script(-1)

    @property
    def n_scripts(self):
        return len(self.session.scripts)
