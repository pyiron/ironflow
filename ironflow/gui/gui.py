# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Top-level objects for getting the front and back end (and various parts of the front end) to talk to each other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type

import ipywidgets as widgets

from ironflow.gui.browser import BrowserGUI
from ironflow.gui.draws_widgets import DrawsWidgets
from ironflow.gui.log import LogGUI
from ironflow.gui.workflows.screen import WorkflowsGUI
from ironflow.model.model import HasSession

if TYPE_CHECKING:
    from ironflow.model.node import Node
    from ironflow.model.port import NodeInput, NodeOutput


class GUI(HasSession, DrawsWidgets):
    """
    The main ironflow object, connecting a ryven backend with a jupyter-friendly ipywidgets+ipycanvas frontend.

    Methods:
        draw: Build the ipywidget to interact with.
        register_user_node: Register with ironflow a new node from the current python process.
    """

    main_widget_class = widgets.Tab

    def __new__(
        cls,
        session_title: str,
        *args,
        extra_nodes_packages: Optional[list] = None,
        script_title: Optional[str] = None,
        enable_ryven_log: bool = True,
        log_to_display: bool = True,
        **kwargs,
    ):
        return super().__new__(cls, *args, **kwargs)

    def __init__(
        self,
        session_title: str,
        *args,
        extra_nodes_packages: Optional[list] = None,
        script_title: Optional[str] = None,
        enable_ryven_log: bool = True,
        log_to_display: bool = True,
        **kwargs,
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
        self.log = LogGUI(
            model=self, enable_ryven_log=enable_ryven_log, log_to_display=log_to_display
        )
        # Log screen needs to be instantiated before the rest of the init so we know whether to look at the ryven log
        # as we boot

        super().__init__(
            *args,
            session_title=session_title,
            extra_nodes_packages=extra_nodes_packages,
            enable_ryven_log=enable_ryven_log,
            **kwargs,
        )

        self.workflows = WorkflowsGUI(gui=self)
        self.browser = BrowserGUI()

        try:
            self.load(f"{self.session_title}.json")
            print(f"Loaded session data for {self.session_title}")
        except FileNotFoundError:
            print(
                f"No session data found for {self.session_title}, making a new script."
            )
            self.create_script(script_title)
        self.workflows.update_tabs()

        self.widget.children = [
            self.workflows.widget,
            self.browser.widget,
            self.log.widget,
        ]
        self.widget.set_title(0, "Workflows")
        self.widget.set_title(1, "Browser")
        self.widget.set_title(2, "Log")

        self.widget.observe(self._change_screen_tabs)

    def create_script(
        self,
        title: Optional[str] = None,
        create_default_logs: bool = True,
        data: Optional[dict] = None,
    ) -> None:
        super().create_script(
            title=title, create_default_logs=create_default_logs, data=data
        )
        self.workflows.add_flow(self.flow)

    @property
    def selected_node(self) -> Node | None:
        return self.workflows.selected_node

    @property
    def new_node_class(self):
        return self.workflows.new_node_class

    def serialize(self) -> dict:
        data = super().serialize()
        currently_active = self.active_script_index
        for i_script, script in enumerate(self.session.scripts):
            all_data = data["scripts"][i_script]["flow"]["nodes"]
            self.active_script_index = i_script
            for i, node_widget in enumerate(self.workflows.flow_canvas.objects_to_draw):
                all_data[i]["pos x"] = node_widget.x
                all_data[i]["pos y"] = node_widget.y
        self.active_script_index = currently_active
        return data

    def load_from_data(self, data: dict) -> None:
        super().load_from_data(data)
        self.workflows.load_from_data(data)

    def register_node(self, node_class: Type[Node], node_group: Optional[str] = None):
        # Inherited __doc__ still applies just fine, all we do here is update a menu item afterwards.
        super().register_node(node_class=node_class, node_group=node_group)
        try:
            self.workflows.update_nodes_selector(self.nodes_dictionary)
        except AttributeError:
            pass  # It's not defined yet in the super().__init__ call, which is fine

    def log_to_display(self):
        self.log.log_to_display()

    def log_to_stdout(self):
        self.log.log_to_stdout()

    def build_recommendations(self, port: NodeInput | NodeOutput):
        self.recommend_nodes(port)
        # self.workflows.flow_box.update_nodes(self.nodes_dictionary)

    def clear_recommendations(self):
        self.clear_recommended_nodes()
        # self.workflows.flow_box.update_nodes(self.nodes_dictionary)

    def draw(self):
        return self.widget

    # Type hinting for unused `change` argument in callbacks taken from ipywidgets docs:
    # https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Events.html#Traitlet-events

    def _change_screen_tabs(self, change: dict):
        if change["name"] == "selected_index" and change["new"] == 1:
            self.browser.project_browser.refresh()

    def close(self):
        self.log.close()
        self.browser.close()
        self.workflows.close()
        super().close()
