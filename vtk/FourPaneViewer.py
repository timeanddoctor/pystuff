#!/bin/env python3
import os
import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

ui_file = os.path.join(os.path.dirname(__file__),
                       'FourPaneViewer.ui')

ui, QMainWindow = loadUiType(ui_file)

class FourPaneViewer(QMainWindow, ui):
  def __init__(self):
    #Parent constructor
    super(FourPaneViewer, self).__init__()
    self.vtk_widget = None
    self.setup()
  def setup(self):
    self.setupUi(self)

    if 0:
      self.vtk_widget = TestMe(self.vtk_panel)
      
      # add a layout to let the vtk panel grow/shrink with window resize
      self.vtk_layout = QtWidgets.QHBoxLayout()
      self.vtk_layout.addWidget(self.vtk_widget)
      self.vtk_layout.setContentsMargins(0,0,0,0)
      self.vtk_panel.setLayout(self.vtk_layout)
    else:
      self.vtk_widgets = [TestMe(self.vtk_panel),
                          TestMe(self.vtk_panel),
                          TestMe(self.vtk_panel),
                          TestMe(self.vtk_panel)]
      self.horz_layout0 = QHBoxLayout()
      # Vertical spliiter
      self.vert_splitter = QtWidgets.QSplitter(Qt.Vertical)
      # Horizontal splitter 0
      self.horz_splitter0 = QtWidgets.QSplitter(Qt.Horizontal)
      self.horz_splitter0.addWidget(self.vtk_widgets[0])
      self.horz_splitter0.addWidget(self.vtk_widgets[1])
      self.vert_splitter.addWidget(self.horz_splitter0)
      # Horizontal splitter 1
      self.horz_splitter1 = QtWidgets.QSplitter(Qt.Horizontal)
      self.horz_splitter1.addWidget(self.vtk_widgets[2])
      self.horz_splitter1.addWidget(self.vtk_widgets[3])
      self.vert_splitter.addWidget(self.horz_splitter1)

      # Add vertical spliiter to out layout
      self.horz_layout0.addWidget(self.vert_splitter)
      self.horz_layout0.setContentsMargins(0,0,0,0)

      # Set layout of frame
      self.vtk_panel.setLayout(self.horz_layout0)

    # TODO: Add splitters, 
    
  def initialize(self):
    print("initialize")
    #self.vtk_widget.start()
    self.vtk_widgets[0].start()
    self.vtk_widgets[1].start()


    
class Viewer2D(QtWidgets.QFrame):
  def __init__(self, parent):
    super(Viewer2D, self).__init__(parent)
    interactor = QVTKRenderWindowInteractor(self)
    self.layout = QtWidgets.QHBoxLayout(self)
    self.layout.addWidget(interactor)
    self.layout.setContentsMargins(0,0,0,0)

    self.viewer = vtk.vtkImageViewer2()
    self.viewer.SetupInteractor(interactor)
    self.viewer.SetRenderWindow(interactor.GetRenderWindow())
    
    #self.setLayout(self.layout)
  def start(self):
    pass
class Tester2D(QtWidgets.QFrame):
  def __init__(self, parent):
    super(Tester2D, self).__init__(parent)
    interactor = QVTKRenderWindowInteractor(self)
    self.layout = QtWidgets.QHBoxLayout()
    self.layout.addWidget(interactor)
    self.layout.setContentsMargins(0,0,0,0)
    self.setLayout(self.layout)

    # set up my VTK Visualization pipeline
    # cut-and-paste from https://lorensen.github.io/VTKExamples/site/Python/GeometricObjects/Sphere/
    colors = vtk.vtkNamedColors()

    # Create a sphere
    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetCenter(0.0,0.0,0.0)
    sphereSource.SetRadius(5.0)
    # Make the surface smooth
    sphereSource.SetPhiResolution(100)
    sphereSource.SetThetaResolution(100)

    # Create a mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphereSource.GetOutputPort())

    # Create an actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d("Cornsilk"))
    actor.GetProperty().SetRepresentation(0)
    actor.GetProperty().SetDiffuseColor(colors.GetColor3d("Cornsilk"))
    actor.GetProperty().SetDiffuse(0.8)
    actor.GetProperty().SetSpecular(0.5)
    actor.GetProperty().SetSpecularColor(1.,1.,1.)
    actor.GetProperty().SetSpecularPower(30.)

    renderer =  vtk.vtkOpenGLRenderer()
    render_window = interactor.GetRenderWindow()
    render_window.AddRenderer(renderer)

    # TEST
    # interactor.SetRenderWindow(render_window)
    #render_window.SetInteractor(interactor)

    renderer.AddActor(actor)
    renderer.SetBackground(colors.GetColor3d("DarkGreen"))

    self.render_window = render_window
    
    # TODO: vtkImageViewer2.SetRenderWindow(self.render_window)
    self.interactor = interactor
    self.renderer = renderer
    self.sphere = sphereSource
    self.actor = actor

  def start(self):
    self.interactor.Initialize()
    # If a big Qt application call app.exec instead
    self.interactor.Start()

#class TestMe(Tester2D):
class TestMe(Viewer2D):
  pass
    
if __name__ == '__main__':
  if QtWidgets.QApplication.startingUp():
    app = QtWidgets.QApplication(["FourPaneViewer"])
  else:
    app = QCoreApplication.instance()
  main_window = FourPaneViewer()
  main_window.show()
  main_window.initialize()
  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
  
