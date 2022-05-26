from ipycanvas import Canvas, hold_canvas
import ipywidgets as widgets
import numpy as np
from IPython.display import display

from .NodeWidget import CanvasLayout, NodeWidget, PortWidget, ButtonNodeWidget
from .NodeWidgets import NodeWidgets
from .has_session import HasSession

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


gui_modes = ["(M)ove Node", "Add (C)onnection", "(N)one"]
mode_move, mode_connect, mode_none = gui_modes


class CanvasObject(HasSession):
    def __init__(self, gui=None, width=2000, height=1000):
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
        self._canvas.on_mouse_move(self.handle_mouse_move)
        self._canvas.on_key_down(self.handle_keyboard_event)

        self.x = 0
        self.y = 0

        self._last_selected_object = None
        self._last_selected_port = None

        self._connection_in = None
        self._node_widget = None

        self._object_to_gui_dict = {}

    def draw_connection(self, port_1, port_2):
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

    def _built_object_to_gui_dict(self):
        self._object_to_gui_dict = {}
        for n in self.objects_to_draw:
            self._object_to_gui_dict[n.node] = n
            for p in n.objects_to_draw:
                if hasattr(p, "port"):
                    self._object_to_gui_dict[p.port] = p

    def canvas_restart(self):
        self._canvas.clear()
        self._canvas.fill_style = self._col_background
        self._canvas.fill_rect(0, 0, self._width, self._height)

    def handle_keyboard_event(self, key, shift_key, ctrl_key, meta_key):
        if key == "Delete":
            self.delete_selected()
        elif key == "m":
            self.gui.mode_dropdown.value = mode_move
        elif key == "c":
            self.deselect_all()
            self.gui.mode_dropdown.value = mode_connect
        elif key == "n":
            self.gui.mode_dropdown.value = mode_none

    def set_connection(self, ind_node):
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

    def deselect_all(self):
        [o.set_selected(False) for o in self.objects_to_draw if o.selected]
        self.redraw()

    def handle_mouse_down(self, x, y):
        sel_object = self.get_element_at_xy(x, y)
        self._selected_object = sel_object
        if sel_object is not None:
            sel_object.set_selected(not sel_object.selected)
            if sel_object.selected:
                if self._last_selected_object is not None:
                    self._last_selected_object.set_selected(False)
                self._last_selected_object = sel_object
                if isinstance(sel_object, NodeWidget):
                    self._handle_node_select(sel_object)
                elif isinstance(sel_object, PortWidget):
                    self._handle_port_select(sel_object)

                if hasattr(sel_object, "handle_select"):
                    sel_object.handle_select(sel_object)

            else:
                self._last_selected_object = None
        else:
            self.add_node(x, y, self.gui._selected_node)
            self._built_object_to_gui_dict()

        self._x0_mouse = x
        self._y0_mouse = y
        self.redraw()

    def _handle_node_select(self, sel_object):
        self._node_widget = NodeWidgets(sel_object.node, self.gui).draw()
        with self.gui.out_status:
            self.gui.out_status.clear_output()
            display(self._node_widget)

    def _handle_port_select(self, sel_object):
        if self._last_selected_port is None:
            self._last_selected_port = sel_object.port
        else:
            self.flow.connect_nodes(self._last_selected_port, sel_object.port)
            self._last_selected_port = None
            self.deselect_all()

    def get_element_at_xy(self, x_in, y_in):
        for o in self.objects_to_draw:
            if o.is_selected(x_in, y_in):
                return o.get_element_at_xy(x_in, y_in)
        return None

    def get_selected_objects(self):
        return [o for o in self.objects_to_draw if o.selected]

    def handle_mouse_move(self, x, y):
        if self.gui.mode_dropdown.value == mode_move:
            # dx = x - self._x0_mouse
            # dy = y - self._y0_mouse
            # self._x0_mouse, self._y0_mouse = x, y

            if [o for o in self.objects_to_draw if o.selected]:
                with hold_canvas(self._canvas):
                    # [o.add_x_y(dx, dy) for o in self.objects_to_draw if o.selected]
                    [o.set_x_y(x, y) for o in self.objects_to_draw if o.selected]
                    self.redraw()

    def redraw(self):
        self.canvas_restart()
        with hold_canvas(self._canvas):
            self.canvas_restart()
            [o.draw() for o in self.objects_to_draw]
            for c in self.flow.connections:
                self.draw_connection(c.inp, c.out)

    def load_node(self, x, y, node):
        #    print ('node: ', node.identifier, node.GLOBAL_ID)

        layout = CanvasLayout(
            font_size=20,
            width=200,
            height=100,
            background_color="gray",
            selected_color="green",
        )

        if hasattr(node, "main_widget_class"):
            if node.main_widget_class is not None:
                # node.title = str(node.main_widget_class)
                f = eval(node.main_widget_class)
                s = f(x, y, parent=self, node=node, layout=layout)
            else:
                s = NodeWidget(x, y, parent=self, node=node, layout=layout)
            # print ('s: ', s)
        else:
            s = NodeWidget(x, y, parent=self, node=node, layout=layout)

        self.objects_to_draw.append(s)
        return s

    def add_node(self, x, y, node):
        n = self.flow.create_node(node)
        print("node: ", n.identifier, n.GLOBAL_ID)
        self.load_node(x, y, n)

        self.redraw()

    def delete_selected(self):
        for o in self.objects_to_draw:
            if o.selected:
                self.objects_to_draw.remove(o)
                self._remove_node_from_flow(o.node)
        self.redraw()

    def _remove_node_from_flow(self, node):
        for c in self.flow.connections[::-1]:  # Reverse to make sure we traverse whole thing even if we delete
            # TODO: Can we be more efficient than looping over all nodes?
            if (c.inp.node == node) or (c.out.node == node):
                self.flow.remove_connection(c)
        self.flow.remove_node(node)
