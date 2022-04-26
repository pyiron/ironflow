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

packages = ['ryven/std', 'ryven/nodes/built_in/']


from ipycanvas import Canvas, hold_canvas
import numpy as np


import ipywidgets as widgets
class canvas_widget:
    def __init__(self, gui=None, width=2000, height=1000, script=None):
        self.gui = gui
        self.script = script
        self._width, self._height = width, height

        self._col_background = "black" # "#584f4e"
        self._col_node_header = "blue" #"#38a8a4"
        self._col_node_selected = "#9dcea6"
        self._col_node_unselected = "#dee7bc"
        
        self._font_size = 30
        self._node_box_size = 160, 70

        self._canvas = Canvas(width=width, height=height)
        self._canvas.fill_style = self._col_background
        self._canvas.fill_rect(0, 0, width, height)
        self._canvas.layout.width = '100%'
        self._canvas.layout.height = 'auto'

        self.objects_to_draw = []
        self.connections = []
        
        self._canvas.on_mouse_down(self.handle_mouse_down)
        self._canvas.on_mouse_move(self.handle_mouse_move)
        self._canvas.on_key_down(self.handle_keyboard_event)
        
        self._connection_in = None
        
        self._node_widget = None
        
    def draw_connection(self, path=[0, 1]):
        i_out, i_in = path
        out = self.objects_to_draw[i_out]
        inp = self.objects_to_draw[i_in]

        canvas = self._canvas
        canvas.stroke_style = 'white' 
        canvas.line_width = 3
        canvas.move_to(out.x_out, out.y_out)
        canvas.line_to(inp.x_in, inp.y_in)
        canvas.stroke()
    
    def canvas_restart(self):
        self._canvas.clear()
        self._canvas.fill_style = self._col_background
        self._canvas.fill_rect(0, 0, self._width, self._height)
           
    def handle_keyboard_event(self, key, shift_key, ctrl_key, meta_key):
#         with self.gui.out_log: 
#             self.gui.out_log.clear_output()

#             print('Keyboard event:', key, shift_key, ctrl_key, meta_key)
        if key == 'Delete':
            self.delete_selected()
        elif key == 'm':
            self.gui.mode.value = mode_move
        elif key == 'c':
            self.deselect_all()
            self.gui.mode.value = mode_connect
        elif key == 'n':
            self.gui.mode.value = mode_none
            
    def set_connection(self, ind_node):
        if self._connection_in is None:
            self._connection_in = ind_node
        else: 
            out = self.objects_to_draw[self._connection_in].node.outputs[0]
            inp = self.objects_to_draw[ind_node].node.inputs[-1]
            if self.script.flow.connect_nodes(inp, out) is None:
                i_con = self.connections.index([self._connection_in, ind_node])
                del self.connections[i_con]
            else:    
                self.connections.append([self._connection_in, ind_node])
            
            self._connection_in = None
            self.deselect_all()
            
    def deselect_all(self):
        [o.set_selected(False) for o in self.objects_to_draw if o.selected]
        self.redraw()
            
    def handle_mouse_down(self, x, y):
        self._selected_node_ind = None
        for i_object, check_region in enumerate(self.objects_to_draw):
            # print (x, y, check_region.is_selected(x, y), check_region.selected)
            if check_region.is_selected(x, y):
                self._selected_node_ind = i_object
                check_region.set_selected(not check_region.selected)
                self._node_widget = NodeWidgets(check_region.node, self.gui).draw()
                with self.gui.out_status:
                    self.gui.out_status.clear_output()
                    display(self._node_widget)
                    
                if self.gui.mode.value == mode_connect:
                    self.set_connection(i_object)
                break    
        else:
            self.add_node(x, y, self.gui._selected_node)
        
        self._x0_mouse = x
        self._y0_mouse = y
        self.redraw()
            
        
    def get_selected_objects(self):
        return [o for o in self.objects_to_draw if o.selected]

    def handle_mouse_move(self, x, y):
        if self.gui.mode.value == mode_move:
            dx = x - self._x0_mouse
            dy = y - self._y0_mouse
            self._x0_mouse, self._y0_mouse = x, y 

            if [o for o in self.objects_to_draw if o.selected]:
                with hold_canvas(self._canvas):
                    [o.add_x_y(dx, dy) for o in self.objects_to_draw if o.selected]
                    self.canvas_restart()
                    [o.draw() for o in self.objects_to_draw]
                    for path in self.connections:
                        self.draw_connection(path)
                    
    def redraw(self):
        self.canvas_restart()
        with hold_canvas(self._canvas):
            self.canvas_restart()
            [o.draw() for o in self.objects_to_draw]
            for path in self.connections:
                self.draw_connection(path)  
          
    def _read_script(self):
        node_gid_dic = {}
        nodes = self.script.flow.nodes
#         nodes_gui = data['scripts'][i_script]['flow']['nodes']
        for i_n, n in enumerate(nodes):
            name = n.identifier.split('.')[-1].split('_')[0]
            o = self.objects_to_draw[i_n]
            x = o.x
            y = o.y

#             n = nodes_gui[i_n]
            gid = n.GLOBAL_ID
            node_gid_dic[gid] = i_n  # TODO: check why indices in json-file are shifted by 2

            val = ''
            if hasattr(n, 'val'):
                val = n.val

            s = NodeGui(x//0.6, y//0.6, self, title=name, val=val)
            s.set_selected(False)

        for c in self.script.flow.connections:
            c_in = c.inp.node.GLOBAL_ID
            c_out = c.out.node.GLOBAL_ID
            con = [node_gid_dic[c_out], node_gid_dic[c_in]]
            self.connections.append(con)                
                    
    def add_node(self, x, y, node):
        n = self.script.flow.create_node(node)
        print ('node: ', n.identifier, n.GLOBAL_ID)
        # name = n.identifier.split('.')[-1].split('_')[0]
        s = NodeGui(x, y, self, node=n) # , title=name)
        s.set_selected(False)
        self.objects_to_draw.append(s)

        self.redraw()     
    
    def delete_selected(self):
        for o in self.objects_to_draw:
            if o.selected:
                self.objects_to_draw.remove(o)
        #TODO: remove connections        
        self.redraw() 
        
        
class NodeGui:
    def __init__(self, x, y, canvas_widget, node, selected=False):
        self.x = x
        self.y = y
        self.width, self.height = canvas_widget._node_box_size
        self.selected = selected
        self.node = node
        name = node.identifier.split('.')[-1].split('_')[0]
        self.title = name
        
        # self.val = None
        # if hasattr(node, 'val'):
        #     self.val = node.val
            
        self.canvas_widget = canvas_widget
        self.canvas = canvas_widget._canvas

    def set_x_y(self, x_in, y_in):
        self.x = x_in
        self.y = y_in
        
    def add_x_y(self, dx_in, dy_in):
        self.x += dx_in
        self.y += dy_in        
        
    def draw_title(self, title):
        self.canvas.fill_style = self.canvas_widget._col_background
        self.canvas.font = f'{self.canvas_widget._font_size}px serif'
        self.canvas.fill_style = 'white'
        x = self.x - (self.width * 0.49)
        y = self.y - (self.height * 0.6),
        self.canvas.fill_text(title, x, y)
        
    def draw_value(self, val):
        self.canvas.fill_style = self.canvas_widget._col_background
        self.canvas.font = f'{self.canvas_widget._font_size}px serif'
        x = self.x - (self.width * 0.4)
        y = self.y - (self.height * 0.01),
        self.canvas.fill_text(val, x, y)        
        
    def draw_input(self):
        self.canvas.fill_style = self.canvas_widget._col_background
        x = self.x - (self.width * 0.5)
        y = self.y - 0 * (self.height * 0.5)
        self.x_in, self.y_in = x, y        
        self.canvas.fill_style = 'blue'
        self.canvas.fill_arc(x, y, 5, -np.pi/2, np.pi/2)      
        
    def draw_output(self):
        self.canvas.fill_style = self.canvas_widget._col_background
        x = self.x + (self.width * 0.5)
        y = self.y - 0 * (self.height * 0.5)
        self.x_out, self.y_out = x, y
        self.canvas.fill_style = 'red'
        self.canvas.fill_arc(x, y, 5, np.pi/2, 3 * np.pi/2)        

    def draw(self):
        self.canvas.fill_style = self.canvas_widget._col_node_header
        self.canvas.fill_rect(
            self.x - (self.width * 0.5), self.y - (self.height), self.width, self.height
        )
        if self.selected:
            self.canvas.fill_style = self.canvas_widget._col_node_selected
        else:
            self.canvas.fill_style = self.canvas_widget._col_node_unselected
        self.canvas.fill_rect(
            self.x - (self.width * 0.5),
            self.y - (self.height * 0.5),
            self.width,
            self.height,
        )
        self.draw_title(self.title)
        if hasattr(self.node, 'val'):
            if self.node.val is not None:
                self.draw_value(self.node.val)
        self.draw_input()
        self.draw_output()
        

    def is_selected(self, x_in, y_in):
        x_coord = self.x - (self.width * 0.5)
        y_coord = self.y - (self.height * 0.5)

        if (
            x_in > x_coord
            and x_in < (x_coord + self.width)
            and y_in > y_coord
            and y_in < (y_coord + self.height)
        ):

            return True
        else:
            return False

    def set_selected(self, state):
        self.selected = state        
        
        
# onto_dic = {}
# onto_dic['Utilities'] = {'Murnaghan':[]}
# onto_dic['Codes'] = {'Vasp':[], 'Lammps':[]}
# onto_dic['Structures'] = {'Bulk':[], 'Surfaces':[]}

gui_modes = ['(M)ove Node', 'Add (C)onnection', '(N)one']
mode_move, mode_connect, mode_none = gui_modes

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
        
        self.canvas_widget = canvas_widget(self, script=script)
        # self.onto_dic = onto_dic
        
        self.out_log = widgets.Output(layout={'border': '1px solid black'}) 
        
    def _print(self, text):
        with self.out_log: 
            self.gui.out_log.clear_output()
            
            print(text)
        
    def draw(self):    
            out = widgets.Output(layout={'border': '1px solid black'})
            with out:
                display(self.canvas_widget._canvas)  
            
            module_options = self._nodes_dict.keys()
            self.modules = widgets.Dropdown(
                options=module_options,
                value=list(module_options)[0],
            #     description='Category:',
                disabled=False,
                layout=widgets.Layout(width='100px')
            )

            self.mode = widgets.Dropdown(
                options=gui_modes,
                value=gui_modes[0],
            #     description='Category:',
                disabled=False,
                layout=widgets.Layout(width='100px')
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


            self.modules.observe(self.on_value_change, names='value')
            self.nodes.observe(self.on_nodes_change, names='value')
            
            # if self.canvas_widget._node_widget is None:
            #     self.canvas_widget._node_widget = widgets.Box()

            return widgets.VBox([
                          widgets.HBox([self.mode]), 
                          widgets.HBox([
                              widgets.VBox([self.modules, self.nodes]), 
                              out]),
                          self.out_log,
                          self.out_status
                          # self.canvas_widget._node_widget
                           ])     


    def on_value_change(self, change):
        self.nodes.options = self._nodes_dict[self.modules.value].keys() 
        
    def on_nodes_change(self, change):    
        self._selected_node = self._nodes_dict[self.modules.value][self.nodes.value]
        
        
import ipywidgets as widgets
import numpy as np

class NodeWidgets:
    def __init__(self, node, central_gui):
        self._node = node
        self._central_gui = central_gui
        self.gui_object()
        self.input_widgets()
        # self.input = []
        
    def gui_object(self):
        if 'slider' in self._node.title.lower():
            self.gui = widgets.FloatSlider(value=self._node.val, min=0, max=10)

            self.gui.observe(self.gui_object_change, names='value') 
        else:
            self.gui = widgets.Box()
        return self.gui

    def gui_object_change(self, change):
        self._node.set_state({'val': change['new']}, 0)
        self._node.update_event()
        self._central_gui.canvas_widget.redraw()
        
    def input_widgets(self):
        self._input = []
        if not hasattr(self._node, 'inputs'):
            return
        for i_c, inp in enumerate(self._node.inputs[:]):
            if inp.dtype is None:
                # if inp.type_ == 'exec':
                inp_widget = widgets.Label(value=inp.type_)
                description = inp.type_
                # inp_widget = 
            else:
                
                dtype = str(inp.dtype).split('.')[-1]
                # print (dtype)
                if dtype == 'Integer':
                    inp_widget = widgets.IntText(
                                            value=inp.val,
                                            disabled=False,
                                            description='',
                                            layout=widgets.Layout(width='110px', border='solid 1px')
                                        )

                elif dtype == 'Boolean':
                    inp_widget = widgets.Checkbox(
                                            value=inp.val,
                                            indent=True,
                                            description='',
                                            layout=widgets.Layout(width='110px', border='solid 1px')
                                        )
                else:
                    inp_widget = widgets.Text(value=str(inp.val))
                
                description = inp.label_str
            self._input.append([widgets.Label(description), inp_widget])
            
            inp_widget.observe(eval(f'self.input_change_{i_c}'), names='value')
       
    def input_change(self, i_c, change):
        # print (change)
        self._node.inputs[i_c].val = change['new']
        self._node.update_event()
        self._central_gui.canvas_widget.redraw()
        
    def input_change_0(self, change):
        self.input_change(0, change)
        
    def input_change_1(self, change):
        self.input_change(1, change)        
        
    def draw(self):
        self.inp_box = widgets.GridBox(list(np.array(self._input).flatten()), 
                                  layout=widgets.Layout(width='210px', 
                                                        grid_template_columns="90px 110px", 
                                                        # grid_gap='1px 1px',
                                                        border='solid 1px blue',
                                                        margin='10px'
                                                       ))
        
        self.gui.layout = widgets.Layout(height='70px', 
                                          border='solid 1px red',
                                          margin='10px',
                                          padding='10px')
        
        glob_id_val = None
        if hasattr(self._node, 'GLOBAL_ID'):
            glob_id_val = self._node.GLOBAL_ID
        global_id = widgets.Text(
                value=str(glob_id_val),
                description='GLOBAL_ID:',
                disabled=True
            )
        # global_id.layout.width = '300px'
        
        title = widgets.Text(
                value=str(self._node.title),
                # placeholder='Type something',
                description='Title:',
                disabled=True
            ) 
        # title.layout.width = '300px'
        
        info_box = widgets.VBox([global_id, title])
        info_box.layout = widgets.Layout(height='70px', 
                                         width='350px',
                                          border='solid 1px red',
                                          margin='10px',
                                          padding='0px')

        return widgets.HBox([self.inp_box, self.gui, info_box])        