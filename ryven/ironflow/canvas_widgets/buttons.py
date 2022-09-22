# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import annotations

from abc import ABC, abstractmethod

from ryvencore.NodePort import NodePort, NodeInput, NodeOutput

from ryven.ironflow.canvas_widgets.base import CanvasWidget, HideableWidget
from ryven.ironflow.canvas_widgets.layouts import ButtonLayout


from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ryven.ironflow.canvas_widgets.base import Number
    from ryven.ironflow.canvas_widgets.nodes import NodeWidget, RepresentableNodeWidget


__author__ = "Liam Huber, Joerg Neugebauer"
__copyright__ = (
    "Copyright 2022, Max-Planck-Institut für Eisenforschung GmbH - "
    "Computational Materials Design (CM) Department"
)
__version__ = "0.1"
__maintainer__ = "Liam Huber"
__email__ = "liamhuber@greyhavensolutions.com"
__status__ = "production"
__date__ = "Sept 21, 2022"


class ButtonWidget(CanvasWidget, ABC):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: NodeWidget,
            layout: ButtonLayout,
            selected: bool = False,
            title: str = "Button",
            pressed: Optional[bool] = False,
    ):
        super().__init__(x, y, parent, layout, selected)
        self.title = title
        self.pressed = pressed

    def on_click(self, last_selected_object: Optional[CanvasWidget]) -> CanvasWidget | None:
        if self.pressed:
            self.unpress()
        else:
            self.press()
        self.deselect()
        return last_selected_object

    def press(self):
        self.pressed = True
        self.on_pressed()
        # Ok, now here is a weird hack:
        self.gui.node_controller.draw()
        # This way, if a button causes some change in node-state, it gets reflected in the node_controller,
        # e.g. if we `run` or `remove` some job, but a nodestream node is taking that job as input.
        # Performance and usability hits are minimal, but from a maintenance perspective it is super bad, confusing,
        # and hard to maintain, so it would be much nicer in the future to find a way to hook the node_controller right
        #  onto input updates on the nodes

    def unpress(self):
        self.pressed = False
        self.on_unpressed()

    @abstractmethod
    def on_pressed(self):
        pass

    @abstractmethod
    def on_unpressed(self):
        pass

    def draw_shape(self) -> None:
        self.canvas.fill_style = self.layout.pressed_color if self.pressed else self.layout.background_color
        self.canvas.fill_rect(
            self.x,
            self.y,
            self.width,
            self.height,
        )

    def draw_title(self) -> None:
        self.canvas.font = self.layout.font_string
        self.canvas.fill_style = self.layout.font_color
        x = self.x + (self.width * 0.1)
        y = self.y + (self.height * 0.05) + self.layout.font_size
        self.canvas.fill_text(self.title, x, y)


class RepresentButtonWidget(ButtonWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: RepresentableNodeWidget,
            layout: ButtonLayout,
            selected: bool = False,
            title="SHOW",
    ):
        super().__init__(x, y, parent, layout, selected, title=title)

    def on_pressed(self):
        self.gui.node_presenter.node_widget = self.parent

    def on_unpressed(self):
        self.gui.node_presenter.node_widget = None


class ExpandCollapseButtonWidget(ButtonWidget, HideableWidget, ABC):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: NodeWidget,
            layout: ButtonLayout,
            selected: bool = False,
            pressed: bool = False,
            visible: bool = True,
            title: Optional[str] = None,
            size: Optional[Number] = None,
    ):
        if size is not None:
            layout.width = size
            layout.height = size
        layout.background_color = parent.node.color
        layout.pressed_color = parent.node.color

        ButtonWidget.__init__(self, x=x, y=y, parent=parent, layout=layout, selected=selected, title=title,
                              pressed=pressed)
        HideableWidget.__init__(self, x=x, y=y, parent=parent, layout=layout, selected=selected, title=title,
                                visible=visible)

    def on_pressed(self):
        self.hide()

    def on_unpressed(self):
        self.show()

    def draw_shape(self) -> None:
        self.canvas.fill_style = self.layout.pressed_color if self.pressed else self.layout.background_color
        self.canvas.fill_polygon(self._points)

    @property
    @abstractmethod
    def _points(self) -> list[tuple[Number, Number]]:
        pass


class ExpandButtonWidget(ExpandCollapseButtonWidget):
    @property
    def _points(self) -> list[tuple[Number, Number]]:
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + 0.5 * self.width, self.y + self.height)
        ]

    def on_pressed(self):
        super().on_pressed()
        self.parent.expand_io()


class CollapseButtonWidget(ExpandCollapseButtonWidget):
    @property
    def _points(self) -> list[tuple[Number, Number]]:
        return [
            (self.x, self.y + self.height),
            (self.x + 0.5 * self.width, self.y),
            (self.x + self.width, self.y + self.height)
        ]

    def on_pressed(self):
        super().on_pressed()
        self.parent.collapse_io()


class ExecButtonWidget(ButtonWidget):
    def __init__(
            self,
            x: Number,
            y: Number,
            parent: NodeWidget,
            layout: ButtonLayout,
            port: NodePort,
            selected: bool = False,
            title: str = "Exec",
            pressed: Optional[bool] = False,
    ):
        super().__init__(
            x=x,
            y=y,
            parent=parent,
            layout=layout,
            selected=selected,
            title=port.label_str if port.label_str != '' else title,
            pressed=pressed
        )
        self.port = port

    def on_pressed(self):
        self.unpress()
        if isinstance(self.port, NodeInput):
            self.port.update()
        elif isinstance(self.port, NodeOutput):
            self.port.exec()

    def on_unpressed(self):
        pass
