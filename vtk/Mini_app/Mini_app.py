import sys
import numpy as np

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import (QtWidgets, QtGui, uic)
from PyQt5.QtCore import QObject

ui, QMainWindow = uic.loadUiType('Mini_app_Qt_VTK.ui')
class ViewersApp(QMainWindow, ui):
  def __init__(self):
    #Parent constructor
    super(ViewersApp, self).__init__()
    self.vtk_widget = None
    self.setup()

  def setup(self):
    self.setupUi(self)
    self.vtk_widget = QMeshViewer(self.vtk_panel)

    # add a layout to let the vtk panel grow/shrink with window resize
    self.vtk_layout = QtWidgets.QHBoxLayout()
    self.vtk_layout.addWidget(self.vtk_widget)
    self.vtk_layout.setContentsMargins(0,0,0,0)
    self.vtk_panel.setLayout(self.vtk_layout)

    # connects slots and signals for all 3 widgets
    self.comboBox.activated.connect(self.vtk_widget.Switch_Mode)
    self.Resolution.valueChanged.connect(self.vtk_widget.set_Resolution)
    self.radioButton.clicked.connect(self.vtk_widget.button_event)

    quitAct = QtWidgets.QAction("Quit", self)
    quitAct.triggered.connect(self.closeEvent)
    
  def initialize(self):
    self.vtk_widget.start()

  def closeEvent(self, event):
    self.vtk_widget.interactor.close()
    
class QMeshViewer(QtWidgets.QFrame):
  def __init__(self, parent):
    super(QMeshViewer,self).__init__(parent)

    # Make the actual QtWidget a child so that it can be re_parented
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
    self.interactor = interactor
    self.renderer = renderer
    self.sphere = sphereSource
    self.actor = actor

  def start(self):
    self.interactor.Initialize()
    # If a big Qt application call app.exec instead
    self.interactor.Start()

  def Switch_Mode(self, new_value):
    self.actor.GetProperty().SetRepresentation(new_value)
    self.render_window.Render()

  def button_event(self, new_value):
    if new_value:
      print("Button was clicked")

  def set_Resolution(self, new_value):
    self.sphere.SetPhiResolution(new_value)
    self.sphere.SetThetaResolution(new_value)
    self.render_window.Render()
if __name__ == '__main__':
  app = QtWidgets.QApplication(["Mini-App"])
  main_window = ViewersApp()
  main_window.show()
  main_window.initialize()
  app.exec_()

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
