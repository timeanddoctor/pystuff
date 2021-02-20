#!/bin/env python3
import os
import sys
from collections import deque

import math

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import red, yellow, black

from PyQt5.uic import loadUiType
from PyQt5.QtCore import Qt, QObject, QCoreApplication,\
  QSettings, QFileInfo
from PyQt5.Qt import QCursor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout,\
  QSplitter, QFrame, QSpacerItem, QPushButton, QToolButton,\
  QAction, QFileDialog, QApplication,  QSizePolicy, QToolTip,\
  QCheckBox

defaultFiles = {0 : 'VesselVolumeUncompressed.mhd',
                1 : 'Connected.vtp'}

ui_file = os.path.join(os.path.dirname(__file__), 'RotContourViewer.ui')

ui, QMainWindow = loadUiType(ui_file)

from FloatSlider import QFloatSlider

def hexCol(s):
  if isinstance(s,str):
    if "#" in s:
      s = s.lstrip("#")
    return tuple(int(s[i : i + 2], 16)/255.0 for i in (0, 2, 4))
  return None

def renderLinesAsTubes(prop):
  prop.SetEdgeVisibility(1)
  prop.SetPointSize(4)
  prop.SetLineWidth(3)
  prop.SetRenderLinesAsTubes(1)
  return prop

# TODO: Call render on EndInteraction
class ResliceCallback(object):
  def __init__(self):
    self.IPW = None
    self.RCW = None
    self.Contours = None
    self.first = False
  def onResliceAxesChanged(self, caller, ev):
    if (caller.GetClassName() == 'vtkResliceCursorWidget'):
      rep = caller.GetRepresentation()
      rep.GetResliceCursorActor().GetCursorAlgorithm().GetResliceCursor()
      # Update 3D widget
      for i in range(3):
        # Only needed for the actual plane (TODO: Optimize)
        pda = self.IPW[i].GetPolyDataAlgorithm()
        ps = self.RCW[i].GetResliceCursorRepresentation().GetPlaneSource()
        origin = ps.GetOrigin()
        pda.SetOrigin(origin)
        pda.SetPoint1(ps.GetPoint1())
        pda.SetPoint2(ps.GetPoint2())
        # If the reslice plane has modified, update it on the 3D widget
        self.IPW[i].UpdatePlacement()
        main_window.vtk_widgets[i].UpdateContours(main_window.imgToMeshTransform)

    self.render()
  def onEndWindowLevelChanged(self, caller, ev):
    # Colormap is shared, so use widget 0
    viewer = main_window.vtk_widgets[0].viewer
    wl = [viewer.GetColorWindow(),
          viewer.GetColorLevel()]
    viewer.SetColorWindow(wl[0])
    viewer.SetColorLevel(wl[1])
    return

  def onWindowLevelChanged(self, caller, ev):
    if (caller.GetClassName() == 'vtkImagePlaneWidget'):
      wl = [caller.GetWindow(), caller.GetLevel()]
      # Triggers an update of vtkImageMapToWindowLevelColors
      # - updates annotations
      main_window.vtk_widgets[0].viewer.SetColorWindow(wl[0])
      main_window.vtk_widgets[0].viewer.SetColorLevel(wl[1])
    self.render()

  def render(self):
    # Render views
    for i in range(3):
      self.RCW[i].Render()
    # Render 3D
    self.IPW[0].GetInteractor().GetRenderWindow().Render()
  def Render(self, caller, ev):
    # This may help on the missing render calls!!
    self.render()
class FourPaneViewer(QMainWindow, ui):
  def __init__(self):
    super(FourPaneViewer, self).__init__()
    self.setup()
    self.DEFAULT_DIR_KEY = __file__
    self.imgToMeshTransform = vtk.vtkTransform()
    self.imgToMeshTransform.Identity()
    self.imgToMeshTransform.PostMultiply()
    self.vessels = None
  def onOrientationClicked(self):
    """
    Blue widget. TODO: Try to actually rotate mesh instead
    """
    sender = self.sender()
    local = self.btnLocal.isChecked()
    if sender == self.btnTransX:
      dx = self.sliderTX.getFloatValue()
      if local:
        vx, vy, vn = self.vtk_widgets[2].GetOrientation()
        vtk.vtkMath.MultiplyScalar(vx, dx)
        self.imgToMeshTransform.Translate(vx[0], vx[1], vx[2])
      else:
        self.imgToMeshTransform.Translate(dx,0.0,0.0)
    elif sender == self.btnRotX:
      da = self.sliderRX.getFloatValue()
      if local:
        vx, vy, vn = self.vtk_widgets[2].GetOrientation()
        cursorPosition = self.vtk_widgets[2].GetPosition()
        self.imgToMeshTransform.Translate(-cursorPosition[0],
                                          -cursorPosition[1],
                                          -cursorPosition[2])
        self.imgToMeshTransform.RotateWXYZ(da, vx)
        self.imgToMeshTransform.Translate(cursorPosition[0],
                                          cursorPosition[1],
                                          cursorPosition[2])
        
      else:
        self.imgToMeshTransform.RotateWXYZ(da, 1.0, 0.0, 0.0)
    elif sender == self.btnTransZ:
      dz = self.sliderTZ.getFloatValue()
      if local:
        vx, vy, vn = self.vtk_widgets[2].GetOrientation()
        vtk.vtkMath.MultiplyScalar(vn, dz)
        self.imgToMeshTransform.Translate(vn[0], vn[1], vn[2])
      else:
        self.imgToMeshTransform.Translate(0.0,0.0,dz)
    elif sender == self.btnRotZ:
      da = self.sliderRZ.getFloatValue()
      if local:
        # TODO: Move to origin, rotate, move back
        vx, vy, vn = self.vtk_widgets[2].GetOrientation()
        cursorPosition = self.vtk_widgets[2].GetPosition()
        print(cursorPosition)
        self.imgToMeshTransform.Translate(-cursorPosition[0],
                                          -cursorPosition[1],
                                          -cursorPosition[2])
        self.imgToMeshTransform.RotateWXYZ(da, vn)

        if 0:
          # Debug code (cursorPosition is in the corner!!!!)
          
          # viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetPosition
          
          # Show cursor position in 3D
          pointSource = vtk.vtkPointSource()
          pointSource.SetNumberOfPoints(10)
          pointSource.SetCenter(cursorPosition)
          pointSource.SetRadius(10.0)
          pointSource.Update()
          
          mapper = vtk.vtkPolyDataMapper()
          mapper.SetInputConnection(pointSource.GetOutputPort())
          
          self.actor = vtk.vtkActor()
          self.actor.SetMapper(mapper)
          self.actor.GetProperty().SetColor(red)
          self.vtk_widgets[2].viewer.GetRenderer().AddActor(self.actor)
          self.vtk_widgets[2].viewer.Render()

        self.imgToMeshTransform.Translate(cursorPosition[0],
                                          cursorPosition[1],
                                          cursorPosition[2])
      else:
        self.imgToMeshTransform.RotateWXYZ(da, 0.0, 0.0, 1.0)
        
    for i in range(3):
      self.vtk_widgets[i].UpdateContours(self.imgToMeshTransform)
    if self.vessels is not None:
      self.vessels.SetUserTransform(self.imgToMeshTransform)
    self.Render()
  def onLoadClicked(self, fileType):
    mySettings = QSettings()
    fileDir = mySettings.value(self.DEFAULT_DIR_KEY)
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileDialog = QFileDialog()
    fileDialog.setDirectory(fileDir)
    fileName, _ = \
      fileDialog.getOpenFileName(self,
                                 "QFileDialog.getOpenFileName()",
                                 "", "All Files (*);"
                                 ";MHD Files (*.mhd);"
                                 "; VTP Files (*.vtp)",
                                 options=options)
    if fileName:
      # Update default dir
      currentDir = QFileInfo(fileName).absoluteDir()
      mySettings.setValue(self.DEFAULT_DIR_KEY,
                          currentDir.absolutePath())
      info = QFileInfo(fileName)
      if (info.completeSuffix() == "vtp") and fileType == 1:
        self.loadSurface(fileName)
      elif (info.completeSuffix() == "mhd") and fileType == 0:
        # Load data
        self.loadFile(fileName)
  def loadSurface(self, fileName):
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(fileName)
    reader.Update()

    # Take the largest connected component
    connectFilter = vtk.vtkPolyDataConnectivityFilter()
    connectFilter.SetInputConnection(reader.GetOutputPort())
    connectFilter.SetExtractionModeToLargestRegion()
    connectFilter.Update();

    self.vesselPolyData = connectFilter.GetOutput()

    # Compute normals
    self.vesselNormals = vtk.vtkPolyDataNormals()
    self.vesselNormals.SetInputData(self.vesselPolyData)

    # Mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(self.vesselNormals.GetOutputPort())

    # Actor for vessels
    self.vessels = vtk.vtkActor()
    self.vessels.SetMapper(mapper)
    prop = self.vessels.GetProperty()
    #prop.SetColor(vtk.vtkColor3d(hexCol("#517487"))) # 25% lighter
    #prop.SetOpacity(0.35)
    prop.SetColor(red)
    prop.SetOpacity(1.0)

    # Assign actor to the renderer
    self.planeWidget[0].GetDefaultRenderer().AddActor(self.vessels)

    for i in range(3):
      self.vtk_widgets[i].InitializeContours(self.vesselNormals)
    self.Render()
    
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
      #self.vtk_widgets[i].interactor.Enable()
      self.vtk_widgets[i].viewer.GetInteractor().Enable()

    axesActor = vtk.vtkAxesActor()
    self.axes = vtk.vtkOrientationMarkerWidget()
    self.axes.SetOrientationMarker( axesActor)
    self.axes.SetInteractor( self.vtk_widgets[3] )
    self.axes.SetViewport( 0.8, 0.0, 1.0, 0.2)
    #self.planeWidget[0].GetDefaultRenderer().AddActor(axesActor)
    self.axes.EnabledOn()
    self.axes.InteractiveOn()

    # Enable 3D rendering
    self.vtk_widgets[3].EnableRenderOn()
    # Reset camera for the renderer - otherwise it is set using dummy data
    #self.planeWidget[0].GetDefaultRenderer().DisplayToWorld()
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

    # Gradient background
    ren.SetBackground(245.0/255.0,245.0/255.0,245.0/255.0)
    ren.SetBackground2(170.0/255.0,170.0/255.0,170.0/255.0)
    ren.GradientBackgroundOn()

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

      prop = pw.GetTextProperty()
      prop.SetColor(black)
      pw.Modified()
      # Set background for 2D views
      for j in range(3):
        color[j] = color[j] / 4.0
      self.vtk_widgets[i].viewer.GetRenderer().SetBackground(color)
      self.vtk_widgets[i].interactor.Disable()
      self.planeWidget.append(pw)

    # Annotation
    cornerAnnotation = vtk.vtkCornerAnnotation()
    cornerAnnotation.SetLinearFontScaleFactor(2)
    cornerAnnotation.SetNonlinearFontScaleFactor(1)
    cornerAnnotation.SetMaximumFontSize(20)
    cornerAnnotation.SetText(vtk.vtkCornerAnnotation.UpperLeft, '3D')
    cornerAnnotation.GetTextProperty().SetColor( 1, 1, 1 )
    cornerAnnotation.SetWindowLevel(self.vtk_widgets[0].viewer.GetWindowLevel())
    ren.AddViewProp(cornerAnnotation)
    
    self.establishCallbacks()

    # Show widgets but hide non-existing data
    for i in range(3):
      self.vtk_widgets[i].show()
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
    horz_splitter1.addWidget(self.vtk_widgets[3])
    vert_splitter.addWidget(horz_splitter1)
    horz_layout0.addWidget(vert_splitter)
    horz_layout0.setContentsMargins(0, 0, 0, 0)
    self.vtk_panel.setLayout(horz_layout0)

    vert_layout = QVBoxLayout()
    horz_layout1 = QHBoxLayout()
    self.btnSagittal = QPushButton("S")
    self.btnSagittal.setCheckable(True)
    self.btnSagittal.setChecked(True)
    horz_layout1.addWidget(self.btnSagittal)
    self.btnCoronal = QPushButton("C")
    self.btnCoronal.setCheckable(True)
    self.btnCoronal.setChecked(True)
    horz_layout1.addWidget(self.btnCoronal)
    self.btnAxial = QPushButton("A")
    self.btnAxial.setCheckable(True)
    self.btnAxial.setChecked(True)

    self.btnSagittal.clicked.connect(self.togglePlanes)
    self.btnCoronal.clicked.connect(self.togglePlanes)
    self.btnAxial.clicked.connect(self.togglePlanes)

    horz_layout1.addWidget(self.btnAxial)
    verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    vert_layout.addSpacerItem(verticalSpacer)

    horzSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
    self.btnLocal = QCheckBox("local")
    self.btnReset = QPushButton("Reset")
    horz_layout4 = QHBoxLayout()
    horz_layout4.addWidget(self.btnLocal)
    horz_layout4.addSpacerItem(horzSpacer)
    horz_layout4.addWidget(self.btnReset)
    vert_layout.addItem(horz_layout4)

    for i in range(3):
      layout0 = QHBoxLayout()
      exec("self.sliderT"+chr(88+i)+"=QFloatSlider(Qt.Horizontal,self)")
      exec("self.sliderT"+chr(88+i)+".setRange(-10.0, 10.0, 21)")
      exec("self.sliderT"+chr(88+i)+".setFloatValue(0.0)")
      exec("self.sliderT"+chr(88+i)+".floatValueChanged.connect(lambda value: QToolTip.showText(QCursor.pos(), \"%f\" % (value), None))")
      exec("self.btnTrans"+chr(88+i)+" = QToolButton()")
      act = QAction()
      exec("act.setText(\"T"+chr(88+i)+"\")")
      exec("self.btnTrans"+chr(88+i)+".setDefaultAction(act)")
      exec("self.btnTrans"+chr(88+i)+".clicked.connect(self.onOrientationClicked)")
      exec("layout0.addWidget(self.sliderT"+chr(88+i)+")")
      exec("layout0.addWidget(self.btnTrans"+chr(88+i)+")")
    
      layout1 = QHBoxLayout()
      exec("self.sliderR"+chr(88+i)+" = QFloatSlider(Qt.Horizontal,self)")
      exec("self.sliderR"+chr(88+i)+".setRange(-90.0,90.0,37)")
      exec("self.sliderR"+chr(88+i)+".setFloatValue(0.0)")
      exec("self.sliderR"+chr(88+i)+".floatValueChanged.connect(lambda value: QToolTip.showText(QCursor.pos(), \"%f\" % (value), None))")
      exec("self.btnRot"+chr(88+i)+" = QToolButton()")
      act = QAction()
      exec("act.setText(\"R"+chr(88+i)+"\")")
      exec("self.btnRot"+chr(88+i)+".setDefaultAction(act)")
      exec("self.btnRot"+chr(88+i)+".clicked.connect(self.onOrientationClicked)")
      exec("layout1.addWidget(self.sliderR"+chr(88+i)+")")
      exec("layout1.addWidget(self.btnRot"+chr(88+i)+")")
      vert_layout.addItem(layout0)
      vert_layout.addItem(layout1)
        

    vert_layout.addItem(horz_layout1)
    self.btnReset.clicked.connect(self.onResetOffset)

    self.frame.setLayout(vert_layout)
  def ResetSliders(self):
    self.sliderRZ.setFloatValue(0.0)
    self.sliderRX.setFloatValue(0.0)
    self.sliderTX.setFloatValue(0.0)
    self.sliderTZ.setFloatValue(0.0)
  def onResetOffset(self):
    self.imgToMeshTransform.Identity()
    self.ResetSliders()
    for i in range(3):
      self.vtk_widgets[i].UpdateContours(self.imgToMeshTransform)
    self.vessels.SetUserTransform(self.imgToMeshTransform)
    self.Render()
  def togglePlanes(self, state):
    obj = self.sender()
    index = -1
    isChecked = state
    if (obj == self.btnSagittal):
      index = 0
    elif obj == self.btnCoronal:
      index = 1
    elif obj == self.btnAxial:
      index = 2
      
    if (index > -1):
      if not isChecked:
        self.planeWidget[index].Off()
      else:
        self.planeWidget[index].On()
    return
  def establishCallbacks(self):
    self.cb = ResliceCallback()
    self.cb.IPW = []
    self.cb.RCW = []
    for i in range(3):
      self.cb.IPW.append(self.planeWidget[i])
      self.cb.RCW.append(self.vtk_widgets[i].viewer.GetResliceCursorWidget())

    for i in range(3):
      rcw = self.vtk_widgets[i].viewer.GetResliceCursorWidget()
      rcw.AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent, self.cb.onResliceAxesChanged)
      rcw.AddObserver(vtk.vtkResliceCursorWidget.WindowLevelEvent, self.cb.onWindowLevelChanged)
      rcw.AddObserver(vtk.vtkResliceCursorWidget.ResliceThicknessChangedEvent, self.cb.onWindowLevelChanged)
      rcw.AddObserver(vtk.vtkResliceCursorWidget.ResetCursorEvent, self.cb.onResliceAxesChanged)
      # Ignored after loading data (why)
      self.vtk_widgets[i].viewer.GetInteractorStyle().AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)
      self.vtk_widgets[i].viewer.GetInteractorStyle().AddObserver('EndWindowLevelEvent', self.cb.onEndWindowLevelChanged)
      self.planeWidget[i].AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)

      # Make them all share the same color map.
      self.vtk_widgets[i].viewer.SetLookupTable(self.vtk_widgets[0].viewer.GetLookupTable())
      self.planeWidget[i].GetColorMap().SetLookupTable(self.vtk_widgets[0].viewer.GetLookupTable())
      self.planeWidget[i].GetColorMap().SetInputData(self.vtk_widgets[i].viewer.GetResliceCursorWidget().\
                                                     GetResliceCursorRepresentation().GetColorMap().GetInput())
      self.planeWidget[i].SetColorMap(self.vtk_widgets[i].viewer.GetResliceCursorWidget().\
                                      GetResliceCursorRepresentation().GetColorMap())

  def initialize(self):
    # For a large application, attach to Qt's event loop instead.
    for i in range(3):
      self.vtk_widgets[i].start()
    # 3D viewer
    self.vtk_widgets[3].Initialize()
    self.vtk_widgets[3].Start()

  def closeEvent(self, event):
    # Stops the renderer such that the application can close without issues
    for i in range(3):
      self.vtk_widgets[i].interactor.close()
    self.vtk_widgets[3].close()
    event.accept()

class Viewer2D(QFrame):
  def __init__(self, parent, iDim=0):
    super(Viewer2D, self).__init__(parent)
    interactor = QVTKRenderWindowInteractor(self)
    self.edgeActor = None
    self.iDim = iDim
    self.layout = QHBoxLayout(self)
    self.layout.addWidget(interactor)
    self.layout.setContentsMargins(0, 0, 0, 0)
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
    self.interactor = interactor
  def GetPosition(self):
    """
    Position of cursor, not the plane
    """
    origin = self.GetResliceCursor().GetCenter()
    return origin
  def GetOrientation(self):
    # Normal can be obtained using self.GetResliceCursor().GetPlane(iDim).GetNormal()
    renderer = self.viewer.GetRenderer()
    # Get screen frame
    coordinate = vtk.vtkCoordinate()
    coordinate.SetCoordinateSystemToNormalizedDisplay()
    coordinate.SetValue(0.0, 0.0) # Lower left
    lowerLeft = coordinate.GetComputedWorldValue(renderer)
    coordinate.SetValue(1.0, 0.0) # Lower right
    lowerRight = coordinate.GetComputedWorldValue(renderer)
    coordinate.SetValue(0.0, 1.0) # Upper left
    upperLeft = coordinate.GetComputedWorldValue(renderer)
    first1 = vtk.vtkVector3d()
    vtk.vtkMath.Subtract(lowerRight, lowerLeft, first1)
    tmp = vtk.vtkMath.Distance2BetweenPoints(lowerRight, lowerLeft)
    vtk.vtkMath.MultiplyScalar(first1, 1.0/math.sqrt(tmp))
    second1 = vtk.vtkVector3d()
    vtk.vtkMath.Subtract(upperLeft, lowerLeft, second1)
    tmp = vtk.vtkMath.Distance2BetweenPoints(upperLeft, lowerLeft)
    vtk.vtkMath.MultiplyScalar(second1, 1.0/math.sqrt(tmp))
    normal1 = vtk.vtkVector3d()
    vtk.vtkMath.Cross(first1, second1, normal1)
    return first1, second1, normal1

  def SetInputData(self, data):
    self.viewer.SetInputData(data)
    # Corner annotation, can use <slice>, <slice_pos>, <window_level>
    cornerAnnotation = vtk.vtkCornerAnnotation()
    cornerAnnotation.SetLinearFontScaleFactor(2)
    cornerAnnotation.SetNonlinearFontScaleFactor(1)
    cornerAnnotation.SetMaximumFontSize(20)
    cornerAnnotation.SetText(vtk.vtkCornerAnnotation.UpperLeft,
                             {2:'Axial',
                              0:'Sagittal',
                              1:'Coronal'}[self.iDim])
    prop = cornerAnnotation.GetTextProperty()
    prop.BoldOn()
    color = deque((1,0,0))
    color.rotate(self.iDim)
    cornerAnnotation.GetTextProperty().SetColor(tuple(color))
    cornerAnnotation.SetImageActor(self.viewer.GetImageActor())
    
    cornerAnnotation.SetWindowLevel(self.viewer.GetWindowLevel())
    self.viewer.GetRenderer().AddViewProp(cornerAnnotation)
  def InitializeContours(self, data):
    # Update contours
    self.plane = vtk.vtkPlane()
    RCW = self.viewer.GetResliceCursorWidget()    
    ps = RCW.GetResliceCursorRepresentation().GetPlaneSource()
    self.plane.SetOrigin(ps.GetOrigin())
    normal = ps.GetNormal()
    self.plane.SetNormal(normal)

    # Generate line segments
    cutEdges = vtk.vtkCutter()
    cutEdges.SetInputConnection(main_window.vesselNormals.GetOutputPort())
    cutEdges.SetCutFunction(self.plane)
    cutEdges.GenerateCutScalarsOff()
    cutEdges.SetValue(0, 0.5)
          
    # Put together into polylines
    self.cutStrips = vtk.vtkStripper()
    self.cutStrips.SetInputConnection(cutEdges.GetOutputPort())
    self.cutStrips.Update()

    edgeMapper = vtk.vtkPolyDataMapper()
    edgeMapper.SetInputConnection(self.cutStrips.GetOutputPort())
          
    self.edgeActor = vtk.vtkActor()
    self.edgeActor.SetMapper(edgeMapper)
    prop = self.edgeActor.GetProperty()
    renderLinesAsTubes(prop)
    prop.SetColor(yellow) # If Scalars are extracted - they turn green

    # Move in front of image
    transform = vtk.vtkTransform()
    transform.Translate(normal)
    self.edgeActor.SetUserTransform(transform)

    # Add actor to renderer
    self.viewer.GetRenderer().AddViewProp(self.edgeActor)

  def SetResliceCursor(self, cursor):
    self.viewer.SetResliceCursor(cursor)

  def GetResliceCursor(self):
    return self.viewer.GetResliceCursor()

  def UpdateContours(self, transform=None):
    if self.edgeActor is not None:
      RCW = self.viewer.GetResliceCursorWidget()    
      ps = RCW.GetResliceCursorRepresentation().GetPlaneSource()
      origin = ps.GetOrigin()
      normal = ps.GetNormal()

      if transform is not None:
        # Transform - apply inverse transform to origin and normal
        inv = vtk.vtkTransform()
        inv.DeepCopy(transform)
        inv.Inverse()
        origin = inv.TransformPoint(origin)
        cutNormal = inv.TransformVector(normal)
        # TODO: Transform vector normal
        
      self.plane.SetOrigin(origin)
      self.plane.SetNormal(cutNormal)
      self.plane.Modified()

      # Move in front of image (z-buffer)
      userTransform = vtk.vtkTransform()
      userTransform.Identity()
      userTransform.PostMultiply()
      if transform is not None:
        userTransform.Concatenate(transform)
      userTransform.Translate(normal)
      self.edgeActor.SetUserTransform(transform)
  def start(self):
    self.interactor.Initialize()
    self.interactor.Start()

if __name__ == '__main__':

  # Qt::AA_ShareOpenGLContexts using QCoreApplication::setAttribute
  
  if QApplication.startingUp():
    app = QApplication(sys.argv)
  else:
    app = QCoreApplication.instance()
  app.setApplicationName("FourPaneViewer")
  app.setOrganizationName("KitWare")
  app.setOrganizationDomain("www.kitware.com")
  main_window = FourPaneViewer()
  main_window.setGeometry(0,40,main_window.width(), main_window.height())
  main_window.show()
  main_window.initialize()
  if len(sys.argv) > 1:
    mySettings = QSettings()
    fileDir = mySettings.value(main_window.DEFAULT_DIR_KEY)
    main_window.loadFile(os.path.join(fileDir,defaultFiles[0]))
    main_window.loadSurface(os.path.join(fileDir,defaultFiles[1])) 
  
  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
