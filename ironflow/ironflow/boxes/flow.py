# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.


from __future__ import annotations

import ipywidgets as widgets
from IPython.display import display
from ironflow.ironflow.boxes.base import Box


class NodeSelector(Box):
    box_class = widgets.VBox

    def __init__(self, nodes_dictionary):
        super().__init__()
        self._nodes_dictionary = nodes_dictionary

        self.modules_dropdown = widgets.Dropdown(
            options=self.module_options,
            value=list(self.module_options)[0],
            disabled=False,
            layout=widgets.Layout(width="130px"),
        )

        self.node_selector = widgets.RadioButtons(
            options=self.nodes_options,
            value=list(self.nodes_options)[0],
            disabled=False,
        )

        self.modules_dropdown.observe(self.change_modules_dropdown, names="value")

        self.box.children = [self.modules_dropdown, self.node_selector]

    def change_modules_dropdown(self, change: dict) -> None:
        self.node_selector.options = sorted(self._nodes_dictionary[self.modules_dropdown.value].keys())

    @property
    def new_node_class(self):
        return self._nodes_dictionary[self.modules_dropdown.value][self.node_selector.value]

    @property
    def module_options(self) -> list[str]:
        return sorted(self._nodes_dictionary.keys())

    @property
    def nodes_options(self) -> list[str]:
        return sorted(self._nodes_dictionary[self.modules_dropdown.value].keys())

    def update(self, nodes_dictionary: dict) -> None:
        self._nodes_dictionary = nodes_dictionary
        self.modules_dropdown.options = self.module_options


class FlowBox(Box):
    box_class = widgets.HBox

    def __init__(self, nodes_dictionary: dict):
        super().__init__()
        self.node_selector = NodeSelector(nodes_dictionary=nodes_dictionary)
        self.script_tabs = widgets.Tab([])

        self.node_selector.box.layout.width = "15%"
        self.script_tabs.layout.width = "85%"

        self.box.children = [self.node_selector.box, self.script_tabs]

    def update_nodes(self, nodes_dictionary: dict):
        self.node_selector.update(nodes_dictionary=nodes_dictionary)

    def update_tabs(self, gui):
        self.script_tabs.selected_index = None
        # ^ To circumvent a bug where the index gets set to 0 on child changes
        # https://github.com/jupyter-widgets/ipywidgets/issues/2988
        self.script_tabs.children = [
            widgets.Output(layout={"border": "1px solid black"}) for _ in range(gui.n_scripts)
        ]
        for i, child in enumerate(self.script_tabs.children):
            self.script_tabs.set_title(i, gui.session.scripts[i].title)
            child.clear_output()
            with child:
                display(gui.flow_canvases[i].canvas)
        self._add_new_script_tab(gui)
        self.script_tabs.selected_index = gui.active_script_index

    def _add_new_script_tab(self, gui):
        self.script_tabs.children += (widgets.Output(layout={"border": "1px solid black"}),)
        self.script_tabs.set_title(len(gui.session.scripts), "+")
