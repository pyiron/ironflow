# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
An interface for doing the visual scripting
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ipywidgets as widgets

from ironflow.gui.base import Screen
from ironflow.gui.workflows.boxes.flow import FlowBox
from ironflow.gui.workflows.boxes.node_interface.control import NodeController
from ironflow.gui.workflows.boxes.node_interface.representation import NodePresenter
from ironflow.gui.workflows.boxes.text_output import TextOut
from ironflow.gui.workflows.boxes.toolbar import Toolbar
from ironflow.gui.workflows.boxes.user_input import UserInput
from ironflow.gui.workflows.canvas_widgets.flow import FlowCanvas
from ironflow.utils import display_string

if TYPE_CHECKING:
    from ironflow.model.model import HasSession
    from ironflow.gui.workflows.canvas_widgets.nodes import NodeWidget
    from ironflow.model.flow import Flow
    from ironflow.model.node import Node


class WorkflowsGUI(Screen):
    def __init__(self, model: HasSession):
        self.model = model
        self.flow_canvases = []

        self.toolbar = Toolbar()
        self.node_controller = NodeController(self)
        self.node_presenter = NodePresenter()
        self.text_out = TextOut()
        self.input = UserInput()
        self.flow_box = FlowBox(self.model.nodes_dictionary)

        self.toolbar.alg_mode_dropdown.observe(
            self._change_alg_mode_dropdown, names="value"
        )
        self.toolbar.buttons.help_node.on_click(self._click_node_help)
        self.toolbar.buttons.load.on_click(self._click_load)
        self.toolbar.buttons.save.on_click(self._click_save)
        self.toolbar.buttons.add_node.on_click(self._click_add_node)
        self.toolbar.buttons.delete_node.on_click(self._click_delete_node)
        self.toolbar.buttons.create_script.on_click(self._click_create_script)
        self.toolbar.buttons.rename_script.on_click(self._click_rename_script)
        self.toolbar.buttons.delete_script.on_click(self._click_delete_script)
        self.toolbar.buttons.zero_location.on_click(self._click_zero_location)
        self.toolbar.buttons.zoom_in.on_click(self._click_zoom_in)
        self.toolbar.buttons.zoom_out.on_click(self._click_zoom_out)
        self.flow_box.script_tabs.observe(self._change_script_tabs)

        self._screen = widgets.VBox(
            [
                self.toolbar.box,
                self.input.box,
                self.flow_box.box,
                self.text_out.box,
                widgets.HBox([self.node_controller.box, self.node_presenter.box]),
            ]
        )

    @property
    def new_node_class(self):
        return self.flow_box.node_selector.new_node_class

    @property
    def flow_canvas(self):
        return self.flow_canvases[self.model.active_script_index]

    @property
    def selected_node(self) -> Node | None:
        selected = self.flow_canvas.get_selected_objects()
        return selected[0].node if len(selected) > 0 else None

    def update_tabs(self):
        self.flow_box.update_tabs(
            outputs=[fc.output for fc in self.flow_canvases],
            titles=[fc.title for fc in self.flow_canvases],
            active_index=self.model.active_script_index,
        )
        for fc in self.flow_canvases:
            fc.display()

    def add_flow(self, flow: Flow):
        self.flow_canvases.append(FlowCanvas(screen=self, flow=flow))

    def load_from_data(self, data: dict):
        self.flow_canvases = []
        for i_script, script in enumerate(self.model.session.scripts):
            flow_canvas = FlowCanvas(screen=self, flow=script.flow)
            all_data = data["scripts"][i_script]["flow"]["nodes"]
            for i_node, node in enumerate(script.flow.nodes):
                flow_canvas.load_node(
                    all_data[i_node]["pos x"], all_data[i_node]["pos y"], node
                )
            flow_canvas._built_object_to_gui_dict()
            flow_canvas.redraw()
            self.flow_canvases.append(flow_canvas)

    def open_node_control(self, node: Node) -> None:
        self.node_controller.draw_for_node(node)

    def update_node_control(self) -> None:
        self.node_controller.update()

    def close_node_control(self) -> None:
        self.node_controller.clear()

    def ensure_node_not_controlled(self, node: Node) -> None:
        if self.node_controller.node == node:
            self.node_controller.clear()

    def open_node_presenter(self, node_widget: NodeWidget):
        self.node_presenter.draw_for_node_widget(node_widget)

    def update_node_presenter(self):
        self.node_presenter.update()

    def close_node_presenter(self):
        self.node_presenter.clear()

    def ensure_node_not_presented(self, node_widget: NodeWidget) -> None:
        if self.node_presenter.node_widget == node_widget:
            self.node_presenter.clear()

    def redraw_active_flow_canvas(self):
        self.flow_canvas.redraw()

    def print(self, msg: str):
        self.text_out.print(msg)

    def update_nodes_selector(self, nodes_dictionary: dict):
        self.flow_box.node_selector.update(nodes_dictionary)

    def delete_flow(self, i: int):
        self.flow_canvases.pop(i)
        self.node_controller.close()
        self.node_presenter.clear()

    @property
    def screen(self):
        return self._screen

    def _change_alg_mode_dropdown(self, change: dict) -> None:
        # Current behaviour: Updates the flow mode for all scripts
        # Todo: Change only for the active script, and update the dropdown on tab (script) switching
        for script in self.model.session.scripts:
            script.flow.set_algorithm_mode(self.toolbar.alg_mode_dropdown.value)

    def _click_save(self, change: dict) -> None:
        self.input.open_text(
            "Save file",
            self._click_confirm_save,
            self.model.session_title,
            description_tooltip="Save to file name (omit the file extension, .json)",
        )
        self.print("Choose a file name to save to (omit the file extension, .json)")

    def _click_confirm_save(self, change: dict) -> None:
        file_name = self.input.text
        self.model.save(f"{file_name}.json")
        self.print(f"Session saved to {file_name}.json")
        self.input.clear()

    def _click_load(self, change: dict) -> None:
        self.input.open_text(
            "Load file",
            self._click_confirm_load,
            self.model.session_title,
            description_tooltip="Load from file name (omit the file extension, .json).",
        )
        self.print("Choose a file name to load (omit the file extension, .json)")

    def _click_confirm_load(self, change: dict) -> None:
        file_name = self.input.text
        self.model.load(f"{file_name}.json")
        self.update_tabs()
        self.node_presenter.clear()
        self.print(f"Session loaded from {file_name}.json")
        self.input.clear()

    def _click_node_help(self, change: dict) -> None:
        self.print(
            display_string(
                f"{self.new_node_class.__name__.replace('_Node', '')}:\n{self.new_node_class.__doc__}"
            )
        )

    def _click_add_node(self, change: dict) -> None:
        self.flow_canvas.add_node(10, 10, self.new_node_class)

    def _click_delete_node(self, change: dict) -> None:
        self.flow_canvas.delete_selected()

    def _click_create_script(self, change: dict) -> None:
        self.model.create_script()
        self.update_tabs()

    def _click_rename_script(self, change: dict) -> None:
        self.input.open_text(
            "New name",
            self._click_confirm_rename,
            self.model.script.title,
            description_tooltip="New script name",
        )
        self.print("Choose a new name for the current script")

    def _click_confirm_rename(self, change: dict) -> None:
        new_name = self.input.text
        old_name = self.model.script.title
        rename_success = self.model.rename_script(new_name)
        if rename_success:
            self.flow_box.script_tabs.set_title(
                self.model.active_script_index, new_name
            )
            self.print(f"Script '{old_name}' renamed '{new_name}'")
        else:
            self.print(
                f"INVALID NAME: Failed to rename script '{self.model.script.title}' to '{new_name}'."
            )

    def _click_delete_script(self, change: dict) -> None:
        self.input.open_bool(
            f"Delete the entire script {self.model.script.title}?",
            self._click_confirm_delete_script,
        )

    def _click_confirm_delete_script(self, change: dict) -> None:
        script_name = self.model.script.title
        self.delete_flow(self.model.active_script_index)
        self.model.delete_script()
        self.update_tabs()
        self.print(f"Script {script_name} deleted")

    def _click_zero_location(self, change: dict) -> None:
        self.flow_canvas.x = 0
        self.flow_canvas.y = 0
        self.flow_canvas.redraw()

    def _click_zoom_in(self, change: dict) -> None:
        self.flow_canvas.zoom_in()

    def _click_zoom_out(self, change: dict) -> None:
        self.flow_canvas.zoom_out()

    def _click_input_text_cancel(self, change: dict) -> None:
        self.input.clear()
        self.text_out.clear()

    def _change_script_tabs(self, change: dict):
        if change["name"] == "selected_index" and change["new"] is not None:
            self.input.clear()
            self.flow_canvas.deselect_all()
            if self.flow_box.script_tabs.selected_index == self.model.n_scripts:
                self.model.create_script()
                self.update_tabs()
            else:
                self.model.active_script_index = (
                    self.flow_box.script_tabs.selected_index
                )
