#!/bin/env python3
import os
import sys

# TODO: Make a VTK button in the corner of each 2DViewer

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt, QSettings, QFileInfo
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QSplitter, QAction, QFileDialog, QApplication, QFrame, QStackedWidget, QPushButton

from Viewer2D import Viewer2D

ui_file = os.path.join(os.path.dirname(__file__), 'FourPaneViewer.ui')

ui, QMainWindow = loadUiType(ui_file)

def renderLinesAsTubes(prop):
  prop.SetEdgeVisibility(1)
  prop.SetPointSize(4)
  prop.SetLineWidth(3)
  prop.SetRenderLinesAsTubes(1)
  return prop

class callback(object):
  def __call__(self, o, e, d = None):
    print(o.GetWindow())
    print(o.GetLevel())
    return
    
class ResliceCallback(object):
  def __init__(self):
    self.IPW = None
    self.RCW = None

  @vtk.calldata_type(vtk.VTK_FLOAT)
  def onTest(self, caller, ev, myInt):
    print(myInt)
    return
  def onResliceAxesChanged(self, caller, ev):
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
    self.render()
  def onEndWindowLevelChanged(self, caller, ev):
    wl = [main_window.vtk_widgets[0].viewer.GetColorWindow(), main_window.vtk_widgets[0].viewer.GetColorLevel()]
    main_window.vtk_widgets[0].viewer.SetColorWindow(wl[0])
    main_window.vtk_widgets[0].viewer.SetColorLevel(wl[1])
    return

  def onWindowLevelChanged(self, caller, ev):
    if (caller.GetClassName() == 'vtkImagePlaneWidget'):
      wl = [caller.GetWindow(), caller.GetLevel()]
      # Triggers an update of vtkImageMapToWindowLevelColors - updates annotations
      main_window.vtk_widgets[0].viewer.SetColorWindow(wl[0])
      main_window.vtk_widgets[0].viewer.SetColorLevel(wl[1])
    self.render()

  def render(self):
    # Render views
    for i in range(3):
      self.RCW[i].Render()
    # Render 3D
    self.IPW[0].GetInteractor().GetRenderWindow().Render()
    
class FourPaneViewer(QMainWindow, ui):
  def __init__(self):
    super(FourPaneViewer, self).__init__()
    self.setup()
    self.DEFAULT_DIR_KEY = "FourPaneViewer.py"

  def onPlaneClicked(self):
    index = self.stack.currentIndex()
    index = index + 1
    index = index % 3
    self.stack.setCurrentIndex(index)

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
    self.vtk_widgets[3].EnableRenderOff()

    # Turn-off plane widgets
    for i in range(3):
      self.planeWidget[i].Off()

    # Assign data to 2D viewers sharing one cursorobject
    for i in range(3):
      self.vtk_widgets[i].SetInputData(reader.GetOutput())
      
    # Enable plane widgets
    for i in range(3):
      self.planeWidget[i].SetInputConnection(reader.GetOutputPort())
      self.planeWidget[i].SetPlaneOrientation(i)
      self.planeWidget[i].SetSliceIndex(imageDims[i] // 2)
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
      self.vtk_widgets[i].viewer.GetInteractor().Enable()

    # Enable 3D rendering
    self.vtk_widgets[3].EnableRenderOn()
    # Reset camera for the renderer - otherwise it is set using dummy data
    self.planeWidget[0].GetDefaultRenderer().ResetCamera()

    # Update 3D
    self.ResetViews()
    self.SetResliceMode(1)

  def ResetViews(self):
    for i in range(3):
      self.vtk_widgets[i].viewer.Reset()

    # Also sync the Image plane widget on the 3D view
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
    exitAct.setShortcut('ALT+F4')
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

    # Cursor representation (anti-alias)
    for i in range(3):
      for j in range(3):
        prop = self.vtk_widgets[i].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(j)
        renderLinesAsTubes(prop)
      
    # Make 3D viewer
    picker = vtk.vtkCellPicker()
    picker.SetTolerance(0.005)

    ipwProp = vtk.vtkProperty()
    ren = vtk.vtkRenderer()
    interactor = QVTKRenderWindowInteractor()

    interactor.GetRenderWindow().AddRenderer(ren)
    self.vtk_widgets.append(interactor)

    # Create plane widgets
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

      prop = pw.GetPlaneProperty()
      renderLinesAsTubes(prop)
      pw.SetPlaneProperty(prop)

      prop = pw.GetSelectedPlaneProperty()
      renderLinesAsTubes(prop)
      pw.SetSelectedPlaneProperty(prop)
      
      prop = pw.GetCursorProperty()
      renderLinesAsTubes(prop)
      pw.SetCursorProperty(prop)

      pw.Modified()
      # Set background for 2D views
      for j in range(3):
        color[j] = color[j] / 4.0
      self.vtk_widgets[i].viewer.GetRenderer().SetBackground(color)
      self.vtk_widgets[i].interactor.Disable()

      self.planeWidget.append(pw)

    self.establishCallbacks()

    # Show widgets but hide non-existing data
    for i in range(3):
      self.vtk_widgets[i].show()
      self.vtk_widgets[i].viewer.GetImageActor().SetVisibility(False)

    # Layouts
    self.stack = QStackedWidget(self)
    self.stack.addWidget(self.vtk_widgets[0])
    self.stack.addWidget(self.vtk_widgets[1])
    self.stack.addWidget(self.vtk_widgets[2])

    vert_layout0 = QVBoxLayout()
    horz_splitter0 = QSplitter(Qt.Horizontal)
    horz_splitter0.addWidget(self.stack)
    horz_splitter0.addWidget(self.vtk_widgets[3])
    vert_layout0.addWidget(horz_splitter0)
    vert_layout0.setContentsMargins(0, 0, 0, 0)
    self.vtk_panel.setLayout(vert_layout0)

    layout = QVBoxLayout()
    self.btn = QPushButton("Next")
    layout.addWidget(self.btn)
    self.frame.setLayout(layout)
    self.btn.clicked.connect(self.onPlaneClicked)

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
      # Ignored after loading data!!! (why)
      self.vtk_widgets[i].viewer.GetInteractorStyle().AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)
      self.vtk_widgets[i].viewer.GetInteractorStyle().AddObserver('EndWindowLevelEvent', self.cb.onEndWindowLevelChanged)

      self.planeWidget[i].AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)

      # Make them all share the same color map.
      self.vtk_widgets[i].viewer.SetLookupTable(self.vtk_widgets[0].viewer.GetLookupTable())

      self.planeWidget[i].GetColorMap().SetLookupTable(self.vtk_widgets[0].viewer.GetLookupTable())
      #self.planeWidget[i].GetColorMap().SetInputData(self.vtk_widgets[i].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetColorMap().GetInput()) # deep copy (not needed)
      self.planeWidget[i].SetColorMap(self.vtk_widgets[i].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetColorMap())

  def initialize(self):
    # For a large application, attach to Qt's event loop instead.
    self.vtk_widgets[0].Start()
    self.vtk_widgets[1].Start()
    self.vtk_widgets[2].Start()
    # 3D viewer
    self.vtk_widgets[3].Initialize()
    self.vtk_widgets[3].Start()

  def closeEvent(self, event):
    # Stops the renderer such that the application can close without issues
    for i in range(3):
      self.vtk_widgets[i].interactor.close()
    self.vtk_widgets[3].close()
    event.accept()

if __name__ == '__main__':
  if QApplication.startingUp():
    app = QApplication(sys.argv)
  else:
    app = QCoreApplication.instance()
  app.setApplicationName("StackView")
  app.setOrganizationName("BK Medical")
  app.setOrganizationDomain("www.bkmedical.com")    
  main_window = FourPaneViewer()
  main_window.show()
  main_window.initialize()
  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
