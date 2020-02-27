import os
os.environ['QT_API'] = 'pyqt5'
#os.environ['QT_API'] = 'pyside2' # Need some refactoring

from qtpy import QtCore, QtGui, QtQuick, QtQml

if os.environ['QT_API'] == 'pyqt5':
  from PyQt5.QtCore import pyqtSignal as Signal
  from PyQt5.QtCore import pyqtProperty as Property
else:
  from PySide2.QtCore import Signal
  from PySide2.QtCore import Property
