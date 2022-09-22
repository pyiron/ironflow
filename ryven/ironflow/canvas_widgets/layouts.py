# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations
from abc import ABC
from dataclasses import dataclass

__author__ = "Liam Huber"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "July 25, 2022"


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
    width: int = 200
    height: int = 100
    font_size: int = 22
    title_box_height: int = 30


@dataclass
class PortLayout(Layout, ABC):
    width: int = 20
    height: int = 20


@dataclass
class DataPortLayout(PortLayout):
    background_color: str = "lightgreen"
    selected_color: str = "darkgreen"


@dataclass
class ExecPortLayout(PortLayout):
    background_color: str = "lightblue"
    selected_color: str = "darkblue"


@dataclass
class ButtonLayout(Layout):
    font_size: int = 16
    width: int = 60
    height: int = 20
    background_color: str = "darkgray"
    pressed_color: str = "dimgray"