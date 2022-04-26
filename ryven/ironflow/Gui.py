import ryvencore as rc
import json
import os
from IPython.display import display

from ryven.main.utils import import_nodes_package, load_from_file

os.environ['RYVEN_MODE'] = 'no-gui'

from os.path import basename, dirname, splitext, normpath, join
class NodesPackage:
    """
    A small container to store meta data about imported node packages.
    """

    def __init__(self, directory: str):

        self.name = basename(normpath(directory))
        self.directory = directory

        self.file_path = normpath(join(directory, 'nodes.py'))

    def config_data(self):
        return {
            'name': self.name,
            'dir': self.directory,
        }
    
import ryven.NENV as NENV
NENV.init_node_env()    

packages = ['ryven/std', 'ryven/nodes/built_in/'] #, 'ryven/mynodes']


gui_modes = ['(M)ove Node', 'Add (C)onnection', '(N)one']
alg_modes = ['data', 'exec']
mode_move, mode_connect, mode_none = gui_modes

debug_view = widgets.Output(layout={'border': '1px solid black'})   

class GUI:
    def __init__(self): # , onto_dic=onto_dic):
        session = rc.Session()
        for package in packages:
            session.register_nodes(
                import_nodes_package(
                    NodesPackage(
                        directory=package 
                    )
                )
            )
    
        self._session = session 
        script = session.create_script(title='test')
        
        nodes_dict = {}
        for n in self._session.nodes:
            node_class = n.__module__  # n.identifier_prefix
            if node_class not in nodes_dict.keys():
                nodes_dict[node_class] = {}
            nodes_dict[node_class][n.title] = n 
        self._nodes_dict = nodes_dict    
        
        self.canvas_widget = CanvasObject(self, script=script)
        # self.onto_dic = onto_dic
        
        self.out_log = widgets.Output(layout={'border': '1px solid black'}) 
        
        
    def _print(self, text):
        with self.out_log: 
            self.gui.out_log.clear_output()
            
            print(text)
            
    @debug_view.capture(clear_output=True)    
    def draw(self): 
            self.out_plot = widgets.Output(layout={'width': '30%', 'border': '1px solid black'})
        
            out = widgets.Output(layout={'border': '1px solid black'})
            with out:
                display(self.canvas_widget._canvas)  
            
            module_options = self._nodes_dict.keys()
            self.modules = widgets.Dropdown(
                options=module_options,
                value=list(module_options)[0],
            #     description='Category:',
                disabled=False,
                layout=widgets.Layout(width='130px')
            )

            self.mode = widgets.Dropdown(
                options=gui_modes,
                value=gui_modes[0],
            #     description='Category:',
                disabled=False,
                layout=widgets.Layout(width='130px')
            )    
            
            self.alg_mode = widgets.Dropdown(
                options=alg_modes,
                value=alg_modes[0],
            #     description='Category:',
                disabled=False,
                layout=widgets.Layout(width='80px')
            )                 

            nodes_options = self._nodes_dict[self.modules.value].keys()
            self.nodes = widgets.RadioButtons(
                options=nodes_options,
                value=list(nodes_options)[0],
            #    layout={'width': 'max-content'}, # If the items' names are long
            #     description='Nodes:',
                disabled=False
            )
            self.on_nodes_change(list(nodes_options)[0])
            
            self.out_status = widgets.Output(layout={'border': '1px solid black'})

            self.alg_mode.observe(self.on_alg_mode_change, names='value')
            self.modules.observe(self.on_value_change, names='value')
            self.nodes.observe(self.on_nodes_change, names='value')
            
            # if self.canvas_widget._node_widget is None:
            #     self.canvas_widget._node_widget = widgets.Box()

            return widgets.VBox([
                          widgets.HBox([self.modules, self.mode, self.alg_mode]), 
                          widgets.HBox([
                              widgets.VBox([self.nodes]), 
                              out, self.out_plot]),
                          self.out_log,
                          self.out_status,
                          debug_view
                          # self.canvas_widget._node_widget
                           ])     


    def on_value_change(self, change):
        self.nodes.options = self._nodes_dict[self.modules.value].keys() 
        
    def on_nodes_change(self, change):    
        self._selected_node = self._nodes_dict[self.modules.value][self.nodes.value]
        
    def on_alg_mode_change(self, change):
        self.canvas_widget.script.flow.set_algorithm_mode(self.alg_mode.value)