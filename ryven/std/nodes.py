from ryven.NENV import *
# widgets = import_widgets(__file__)

import sys
import os
sys.path.append(os.path.dirname(__file__))

from special_nodes import nodes as special_nodes
from basic_operators import nodes as operator_nodes
# from control_structures import nodes as cs_nodes
from pyiron_nodes import nodes as pyiron_nodes

export_nodes(
    *special_nodes,
    *operator_nodes,
#     *cs_nodes,
    *pyiron_nodes,
)







# from ryven.NENV import *
# # widgets = import_widgets(__file__)

# import sys
# import os
# sys.path.append(os.path.dirname(__file__))

# from ryven.mynodes.pyiron_nodes import nodes as pyiron_nodes

# export_nodes(
#     *pyiron_nodes,
#     # *operator_nodes,
# #     *cs_nodes,
# )