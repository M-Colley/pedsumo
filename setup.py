"""
A Python library extending SUMO for the simulation of interaction between automated vehicles and pedestrians.
"""
# setuptools, not distutils: distutils was removed from the standard library in Python 3.12 and the
# previous "from distutils.core import setup" only kept working through the setuptools compatibility shim.
from setuptools import setup, find_packages

short_description = __doc__.split("\n")

try:
    with open("README.md", "r", encoding="utf-8") as handle:
        long_description = handle.read()
except OSError:
    long_description = "\n".join(short_description[2:])


setup(
    name='PedSUMO',
    # find_packages() previously matched only "tests", because SumoWithAVs had no __init__.py:
    # the distribution shipped the test suite and none of the actual simulation code.
    packages=find_packages(include=["SumoWithAVs", "SumoWithAVs.*"]),
    version='1.0.0',
    # SPDX expression: the "License :: OSI Approved :: ..." classifier is deprecated in setuptools >= 77
    license='MIT',
    license_files=['LICENSE'],
    description=short_description[1],
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Mark Colley',
    author_email='m.colley@ucl.ac.uk',
    url='https://github.com/M-Colley/pedsumo',
    keywords=['simulation', 'pedestrian', 'automated-vehicles', 'ehmi', 'llm', 'sumo', 'traffic'],
    python_requires='>=3.11',
    install_requires=[
        'pandas>=2.3.3',
        'numpy>=1.26.4',
        'PySide6>=6.7.3',
        'screeninfo',
        'matplotlib>=3.10.8',
        'sumolib>=1.25.0',
    ],
    # torch and transformers are only needed for --prob_computation llm and add multiple GB to the
    # install, so they are an opt-in extra rather than a hard requirement.
    extras_require={
        'llm': [
            'torch>=2.7.0',
            'transformers>=4.51.3',
        ],
    },
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
)
