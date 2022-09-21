# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from ipycanvas import Canvas, hold_canvas
from time import time

from ryven.ironflow.canvas.canvas_widgets import (
    NodeWidget, PortWidget, CanvasWidget, ButtonNodeWidget, RepresentableNodeWidget, RepresentButtonWidget
)
from ryven.ironflow.canvas.layouts import NodeLayout

from typing import TYPE_CHECKING, Optional, Union
if TYPE_CHECKING:
    from ryven.ironflow.gui import GUI
    from ryven.NENV import Node
    Number = Union[int, float]
    from ryvencore.Flow import Flow

__author__ = "Joerg Neugebauer, Liam Huber"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "May 10, 2022"


class FlowCanvas:
    """
    A canvas for representing a particular Ryven script, which is determined at instantiation by the currently active
    gui script.

    Mouse behaviour:
        - Mouse click (down and release) on a node element or any child element selects that element
        - Mouse down, hold, and move on a node element or any child element selects the (parent) node and moves it
        - Mouse click on nothing clears selection
        - Mouse double-click on nothing creates a new node of the type currently selected in the node menu
        - Mouse click on a selected (pressed) port (button) deselects (unpresses) that port (button)
        - TODO: Mouse down, hold, and move on nothing draws a rectangle, everything inside is selected on release

    Keyboard behaviour: TODO
        - ESC: Deselect all.
        - Backspace/Delete:
            - If a node is selected, deletes it
            - If a port is selected, deletes all connections it is part of
    """
    def __init__(self, gui: GUI, flow: Optional[Flow] = None):
        self._gui = gui
        self.flow = flow if flow is not None else gui.flow

        self._standard_size = (1800, 800)
        self._zoom_factors = [0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00]
        self._zoom_index = 2
        self._width, self._height = self._get_size()

        self._canvas_color = "black"  # "#584f4e"
        self._connection_style = "white"
        self._connection_width = 3

        self._canvas = Canvas(width=self._width, height=self._height)
        self.canvas_restart()
        self._canvas.layout.width = "100%"
        self._canvas.layout.height = "auto"

        self._canvas.on_mouse_down(self.handle_mouse_down)
        self._canvas.on_mouse_up(self.handle_mouse_up)
        self._canvas.on_mouse_move(self.handle_mouse_move)
        self._canvas.on_key_down(self.handle_keyboard_event)

        self.objects_to_draw = []
        self.connections = []

        self.x = 0
        self.y = 0
        self._x_move_anchor = None
        self._y_move_anchor = None

        self._last_selected_object = None

        self._mouse_is_down = False
        self._last_mouse_down = time()
        self._double_click_speed = 0.25  # In seconds. TODO: Put this in a config somewhere

        self._object_to_gui_dict = {}

    @property
    def canvas(self):
        return self._canvas

    @property
    def gui(self):
        return self._gui

    def draw_connection(self, port_1: int, port_2: int) -> None:
        out = self._object_to_gui_dict[port_1]
        inp = self._object_to_gui_dict[port_2]

        canvas = self._canvas
        canvas.stroke_style = self._connection_style
        canvas.line_width = self._connection_width
        canvas.move_to(out.x, out.y)
        canvas.line_to(inp.x, inp.y)
        canvas.stroke()

    def _built_object_to_gui_dict(self) -> None:
        self._object_to_gui_dict = {}
        for n in self.objects_to_draw:
            self._object_to_gui_dict[n.node] = n
            for p in n.objects_to_draw:
                if isinstance(p, PortWidget):
                    self._object_to_gui_dict[p.port] = p

    def canvas_restart(self) -> None:
        self._canvas.clear()
        self._canvas.fill_style = self._canvas_color
        self._canvas.fill_rect(0, 0, self._width, self._height)

    def handle_keyboard_event(self, key: str, shift_key, ctrl_key, meta_key) -> None:
        pass  # TODO

    def deselect_all(self) -> None:
        [o.deselect() for o in self.objects_to_draw]
        self._last_selected_object = None
        self.redraw()

    def handle_mouse_down(self, x: Number, y: Number):
        self._mouse_is_down = True
        self._x_move_anchor = x
        self._y_move_anchor = y

        now = time()
        time_since_last_click = now - self._last_mouse_down
        self._last_mouse_down = now

        sel_object = self.get_element_at_xy(x, y)
        last_object = self._last_selected_object

        if sel_object is None:
            if last_object is not None:
                last_object.deselect()
            elif time_since_last_click < self._double_click_speed:
                self.add_node(x, y, self.gui.new_node_class)
                self._built_object_to_gui_dict()
        else:
            if sel_object == last_object and time_since_last_click < self._double_click_speed:
                sel_object = sel_object.on_double_click()
            else:
                sel_object = sel_object.on_click(last_object)

        self._last_selected_object = sel_object

        self.redraw()

    def handle_mouse_up(self, x: Number, y: Number):
        self._mouse_is_down = False

    def get_element_at_xy(self, x_in: Number, y_in: Number) -> CanvasWidget | None:
        for o in self.objects_to_draw:
            if o.is_here(x_in, y_in):
                return o.get_element_at_xy(x_in, y_in)
        return None

    def get_selected_objects(self) -> list[CanvasWidget]:
        return [o for o in self.objects_to_draw if o.selected]

    def handle_mouse_move(self, x: Number, y: Number) -> None:
        if self._mouse_is_down:
            selected_objects = self.get_selected_objects()
            if len(selected_objects) > 0:
                with hold_canvas(self._canvas):
                    [o.set_x_y(x, y) for o in selected_objects]
                    self.redraw()
            else:
                self.x += x - self._x_move_anchor
                self.y += y - self._y_move_anchor
                self._x_move_anchor = x
                self._y_move_anchor = y
                self.redraw()

    def redraw(self) -> None:
        with hold_canvas(self._canvas):
            self.canvas_restart()
            [o.draw() for o in self.objects_to_draw]
            for c in self.flow.connections:
                self.draw_connection(c.inp, c.out)
        self.gui.node_presenter.draw()

    def load_node(self, x: Number, y: Number, node: Node) -> NodeWidget:
        layout = NodeLayout()

        if hasattr(node, "main_widget_class") and node.main_widget_class is not None:
            if isinstance(node.main_widget_class, str):
                node_class = eval(node.main_widget_class)
            elif issubclass(node.main_widget_class, NodeWidget):
                node_class = node.main_widget_class
            else:
                raise TypeError(f"main_widget_class {node.main_widget_class} not recognized")
        else:
            node_class = NodeWidget
        s = node_class(x=x, y=y, parent=self, layout=layout, node=node)

        self.objects_to_draw.append(s)
        return s

    def add_node(self, x: Number, y: Number, node: Node):
        n = self.flow.create_node(node)
        self.load_node(x, y, n)

        self.redraw()

    def delete_selected(self) -> None:
        for o in self.objects_to_draw:
            if o.selected:
                o.delete()
        self.redraw()

    def _get_size(self) -> tuple[int, int]:
        scale = self._zoom_factors[self._zoom_index]
        return int(self._standard_size[0] * scale), int(self._standard_size[1] * scale)

    def _zoom(self, zoom_index) -> None:
        if zoom_index != self._zoom_index:
            self._zoom_index = zoom_index
            self._width, self._height = self._get_size()
            self._canvas.width = self._width
            self._canvas.height = self._height
            self.redraw()
        else:
            self.gui._print("Zoom limit reached")

    def zoom_in(self) -> None:
        self._zoom(max(self._zoom_index - 1, 0))

    def zoom_out(self) -> None:
        self._zoom(min(self._zoom_index + 1, len(self._zoom_factors) - 1))
