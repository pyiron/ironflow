# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Shared code among various canvas widgets.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Union

Number = Union[int, float]
if TYPE_CHECKING:
    from ipycanvas import Canvas
    from ironflow.gui.workflows.canvas_widgets.flow import FlowCanvas
    from ironflow.gui.workflows.screen import WorkflowsGUI
    from ironflow.model.flow import Flow
    from ironflow.model.model import HasSession
    from ironflow.gui.workflows.canvas_widgets.layouts import Layout


class CanvasWidget(ABC):
    """
    Parent class for all "widgets" that exist inside the scope of the flow canvas.
    """

    def __init__(
        self,
        x: Number,
        y: Number,
        parent: FlowCanvas | CanvasWidget,
        layout: Layout,
        selected: bool = False,
        title: Optional[str] = None,
    ):
        self._x = x  # relative to parent
        self._y = y

        self.layout = layout
        self.parent = parent
        self._selected = selected
        self.title = title

        self.objects_to_draw = []

        self._height = self.layout.height

    @abstractmethod
    def on_click(
        self, last_selected_object: Optional[CanvasWidget]
    ) -> CanvasWidget | None:
        pass

    def on_double_click(self) -> CanvasWidget | None:
        return self

    @property
    def width(self) -> int:
        return self.layout.width

    @property
    def height(self) -> int:
        return self._height

    @property
    def x(self) -> Number:
        return self.parent.x + self._x

    @property
    def y(self) -> Number:
        return self.parent.y + self._y

    @property
    def canvas(self) -> Canvas:
        return self.parent.canvas

    @property
    def model(self) -> HasSession:
        return self.parent.model

    @property
    def screen(self) -> WorkflowsGUI:
        return self.parent.screen

    @property
    def flow(self) -> Flow:
        return self.parent.flow

    @property
    def flow_canvas(self) -> FlowCanvas:
        return self.parent.flow_canvas

    def deselect_all(self) -> None:
        return self.parent.deselect_all()

    def add_widget(self, widget: CanvasWidget) -> None:
        self.objects_to_draw.append(widget)

    def set_x_y(self, x_in: Number, y_in: Number) -> None:
        self._x = x_in - self.width // 2
        self._y = y_in - self.height // 2

    def add_x_y(self, dx_in: Number, dy_in: Number) -> None:
        self._x += dx_in
        self._y += dy_in

    @property
    def color(self) -> str:
        return (
            self.layout.selected_color
            if self.selected
            else self.layout.background_color
        )

    def draw_shape(self) -> None:
        self.canvas.fill_style = self.color
        self.canvas.fill_rect(
            self.x,
            self.y,
            self.width,
            self.height,
        )

    @abstractmethod
    def draw_title(self) -> None:
        pass

    def draw(self) -> None:
        self.draw_shape()
        if self.title is not None:
            self.draw_title()
        for o in self.objects_to_draw:
            o.draw()

    def _is_at_xy(self, x_in: Number, y_in: Number) -> bool:
        x_coord = self.x
        y_coord = self.y
        return x_coord < x_in < (x_coord + self.width) and y_coord < y_in < (
            y_coord + self.height
        )

    def get_element_at_xy(self, x_in: Number, y_in: Number) -> CanvasWidget | None:
        if self.is_here(x_in, y_in):
            for o in self.objects_to_draw:
                if o.is_here(x_in, y_in):
                    return o.get_element_at_xy(x_in, y_in)
            return self
        else:
            return None

    def is_here(self, x_in: Number, y_in: Number) -> bool:
        return self._is_at_xy(x_in, y_in)

    def select(self) -> None:
        self._selected = True

    def deselect(self) -> None:
        self._selected = False
        [o.deselect() for o in self.objects_to_draw]

    @property
    def selected(self):
        return self._selected


class HideableWidget(CanvasWidget, ABC):
    def __init__(
        self,
        x: Number,
        y: Number,
        parent: FlowCanvas | CanvasWidget,
        layout: Layout,
        selected: bool = False,
        title: Optional[str] = None,
        visible: bool = True,
        hidden_x: Optional[Number] = None,
        hidden_y: Optional[Number] = None,
    ):
        super().__init__(
            x=x, y=y, parent=parent, layout=layout, selected=selected, title=title
        )
        self._hidden_x = hidden_x if hidden_x is not None else x
        self._hidden_y = hidden_y if hidden_y is not None else y
        self.visible = visible

    @property
    def hidden_x(self) -> Number:
        return self.parent.x + self._hidden_x

    @property
    def hidden_y(self) -> Number:
        return self.parent.y + self._hidden_y

    @property
    def x(self) -> Number:
        if self.visible:
            return self.parent.x + self._x
        else:
            return self.hidden_x

    @property
    def y(self) -> Number:
        if self.visible:
            return self.parent.y + self._y
        else:
            return self.hidden_y

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def is_here(self, x_in: Number, y_in: Number) -> bool:
        if self.visible:
            return self._is_at_xy(x_in=x_in, y_in=y_in)
        else:
            return False

    def draw(self) -> None:
        if self.visible:
            super().draw()
