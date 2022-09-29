# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.


from __future__ import annotations

import ipywidgets as widgets
from abc import ABC, abstractmethod


class Box(ABC):
    @property
    @abstractmethod
    def box(self) -> widgets.Box:
        pass
