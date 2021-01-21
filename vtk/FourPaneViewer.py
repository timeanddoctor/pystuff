#!/bin/env python3
import os
import sys

from PyQt5 import QtCore
from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QSplitter, QAction, QFileDialog, QApplication, QFrame

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

ui_file = os.path.join(os.path.dirname(__file__),
                       'FourPaneViewer.ui')

ui, QMainWindow = loadUiType(ui_file)

class FourPaneViewer(QMainWindow, ui):
  def __init__(self):
    super(FourPaneViewer, self).__init__()
    self.vtk_widget = None
    self.setup()

  def onLoadClicked(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;MHD Files (*.mhd)", options=options)
    if fileName:
      self.loadFile(fileName)
  def loadFile(self, fileName):
    # Load meta file
    print("loading: %s" % fileName)
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(fileName)
    reader.Update()
    return self.loadFile1(reader)
  def loadFile1(self, reader):
    imageDims = reader.GetOutput().GetDimensions()
    for i in range(3):
      self.vtk_widgets[i].viewer.GetInteractor().EnableRenderOff()
    self.vtk_widgets[3].viewer.GetInteractor().EnableRenderOff()

    # Turn-off plane widgets
    for i in range(3):
      self.planeWidget[i].Off()

    for i in range(3):
      print("%d" % i)
  def setup(self):
    self.setupUi(self)

    loadAct = QAction('&Open', self)
    loadAct.setShortcut('Ctrl+O')
    loadAct.setStatusTip('Load data')
    loadAct.triggered.connect(self.onLoadClicked)

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    fileMenu.addAction(loadAct)    

    self.vtk_widgets = [TestMe(self.vtk_panel,0),
                        TestMe(self.vtk_panel,1),
                        TestMe(self.vtk_panel,2),
                        TestMe(self.vtk_panel)]

    # Make all views share the same cursor object
    for i in range(3):
      self.vtk_widgets[i].SetResliceCursor(self.vtk_widgets[0].GetResliceCursor())

    # Make 3D viewer
    picker = vtk.vtkCellPicker()
    picker.SetTolerance(0.005)

    ipwProp = vtk.vtkProperty()
    ren = vtk.vtkRenderer()

    interactor = QVTKRenderWindowInteractor()
    renderWindow = vtk.vtkGenericOpenGLRenderWindow()
    interactor.SetRenderWindow(renderWindow)

    interactor.GetRenderWindow().AddRenderer(ren)
    
    self.planeWidget = []
    for i in range(3):
      pw = vtk.vtkImagePlaneWidget()
      pw.SetInteractor(interactor)
      pw.SetPicker(picker)
      pw.RestrictPlaneToVolumeOn()
      color = [0.0,0.0,0.0]
      color[i] = 1
      pw.GetPlaneProperty().SetColor(color)
      for j in range(3):
        color[j] = color[j] / 4.0
      self.vtk_widgets[i].viewer.GetRenderer().SetBackground(color)

      pw.SetTexturePlaneProperty(ipwProp)
      pw.TextureInterpolateOff()
      pw.SetResliceInterpolateToLinear()
      pw.DisplayTextOn()
      pw.SetDefaultRenderer(ren)
      self.planeWidget.append(pw)

    # Establish callbacks (TODO)
    

    
    self.vtk_widgets[0].show()
    self.vtk_widgets[1].show()
    self.vtk_widgets[2].show()

    for i in range(3):
      self.vtk_widgets[i].viewer.GetImageActor().SetVisibility(False)
      
    self.horz_layout0 = QHBoxLayout()
    # Vertical spliiter
    self.vert_splitter = QSplitter(Qt.Vertical)
    # Horizontal splitter 0
    self.horz_splitter0 = QSplitter(Qt.Horizontal)
    self.horz_splitter0.addWidget(self.vtk_widgets[0])
    self.horz_splitter0.addWidget(self.vtk_widgets[1])
    self.vert_splitter.addWidget(self.horz_splitter0)
    # Horizontal splitter 1
    self.horz_splitter1 = QSplitter(Qt.Horizontal)
    self.horz_splitter1.addWidget(self.vtk_widgets[2])
    self.horz_splitter1.addWidget(self.vtk_widgets[3])
    self.vert_splitter.addWidget(self.horz_splitter1)

    # Add vertical spliiter to out layout
    self.horz_layout0.addWidget(self.vert_splitter)
    self.horz_layout0.setContentsMargins(0,0,0,0)

    # Set layout of frame
    self.vtk_panel.setLayout(self.horz_layout0)

  def initialize(self):
    print("initialize")
    #self.vtk_widget.start()
    self.vtk_widgets[0].start()
    self.vtk_widgets[1].start()
    
class Viewer2D(QFrame):
  def __init__(self, parent, iDim=0):
    super(Viewer2D, self).__init__(parent)
    interactor = QVTKRenderWindowInteractor(self)
    self.layout = QHBoxLayout(self)
    self.layout.addWidget(interactor)
    self.layout.setContentsMargins(0,0,0,0)
    self.setLayout(self.layout)

    self.viewer = vtk.vtkResliceImageViewer()
    self.viewer.SetupInteractor(interactor)
    self.viewer.SetRenderWindow(interactor.GetRenderWindow())

    # Disable interactor until data are present
    self.viewer.GetRenderWindow().GetInteractor().Disable()

    # Setup cursors and orientation of reslice image widget
    rep = self.viewer.GetResliceCursorWidget().GetRepresentation()
    rep.GetResliceCursorActor().GetCursorAlgorithm().SetReslicePlaneNormal(iDim)
    self.viewer.SetSliceOrientation(iDim)
    self.viewer.SetResliceModeToAxisAligned()
  def SetResliceCursor(self, cursor):
    self.viewer.SetResliceCursor(cursor)
  def GetResliceCursor(self):
    return self.viewer.GetResliceCursor()
  def start(self):
    # Start interactor(s). Figure out to attach to Qt event-loop
    pass

class Tester2D(QFrame):
  def __init__(self, parent):
    super(Tester2D, self).__init__(parent)
    interactor = QVTKRenderWindowInteractor(self)
    self.layout = QHBoxLayout()
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
  if QApplication.startingUp():
    app = QApplication(["FourPaneViewer"])
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
  
