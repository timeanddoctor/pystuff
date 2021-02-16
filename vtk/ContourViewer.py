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
