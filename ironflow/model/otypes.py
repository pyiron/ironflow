# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Provides lazy-loading of `pyiron_ontology` ontologies for de-serializing otypes.

TODO: This is not easily extensible; it needs a system for users to register their
      ontology with the session so that they can use their own otypes alongside
      modules of their own custom nodes.
"""

import pyiron_ontology


class OTypeLoader:
    _atomistics = None

    @classmethod
    def atomistics(cls, item):
        if cls._atomistics is None:
            cls._atomistics = pyiron_ontology.dynamic.atomistics()
        return cls._atomistics[item]


def otype_from_str(namespace, item):
    return getattr(OTypeLoader, namespace)(item)
