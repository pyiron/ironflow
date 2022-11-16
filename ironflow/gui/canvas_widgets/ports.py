# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Canvas widgets for ryven IO ports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional

from ironflow.gui.canvas_widgets.base import HideableWidget, CanvasWidget
from ironflow.gui.canvas_widgets.layouts import PortLayout

if TYPE_CHECKING:
    from ironflow.gui.canvas_widgets.flow import FlowCanvas
    from ironflow.gui.canvas_widgets.base import Number
    from ironflow.model import NodePort


class PortWidget(HideableWidget):
    def __init__(
        self,
        x: Number,
        y: Number,
        parent: FlowCanvas | CanvasWidget,
        layout: PortLayout,
        port: NodePort,
        selected: bool = False,
        title: Optional[str] = None,
        hidden_x: Optional[Number] = None,
        hidden_y: Optional[Number] = None,
        radius: Number = 10,
        title_alignment: Literal["start", "end"] = "start",
    ):
        super().__init__(
            x=x,
            y=y,
            parent=parent,
            layout=layout,
            selected=selected,
            title=title if title is not None else port.label_str,
            hidden_x=hidden_x,
            hidden_y=hidden_y,
        )

        self.radius = radius
        self.port = port
        self.title_alignment = title_alignment

    def on_click(
        self, last_selected_object: Optional[CanvasWidget]
    ) -> PortWidget | None:
        if last_selected_object == self:
            self.deselect()
            return None
        elif isinstance(last_selected_object, PortWidget):
            self.flow.connect_nodes(last_selected_object.port, self.port)
            self.deselect_all()
            return None
        else:
            if last_selected_object is not None:
                last_selected_object.deselect()
            self.select()
            return self

    def draw_shape(self) -> None:
        self.canvas.fill_style = (
            self.layout.selected_color
            if self.selected
            else self.layout.background_color
        )
        self.canvas.fill_circle(self.x, self.y, self.radius)

    def draw_title(self) -> None:
        self.canvas.font = self.layout.font_string
        self.canvas.fill_style = self.layout.font_color
        shift_magnitude = self.radius + 3
        if self.title_alignment == "start":
            shift = shift_magnitude
        elif self.title_alignment == "end":
            shift = -shift_magnitude
        else:
            raise ValueError(
                f"Title alignment {self.title_alignment} not recognized, please choose start or end"
            )
        self.canvas.text_align = self.title_alignment
        self.canvas.fill_text(
            self.title[: self.layout.max_title_chars],
            self.x + shift,
            self.y + self.radius // 2,
        )
        self.canvas.text_align = "start"  # Revert to default after writing

    def _is_at_xy(self, x_in: Number, y_in: Number) -> bool:
        return (x_in - self.x) ** 2 + (y_in - self.y) ** 2 < self.radius**2
