#!/bin/env python3
import os
import sys

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt, QSettings, QFileInfo, QRect
from PyQt5.QtWidgets import QFileDialog, QApplication, QAction, QCommonStyle, QStyle, QSplitter

ui_file = os.path.join(os.path.dirname(__file__), 'SmartLock2.ui')

ui, QMainWindow = loadUiType(ui_file)

class SmartLock(QMainWindow, ui):
  def __init__(self):
    super(SmartLock, self).__init__()
    self.setup()
    self.DEFAULT_DIR_KEY = "SmartLock2.py"

  def initialize(self):
    print("Initializing")
  def setup(self):
    self.setupUi(self)

    loadAct = QAction('&Open', self)
    loadAct.setShortcut('Ctrl+O')
    loadAct.setStatusTip('Load data')
    loadAct.triggered.connect(lambda: self.onLoadClicked(0))

    surfAct = QAction('&Open Surface', self)
    surfAct.setShortcut('Ctrl+S')
    surfAct.setStatusTip('Surf data')
    surfAct.triggered.connect(lambda: self.onLoadClicked(1))
    
    exitAct = QAction('&Exit', self)
    exitAct.setShortcut('ALT+F4')
    exitAct.setStatusTip('Exit application')
    exitAct.triggered.connect(self.close)

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    fileMenu.addAction(loadAct)
    fileMenu.addAction(surfAct)
    fileMenu.addAction(exitAct)

    style = QCommonStyle()
    self.btnUpAzimuth.setIcon(style.standardIcon(QStyle.SP_ArrowUp))
    self.btnDownAzimuth.setIcon(style.standardIcon(QStyle.SP_ArrowDown))
    self.btnRightAzimuth.setIcon(style.standardIcon(QStyle.SP_ArrowForward))
    self.btnLeftAzimuth.setIcon(style.standardIcon(QStyle.SP_ArrowBack))

    self.btnUpElevation.setIcon(style.standardIcon(QStyle.SP_ArrowUp))
    self.btnDownElevation.setIcon(style.standardIcon(QStyle.SP_ArrowDown))
    self.btnRightElevation.setIcon(style.standardIcon(QStyle.SP_ArrowForward))
    self.btnLeftElevation.setIcon(style.standardIcon(QStyle.SP_ArrowBack))

    self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
    self.statusBar().hide()

    all_widgets = QApplication.instance().allWidgets()
    for widget in all_widgets:
        if type(widget) == QSplitter:
            widget.setStyleSheet(""
                                 " QSplitter::handle:horizontal { "
                                 "    border: 1px outset darkgrey; "
                                 " } " 
                                 " QSplitter::handle:vertical{ "
                                 "    border: 1px outset darkgrey; "
                                 " } ")
            widget.setHandleWidth(2) # Default is 3
    
  def closeEvent(self, event):
    # Stops the renderer such that the application can close without issues
    #for i in range(3):
    #  self.vtk_widgets[i].interactor.close()
    #self.vtk_widgets[3].close()
    event.accept()

if __name__ == '__main__':
  if QApplication.startingUp():
    app = QApplication(sys.argv)
  else:
    app = QCoreApplication.instance()
  app.setApplicationName("SmartLock")
  app.setOrganizationName("BK Medical")
  app.setOrganizationDomain("www.bkmedical.com")
  main_window = SmartLock()
  main_window.setGeometry(0,40,main_window.width(), main_window.height())
  main_window.show()
  main_window.initialize()
  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
