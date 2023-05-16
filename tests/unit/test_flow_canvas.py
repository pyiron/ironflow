# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase
from ironflow.gui.gui import GUI
import os


class TestCanvasObect(TestCase):

    def setUp(self):
        self.gui = GUI('gui', log_to_display=False)
        self.canvas = self.gui.workflows.flow_canvas

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(os.path.join('.', "pyiron.log"))
        except (FileNotFoundError, PermissionError):
            pass

    def test_remove_node_from_flow(self):
        flow = self.canvas.flow

        lin_node = self.gui.nodes_dictionary['array']['Linspace']
        select_node = self.gui.nodes_dictionary['array']['Select']

        self.canvas.add_node(0, 0, lin_node)
        self.canvas.add_node(0, 0, select_node)
        c12 = flow.connect_nodes(
            self.canvas.objects_to_draw[0].outputs[0],
            self.canvas.objects_to_draw[1].inputs[0]
        )
        self.assertEqual(2, len(flow.nodes))
        self.assertEqual(1, len(flow.connections))
        self.canvas.objects_to_draw[0].select()
        self.canvas.delete_selected()
        self.assertEqual(
            1, len(flow.nodes), msg="Expected exactly one node to get deleted."
        )
        self.assertEqual(
            0,
            len(flow.connections),
            msg="Expected the connection to get automatically deleted"
        )