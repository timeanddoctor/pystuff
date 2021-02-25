#!/bin/env python3
import os
import sys
from collections import deque

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import red, yellow

from PyQt5.uic import loadUiType
from PyQt5.QtCore import Qt, QObject, QCoreApplication,\
  QSettings, QFileInfo
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout,\
  QSplitter, QFrame, QSpacerItem, QPushButton,\
  QAction, QFileDialog, QApplication,  QSizePolicy

ui_file = os.path.join(os.path.dirname(__file__), 'ContourViewer.ui')

ui, QMainWindow = loadUiType(ui_file)

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


# TODO: Rotate
#  S 90 degrees around Z
#  R 180 degrees X
#  I 90 degrees Z
#  P -90 degrees Y
#  A -90 degrees Y
def MakeCubeActor(scale, xyzLabels, colors):
  """
  :param scale: Sets the scale and direction of the axes.
  :param xyzLabels: Labels for the axes.
  :param colors: Used to set the colors of the cube faces.
  :return: The combined axes and annotated cube prop.

  TODO: Move to VTK utils
  """
  # We are combining a vtk.vtkAxesActor and a vtk.vtkAnnotatedCubeActor
  # into a vtk.vtkPropAssembly
  cube = MakeAnnotatedCubeActor(colors)
  axes = MakeAxesActor(scale, xyzLabels)

  # Combine orientation markers into one with an assembly.
  assembly = vtk.vtkPropAssembly()
  assembly.AddPart(axes)
  assembly.AddPart(cube)
  return assembly
      

def MakeAnnotatedCubeActor(colors):
  """
  :param colors: Used to determine the cube color.
  :return: The annotated cube actor.
  """
  # A cube with labeled faces.
  cube = vtk.vtkAnnotatedCubeActor()
  # Interchange R and L for RAS, this is LPS
  # Interchange A and P for RAS

  cube.SetXPlusFaceText('L')  # Right
  cube.SetXMinusFaceText('R')  # Left
  cube.SetYPlusFaceText('P')  # Anterior
  cube.SetYMinusFaceText('A')  # Posterior

  cube.SetZPlusFaceText('S')  # Superior/Cranial
  cube.SetZMinusFaceText('I')  # Inferior/Caudal
  cube.SetFaceTextScale(0.5)
  cube.GetCubeProperty().SetColor(colors.GetColor3d('Gainsboro'))

  cube.GetTextEdgesProperty().SetColor(colors.GetColor3d('LightSlateGray'))

  # Change the vector text colors.
  cube.GetXPlusFaceProperty().SetColor(colors.GetColor3d('Tomato'))
  cube.GetXMinusFaceProperty().SetColor(colors.GetColor3d('Tomato'))

  cube.GetYPlusFaceProperty().SetColor(colors.GetColor3d( 'SeaGreen'   ))
  cube.GetYMinusFaceProperty().SetColor(colors.GetColor3d('SeaGreen'   ))
  cube.GetZPlusFaceProperty().SetColor(colors.GetColor3d( 'DeepSkyBlue'))
  cube.GetZMinusFaceProperty().SetColor(colors.GetColor3d('DeepSkyBlue'))

  cube.SetZFaceTextRotation(90)
  
  return cube

def MakeAxesActor(scale, xyzLabels):
    """
    :param scale: Sets the scale and direction of the axes.
    :param xyzLabels: Labels for the axes.
    :return: The axes actor.
    """
    axes = vtk.vtkAxesActor()
    axes.SetScale(scale)
    axes.SetShaftTypeToCylinder()
    axes.SetXAxisLabelText(xyzLabels[0])
    axes.SetYAxisLabelText(xyzLabels[1])
    axes.SetZAxisLabelText(xyzLabels[2])
    axes.SetCylinderRadius(0.5 * axes.GetCylinderRadius())
    axes.SetConeRadius(1.025 * axes.GetConeRadius())
    axes.SetSphereRadius(1.5 * axes.GetSphereRadius())
    tprop = axes.GetXAxisCaptionActor2D().GetCaptionTextProperty()
    tprop.ItalicOn()
    tprop.ShadowOn()
    tprop.SetFontFamilyToTimes()
    # Use the same text properties on the other two axes.
    axes.GetYAxisCaptionActor2D().GetCaptionTextProperty().ShallowCopy(tprop)
    axes.GetZAxisCaptionActor2D().GetCaptionTextProperty().ShallowCopy(tprop)
    return axes

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
        main_window.vtk_widgets[i].UpdateContour()
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
    self.DEFAULT_DIR_KEY = "ContourViewer.py"
    self.planeTextActors = []
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
    prop.SetColor(vtk.vtkColor3d(hexCol("#517487"))) # 25% lighter

    # Assign actor to the renderer
    prop.SetOpacity(0.35)
    self.planeWidget[0].GetDefaultRenderer().AddActor(self.vessels)

    for i in range(3):
      self.vtk_widgets[i].InitializeContour(self.vesselNormals)
    self.Render()
    
  def loadFile(self, fileName):
    # Load VTK Meta Image
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(fileName)
    reader.Update()
    imageDims = reader.GetOutput().GetDimensions()

    ren = self.planeWidget[0].GetDefaultRenderer()
    for planeTextActor in self.planeTextActors:
      ren.RemoveViewProp(planeTextActor)
    
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
      
    self.om2.EnabledOn()
    self.om2.InteractiveOn()

    # Enable 2D viewers
    for i in range(3):
      self.vtk_widgets[i].viewer.GetRenderer().ResetCamera()
      self.vtk_widgets[i].viewer.GetInteractor().EnableRenderOn()

    # Enable interactors
    for i in range(3):
      #self.vtk_widgets[i].interactor.Enable()
      self.vtk_widgets[i].viewer.GetInteractor().Enable()

    # Enable 3D rendering
    self.vtk_widgets[3].EnableRenderOn()
    # Reset camera for the renderer - otherwise it is set using dummy data
    self.planeWidget[0].GetDefaultRenderer().ResetCamera()

    # Update 3D
    self.ResetViews()
    self.SetResliceMode(1)

    # TODO: Scale font size to size of data and positioning also
    spacing = reader.GetOutput().GetSpacing()

    imageSize = (spacing[0]*imageDims[0],
                 spacing[1]*imageDims[1],

                 spacing[2]*imageDims[2])
    
    self.planeTextActors = self.AddTextToPlanes(imageSize,scale0=imageSize[0]/30.0)
    
    ren = self.planeWidget[0].GetDefaultRenderer()
    for i in range(len(self.planeTextActors)):
      self.planeTextActors[i].SetUserMatrix(self.planeWidget[i % 3].GetResliceAxes())
      ren.AddViewProp(self.planeTextActors[i])
      
  def AddTextToPlanes(self, imageSize, scale0=15.0):
    # Size is in [mm]
    # TODO: Positioning depends on size of labels and imageSize (FIX)
    # Right now, they are hardcoded
    textActors = list()
    scale = [scale0, scale0, scale0] # Consider scaling to fraction of data

    margin = scale0*0.66
    
    text1 = vtk.vtkVectorText()
    text1.SetText("Sagittal\nPlane\n\nLeft")
    text1.Modified()
    trnf1 = vtk.vtkTransform()
    tpdPlane1 = vtk.vtkTransformPolyDataFilter()
    tpdPlane1.SetTransform(trnf1)
    tpdPlane1.SetInputConnection(text1.GetOutputPort())
    textMapper1 = vtk.vtkPolyDataMapper()
    textMapper1.SetInputConnection(tpdPlane1.GetOutputPort())
    textActor1 = vtk.vtkActor()
    textActor1.SetMapper(textMapper1)
    textActor1.SetScale(scale)
    textActor1.GetProperty().SetColor(1,0,0)
    bounds = textActor1.GetBounds()
    textActor1.AddPosition(margin, bounds[3]-bounds[2], 0.5) # Last is out of plane
    textActors.append(textActor1)

    text2 = vtk.vtkVectorText()
    text2.SetText("Coronal\nPlane\n\nAnterior")
    trnf2 = vtk.vtkTransform()
    tpdPlane2 = vtk.vtkTransformPolyDataFilter()
    tpdPlane2.SetTransform(trnf2)
    tpdPlane2.SetInputConnection(text2.GetOutputPort())
    textMapper2 = vtk.vtkPolyDataMapper()
    textMapper2.SetInputConnection(tpdPlane2.GetOutputPort())
    textActor2 = vtk.vtkActor()
    textActor2.SetMapper(textMapper2)
    textActor2.SetScale(scale)
    textActor2.GetProperty().SetColor(0,1,0)
    bounds = textActor2.GetBounds()
    textActor2.AddPosition(margin, bounds[3]-bounds[2], 0.5) # Last is out of plane
    textActors.append(textActor2)

    text3 = vtk.vtkVectorText()
    text3.SetText("Axial\nPlane\n\nSuperior\nCranial")
    trnf3 = vtk.vtkTransform()
    tpdPlane3 = vtk.vtkTransformPolyDataFilter()
    tpdPlane3.SetTransform(trnf3)
    tpdPlane3.SetInputConnection(text3.GetOutputPort())
    textMapper3 = vtk.vtkPolyDataMapper()
    textMapper3.SetInputConnection(tpdPlane3.GetOutputPort())
    textActor3 = vtk.vtkActor()
    textActor3.SetMapper(textMapper3)
    textActor3.SetScale(scale)
    textActor3.GetProperty().SetColor(0,0,1)
    bounds = textActor3.GetBounds()
    textActor3.AddPosition(margin, bounds[3]-bounds[2], 0.5) # Last is out of plane
    textActors.append(textActor3)

    text4 = vtk.vtkVectorText()
    text4.SetText("Sagittal\nPlane\n\nRight")
    trnf4 = vtk.vtkTransform()
    trnf4.RotateY(180)
    tpdPlane4 = vtk.vtkTransformPolyDataFilter()
    tpdPlane4.SetTransform(trnf4)
    tpdPlane4.SetInputConnection(text4.GetOutputPort())
    textMapper4 = vtk.vtkPolyDataMapper()
    textMapper4.SetInputConnection(tpdPlane4.GetOutputPort())
    textActor4 = vtk.vtkActor()
    textActor4.SetMapper(textMapper4)
    textActor4.SetScale(scale)
    textActor4.GetProperty().SetColor(1,0,0)
    #textActor4.AddPosition(10.0, 30.0, -0.5) # Last is out of plane (only X)
    bounds = textActor4.GetBounds()
    
    textActor4.AddPosition(-margin+imageSize[1]+bounds[1], bounds[3]-bounds[2], -0.5) # use for no flip (dep on width)
    textActors.append(textActor4)
      
    text5 = vtk.vtkVectorText()
    text5.SetText("Coronal\nPlane\n\nPosterior")
    trnf5 = vtk.vtkTransform()
    trnf5.RotateY(180)
    tpdPlane5 = vtk.vtkTransformPolyDataFilter()
    tpdPlane5.SetTransform(trnf5)
    tpdPlane5.SetInputConnection(text5.GetOutputPort())
    textMapper5 = vtk.vtkPolyDataMapper()
    textMapper5.SetInputConnection(tpdPlane5.GetOutputPort())
    textActor5 = vtk.vtkActor()
    textActor5.SetMapper(textMapper5)
    textActor5.SetScale(scale)
    textActor5.GetProperty().SetColor(0,1,0)
    #textActor5.AddPosition(20.0, 80.0, -0.5) # Last is out of plane
    bounds = textActor5.GetBounds()
    # possible bug here
    textActor5.AddPosition(-margin+imageSize[0]+bounds[1], bounds[1]-bounds[0], -0.5)
    textActors.append(textActor5)
      
    text6 = vtk.vtkVectorText()
    text6.SetText("Axial\nPlane\n\nInferior\n(Caudal)")
    trnf6 = vtk.vtkTransform()
    trnf6.RotateY(180)
    tpdPlane6 = vtk.vtkTransformPolyDataFilter()
    tpdPlane6.SetTransform(trnf6)
    tpdPlane6.SetInputConnection(text6.GetOutputPort())
    textMapper6 = vtk.vtkPolyDataMapper()
    textMapper6.SetInputConnection(tpdPlane6.GetOutputPort())
    textActor6 = vtk.vtkActor()
    textActor6.SetMapper(textMapper6)
    textActor6.SetScale(scale)
    textActor6.GetProperty().SetColor(0,0,1)
    # textActor6.AddPosition(100.0, 100.0, -0.5) # Original
    bounds = textActor6.GetBounds()
    textActor6.AddPosition(-margin+imageSize[0]+bounds[1], bounds[3]-bounds[2], -0.5) # Last is out of plane
    textActors.append(textActor6)
    
    return textActors

    
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

    # Create cube, Right Anterior Superior
    colors = vtk.vtkNamedColors()
    xyzLabels = ['X', 'Y', 'Z']
    scale = (1.5, 1.5, 1.5)
    axes2 = MakeCubeActor(scale, xyzLabels, colors)
    self.om2 = vtk.vtkOrientationMarkerWidget()
    self.om2.SetOrientationMarker(axes2)
    # Position lower right in the viewport.
    self.om2.SetInteractor(self.vtk_widgets[3])
    self.om2.SetViewport(0.75, 0, 1.0, 0.25)
    
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
    vert_layout.addItem(verticalSpacer)
    vert_layout.addItem(horz_layout1)
    self.frame.setLayout(vert_layout)
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
  def SetInputData(self, data):
    self.viewer.SetInputData(data)
    # Corner annotation, can use <slice>, <slice_pos>, <window_level>
    cornerAnnotation = vtk.vtkCornerAnnotation()
    cornerAnnotation.SetLinearFontScaleFactor(2)
    cornerAnnotation.SetNonlinearFontScaleFactor(1)
    cornerAnnotation.SetMaximumFontSize(20)
    cornerAnnotation.SetText(vtk.vtkCornerAnnotation.UpperLeft,
                             {2:'Axial Superior',
                              0:'Sagittal Left',
                              1:'Coronal Anterior'}[self.iDim])
    prop = cornerAnnotation.GetTextProperty()
    prop.BoldOn()
    color = deque((1,0,0))
    color.rotate(self.iDim)
    cornerAnnotation.GetTextProperty().SetColor(tuple(color))
    cornerAnnotation.SetImageActor(self.viewer.GetImageActor())
    
    cornerAnnotation.SetWindowLevel(self.viewer.GetWindowLevel())
    self.viewer.GetRenderer().AddViewProp(cornerAnnotation)
  def InitializeContour(self, data):
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
    cutStrips = vtk.vtkStripper()
    cutStrips.SetInputConnection(cutEdges.GetOutputPort())
    cutStrips.Update()

    edgeMapper = vtk.vtkPolyDataMapper()
    edgeMapper.SetInputConnection(cutStrips.GetOutputPort())
          
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
  def UpdateContour(self):
    if self.edgeActor is not None:
      RCW = self.viewer.GetResliceCursorWidget()    
      ps = RCW.GetResliceCursorRepresentation().GetPlaneSource()
      self.plane.SetOrigin(ps.GetOrigin())
      normal = ps.GetNormal()
      self.plane.SetNormal(normal)
      # Move in front of image (z-buffer)
      transform = vtk.vtkTransform()
      transform.PostMultiply()
      transform.Translate(normal) # TODO: Add 'EndEvent' on transform filter
      self.edgeActor.SetUserTransform(transform)
    
  def start(self):
    self.interactor.Initialize()
    self.interactor.Start()

if __name__ == '__main__':
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
  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
