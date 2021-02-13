#!/bin/env python3

# TODO: Stack of 2 widgets (postponed)
#       View Axial and Coronal Ultrasound
#       Sync views
#       Contours in US
# Thur
#       Coordinates
#       Grap US image
#       Run segmentation
# Fri
#       Transform plane (correction), slice and back
#       Introduce offset

import os
import sys
from importlib import reload

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import red, yellow

from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt, QSettings, QFileInfo, QRect
from PyQt5.QtWidgets import QFileDialog, QApplication, QAction, QCommonStyle, QStyle, QSplitter#, QGuiApplication

import numpy as np

from vtkUtils import hexCol, renderLinesAsTubes, AxesToTransform

ui_file = os.path.join(os.path.dirname(__file__), 'SmartLock3.ui')

ui, QMainWindow = loadUiType(ui_file)

from Viewer2D import Viewer3D, Viewer2D, Viewer2DStacked

from SegService import SegmentationService

# Initialize this using either CT or US
class ResliceCallback(object):
  def __init__(self):
    self.IPW = None
    self.RCW = None
    self.syncViews = False
  def onResliceAxesChanged(self, caller, ev):
    if (caller.GetClassName() == 'vtkResliceCursorWidget'):
      rep = caller.GetRepresentation()
      rep.GetResliceCursorActor().GetCursorAlgorithm().GetResliceCursor()
      if self.syncViews:
        # TODO: Call this when button is clicked
        cursor = rep.GetResliceCursorActor().GetCursorAlgorithm().GetResliceCursor()
        src = self.RCW[0].GetResliceCursorRepresentation().GetResliceCursor()
        dest = main_window.viewUS[0].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursor()
        for i in range(3):
          normal = src.GetPlane(i).GetNormal()
          dest.GetPlane(i).SetNormal(normal)
          origin = src.GetPlane(i).GetOrigin()
          dest.GetPlane(i).SetOrigin(origin)
          if i > 0:
            if (rep == self.RCW[i].GetResliceCursorRepresentation()):
              target = main_window.viewUS[i-1].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursor()
              target.SetCenter(cursor.GetCenter())
        for i in range(2):
          main_window.viewUS[i].UpdateContour()
        # TODO: Handle no US and update plane widget (see C++)
          
        
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
        main_window.stackCT.widget(i).UpdateContour()
        
    self.render() # TODO: Consider partly rendering
  def onEndWindowLevelChanged(self, caller, ev):
    wl = [main_window.stackCT.widget(0).viewer.GetColorWindow(), main_window.stackCT.widget(0).viewer.GetColorLevel()]
    main_window.stackCT.widget(0).viewer.SetColorWindow(wl[0])
    main_window.stackCT.widget(0).viewer.SetColorLevel(wl[1])
    return

  def onWindowLevelChanged(self, caller, ev):
    # 3D -> 2D views
    if (caller.GetClassName() == 'vtkImagePlaneWidget'):
      wl = [caller.GetWindow(), caller.GetLevel()]
      main_window.stackCT.widget(0).viewer.SetColorWindow(wl[0])
      main_window.stackCT.widget(0).viewer.SetColorLevel(wl[1])
    self.render()

  def render(self):
    # Render views
    for i in range(3):
      self.RCW[i].Render()
    # Render 3D
    self.IPW[0].GetInteractor().GetRenderWindow().Render()
    if self.syncViews:
      # Update ultrasound also
      for i in range(2):
        main_window.viewUS[i].viewer.GetResliceCursorWidget().Render()

class ResliceCallbackUS(object):
  def __init__(self):
    self.RCW = None
    self.syncViews = False
  def onResliceAxesChanged(self, caller, ev):
    if (caller.GetClassName() == 'vtkResliceCursorWidget'):
      rep = caller.GetRepresentation()
      rep.GetResliceCursorActor().GetCursorAlgorithm().GetResliceCursor()
      for i in range(2):
        main_window.viewUS[i].UpdateContour()
        
    self.render() # TODO: Consider partly rendering
  def onEndWindowLevelChanged(self, caller, ev):
    wl = [main_window.viewUS[0].viewer.GetColorWindow(), main_window.viewUS[0].viewer.GetColorLevel()]
    main_window.viewUS[0].viewer.SetColorWindow(wl[0])
    main_window.viewUS[0].viewer.SetColorLevel(wl[1])
    return

  def onWindowLevelChanged(self, caller, ev):
    # 3D -> 2D views (never happens)
    if (caller.GetClassName() == 'vtkImagePlaneWidget'):
      wl = [caller.GetWindow(), caller.GetLevel()]
      main_window.viewUS[0].viewer.SetColorWindow(wl[0])
      main_window.viewUS[0].viewer.SetColorLevel(wl[1])
    self.render()

  def render(self):
    # Render views
    for i in range(2):
      self.RCW[i].Render()

    
class SmartLock(QMainWindow, ui):
  def __init__(self):
    super(SmartLock, self).__init__()
    self.setup()
    self.DEFAULT_DIR_KEY = __file__
    self.segServer = SegmentationService(self)
    
  def initialize(self):
    # For a large application, attach to Qt's event loop instead.
    self.stackCT.Initialize()
    # 3D viewer
    self.viewer3D.Initialize()
    # Initialize US views
    for i in range(len(self.viewUS)):
      self.viewUS[i].Start()

  def setupMenu(self):
    loadAct = QAction('&Open CT', self)
    loadAct.setShortcut('Ctrl+O')
    loadAct.setStatusTip('Load CT data')
    loadAct.triggered.connect(lambda: self.onLoadClicked(0))

    outerSurfAct = QAction('Open &Exterior Surface', self)
    outerSurfAct.setShortcut('Ctrl+E')
    outerSurfAct.setStatusTip('Surf data')
    outerSurfAct.triggered.connect(lambda: self.onLoadClicked(2))

    innerSurfAct = QAction('Open &Interior Surface', self)
    innerSurfAct.setShortcut('Ctrl+I')
    innerSurfAct.setStatusTip('Surf data')
    innerSurfAct.triggered.connect(lambda: self.onLoadClicked(1))

    loadUSAct = QAction('Open &US', self)
    loadUSAct.setShortcut('Ctrl+U')
    loadUSAct.setStatusTip('Load US data')
    loadUSAct.triggered.connect(lambda: self.onLoadClicked(3))
    
    exitAct = QAction('&Exit', self)
    exitAct.setShortcut('ALT+F4')
    exitAct.setStatusTip('Exit application')
    exitAct.triggered.connect(self.close)

    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    fileMenu.addAction(loadAct)
    fileMenu.addAction(outerSurfAct)
    fileMenu.addAction(innerSurfAct)
    fileMenu.addAction(loadUSAct)
    fileMenu.addAction(exitAct)

    self.cboxPreset.currentIndexChanged.connect(self.onApplyPresetClicked)
    self.cboxPreset.setCurrentIndex(0)
    self.btnSyncCTUS.clicked.connect(lambda: self.onSyncClicked(0))
    self.btnSyncUSCT.clicked.connect(lambda: self.onSyncClicked(1))
    self.btnReg.clicked.connect(self.onRegClicked)
    self.btnSeg.clicked.connect(self.onSegClicked)
  def onSyncClicked(self, index):
    if index == 0:
      # Sync CT to US
      self.cb.syncViews = True
  def showHideCursor(self, visible=False, target=0):
    if target == 0:
      # CT view
      for iView in range(self.stackCT.count()):
        for iDim in range(3):
          prop = self.stackCT.widget(iView).viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(iDim)
          if visible:
            prop.SetOpacity(1.0)
          else:
            prop.SetOpacity(0.0)
    else:
      for iView in range(len(self.viewUS)):
        for iDim in range(3):
          prop = self.viewUS[iView].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(iDim)
          if visible:
            prop.SetOpacity(1.0)
          else:
            prop.SetOpacity(0.0)

  def readOnScreenBuffer(self):
    # Read on-screen buffer
    renderWindow = self.viewUS[1].viewer.GetRenderWindow()
    
    oldSB = renderWindow.GetSwapBuffers()
    renderWindow.SwapBuffersOff()
    
    # Hide cursor
    self.showHideCursor(False, 1)
    self.viewUS[1].ShowHideAnnotations(False)
    # Hide contours
    self.viewUS[1].ShowHideContours(False)
    
    self.windowToImageFilter = vtk.vtkWindowToImageFilter()
    self.windowToImageFilter.SetInput(renderWindow)

    self.windowToImageFilter.SetScale(1)
    self.windowToImageFilter.SetInputBufferTypeToRGBA()
    
    self.windowToImageFilter.ReadFrontBufferOff()
    self.windowToImageFilter.Update() # Issues a render on input
    
    renderWindow.SetSwapBuffers(oldSB)
    renderWindow.SwapBuffersOn()
    #self.segImage = self.windowToImageFilter.GetOutput()

    self.showHideCursor(True, 1)
    self.viewUS[1].ShowHideAnnotations(True)
    self.viewUS[1].ShowHideContours(True)
    
  def readOffScrenBuffer(self):
    print("Off-screen")
    renderWindow = self.viewUS[1].viewer.GetRenderWindow()
    if not renderWindow.SetUseOffScreenBuffers(True):
      glRenderWindow.DebugOn()
      glRenderWindow.SetUseOffScreenBuffers(True)
      glRenderWindow.DebugOff()
      print("Unable create a hardware frame buffer, the graphic board or driver can be too old")
      sys.exit(-1)
      renderWindow.Render()

    # Hide cursor
    self.showHideCursor(False, 1)
    self.viewUS[1].ShowHideAnnotations(False)
    # Hide contours
    self.viewUS[1].ShowHideContours(False)

    self.windowToImageFilter = vtk.vtkWindowToImageFilter()
    self.windowToImageFilter.SetInput(renderWindow)
    self.windowToImageFilter.Update() # Issues a render call
  
    renderWindow.SetUseOffScreenBuffers(False)

    self.showHideCursor(True, 1)
    self.viewUS[1].ShowHideAnnotations(True)
    self.viewUS[1].ShowHideContours(True)
    
  def onSegClicked(self):
    print("Segmentation")
    showCoordinates = False
    savePNGImage = True
    saveMetaImage = True
    
    # Both works
    #self.readOnScreenBuffer()
    self.readOffScrenBuffer()
    self.segImage = self.windowToImageFilter.GetOutput()

    if savePNGImage:
      writer = vtk.vtkPNGWriter()
      writer.SetFileName('./output.png')
      writer.SetInputData(self.segImage)
      writer.Write()

    # Compute spacing in world-coordinates
    renderer = self.viewUS[1].viewer.GetRenderer()      
    coordinate = vtk.vtkCoordinate()
    coordinate.SetCoordinateSystemToNormalizedDisplay()

    dims = self.segImage.GetDimensions()
    coordinate.SetValue(1.0, 0.0)
    lowerRight = np.array(coordinate.GetComputedWorldValue(renderer))
    coordinate.SetValue(0.0, 0.0)
    lowerLeft = np.array(coordinate.GetComputedWorldValue(renderer))
    coordinate.SetValue(0.0, 1.0)
    upperLeft = np.array(coordinate.GetComputedWorldValue(renderer))
    dx = np.sqrt(np.sum((lowerRight - lowerLeft) ** 2)) / dims[0]
    dy = np.sqrt(np.sum((upperLeft - lowerLeft) ** 2)) / dims[1]
    self.segImage.SetSpacing(dx,dy,0)

    self.trans = vtk.vtkMatrix4x4()
    
    # Compute direction matrix
    sliceAxes = self.viewUS[1].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceAxes()
    orientation = vtk.vtkMatrix3x3()
    if vtk.VTK_VERSION > '9.0.0':
      for i in range(3):
        for j in range(3):
          orientation.SetElement(i,j,sliceAxes.GetElement(i,j))
      self.segImage.SetDirectionMatrix(orientation)
      self.segImage.SetOrigin(lowerLeft)
      self.segImage.Modified()
    else:
      # Compute transformation from x = (1,0,0), y = (0,1,0) to origin and new orientation
      normal0 = (0,0,1)
      first0 = (1,0,0)
      origin0 = (0,0,0)
      
      origin1 = lowerLeft
      first1 = lowerRight - lowerLeft
      second1 = upperLeft - lowerLeft

      normal1 = np.cross(first1, second1)
      normal1 = normal1 / np.sqrt(np.sum(normal1**2))
      
      first1 = first1 / np.sqrt(np.sum(first1**2))

      self.trans = AxesToTransform(normal0, first0, origin0,
                                   normal1, first1, origin1)

    if showCoordinates:
      for i in range(2):
        for j in range(2):
          coordinate.SetValue(float(i), float(j), 0.0)
          sys.stdout.write("(%d, %d): " % (i,j))
          sys.stdout.write("(%f, " % (coordinate.GetComputedWorldValue(renderer)[0]))
          sys.stdout.write("%f, " % (coordinate.GetComputedWorldValue(renderer)[1]))
          sys.stdout.write("%f)" % (coordinate.GetComputedWorldValue(renderer)[2]))
          print("")

    if saveMetaImage:
      # Save to disk
      smoother = vtk.vtkImageGaussianSmooth()
      smoother.SetStandardDeviations(3.0, 3.0)
      smoother.SetDimensionality(2)
      smoother.SetInputData(self.segImage)
      smoother.Update()
      
      writer = vtk.vtkMetaImageWriter()
      writer.SetFileName('./output.mhd')
      writer.SetInputConnection(smoother.GetOutputPort())
      writer.Write()

    # For VTK version 8.2, we need to add the orientation as a separate parameter
    self.segServer.execute.emit(self.segImage, self.trans)

    
  def onRegClicked(self):
    print("Registration")
    # TODO: Hide cursor, render to back buffer
  def onApplyPresetClicked(self, index):
    window = 200
    level = 100
    index = self.cboxPreset.currentIndex()

    if (index == 0):
      rng = [0,0]
      if (self.stackCT.widget(0)):
        rng = self.stackCT.widget(0).viewer.GetInput().GetScalarRange()
        window = rng[1]-rng[0]
        level = (rng[0]+rng[1])/2.0
    for i in range(3):
      if self.stackCT.widget(i):
        self.stackCT.widget(i).viewer.SetColorWindow(window)
        self.stackCT.widget(i).viewer.SetColorLevel(level)
        self.stackCT.widget(i).viewer.Render()
    
  def setup(self):
    self.setupUi(self)
    self.setupMenu()
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
                                 "    border: 1px outset darkgrey "
                                 " } " 
                                 " QSplitter::handle:vertical{ "
                                 "    border: 1px outset darkgrey "
                                 " } ")
            widget.setHandleWidth(2) # Default is 3
    # Setup 3D viewer
    self.viewer3D = Viewer3D(self)
    self.viewer3D.AddCornerButtons()

    self.layout3D.setContentsMargins(0,0,0,0)
    self.layout3D.addWidget(self.viewer3D)

    # Setup CT viewer
    self.stackCT = Viewer2DStacked(self)
    self.layoutCT.setContentsMargins(0,0,0,0)
    self.layoutCT.insertWidget(0,self.stackCT)

    # Setup US views
    self.viewUS = []
    self.viewUS.append(Viewer2D(self, 1))
    self.viewUS.append(Viewer2D(self, 2))

    # Make all views share the same cursor object
    for i in range(2):
      self.viewUS[i].viewer.SetResliceCursor(self.viewUS[0].viewer.GetResliceCursor())

    # Cursor representation (anti-alias)
    for i in range(len(self.viewUS)):
      for j in range(3):
        prop = self.viewUS[i].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(j)
        renderLinesAsTubes(prop)
    
    # Remove when stacked works for 2 images
    for i in range(len(self.viewUS)):
      # Set background for 2D views
      color = [0.0, 0.0, 0.0]
      color[self.viewUS[i].iDim] = 1
      for j in range(3):
        color[j] = color[j] / 4.0
      self.viewUS[i].viewer.GetRenderer().SetBackground(color)
      self.viewUS[i].interactor.Disable()
        
    self.establishCallbacks()
    
    # Show widgets but hide non-existing data
    for i in range(3):
      self.stackCT.widget(i).show()
      self.stackCT.widget(i).viewer.GetImageActor().SetVisibility(False)

    # Show widgets but hide non-existing data
    for i in range(2):
      self.viewUS[i].show()
      self.viewUS[i].viewer.GetImageActor().SetVisibility(False)

    self.layoutUS0.setContentsMargins(0,0,0,0)
    self.layoutUS0.insertWidget(0, self.viewUS[0])
    self.layoutUS1.setContentsMargins(0,0,0,0)
    self.layoutUS1.insertWidget(0, self.viewUS[1])
      
  def onLoadClicked(self, fileType):
    mySettings = QSettings()
    fileDir = mySettings.value(self.DEFAULT_DIR_KEY)
    print(fileDir)
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileDialog = QFileDialog()
    fileDialog.setDirectory(fileDir)

    defaultFile = {0 : 'CT-Abdomen.mhd',
                   1 : 'Connected.vtp',
                   2 : 'Liver_3D_Fast_Marching_Closed.vtp',
                   3 : 'VesselVolume.mhd'}[fileType]

    defaultFile = os.path.join(fileDir, defaultFile)
    
    fileName, _ = \
      fileDialog.getOpenFileName(self,
                                 "QFileDialog.getOpenFileName()",
                                 defaultFile, "All Files (*)MHD Files (*.mhd) VTP Files (*.vtp)",
                                 options=options)
    if fileName:
      # Update default dir
      currentDir = QFileInfo(fileName).absoluteDir()
      mySettings.setValue(self.DEFAULT_DIR_KEY,
                          currentDir.absolutePath())
      info = QFileInfo(fileName)
      if (info.completeSuffix() == "mhd") and fileType == 0:
        # Load data
        self.loadFile(fileName)
      elif (info.completeSuffix() == "vtp") and fileType == 1:
        self.loadSurface(fileName, contours=True)
      elif (info.completeSuffix() == "vtp") and fileType == 2:
        self.loadSurface(fileName, contours=False)
      elif (info.completeSuffix() == "mhd") and fileType == 3:
        self.loadUSFile(fileName)

  def loadSurface(self, fileName, contours=True):
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(fileName)
    reader.Update()

    # Take the largest connected component
    connectFilter = vtk.vtkPolyDataConnectivityFilter()
    connectFilter.SetInputConnection(reader.GetOutputPort())
    connectFilter.SetExtractionModeToLargestRegion()
    connectFilter.Update()

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
    prop.SetColor(vtk.vtkColor3d(hexCol("#517487"))) # 25% lighter

    # Assign actor to the renderer
    prop.SetOpacity(0.35)
    self.viewer3D.planeWidgets[0].GetDefaultRenderer().AddActor(self.vessels)
    # TODO: Make this work if read before US
    if contours:
      for i in range(self.stackCT.count()):
        self.stackCT.widget(i).InitializeContour(self.vesselNormals,color=red)
      for i in range(len(self.viewUS)):
        self.viewUS[i].InitializeContour(self.vesselNormals)
    self.Render()

  # TODO
  def loadUSFile(self, fileName):
    # Load VTK Meta Image
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(fileName)
    reader.Update()
    imageDims = reader.GetOutput().GetDimensions()

    # Disable renderers
    for i in range(len(self.viewUS)):
      self.viewUS[i].viewer.GetInteractor().EnableRenderOff()

    # Share one cursor object
    for i in range(len(self.viewUS)):
      self.viewUS[i].viewer.SetResliceCursor(self.viewUS[0].viewer.GetResliceCursor())
      
    # Assign data to 2D viewers sharing one cursorobject
    for i in range(len(self.viewUS)):
      self.viewUS[i].SetInputData(reader.GetOutput())

    # Enable 2D viewers
    for i in range(len(self.viewUS)):
      self.viewUS[i].viewer.GetRenderer().ResetCamera()
      self.viewUS[i].viewer.GetInteractor().EnableRenderOn()

    # Enable interactors
    for i in range(len(self.viewUS)):
      self.viewUS[i].viewer.GetInteractor().Enable()

    # Update 3D
    self.ResetUSViews()
    self.SetUSResliceMode(1)
    self.Render()
  def loadFile(self, fileName):
    # Load VTK Meta Image
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(fileName)
    reader.Update()
    imageDims = reader.GetOutput().GetDimensions()

    # Disable renderers and widgets
    self.stackCT.EnableRenderOff()
    self.viewer3D.interactor.EnableRenderOff()

    # Turn-off plane widgets
    self.viewer3D.Off()

    # Assign data to 2D viewers sharing one cursorobject
    self.stackCT.SetInputData(reader.GetOutput())

    # Enable plane widgets
    self.viewer3D.EnablePlaneWidgets(reader)

    # Enable 2D viewers
    for i in range(self.stackCT.count()):
      self.stackCT.widget(i).viewer.GetRenderer().ResetCamera()
      self.stackCT.widget(i).viewer.GetInteractor().EnableRenderOn()

    # Enable interactors
    for i in range(self.stackCT.count()):
      self.stackCT.widget(i).interactor.Enable()
      self.stackCT.widget(i).viewer.GetInteractor().Enable()

    # Enable 3D rendering
    self.viewer3D.interactor.EnableRenderOn()

    # Reset camera for the renderer - otherwise it is set using dummy data
    self.viewer3D.planeWidgets[0].GetDefaultRenderer().ResetCamera()

    # Update 3D
    self.ResetViews()
    self.SetResliceMode(1)

  def establishCallbacks(self):
    self.cb = ResliceCallback()
    self.cb.IPW = []
    self.cb.RCW = []
    for i in range(3):
      self.cb.IPW.append(self.viewer3D.planeWidgets[i])
      self.cb.RCW.append(self.stackCT.widget(i).viewer.GetResliceCursorWidget())

    for i in range(3):
      self.stackCT.widget(i).viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent, self.cb.onResliceAxesChanged)
      self.stackCT.widget(i).viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.WindowLevelEvent, self.cb.onWindowLevelChanged)
      self.stackCT.widget(i).viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceThicknessChangedEvent, self.cb.onWindowLevelChanged)
      self.stackCT.widget(i).viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResetCursorEvent, self.cb.onResliceAxesChanged)

      # Ignored after loading data!!! (why)
      self.stackCT.widget(i).viewer.GetInteractorStyle().AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)
      self.stackCT.widget(i).viewer.GetInteractorStyle().AddObserver('EndWindowLevelEvent', self.cb.onEndWindowLevelChanged)

      self.viewer3D.planeWidgets[i].AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)

      # Colormap from 2D to 3D widget
      self.viewer3D.planeWidgets[i].GetColorMap().SetLookupTable(self.stackCT.widget(0).viewer.GetLookupTable())
      self.viewer3D.planeWidgets[i].SetColorMap(self.stackCT.widget(i).viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetColorMap())

    self.cb1 = ResliceCallbackUS()
    self.cb1.RCW = []
    for i in range(2):
      self.cb1.RCW.append(self.viewUS[i].viewer.GetResliceCursorWidget())
    for i in range(2):
      self.viewUS[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceAxesChangedEvent, self.cb1.onResliceAxesChanged)
      self.viewUS[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.WindowLevelEvent, self.cb1.onWindowLevelChanged)
      self.viewUS[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResliceThicknessChangedEvent, self.cb1.onWindowLevelChanged)
      self.viewUS[i].viewer.GetResliceCursorWidget().AddObserver(vtk.vtkResliceCursorWidget.ResetCursorEvent, self.cb1.onResliceAxesChanged)

      # Ignored after loading data!!! (why)
      self.viewUS[i].viewer.GetInteractorStyle().AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb.onWindowLevelChanged)
      self.viewUS[i].viewer.GetInteractorStyle().AddObserver('EndWindowLevelEvent', self.cb.onEndWindowLevelChanged)
  
  def ResetViews(self):
    for i in range(self.stackCT.count()):
      self.stackCT.widget(i).viewer.Reset()

    # Also sync the Image plane widget on the 3D view
    for i in range(3):
      ps = self.viewer3D.planeWidgets[i].GetPolyDataAlgorithm()
      ps.SetNormal(self.stackCT.widget(0).viewer.GetResliceCursor().GetPlane(i).GetNormal())
      ps.SetCenter(self.stackCT.widget(0).viewer.GetResliceCursor().GetPlane(i).GetOrigin())
      # If the reslice plane has modified, update it on the 3D widget
      self.viewer3D.planeWidgets[i].UpdatePlacement()

    # Render once
    self.Render()

  def ResetUSViews(self):
    for i in range(len(self.viewUS)):
      self.viewUS[i].viewer.Reset()
    
  def Render(self):
    for i in range(self.stackCT.count()):
      self.stackCT.widget(i).viewer.Render()
    # Render 3D
    self.viewer3D.interactor.GetRenderWindow().Render()
    # Render US
    for i in range(len(self.viewUS)):
      self.viewUS[i].viewer.Render()

  def SetResliceMode(self, mode):
    # Do we need to render planes if mode == 1?
    for i in range(self.stackCT.count()):
      self.stackCT.widget(i).viewer.SetResliceMode(mode)
      self.stackCT.widget(i).viewer.GetRenderer().ResetCamera()
      self.stackCT.widget(i).viewer.Render()
  def SetUSResliceMode(self, mode):
    for i in range(len(self.viewUS)):
      self.viewUS[i].viewer.SetResliceMode(mode)
      self.viewUS[i].viewer.GetRenderer().ResetCamera()
      self.viewUS[i].viewer.Render()
  def closeEvent(self, event):
    # Stops the renderer such that the application can close without issues
    self.stackCT.close()
    self.viewer3D.interactor.close()
    for i in range(len(self.viewUS)):
      self.viewUS[i].interactor.close()
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
