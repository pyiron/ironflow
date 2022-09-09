# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

import numpy as np
from IPython.display import display
from ryven.ironflow.layouts import Layout, NodeLayout, PortLayout, DataPortLayout, ExecPortLayout, ButtonLayout
from abc import ABC, abstractmethod
from ryvencore.NodePort import NodeInput, NodeOutput

from typing import TYPE_CHECKING, Optional, Union
if TYPE_CHECKING:
    from ryven.ironflow.flow_canvas import FlowCanvas
    from ryven.ironflow.gui import GUI
    from ipycanvas import Canvas
    from ryven.NENV import Node, NodeInputBP, NodeOutputBP
    Number = Union[int, float]
    from ryvencore.NodePort import NodePort
    from ryvencore.Flow import Flow


__author__ = "Joerg Neugebauer, Liam Huber"
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
    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> CanvasWidget | None:
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
        return x_coord < x_in < (x_coord + self.width) and y_coord < y_in < (y_coord + self.height)

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
        super().__init__(x=x, y=y, parent=parent, layout=layout, selected=selected, title=title)
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
    ):
        super().__init__(
            x=x,
            y=y,
            parent=parent,
            layout=layout,
            selected=selected,
            title=title if title is not None else port.label_str,
            hidden_x=hidden_x,
            hidden_y=hidden_y
        )

        self.radius = radius
        self.port = port

    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> PortWidget | None:
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
        self.canvas.fill_style = self.layout.selected_color if self.selected else self.layout.background_color
        self.canvas.fill_circle(self.x, self.y, self.radius)

    def draw_title(self) -> None:
        self.canvas.font = self.layout.font_string
        self.canvas.fill_style = self.layout.font_color
        self.canvas.fill_text(self.title, self.x + self.radius + 3, self.y + self.radius // 2)

    def _is_at_xy(self, x_in: Number, y_in: Number) -> bool:
        return (x_in - self.x) ** 2 + (y_in - self.y) ** 2 < self.radius ** 2


class NodeWidget(CanvasWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: FlowCanvas | CanvasWidget,
            layout: NodeLayout,
            node: Node,
            selected: bool = False,
            title: Optional[str] = None,
            port_radius: Number = 10,
    ):
        super().__init__(
            x=x,
            y=y,
            parent=parent,
            layout=layout,
            selected=selected,
            title=title if title is not None else node.title,
        )

        self.node = node
        self.inputs = node.inputs
        self.outputs = node.outputs

        self.port_radius = port_radius
        self.port_layouts = {
            'data': DataPortLayout(),
            'exec': ExecPortLayout()
        }

        self._title_box_height = self.layout.title_box_height
        n_ports_max = max(len(self.node.inputs), len(self.node.outputs))
        exec_port_i = np.where([p.type_ == "exec" for p in self.node.inputs])[0]
        n_ports_min = exec_port_i[-1] + 1 if len(exec_port_i) > 0 else 1
        subwidget_size_and_buffer = 1.33 * 2 * self.port_radius
        self._io_height = subwidget_size_and_buffer * n_ports_max
        self._exec_height = subwidget_size_and_buffer * n_ports_min
        self._expand_collapse_height = subwidget_size_and_buffer
        self._height = self._expanded_height

        y_step = (self._io_height + self._expand_collapse_height) / (n_ports_max + 1)
        self._port_y_locs = (np.arange(n_ports_max + 1) + 0.5) * y_step + self._title_box_height

        self.add_inputs()
        self.add_outputs()
        self.expand_button = ExpandButtonWidget(
            x=0.5 * self.width - self.port_radius,
            y=self._port_y_locs[0] - self.port_radius,
            parent=self,
            layout=ButtonLayout(),
            pressed=True,
            visible=False,
            size=2 * self.port_radius
        )
        self.add_widget(self.expand_button)
        self.collapse_button = CollapseButtonWidget(
            x=0.5 * self.width - self.port_radius,
            y=self._port_y_locs[-1] - self.port_radius,
            parent=self,
            layout=ButtonLayout(),
            pressed=False,
            visible=True,
            size=2 * self.port_radius
        )
        self.add_widget(self.collapse_button)

    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> NodeWidget | None:
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

    def on_double_click(self) -> None:
        self.delete()
        return None

    def draw_title(self) -> None:
        self.canvas.fill_style = self.node.color
        self.canvas.fill_rect(self.x, self.y, self.width, self._title_box_height)
        self.canvas.font = self.layout.font_string
        self.canvas.fill_style = self.layout.font_color
        x = self.x + (self.width * 0.04)
        y = self.y + self._title_box_height - 8
        self.canvas.fill_text(self.title, x, y)

    def _add_ports(
            self,
            radius: Number,
            inputs: Optional[list[NodeInputBP]] = None,
            outputs: Optional[list[NodeOutputBP]] = None,
            border: Number = 1.4,
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
        for i_port in range(n_ports):
            port = data[i_port]
            data_or_exec = port.type_
            self.add_widget(
                PortWidget(
                    x=x,
                    y=self._port_y_locs[i_port],
                    parent=self,
                    layout=self.port_layouts[data_or_exec],
                    port=port,
                    hidden_x=x,
                    hidden_y=self._port_y_locs[0],
                    radius=radius,
                )
            )
            if data_or_exec == "exec" and inputs is not None:
                button_layout = ButtonLayout()
                self.add_widget(
                    ExecButtonWidget(
                        x=x + radius,
                        y=self._port_y_locs[i_port] - 0.5 * button_layout.height,
                        parent=self,
                        layout=button_layout,
                        port=port
                    )
                )

    def add_inputs(self) -> None:
        self._add_ports(radius=self.port_radius, inputs=self.inputs)

    def add_outputs(self) -> None:
        self._add_ports(radius=self.port_radius, outputs=self.outputs)

    def delete(self) -> None:
        for c in self.flow.connections[::-1]:  # Reverse to make sure we traverse whole thing even if we delete
            # TODO: Can we be more efficient than looping over all nodes?
            if (c.inp.node == self.node) or (c.out.node == self.node):
                self.flow.remove_connection(c)
        self.flow.remove_node(self.node)
        self.parent.objects_to_draw.remove(self)
        if self.gui.node_interface.node == self.node:
            self.gui.node_interface.draw_for_node(None)

    @property
    def port_widgets(self) -> list[PortWidget]:
        return [o for o in self.objects_to_draw if isinstance(o, PortWidget)]

    @property
    def _expanded_height(self) -> Number:
        return self._title_box_height + self._io_height + self._expand_collapse_height

    @property
    def _collapsed_height(self) -> Number:
        return self._title_box_height + max(self._expand_collapse_height, self._exec_height)

    def expand_io(self):
        self._height = self._expanded_height
        for o in self.port_widgets:
            o.show()
        self.collapse_button.unpress()

    def collapse_io(self):
        self._height = self._collapsed_height
        for o in self.port_widgets:
            o.hide()
        self.expand_button.unpress()


class ButtonNodeWidget(NodeWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: FlowCanvas | CanvasWidget,
            layout: NodeLayout,
            node: Node,
            selected: bool = False,
            title: Optional[str] = None,
            port_radius: Number = 10,
    ):
        super().__init__(
            x=x, y=y, parent=parent, layout=layout, node=node, selected=selected, title=title, port_radius=port_radius
        )

        button_layout = ButtonLayout()
        self.exec_button = ExecButtonWidget(
            x=0.8 * (self.width - button_layout.width),
            y=self._port_y_locs[0] - 0.5 * button_layout.height,
            parent=self,
            layout=button_layout,
            port=self.node.outputs[0],
        )
        self.add_widget(self.exec_button)


class ButtonWidget(CanvasWidget, ABC):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: NodeWidget,
            layout: ButtonLayout,
            selected: bool = False,
            title: str = "Button",
            pressed: Optional[bool] = False,
    ):
        super().__init__(x, y, parent, layout, selected)
        self.title = title
        self.pressed = pressed

    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> CanvasWidget | None:
        if self.pressed:
            self.unpress()
        else:
            self.press()
        self.deselect()
        return last_selected_object
    
    def press(self):
        self.pressed = True
        self.on_pressed()
        
    def unpress(self):
        self.pressed = False
        self.on_unpressed()

    @abstractmethod
    def on_pressed(self):
        pass

    @abstractmethod
    def on_unpressed(self):
        pass

    def draw_shape(self) -> None:
        self.canvas.fill_style = self.layout.pressed_color if self.pressed else self.layout.background_color
        self.canvas.fill_rect(
            self.x,
            self.y,
            self.width,
            self.height,
        )

    def draw_title(self) -> None:
        self.canvas.font = self.layout.font_string
        self.canvas.fill_style = self.layout.font_color
        x = self.x + (self.width * 0.1)
        y = self.y + (self.height * 0.05) + self.layout.font_size
        self.canvas.fill_text(self.title, x, y)


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

    def on_pressed(self):
        self.parent.set_display()

    def on_unpressed(self):
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
            parent: FlowCanvas | CanvasWidget,
            layout: NodeLayout,
            node: Node,
            selected: bool = False,
            title: Optional[str] = None,
            port_radius: Number = 10,
    ):
        super().__init__(
            x=x,
            y=y,
            parent=parent,
            layout=layout,
            node=node,
            selected=selected,
            title=title,
            port_radius=port_radius,
        )

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


class ExpandCollapseButtonWidget(ButtonWidget, HideableWidget, ABC):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: NodeWidget,
            layout: ButtonLayout,
            selected: bool = False,
            pressed: bool = False,
            visible: bool = True,
            title: Optional[str] = None,
            size: Optional[Number] = None,
    ):
        if size is not None:
            layout.width = size
            layout.height = size
        layout.background_color = parent.node.color
        layout.pressed_color = parent.node.color

        ButtonWidget.__init__(self, x=x, y=y, parent=parent, layout=layout, selected=selected, title=title,
                              pressed=pressed)
        HideableWidget.__init__(self, x=x, y=y, parent=parent, layout=layout, selected=selected, title=title,
                                visible=visible)

    def on_pressed(self):
        self.hide()

    def on_unpressed(self):
        self.show()

    def draw_shape(self) -> None:
        self.canvas.fill_style = self.layout.pressed_color if self.pressed else self.layout.background_color
        self.canvas.fill_polygon(self._points)

    @property
    @abstractmethod
    def _points(self) -> list[tuple[Number, Number]]:
        pass


class ExpandButtonWidget(ExpandCollapseButtonWidget):
    @property
    def _points(self) -> list[tuple[Number, Number]]:
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + 0.5 * self.width, self.y + self.height)
        ]

    def on_pressed(self):
        super().on_pressed()
        self.parent.expand_io()


class CollapseButtonWidget(ExpandCollapseButtonWidget):
    @property
    def _points(self) -> list[tuple[Number, Number]]:
        return [
            (self.x, self.y + self.height),
            (self.x + 0.5 * self.width, self.y),
            (self.x + self.width, self.y + self.height)
        ]

    def on_pressed(self):
        super().on_pressed()
        self.parent.collapse_io()


class ExecButtonWidget(ButtonWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: NodeWidget,
            layout: ButtonLayout,
            port: NodePort,
            selected: bool = False,
            title: str = "Exec",
            pressed: Optional[bool] = False,
    ):
        super().__init__(
            x=x,
            y=y,
            parent=parent,
            layout=layout,
            selected=selected,
            title=port.label_str if port.label_str != '' else title,
            pressed=pressed
        )
        self.port = port

    def on_pressed(self):
        self.unpress()
        if isinstance(self.port, NodeInput):
            self.port.update()
        elif isinstance(self.port, NodeOutput):
            self.port.exec()

    def on_unpressed(self):
        pass
