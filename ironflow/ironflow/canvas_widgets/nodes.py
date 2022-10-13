# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Canvas representations of the nodes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np

from ironflow.ironflow.canvas_widgets.base import CanvasWidget
from ironflow.ironflow.canvas_widgets.buttons import (
    RepresentButtonWidget, ExpandButtonWidget, CollapseButtonWidget, ExecButtonWidget
)
from ironflow.ironflow.canvas_widgets.layouts import NodeLayout, DataPortLayout, ExecPortLayout, ButtonLayout
from ironflow.ironflow.canvas_widgets.ports import PortWidget

if TYPE_CHECKING:
    from ironflow.ironflow.canvas_widgets.flow import FlowCanvas
    from ironflow.NENV import Node, NodeInputBP, NodeOutputBP
    from ironflow.ironflow.canvas_widgets.base import Number


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

        # Register callback to change color on updates
        self.node.widget = self
        self._updating = False
        self.node.before_update.connect(self._draw_before_updating)
        self.node.after_update.connect(self._draw_after_updating)

        self.port_radius = port_radius
        self.port_layouts = {
            'data': DataPortLayout(),
            'exec': ExecPortLayout()
        }

        n_ports_max = max(len(self.node.inputs), len(self.node.outputs)) + 1  # Includes the expand/collapse button
        exec_port_i = np.where([p.type_ == "exec" for p in self.node.inputs])[0]
        n_ports_min = exec_port_i[-1] + 1 if len(exec_port_i) > 0 else 1
        subwidget_size_and_buffer = 1.33 * 2 * self.port_radius
        self._title_box_height = self.layout.title_box_height
        self._max_body_height = subwidget_size_and_buffer * n_ports_max
        self._min_body_height = subwidget_size_and_buffer * n_ports_min
        self._expanded_height = self._title_box_height + self._max_body_height
        self._collapsed_height = self._title_box_height + self._min_body_height
        self._height = self._expanded_height

        y_step = self._max_body_height / n_ports_max
        self._subwidget_y_locs = (np.arange(n_ports_max) + 0.5) * y_step + self._title_box_height

        self.add_inputs()
        self.add_outputs()
        self.expand_button = ExpandButtonWidget(
            x=0.5 * self.width - self.port_radius,
            y=self._subwidget_y_locs[0] - self.port_radius,
            parent=self,
            layout=ButtonLayout(),
            pressed=True,
            visible=False,
            size=2 * self.port_radius
        )
        self.add_widget(self.expand_button)
        self.collapse_button = CollapseButtonWidget(
            x=0.5 * self.width - self.port_radius,
            y=self._subwidget_y_locs[-1] - self.port_radius,
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
                self.gui.open_node_control(self.node)
                return self
            except Exception as e:
                self.gui.print(f"Failed to handle selection of {self} with exception {e}")
                self.gui.close_node_control()
                self.deselect()
                return None

    def on_double_click(self) -> None:
        self.delete()
        return None

    @staticmethod
    def _draw_before_updating(node: Node, inp: int) -> None:
        node.widget.gui.print(f"Updating {node}")
        node.widget._updating = True
        node.widget.draw()

    @staticmethod
    def _draw_after_updating(node: Node, inp: int) -> None:
        node.widget._updating = False
        node.widget.draw()

    @property
    def color(self) -> str:
        if self._updating:
            return self.layout.updating_color
        elif self.selected:
            return self.layout.selected_color
        else:
            return self.layout.background_color

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
                    y=self._subwidget_y_locs[i_port],
                    parent=self,
                    layout=self.port_layouts[data_or_exec],
                    port=port,
                    hidden_x=x,
                    hidden_y=self._subwidget_y_locs[0],
                    radius=radius,
                )
            )
            if data_or_exec == "exec" and inputs is not None:
                button_layout = ButtonLayout()
                self.add_widget(
                    ExecButtonWidget(
                        x=x + radius,
                        y=self._subwidget_y_locs[i_port] - 0.5 * button_layout.height,
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
        self.gui.ensure_node_not_controlled(self.node)

    def deselect(self) -> None:
        super().deselect()
        self.gui.ensure_node_not_controlled(self.node)

    @property
    def port_widgets(self) -> list[PortWidget]:
        return [o for o in self.objects_to_draw if isinstance(o, PortWidget)]

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
            y=self._subwidget_y_locs[0] - 0.5 * button_layout.height,
            parent=self,
            layout=button_layout,
            port=self.node.outputs[0],
        )
        self.add_widget(self.exec_button)


class RepresentableNodeWidget(NodeWidget):
    """
    Has a `SHOW` button that sends a representation over to the `ryven.ironflow.Gui.GUI.node_presenter.output`
    window.
    Display gets locked until the button is pressed again, the node is deleted, or another node gets displayed.
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
        self.represent_button = RepresentButtonWidget(
            x=self.width - button_layout.width - button_edge_offset,
            y=button_edge_offset,
            parent=self,
            layout=button_layout
        )
        self.add_widget(self.represent_button)

    def delete(self) -> None:
        self.gui.ensure_node_not_presented(self)
        return super().delete()


