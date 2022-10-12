# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

import numpy as np
from IPython.display import display
from .layouts import Layout, NodeLayout, PortLayout, DataPortLayout, ExecPortLayout, ButtonLayout

from typing import TYPE_CHECKING, Optional, Union, List, Any
if TYPE_CHECKING:
    from .FlowCanvas import FlowCanvas
    from ipycanvas import Canvas
    from ryven.NENV import Node, NodeInputBP, NodeOutputBP
    Number = Union[int, float]
    from ryvencore.NodePort import NodePort

__author__ = "Joerg Neugebauer"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "May 10, 2022"


class BaseCanvasWidget:
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Union[FlowCanvas, BaseCanvasWidget],
            layout: Layout,
            selected: bool = False
    ):
        self._x = x  # relative to parent
        self._y = y

        self.layout = layout
        self.parent = parent
        self._selected = selected

        self.objects_to_draw = []

        self._height = self.layout.height

    def _init_after_parent_assignment(self):
        pass

    @property
    def width(self) -> int:
        return self.layout.width

    @property
    def height(self) -> int:
        return self._height

    @property
    def x(self) -> Number:
        return self.parent.x + self._x  # - self.parent.width//2

    @property
    def y(self) -> Number:
        return self.parent.y + self._y  # - self.parent.height//2

    @property
    def canvas(self) -> Canvas:
        return self.parent.canvas

    def add_widget(self, widget: BaseCanvasWidget) -> None:
        self.objects_to_draw.append(widget)

    def set_x_y(self, x_in: Number, y_in: Number) -> None:
        self._x = x_in - self.width // 2
        self._y = y_in - self.height // 2

    def add_x_y(self, dx_in: Number, dy_in: Number) -> None:
        self._x += dx_in
        self._y += dy_in

    def draw_shape(self) -> None:
        self.canvas.fill_style = self.layout.selected_color if self.selected else self.layout.background_color
        self.canvas.fill_rect(
            self.x,  # - (self.width * 0.5),
            self.y,  # - (self.height * 0.5),
            self.width,
            self.height,
        )

    def draw(self) -> None:
        self.draw_shape()
        for o in self.objects_to_draw:
            o.draw()

    def _is_at_xy(self, x_in: Number, y_in: Number) -> bool:
        x_coord = self.x  # - (self.width * 0.5)
        y_coord = self.y  # - (self.height * 0.5)
        return x_coord < x_in < (x_coord + self.width) and y_coord < y_in < (y_coord + self.height)

    def get_element_at_xy(self, x_in: Number, y_in: Number) -> Union[BaseCanvasWidget, None]:
        if self._is_at_xy(x_in, y_in):
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


class PortWidget(BaseCanvasWidget):
    def __init__(
        self,
        x: Number,
        y: Number,
        parent: Union[FlowCanvas, BaseCanvasWidget],
        layout: PortLayout,
        radius: Number = 10,
        port: Optional[NodePort] = None,
        selected: bool = False,
        text_left: str = "",
    ):
        super().__init__(x, y, parent, layout, selected)

        self.radius = radius
        self.port = port
        self.text_left = text_left

    def draw_shape(self) -> None:
        self.canvas.fill_style = self.layout.background_color
        if self.selected:
            self.canvas.fill_style = self.layout.selected_color
        self.canvas.fill_circle(self.x, self.y, self.radius)
        self.canvas.font = self.layout.font_string
        self.canvas.fill_style = self.layout.font_color
        self.canvas.fill_text(
            self.text_left, self.x + self.radius + 3, self.y + self.radius // 2
        )

    def _is_at_xy(self, x_in: Number, y_in: Number) -> bool:
        x_coord = self.x - self.radius
        y_coord = self.y - self.radius

        return x_coord < x_in < (x_coord + 2 * self.radius) and y_coord < y_in < (y_coord + 2 * self.radius)


class NodeWidget(BaseCanvasWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Union[FlowCanvas, BaseCanvasWidget],
            layout: NodeLayout,
            node: Node,
            selected: bool = False,
            port_radius: Number = 10,
    ):
        super().__init__(x, y, parent, layout, selected)

        self._title_box_height = 30  # 0.3  # ratio with respect to height

        self.node = node
        self.title = node.title

        self.inputs = node.inputs
        self.outputs = node.outputs

        self.port_radius = port_radius
        self.port_layouts = {
            'data': DataPortLayout(),
            'exec': ExecPortLayout()
        }

        if len(self.node.inputs) > 3:
            self._height = 200  # TODO: Make height programatically dependent on content
        self.add_inputs()
        self.add_outputs()

    def draw_title(self, title: str) -> None:
        self.canvas.fill_style = self.node.color
        self.canvas.fill_rect(self.x, self.y, self.width, self._title_box_height)
        self.canvas.font = self.layout.title_font_string
        self.canvas.fill_style = self.layout.font_title_color
        x = self.x + (self.width * 0.04)
        y = self.y + self._title_box_height - 8
        self.canvas.fill_text(title, x, y)

    def draw_value(self, val: Any, val_is_updated: bool = True) -> None:
        self.canvas.fill_style = self.layout.font_color
        self.canvas.font = self.layout.title_font_string
        x = self.x + (self.width * 0.3)
        y = (self.y + (self.height * 0.65),)
        self.canvas.fill_text(str(val), x, y)
        if val_is_updated:
            if ("matplotlib" in str(type(val))) or ("NGLWidget" in str(type(val))):
                self.parent.gui.out_plot.clear_output()
                with self.parent.gui.out_plot:
                    display(val)

    def _add_ports(
            self,
            radius: Number,
            inputs: Optional[List[NodeInputBP]] = None,
            outputs: Optional[List[NodeOutputBP]] = None,
            border: Number = 1.4,
            text: str = ""
    ) -> None:
        if inputs is not None:
            x = radius * border
            data = inputs
        elif outputs is not None:
            x = self.width - radius * border
            data = outputs
        else:
            return

        n_ports = len(data)

        y_min = self._title_box_height
        d_y = self.height - y_min

        if n_ports > 0:
            i_y_vec = (np.arange(n_ports) + 1 / 2) / n_ports

            for i_port, y_port in enumerate(i_y_vec):
                self.add_widget(
                    PortWidget(
                        x,
                        y_port * d_y + y_min,
                        parent=self,
                        layout=self.port_layouts[data[i_port].type_],
                        port=data[i_port],
                        radius=radius,
                        text_left=data[i_port].label_str,
                    )
                )

    def add_inputs(self) -> None:
        self._add_ports(radius=self.port_radius, inputs=self.inputs)

    def add_outputs(self) -> None:
        self._add_ports(radius=self.port_radius, outputs=self.outputs)

    def draw(self) -> None:
        super().draw()
        if self.title is not None:
            self.draw_title(self.title)

        if hasattr(self.node, "val"):
            val_is_updated = True
            if hasattr(self.node, "_val_is_updated"):
                val_is_updated = self.node._val_is_updated

            self.draw_value(self.node.val, val_is_updated)
            self.node._val_is_updated = False

        for o in self.objects_to_draw:
            o.draw()


class ButtonNodeWidget(NodeWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Union[FlowCanvas, BaseCanvasWidget],
            layout: ButtonLayout,
            node: Node,
            selected: bool = False,
            port_radius: Number = 10,
    ):
        super().__init__(x, y, parent, layout, node, selected, port_radius)

        layout = ButtonLayout()
        s = BaseCanvasWidget(50, 50, parent=self, layout=layout)
        s.handle_select = self.handle_button_select
        self.add_widget(s)

    def handle_button_select(self, button: ButtonNodeWidget) -> None:
        button.parent.node.exec_output(0)
        button.deselect()
