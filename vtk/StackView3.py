#!/bin/env python3
import os
import sys

# TODO: Make a VTK button in the corner of each 2DViewer

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt, QSettings, QFileInfo
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QSplitter, QAction, QFileDialog, QApplication, QFrame, QStackedWidget, QPushButton

from Viewer2D import Viewer2D, Viewer2DStacked, Viewer3D
from vtkUtils import renderLinesAsTubes

ui_file = os.path.join(os.path.dirname(__file__), 'FourPaneViewer.ui')

ui, QMainWindow = loadUiType(ui_file)

class ResliceCallback(object):
  def __init__(self):
    self.IPW = None
    self.RCW = None

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
    wl = [main_window.stack.widget(0).viewer.GetColorWindow(), main_window.stack.widget(0).viewer.GetColorLevel()]
    main_window.stack.widget(0).viewer.SetColorWindow(wl[0])
    main_window.stack.widget(0).viewer.SetColorLevel(wl[1])
    return

  def onWindowLevelChanged(self, caller, ev):
    # 3D -> 2D views
    if (caller.GetClassName() == 'vtkImagePlaneWidget'):
      wl = [caller.GetWindow(), caller.GetLevel()]
      main_window.stack.widget(0).viewer.SetColorWindow(wl[0])
      main_window.stack.widget(0).viewer.SetColorLevel(wl[1])
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
    self.stack.EnableRenderOff()
    self.viewer3D.interactor.EnableRenderOff()

    # Turn-off plane widgets
    for i in range(3):
      self.viewer3D.planeWidgets[i].Off()

    # Assign data to 2D viewers sharing one cursorobject
    self.stack.SetInputData(reader.GetOutput())
    
    # Enable plane widgets
    for i in range(3):
      self.viewer3D.planeWidgets[i].SetInputConnection(reader.GetOutputPort())
      self.viewer3D.planeWidgets[i].SetPlaneOrientation(i)
      self.viewer3D.planeWidgets[i].SetSliceIndex(imageDims[i] // 2)
      self.viewer3D.planeWidgets[i].GetInteractor().Enable()
      self.viewer3D.planeWidgets[i].On()
      self.viewer3D.planeWidgets[i].InteractionOn()

    # Enable 2D viewers
    for i in range(3):
      self.stack.widget(i).viewer.GetRenderer().ResetCamera()
      self.stack.widget(i).viewer.GetInteractor().EnableRenderOn()

    # Enable interactors
    for i in range(3):
      self.stack.widget(i).interactor.Enable()
      self.stack.widget(i).viewer.GetInteractor().Enable()

    # Enable 3D rendering
    self.viewer3D.interactor.EnableRenderOn()
    # Reset camera for the renderer - otherwise it is set using dummy data
    self.viewer3D.planeWidgets[0].GetDefaultRenderer().ResetCamera()

    # Update 3D
    self.ResetViews()
    self.SetResliceMode(1)

  def ResetViews(self):
    for i in range(3):
      self.stack.widget(i).viewer.Reset()

    # Also sync the Image plane widget on the 3D view
    for i in range(3):
      ps = self.viewer3D.planeWidgets[i].GetPolyDataAlgorithm()
      ps.SetNormal(self.stack.widget(0).viewer.GetResliceCursor().GetPlane(i).GetNormal())
      ps.SetCenter(self.stack.widget(0).viewer.GetResliceCursor().GetPlane(i).GetOrigin())
      # If the reslice plane has modified, update it on the 3D widget
      self.viewer3D.planeWidgets[i].UpdatePlacement()

    # Render once
    self.Render()

  def Render(self):
    for i in range(3):
      self.stack.widget(i).viewer.Render()
    # Render 3D
    self.viewer3D.interactor.GetRenderWindow().Render()

  def SetResliceMode(self, mode):
    # Do we need to render planes if mode == 1?
    for i in range(3):
      self.stack.widget(i).viewer.SetResliceMode(mode)
      self.stack.widget(i).viewer.GetRenderer().ResetCamera()
      self.stack.widget(i).viewer.Render()

  def setup(self):
    self.setupUi(self)
    self.frame.setMaximumWidth(0)

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

    self.stack = Viewer2DStacked(self)
    self.vtk_widgets = []

    self.viewer3D = Viewer3D(self)
    self.viewer3D.AddCornerButtons()
    
    self.establishCallbacks()

    # Show widgets but hide non-existing data
    for i in range(3):
      self.stack.widget(i).show()
      self.stack.widget(i).viewer.GetImageActor().SetVisibility(False)

    # Layouts (to edges)
    #self.horizontalLayout.setContentsMargins(0,0,0,0)
    
    vert_layout0 = QVBoxLayout()
    horz_splitter0 = QSplitter(Qt.Horizontal)
    horz_splitter0.addWidget(self.stack)
    horz_splitter0.addWidget(self.viewer3D)
    vert_layout0.addWidget(horz_splitter0)
    vert_layout0.setContentsMargins(0, 0, 0, 0)
    self.vtk_panel.setLayout(vert_layout0)

    layout = QVBoxLayout()
    self.frame.setLayout(layout)
    self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
    self.statusBar().hide()
  def establishCallbacks(self):
    self.cb = ResliceCallback()
    self.cb.IPW = []
    self.cb.RCW = []
    for i in range(3):
      self.cb.IPW.append(self.viewer3D.planeWidgets[i])
      self.cb.RCW.append(self.stack.widget(i).viewer.GetResliceCursorWidget())

    for i in range(3):
      self.stack.widget(i).viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent, self.cb.onResliceAxesChanged)
      self.stack.widget(i).viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.WindowLevelEvent, self.cb.onWindowLevelChanged)
      self.stack.widget(i).viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceThicknessChangedEvent, self.cb.onWindowLevelChanged)
      self.stack.widget(i).viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResetCursorEvent, self.cb.onResliceAxesChanged)

      # Ignored after loading data!!! (why)
      self.stack.widget(i).viewer.GetInteractorStyle().AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)
      self.stack.widget(i).viewer.GetInteractorStyle().AddObserver('EndWindowLevelEvent', self.cb.onEndWindowLevelChanged)

      self.viewer3D.planeWidgets[i].AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)

      # Make them all share the same color map.
      #self.stack.widget(i).viewer.SetLookupTable(self.stack.widget(0).viewer.GetLookupTable())

      # Colormap from 2D to 3D widget
      self.viewer3D.planeWidgets[i].GetColorMap().SetLookupTable(self.stack.widget(0).viewer.GetLookupTable())
      #self.viewer3D.planeWidgets[i].GetColorMap().SetInputData(self.stack.widget(i).viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetColorMap().GetInput()) # deep copy (not needed)
      self.viewer3D.planeWidgets[i].SetColorMap(self.stack.widget(i).viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetColorMap())

  def initialize(self):
    # For a large application, attach to Qt's event loop instead.
    self.stack.Initialize()
    # 3D viewer
    self.viewer3D.Initialize()

  def closeEvent(self, event):
    # Stops the renderer such that the application can close without issues
    for i in range(3):
      self.stack.widget(i).interactor.close()
    self.viewer3D.interactor.close()
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
  main_window.setGeometry(0,40,main_window.width(), main_window.height())
  main_window.show()
  main_window.initialize()
  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
