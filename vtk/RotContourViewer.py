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
  QCheckBox, QGroupBox

# TODO: Replace imgToMeshTransform with (misAlign * reAlign)
#       SliderPressed, SliderMoved, SliderReleased

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
        # Needed to trigger new intersection and move in front
        main_window.vtk_widgets[i].UpdateContours()
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
  def onRender(self, caller, ev):
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
    self.lort = 0.0
    self.setup()
    self.DEFAULT_DIR_KEY = __file__
    self.imgToMeshTransform = vtk.vtkTransform()
    self.imgToMeshTransform.Identity()
    self.imgToMeshTransform.PostMultiply()
    self.vessels = None

    self.startX = 0.0
    self.startY = 0.0
    self.startZ = 0.0

    self.startRX = 0.0
    self.startRY = 0.0
    self.startRZ = 0.0
    
  def onOrientationClicked(self):
    """
    Blue widget. TODO: Try to actually rotate mesh instead
    """
    sender = self.sender()
    local = self.btnLocal.isChecked()

    widget = self.vtk_widgets[2]

    vx, vy, vn = widget.GetOrientation()
    cursorPosition = widget.GetPosition()

    if sender in [self.btnRotX, self.btnRotY, self.btnRotZ]:
      if local:
        rotAxis = {self.btnRotX : vx,
                   self.btnRotY : vy,
                   self.btnRotZ : vn}[sender]
      else:
        rotAxis = {self.btnRotX : (1, 0, 0),
                   self.btnRotY : (0, 1, 0),
                   self.btnRotZ : (0, 0, 1)}[sender]
        
      da = {self.btnRotX : self.sliderRX,
            self.btnRotY : self.sliderRY,
            self.btnRotZ : self.sliderRZ}[sender].getFloatValue()
      if local:
        self.imgToMeshTransform.Translate(-cursorPosition[0],
                                          -cursorPosition[1],
                                          -cursorPosition[2])
        self.imgToMeshTransform.RotateWXYZ(da, rotAxis)
        self.imgToMeshTransform.Translate(cursorPosition[0],
                                          cursorPosition[1],
                                          cursorPosition[2])
      else:
        self.imgToMeshTransform.RotateWXYZ(da,
                                           rotAxis[0],
                                           rotAxis[1],
                                           rotAxis[2])
    elif sender in [self.btnTransX, self.btnTransY, self.btnTransZ]:
      dxyz = {self.btnTransX : self.sliderTX,
              self.btnTransY : self.sliderTY,
              self.btnTransZ : self.sliderTZ}[sender].getFloatValue()

      if local:
        axis = {self.btnTransX : vx,
                self.btnTransY : vy,
                self.btnTransZ : vn}[sender]
      else:
        axis = {self.btnTransX : (1, 0, 0),
                self.btnTransY : (0, 1, 0),
                self.btnTransZ : (0, 0, 1)}[sender]

      if local:
        vtk.vtkMath.MultiplyScalar(axis, dxyz)
        self.imgToMeshTransform.Translate(axis[0], axis[1], axis[2])
      else:
        self.imgToMeshTransform.Translate(axis[0]*dxyz,
                                          axis[1]*dxyz,
                                          axis[2]*dxyz)

    #test = vtk.vtkTransform()
    #test.Translate(0.2,10,17)
    #self.imgToMeshTransform.Concatenate(test)
    for i in range(3):
      self.vtk_widgets[i].UpdateContours()#self.imgToMeshTransform)
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
    prop.SetColor(red)
    prop.SetOpacity(1.0)

    # Assign actor to the renderer
    self.planeWidget[0].GetDefaultRenderer().AddActor(self.vessels)

    for i in range(3):
      self.vtk_widgets[i].InitializeContours(self.vesselNormals)
      self.vtk_widgets[i].SetTransform(self.imgToMeshTransform)

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

    self.origin = self.vtk_widgets[0].GetResliceCursor().GetCenter()

    # Store initial normals

    self.normals = []
    
    src = self.vtk_widgets[0].GetResliceCursor()

    for i in range(3):
      normal = src.GetPlane(i).GetNormal()
      self.normals.append(normal)
    
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

    # Sagittal/Coronal/Axial planes
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
    horz_layout1.addWidget(self.btnAxial)

    self.btnSagittal.clicked.connect(self.togglePlanes)
    self.btnCoronal.clicked.connect(self.togglePlanes)
    self.btnAxial.clicked.connect(self.togglePlanes)

    verticalSpacer = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
    vert_layout.addSpacerItem(verticalSpacer)

    groupBox = QGroupBox("Misalignment")
    vert_layout.addWidget(groupBox)
    mis_layout = QVBoxLayout()

    # Misalignment
    
    # Local and reset
    horzSpacer = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
    self.btnLocal = QCheckBox("local")
    self.btnReset = QPushButton("Reset")
    self.btnReset.clicked.connect(self.onResetOffset)

    # Misalignment buttons
    horz_layout4 = QHBoxLayout()
    horz_layout4.addWidget(self.btnLocal)
    horz_layout4.addSpacerItem(horzSpacer)
    horz_layout4.addWidget(self.btnReset)
    mis_layout.addItem(horz_layout4)
    
    # Misalignment sliders
    [(self.sliderTX, self.btnTransX),
     (self.sliderTY, self.btnTransY),
     (self.sliderTZ, self.btnTransZ),
     (self.sliderRX, self.btnRotX),
     (self.sliderRY, self.btnRotY),
     (self.sliderRZ, self.btnRotZ)] = self.createMisAlignment(mis_layout, self.onOrientationClicked)
    groupBox.setLayout(mis_layout)

    # Movement
    
    groupBox = QGroupBox("Movement")
    vert_layout.addWidget(groupBox)
    groupLayout = QVBoxLayout()
    
    # Local and reset
    horzSpacer = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
    
    # TODO: Return values
    self.btnMoveLocal = QCheckBox("local")
    self.btnReset1 = QPushButton("Reset")
    self.btnReset1.clicked.connect(self.onResetMovement)
    
    # Movement sliders
    layout = QHBoxLayout()
    layout.addWidget(self.btnMoveLocal)
    layout.addSpacerItem(horzSpacer)
    layout.addWidget(self.btnReset1)
    groupLayout.addItem(layout)

    [(self.sliderMTX, self.sliderMTY, self.sliderMTZ),
     (self.sliderMRX, self.sliderMRY, self.sliderMRZ)] = self.createMovement(groupLayout, self.onSliderPressed, self.onMove)
    groupBox.setLayout(groupLayout)
      
    self.frame.setLayout(vert_layout)

  def createMisAlignment(self, mis_layout, callback):
    controls0 = []
    controls1 = []
    for i in range(3):
      # Translation
      layout0 = QHBoxLayout()
      slider=QFloatSlider(Qt.Horizontal,self)
      slider.setRange(-50.0, 50.0, 101)
      slider.setFloatValue(0.0)
      slider.floatValueChanged.connect(lambda value: QToolTip.showText(QCursor.pos(), "%f" % (value), None))
      button = QToolButton()
      act = QAction()
      act.setText("T"+chr(88+i))
      button.setDefaultAction(act)
      button.clicked.connect(callback)
      layout0.addWidget(slider)
      layout0.addWidget(button)
      controls0.append((slider,button))

      # Rotation
      layout1 = QHBoxLayout()
      slider = QFloatSlider(Qt.Horizontal,self)
      slider.setRange(-90.0,90.0,37)
      slider.setFloatValue(0.0)
      slider.floatValueChanged.connect(lambda value: QToolTip.showText(QCursor.pos(), "%f" % (value), None))
      button = QToolButton()
      act = QAction()
      act.setText("R"+chr(88+i))
      button.setDefaultAction(act)
      button.clicked.connect(callback)
      layout1.addWidget(slider)
      layout1.addWidget(button)
      mis_layout.addItem(layout0)
      mis_layout.addItem(layout1)
      controls1.append((slider,button))
    return controls0 + controls1

  def createMovement(self, inLayout, onPressed, onReleased):
    controls0 = []
    controls1 = []

    for i in range(3):
      layout0 = QHBoxLayout()
      slider=QFloatSlider(Qt.Horizontal,self)
      slider.setRange(-50.0, 50.0, 101)
      slider.setFloatValue(0.0)
      slider.floatValueChanged.connect(lambda value, slider=slider, i=i: QToolTip.showText(QCursor.pos(), "T" + chr(88+i) + ": %f" % (value), None))
      slider.sliderPressed.connect(lambda i=i: onPressed(0, i))
      slider.sliderReleased.connect(lambda i=i: onReleased(0, i))
      layout0.addWidget(slider)
      controls0.append(slider)
      inLayout.addItem(layout0)

      layout1 = QHBoxLayout()
      slider = QFloatSlider(Qt.Horizontal,self)
      slider.setRange(-45.0, 45.0, 91)
      slider.setFloatValue(0.0)
      slider.floatValueChanged.connect(lambda value, slider=slider, i=i: QToolTip.showText(QCursor.pos(), "R" + chr(88+i) + ": %f" % (value), None))
      slider.sliderPressed.connect(lambda i=i, slider=slider: onPressed(1, i))
      slider.sliderReleased.connect(lambda i=i, slider=slider: onReleased(1, i))
      layout1.addWidget(slider)
      controls1.append(slider)
      inLayout.addItem(layout1)
      
    return controls0, controls1

  def onSliderPressed(self, TR, dim):
    if TR == 0:
      startVal = {0 : self.startX,
                  1 : self.startY,
                  2 : self.startZ}[dim]
    else:
      startVal = {0 : self.startRX,
                  1 : self.startRY,
                  2 : self.startRZ}[dim]
      
    startVal = self.sender().getFloatValue()

  def onResetMovement(self):
    print("Reset movement")
    self.ResetViews()
    self.cb.onResliceAxesChanged(self.vtk_widgets[0].viewer.GetResliceCursorWidget(),vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent)
    self.Render()
    return
    
  def onMove(self, TR, dim):
    # TODO: Support rotate and local movement
    if TR == 0:
      startVal = {0 : self.startX,
                  1 : self.startY,
                  2 : self.startZ}[dim]
    else:
      startVal = {0 : self.startRX,
                  1 : self.startRY,
                  2 : self.startRZ}[dim]
      
    diff = self.sender().getFloatValue() - startVal

    local = self.btnMoveLocal.isChecked()
    
    # For local transformations
    vx, vy, vz = self.vtk_widgets[0].GetOrientation()
    
    origin = self.vtk_widgets[0].GetResliceCursor().GetCenter()
    normal = self.vtk_widgets[0].GetResliceCursor().GetPlane(dim).GetNormal()
    
    newOrigin = origin

    tmp = vtk.vtkTransform()
    
    if TR == 0:
      # Move origin
      if local:
        vtk.vtkMath.MultiplyScalar(vx, diff)
        vtk.vtkMath.MultiplyScalar(vy, diff)
        vtk.vtkMath.MultiplyScalar(vz, diff)
        newOrigin = (origin[0] + vx[0] + vy[0] + vz[0],
                     origin[1] + vx[1] + vy[1] + vz[1],
                     origin[2] + vx[2] + vy[2] + vz[2])
      else:
        newOrigin = (origin[0]+diff*normal[0], origin[1]+diff*normal[1], origin[2]+diff*normal[2])
    else:
      # Rotation around normal
      tmp.RotateWXYZ(diff, normal[0], normal[1], normal[2])
    
    # Set origin of cursor object
    target = self.vtk_widgets[0].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursor()
    for i in range(3):
      target.GetPlane(i).SetOrigin(newOrigin)
      
    # Modify normals
    for i in range(3):
      newNormal = tmp.TransformVector(target.GetPlane(i).GetNormal())
      target.GetPlane(i).SetNormal(newNormal)

    # Set center for all widgets
    for i in range(3):
      self.vtk_widgets[i].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursor().SetCenter(newOrigin)

    self.Render()
      
    # Execute callback to sync contours
    self.cb.onResliceAxesChanged(self.vtk_widgets[dim].viewer.GetResliceCursorWidget(),vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent)

    # Reset slider
    self.sender().setFloatValue(0.0)

    
  def ResetSliders(self):
    self.sliderRZ.setFloatValue(0.0)
    self.sliderRX.setFloatValue(0.0)
    self.sliderTX.setFloatValue(0.0)
    self.sliderTZ.setFloatValue(0.0)
  def onResetOffset(self):
    self.imgToMeshTransform.Identity()
    self.ResetSliders()
    for i in range(3):
      self.vtk_widgets[i].UpdateContours()
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
      # Ignored after loading data, the interactors are no longer used
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

    self.trans = None    # Misalignment
    self.invTrans = None # Inverse
    
    self.adjustment = vtk.vtkTransform() # Move in front
    #self.adjustment.PostMultiply()
    
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
    self.cutEdges = vtk.vtkCutter()
    self.cutEdges.SetInputConnection(main_window.vesselNormals.GetOutputPort())
    self.cutEdges.SetCutFunction(self.plane)
    self.cutEdges.GenerateCutScalarsOff()
    self.cutEdges.SetValue(0, 0.5)
          
    # Put together into polylines
    self.cutStrips = vtk.vtkStripper()
    self.cutStrips.SetInputConnection(self.cutEdges.GetOutputPort())
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

# TODO: Figure out pipeline

# Proper way would be to define pipeline, which
# updates when orientation is changed

# Try with a method SetTransform and store inverse

  def SetTransform(self, tf):
    self.trans = tf
    self.invTrans = tf.GetInverse()
    if 0:
      self.edgeActor.SetUserTransform(tf)
    else:
      # New way using extra adjustment
      tmp = vtk.vtkTransform() # Stored as a user transform
      tmp.PostMultiply()
      tmp.Concatenate(tf)
      tmp.Concatenate(self.adjustment)
      self.edgeActor.SetUserTransform(tmp)

  def UpdateContours(self):
    if self.edgeActor is not None:
      RCW = self.viewer.GetResliceCursorWidget()    
      ps = RCW.GetResliceCursorRepresentation().GetPlaneSource()
      origin = ps.GetOrigin()
      normal = ps.GetNormal()
      # TEST use cursor instead (works)
      #origin = self.GetResliceCursor().GetCenter()
      #normal = self.GetResliceCursor().GetPlane(self.iDim).GetNormal()
      if self.trans is not None:
        origin = self.invTrans.TransformPoint(origin)
        cutNormal = self.invTrans.TransformVector(normal)
        
      self.plane.SetOrigin(origin)
      self.plane.SetNormal(cutNormal)
      self.plane.Modified()

      self.cutEdges.Update()

      # Move in front of image (z-buffer) - premultiply
      self.adjustment.Identity()
      self.adjustment.Translate(normal)

      # TEST this
      #main_window.vesselNormals.Modified()
    

# TODO: Experiment setting transform once and only modify
# usertransform in callback

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
