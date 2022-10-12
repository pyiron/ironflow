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
    width: int = 200
    height: int = 100
    font_title_size: int = 22
    font_title_color: str = "black"
    title_font: str = "serif"

    @property
    def title_font_string(self):
        return f"{self.font_title_size}px {self.title_font}"


@dataclass
class PortLayout(Layout, ABC):
    width: int = 20
    height: int = 10


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
    width: int = 100
    height: int = 30
    background_color: str = "darkgray"
