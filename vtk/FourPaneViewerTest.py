#!/bin/env python3

# TODO: Fix window level when set in 3D - verify if it is working for the c++ FourPaneViewer

import os
import sys

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt, QSettings, QFileInfo
from PyQt5.QtWidgets import QHBoxLayout, QSplitter, QAction, QFileDialog, QApplication, QFrame

ui_file = os.path.join(os.path.dirname(__file__), 'FourPaneViewer.ui')

ui, QMainWindow = loadUiType(ui_file)

use3D = True

# Overload AddObserver

def callback(obj, ev):
  print(ev)
  #print(obj)

@vtk.calldata_type(vtk.VTK_INT)
def callbackInt(obj, ev, *calldata):
  print(ev)
  print(calldata)

# Works
class ResliceCallback(object):
  def __init__(self):
    self.IPW = None
    self.RCW = None
    
  def onResliceAxesChanged(self, caller, ev, *calldata):
    # Does this every happen - never here
    # TODO: instead of QVTKRenderWindowInteractor add a generic
    # openglrenderwindow.
    if (caller.GetClassName() == 'vtkImagePlaneWidget'):
      print(calldata)
      wl = calldata
      if (caller == self.IPW[0]):
        self.IPW[1].SetWindowLevel(wl[0],wl[1],1)
        self.IPW[2].SetWindowLevel(wl[0],wl[1],1)
      elif caller == self.IPW[1]:
        self.IPW[0].SetWindowLevel(wl[0],wl[1],1)
        self.IPW[2].SetWindowLevel(wl[0],wl[1],1)
      elif caller == self.IPW[2]:
        self.IPW[0].SetWindowLevel(wl[0],wl[1],1)
        self.IPW[1].SetWindowLevel(wl[0],wl[1],1)
    
    if (caller.GetClassName() == 'vtkResliceCursorWidget'):
      rep = caller.GetRepresentation()
      rep.GetResliceCursorActor().GetCursorAlgorithm().GetResliceCursor()

      # Update 3D widget
      for i in range(3):
        ps = self.IPW[i].GetPolyDataAlgorithm()
        origin = self.RCW[i].GetResliceCursorRepresentation().GetPlaneSource().GetOrigin()
        ps.SetOrigin(origin)
        ps.SetPoint1(self.RCW[i].GetResliceCursorRepresentation().GetPlaneSource().GetPoint1())
        ps.SetPoint2(self.RCW[i].GetResliceCursorRepresentation().GetPlaneSource().GetPoint2())
        # If the reslice plane has modified, update it on the 3D widget
        self.IPW[i].UpdatePlacement()

    # Render everything
    for i in range(3):
      self.RCW[i].Render()

    self.IPW[0].GetInteractor().GetRenderWindow().Render()
    return
  def onWindowLevelChanged(self, caller, ev):
    for i in range(3):
      self.RCW[i].Render()
    self.IPW[0].GetInteractor().GetRenderWindow().Render()

  # TODO: Call this everytime except for window level
  def onImagePlaneWidget(self, caller, ev, *calldata):
    if (caller.GetClassName() == 'vtkImagePlaneWidget'):
      # How to get calldata
      print(calldata)
      wl = calldata
      if (caller == self.IPW[0]):
        self.IPW[1].SetWindowLevel(wl[0],wl[1],1)
        self.IPW[2].SetWindowLevel(wl[0],wl[1],1)
      elif caller == self.IPW[1]:
        self.IPW[0].SetWindowLevel(wl[0],wl[1],1)
        self.IPW[2].SetWindowLevel(wl[0],wl[1],1)
      elif caller == self.IPW[2]:
        self.IPW[0].SetWindowLevel(wl[0],wl[1],1)
        self.IPW[1].SetWindowLevel(wl[0],wl[1],1)
    print('vtkImagePlaneWidget')

# Works
class CustomCallback(object):
  def __init__(self, ev=vtk.vtkCommand.NoEvent):
    self.ev = ev
  def __call__(self, caller, ev):
    print(self.ev)
    
class FourPaneViewer(QMainWindow, ui):
  def __init__(self):
    super(FourPaneViewer, self).__init__()
    self.cb = None
    self.vtk_widgets = None
    self.DEFAULT_DIR_KEY = "FourPaneViewer.py"

    self.setup()
    
  def onLoadClicked(self):
    mySettings = QSettings()
    fileDir = mySettings.value(self.DEFAULT_DIR_KEY)
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileDialog = QFileDialog()
    fileDialog.setDirectory(fileDir)
    fileName, _ = \
      fileDialog.getOpenFileName(self,
                                 "QFileDialog.getOpenFileName()",
                                 "", "All Files (*);;MHD Files (*.mhd)",
                                 options=options)
    if fileName:
      # Update default dir
      currentDir = QFileInfo(fileName).absoluteDir()
      mySettings.setValue(self.DEFAULT_DIR_KEY,
                          currentDir.absolutePath())
      # Load data
      self.loadFile(fileName)

  def loadFile(self, fileName):
    # Load VTK Meta Image
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(fileName)
    reader.Update()
    imageDims = reader.GetOutput().GetDimensions()

    # Disable renderers and widgets
    for i in range(3):
      self.vtk_widgets[i].viewer.GetInteractor().EnableRenderOff()
    if use3D:
      self.vtk_widgets[3].EnableRenderOff()
      # Turn-off plane widgets
      for i in range(3):
        self.planeWidget[i].Off()

    # Assign data to 2D viewers sharing one cursorobject
    for i in range(3):
      self.vtk_widgets[i].viewer.SetInputData(reader.GetOutput())

    if use3D:
      # Enable plane widgets
      for i in range(3):
        # Something missing when compared to c++ (no interactor is set)
        self.planeWidget[i].SetInteractor(self.vtk_widgets[3]) # was missing
        
        self.planeWidget[i].SetInputConnection(reader.GetOutputPort())
        self.planeWidget[i].SetPlaneOrientation(i)
        self.planeWidget[i].SetSliceIndex(imageDims[i] // 2)
        self.planeWidget[i].UpdatePlacement() # was missing
        self.planeWidget[i].GetInteractor().Enable()
        self.planeWidget[i].On()
        self.planeWidget[i].InteractionOn()

    # Enable 2D viewers
    for i in range(3):
      self.vtk_widgets[i].viewer.GetRenderer().ResetCamera()
      self.vtk_widgets[i].viewer.GetInteractor().EnableRenderOn()

    # Enable interactors
    for i in range(3):
      self.vtk_widgets[i].interactor.Enable()

    if use3D:
      # Enable 3D rendering
      self.vtk_widgets[3].EnableRenderOn()
      # Reset camera for the renderer - otherwise it is set using dummy data
      self.planeWidget[0].GetDefaultRenderer().ResetCamera()

      # Could we requist interactor for 3D image??

    # Update 3D
    self.ResetViews()
    self.SetResliceMode(1)

  def ResetViews(self):
    for i in range(3):
      self.vtk_widgets[i].viewer.Reset()

    # Also sync the Image plane widget on the 3D view
    if use3D:
      for i in range(3):
        ps = self.planeWidget[i].GetPolyDataAlgorithm()
        ps.SetNormal(self.vtk_widgets[0].viewer.GetResliceCursor().GetPlane(i).GetNormal())
        ps.SetCenter(self.vtk_widgets[0].viewer.GetResliceCursor().GetPlane(i).GetOrigin())
        # If the reslice plane has modified, update it on the 3D widget
        self.planeWidget[i].UpdatePlacement()

    # Render once
    self.Render()

  def Render(self):
    for i in range(3):
      self.vtk_widgets[i].viewer.Render()
    if use3D:
      # Render 3D
      self.vtk_widgets[3].GetRenderWindow().Render()

  def SetResliceMode(self, mode):
    # Do we need to render planes if mode == 1?
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

    self.vtk_widgets = [Viewer2D(self.vtk_panel, 0),
                        Viewer2D(self.vtk_panel, 1),
                        Viewer2D(self.vtk_panel, 2)]

    # Make all views share the same cursor object
    for i in range(3):
      self.vtk_widgets[i].viewer.SetResliceCursor(self.vtk_widgets[0].viewer.GetResliceCursor())

    if use3D:
      # Make 3D viewer
      picker = vtk.vtkCellPicker()
      picker.SetTolerance(0.005)

      ipwProp = vtk.vtkProperty()
      ren = vtk.vtkRenderer()
      # In c++ we create generic opengl renderwindow and replace that of
      # the window - can we do that and not use QVTKRenderWindowInteractor
      interactor = QVTKRenderWindowInteractor()
      interactor.GetRenderWindow().AddRenderer(ren)
      self.vtk_widgets.append(interactor)

      self.planeWidget = []
      for i in range(3):
        pw = vtk.vtkImagePlaneWidget()
        pw.SetInteractor(interactor)
        pw.SetPicker(picker)
        pw.RestrictPlaneToVolumeOn()
        color = [0.0, 0.0, 0.0]
        color[i] = 1
        pw.GetPlaneProperty().SetColor(color)
        pw.SetTexturePlaneProperty(ipwProp)
        pw.TextureInterpolateOn()
        pw.SetResliceInterpolateToLinear()
        pw.DisplayTextOn()
        pw.SetDefaultRenderer(ren)
        self.planeWidget.append(pw)
    for i in range(3):
      color = [0.0, 0.0, 0.0]
      color[i] = 1
      for j in range(3):
        color[j] = color[j] / 4.0
      self.vtk_widgets[i].viewer.GetRenderer().SetBackground(color)
      self.vtk_widgets[i].interactor.Disable()

    self.establishCallbacks()
      
    for i in range(3):
      self.vtk_widgets[i].show()

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
    horz_layout0.setContentsMargins(0, 0, 0, 0)
    self.vtk_panel.setLayout(horz_layout0)

  def establishCallbacks(self):
    self.cb = ResliceCallback()
    self.cb.IPW = []
    self.cb.RCW = []
    for i in range(3):
      self.cb.IPW.append(self.planeWidget[i])
      self.cb.RCW.append(self.vtk_widgets[i].viewer.GetResliceCursorWidget())

    for i in range(3):
      self.vtk_widgets[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent, self.cb.onResliceAxesChanged)
      self.vtk_widgets[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.WindowLevelEvent, self.cb.onWindowLevelChanged)
      self.vtk_widgets[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceThicknessChangedEvent, self.cb.onWindowLevelChanged)
      self.vtk_widgets[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResetCursorEvent, self.cb.onResliceAxesChanged)
      self.vtk_widgets[i].viewer.GetInteractorStyle().AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)
      
      # Make them all share the same color map.
      self.vtk_widgets[i].viewer.SetLookupTable(self.vtk_widgets[0].viewer.GetLookupTable())
      self.planeWidget[i].GetColorMap().SetLookupTable(self.vtk_widgets[0].viewer.GetLookupTable())
      self.planeWidget[i].SetColorMap(self.vtk_widgets[i].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetColorMap())
      
  def initialize(self):
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
    self.layout.setContentsMargins(0, 0, 0, 0)
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

  def SetResliceCursor(self, cursor):
    self.viewer.SetResliceCursor(cursor)
  def GetResliceCursor(self):
    return self.viewer.GetResliceCursor()
  def start(self):
    # Start interactor(s).
    self.interactor.Initialize()
    self.interactor.Start()

if __name__ == '__main__':
  if QApplication.startingUp():
    app = QApplication(["FourPaneViewer"])
  else:
    app = QCoreApplication.instance()
  app.setApplicationName("FourPaneViewer")
  app.setOrganizationName("KitWare")
  app.setOrganizationDomain("www.kitware.com")
  
  main_window = FourPaneViewer()
  main_window.show()
  main_window.initialize()
  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
