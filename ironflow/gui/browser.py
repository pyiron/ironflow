# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Provide access to the `pyiron_gui`
"""

from __future__ import annotations

import ipywidgets as widgets

from pyiron_atomistics import Project
from pyiron_gui import ProjectBrowser

from ironflow.gui.draws_widgets import DrawsWidgets


class BrowserGUI(DrawsWidgets):
    main_widget_class = widgets.VBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.widget = self.main_widget_class([])
        self.top_level_project = Project(".")
        self.widget.layout.height = "470px"
        self.project_browser = ProjectBrowser(self.top_level_project, Vbox=self.widget)
        self.project_browser.refresh()
