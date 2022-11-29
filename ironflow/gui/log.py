# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Control the underlying Ryven logging system, and route logs to a widget.
"""

from __future__ import annotations

import sys
from io import TextIOBase
from typing import TYPE_CHECKING

import ipywidgets as widgets
from pyiron_base.interfaces.singleton import Singleton

from ironflow.gui.base import Screen

if TYPE_CHECKING:
    from ironflow.model.model import HasSession


class StdOutPut(TextIOBase):
    """
    Helper class that can be assigned to stdout and/or stderr,  passing string to a widget
    """

    def __init__(self):
        self.output = widgets.Output()

    def write(self, s):
        self.output.append_stdout(s)


class LogController(metaclass=Singleton):
    """
    Singleton pattern ensures that whatever `sys.stdout/err` was at the beginning of the session gets preserved.
    """

    def __init__(self):
        self.stdoutput = StdOutPut()
        self._standard_stdout = sys.stdout
        self._standard_stderr = sys.stderr

    @property
    def output(self):
        return self.stdoutput.output

    def log_to_display(self):
        sys.stdout = self.stdoutput
        sys.stderr = self.stdoutput

    def log_to_stdout(self):
        sys.stdout = self._standard_stdout
        sys.stderr = self._standard_stderr


class LogGUI(Screen):
    """
    A class that can redirect stdout and stderr to a widget, and gives controls for both this and toggling the
    Ryven logger.
    """

    def __init__(self, model: HasSession, enable_ryven_log: bool, log_to_display: bool):
        self.model = model
        self._log_controller = LogController()

        if log_to_display:
            self.log_to_display()

        self.ryven_log_button = widgets.Checkbox(
            value=enable_ryven_log, description="Use Ryven's InfoMsgs system"
        )
        self.display_log_button = widgets.Checkbox(
            value=log_to_display, description="Route stdout to ironflow"
        )
        self.clear_button = widgets.Button(
            description="Clear", tooltip="Clear the log output and flush the stdout."
        )

        self.ryven_log_button.observe(self._toggle_ryven_log)
        self.display_log_button.observe(self._toggle_display_log)
        self.clear_button.on_click(self._click_clear)

        self._screen = widgets.VBox(
            [
                widgets.HBox(
                    [self.display_log_button, self.ryven_log_button, self.clear_button],
                    layout=widgets.Layout(min_height="35px"),
                ),
                widgets.HBox([self.output], layout=widgets.Layout(height="435px")),
            ],
        )

    @property
    def screen(self):
        return self._screen

    @property
    def output(self):
        return self._log_controller.output

    def log_to_display(self):
        self._log_controller.log_to_display()

    def log_to_stdout(self):
        self._log_controller.log_to_stdout()

    def _toggle_ryven_log(self, change: dict):
        if change["name"] == "value":
            if change["new"]:
                self.model.session.info_messenger().enable()
            else:
                self.model.session.info_messenger().disable()

    def _toggle_display_log(self, change: dict):
        if change["name"] == "value":
            if change["new"]:
                self.log_to_display()
            else:
                self.log_to_stdout()

    def _click_clear(self, button: widgets.Button):
        self.output.clear_output()
        self._log_controller.stdoutput.flush()
