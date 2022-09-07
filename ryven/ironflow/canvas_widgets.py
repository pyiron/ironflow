# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

import numpy as np
from IPython.display import display
from .layouts import Layout, NodeLayout, PortLayout, DataPortLayout, ExecPortLayout, ButtonLayout
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, Optional, Union, List, Any
if TYPE_CHECKING:
    from .flow_canvas import FlowCanvas
    from ryven.ironflow.gui import GUI
    from ipycanvas import Canvas
    from ryven.NENV import Node, NodeInputBP, NodeOutputBP
    Number = Union[int, float]
    from ryvencore.NodePort import NodePort
    from ryvencore.Flow import Flow


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


class CanvasWidget(ABC):
    """
    Parent class for all "widgets" that exist inside the scope of the flow canvas.
    """

    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Union[FlowCanvas, CanvasWidget],
            layout: Layout,
            selected: bool = False,
    ):
        self._x = x  # relative to parent
        self._y = y

        self.layout = layout
        self.parent = parent
        self._selected = selected

        self.objects_to_draw = []

        self._height = self.layout.height

    @abstractmethod
    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> Optional[CanvasWidget]:
        pass

    def on_double_click(self) -> Optional[CanvasWidget]:
        return self

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

    @property
    def gui(self) -> GUI:
        return self.parent.gui

    @property
    def flow(self) -> Flow:
        return self.parent.flow

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

    def get_element_at_xy(self, x_in: Number, y_in: Number) -> Union[CanvasWidget, None]:
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


class HideableWidget(CanvasWidget, ABC):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Union[FlowCanvas, CanvasWidget],
            layout: Layout,
            selected: bool = False,
            hidden_x: Optional[Number] = None,
            hidden_y: Optional[Number] = None
    ):
        super().__init__(x=x, y=y, parent=parent, layout=layout, selected=selected)
        self._hidden_x = hidden_x if hidden_x is not None else x
        self._hidden_y = hidden_y if hidden_y is not None else y
        self.visible = True

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

    def _is_at_xy(self, x_in: Number, y_in: Number) -> bool:
        if self.visible:
            return super()._is_at_xy(x_in=x_in, y_in=y_in)
        else:
            return False

    def draw(self) -> None:
        if self.visible:
            super().draw()


class PortWidget(HideableWidget):
    def __init__(
        self,
        x: Number,
        y: Number,
        parent: Union[FlowCanvas, CanvasWidget],
        layout: PortLayout,
        selected: bool = False,
        hidden_x: Optional[Number] = None,
        hidden_y: Optional[Number] = None,
        radius: Number = 10,
        port: Optional[NodePort] = None,
        text_left: str = "",
    ):
        super().__init__(
            x=x, y=y, parent=parent, layout=layout, selected=selected, hidden_x=hidden_x, hidden_y=hidden_y
        )

        self.radius = radius
        self.port = port
        self.text_left = text_left

    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> Optional[CanvasWidget]:
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


class NodeWidget(CanvasWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Union[FlowCanvas, CanvasWidget],
            layout: NodeLayout,
            node: Node,
            selected: bool = False,
            port_radius: Number = 10,
    ):
        super().__init__(x, y, parent, layout, selected)



        self.node = node
        self.title = node.title

        self.inputs = node.inputs
        self.outputs = node.outputs

        self.port_radius = port_radius
        self.port_layouts = {
            'data': DataPortLayout(),
            'exec': ExecPortLayout()
        }

        self._title_box_height = 30  # 0.3  # ratio with respect to height
        self._io_height = 1.33 * 2 * self.port_radius * max(len(self.node.inputs), len(self.node.outputs))
        self._height = self._io_height + self._title_box_height
        self.add_inputs()
        self.add_outputs()

    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> Optional[CanvasWidget]:
        if last_selected_object == self:
            return self
        else:
            if last_selected_object is not None:
                last_selected_object.deselect()
            self.select()
            try:
                self.gui.node_interface.draw_for_node(self.node)
                return self
            except Exception as e:
                self.gui._print(f"Failed to handle selection of {self} with exception {e}")
                self.gui.out_status.clear_output()
                self.deselect()
                return None

    def on_double_click(self) -> Optional[CanvasWidget]:
        self.delete()
        return None

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
        l_y = (self.height - y_min)

        if n_ports > 0:
            y_step = l_y / n_ports
            y_locs = (np.arange(n_ports) + 0.5) * y_step + y_min

            for i_port, y_port in enumerate(y_locs):
                self.add_widget(
                    PortWidget(
                        x,
                        y_port,
                        parent=self,
                        layout=self.port_layouts[data[i_port].type_],
                        hidden_x=x,
                        hidden_y=y_locs[0],
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

    def delete(self) -> None:
        for c in self.flow.connections[::-1]:  # Reverse to make sure we traverse whole thing even if we delete
            # TODO: Can we be more efficient than looping over all nodes?
            if (c.inp.node == self.node) or (c.out.node == self.node):
                self.flow.remove_connection(c)
        self.flow.remove_node(self.node)
        self.parent.objects_to_draw.remove(self)
        if self.gui.node_interface.node == self.node:
            self.gui.node_interface.draw_for_node(None)


class ButtonNodeWidget(NodeWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Union[FlowCanvas, CanvasWidget],
            layout: NodeLayout,
            node: Node,
            selected: bool = False,
            port_radius: Number = 10,
    ):
        super().__init__(x, y, parent, layout, node, selected, port_radius)

        layout = ButtonLayout()
        s = CanvasWidget(50, 50, parent=self, layout=layout)
        s.handle_select = self.handle_button_select
        self.add_widget(s)

    def handle_button_select(self, button: ButtonNodeWidget) -> None:
        button.parent.node.exec_output(0)
        button.deselect()


class ButtonWidget(CanvasWidget, ABC):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: NodeWidget,
            layout: ButtonLayout,
            selected: bool = False,
            title="Button",
    ):
        super().__init__(x, y, parent, layout, selected)
        self.title = title
        self.pressed = False

    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> Optional[CanvasWidget]:
        if self.pressed:
            self.pressed = False
            self.unpress()
        else:
            self.pressed = True
            self.press()
        self.deselect()
        return last_selected_object

    @abstractmethod
    def press(self):
        pass

    @abstractmethod
    def unpress(self):
        pass

    def draw_shape(self) -> None:
        self.canvas.fill_style = self.layout.pressed_color if self.pressed else self.layout.background_color
        self.canvas.fill_rect(
            self.x,  # - (self.width * 0.5),
            self.y,  # - (self.height * 0.5),
            self.width,
            self.height,
        )

    def draw_title(self) -> None:
        self.canvas.font = self.layout.font_string
        self.canvas.fill_style = self.layout.font_color
        x = self.x + (self.width * 0.1)
        y = self.y + (self.height * 0.05) + self.layout.font_size
        self.canvas.fill_text(self.title, x, y)

    def draw(self) -> None:
        self.draw_shape()
        self.draw_title()


class DisplayButtonWidget(ButtonWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: DisplayableNodeWidget,
            layout: ButtonLayout,
            selected: bool = False,
            title="PLOT",
    ):
        super().__init__(x, y, parent, layout, selected, title=title)

    def press(self):
        self.pressed = True
        self.parent.set_display()

    def unpress(self):
        self.pressed = False
        self.parent.clear_display()


class DisplayableNodeWidget(NodeWidget):
    """
    Has a `Display` button that sends a representation over to the `ryven.ironflow.Gui.GUI.out_plot` window.
    Display gets locked until the button is pressed again, or another node gets displayed.
    While displayed, display updates automatically on changes to input.
    """

    def __init__(
            self,
            x: Number,
            y: Number,
            parent: Union[FlowCanvas, CanvasWidget],
            layout: NodeLayout,
            node: Node,
            selected: bool = False,
            port_radius: Number = 10,
    ):
        super().__init__(x, y, parent, layout, node, selected, port_radius)

        button_layout = ButtonLayout()
        button_edge_offset = 5
        self.display_button = DisplayButtonWidget(
            x=self.width - button_layout.width - button_edge_offset,
            y=button_edge_offset,
            parent=self,
            layout=button_layout
        )
        self.add_widget(self.display_button)

    def set_display(self):
        if self.gui.displayed_node is not None:
            self.gui.displayed_node.display_button.unpress()
        self.node.displayed = True
        self.node.representation_updated = True
        self.gui.displayed_node = self

    def clear_display(self):
        self.node.displayed = False
        if self.gui.displayed_node == self:
            self.gui.out_plot.clear_output()
            self.gui.displayed_node = None

    def draw_display(self):
        """Send the node's representation to a separate GUI window"""
        self.parent.gui.out_plot.clear_output()
        with self.parent.gui.out_plot:
            for rep in self.node.representations:
                display(rep)
        self.node.representation_updated = False

    def draw(self):
        super().draw()
        if self.node.displayed and self.node.representation_updated:
            self.draw_display()

    def delete(self) -> None:
        self.clear_display()
        return super().delete()

