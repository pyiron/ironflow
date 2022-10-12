# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from ryven.ironflow.node_interface.base import NodeInterfaceBase
from IPython.display import display
import ipywidgets as widgets
import numpy as np

import pickle
import base64

from typing import TYPE_CHECKING, Callable, Optional
if TYPE_CHECKING:
    from ryven.ironflow.gui import GUI
    from ryven.NENV import Node

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


def deserialize(data):
    return pickle.loads(base64.b64decode(data))


class NodeController(NodeInterfaceBase):
    """
    Handles the creation of widgets for manually adjusting node input and viewing node info.
    """

    def __init__(self, gui: GUI, layout: Optional[dict] = None):
        super().__init__(gui=gui, layout=layout)
        self.node = None
        self._margin = 5  # px
        self._row_height = 30  # px

    def _box_height(self, n_rows: int) -> int:
        return n_rows * self._row_height + 2 * self._margin

    @property
    def input_widget(self) -> widgets.Widget:
        try:
            widget = self.node.input_widget(self.gui, self.node).widget
            widget.layout = widgets.Layout(
                height="70px", border="solid 1px blue", margin=f"{self._margin}px", padding="10px", width="auto"
            )
            return widget
        except AttributeError:
            return widgets.Output()

    def input_field_list(self) -> list[list[widgets.Widget]]:
        input = []
        if hasattr(self.node, "inputs"):
            for i_c, inp in enumerate(self.node.inputs[:]):
                if inp.dtype is not None:
                    dtype = str(inp.dtype).split(".")[-1]
                    dtype_state = deserialize(inp.data()["dtype state"])
                    if inp.val is None:
                        inp.val = dtype_state["val"]
                    if dtype == "Integer":
                        inp_widget = widgets.IntText(
                            value=inp.val,
                            disabled=False,
                            description="",
                            continuous_update=False,
                        )
                    elif dtype == "Boolean":
                        inp_widget = widgets.Checkbox(
                            value=inp.val,
                            indent=False,
                            description="",
                        )
                    elif dtype == "Choice":
                        inp_widget = widgets.Dropdown(
                            value=inp.val,
                            options=inp.dtype.items,
                            description="",
                            ensure_option=True,
                        )

                    else:
                        inp_widget = widgets.Text(
                            value=str(inp.val),
                            continuous_update=False,
                        )
                    description = inp.label_str
                elif inp.label_str != "":
                    inp_widget = widgets.Label(value=inp.type_)
                    description = inp.label_str
                else:
                    inp_widget = widgets.Label(value=inp.type_)
                    description = inp.type_
                inp_widget.observe(self.input_change_i(i_c), names="value")
                input.append([widgets.Label(description), inp_widget])
        return input

    def input_change_i(self, i_c) -> Callable:
        def input_change(change: dict) -> None:
            self.node.inputs[i_c].val = change["new"]
            self.node.update_event()
            self.gui.flow_canvas.redraw()
        return input_change

    @property
    def input_box(self) -> widgets.GridBox | widgets.Output:
        input_fields = self.input_field_list()
        n_fields = len(input_fields)
        if n_fields > 0:
            return widgets.GridBox(
                list(np.array(input_fields).flatten()),
                layout=widgets.Layout(
                    grid_template_columns="110px auto",
                    grid_auto_rows=f"{self._row_height}px",
                    border="solid 1px blue",
                    margin=f"{self._margin}px",
                    height=f"{self._box_height(n_fields)}px",
                    # Automatic height like this really should be doable just with the CSS,
                    # but for the life of me I can't get a CSS solution working right -Liam
                )
            )
        else:
            return widgets.Output()

    @property
    def info_box(self):
        glob_id_val = None
        if hasattr(self.node, "GLOBAL_ID"):
            glob_id_val = self.node.GLOBAL_ID
        global_id = widgets.Text(value=str(glob_id_val), description="GLOBAL_ID:", disabled=True)

        title = widgets.Text(value=str(self.node.title), description="Title:", disabled=True)

        info_box = widgets.VBox([title, global_id])
        info_box.layout = widgets.Layout(
            height=f"{self._box_height(2)}px",
            border="solid 1px red",
            margin=f"{self._margin}px",
            padding="0px",
        )
        return info_box

    def draw(self) -> None:
        self.clear_output()
        if self.node is not None:
            with self.output:
                display(widgets.VBox([self.input_box, self.input_widget, self.info_box]))
                # PyCharm nit is invalid, display takes *args is why it claims to want a tuple

    def draw_for_node(self, node: Node | None):
        self.node = node
        self.draw()


