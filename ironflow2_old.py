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


from ipycanvas import Canvas, hold_canvas
import numpy as np



import ipywidgets as widgets
class CanvasObject:
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
        
        self.x = 0
        self.y = 0
        
        self._last_selected_object = None
        self._last_selected_port = None
        
        self._connection_in = None
        self._node_widget = None
        
        self._object_to_gui_dict = {}
        
    def draw_connection(self, port_1, port_2):
        # i_out, i_in = path
        # out = self.objects_to_draw[i_out]
        # inp = self.objects_to_draw[i_in]
        out = self._object_to_gui_dict[port_1]
        inp = self._object_to_gui_dict[port_2]

        canvas = self._canvas
        canvas.stroke_style = 'white' 
        canvas.line_width = 3
        canvas.move_to(out.x, out.y)
        canvas.line_to(inp.x, inp.y)
        canvas.stroke()
        
    def _built_object_to_gui_dict(self):
        self._object_to_gui_dict = {}
        for n in self.objects_to_draw:
            self._object_to_gui_dict[n.node] = n
            for p in n.objects_to_draw:
                if hasattr(p, 'port'):
                    self._object_to_gui_dict[p.port] = p        
    
    def canvas_restart(self):
        self._canvas.clear()
        self._canvas.fill_style = self._col_background
        self._canvas.fill_rect(0, 0, self._width, self._height)
           
    def handle_keyboard_event(self, key, shift_key, ctrl_key, meta_key):
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
        sel_object = self.get_element_at_xy(x, y)
        self._selected_object = sel_object
        if sel_object is not None:
            sel_object.set_selected(not sel_object.selected)
            if sel_object.selected:
                if self._last_selected_object is not None:
                    self._last_selected_object.set_selected(False)
                self._last_selected_object = sel_object
                if isinstance(sel_object, NodeWidget):
                    self._handle_node_select(sel_object)
                elif isinstance(sel_object, PortWidget):
                    self._handle_port_select(sel_object)
                    
                if hasattr(sel_object, 'handle_select'):
                    sel_object.handle_select(sel_object)

            else:
                self._last_selected_object = None
        else:
            self.add_node(x, y, self.gui._selected_node)   
            self._built_object_to_gui_dict()
 
        self._x0_mouse = x
        self._y0_mouse = y
        self.redraw()  
        
    def _handle_node_select(self, sel_object):
        self._node_widget = NodeWidgets(sel_object.node, self.gui).draw()
        with self.gui.out_status:
            self.gui.out_status.clear_output()
            display(self._node_widget)    
            
    def _handle_port_select(self, sel_object):
        if self._last_selected_port is None:
            self._last_selected_port = sel_object.port
        else:
            self.script.flow.connect_nodes(self._last_selected_port, sel_object.port)
            self._last_selected_port = None 
            self.deselect_all()        
        

        
    def get_element_at_xy(self, x_in, y_in):
        for o in self.objects_to_draw:
            if o.is_selected(x_in, y_in):
                return o.get_element_at_xy(x_in, y_in)
        return None                   
        
    def get_selected_objects(self):
        return [o for o in self.objects_to_draw if o.selected]

    def handle_mouse_move(self, x, y):
        if self.gui.mode.value == mode_move:
            # dx = x - self._x0_mouse
            # dy = y - self._y0_mouse
            # self._x0_mouse, self._y0_mouse = x, y 

            if [o for o in self.objects_to_draw if o.selected]:
                with hold_canvas(self._canvas):
                    # [o.add_x_y(dx, dy) for o in self.objects_to_draw if o.selected]
                    [o.set_x_y(x, y) for o in self.objects_to_draw if o.selected]
                    self.redraw()    
                    
    def redraw(self):
        self.canvas_restart()
        with hold_canvas(self._canvas):
            self.canvas_restart()
            [o.draw() for o in self.objects_to_draw]
            for c in self.script.flow.connections:
                self.draw_connection(c.inp, c.out)  
          
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
        
        layout = CanvasLayout(font_size=20, width=200, height=100, background_color='gray', selected_color='green')

        if hasattr(node, 'main_widget_class'):
            if node.main_widget_class is not None:
                # node.title = str(node.main_widget_class)
                f = eval(node.main_widget_class)
                s = f(x, y, parent=self, node=n, layout=layout)
            else:
                s = NodeWidget(x, y, parent=self, node=n, layout=layout) 
            # print ('s: ', s)
        else:
            s = NodeWidget(x, y, parent=self, node=n, layout=layout) 

        self.objects_to_draw.append(s)

        self.redraw()     
    
    def delete_selected(self):
        for o in self.objects_to_draw:
            if o.selected:
                self.objects_to_draw.remove(o)
        #TODO: remove connections        
        self.redraw() 

        

        
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
        
        
import ipywidgets as widgets
import numpy as np

import pickle
import base64

def deserialize(data):
    return pickle.loads(base64.b64decode(data))

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
                dtype_state = deserialize(inp.data()['dtype state'])
                if inp.val is None:
                    inp.val = dtype_state['val']
                # print (dtype)
                if dtype == 'Integer':
                    inp_widget = widgets.IntText(
                                            value=inp.val,  # dtype_state['val'],
                                            disabled=False,
                                            description='',
                                            layout=widgets.Layout(width='110px', border='solid 1px')
                                        )
                elif dtype == 'Boolean':
                    inp_widget = widgets.Checkbox(
                                            value=inp.val, # dtype_state['val'],
                                            indent=True,
                                            description='',
                                            layout=widgets.Layout(width='110px', border='solid 1px')
                                        )
                else:
                    inp_widget = widgets.Text(value=str(inp.val))
                
                description = inp.label_str
            self._input.append([widgets.Label(description), inp_widget])
            
            inp_widget.observe(eval(f'self.input_change_{i_c}'), names='value')

            # inp_widget.value = dtype_state['default']
            
       
    def input_change(self, i_c, change):
        # print (change)
        self._node.inputs[i_c].val = change['new']
        self._node.update_event()
        self._central_gui.canvas_widget.redraw()
        
    def input_change_0(self, change):
        self.input_change(0, change)
        
    def input_change_1(self, change):
        self.input_change(1, change)        

    def input_change_2(self, change):
        self.input_change(2, change)       
        
    def input_change_3(self, change):
        self.input_change(3, change)               
        
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
    
    
class CanvasLayout:
    def __init__(self, width=100, height=60, font_size=12, background_color='blue', selected_color='lightblue', font_color='black', font_title_color='white'):
        self.width = width
        self.height = height
        self.background_color = background_color
        self.selected_color = selected_color        
        self.font_size = font_size
        self.font_color = font_color
        self.font_title_color = font_title_color

        
class BaseCanvasWidget:
    def __init__(self, x, y, parent=None, layout=None, selected=False):
        self._x = x  # relative to parent
        self._y = y
        
        self.layout = layout 

        self.parent = parent
        self.selected = selected
        
        self.objects_to_draw = []
        
    def _init_after_parent_assignment(self):
        pass
    
    @property
    def width(self):
        return self.layout.width
        
    @property
    def height(self):
        return self.layout.height        
    
    @property
    def x(self):
        return self.parent.x + self._x  #- self.parent.width//2 
    
    @property
    def y(self):
        return self.parent.y + self._y #- self.parent.height//2     
     
    @property
    def _canvas(self):
        return self.parent._canvas
        
    def add_widget(self, widget):
        if widget.parent is None:
            widget.parent = self
        if widget.layout is None:
            widget.layout = self.parent.layout   
            
        self.objects_to_draw.append(widget)

    def set_x_y(self, x_in, y_in):
        self._x = x_in - self.width//2
        self._y = y_in - self.height//2
        
    def add_x_y(self, dx_in, dy_in):
        self._x += dx_in
        self._y += dy_in        
        
    def draw_shape(self):
        self._canvas.fill_style = self.layout.background_color
        if self.selected:
            self._canvas.fill_style = self.layout.selected_color
        self._canvas.fill_rect(
            self.x, # - (self.width * 0.5),
            self.y, # - (self.height * 0.5),
            self.width,
            self.height,
        ) 
        
    def draw(self):
        self.draw_shape()
        for o in self.objects_to_draw:
            o.draw()
            
    def _is_at_xy(self, x_in, y_in):
        x_coord = self.x #- (self.width * 0.5)
        y_coord = self.y #- (self.height * 0.5)

        return (
            x_in > x_coord
            and x_in < (x_coord + self.width)
            and y_in > y_coord
            and y_in < (y_coord + self.height)
            )
        
    def get_element_at_xy(self, x_in, y_in):
        if self._is_at_xy(x_in, y_in):
            for o in self.objects_to_draw:
                if o.is_selected(x_in, y_in):
                    return o.get_element_at_xy(x_in, y_in)
            return self
        else:
            return None        
        
    def is_selected(self, x_in, y_in):
        if self._is_at_xy(x_in, y_in):
            return True
        else:
            return False

    def set_selected(self, state):
        self.selected = state  
        
        
class PortWidget(BaseCanvasWidget):
    def __init__(self, x, y, radius=10, parent=None, port=None, layout=None, selected=False):
        super().__init__(x, y, parent, layout, selected)
        
        self.radius = radius  
        self.port = port
        
    def draw_shape(self):
        self._canvas.fill_style = self.layout.background_color
        if self.selected:
            self._canvas.fill_style = self.layout.selected_color
        self._canvas.fill_circle(self.x, self.y, self.radius)   
        
    def _is_at_xy(self, x_in, y_in):
        x_coord = self.x - self.radius
        y_coord = self.y - self.radius

        return (
            x_in > x_coord
            and x_in < (x_coord + 2 * self.radius)
            and y_in > y_coord
            and y_in < (y_coord + 2 * self.radius)
            )  
    
    
class NodeWidget(BaseCanvasWidget):
    def __init__(self, x, y, node, parent=None, layout=None, selected=False, port_radius=10):
        super().__init__(x, y, parent, layout, selected)
        
        self._title_box_height = 0.3  # ratio with respect to height
        
        self.node = node
        self.title = node.title

        self.inputs = node.inputs
        self.outputs = node.outputs
        
        self.port_radius = port_radius
        self.layout_ports = CanvasLayout(width=20, height=10, background_color='brown', selected_color='red')

        self.add_inputs()
        self.add_outputs()
        
    def draw_title(self, title):
        
        self._canvas.fill_style = 'blue'
        self._canvas.fill_rect(
            self.x, self.y, self.width, self.height * self._title_box_height
        )
        self._canvas.font = f'{self.layout.font_size}px serif'
        self._canvas.fill_style = self.layout.font_title_color
        x = self.x + (self.width * 0.04)
        y = self.y + (self.height * 0.25),
        self._canvas.fill_text(title, x, y)
        
    def draw_value(self, val):
        self._canvas.fill_style = self.layout.font_color
        self._canvas.font = f'{self.layout.font_size}px serif'
        x = self.x + (self.width * 0.3)
        y = self.y + (self.height * 0.65),
        self._canvas.fill_text(str(val), x, y)  
        if ('matplotlib' in str(type(val))) or ('NGLWidget' in str(type(val))):
            self.parent.gui.out_plot.clear_output()
            with self.parent.gui.out_plot:
                display(val)
        
    def _add_ports(self, radius, inputs=None, outputs=None, border=1.4):
        if inputs is not None:
            x = radius * border
            data = inputs
        elif outputs is not None:
            x = self.width - radius * border
            data = outputs
        else:
            return

        n_ports = len(data)
        
        y_min = self.height * self._title_box_height
        d_y = self.height - y_min
        
        if n_ports > 0:
            i_y_vec = (np.arange(n_ports) + 1/2)/n_ports

            for i_port, y_port in enumerate(i_y_vec):
                self.add_widget(PortWidget(x, y_port * d_y + y_min, radius=radius, parent=self, port=data[i_port],  layout=self.layout_ports))        
        
    def add_inputs(self):
        self._add_ports(radius=self.port_radius, inputs=self.inputs)
                
    def add_outputs(self, radius=5):
        self._add_ports(radius=self.port_radius, outputs=self.outputs)
                     
    def draw(self):
        super().draw()
        if self.title is not None:
            self.draw_title(self.title)
        if hasattr(self.node, 'val'): 
            self.draw_value(self.node.val)
            
        for o in self.objects_to_draw:
            o.draw()   
            
            
class ButtonNodeWidget(NodeWidget):
    def __init__(self, x, y, node, parent=None, layout=None, selected=False, port_radius=10):
        super().__init__(x, y, node, parent, layout, selected, port_radius)
        
        layout = CanvasLayout(width=100, height=30, background_color='darkgray')
        s = BaseCanvasWidget(50, 50, parent=self, layout=layout)
        s.handle_select = self.handle_button_select    #lambda self : self.parent.node.exec_output(0)

        self.add_widget(s)
    
    def handle_button_select(self, button):
        button.parent.node.exec_output(0)
        button.set_selected(False)

        