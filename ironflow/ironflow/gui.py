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
from IPython.display import display, HTML
from ironflow.ironflow.model import HasSession
from ironflow.ironflow.boxes import Toolbar, NodeController, NodePresenter, TextOut, TextIn
from ironflow.ironflow.canvas_widgets import FlowCanvas

from typing import Optional
from ryvencore import Session

debug_view = widgets.Output(layout={"border": "1px solid black"})


class GUI(HasSession):
    def __init__(self, session_title: str, session: Optional[Session] = None, script_title: Optional[str] = None):
        super().__init__(session_title=session_title, session=session)

        self._flow_canvases = []
        self.toolbar = Toolbar()
        self.node_controller = NodeController(self)
        self.node_presenter = NodePresenter(self)
        self.text_out = TextOut()
        self.text_in = TextIn()

        self.create_script(script_title)

    def create_script(
            self,
            title: Optional[str] = None,
            create_default_logs: bool = True,
            data: Optional[dict] = None
    ) -> None:
        super().create_script(title=title, create_default_logs=create_default_logs, data=data)
        self._flow_canvases.append(FlowCanvas(gui=self))

    def delete_script(self) -> None:
        self._flow_canvases.pop(self.active_script_index)
        super().delete_script()

    @property
    def flow_canvas(self):
        return self._flow_canvases[self.active_script_index]

    @property
    def new_node_class(self):
        return self._nodes_dict[self.modules_dropdown.value][self.node_selector.value]

    def serialize(self) -> dict:
        data = super().serialize()
        currently_active = self.active_script_index
        for i_script, script in enumerate(self.session.scripts):
            all_data = data["scripts"][i_script]["flow"]["nodes"]
            self.active_script_index = i_script
            for i, node_widget in enumerate(self.flow_canvas.objects_to_draw):
                all_data[i]["pos x"] = node_widget.x
                all_data[i]["pos y"] = node_widget.y
        self.active_script_index = currently_active
        return data

    def load_from_data(self, data: dict) -> None:
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
        module_options = sorted(self._nodes_dict.keys())
        self.modules_dropdown = widgets.Dropdown(
            options=module_options,
            value=list(module_options)[0],
            disabled=False,
            layout=widgets.Layout(width="130px"),
        )

        nodes_options = sorted(self._nodes_dict[self.modules_dropdown.value].keys())
        self.node_selector = widgets.RadioButtons(
            options=nodes_options,
            value=list(nodes_options)[0],
            disabled=False,
        )
        self.node_selector_box = widgets.VBox([self.node_selector])

        node_panel = widgets.VBox([self.modules_dropdown, self.node_selector_box])
        node_panel.layout.width = "15%"

        self.script_tabs = widgets.Tab([])
        self.script_tabs.layout.width = "85%"
        self._update_tabs_from_model()

        flow_panel = widgets.HBox([node_panel, self.script_tabs])

        node_box = widgets.HBox([self.node_controller.output, self.node_presenter.output])

        # Wire callbacks
        self.toolbar.alg_mode_dropdown.observe(self.change_alg_mode_dropdown, names="value")
        self.modules_dropdown.observe(self.change_modules_dropdown, names="value")
        self.toolbar.buttons.help_node.on_click(self.click_node_help)
        self.toolbar.buttons.load.on_click(self.click_load)
        self.toolbar.buttons.save.on_click(self.click_save)
        self.toolbar.buttons.add_node.on_click(self.click_add_node)
        self.toolbar.buttons.delete_node.on_click(self.click_delete_node)
        self.toolbar.buttons.create_script.on_click(self.click_create_script)
        self.toolbar.buttons.rename_script.on_click(self.click_rename_script)
        # ^ Ignore the deprecation warning, 'observe' doesn't function the way we actually want
        # https://github.com/jupyter-widgets/ipywidgets/issues/2446
        self.toolbar.buttons.delete_script.on_click(self.click_delete_script)
        self.toolbar.buttons.zero_location.on_click(self.click_zero_location)
        self.toolbar.buttons.zoom_in.on_click(self.click_zoom_in)
        self.toolbar.buttons.zoom_out.on_click(self.click_zoom_out)
        self.script_tabs.observe(self.change_script_tabs)

        return widgets.VBox(
            [
                self.toolbar.box,
                self.text_in.box,
                flow_panel,
                self.text_out.box,
                node_box,
                debug_view
            ]
        )

    # Type hinting for unused `change` argument in callbacks taken from ipywidgets docs:
    # https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Events.html#Traitlet-events
    def change_modules_dropdown(self, change: dict) -> None:
        self.node_selector.options = sorted(self._nodes_dict[self.modules_dropdown.value].keys())

    def change_alg_mode_dropdown(self, change: dict) -> None:
        # Current behaviour: Updates the flow mode for all scripts
        # TODO: Change only for the active script, and update the dropdown on tab (script) switching
        for script in self.session.scripts:
            script.flow.set_algorithm_mode(self.toolbar.alg_mode_dropdown.value)

    def click_save(self, change: dict) -> None:
        self.text_in.open(
            "Save file",
            self.click_confirm_save,
            self.session_title,
            description_tooltip="Save to file name (omit the file extension, .json)"
        )
        self.print("Choose a file name to save to (omit the file extension, .json)")

    def click_confirm_save(self, change: dict) -> None:
        file_name = self.text_in.value
        self.save(f"{file_name}.json")
        self.print(f"Session saved to {file_name}.json")
        self.text_in.clear()

    def click_load(self, change: dict) -> None:
        self.text_in.open(
            "Load file",
            self.click_confirm_load,
            self.session_title,
            description_tooltip="Load from file name (omit the file extension, .json)."
        )
        self.print("Choose a file name to load (omit the file extension, .json)")

    def click_confirm_load(self, change: dict) -> None:
        file_name = self.text_in.value
        self.load(f"{file_name}.json")
        self._update_tabs_from_model()
        self.node_presenter.clear_output()
        self.print(f"Session loaded from {file_name}.json")
        self.text_in.clear()

    def click_node_help(self, change: dict) -> None:
        def _pretty_docstring(node_class):
            """
            If we just pass a string, `display` doesn't resolve newlines.
            If we pass a `print`ed string, `display` also shows the `None` value returned by `print`
            So we use this ugly hack.
            """
            string = f"{node_class.__name__.replace('_Node', '')}:\n{node_class.__doc__}"
            return HTML(string.replace("\n", "<br>").replace("\t", "&emsp;").replace(" ", "&nbsp;"))

        self.print(_pretty_docstring(self.new_node_class))

    def click_add_node(self, change: dict) -> None:
        self.flow_canvas.add_node(10, 10, self.new_node_class)

    def click_delete_node(self, change: dict) -> None:
        self.flow_canvas.delete_selected()

    def click_create_script(self, change: dict) -> None:
        self.create_script()
        self._update_tabs_from_model()
        self.script_tabs.selected_index = self.n_scripts - 1
        self.active_script_index = self.script_tabs.selected_index
        self.flow_canvas.redraw()

    def click_rename_script(self, change: dict) -> None:
        self.text_in.open(
            "New name",
            self.click_confirm_rename,
            self.script.title,
            description_tooltip="New script name"
        )
        self.print("Choose a new name for the current script")

    def click_confirm_rename(self, change: dict) -> None:
        new_name = self.text_in.value
        old_name = self.script.title
        rename_success = self.rename_script(new_name)
        if rename_success:
            self.script_tabs.set_title(self.active_script_index, new_name)
            self.print(f"Script '{old_name}' renamed '{new_name}'")
        else:
            self.print(f"INVALID NAME: Failed to rename script '{self.script.title}' to '{new_name}'.")

    def click_delete_script(self, change: dict) -> None:
        self.delete_script()
        self._update_tabs_from_model()

    def click_zero_location(self, change: dict) -> None:
        self.flow_canvas.x = 0
        self.flow_canvas.y = 0
        self.flow_canvas.redraw()

    def click_zoom_in(self, change: dict) -> None:
        self.flow_canvas.zoom_in()

    def click_zoom_out(self, change: dict) -> None:
        self.flow_canvas.zoom_out()

    def click_input_text_cancel(self, change: dict) -> None:
        self.text_in.clear()
        self.text_out.clear()

    def change_script_tabs(self, change: dict):
        if change['name'] == 'selected_index' and change['new'] is not None:
            self.text_in.clear()
            self.flow_canvas.deselect_all()
            if self.script_tabs.selected_index == self.n_scripts:
                self.create_script()
                self._update_tabs_from_model()
            else:
                self.active_script_index = self.script_tabs.selected_index
            self.flow_canvas.redraw()

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

    def print(self, msg: str):
        self.text_out.print(msg)
