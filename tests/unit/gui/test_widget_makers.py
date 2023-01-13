# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase

import ipywidgets as widgets

from ironflow.gui.widget_makers import DrawsWidgets, draws_widgets


class Child(DrawsWidgets):
    def __new__(cls, some_string, *args, some_float=1.0, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, some_string, *args, some_float=1.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.some_string = some_string
        self.some_float = some_float
        self.hbox = widgets.HBox([])
        self.widget.children = [self.hbox]

    @draws_widgets
    def draw(self):
        self.widget.children = [self.hbox, widgets.FloatSlider(value=self.some_float)]
        self.hbox.children = [
            widgets.Label(self.some_string),
            widgets.Button(icon="compress"),
            widgets.Text()
        ]
        return self.widget

    def clear(self):
        self.widget.children = [self.hbox]
        self.hbox.children = []
        super().clear()


class TestDrawsWidgets(TestCase):
    def n_widgets(self):
        return len(widgets.Widget.widgets)

    def test(self):
        n_widgets_0 = self.n_widgets()

        foo = Child("foo")
        n_widgets_init = self.n_widgets()
        self.assertEqual(n_widgets_init - n_widgets_0, len(foo._init_widgets))

        foo.draw()
        n_widgets_draw = self.n_widgets()
        self.assertEqual(n_widgets_draw - n_widgets_init, len(foo._drawn_widgets))

        foo.clear()
        n_widgets_clear = self.n_widgets()
        self.assertEqual(n_widgets_clear, n_widgets_init)

        foo.draw()  # Re-populate the drawn widget list
        foo.close()
        n_widgets_close = self.n_widgets()
        self.assertEqual(n_widgets_close, n_widgets_0)

        foo = Child("bar")
        foo = Child("baz")
        self.assertEqual(
            n_widgets_init,
            self.n_widgets(),
            msg="Reinstantiating to the same var should trigger del and purge widgets"
        )

        del foo
        self.assertEqual(n_widgets_0, self.n_widgets())
