from ryven.NENV import *


class NodeBase(Node):

    def __init__(self, params):
        super().__init__(params)

        # here we could add some stuff for all nodes below...

from special_nodes import DualNodeBase 
import matplotlib.pylab as plt

import numpy as np
import random
from pyiron import Project


class Project_Node(NodeBase):
    """Create a pyiron project node"""
    # this __doc__ string will be displayed as tooltip in the editor

    title = 'Project'
    init_inputs = [
        NodeInputBP(dtype=dtypes.Char(default='.'), label='name'),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = '#aabb44'

    def update_event(self, inp=-1):
        pr = Project(self.input(0))
        self.set_output_val(0, pr)
        
        
class BulkStructure_Node(NodeBase):
    """Generate a bulk atomic structure"""
    # this __doc__ string will be displayed as tooltip in the editor

    title = 'BulkStructure'
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size='m'), label='project'),
        NodeInputBP(dtype=dtypes.Char(default='Fe'), label='element'),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = '#aabb44'

    def update_event(self, inp=-1):
        pr = self.input(0)
        self.set_output_val(0, pr.create.structure.bulk(self.input(1)))             


class IntRand_Node(NodeBase):
    """Generate a random number in a given range"""
    # this __doc__ string will be displayed as tooltip in the editor

    title = 'IntRandom'
    init_inputs = [
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(10, 100)), label='high'),
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(1, 100)), label='length'),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = '#aabb44'

    def update_event(self, inp=-1):
        val = np.random.randint(0, high=self.input(0), size=self.input(1)) 
        self.set_output_val(0, val)
        

class Linspace_Node(NodeBase):
    """Generate a linear mesh in a given range using np.linspace"""
    # this __doc__ string will be displayed as tooltip in the editor

    title = 'Linspace'
    init_inputs = [
        NodeInputBP(dtype=dtypes.Integer(default=1, bounds=(0, 100)), label='min'),
        NodeInputBP(dtype=dtypes.Integer(default=2, bounds=(0, 100)), label='max'),
        NodeInputBP(dtype=dtypes.Integer(default=10, bounds=(1, 100)), label='steps'),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = '#aabb44'

    def update_event(self, inp=-1):
        val = np.linspace(self.input(0), self.input(1), self.input(2)) 
        # val = 10
        self.set_output_val(0, val)
        
        
class Plot3d_Node(DualNodeBase):
    title = 'Plot3d'
    version = 'v0.1'
    init_inputs = [
        NodeInputBP(type_='exec'),
        NodeInputBP(dtype=dtypes.Data(size='m'), label='structure'),
    ]
    init_outputs = [
        NodeOutputBP(type_='exec'),
    ]
    color = '#5d95de'

    def __init__(self, params):
        super().__init__(params, active=True)

    def update_event(self, inp=-1):
        if self.active and inp == 0:
            self.val = self.input(1).plot3d()
        elif not self.active:
            self.val = self.input(0)           
        

class Matplot_Node(DualNodeBase):
    title = 'MatPlot'
    version = 'v0.1'
    init_inputs = [
        NodeInputBP(type_='exec'),
        NodeInputBP(dtype=dtypes.Data(size='m'), label='x'),
        NodeInputBP(dtype=dtypes.Data(size='m'), label='y'),
    ]
    init_outputs = [
        NodeOutputBP(type_='exec'),
    ]
    color = '#5d95de'

    def __init__(self, params):
        super().__init__(params, active=True)

    def update_event(self, inp=-1):
        if self.active and inp == 0:
            fig = plt.figure()
            plt.clf()
            plt.plot(self.input(1), self.input(2))
            self.val = fig
        elif not self.active:
            self.val = self.input(0)   
            
class Sin_Node(NodeBase):
    title = 'Sin'
    version = 'v0.1'
    init_inputs = [
        NodeInputBP(dtype=dtypes.Data(size='m')),
    ]
    init_outputs = [
        NodeOutputBP(),
    ]
    color = '#5d95de'

    def update_event(self, inp=-1):
        self.set_output_val(0, np.sin(self.input(0)))    
        
        
class Result_Node(NodeBase):
    """Simply shows a value converted to str"""

    version = 'v0.1'

    title = 'result'
    init_inputs = [
        NodeInputBP(type_='data'),
    ]
    # main_widget_class = widgets.Result_Node_MainWidget
    # main_widget_pos = 'between ports'
    color = '#c69a15'

    def __init__(self, params):
        super().__init__(params)
        self.val = None

    def place_event(self):
        self.update()

    def view_place_event(self):
        self.main_widget().show_val(self.val)

    def update_event(self, input_called=-1):
        self.val = self.input(0)
        if self.session.gui:
            self.main_widget().show_val(self.val)
            
        
class Print_Node(DualNodeBase):
    title = 'Print'
    version = 'v0.1'
    init_inputs = [
        NodeInputBP(type_='exec'),
        NodeInputBP(dtype=dtypes.Data(size='m')),
    ]
    init_outputs = [
        NodeOutputBP(type_='exec'),
    ]
    color = '#5d95de'

    def __init__(self, params):
        super().__init__(params, active=True)

    def update_event(self, inp=-1):
        if self.active and inp == 0:
            self.val = self.input(1)
        elif not self.active:
            self.val = self.input(0) 
           
        
class Button_Node(NodeBase):
    title = 'Button'
    version = 'v0.1'
    main_widget_class = 'ButtonNodeWidget'
    main_widget_pos = 'between ports'
    init_inputs = [

    ]
    init_outputs = [
        NodeOutputBP(type_='exec')
    ]
    color = '#99dd55'

    def update_event(self, inp=-1):
        self.exec_output(0)

nodes = [
    Project_Node,
    BulkStructure_Node,
    Plot3d_Node,
    IntRand_Node,
    Linspace_Node,
    Sin_Node,
    Result_Node,
    Print_Node,
    Matplot_Node,
    Button_Node,
]