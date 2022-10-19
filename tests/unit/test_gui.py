# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from unittest import TestCase
from ironflow.gui.gui import GUI
from ironflow.custom_nodes import Node, NodeInputBP, NodeOutputBP, dtypes
import os


class TestGUI(TestCase):

    def tearDown(self) -> None:
        try:
            os.remove("pyiron.log")
        except FileNotFoundError:
            pass

    def test_multiple_scripts(self):
        gui = GUI('foo')
        gui.flow_canvas.add_node(0, 0, gui.nodes_dictionary['nodes']['val'])
        gui.create_script()
        gui.flow_canvas.add_node(1, 1, gui.nodes_dictionary['nodes']['result'])
        canonical_file_name = f"{gui.session_title}.json"
        gui.save(canonical_file_name)
        new_gui = GUI('something_random')
        new_gui.load(canonical_file_name)

        self.assertEqual(
            0,
            new_gui._active_script_index,
            msg=f"Expected loaded sessions to start on the zeroth script, but got script {new_gui._active_script_index}"
        )

        for i in range(len(gui.session.scripts)):
            saved_node = gui.session.scripts[i].flow.nodes[0].title
            loaded_node = new_gui.session.scripts[i].flow.nodes[0].title
            self.assertEqual(
                saved_node,
                loaded_node,
                msg=f"Expected saved and loaded nodes to match, but got {saved_node} and {loaded_node}"
            )

        os.remove(canonical_file_name)

    def test_saving_and_loading(self):
        title = 'foo'
        gui = GUI(title)
        canvas = gui.flow_canvas
        flow = gui._session.scripts[0].flow

        canvas.add_node(0, 0, gui.nodes_dictionary['nodes']['val'])  # Need to create with canvas instead of flow
        canvas.add_node(1, 0, gui.nodes_dictionary['nodes']['result'])  # because serialization includes xy location
        n1, n2 = flow.nodes
        flow.connect_nodes(n1.outputs[0], n2.inputs[0])

        canonical_file_name = f"{gui.session_title}.json"
        with self.assertRaises(FileNotFoundError):
            gui.load(canonical_file_name)  # Or any other non-existent file

        gui.save(canonical_file_name)

        new_gui = GUI(title)
        self.assertNotEqual(new_gui._session, gui._session, msg="New instance expected to get its own session")
        # Maybe this will change in the future, but it's baked in the assumptions for now so let's make sure to test it

        new_flow = new_gui._session.scripts[0].flow
        self.assertEqual(0, len(new_flow.nodes), msg="Fresh GUI shouldn't have any nodes yet.")
        self.assertEqual(0, len(new_flow.connections), msg="Fresh GUI shouldn't have any connections yet.")

        new_gui.load(canonical_file_name)
        new_flow = new_gui._session.scripts[0].flow  # Session script gets reloaded, so grab this again
        print(new_gui._session.scripts, new_gui._session.scripts[0].flow)
        self.assertEqual(len(flow.nodes), len(new_flow.nodes), msg="Loaded GUI should recover nodes.")
        self.assertEqual(
            len(flow.connections),
            len(new_flow.connections),
            msg="Loaded GUI should recover connections."
        )

        os.remove(f"{title}.json")

    def test_user_node_registration(self):
        """Todo: This only tests the backend graph, need to test front end as well"""
        gui = GUI('foo')

        class MyNode(Node):
            title = "MyUserNode"
            init_inputs = [
                NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
            ]
            init_outputs = [
                NodeOutputBP(label="bar")
            ]
            color = 'cyan'

            def update_event(self, inp=-1):
                self.set_output_val(0, self.input(0) + 42)

        gui.register_user_node(MyNode)
        self.assertIn(MyNode, gui.session.nodes)

        gui.flow_canvas.add_node(0, 0, gui.nodes_dictionary["user"][MyNode.title])
        gui.flow.nodes[0].inputs[0].update(1)
        self.assertEqual(gui.flow.nodes[0].outputs[0].val, 43)

        class MyNode(Node):  # Update class
            title = "MyUserNode"
            init_inputs = [
                NodeInputBP(dtype=dtypes.Integer(default=1), label="foo")
            ]
            init_outputs = [
                NodeOutputBP(label="bar")
            ]
            color = 'cyan'

            def update_event(self, inp=-1):
                self.set_output_val(0, self.input(0) - 42)

        gui.register_user_node(MyNode)
        gui.flow.nodes[0].inputs[0].update(2)
        self.assertEqual(gui.flow.nodes[0].outputs[0].val, 44, msg="Expected to be using instance of old class")

        gui.flow_canvas.add_node(1, 1, gui.nodes_dictionary["user"][MyNode.title])
        gui.flow.nodes[1].inputs[0].update(2)
        self.assertEqual(gui.flow.nodes[1].outputs[0].val, -40, msg="New node instances should reflect updated class.")

        canonical_file_name = f"{gui.session_title}.json"
        gui.save(canonical_file_name)
        new_gui = GUI(gui.session_title)
        with self.assertRaises(Exception):  # User node not registered yet
            new_gui.load(canonical_file_name)

        new_gui.register_user_node(MyNode)
        new_gui.load(canonical_file_name)
        new_gui.flow.nodes[0].inputs[0].update(3)
        new_gui.flow.nodes[1].inputs[0].update(3)
        self.assertEqual(
            new_gui.flow.nodes[0].outputs[0].val,
            new_gui.flow.nodes[1].outputs[0].val,
            msg="The updated class was registered, so expect the same behaviour from both nodes now."
        )

        os.remove(canonical_file_name)

    def test_repeated_instantiation(self):
        gui = GUI('foo')
        id0 = str(gui.session.nodes[0].identifier)
        gui = GUI(gui.session_title)
        self.assertEqual(
            gui.session.nodes[0].identifier,
            id0,
            msg=f"Reinstantiating the gui should not change node identifiers, but got {id0} then "
                f"{gui.session.nodes[0].identifier}"
        )
