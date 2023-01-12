# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase

import ipywidgets as widgets

from ironflow.gui.draws_widgets import DrawsWidgets


class Child(DrawsWidgets):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hbox = widgets.HBox([])

    def _draw(self):
        drawn = [
            widgets.Label("Foo"),
            widgets.Button(icon="compress"),
            widgets.Text()
        ]
        self.hbox.children = drawn

    def _clear(self):
        self.hbox.children = []


class TestDrawsWidgets(TestCase):
    def n_widgets(self):
        return len(widgets.Widget.widgets)

    def test(self):
        n_widgets_0 = self.n_widgets()

        foo = Child()
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

        foo = Child()
        foo = Child()
        self.assertEqual(
            n_widgets_init,
            self.n_widgets(),
            msg="Reinstantiating to the same var should trigger del and purge widgets"
        )

        del foo
        self.assertEqual(n_widgets_0, self.n_widgets())
