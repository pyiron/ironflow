# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Wrappers and extensions of the underlying ryven model.

The `model.HasSession` class provides the main interface between ironflow and ryven.
The rest of these modules revolve mostly around the `DType` class -- namely, ensuring
that each port has a `dtype` attribute (`None` values are handled fine to describe
un-typed ports) and that these dtypes can be used for meaningful type checking when
making connections.
"""

from ryvencore.NodePort import NodePort
