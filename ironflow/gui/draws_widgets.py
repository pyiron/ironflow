# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
ipywidgets holds each instantiated widget independently, and they aren't released to the
garbage collector until their `close` method has been called and there are no further
references to their isntance.

If we're not careful, this can lead to a massive bloat of the registered widgets and
memory strain. Here, we introduce a abstract class to help manage the closure of the
widgets we create.
"""

from __future__ import annotations
from abc import ABC, ABCMeta, abstractmethod

import ipywidgets as widgets


class PostCaller(type):
    """
    Inspired by [@Cam.Davidson.Pilon](https://stackoverflow.com/questions/795190/how-to-perform-common-post-initialization-tasks-in-inherited-classes)
    """

    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post__()
        return obj


class AbstractPostCaller(PostCaller, ABCMeta):
    pass


class DrawsWidgets(ABC, metaclass=AbstractPostCaller):
    """
    A mixin for classes that instantiate ipywidgets widgets to make sure they get
    cleaned up ok.

    Looks at the total number of widgets added to the widget registry at instantiation
    and stores them. Similarly, when `draw` is called, all the new widgets are stored.
    Then at `close` and `clear`, all or just the drawn widgets (respectively) are closed
    and deleted.

    The `__del__` method ensures that `close` gets called before the object is garbage
    collected.

    As long as all new widget instantiate happens inside `__init__` or `_draw` methods,
    they are automatically registered without any effort by the child class.
    """

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        obj.__n_widgets_at_init = len(widgets.Widget.widgets)
        return obj

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_widgets: list[widgets.Widget] = None
        self._drawn_widgets: list[widgets.Widget] = []

    def __post__(self):
        n_init_widgets = len(widgets.Widget.widgets) - self.__n_widgets_at_init
        if n_init_widgets > 0:
            self._init_widgets = list(widgets.Widget.widgets.values())[-n_init_widgets:]

    def draw(self):
        n_widgets_i = len(widgets.Widget.widgets)
        self._draw()
        n_widgets_drawn = len(widgets.Widget.widgets) - n_widgets_i
        self._drawn_widgets += list(widgets.Widget.widgets.values())[-n_widgets_drawn:]

    @abstractmethod
    def _draw(self):
        pass

    def clear(self):
        self._clear()
        self._delete_widget_list(self._drawn_widgets)

    def _delete_widget_list(self, widget_list: list[widgets.Widget]):
        while widget_list:
            w = widget_list.pop()
            w.close()
            del w

    @abstractmethod
    def _clear(self):
        pass

    def close(self):
        self.clear()
        self._delete_widget_list(self._init_widgets)

    def __del__(self):
        self.close()
        try:
            super().__del__()
        except AttributeError:
            pass
