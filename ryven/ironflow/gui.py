# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

__author__ = "Joerg Neugebauer, Liam Huber"
__copyright__ = (
    "Copyright 2020, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "May 10, 2022"

import ipywidgets as widgets
from IPython.display import display
from ryven.ironflow.models import HasSession
from ryven.ironflow.node_interface import NodeInterface
from ryven.ironflow.flow_canvas import FlowCanvas

from typing import Optional, Dict
from ryvencore import Session

alg_modes = ["data", "exec"]
debug_view = widgets.Output(layout={"border": "1px solid black"})


class GUI(HasSession):
    def __init__(self, session_title: str, session: Optional[Session] = None, script_title: Optional[str] = None):
        super().__init__(session_title=session_title, session=session)

        self._flow_canvases = []
        self.displayed_node = None
        self.node_interface = NodeInterface(self)

        self._context = None
        self._context_actions = {
            "rename": self._rename_context_action,
            "save": self._save_context_action,
            "load": self._load_context_action
        }

        self.create_script(script_title)

    def create_script(
            self,
            title: Optional[str] = None,
            create_default_logs: bool = True,
            data: Optional[Dict] = None
    ) -> None:
        super().create_script(title=title, create_default_logs=create_default_logs, data=data)
        self._flow_canvases.append(FlowCanvas(gui=self))

    def delete_script(self) -> None:
        self._flow_canvases.pop(self.active_script_index)
        super().delete_script()

    @property
    def flow_canvas_widget(self):
        return self._flow_canvases[self.active_script_index]

    @property
    def new_node_class(self):
        return self._nodes_dict[self.modules_dropdown.value][self.node_selector.value]

    def load_from_data(self, data: Dict) -> None:
        super().load_from_data(data)
        self._flow_canvases = []
        for i_script, script in enumerate(self.session.scripts):
            flow_canvas = FlowCanvas(gui=self, flow=script.flow)
            all_data = data["scripts"][i_script]["flow"]["nodes"]
            for i_node, node in enumerate(script.flow.nodes):
                flow_canvas.load_node(all_data[i_node]["pos x"], all_data[i_node]["pos y"], node)
            flow_canvas._built_object_to_gui_dict()
            flow_canvas.redraw()
            self._flow_canvases.append(flow_canvas)

    @debug_view.capture(clear_output=True)
    def draw(self) -> widgets.VBox:
        self.out_plot = widgets.Output(layout={"width": "50%", "border": "1px solid black"})
        self.out_log = widgets.Output(layout={"border": "1px solid black"})

        self.script_tabs = widgets.Tab([])
        self._update_tabs_from_model()

        module_options = sorted(self._nodes_dict.keys())
        self.modules_dropdown = widgets.Dropdown(
            options=module_options,
            value=list(module_options)[0],
            disabled=False,
            layout=widgets.Layout(width="130px"),
        )

        button_layout = widgets.Layout(width="50px")
        # Icon source: https://fontawesome.com
        self.btn_load = widgets.Button(tooltip="Load", icon="upload", layout=button_layout)
        self.btn_save = widgets.Button(tooltip="Save", icon="download", layout=button_layout)
        self.btn_delete_node = widgets.Button(tooltip="Delete Node", icon="trash", layout=button_layout)
        self.btn_rename_script = widgets.Button(tooltip="Rename script", icon="file", layout=button_layout)
        # TODO: Use file-pen once this is available
        self.btn_delete_script = widgets.Button(tooltip="Delete script", icon="minus", layout=button_layout)
        # TODO: Use file-circle-minus once this is available

        self.text_input_panel = widgets.HBox([])
        self.text_input_field = widgets.Text(value="INIT VALUE", description="DESCRIPTION")
        self.btn_input_text_ok = widgets.Button(tooltip="Confirm new name", icon="check", layout=button_layout)
        self.btn_input_text_cancel = widgets.Button(tooltip="Cancel renaming", icon="ban", layout=button_layout)
        # TODO: Use xmark once this is available

        self.alg_mode_dropdown = widgets.Dropdown(
            options=alg_modes,
            value=alg_modes[0],
            disabled=False,
            layout=widgets.Layout(width="80px"),
        )

        nodes_options = sorted(self._nodes_dict[self.modules_dropdown.value].keys())
        self.node_selector = widgets.RadioButtons(
            options=nodes_options,
            value=list(nodes_options)[0],
            #    layout={'width': 'max-content'}, # If the items' names are long
            #     description='Nodes:',
            disabled=False,
        )

        self.out_status = widgets.Output(layout={"border": "1px solid black"})

        self.alg_mode_dropdown.observe(self.change_alg_mode_dropdown, names="value")
        self.modules_dropdown.observe(self.change_modules_dropdown, names="value")
        self.btn_load.on_click(self.click_load)
        self.btn_save.on_click(self.click_save)
        self.btn_delete_node.on_click(self.click_delete_node)
        self.btn_rename_script.on_click(self.click_rename_script)
        self.btn_input_text_ok.on_click(self.click_input_text_ok)
        self.text_input_field.on_submit(self.click_input_text_ok)
        # ^ Ignore the deprecation warning, 'observe' does function the way we actually want
        # https://github.com/jupyter-widgets/ipywidgets/issues/2446
        self.btn_input_text_cancel.on_click(self.click_input_text_cancel)
        self.btn_delete_script.on_click(self.click_delete_script)
        self.script_tabs.observe(self.change_script_tabs)

        return widgets.VBox(
            [
                widgets.HBox(
                    [
                        self.modules_dropdown,
                        self.alg_mode_dropdown,
                        self.btn_save,
                        self.btn_load,
                        self.btn_delete_node,
                        self.btn_rename_script,
                        self.btn_delete_script,
                    ]
                ),
                self.text_input_panel,
                widgets.HBox(
                    [widgets.VBox([self.node_selector]), self.script_tabs, self.out_plot]
                ),
                self.out_log,
                self.out_status,
                debug_view
            ]
        )

    # Type hinting for unused `change` argument in callbacks taken from ipywidgets docs:
    # https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Events.html#Traitlet-events
    def click_delete_node(self, change: Dict) -> None:
        self.flow_canvas_widget.delete_selected()

    def change_modules_dropdown(self, change: Dict) -> None:
        self.node_selector.options = sorted(self._nodes_dict[self.modules_dropdown.value].keys())

    def change_alg_mode_dropdown(self, change: Dict) -> None:
        # Current behaviour: Updates the flow mode for all scripts
        # TODO: Change only for the active script, and update the dropdown on tab (script) switching
        for script in self.session.scripts:
            script.flow.set_algorithm_mode(self.alg_mode_dropdown.value)

    def change_script_tabs(self, change: Dict):
        if change['name'] == 'selected_index' and change['new'] is not None:
            self._depopulate_text_input_panel()
            if self.script_tabs.selected_index == self.n_scripts:
                self.create_script()
                self._update_tabs_from_model()
            else:
                self.active_script_index = self.script_tabs.selected_index
            self.flow_canvas_widget.redraw()

    def _populate_text_input_panel(self, description, initial_value):
        self.text_input_panel.children = [
            self.text_input_field,
            self.btn_input_text_ok,
            self.btn_input_text_cancel
        ]
        self.text_input_field.description = description
        self.text_input_field.value = initial_value

    def _depopulate_text_input_panel(self) -> None:
        self.text_input_panel.children = []

    def click_input_text_ok(self, change: Dict) -> None:
        self._context_actions[self._context](self.text_input_field.value)
        self._depopulate_text_input_panel()

    def click_input_text_cancel(self, change: Dict) -> None:
        self._depopulate_text_input_panel()
        self._print("")

    def _set_context(self, context):
        if context not in self._context_actions.keys():
            raise KeyError(f"Expected a context action among {list(self._context_actions.keys())} but got {context}.")
        self._context = context

    def click_save(self, change: Dict) -> None:
        self._depopulate_text_input_panel()
        self._populate_text_input_panel("Save file name", self.session_title)
        self._set_context("save")
        self._print("Choose a file name to save to (omit the file extension, .json)")

    def _save_context_action(self, file_name):
        self.save(f"{file_name}.json")
        self._print(f"Session saved to {file_name}.json")

    def click_load(self, change: Dict) -> None:
        self._depopulate_text_input_panel()
        self._populate_text_input_panel("Load file name", self.session_title)
        self._set_context("load")
        self._print("Choose a file name to load (omit the file extension, .json)")

    def _load_context_action(self, file_name):
        self.load(f"{file_name}.json")
        self._update_tabs_from_model()
        self.out_plot.clear_output()
        self.out_log.clear_output()
        self._print(f"Session loaded from {file_name}.json")

    def click_rename_script(self, change: Dict) -> None:
        self._depopulate_text_input_panel()
        self._populate_text_input_panel("Script name", self.script.title)
        self._set_context('rename')
        self._print("Choose a new name for the current script")

    def _rename_context_action(self, new_name):
        old_name = self.script.title
        rename_success = self.rename_script(new_name)
        if rename_success:
            self.script_tabs.set_title(self.active_script_index, new_name)
            self._print(f"Script '{old_name}' renamed '{new_name}'")
        else:
            self._print(f"INVALID NAME: Failed to rename script '{self.script.title}' to '{new_name}'.")


    def click_delete_script(self, change: Dict) -> None:
        self.delete_script()
        self._update_tabs_from_model()

    def _update_tabs_from_model(self):
        self.script_tabs.selected_index = None
        # ^ To circumvent a bug where the index gets set to 0 on child changes
        # https://github.com/jupyter-widgets/ipywidgets/issues/2988
        self.script_tabs.children = [
            widgets.Output(layout={"border": "1px solid black"}) for _ in range(self.n_scripts)
        ]
        for i, child in enumerate(self.script_tabs.children):
            self.script_tabs.set_title(i, self.session.scripts[i].title)
            child.clear_output()
            with child:
                display(self._flow_canvases[i].canvas)
        self._add_new_script_tab()
        self.script_tabs.selected_index = self.active_script_index

    def _add_new_script_tab(self):
        self.script_tabs.children += (widgets.Output(layout={"border": "1px solid black"}),)
        self.script_tabs.set_title(len(self.session.scripts), "+")

    def _print(self, text: str) -> None:
        with self.out_log:
            self.out_log.clear_output()

            print(text)
