import ipywidgets as widgets
import numpy as np

from .NodeWidget import CanvasLayout

import pickle
import base64

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


def deserialize(data):
    return pickle.loads(base64.b64decode(data))


class NodeWidgets:
    def __init__(self, node, central_gui):
        self._node = node
        self._central_gui = central_gui
        self.gui_object()
        self.input_widgets()
        # self.input = []

    def gui_object(self):
        if "slider" in self._node.title.lower():
            self.gui = widgets.FloatSlider(
                value=self._node.val, min=0, max=10, continuous_update=False
            )

            self.gui.observe(self.gui_object_change, names="value")
        else:
            self.gui = widgets.Box()
        return self.gui

    def gui_object_change(self, change):
        self._node.set_state({"val": change["new"]}, 0)
        self._node.update_event()
        self._central_gui.canvas_widget.redraw()

    def input_widgets(self):
        self._input = []
        if not hasattr(self._node, "inputs"):
            return
        for i_c, inp in enumerate(self._node.inputs[:]):
            if inp.dtype is None:
                # if inp.type_ == 'exec':
                inp_widget = widgets.Label(value=inp.type_)
                description = inp.type_
                # inp_widget =
            else:
                dtype = str(inp.dtype).split(".")[-1]
                dtype_state = deserialize(inp.data()["dtype state"])
                if inp.val is None:
                    inp.val = dtype_state["val"]
                # print (dtype)
                if dtype == "Integer":
                    inp_widget = widgets.IntText(
                        value=inp.val,  # dtype_state['val'],
                        disabled=False,
                        description="",
                        continuous_update=False,
                        layout=widgets.Layout(width="110px", border="solid 1px"),
                    )
                elif dtype == "Boolean":
                    inp_widget = widgets.Checkbox(
                        value=inp.val,  # dtype_state['val'],
                        indent=True,
                        description="",
                        layout=widgets.Layout(width="110px", border="solid 1px"),
                    )
                elif dtype == "Choice":
                    inp_widget = widgets.Dropdown(
                        value=inp.val,
                        options=inp.dtype.items,
                        description="",
                        ensure_option=True,
                        layout=widgets.Layout(width="110px", border="solid 1px"),
                    )

                else:
                    inp_widget = widgets.Text(
                        value=str(inp.val),
                        continuous_update=False,
                    )

                description = inp.label_str
            self._input.append([widgets.Label(description), inp_widget])

            inp_widget.observe(eval(f"self.input_change_{i_c}"), names="value")

            # inp_widget.value = dtype_state['default']

    def input_change(self, i_c, change):
        # print (change)
        self._node.inputs[i_c].val = change["new"]
        self._node.update_event()
        self._central_gui.canvas_widget.redraw()

    def input_change_0(self, change):
        self.input_change(0, change)

    def input_change_1(self, change):
        self.input_change(1, change)

    def input_change_2(self, change):
        self.input_change(2, change)

    def input_change_3(self, change):
        self.input_change(3, change)

    def input_change_4(self, change):
        self.input_change(3, change)

    def input_change_5(self, change):
        self.input_change(3, change)

    def draw(self):
        self.inp_box = widgets.GridBox(
            list(np.array(self._input).flatten()),
            layout=widgets.Layout(
                width="210px",
                grid_template_columns="90px 110px",
                # grid_gap='1px 1px',
                border="solid 1px blue",
                margin="10px",
            ),
        )

        self.gui.layout = widgets.Layout(
            height="70px", border="solid 1px red", margin="10px", padding="10px"
        )

        glob_id_val = None
        if hasattr(self._node, "GLOBAL_ID"):
            glob_id_val = self._node.GLOBAL_ID
        global_id = widgets.Text(
            value=str(glob_id_val), description="GLOBAL_ID:", disabled=True
        )
        # global_id.layout.width = '300px'

        title = widgets.Text(
            value=str(self._node.title),
            # placeholder='Type something',
            description="Title:",
            disabled=True,
        )
        # title.layout.width = '300px'

        info_box = widgets.VBox([global_id, title])
        info_box.layout = widgets.Layout(
            height="70px",
            width="350px",
            border="solid 1px red",
            margin="10px",
            padding="0px",
        )

        return widgets.HBox([self.inp_box, self.gui, info_box])
