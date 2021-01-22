#!/bin/env python3
import os
import sys

from PyQt5 import QtCore
from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QSplitter, QAction, QFileDialog, QApplication, QFrame

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

ui_file = os.path.join(os.path.dirname(__file__), 'FourPaneViewer.ui')

ui, QMainWindow = loadUiType(ui_file)

# Won't work on member function - dunno why
#@vtk.calldata_type(vtk.VTK_OBJECT)
def callback(widget, event):#, callData):
  print(event)

class MyClass:
  def __init__(self):
    from functools import partial
    def nodeAddedCallback(self, caller, eventId):
      print("Node added")
      print("New node: {0}".format(callData.GetName()))
    self.nodeAddedCallback = partial(nodeAddedCallback, self)
    self.nodeAddedCallback.CallDataType = vtk.VTK_OBJECT
  def registerCallbacks(self):
    self.nodeAddedModifiedObserverTag = main_window.vtk_widgets[0].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent, callback)

  def unregisterCallbacks(self):
    main_window.vtk_widgets[0].viewer.GetInteractorStyle().RemoveObserver(self.nodeAddedModifiedObserverTag)
        

use3D = True

class FourPaneViewer(QMainWindow, ui):
  def __init__(self):
    super(FourPaneViewer, self).__init__()
    self.setup()

  def onLoadClicked(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;MHD Files (*.mhd)", options=options)
    if fileName:
      self.loadFile(fileName)

  def loadFile(self, fileName):
    # Load meta file
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(fileName)
    reader.Update()
    imageDims = reader.GetOutput().GetDimensions()
    for i in range(3):
      self.vtk_widgets[i].viewer.GetInteractor().EnableRenderOff()

    if use3D:
      self.vtk_widgets[3].EnableRenderOff()

      # Turn-off plane widgets
      for i in range(3):
        self.planeWidget[i].Off()

    for i in range(3):
      rep = self.vtk_widgets[i].viewer.GetResliceCursorWidget().GetRepresentation()
      self.vtk_widgets[i].viewer.SetResliceCursor(self.vtk_widgets[0].viewer.GetResliceCursor())
      rep.GetResliceCursorActor().GetCursorAlgorithm().SetReslicePlaneNormal(i)
      self.vtk_widgets[i].viewer.SetInputData(reader.GetOutput())
      self.vtk_widgets[i].viewer.SetSliceOrientation(i)
      self.vtk_widgets[i].viewer.SetResliceModeToAxisAligned()

    if use3D:
      iren = self.vtk_widgets[3]
      for i in range(3):
        self.planeWidget[i].SetInteractor( iren )
        self.planeWidget[i].RestrictPlaneToVolumeOn()
          
        self.planeWidget[i].TextureInterpolateOn()
        self.planeWidget[i].SetResliceInterpolateToLinear()
        self.planeWidget[i].SetInputConnection(reader.GetOutputPort())
        self.planeWidget[i].SetPlaneOrientation(i)
        self.planeWidget[i].SetSliceIndex(imageDims[i] // 2)
        self.planeWidget[i].DisplayTextOn()
          
        self.planeWidget[i].UpdatePlacement()
        self.planeWidget[i].GetInteractor().Enable()
        self.planeWidget[i].On()
        self.planeWidget[i].InteractionOn()

    for i in range(3):
      self.vtk_widgets[i].viewer.GetRenderer().ResetCamera()
      self.vtk_widgets[i].viewer.GetInteractor().EnableRenderOn()

    # Re-establish callbacks
    #self.establishCallbacks()

    self.myObject = MyClass()
    self.myObject.registerCallbacks()

    for i in range(3):
      self.vtk_widgets[i].interactor.Enable()

    if use3D:
      self.vtk_widgets[3].EnableRenderOn()
      # Reset camera for the renderer - otherwise it is set using dummy data
      self.planeWidget[0].GetDefaultRenderer().ResetCamera()

    # Update 3D
    self.ResetViews()
    self.SetResliceMode(1)
    
  def ResetViews(self):
    for i in range(3):
      self.vtk_widgets[i].viewer.Reset()

    # Also sync the Image plane widget on the 3D top right view with any
    # changes to the reslice cursor.
    if use3D:
      for i in range(3):
        ps = self.planeWidget[i].GetPolyDataAlgorithm()
        ps.SetNormal(self.vtk_widgets[0].viewer.GetResliceCursor().GetPlane(i).GetNormal())
        ps.SetCenter(self.vtk_widgets[0].viewer.GetResliceCursor().GetPlane(i).GetOrigin())
      
        # If the reslice plane has modified, update it on the 3D widget
        self.planeWidget[i].UpdatePlacement()

    # Render in response to changes (omit this)
    self.Render()

  def Render(self):
    for i in range(3):
      self.vtk_widgets[i].viewer.Render()
    if use3D:
      # Render 3D
      self.vtk_widgets[3].GetRenderWindow().Render()

  def SetResliceMode(self, mode):
    for i in range(3):
      self.vtk_widgets[i].viewer.SetResliceMode(mode)
      self.vtk_widgets[i].viewer.GetRenderer().ResetCamera()
      self.vtk_widgets[i].viewer.Render()
    
  def setup(self):
    self.setupUi(self)

    loadAct = QAction('&Open', self)
    loadAct.setShortcut('Ctrl+O')
    loadAct.setStatusTip('Load data')
    loadAct.triggered.connect(self.onLoadClicked)

    exitAct = QAction('&Exit', self)
    exitAct.setShortcut('Ctrl+Q')
    exitAct.setStatusTip('Exit application')
    exitAct.triggered.connect(self.close)
    
    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    fileMenu.addAction(loadAct)    
    fileMenu.addAction(exitAct)
    
    self.vtk_widgets = [TestMe(self.vtk_panel,0),
                        TestMe(self.vtk_panel,1),
                        TestMe(self.vtk_panel,2)]

    # Make all views share the same cursor object
    for i in range(3):
      self.vtk_widgets[i].viewer.SetResliceCursor(self.vtk_widgets[0].viewer.GetResliceCursor())

    if use3D:
      # Make 3D viewer
      picker = vtk.vtkCellPicker()
      picker.SetTolerance(0.005)
      
      ipwProp = vtk.vtkProperty()
      ren = vtk.vtkRenderer()
      interactor = QVTKRenderWindowInteractor()
      interactor.GetRenderWindow().AddRenderer(ren)
      self.vtk_widgets.append(interactor)

      self.planeWidget = []
      for i in range(3):
        pw = vtk.vtkImagePlaneWidget()
        pw.SetInteractor(interactor)
        pw.SetPicker(picker)
        pw.RestrictPlaneToVolumeOn()
        color = [0.0,0.0,0.0]
        color[i] = 1
        pw.GetPlaneProperty().SetColor(color)
        pw.SetTexturePlaneProperty(ipwProp)
        pw.TextureInterpolateOff()
        pw.SetResliceInterpolateToLinear()
        pw.DisplayTextOn()
        pw.SetDefaultRenderer(ren)
        self.planeWidget.append(pw)
    for i in range(3):
      color = [0.0,0.0,0.0]
      color[i] = 1
      for j in range(3):
        color[j] = color[j] / 4.0
      self.vtk_widgets[i].viewer.GetRenderer().SetBackground(color)
      self.vtk_widgets[i].interactor.Disable() # TEST
    #self.establishCallbacks()

    self.vtk_widgets[0].show()
    self.vtk_widgets[1].show()
    self.vtk_widgets[2].show()
    #self.vtk_widgets[3].show()

    for i in range(3):
      self.vtk_widgets[i].viewer.GetImageActor().SetVisibility(False)

    # Layouts
    horz_layout0 = QHBoxLayout()
    vert_splitter = QSplitter(Qt.Vertical)
    horz_splitter0 = QSplitter(Qt.Horizontal)
    horz_splitter0.addWidget(self.vtk_widgets[0])
    horz_splitter0.addWidget(self.vtk_widgets[1])
    vert_splitter.addWidget(horz_splitter0)
    horz_splitter1 = QSplitter(Qt.Horizontal)
    horz_splitter1.addWidget(self.vtk_widgets[2])
    if use3D:
      horz_splitter1.addWidget(self.vtk_widgets[3])
    vert_splitter.addWidget(horz_splitter1)
    horz_layout0.addWidget(vert_splitter)
    horz_layout0.setContentsMargins(0,0,0,0)
    self.vtk_panel.setLayout(horz_layout0)

  def establishCallbacks(self):
    # Establish callbacks - show I inherit from something
    for i in range(1):
      # TODO: Figure out to call member function - do I need to inherit vtkInteractor?
      self.vtk_widgets[i].viewer.GetInteractorStyle().AddObserver(vtk.vtkCommand.WindowLevelEvent, callback) # ignored
      self.vtk_widgets[i].viewer.GetInteractorStyle().AddObserver(vtk.vtkResliceCursorWidget.WindowLevelEvent, callback)
      self.vtk_widgets[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResetCursorEvent, callback)
      self.vtk_widgets[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent, callback)
      self.vtk_widgets[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceThicknessChangedEvent, callback)

      # Make all views and planes share the same color map
      self.vtk_widgets[i].viewer.SetLookupTable(self.vtk_widgets[0].viewer.GetLookupTable())
      if use3D:
        self.planeWidget[i].GetColorMap().SetLookupTable(self.vtk_widgets[0].viewer.GetLookupTable())
        self.planeWidget[i].SetColorMap(
          self.vtk_widgets[i].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetColorMap())

      # Buffers are updated when resizing. Otherwise uninitialized
      # memory is shown.
      self.vtk_widgets[i].viewer.GetInteractor().Enable()
    
  def initialize(self):
    print("initialize")
    # For a large application, attach to Qt's event loop instead.
    self.vtk_widgets[0].start()
    self.vtk_widgets[1].start()
    self.vtk_widgets[2].start()
    if use3D:
      # 3D viewer
      self.vtk_widgets[3].Initialize()
      self.vtk_widgets[3].Start()

  def closeEvent(self, event):
    """
    Stops the renderer such that the application can close without issues
    """
    print("closing")
    for i in range(3):
      self.vtk_widgets[i].interactor.close()
    if use3D:
      self.vtk_widgets[3].close()
    event.accept()
    
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
    # TODO: Do this after setting the interactor
    self.viewer.GetRenderWindow().GetInteractor().Disable()

    # Setup cursors and orientation of reslice image widget
    rep = self.viewer.GetResliceCursorWidget().GetRepresentation()
    rep.GetResliceCursorActor().GetCursorAlgorithm().SetReslicePlaneNormal(iDim)
    self.viewer.SetSliceOrientation(iDim)
    self.viewer.SetResliceModeToAxisAligned()
    self.interactor = interactor

#  def SetResliceCursor(self, cursor):
#    self.viewer.SetResliceCursor(cursor)
#  def GetResliceCursor(self):
#    return self.viewer.GetResliceCursor()
  def start(self):
    # Start interactor(s). Figure out to attach to Qt event-loop
    #pass
    self.interactor.Initialize()
    self.interactor.Start()

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
  #sys.exit(app.exec())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
  
