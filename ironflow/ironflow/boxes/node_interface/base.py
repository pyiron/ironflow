# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from abc import ABC, abstractmethod
from ironflow.ironflow.boxes.base import Box
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ironflow.ironflow.gui import GUI
import ipywidgets as widgets


class NodeInterfaceBase(Box, ABC):
    box_class = widgets.Box

    def __init__(self):
        super().__init__()
        self.output = widgets.Output(layout={"width": "100%"})
        self.box.children = [self.output]

    @property
    def layout(self):
        return widgets.Layout(
            width="50%",
            border="1px solid black",
        )

    @abstractmethod
    def draw(self):
        pass

    def clear_output(self):
        self.output.clear_output()
