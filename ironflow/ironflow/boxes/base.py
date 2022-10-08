# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

import ipywidgets as widgets
from abc import ABC, abstractmethod
from typing import Type


class Box(ABC):
    def __init__(self):
        self._box = self.box_class([], layout=self.layout)

    @property
    @abstractmethod
    def box_class(self) -> Type[widgets.Box]:
        """E.g. `widgets.HBox` or `widgets.VBox`"""
        pass

    @property
    def box(self) -> widgets.Box:
        return self._box

    @property
    def layout(self) -> widgets.Layout:
        """An empty layout. Overwrite in children as desired."""
        return widgets.Layout()

    def clear(self):
        self.box.children = []

