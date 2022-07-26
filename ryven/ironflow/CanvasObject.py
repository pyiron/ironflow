from __future__ import annotations

from ipycanvas import Canvas, hold_canvas
from IPython.display import display
from time import time

from .NodeWidget import NodeWidget, PortWidget, BaseCanvasWidget, ButtonNodeWidget
from .layouts import NodeLayout
from .NodeWidgets import NodeWidgets
from .has_session import HasSession

from typing import TYPE_CHECKING, Optional, Union, List
if TYPE_CHECKING:
    from Gui import GUI
    from ryven.NENV import Node
    Number = Union[int, float]

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


class CanvasObject(HasSession):
    """

    Mouse behaviour:
        - Mouse click (down and release) on a node element or any child element selects that element
        - Mouse down, hold, and move on a node element or any child element selects the (parent) node and moves it
        - Mouse click on nothing clears selection
        - Mouse double-click on nothing creates a new node of the type currently selected in the node menu
        - TODO: Mouse down, hold, and move on nothing draws a rectangle, everything inside is selected on release

    Keyboard behaviour: TODO
        - ESC: Deselect all.
        - Backspace/Delete:
            - If a node is selected, deletes it
            - If a port is selected, deletes all connections it is part of
    """
    def __init__(self, gui: Optional[GUI] = None, width: int = 2000, height: int = 1000):
        self.gui = gui
        super().__init__(self.gui.session)
        self._width, self._height = width, height

        self._col_background = "black"  # "#584f4e"
        self._col_node_header = "blue"  # "#38a8a4"
        self._col_node_selected = "#9dcea6"
        self._col_node_unselected = "#dee7bc"

        self._font_size = 30
        self._node_box_size = 160, 70

        self._canvas = Canvas(width=width, height=height)
        self._canvas.fill_style = self._col_background
        self._canvas.fill_rect(0, 0, width, height)
        self._canvas.layout.width = "100%"
        self._canvas.layout.height = "auto"

        self.objects_to_draw = []
        self.connections = []

        self._canvas.on_mouse_down(self.handle_mouse_down)
        self._canvas.on_mouse_up(self.handle_mouse_up)
        self._canvas.on_mouse_move(self.handle_mouse_move)
        self._canvas.on_key_down(self.handle_keyboard_event)

        self.x = 0
        self.y = 0

        self._last_selected_object = None

        self._mouse_is_down = False
        self._last_mouse_down = time()
        self._double_click_speed = 0.2

        self._connection_in = None
        self._node_widget = None

        self._object_to_gui_dict = {}

    @property
    def canvas(self):
        return self._canvas

    def draw_connection(self, port_1: int, port_2: int) -> None:
        # i_out, i_in = path
        # out = self.objects_to_draw[i_out]
        # inp = self.objects_to_draw[i_in]
        out = self._object_to_gui_dict[port_1]
        inp = self._object_to_gui_dict[port_2]

        canvas = self._canvas
        canvas.stroke_style = "white"
        canvas.line_width = 3
        canvas.move_to(out.x, out.y)
        canvas.line_to(inp.x, inp.y)
        canvas.stroke()

    def _built_object_to_gui_dict(self) -> None:
        self._object_to_gui_dict = {}
        for n in self.objects_to_draw:
            self._object_to_gui_dict[n.node] = n
            for p in n.objects_to_draw:
                if hasattr(p, "port"):
                    self._object_to_gui_dict[p.port] = p

    def canvas_restart(self) -> None:
        self._canvas.clear()
        self._canvas.fill_style = self._col_background
        self._canvas.fill_rect(0, 0, self._width, self._height)

    def handle_keyboard_event(self, key: str, shift_key, ctrl_key, meta_key) -> None:
        pass  # TODO

    def set_connection(self, ind_node: int) -> None:
        if self._connection_in is None:
            self._connection_in = ind_node
        else:
            out = self.objects_to_draw[self._connection_in].node.outputs[0]
            inp = self.objects_to_draw[ind_node].node.inputs[-1]
            if self.flow.connect_nodes(inp, out) is None:
                i_con = self.connections.index([self._connection_in, ind_node])
                del self.connections[i_con]
            else:
                self.connections.append([self._connection_in, ind_node])

            self._connection_in = None
            self.deselect_all()

    def deselect_all(self) -> None:
        [o.deselect() for o in self.objects_to_draw]
        self.redraw()

    def handle_mouse_down(self, x: Number, y: Number):
        self._mouse_is_down = True
        now = time()
        time_since_last_click = now - self._last_mouse_down
        self._last_mouse_down = now

        sel_object = self.get_element_at_xy(x, y)
        last_object = self._last_selected_object

        # Case 1: Select something new
        if sel_object is not None and sel_object != last_object:
            if last_object is not None:
                last_object.deselect()
            sel_object = self._handle_new_object_selection(sel_object)
        # Case 2: Double-click on empty space
        elif last_object is None and time_since_last_click < self._double_click_speed:
            self.add_node(x, y, self.gui.new_node_class)
            self._built_object_to_gui_dict()
        # Case 3: Single-click on empty space
        elif last_object is not None:
            last_object.deselect()
        # Case 4: you re-selected the same thing (possibly empty space)

        self._last_selected_object = sel_object

        self.redraw()

    def handle_mouse_up(self, x: Number, y: Number):
        self._mouse_is_down = False

    def _handle_new_object_selection(self, newly_selected_object: BaseCanvasWidget) -> Union[BaseCanvasWidget | None]:
        newly_selected_object.select()

        if hasattr(newly_selected_object, "handle_select"):
            newly_selected_object.handle_select(newly_selected_object)

        if isinstance(newly_selected_object, NodeWidget):
            return self._handle_node_select(newly_selected_object)
        elif isinstance(newly_selected_object, PortWidget):
            return self._handle_port_select(newly_selected_object)
        else:
            return newly_selected_object

    def _handle_node_select(self, sel_object: NodeWidget) -> NodeWidget:
        self._node_widget = NodeWidgets(sel_object.node, self.gui).draw()
        with self.gui.out_status:
            self.gui.out_status.clear_output()
            display(self._node_widget)  # PyCharm nit is invalid, display takes *args is why it claims to want a tuple
        return sel_object

    def _handle_port_select(self, sel_object: PortWidget) -> Union[PortWidget | None]:
        if isinstance(self._last_selected_object, PortWidget):
            self.flow.connect_nodes(self._last_selected_object.port, sel_object.port)
            self.deselect_all()
            return None
        else:
            return sel_object

    def get_element_at_xy(self, x_in: Number, y_in: Number) -> Union[BaseCanvasWidget, None]:
        for o in self.objects_to_draw:
            if o.is_selected(x_in, y_in):
                return o.get_element_at_xy(x_in, y_in)
        return None

    def get_selected_objects(self) -> List[BaseCanvasWidget]:
        return [o for o in self.objects_to_draw if o.selected if o.selected]

    def handle_mouse_move(self, x: Number, y: Number) -> None:
        # dx = x - self._x0_mouse
        # dy = y - self._y0_mouse
        # self._x0_mouse, self._y0_mouse = x, y

        if [o for o in self.objects_to_draw if o.selected] and self._mouse_is_down:
            with hold_canvas(self._canvas):
                # [o.add_x_y(dx, dy) for o in self.objects_to_draw if o.selected]
                [o.set_x_y(x, y) for o in self.objects_to_draw if o.selected]
                self.redraw()

    def redraw(self) -> None:
        self.canvas_restart()
        with hold_canvas(self._canvas):
            self.canvas_restart()
            [o.draw() for o in self.objects_to_draw]
            for c in self.flow.connections:
                self.draw_connection(c.inp, c.out)

    def load_node(self, x: Number, y: Number, node: Node) -> NodeWidget:
        #    print ('node: ', node.identifier, node.GLOBAL_ID)

        layout = NodeLayout()

        if hasattr(node, "main_widget_class"):
            if node.main_widget_class is not None:
                # node.title = str(node.main_widget_class)
                f = eval(node.main_widget_class)
                s = f(x, y, parent=self, layout=layout, node=node)
            else:
                s = NodeWidget(x, y, parent=self, layout=layout, node=node)
            # print ('s: ', s)
        else:
            s = NodeWidget(x, y, parent=self, layout=layout, node=node)

        self.objects_to_draw.append(s)
        return s

    def add_node(self, x: Number, y: Number, node: Node):
        n = self.flow.create_node(node)
        self.load_node(x, y, n)

        self.redraw()

    def delete_selected(self) -> None:
        for o in self.objects_to_draw:
            if o.selected:
                self.objects_to_draw.remove(o)
                self._remove_node_from_flow(o.node)
        self.redraw()

    def _remove_node_from_flow(self, node: Node) -> None:
        for c in self.flow.connections[::-1]:  # Reverse to make sure we traverse whole thing even if we delete
            # TODO: Can we be more efficient than looping over all nodes?
            if (c.inp.node == node) or (c.out.node == node):
                self.flow.remove_connection(c)
        self.flow.remove_node(node)
