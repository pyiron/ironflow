# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from abc import ABC, abstractmethod
from ironflow.ironflow.boxes.base import Box
import ipywidgets as widgets

__author__ = "Liam Huber"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "Oct 7, 2022"


class NodeInterfaceBase(Box, ABC):
    box_class = widgets.Box

    def __init__(self):
        super().__init__()
        self.output = widgets.Output(layout={"width": "100%"})
        self.box.children = [self.output]

    @property
    def layout(self) -> widgets.Layout:
        return widgets.Layout(
            width="50%",
            border="1px solid black",
        )

    @abstractmethod
    def draw(self) -> None:
        pass

    def clear_output(self) -> None:
        self.output.clear_output()
