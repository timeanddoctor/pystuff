#!/bin/env python3

# AVOID SetMatrix on chains!!!!

# TODO:
# 1. Sliders from RotContourViewer
# 2. Reg matrix in RegService
# 3. Display translation error, angle error, dot product. (deg, x,y,z) = self.alignment.GetOrientationWXYZ()

# 4. Dump to file, 1mm, 2mm, 5mm, 10mm
# 5. Perform bifurcation in-plane
#    a. in-plane translation (x2)
#    b. out-of-plane translation
# 6. Vessel in-plane
#    a. in-plane translation (x2)
#    b. out-of-plane translation
# 7. Crossing vessels
#    a. in-plane translation (x2)
#    b. out-of-plane translation

# Something works, but red moves

import os
import sys
import math
from importlib import reload

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import red, green, pink, yellow

from PyQt5.uic import loadUiType
from PyQt5.QtCore import QCoreApplication, Qt,\
  QSettings, QFileInfo, QRect, pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QApplication,\
  QAction, QCommonStyle, QStyle, QSplitter

from vtkUtils import hexCol, renderLinesAsTubes, AxesToTransform

ui_file = os.path.join(os.path.dirname(__file__), 'SmartLock3.ui')

ui, QMainWindow = loadUiType(ui_file)

deltaXYZ = 1.0 # [mm] steps for misalignment

from Viewer2DPlus import Viewer2D, Viewer2DStacked
from Viewer3DPlus import Viewer3D

from SegServicePlus import SegmentationService
from RegServicePlus import RegistrationService

def enum(*sequential, **named):
  enums = dict(zip(sequential, range(len(sequential))), **named)
  reverse = dict((value, key) for key, value in enums.items())
  enums['reverse_mapping'] = reverse
  return type('Enum', (), enums)

# Two simple enumerations
direction = enum('UP','DOWN','LEFT','RIGHT')
azel = enum('AZ','EL', 'RESET')

defaultFiles = {0 : 'CT-Abdomen.mhd',
                1 : 'Connected.vtp',
                2 : 'Liver_3D_Fast_Marching_Closed.vtp',
                3 : 'VesselVolumeUncompressed.mhd',
                4 : 'LiverWithoutBoundaries.mhd',
                5 : 'White.mhd',
                6 : 'hej.mhd'}


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
          main_window.viewUS[i].UpdateContours()
        # TODO: Handle no US and update plane widget (see C++)
      # Update 3D widget
      for i in range(len(self.IPW)):
        # Only needed for the actual plane (TODO: Optimize)
        pda = self.IPW[i].GetPolyDataAlgorithm()
        ps = self.RCW[i].GetResliceCursorRepresentation().GetPlaneSource()
        origin = ps.GetOrigin()
        pda.SetOrigin(origin)
        pda.SetPoint1(ps.GetPoint1())
        pda.SetPoint2(ps.GetPoint2())
        # If the reslice plane has modified, update it on the 3D widget
        self.IPW[i].UpdatePlacement()
        # TEST disable
        main_window.stackCT.widget(i).UpdateContours()
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
        # TEST
        main_window.viewUS[i].UpdateContours()

      if self.syncViews:
        # TODO: Call this when button is clicked
        cursor = rep.GetResliceCursorActor().GetCursorAlgorithm().GetResliceCursor()
        src = self.RCW[0].GetResliceCursorRepresentation().GetResliceCursor()
        dest = main_window.stackCT.widget(0).viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursor()
        for i in range(3):
          normal = src.GetPlane(i).GetNormal()
          dest.GetPlane(i).SetNormal(normal)
          origin = src.GetPlane(i).GetOrigin()
          dest.GetPlane(i).SetOrigin(origin)
          
          if (rep == self.RCW[i].GetResliceCursorRepresentation()):
            target = main_window.stackCT.widget(i).viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursor()
            target.SetCenter(cursor.GetCenter())
        for i in range(3):
          main_window.stackCT.widget(i).UpdateContours()

        
    self.render() # TODO: Consider partly rendering

  def onEndWindowLevelChanged(self, caller, ev):
    viewer = main_window.viewUS[0].viewer
    wl = [viewer.GetColorWindow(), viewer.GetColorLevel()]
    viewer.SetColorWindow(wl[0])
    viewer.SetColorLevel(wl[1])
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
    self.regServer = RegistrationService(self)
    self.usActor = None # Used for overlay
    self.usCorrectedActor = None
    self.lastUSContours = None

    self.vessel = None
    
    # Update this when load interior and exterior
    self.CTContours = None

    # Append all surfaces to this
    self.appendFilter = vtk.vtkAppendPolyData()

    # TODO: Consider using SetInput
    self.alignment = vtk.vtkTransform()
    self.alignment.Identity() # Never change using SetMatrix
    self.alignment.PostMultiply()

    self.misAlignment = vtk.vtkTransform()
    self.misAlignment.PostMultiply()
    
    self.regAlignment = vtk.vtkTransform()
    self.regAlignment.PostMultiply()

    #self.alignment.Concatenate(self.misAlignment)
    #self.alignment.Concatenate(self.regAlignment)

    self.alignment.SetInput(self.regAlignment)
    self.regAlignment.SetInput(self.misAlignment)

    # TEST (No difference)
    #self.misAlignment.SetInput(self.regAlignment)
    #self.regAlignment.SetInput(self.alignment)
    
  def onArrowsClicked(self, _view, _direction):
    self.misAlignment.PreMultiply()
    if _view == azel.AZ:
      first, second, normal = self.viewUS[1].GetDirections()
      if (_direction == direction.RIGHT):
        # Modify transformation 
        vtk.vtkMath.MultiplyScalar(first, deltaXYZ)
        self.misAlignment.Translate(first)
      elif (_direction == direction.LEFT):
        vtk.vtkMath.MultiplyScalar(first, -deltaXYZ)
        self.misAlignment.Translate(first)
      elif (_direction == direction.UP):
        # You cannot get and set matrix????
        vtk.vtkMath.MultiplyScalar(second, deltaXYZ)
        self.misAlignment.Translate(second)
      elif (_direction == direction.DOWN):
        vtk.vtkMath.MultiplyScalar(second, -deltaXYZ)
        self.misAlignment.Translate(second)
      # Do we need this?
      self.misAlignment.PostMultiply()
      self.regAlignment.Identity()
      self.regAlignment.Concatenate(self.misAlignment)
      self.alignment.Identity()
      self.alignment.Concatenate(self.regAlignment)
      print(self.misAlignment.GetNumberOfConcatenatedTransforms())
    elif _view == azel.EL:
      first, second, normal = self.viewUS[0].GetDirections()
      if (_direction == direction.RIGHT):
        # Modify transformation 
        vtk.vtkMath.MultiplyScalar(first, deltaXYZ)
        self.misAlignment.Translate(first)
      elif (_direction == direction.LEFT):
        vtk.vtkMath.MultiplyScalar(first, -deltaXYZ)
        self.misAlignment.Translate(first)
      elif (_direction == direction.UP):
        vtk.vtkMath.MultiplyScalar(second, deltaXYZ)
        self.misAlignment.Translate(second)
      elif (_direction == direction.DOWN):
        vtk.vtkMath.MultiplyScalar(second, -deltaXYZ)
        self.misAlignment.Translate(second)
      # VERY IMPORTANT
      # Do we need this?
      self.misAlignment.PostMultiply()
      self.regAlignment.Identity()
      self.regAlignment.Concatenate(self.misAlignment)
      self.alignment.Identity()
      self.alignment.Concatenate(self.regAlignment)
      
    elif _view == azel.RESET:
      # Remove actors from 3D
      if self.usActor is not None or self.usCorrectedActor is not None:
        self.viewer3D.interactor.Disable()
        if self.usCorrectedActor is not None:
          self.viewer3D.planeWidgets[0].GetDefaultRenderer().RemoveActor(self.usCorrectedActor)
          self.usCorrectedActor = None
        if self.usActor is not None:
          self.viewer3D.planeWidgets[0].GetDefaultRenderer().RemoveActor(self.usActor)
          self.usActor = None
        self.viewer3D.interactor.Enable()
        #self.viewer3D.planeWidgets[0].GetInteractor().GetRenderWindow().Render()
      self.viewUS[1].RemoveOverlay()
      self.misAlignment.Identity()
      self.regAlignment.Identity()

    # Triggers entire chain
    self.alignment.Update()
    
    # Update contours
    for i in range(2):
      self.viewUS[i].UpdateContours()
    self.Render()
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

    self.btnRightAzimuth.clicked.connect(lambda: self.onArrowsClicked(azel.AZ, direction.RIGHT))
    self.btnLeftAzimuth.clicked.connect(lambda: self.onArrowsClicked(azel.AZ, direction.LEFT))
    self.btnUpAzimuth.clicked.connect(lambda: self.onArrowsClicked(azel.AZ, direction.UP))
    self.btnDownAzimuth.clicked.connect(lambda: self.onArrowsClicked(azel.AZ, direction.DOWN))
    self.btnResetAzimuth.clicked.connect(lambda: self.onArrowsClicked(azel.RESET, direction.DOWN))
    
    self.btnRightElevation.clicked.connect(lambda: self.onArrowsClicked(azel.EL, direction.RIGHT))
    self.btnLeftElevation.clicked.connect(lambda: self.onArrowsClicked(azel.EL, direction.LEFT))
    self.btnUpElevation.clicked.connect(lambda: self.onArrowsClicked(azel.EL, direction.UP))
    self.btnDownElevation.clicked.connect(lambda: self.onArrowsClicked(azel.EL, direction.DOWN))
    self.btnResetElevation.clicked.connect(lambda: self.onArrowsClicked(azel.RESET, direction.DOWN))
    
  def onSyncClicked(self, index):
    sender = self.sender()
    if index == 0:
      if sender.isChecked():
        self.cb.syncViews = True
      else:
        self.cb.syncViews = False
    if index == 1:
      if sender.isChecked():
        self.cb1.syncViews = True
      else:
        self.cb1.syncViews = False
        

  def onSegClicked(self):
    print("Segmentation")
  
    showCoordinates = False
    savePNGImage = True
    saveMetaImage = False
    self.btnSeg.setEnabled(False)

    if savePNGImage:
      img = self.viewUS[1].GetScreenImage(useOffScreenBuffer=False,
                                          showContours=True)
      writer = vtk.vtkPNGWriter()
      writer.SetFileName('./output.png')
      writer.SetInputData(img)
      writer.Write()

    self.segImage = self.viewUS[1].GetScreenImage(useOffScreenBuffer=False)
      
    # We move image to (0,0,0) but keep size
    self.segImage.SetOrigin(0,0,0)

    # Transform from xy-plane to current plane
    transMat = self.viewUS[1].GetScreenTransform()
    self.trans = vtk.vtkTransform()
    self.trans.SetMatrix(transMat)

    if showCoordinates:
      # Center of plane
      origin = self.viewUS[1].viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetPlaneSource().GetOrigin()
      for i in range(2):
        for j in range(2):
          coordinate.SetValue(float(i), float(j), 0.0)
          sys.stdout.write("(%d, %d): " % (i,j))
          sys.stdout.write("(%f, " % (coordinate.GetComputedWorldValue(renderer)[0]))
          sys.stdout.write("%f, " % (coordinate.GetComputedWorldValue(renderer)[1]))
          sys.stdout.write("%f)" % (coordinate.GetComputedWorldValue(renderer)[2]))
          print("")

    ################################
    # Write misalignment to output
    ################################

    displacementError = self.misAlignment.GetPosition()

    # Screen rotation
    screenRot = vtk.vtkTransform()
    screenRot.DeepCopy(self.trans)
    screenRot.PostMultiply()
    # Remove translation
    pos = screenRot.GetPosition()
    screenRot.Translate(-pos[0], -pos[1], -pos[2])
    # World to screen rotation
    screenRot.Inverse()

    # Displacement on screen [mm]
    screenDisplacmentError = screenRot.TransformPoint(displacementError)
    sys.stdout.write('dx: %3.2f [mm], dy: %3.2f [mm], dz: %3.2f [mm]\n' %\
                     (screenDisplacmentError[0],
                      screenDisplacmentError[1],
                      screenDisplacmentError[2]))

    # Rotation error on screen
    deg, xAxis, yAxis, zAxis = self.misAlignment.GetOrientationWXYZ()
    normal = self.viewUS[1].GetResliceCursor().GetPlane(self.viewUS[1].iDim).GetNormal()
    dotNAxis = xAxis*normal[0] + yAxis*normal[1] + zAxis*normal[2]
    sys.stdout.write('da: %3.2f [degrees], (axis.N): %3.2f\n' % (deg, dotNAxis))
    
    # Callback for displaying segmentation
    self.segServer.ready.connect(self.updateSegmentation)

    # For VTK version 8.2, we need to add the orientation as a
    # separate parameter, self.trans
    self.segServer.execute.emit(self.segImage, self.trans)

  @pyqtSlot(float, 'PyQt_PyObject', 'PyQt_PyObject')
  def updateRegistration(self, rmse, mat, newContours):
    print('RMSE: %f' % (rmse))

    # TEST AVOID INVERTING
    invMat = vtk.vtkMatrix4x4()
    vtk.vtkMatrix4x4.Invert(mat, invMat)

    # NOT GOOD - concatenate invMat to existing
    # PROBLEM
    self.regAlignment.SetMatrix(invMat)
    self.regAlignment.Update()

    print(invMat)
    print(self.regAlignment.GetMatrix())

    for i in range(len(self.viewUS)):
      self.viewUS[i].UpdateContours()
      self.viewUS[i].viewer.GetResliceCursorWidget().Render()

    if self.usCorrectedActor is not None:
      self.viewer3D.interactor.Disable()
      self.viewer3D.planeWidgets[0].GetDefaultRenderer().RemoveActor(self.usCorrectedActor)
      self.viewer3D.interactor.Enable()
      self.usCorrectedActor = None

    # Tube filter and color them green
    tubes = vtk.vtkTubeFilter()
    tubes.SetInputData(newContours)
    tubes.CappingOn()
    tubes.SidesShareVerticesOff()
    tubes.SetNumberOfSides(12)
    tubes.SetRadius(1.0)
      
    edgeMapper = vtk.vtkPolyDataMapper()
    edgeMapper.SetInputConnection(tubes.GetOutputPort())
    edgeMapper.ScalarVisibilityOff()
      
    self.usCorrectedActor = vtk.vtkActor()
    self.usCorrectedActor.SetMapper(edgeMapper)

    
    self.usCorrectedActor.SetUserTransform(self.alignment)
    prop = self.usCorrectedActor.GetProperty()
    prop.SetColor(yellow)
    
    self.viewer3D.planeWidgets[0].GetDefaultRenderer().AddActor(self.usCorrectedActor)

    # GetMatrix is the entire product, SetMatrix is only the local

    what = self.regAlignment # Why not alignment
    
    # Print error after registration to output, TODO: Project to plane
    posError = what.GetPosition()
    print(self.regAlignment.GetMatrix())
    print(posError)
    absPosError = math.sqrt(posError[0]**2+posError[1]**2+posError[2]**2)
    sys.stdout.write('dp: %3.2f [mm]\n' % (absPosError))
    angleError, xAxis, yAxis, zAxis = what.GetOrientationWXYZ()
    sys.stdout.write('da: %3.2f [degrees]\n' % (angleError))
    
    self.btnReg.setEnabled(True)
    self.Render()

      
  @pyqtSlot('PyQt_PyObject')
  def updateSegmentation(self, contours):
    self.lastUSContours = contours
    edgeMapper = vtk.vtkPolyDataMapper()
    edgeMapper.SetInputData(self.lastUSContours)
    
    if self.usActor is not None:
      self.viewer3D.interactor.Disable()
      self.viewer3D.planeWidgets[0].GetDefaultRenderer().RemoveActor(self.usActor)
      self.viewer3D.interactor.Enable()
      self.usActor = None
    
    # Add contours in 3D space (misaligned)
    self.usActor = vtk.vtkActor()
    self.usActor.SetMapper(edgeMapper)
    prop = self.usActor.GetProperty()
    renderLinesAsTubes(prop)
    prop.SetPointSize(4)
    prop.SetLineWidth(3)

    # US contours move opposite of CT contours (was .GetInverse)
    self.usActor.SetUserTransform(self.misAlignment)
    self.viewer3D.planeWidgets[0].GetDefaultRenderer().AddActor(self.usActor)

    # Add overlay to 2D ultrasound
    self.viewUS[1].AddOverlay(contours)
    self.btnSeg.setEnabled(True)
    self.Render()

  def onRegClicked(self):
    print("Registration")
    if self.lastUSContours is not None:
      self.btnReg.setEnabled(False)
      self.viewUS[1].RemoveOverlay()
      
      # Callback for displaying segmentation
      self.regServer.ready.connect(self.updateRegistration)
      
      dummy = vtk.vtkTransform()
      dummy.PostMultiply()
      dummy.DeepCopy(self.misAlignment)

#     This goes crazy
#      dummy = vtk.vtkTransform()
#      dummy.SetMatrix(self.misAlignment.GetMatrix())
#      dummy.PostMultiply()

      
      print("MIS")
      print(dummy.GetMatrix())
      # No need it is already copied
      self.regServer.execute.emit(self.lastUSContours, dummy, self.appendFilter)
      
      self.Render()
    
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
    for i in range(self.stackCT.count()):
      if self.stackCT.widget(i):
        self.stackCT.widget(i).viewer.SetColorWindow(window)
        self.stackCT.widget(i).viewer.SetColorLevel(level)
        self.stackCT.widget(i).viewer.Render()

    # Set window
    for i in range(len(self.viewUS)):
      self.viewUS[i].viewer.SetColorWindow(120.0)
      self.viewUS[i].viewer.SetColorLevel(160.5)
      self.viewUS[i].viewer.Render()
      
        
  def setup(self):
    self.setupUi(self)
    self.setupMenu()
    style = QCommonStyle()
    self.btnUpAzimuth.setIcon(style.standardIcon(QStyle.SP_ArrowUp))
    self.btnDownAzimuth.setIcon(style.standardIcon(QStyle.SP_ArrowDown))
    self.btnRightAzimuth.setIcon(style.standardIcon(QStyle.SP_ArrowForward))
    self.btnLeftAzimuth.setIcon(style.standardIcon(QStyle.SP_ArrowBack))
    self.btnResetAzimuth.setIcon(style.standardIcon(QStyle.SP_BrowserStop))
    
    self.btnUpElevation.setIcon(style.standardIcon(QStyle.SP_ArrowUp))
    self.btnDownElevation.setIcon(style.standardIcon(QStyle.SP_ArrowDown))
    self.btnRightElevation.setIcon(style.standardIcon(QStyle.SP_ArrowForward))
    self.btnLeftElevation.setIcon(style.standardIcon(QStyle.SP_ArrowBack))
    self.btnResetElevation.setIcon(style.standardIcon(QStyle.SP_BrowserStop))

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
    self.viewer3D = Viewer3D(self, showOrientation=True,
                             showPlaneTextActors=False)
    self.viewer3D.AddPlaneCornerButtons()

    self.layout3D.setContentsMargins(0, 0, 0, 0)
    self.layout3D.addWidget(self.viewer3D)

    # Setup CT viewer
    self.stackCT = Viewer2DStacked(self)
    self.layoutCT.setContentsMargins(0, 0, 0, 0)
    self.layoutCT.insertWidget(0,self.stackCT)

    # Setup US views
    self.viewUS = []
    self.viewUS.append(Viewer2D(self, 1))
    self.viewUS.append(Viewer2D(self, 2))

    # Make all views share the same cursor object
    for i in range(2):
      self.viewUS[i].viewer.SetResliceCursor(self.viewUS[0].viewer.GetResliceCursor())

    # Make them all share the same color map.
    for i in range(2):
      self.viewUS[i].viewer.SetLookupTable(self.viewUS[0].viewer.GetLookupTable())
      
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
    for i in range(self.stackCT.count()):
      self.stackCT.widget(i).show()
      self.stackCT.widget(i).viewer.GetImageActor().SetVisibility(False)

    # Show widgets but hide non-existing data
    for i in range(len(self.viewUS)):
      self.viewUS[i].show()
      self.viewUS[i].viewer.GetImageActor().SetVisibility(False)

    self.layoutUS0.setContentsMargins(0,0,0,0)
    self.layoutUS0.insertWidget(0, self.viewUS[0])
    self.layoutUS1.setContentsMargins(0,0,0,0)
    self.layoutUS1.insertWidget(0, self.viewUS[1])
      
  def onLoadClicked(self, fileType):
    mySettings = QSettings()
    fileDir = mySettings.value(self.DEFAULT_DIR_KEY)
    if fileDir is None:
      fileDir = os.path.dirname(__file__)
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileDialog = QFileDialog()
    fileDialog.setDirectory(fileDir)


    defaultFile = os.path.join(fileDir, defaultFiles[fileType])
    
    fileName, _ = \
      fileDialog.getOpenFileName(self,
                                 "QFileDialog.getOpenFileName()",
                                 defaultFile, "All Files (*);"
                                 "MHD Files (*.mhd);"
                                 "VTP Files (*.vtp)",
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
        self.loadSurface(fileName, index=0)
      elif (info.completeSuffix() == "vtp") and fileType == 2:
        self.loadSurface(fileName, index=1)
      elif (info.completeSuffix() == "mhd") and fileType == 3:
        self.loadUSFile(fileName)

  def loadSurface(self, fileName, index=0):
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(fileName)
    reader.Update()

    # Take the largest connected component
    connectFilter = vtk.vtkPolyDataConnectivityFilter()
    connectFilter.SetInputConnection(reader.GetOutputPort())
    connectFilter.SetExtractionModeToLargestRegion()
    connectFilter.Update()

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(connectFilter.GetOutputPort())

    # 3D viewer

    # Mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())

    # Actor for vessels
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()

    
    if index == 0:
      # Veins
      prop.SetColor(vtk.vtkColor3d(hexCol("#517487"))) # 25% lighter
    else:
      # Liver
      prop.SetColor(vtk.vtkColor3d(hexCol("#873927")))

    # Assign actor to the renderer
    prop.SetOpacity(0.35)
    self.viewer3D.planeWidgets[0].GetDefaultRenderer().AddActor(actor)
    
    # 2D Views
    polyData = normals.GetOutput()
    
    self.appendFilter.AddInputData(polyData)
    self.appendFilter.Update()
    
    # TODO: Make this work if read before US
    for i in range(self.stackCT.count()):
      self.stackCT.widget(i).InitializeContours(self.appendFilter,color=pink)

    for i in range(len(self.viewUS)):
      self.viewUS[i].InitializeContours(self.appendFilter)
      # TODO: Assign instead product of two identity matrices
      self.viewUS[i].SetTransform(self.alignment)

    self.Render()

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

    self.ResetUSViews()
    self.SetUSResliceMode(1) # Oblique
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
      self.viewUS[i].viewer.GetInteractorStyle().AddObserver(vtk.vtkCommand.WindowLevelEvent, self.cb1.onWindowLevelChanged)
      self.viewUS[i].viewer.GetInteractorStyle().AddObserver('EndWindowLevelEvent', self.cb1.onEndWindowLevelChanged)


      
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
  # Hack to load stuff on startup
  if len(sys.argv) > 1:
    mySettings = QSettings()
    fileDir = mySettings.value(main_window.DEFAULT_DIR_KEY)
    main_window.loadFile(os.path.join(fileDir,defaultFiles[0])) # CT
    main_window.loadSurface(os.path.join(fileDir,defaultFiles[1]),0)  # Vessels
    if int(sys.argv[1]) == 1:
      main_window.loadUSFile(os.path.join(fileDir,defaultFiles[3])) # US
    elif int(sys.argv[1]) == 2:
      main_window.loadUSFile(os.path.join(fileDir,defaultFiles[5])) # White
    else:
      main_window.loadUSFile(os.path.join(fileDir,defaultFiles[4])) # NoBound
#    main_window.loadSurface(os.path.join(fileDir,defaultFiles[2]),1) # Surface
  
  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
