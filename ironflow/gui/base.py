# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Abstract class for high-level GUI objects
"""

from abc import ABC, abstractmethod

from ipywidgets import Box


class Screen(ABC):
    """
    Abstract class for high-level GUI objects
    """

    # Data methods

    @property
    @abstractmethod
    def screen(self) -> Box:
        pass

    def draw(self):
        return self.screen

    # UI methods
