from __future__ import annotations
from typing import Optional


def layout_factory(
        width: int = 100,
        height: int = 60,
        font_size: int = 18,
        background_color: str = "gray",
        selected_color: str = "green",
        font_color: str = "black",
        font_title_color: str = "black",
        font_title_size: int = 22,
        docstring: Optional[str] = None,
):
    class Layout:
        def __init__(
                self,
                width: int = width,
                height: int = height,
                font_size: int = font_size,
                background_color: str = background_color,
                selected_color: str = selected_color,
                font_color: str = font_color,
                font_title_color: str = font_title_color,
                font_title_size: int = font_title_size
        ):
            self.width = width
            self.height = height
            self.background_color = background_color
            self.selected_color = selected_color
            self.font_size = font_size
            self.font_color = font_color
            self.font_title_color = font_title_color
            self.font_title_size = font_title_size
    Layout.__doc__ = docstring
    return Layout


CanvasLayout = layout_factory()

NodeLayout = layout_factory(
    width=200,
    height=100
)

DataPortLayout = layout_factory(
    width=20,
    height=10,
    background_color="lightgreen",
    selected_color="darkgreen",
)

ExecPortLayout = layout_factory(
    width=20,
    height=10,
    background_color="lightblue",
    selected_color="darkblue",
)


ButtonLayout = layout_factory(
    width=100,
    height=30,
    background_color="darkgray",
)