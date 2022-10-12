import json
import os

import ipywidgets as widgets
import ryvencore as rc
from IPython.display import display
from ryven.main.utils import import_nodes_package, NodesPackage

from .CanvasObject import CanvasObject
from .has_session import HasSession

import ryven.NENV as NENV
from pathlib import Path

from typing import Optional, Dict, Type

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


class GUI(HasSession):
    def __init__(self, script_title: str = "test", session: Optional[rc.Session] = None):  # , onto_dic=onto_dic):
        super().__init__(session=rc.Session() if session is None else session)
        self._script_title = script_title
        self.session.create_script(title=self.script_title)

        for package in packages:
            self.session.register_nodes(
                import_nodes_package(NodesPackage(directory=package))
            )

        self._nodes_dict = {}
        for n in self.session.nodes:
            self._register_node(n)

        self.canvas_widget = CanvasObject(gui=self)
        # self.onto_dic = onto_dic

        self.out_log = widgets.Output(layout={"border": "1px solid black"})

    def _register_node(self, node_class: Type[NENV.Node], node_module: Optional[str] = None):
        node_module = node_module or node_class.__module__  # n.identifier_prefix
        if node_module not in self._nodes_dict.keys():
            self._nodes_dict[node_module] = {}
        self._nodes_dict[node_module][node_class.title] = node_class

    def register_user_node(self, node_class: Type[NENV.Node]):
        """
        Register a custom node class from the gui's current working scope. These nodes are available under the
        'notebook' module.

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

    @property
    def script_title(self) -> str:
        return self._script_title

    def save(self, file_path: str) -> None:
        data = self.serialize()

        with open(file_path, "w") as f:
            f.write(json.dumps(data, indent=4))

    def serialize(self) -> Dict:
        data = self.session.serialize()
        i_script = 0
        all_data = data["scripts"][i_script]["flow"]["nodes"]
        for i, node_widget in enumerate(self.canvas_widget.objects_to_draw):
            all_data[i]["pos x"] = node_widget.x
            all_data[i]["pos y"] = node_widget.y
        return data

    def load(self, file_path: str) -> None:
        with open(file_path, "r") as f:
            data = json.loads(f.read())

        self.load_from_data(data)

    def load_from_data(self, data: Dict) -> None:
        i_script = 0
        self.session.delete_script(self.script)
        self.session.load(data)

        self.canvas_widget = CanvasObject(gui=self)
        self.canvas_widget.canvas_restart()
        all_data = data["scripts"][i_script]["flow"]["nodes"]
        for i, node in enumerate(self.flow.nodes):
            self.canvas_widget.load_node(
                all_data[i]["pos x"], all_data[i]["pos y"], node
            )
        self.canvas_widget._built_object_to_gui_dict()

        self.out_canvas.clear_output()
        with self.out_canvas:
            display(self.canvas_widget.canvas)

        self.canvas_widget.redraw()
        self.out_plot.clear_output()
        self.out_log.clear_output()

    def _print(self, text: str) -> None:
        with self.out_log:
            self.out_log.clear_output()

            print(text)

    @debug_view.capture(clear_output=True)
    def draw(self) -> widgets.VBox:
        self.out_plot = widgets.Output(
            layout={"width": "50%", "border": "1px solid black"}
        )

        self.out_canvas = widgets.Output(layout={"border": "1px solid black"})
        with self.out_canvas:
            display(self.canvas_widget.canvas)

        module_options = sorted(self._nodes_dict.keys())
        self.modules_dropdown = widgets.Dropdown(
            options=module_options,
            value=list(module_options)[0],
            #     description='Category:',
            disabled=False,
            layout=widgets.Layout(width="130px"),
        )

        self.btn_load = widgets.Button(
            tooltip="Load", icon="upload", layout=widgets.Layout(width="50px")
        )
        self.btn_save = widgets.Button(
            tooltip="Save", icon="download", layout=widgets.Layout(width="50px")
        )
        self.btn_delete_node = widgets.Button(
            tooltip="Delete Node", icon="trash", layout=widgets.Layout(width="50px")
        )

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

        self.alg_mode_dropdown.observe(self.on_alg_mode_change, names="value")
        self.modules_dropdown.observe(self.on_value_change, names="value")
        self.btn_load.on_click(self.on_file_load)
        self.btn_save.on_click(self.on_file_save)
        self.btn_delete_node.on_click(self.on_delete_node)

        # if self.canvas_widget._node_widget is None:
        #     self.canvas_widget._node_widget = widgets.Box()

        return widgets.VBox(
            [
                widgets.HBox(
                    [
                        self.modules_dropdown,
                        self.alg_mode_dropdown,
                        self.btn_save,
                        self.btn_load,
                        self.btn_delete_node
                    ]
                ),
                widgets.HBox(
                    [widgets.VBox([self.node_selector]), self.out_canvas, self.out_plot]
                ),
                self.out_log,
                self.out_status,
                debug_view
                # self.canvas_widget._node_widget
            ]
        )

    # Type hinting for unused `change` argument in callbacks taken from ipywidgets docs:
    # https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Events.html#Traitlet-events
    def on_file_save(self, change: Dict) -> None:
        self.save(f"{self.script_title}.json")

    def on_file_load(self, change: Dict) -> None:
        self.load(f"{self.script_title}.json")

    def on_delete_node(self, change: Dict) -> None:
        self.canvas_widget.delete_selected()

    def on_value_change(self, change: Dict) -> None:
        self.node_selector.options = sorted(self._nodes_dict[self.modules_dropdown.value].keys())

    def on_alg_mode_change(self, change: Dict) -> None:
        self.canvas_widget.script.flow.set_algorithm_mode(self.alg_mode_dropdown.value)

    @property
    def new_node_class(self):
        return self._nodes_dict[self.modules_dropdown.value][self.node_selector.value]
