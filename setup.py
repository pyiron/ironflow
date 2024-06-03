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

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

    keywords='pyiron',
    packages=find_packages(exclude=["*tests*", "*docs*", "*binder*", "*conda*", "*notebooks*", "*.ci_support*"]),
    install_requires=[
        'aimsgb ==0.1.3',
        'ipycanvas ==0.13.2',
        'ipython ==8.24.0',
        'ipywidgets ==7.7.1',
        'jupyterlab ==3.6.7',
        'matplotlib ==3.8.4',
        'nglview ==3.0.8',
        'numpy ==1.26.4',
        'owlready2 ==0.46',
        'pandas ==1.5.3',
        'pyiron_atomistics == 0.2.63',
        'pyiron_base ==0.5.33',
        'pyiron_gui <=0.0.8',
        'pyiron_ontology ==0.1.3',
        'pymatgen ==2024.5.31',
        'ryvencore ==0.3.1.1',
        'seaborn ==0.13.2',
        'traitlets ==5.14.3',
    ],
    cmdclass=versioneer.get_cmdclass(),

    )
