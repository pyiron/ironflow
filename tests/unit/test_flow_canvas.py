# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase
from ryven.ironflow.gui import GUI
import os


class TestCanvasObect(TestCase):

    def setUp(self):
        self.gui = GUI('gui')
        self.canvas = self.gui.flow_canvas

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(os.path.join('.', "pyiron.log"))
        except FileNotFoundError:
            pass

    def test_remove_node_from_flow(self):
        flow = self.canvas.flow
        val_node = self.gui._nodes_dict['nodes']['val']
        results_node = self.gui._nodes_dict['nodes']['result']

        self.canvas.add_node(0, 0, val_node)
        self.canvas.add_node(0, 0, results_node)
        c12 = flow.connect_nodes(self.canvas.objects_to_draw[0].outputs[0], self.canvas.objects_to_draw[1].inputs[0])
        self.assertEqual(2, len(flow.nodes))
        self.assertEqual(1, len(flow.connections))
        self.canvas.objects_to_draw[0].select()
        self.canvas.delete_selected()
        self.assertEqual(1, len(flow.nodes), msg="Expected exactly one node to get deleted.")
        self.assertEqual(0, len(flow.connections), msg="Expected the connection to get automatically deleted")