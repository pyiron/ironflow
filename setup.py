"""
Setuptools based setup module
"""
from setuptools import setup, find_packages
import versioneer

setup(
    name='ironflow',
    version=versioneer.get_version(),
    description='ironflow - A visual scripting interface for pyiron.',
    long_description='Ironflow combines ryven, ipycanvas and ipywidgets to provide a Jupyter-based visual scripting '
                     'gui for running pyiron workflow graphs.',

    url='https://github.com/pyiron/ironflow',
    author='Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department',
    author_email='liamhuber@greyhavensolutions.com',
    license='BSD',

    classifiers=['Development Status :: 3 - Alpha',
                 'Topic :: Scientific/Engineering :: Physics',
                 'License :: OSI Approved :: BSD License',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9',
                 'Programming Language :: Python :: 3.10'],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*", "*docs*", "*binder*", "*conda*", "*notebooks*", "*.ci_support*"]),
    install_requires=[
        'ipycanvas',
        'ipython',
        'ipywidgets >= 7,< 8',
        'matplotlib',
        'nglview',
        'numpy',
        'pyiron_base',
        'pyiron_atomistics',
        'pyiron_gui >= 0.0.8',
        'ryvencore',
        'seaborn',
        'traitlets',
    ],
    cmdclass=versioneer.get_cmdclass(),

    )
