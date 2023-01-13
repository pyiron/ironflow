# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Widgets for interacting with the flow diagram.
"""

from __future__ import annotations

import ipywidgets as widgets

from ironflow.gui.draws_widgets import DrawsWidgets, draws_widgets


class NodeSelector(DrawsWidgets):
    main_widget_class = widgets.VBox

    def __new__(cls, nodes_dictionary, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, nodes_dictionary, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

        self.widget.children = [self.modules_dropdown, self.node_selector]

    def change_modules_dropdown(self, change: dict) -> None:
        self.node_selector.options = sorted(
            self._nodes_dictionary[self.modules_dropdown.value].keys()
        )

    @property
    def new_node_class(self):
        return self._nodes_dictionary[self.modules_dropdown.value][
            self.node_selector.value
        ]

    @property
    def module_options(self) -> list[str]:
        return sorted(self._nodes_dictionary.keys())

    @property
    def nodes_options(self) -> list[str]:
        return sorted(self._nodes_dictionary[self.modules_dropdown.value].keys())

    def update(self, nodes_dictionary: dict) -> None:
        self._nodes_dictionary = nodes_dictionary
        self.modules_dropdown.options = self.module_options


class FlowBox(DrawsWidgets):
    def __new__(cls, nodes_dictionary, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, nodes_dictionary: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node_selector = NodeSelector(nodes_dictionary=nodes_dictionary)
        self.script_tabs = widgets.Tab([])

        self.node_selector.widget.layout.width = "15%"
        self.script_tabs.layout.width = "85%"

        self.widget.children = [self.node_selector.widget, self.script_tabs]

    def update_tabs(
        self, outputs: list[widgets.Output], titles: list[str], active_index: int
    ):
        self._outputs = outputs
        self._titles = titles
        self._active_index = active_index
        self.draw()

    @draws_widgets
    def draw(self):
        self.script_tabs.selected_index = None
        # ^ To circumvent a bug where the index gets set to 0 on child changes
        # https://github.com/jupyter-widgets/ipywidgets/issues/2988
        self.script_tabs.children = self._outputs
        for i, title in enumerate(self._titles):
            self.script_tabs.set_title(i, title)
        self._add_new_script_tab()
        self.script_tabs.selected_index = self._active_index

    def update_nodes(self, nodes_dictionary: dict):
        self.node_selector.update(nodes_dictionary=nodes_dictionary)

    def _add_new_script_tab(self):
        self.script_tabs.children += (
            widgets.Output(layout={"border": "1px solid black"}),
        )
        self.script_tabs.set_title(len(self.script_tabs.children) - 1, "+")

    def close(self):
        self.node_selector.close()
        super().close()
