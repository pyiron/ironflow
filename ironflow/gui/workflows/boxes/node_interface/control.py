# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
For directly controlling node IO (as opposed to giving it to nodes by connecting them to other OI).
"""

from __future__ import annotations

import pickle
import base64
from typing import TYPE_CHECKING, Callable

import ipywidgets as widgets
import numpy as np
from IPython.display import display

from ironflow.gui.workflows.boxes.node_interface.base import NodeInterfaceBase


if TYPE_CHECKING:
    from ironflow.gui.workflows.screen import WorkflowsGUI
    from ironflow.model.node import Node


def deserialize(data):
    return pickle.loads(base64.b64decode(data))


class NodeController(NodeInterfaceBase):
    """
    Handles the creation of widgets for manually adjusting node input and viewing node info.
    """

    def __init__(self, screen: WorkflowsGUI):
        super().__init__()
        self.screen = screen
        self.node = None
        self._margin = 5  # px
        self._row_height = 30  # px

    def _box_height(self, n_rows: int) -> int:
        return n_rows * self._row_height + 2 * self._margin

    @property
    def input_widget(self) -> widgets.Widget:
        try:
            widget = self.node.input_widget(self.screen, self.node).widget
            widget.layout = widgets.Layout(
                height="70px",
                border="solid 1px blue",
                margin=f"{self._margin}px",
                padding="10px",
                width="auto",
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
                    try:
                        dtype_state = deserialize(inp.data()["dtype state"])
                    except TypeError:
                        # `inp.data()` winds up calling `serialize` on `inp.get_val()`
                        # This serialization is a pickle dump, which fails with structures (`Atoms`)
                        # Just gloss over it for now
                        dtype_state = {
                            "val": "Serialization error -- please reconnect an input"
                        }
                    if inp.val is None:
                        inp.val = dtype_state["val"]
                    if dtype == "Integer":
                        inp_widget = widgets.IntText(
                            value=inp.val,
                            disabled=False,
                            description="",
                            continuous_update=False,
                        )
                    elif dtype == "Float":
                        inp_widget = widgets.FloatText(
                            value=inp.val,
                            description="",
                            continuous_update=False
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
            # Todo: Test this in exec mode
            self.node.inputs[i_c].val = change["new"]
            self.node.update(i_c)
            self.screen.redraw_active_flow_canvas()

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
                ),
            )
        else:
            return widgets.Output()

    @property
    def info_box(self) -> widgets.VBox:
        glob_id_val = None
        if hasattr(self.node, "GLOBAL_ID"):
            glob_id_val = self.node.GLOBAL_ID
        global_id = widgets.Text(
            value=str(glob_id_val), description="GLOBAL_ID:", disabled=True
        )

        title = widgets.Text(
            value=str(self.node.title), description="Title:", disabled=True
        )

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
                display(
                    widgets.VBox([self.input_box, self.input_widget, self.info_box])
                )
                # PyCharm nit is invalid, display takes *args is why it claims to want a tuple

    def draw_for_node(self, node: Node | None) -> None:
        self.node = node
        self.draw()

    def close(self) -> None:
        self.draw_for_node(None)
