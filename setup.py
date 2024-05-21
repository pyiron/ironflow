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
        'atomistics ==0.0.5',
        'aimsgb ==1.1.1',
        'ipycanvas ==0.13.2',
        'ipython ==8.24.0',
        'ipywidgets ==7.7.1',
        'jupyterlab ==3.6.6',
        'matplotlib ==3.8.4',
        'nglview ==3.0.8',
        'numpy ==1.23.5',
        'openjdk ==22.0.1',
        'owlready2 ==0.46',
        'pandas ==2.2.0',
        'pyiron-data ==0.0.27',
        'pyiron_base ==0.7.3',
        'pyiron_atomistics == 0.3.3',
        'pyiron_gui ==0.0.8',
        'pyiron_ontology ==0.1.3',
        'ryvencore ==0.3.1.1',
        'seaborn ==0.13.2',
        'traitlets ==5.14.1',
    ],
    cmdclass=versioneer.get_cmdclass(),

    )
