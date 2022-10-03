# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.


from __future__ import annotations

import ipywidgets as widgets
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
