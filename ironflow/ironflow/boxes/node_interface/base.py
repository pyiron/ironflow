# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ironflow.ironflow.gui import GUI
import ipywidgets as widgets


class NodeInterfaceBase(ABC):
    def __init__(self):
        self._output = None

    @property
    def layout(self):
        """Overwrite in children as desired"""
        return widgets.Layout(
            width="50%",
            border="1px solid black",
        )

    @abstractmethod
    def draw(self):
        pass

    @property
    def output(self) -> widgets.Output:
        if self._output is None:
            self._output = widgets.Output(layout=self.layout)
        return self._output

    def clear_output(self):
        self.output.clear_output()
