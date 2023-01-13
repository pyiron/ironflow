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
from typing import Callable

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


def draws_widgets(fnc: Callable) -> Callable:
    """
    A decorator for any class methods that instantiate new widgets outside init.
    """
    def wrapper(self, *args, **kwargs):
        n_widgets_i = len(widgets.Widget.widgets)
        result = fnc(self, *args, **kwargs)
        n_widgets_drawn = len(widgets.Widget.widgets) - n_widgets_i
        self._drawn_widgets += list(widgets.Widget.widgets.values())[-n_widgets_drawn:]
        return result

    return wrapper


class DrawsWidgets(ABC, metaclass=AbstractPostCaller):
    """
    A mixin for classes that instantiate at least one ipywidgets widget during their
    `__init__` and _only_ instantiate other widgets in methods decorated with the
    `draws_widgets` decorator.

    All instantiated widgets are logged and can then be destroyed with the `clear`
    or `close` methods for those widgets instantiated since the last clear call or all
    instantiated widgets, respectively.

    Children will instantiate one `widget` attribute, which will be of type
    `main_widget_class`, which must be of type `ipywidgets.Box` (i.e. it takes a list of
    `children` as its first argument.)

    Note: Child classes will need to additionally define `__new__` to pull out all args
        and kwargs that are explicitly passed into the init, and pass on only
        `super().__new__(cls, *args, **kwargs)` upstream.
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
        self._drawn_widgets: list[widgets.Widget] = []

    def __post__(self):
        n_init_widgets = len(widgets.Widget.widgets) - self.__n_widgets_at_init
        self._init_widgets = list(widgets.Widget.widgets.values())[-n_init_widgets:]

    def clear(self):
        """
        Delete all widgets instantiated between the end of init and the last clear call.
        """
        self._delete_widget_list(self._drawn_widgets)

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

    def close(self):
        """
        Call clear, then delete all widgets instantiated in init.
        """
        self.clear()
        self._delete_widget_list(self._init_widgets)
