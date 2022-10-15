# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Shared code among representations of node data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import ipywidgets as widgets

from ironflow.gui.boxes.base import Box


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
