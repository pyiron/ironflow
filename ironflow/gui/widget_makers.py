# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
ipywidgets holds each instantiated widget independently, and they aren't released to the
garbage collector until their `close` method has been called and there are no further
references to their instance.

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


class HasWidgets(ABC, metaclass=AbstractPostCaller):
    """
    A mixin for classes that instantiate at least one ipywidgets widget during their
    `__init__` call and _no other widgets_ during their lifetime.

    Children will instantiate one `widget` attribute, which will be of type
    `main_widget_class`, which must be of type `ipywidgets.Box` (i.e. it takes a list of
    `children` as its first argument.)

    All widgets created in `__init__` are registered, and get closed and deleted with
    the `close` method.

    Note: Child classes will need to additionally define `__new__` to pull out all args
        and kwargs that are explicitly passed into the init, and pass on only
        `super().__new__(cls, *args, **kwargs)`.
    """

    main_widget_class: type[widgets.Box] = widgets.Box

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        obj.__n_widgets_at_init = len(widgets.Widget.widgets)
        return obj

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = self.main_widget_class([])
        self._init_widgets: list[widgets.Widget] = None

    def __post__(self):
        n_init_widgets = len(widgets.Widget.widgets) - self.__n_widgets_at_init
        if n_init_widgets > 0:
            self._init_widgets = list(widgets.Widget.widgets.values())[-n_init_widgets:]

    def close(self):
        self._delete_widget_list(self._init_widgets)

    @staticmethod
    def _delete_widget_list(widget_list: list[widgets.Widget]):
        while widget_list:
            w = widget_list.pop()
            w.close()
            del w

    def __del__(self):
        self.close()
        try:
            super().__del__()
        except AttributeError:
            pass


class DrawsWidgets(HasWidgets):
    """
    A mixin for classes that instantiate ipywidgets widgets on each `draw` call (and
    _only_ on `draw` calls and in `__init__`.

    New widgets instantiated in `draw` are stored in a list, and get closed and deleted
    on calls to `clear`, as well as `close` and on object deletion.

    All other behaviour is inherited from `HasWidgets`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drawn_widgets: list[widgets.Widget] = []

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

    @abstractmethod
    def _clear(self):
        pass

    def close(self):
        self.clear()
        super().close()
