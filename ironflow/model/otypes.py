# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.
"""
Provides lazy-loading of `pyiron_ontology` ontologies for de-serializing otypes.

TODO: This is not easily extensible; it needs a system for users to register their
      ontology with the session so that they can use their own otypes alongside
      modules of their own custom nodes.
"""


class OTypeLoader:

    _pyiron_atomistics = None

    @classmethod
    def pyiron_atomistics(cls, item):
        if cls._pyiron_atomistics is None:
            from pyiron_ontology import atomistics_onto
            cls._pyiron_atomistics = atomistics_onto
        return cls._pyiron_atomistics[item]


def otype_from_str(namespace, item):
    return getattr(OTypeLoader, namespace)(item)
