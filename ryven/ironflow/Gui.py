import json
import os

import ipywidgets as widgets
import ryvencore as rc
from IPython.display import display
from ryven.main.utils import import_nodes_package, load_from_file, NodesPackage

from .CanvasObject import CanvasObject, gui_modes

import ryven.NENV as NENV
from pathlib import Path

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
packages = [os.path.join(ryven_location, *subloc) for subloc in [("std",), ("nodes", "built_in")]]  # , ("mynodes",)
alg_modes = ["data", "exec"]


debug_view = widgets.Output(layout={"border": "1px solid black"})


class GUI:
    def __init__(self, script_title="test"):  # , onto_dic=onto_dic):
        self._script_title = script_title
        session = rc.Session()
        for package in packages:
            session.register_nodes(
                import_nodes_package(NodesPackage(directory=package))
            )

        self._session = session
        script = session.create_script(title=self.script_title)

        nodes_dict = {}
        for n in self._session.nodes:
            node_class = n.__module__  # n.identifier_prefix
            if node_class not in nodes_dict.keys():
                nodes_dict[node_class] = {}
            nodes_dict[node_class][n.title] = n
        self._nodes_dict = nodes_dict

        self.canvas_widget = CanvasObject(self, script=script)
        # self.onto_dic = onto_dic

        self.out_log = widgets.Output(layout={"border": "1px solid black"})

    @property
    def script_title(self) -> str:
        return self._script_title

    def save(self, file_path):
        data = self.serialize()

        with open(file_path, "w") as f:
            f.write(json.dumps(data, indent=4))

    def serialize(self):
        data = self._session.serialize()
        i_script = 0
        all_data = data["scripts"][i_script]["flow"]["nodes"]
        for i, node_widget in enumerate(self.canvas_widget.objects_to_draw):
            all_data[i]["pos x"] = node_widget.x
            all_data[i]["pos y"] = node_widget.y
        return data

    def load(self, file_path):
        with open(file_path, "r") as f:
            data = json.loads(f.read())

        self.load_from_data(data)

    def load_from_data(self, data):
        i_script = 0
        self._session.delete_script(self._session.scripts[i_script])
        self._session.load(data)

        script = self._session.scripts[i_script]
        self.canvas_widget = CanvasObject(self, script=script)
        self.canvas_widget.canvas_restart()
        all_data = data["scripts"][i_script]["flow"]["nodes"]
        for i, node in enumerate(script.flow.nodes):
            self.canvas_widget.load_node(
                all_data[i]["pos x"], all_data[i]["pos y"], node
            )
        self.canvas_widget._built_object_to_gui_dict()

        self.out_canvas.clear_output()
        with self.out_canvas:
            display(self.canvas_widget._canvas)

        self.canvas_widget.redraw()
        self.out_plot.clear_output()
        self.out_log.clear_output()

    def _print(self, text):
        with self.out_log:
            self.gui.out_log.clear_output()

            print(text)

    @debug_view.capture(clear_output=True)
    def draw(self):
        self.out_plot = widgets.Output(
            layout={"width": "50%", "border": "1px solid black"}
        )

        self.out_canvas = widgets.Output(layout={"border": "1px solid black"})
        with self.out_canvas:
            display(self.canvas_widget._canvas)

        module_options = self._nodes_dict.keys()
        self.modules_dropdown = widgets.Dropdown(
            options=module_options,
            value=list(module_options)[0],
            #     description='Category:',
            disabled=False,
            layout=widgets.Layout(width="130px"),
        )

        self.mode_dropdown = widgets.Dropdown(
            options=gui_modes,
            value=gui_modes[0],
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

        nodes_options = self._nodes_dict[self.modules_dropdown.value].keys()
        self.node_selector = widgets.RadioButtons(
            options=nodes_options,
            value=list(nodes_options)[0],
            #    layout={'width': 'max-content'}, # If the items' names are long
            #     description='Nodes:',
            disabled=False,
        )
        self.on_nodes_change(list(nodes_options)[0])

        self.out_status = widgets.Output(layout={"border": "1px solid black"})

        self.alg_mode_dropdown.observe(self.on_alg_mode_change, names="value")
        self.modules_dropdown.observe(self.on_value_change, names="value")
        self.node_selector.observe(self.on_nodes_change, names="value")
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
                        self.mode_dropdown,
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

    def on_file_save(self, change):
        self.save(f"{self.script_title}.json")

    def on_file_load(self, change):
        self.load(f"{self.script_title}.json")

    def on_delete_node(self, change):
        self.canvas_widget.delete_selected()

    def on_value_change(self, change):
        self.node_selector.options = self._nodes_dict[self.modules_dropdown.value].keys()

    def on_nodes_change(self, change):
        self._selected_node = self._nodes_dict[self.modules_dropdown.value][self.node_selector.value]

    def on_alg_mode_change(self, change):
        self.canvas_widget.script.flow.set_algorithm_mode(self.alg_mode_dropdown.value)
