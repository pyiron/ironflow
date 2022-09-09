# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from IPython.display import display
import ipywidgets as widgets
import numpy as np

import pickle
import base64

from typing import TYPE_CHECKING, Dict, Union, Callable
if TYPE_CHECKING:
    from gui import GUI
    from ryven.NENV import Node

__author__ = "Joerg Neugebauer"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "May 10, 2022"


def deserialize(data):
    return pickle.loads(base64.b64decode(data))


class NodeInterface:
    """
    Handles the creation of widgets for manually adjusting node input and viewing node info.
    """

    def __init__(self, central_gui: GUI):
        self.node = None
        self._central_gui = central_gui
        # self.input = []

    def gui_object(self) -> Union[widgets.FloatSlider, widgets.Box]:
        if "slider" in self.node.title.lower():
            self.gui = widgets.FloatSlider(
                value=self.node.val, min=0, max=10, continuous_update=False
            )

            self.gui.observe(self.gui_object_change, names="value")
        else:
            self.gui = widgets.Box()
        return self.gui

    def gui_object_change(self, change: Dict) -> None:
        self.node.set_state({"val": change["new"]}, 0)
        self.node.update_event()
        self._central_gui.flow_canvas.redraw()

    def input_widgets(self) -> None:
        self._input = []
        if not hasattr(self.node, "inputs"):
            return
        for i_c, inp in enumerate(self.node.inputs[:]):
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

            inp_widget.observe(self.input_change_i(i_c), names="value")

            # inp_widget.value = dtype_state['default']

    def input_change_i(self, i_c) -> Callable:
        def input_change(change: Dict) -> None:
            self.node.inputs[i_c].val = change["new"]
            self.node.update_event()
            self._central_gui.flow_canvas.redraw()
        return input_change

    def draw(self) -> widgets.HBox:
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
        if hasattr(self.node, "GLOBAL_ID"):
            glob_id_val = self.node.GLOBAL_ID
        global_id = widgets.Text(
            value=str(glob_id_val), description="GLOBAL_ID:", disabled=True
        )
        # global_id.layout.width = '300px'

        title = widgets.Text(
            value=str(self.node.title),
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

    def draw_for_node(self, node: Node | None):
        self.node = node
        with self._central_gui.out_status:
            self._central_gui.out_status.clear_output()
            if node is not None:
                self.gui_object()
                self.input_widgets()
                display(self.draw())  # PyCharm nit is invalid, display takes *args is why it claims to want a tuple
