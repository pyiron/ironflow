# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase
from ryven.ironflow.Gui import GUI
import os


class TestCanvasObect(TestCase):

    def setUp(self):
        self.gui = GUI(packages=["../../ryven/std", "../../ryven/nodes/built_in/"])
        self.canvas = self.gui.canvas_widget

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(os.path.join('.', "pyiron.log"))
        except FileNotFoundError:
            pass

    def test_remove_node_from_flow(self):
        flow = self.canvas.script.flow
        val_node = self.gui._nodes_dict['nodes']['val']
        results_node = self.gui._nodes_dict['nodes']['val']

        n1 = flow.create_node(node_class=val_node)
        n2 = flow.create_node(node_class=results_node)
        c12 = flow.connect_nodes(n1.outputs[0], n2.inputs[0])
        self.assertEqual(2, len(flow.nodes))
        self.assertEqual(1, len(flow.connections))
        self.canvas._remove_node_from_flow(n1)
        self.assertEqual(1, len(flow.nodes), msg="Expected exactly one node to get deleted.")
        self.assertEqual(0, len(flow.connections), msg="Expected the connection to get automatically deleted")