#!/bin/bash
python3 -m virtualenv -p /usr/bin/python3 .virtualenv
.virtualenv/bin/python -m pip install --upgrade pip setuptools wheel
.virtualenv/bin/python -m pip install ipython
.virtualenv/bin/python -m pip install numpy
.virtualenv/bin/python -m pip install vtk
.virtualenv/bin/python -m pip install pyside2
.virtualenv/bin/python -m pip install qtpy
