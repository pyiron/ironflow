# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Top-level objects for getting the front and back end (and various parts of the front end) to talk to each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type

import ipywidgets as widgets

from ironflow.gui.boxes import (
    Toolbar,
    NodeController,
    NodePresenter,
    TextOut,
    UserInput,
    FlowBox,
)
from ironflow.gui.canvas_widgets import FlowCanvas
from ironflow.gui.log import LogScreen
from ironflow.model.model import HasSession
from ironflow.utils import display_string

if TYPE_CHECKING:
    from ironflow.model.node import Node
    from ironflow.gui.canvas_widgets.nodes import NodeWidget


class GUI(HasSession):
    """
    The main ironflow object, connecting a ryven backend with a jupyter-friendly ipywidgets+ipycanvas frontend.

    Methods:
        draw: Build the ipywidget to interact with.
        register_user_node: Register with ironflow a new node from the current python process.
    """

    def __init__(
        self,
        session_title: str,
        extra_nodes_packages: Optional[list] = None,
        script_title: Optional[str] = None,
        enable_ryven_log: bool = True,
        log_to_display: bool = True,
    ):
        """
        Create a new gui instance.

        Args:
            session_title (str): Title of the session to use. Will look for a json file of the same name and try to
                read it. If no such file exists, simply makes a new script instead.
            extra_nodes_packages (list | None): an optional list of nodes to register at instantiation. List items can
                be either a list of `ironflow.model.node.Node` subclasses, a module containing such subclasses, or a .py
                file of a module containing such subclasses. In all cases only those subclasses with the name pattern
                `*_Node` will be registered. (Default is None, don't register any extra nodes.)
            script_title (str|None): Title for an initial script. (Default is None, which generates "script_0" if a
                new script is needed on initialization, i.e. when existing session data cannot be read.)
            enable_ryven_log (bool): Activate Ryven's logging system to catch Ryven actions and node errors. (Default
                is True.)
            log_to_display (bool): Re-route stdout (and node error's captured by the Ryven logger, if activated) to a
                separate output widget. (Default is True.)
        """
        self.log_screen = LogScreen(
            gui=self, enable_ryven_log=enable_ryven_log, log_to_display=log_to_display
        )
        # Log screen needs to be instantiated before the rest of the init so we know whether to look at the ryven log
        # as we boot

        super().__init__(
            session_title=session_title,
            extra_nodes_packages=extra_nodes_packages,
            enable_ryven_log=enable_ryven_log,
        )

        self.flow_canvases = []
        self.toolbar = Toolbar()
        self.node_controller = NodeController(self)
        self.node_presenter = NodePresenter()
        self.text_out = TextOut()
        self.input = UserInput()
        self.flow_box = FlowBox(self.nodes_dictionary)

        try:
            self.load(f"{self.session_title}.json")
            print(f"Loaded session data for {self.session_title}")
        except FileNotFoundError:
            print(
                f"No session data found for {self.session_title}, making a new script."
            )
            self.create_script(script_title)
        self.update_tabs()

    def create_script(
        self,
        title: Optional[str] = None,
        create_default_logs: bool = True,
        data: Optional[dict] = None,
    ) -> None:
        super().create_script(
            title=title, create_default_logs=create_default_logs, data=data
        )
        self.flow_canvases.append(FlowCanvas(gui=self))

    def delete_script(self) -> None:
        self.flow_canvases.pop(self.active_script_index)
        self.node_controller.close()
        self.node_presenter.close()
        super().delete_script()

    @property
    def flow_canvas(self):
        return self.flow_canvases[self.active_script_index]

    @property
    def new_node_class(self):
        return self.flow_box.node_selector.new_node_class

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
        self.flow_canvases = []
        for i_script, script in enumerate(self.session.scripts):
            flow_canvas = FlowCanvas(gui=self, flow=script.flow)
            all_data = data["scripts"][i_script]["flow"]["nodes"]
            for i_node, node in enumerate(script.flow.nodes):
                flow_canvas.load_node(
                    all_data[i_node]["pos x"], all_data[i_node]["pos y"], node
                )
            flow_canvas._built_object_to_gui_dict()
            flow_canvas.redraw()
            self.flow_canvases.append(flow_canvas)

    def register_node(self, node_class: Type[Node], node_group: Optional[str] = None):
        # Inherited __doc__ still applies just fine, all we do here is update a menu item afterwards.
        super().register_node(node_class=node_class, node_group=node_group)
        try:
            self.flow_box.node_selector.update(self.nodes_dictionary)
        except AttributeError:
            pass  # It's not defined yet in the super().__init__ call, which is fine

    def update_tabs(self):
        self.flow_box.update_tabs(
            outputs=[fc.output for fc in self.flow_canvases],
            titles=[fc.title for fc in self.flow_canvases],
            active_index=self.active_script_index,
        )
        for fc in self.flow_canvases:
            fc.display()

    def open_node_control(self, node: Node) -> None:
        self.node_controller.draw_for_node(node)

    def update_node_control(self) -> None:
        self.node_controller.draw()

    def close_node_control(self) -> None:
        self.node_controller.node = None
        self.node_controller.clear_output()

    def ensure_node_not_controlled(self, node: Node) -> None:
        if self.node_controller.node == node:
            self.node_controller.draw_for_node(None)

    def open_node_presenter(self, node_widget: NodeWidget):
        self.node_presenter.node_widget = node_widget

    def update_node_presenter(self):
        self.node_presenter.draw()

    def close_node_presenter(self):
        self.node_presenter.close()

    def ensure_node_not_presented(self, node_widget: NodeWidget) -> None:
        if self.node_presenter.node_widget == node_widget:
            self.node_presenter.node_widget = None

    def redraw_active_flow_canvas(self):
        self.flow_canvas.redraw()

    def print(self, msg: str):
        self.text_out.print(msg)

    def log_to_display(self):
        self.log_screen.log_to_display()

    def log_to_stdout(self):
        self.log_screen.log_to_stdout()

    def draw(self) -> widgets.VBox:
        """
        Build the gui.

        Returns:
            ipywidgets.VBox: The gui.
        """

        # Wire callbacks
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

        flow_screen = widgets.VBox(
            [
                self.toolbar.box,
                self.input.box,
                self.flow_box.box,
                self.text_out.box,
                widgets.HBox([self.node_controller.box, self.node_presenter.box]),
            ]
        )

        window = widgets.Tab([flow_screen, self.log_screen.box])
        window.set_title(0, "Workflow")
        window.set_title(1, "Log")
        return window

    # Type hinting for unused `change` argument in callbacks taken from ipywidgets docs:
    # https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Events.html#Traitlet-events
    def _change_alg_mode_dropdown(self, change: dict) -> None:
        # Current behaviour: Updates the flow mode for all scripts
        # Todo: Change only for the active script, and update the dropdown on tab (script) switching
        for script in self.session.scripts:
            script.flow.set_algorithm_mode(self.toolbar.alg_mode_dropdown.value)

    def _click_save(self, change: dict) -> None:
        self.input.open_text(
            "Save file",
            self._click_confirm_save,
            self.session_title,
            description_tooltip="Save to file name (omit the file extension, .json)",
        )
        self.print("Choose a file name to save to (omit the file extension, .json)")

    def _click_confirm_save(self, change: dict) -> None:
        file_name = self.input.text
        self.save(f"{file_name}.json")
        self.print(f"Session saved to {file_name}.json")
        self.input.clear()

    def _click_load(self, change: dict) -> None:
        self.input.open_text(
            "Load file",
            self._click_confirm_load,
            self.session_title,
            description_tooltip="Load from file name (omit the file extension, .json).",
        )
        self.print("Choose a file name to load (omit the file extension, .json)")

    def _click_confirm_load(self, change: dict) -> None:
        file_name = self.input.text
        self.load(f"{file_name}.json")
        self.update_tabs()
        self.node_presenter.clear_output()
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
        self.create_script()
        self.update_tabs()

    def _click_rename_script(self, change: dict) -> None:
        self.input.open_text(
            "New name",
            self._click_confirm_rename,
            self.script.title,
            description_tooltip="New script name",
        )
        self.print("Choose a new name for the current script")

    def _click_confirm_rename(self, change: dict) -> None:
        new_name = self.input.text
        old_name = self.script.title
        rename_success = self.rename_script(new_name)
        if rename_success:
            self.flow_box.script_tabs.set_title(self.active_script_index, new_name)
            self.print(f"Script '{old_name}' renamed '{new_name}'")
        else:
            self.print(
                f"INVALID NAME: Failed to rename script '{self.script.title}' to '{new_name}'."
            )

    def _click_delete_script(self, change: dict) -> None:
        self.input.open_bool(
            f"Delete the entire script {self.script.title}?",
            self._click_confirm_delete_script,
        )

    def _click_confirm_delete_script(self, change: dict) -> None:
        script_name = self.script.title
        self.delete_script()
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
            if self.flow_box.script_tabs.selected_index == self.n_scripts:
                self.create_script()
                self.update_tabs()
            else:
                self.active_script_index = self.flow_box.script_tabs.selected_index
