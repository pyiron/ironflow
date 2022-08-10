# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import json
import os

import ipywidgets as widgets
from IPython.display import display
from ryven.main.utils import import_nodes_package, NodesPackage

from .FlowCanvas import FlowCanvas
from ryvencore import Session, Script, Flow

import ryven.NENV as NENV
from pathlib import Path

from typing import Optional, Dict, Type

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

os.environ["RYVEN_MODE"] = "no-gui"
NENV.init_node_env()

ryven_location = Path(__file__).parents[1]
packages = [os.path.join(ryven_location, "nodes", *subloc) for subloc in [
    ("built_in",),
    ("std",),
    ("pyiron",),
]]  # , ("mynodes",)
alg_modes = ["data", "exec"]


debug_view = widgets.Output(layout={"border": "1px solid black"})


class GUI:
    def __init__(self, session_title: str, script_title: Optional[str] = None, session: Optional[Session] = None):
        self._session = session if session is not None else Session()
        self.session_title = session_title
        self._flow_canvases = []
        self._active_script_index = 0

        for package in packages:
            self.session.register_nodes(
                import_nodes_package(NodesPackage(directory=package))
            )

        self._nodes_dict = {}
        for n in self.session.nodes:
            self._register_node(n)

        self.create_script(script_title)

    @property
    def active_script_index(self) -> int:
        return self._active_script_index

    @active_script_index.setter
    def active_script_index(self, i: int) -> None:
        if i >= len(self.session.scripts):
            raise KeyError(
                f"Attempted to activate script {i}, but there are only {len(self.session.scripts)} available."
            )
        self._active_script_index = i % self.n_scripts

    @property
    def session(self) -> Session:
        return self._session

    @property
    def script(self) -> Script:
        return self.session.scripts[self.active_script_index]

    @property
    def flow(self) -> Flow:
        return self.script.flow

    @property
    def n_scripts(self):
        return len(self.session.scripts)

    @property
    def next_auto_script_name(self):
        i = 0
        titles = [s.title for s in self.session.scripts]
        while f"script_{i}" in titles:
            i += 1
        return f"script_{i}"

    @property
    def flow_canvas_widget(self):
        return self._flow_canvases[self.active_script_index]

    @property
    def new_node_class(self):
        return self._nodes_dict[self.modules_dropdown.value][self.node_selector.value]

    def create_script(
            self,
            title: Optional[str] = None,
            create_default_logs: bool = True,
            data: Optional[Dict] = None
    ) -> None:
        self.session.create_script(
            title=title if title is not None else self.next_auto_script_name,
            create_default_logs=create_default_logs,
            data=data
        )
        self.active_script_index = -1
        self._flow_canvases.append(FlowCanvas(gui=self))

    def delete_script(self) -> None:
        last_active = self.active_script_index
        self._flow_canvases.pop(self.active_script_index)
        self.session.delete_script(self.script)
        if self.n_scripts == 0:
            self.create_script()
        else:
            self.active_script_index = last_active - 1

    def rename_script(self, new_name: str) -> bool:
        return self.session.rename_script(self.script, new_name)

    def save(self, file_path: str) -> None:
        data = self.serialize()

        with open(file_path, "w") as f:
            f.write(json.dumps(data, indent=4))

    def serialize(self) -> Dict:
        currently_active = self.active_script_index
        data = self.session.serialize()
        for i_script, script in enumerate(self.session.scripts):
            all_data = data["scripts"][i_script]["flow"]["nodes"]
            self.active_script_index = i_script
            for i, node_widget in enumerate(self.flow_canvas_widget.objects_to_draw):
                all_data[i]["pos x"] = node_widget.x
                all_data[i]["pos y"] = node_widget.y
        self.active_script_index = currently_active
        return data

    def load(self, file_path: str) -> None:
        with open(file_path, "r") as f:
            data = json.loads(f.read())

        self.load_from_data(data)

    def load_from_data(self, data: Dict) -> None:
        for script in self.session.scripts[::-1]:
            self.session.delete_script(script)
        self._flow_canvases = []

        self.session.load(data)
        for i_script, script in enumerate(self.session.scripts):
            flow_canvas = FlowCanvas(gui=self, flow=script.flow)
            all_data = data["scripts"][i_script]["flow"]["nodes"]
            for i_node, node in enumerate(script.flow.nodes):
                flow_canvas.load_node(all_data[i_node]["pos x"], all_data[i_node]["pos y"], node)
            flow_canvas._built_object_to_gui_dict()
            flow_canvas.redraw()
            self._flow_canvases.append(flow_canvas)

        self.active_script_index = 0

    def _register_node(self, node_class: Type[NENV.Node], node_module: Optional[str] = None):
        node_module = node_module or node_class.__module__  # n.identifier_prefix
        if node_module not in self._nodes_dict.keys():
            self._nodes_dict[node_module] = {}
        self._nodes_dict[node_module][node_class.title] = node_class

    def register_user_node(self, node_class: Type[NENV.Node]):
        """
        Register a custom node class from the gui's current working scope. These nodes are available under the
        'user' module. You will need to (re-)draw your GUI to see the change.

        Note: You can re-register a class to update its functionality, but only *newly placed* nodes will see this
                update. Already-placed nodes are still instances of the old class and need to be deleted.

        Note: You can save the graph as normal, but new gui instances will need to register the same custom nodes before
            loading the saved graph is possible.

        Args:
            node_class Type[NENV.Node]: The new node class to register.

        Example:
            >>> from ryven.ironflow import GUI, Node, NodeInputBP, NodeOutputBP, dtypes
            >>> gui = GUI(script_title='foo')
            >>>
            >>> class MyNode(Node):
            >>>     title = "MyUserNode"
            >>>     init_inputs = [
            >>>         NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
            >>>     ]
            >>>     init_outputs = [
            >>>        NodeOutputBP(label="bar")
            >>>    ]
            >>>    color = 'cyan'
            >>>
            >>>     def update_event(self, inp=-1):
            >>>         self.set_output_val(0, self.input(0) + 42)
            >>>
            >>> gui.register_user_node(MyNode)
        """
        if node_class in self.session.nodes:
            self.session.unregister_node(node_class)
        self.session.register_node(node_class)
        self._register_node(node_class, node_module='user')

    ### ^ Back end ########
    ### More or less... ###
    ### v Front end #######

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
    def click_save(self, change: Dict) -> None:
        self.save(f"{self.session_title}.json")

    def click_load(self, change: Dict) -> None:
        self.load(f"{self.session_title}.json")
        self._update_tabs_from_model()
        self.out_plot.clear_output()
        self.out_log.clear_output()

    def click_delete_node(self, change: Dict) -> None:
        self.flow_canvas_widget.delete_selected()

    def change_modules_dropdown(self, change: Dict) -> None:
        self.node_selector.options = sorted(self._nodes_dict[self.modules_dropdown.value].keys())

    def change_alg_mode_dropdown(self, change: Dict) -> None:
        self.flow_canvas_widget.script.flow.set_algorithm_mode(self.alg_mode_dropdown.value)

    def change_script_tabs(self, change: Dict):
        if change['name'] == 'selected_index' and change['new'] is not None:
            self._depopulate_text_input_panel()
            if self.script_tabs.selected_index == self.n_scripts:
                self.create_script()
                self._update_tabs_from_model()
            else:
                self.active_script_index = self.script_tabs.selected_index

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
        new_name = self.text_input_field.value
        rename_success = self.rename_script(new_name)
        if rename_success:
            self.script_tabs.set_title(self.active_script_index, new_name)
        else:
            self._print(f"INVALID NAME: Failed to rename script '{self.script.title}' to '{new_name}'.")
        self._depopulate_text_input_panel()

    def click_input_text_cancel(self, change: Dict) -> None:
        self._depopulate_text_input_panel()

    def click_rename_script(self, change: Dict) -> None:
        self._populate_text_input_panel("Script name", self.script.title)

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
