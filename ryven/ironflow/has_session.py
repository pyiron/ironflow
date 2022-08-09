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
