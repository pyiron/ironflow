# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
A collection of layouts for various canvas widgets, i.e. pure representation zero logic.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


@dataclass
class Layout(ABC):
    width: int
    height: int
    background_color: str = "gray"
    font_size: int = 18
    font_color: str = "black"
    selected_color: str = "green"
    font: str = "serif"

    @property
    def font_string(self):
        return f"{self.font_size}px {self.font}"


@dataclass
class NodeLayout(Layout):
    width: int = 240
    height: int = 100
    font_size: int = 22
    title_box_height: int = 30
    updating_color: str = "red"
    max_title_chars: int = 14


@dataclass
class PortLayout(Layout, ABC):
    width: int = 20
    height: int = 20
    max_title_chars: int = 10


@dataclass
class DataPortLayout(PortLayout):
    valid_color: str = "lightgreen"
    valid_selected_color: str = "darkgreen"
    invalid_color: str = "red"
    invalid_selected_color: str = "darkred"


@dataclass
class ExecPortLayout(PortLayout):
    # Exec ports have no data, so are always valid
    valid_color: str = "lightblue"
    valid_selected_color: str = "darkblue"


@dataclass
class ButtonLayout(Layout):
    font_size: int = 16
    width: int = 60
    height: int = 20
    background_color: str = "darkgray"
    pressed_color: str = "dimgray"
