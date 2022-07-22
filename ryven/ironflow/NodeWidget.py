from __future__ import annotations

import numpy as np
from IPython.display import display

from typing import TYPE_CHECKING, Optional, Union, Dict, Any
if TYPE_CHECKING:
    from .CanvasObject import CanvasObject
    from ipycanvas import Canvas
    from ryven.NENV import Node
    Number = Union[int, float]
    from ryvencore.NodePort import NodePort

__author__ = "Joerg Neugebauer"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Joerg Neugebauer"
__email__ = "janssen@mpie.de"
__status__ = "production"
__date__ = "May 10, 2022"


class CanvasLayout:
    def __init__(
        self,
        width: int = 100,
        height: int = 60,
        font_size: int = 12,
        background_color: str = "blue",
        selected_color: str = "lightblue",
        font_color: str = "black",
        font_title_color: str = "black",
    ):
        self.width = width
        self.height = height
        self.background_color = background_color
        self.selected_color = selected_color
        self.font_size = font_size
        self.font_color = font_color
        self.font_title_color = font_title_color


class BaseCanvasWidget:
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Optional[Union[CanvasObject, BaseCanvasWidget]] = None,
            layout: Optional[CanvasLayout] = None,
            selected: bool = False
    ):
        self._x = x  # relative to parent
        self._y = y

        self.layout = layout

        self.parent = parent
        self.selected = selected

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
    def _canvas(self) -> Canvas:
        return self.parent._canvas

    def add_widget(self, widget: BaseCanvasWidget) -> None:
        if widget.parent is None:
            widget.parent = self
        if widget.layout is None:
            widget.layout = self.parent.layout

        self.objects_to_draw.append(widget)

    def set_x_y(self, x_in: Number, y_in: Number) -> None:
        self._x = x_in - self.width // 2
        self._y = y_in - self.height // 2

    def add_x_y(self, dx_in: Number, dy_in: Number) -> None:
        self._x += dx_in
        self._y += dy_in

    def draw_shape(self) -> None:
        self._canvas.fill_style = self.layout.background_color
        if self.selected:
            self._canvas.fill_style = self.layout.selected_color
        self._canvas.fill_rect(
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
                if o.is_selected(x_in, y_in):
                    return o.get_element_at_xy(x_in, y_in)
            return self
        else:
            return None

    def is_selected(self, x_in: Number, y_in: Number) -> bool:
        if self._is_at_xy(x_in, y_in):
            return True
        else:
            return False

    def set_selected(self, state: bool) -> None:
        self.selected = state


class PortWidget(BaseCanvasWidget):
    def __init__(
        self,
        x: Number,
        y: Number,
        radius: Number = 10,
        parent: Optional[Union[CanvasObject, BaseCanvasWidget]] = None,
        port: Optional[NodePort] = None,
        layout: Optional[CanvasLayout] = None,
        selected: bool = False,
        text_left: str = "",
    ):
        super().__init__(x, y, parent, layout, selected)

        self.radius = radius
        self.port = port
        self.text_left = text_left

    def draw_shape(self) -> None:
        self._canvas.fill_style = self.layout.background_color
        if self.selected:
            self._canvas.fill_style = self.layout.selected_color
        self._canvas.fill_circle(self.x, self.y, self.radius)
        self._canvas.font = "21px serif"
        self._canvas.fill_style = "black"
        self._canvas.fill_text(
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
            node: Node,
            parent: Optional[Union[CanvasObject, BaseCanvasWidget]] = None,
            layout: Optional[CanvasLayout] = None,
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
        self.layout_ports = CanvasLayout(
            width=20,
            height=10,
            background_color="lightgreen",
            selected_color="darkgreen",
        )

        if len(self.node.inputs) > 3:
            self._height = 200
        self.add_inputs()
        self.add_outputs()

    def draw_title(self, title: str) -> None:
        self._canvas.fill_style = "darkgray"
        self._canvas.fill_rect(self.x, self.y, self.width, self._title_box_height)
        self._canvas.font = f"{self.layout.font_size}px serif"
        self._canvas.fill_style = self.layout.font_title_color
        x = self.x + (self.width * 0.04)
        y = self.y + self._title_box_height - 8
        self._canvas.fill_text(title, x, y)

    def draw_value(self, val: Any, val_is_updated: bool = True) -> None:
        self._canvas.fill_style = self.layout.font_color
        self._canvas.font = f"{self.layout.font_size}px serif"
        x = self.x + (self.width * 0.3)
        y = (self.y + (self.height * 0.65),)
        self._canvas.fill_text(str(val), x, y)
        if val_is_updated:
            if ("matplotlib" in str(type(val))) or ("NGLWidget" in str(type(val))):
                self.parent.gui.out_plot.clear_output()
                with self.parent.gui.out_plot:
                    display(val)

    def _add_ports(
            self,
            radius: Number,
            inputs: Optional[Dict] = None,
            outputs: Optional[Dict] = None,
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
                        radius=radius,
                        parent=self,
                        port=data[i_port],
                        text_left=data[i_port].label_str,
                        layout=self.layout_ports,
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
            node: Node,
            parent: Optional[Union[CanvasObject, BaseCanvasWidget]] = None,
            layout: Optional[CanvasLayout] = None,
            selected: bool = False,
            port_radius: Number = 10,
    ):
        super().__init__(x, y, node, parent, layout, selected, port_radius)

        layout = CanvasLayout(width=100, height=30, background_color="darkgray")
        s = BaseCanvasWidget(50, 50, parent=self, layout=layout)
        s.handle_select = self.handle_button_select
        self.add_widget(s)

    def handle_button_select(self, button: ButtonNodeWidget) -> None:
        button.parent.node.exec_output(0)
        button.set_selected(False)
