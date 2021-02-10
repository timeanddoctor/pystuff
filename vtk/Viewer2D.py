# TODO: x. Viewer2DStacked 
#       x. Main using it and 3D (hack)
#       x. 3D widget
#       x. Buttons on stacked widget
#       5. Buttons on 3D widget

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import red, yellow

from collections import deque

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame
from PyQt5.QtCore import pyqtSignal

from vtkUtils import renderLinesAsTubes

class Viewer3D(QFrame):
  def __init__(self, parent, iDim=0):
    super(Viewer3D, self).__init__(parent)
    self.interactor = QVTKRenderWindowInteractor(self)
    self.renderer = vtk.vtkRenderer()
    self.renderer.SetBackground(245.0/255.0,245.0/255.0,245.0/255.0)
    self.renderer.SetBackground2(170.0/255.0,170.0/255.0,170.0/255.0)
    self.renderer.GradientBackgroundOn()
    
    self.interactor.GetRenderWindow().AddRenderer(self.renderer)

    self.planeWidgets = []
    self.SetupPlaneWidgets()

    layout = QHBoxLayout(self)
    layout.setContentsMargins(0,0,0,0)
    layout.addWidget(self.interactor)
    self.setLayout(layout)
    self.buttonWidgets = []
    self.lastSize = (0,0) # Used for corner buttons
  def EnablePlaneWidgets(self, reader):
    imageDims = reader.GetOutput().GetDimensions()
    for i in range(3):
      self.planeWidgets[i].SetInputConnection(reader.GetOutputPort())
      self.planeWidgets[i].SetPlaneOrientation(i)
      self.planeWidgets[i].SetSliceIndex(imageDims[i] // 2)
      self.planeWidgets[i].GetInteractor().Enable()
      self.planeWidgets[i].On()
      self.planeWidgets[i].InteractionOn()

  def Off(self):
    for i in range(len(self.planeWidgets)):
      self.planeWidgets[i].Off()
      
  def SetupPlaneWidgets(self):
    picker = vtk.vtkCellPicker()
    picker.SetTolerance(0.005)
    pwTextureProp = vtk.vtkProperty()
    for i in range(3):
      pw =  vtk.vtkImagePlaneWidget()
      pw.SetInteractor(self.interactor)
      pw.SetPicker(picker)
      pw.RestrictPlaneToVolumeOn()
      color = [0.0, 0.0, 0.0]
      color[i] = 1
      pw.GetPlaneProperty().SetColor(color)
      pw.SetTexturePlaneProperty(pwTextureProp)
      pw.TextureInterpolateOn()
      pw.SetResliceInterpolateToLinear()
      pw.DisplayTextOn()
      pw.SetDefaultRenderer(self.renderer)

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
      self.planeWidgets.append(pw)

  def AddCornerButtons(self):
    # Add corner buttons
    fileName0 = ['./S00.png', './C00.png', './A00.png']
    fileName1 = ['./S01.png', './C01.png', './A01.png']
    for i in range(3):
      reader = vtk.vtkPNGReader()
      reader.SetFileName(fileName0[(i + 1) % 3])
      reader.Update()
      texture0 = reader.GetOutput()
      reader = vtk.vtkPNGReader()
      reader.SetFileName(fileName1[(i + 1) % 3])
      reader.Update()
      texture1 = reader.GetOutput()
      self.AddCornerButton(texture0, texture1)

  def AddCornerButton(self, texture0, texture1):
    """
    Add corner button. TODO: Support callback argument
    """

    # Render to ensure viewport has the right size (it has not)
    buttonRepresentation = vtk.vtkTexturedButtonRepresentation2D()
    buttonRepresentation.SetNumberOfStates(2)
    buttonRepresentation.SetButtonTexture(0, texture0)
    buttonRepresentation.SetButtonTexture(1, texture1)
    buttonWidget = vtk.vtkButtonWidget()
    buttonWidget.SetInteractor(self.interactor)
    buttonWidget.SetRepresentation(buttonRepresentation)
    buttonWidget.AddObserver(vtk.vtkCommand.StateChangedEvent, self.onTogglePlanesClicked)
    buttonWidget.On()
    self.buttonWidgets.append(buttonWidget)

    renWin = self.interactor.GetRenderWindow()
    renWin.AddObserver('ModifiedEvent', self.resizeCallback)

  def dataValid(self):
    return self.planeWidgets[0].GetResliceOutput().GetDimensions() > (0,0,0)

  def onTogglePlanesClicked(self, widget, event):
    # TODO: Find a better way to see if connection is made
    if (self.dataValid()):
      index = -1
      isChecked = widget.GetRepresentation().GetState()
      if (widget == self.buttonWidgets[0]):
        index = 0
      elif (widget == self.buttonWidgets[1]):
        index = 1
      elif (widget == self.buttonWidgets[2]):
        index = 2
      index = (index + 1) % 3
      if (index > -1):
        if isChecked:
          self.planeWidgets[index].Off()
        else:
          self.planeWidgets[index].On()
    return
    
  def Initialize(self):
    self.interactor.Initialize()
    self.interactor.Start()

  def resizeCallback(self, widget, event):
    """
    Callback for repositioning button. Only observe this if
    a button is added
    """
    curSize = widget.GetSize()
    if (curSize != self.lastSize):
      self.lastSize = curSize
    
      upperRight = vtk.vtkCoordinate()
      upperRight.SetCoordinateSystemToNormalizedDisplay()
      upperRight.SetValue(1.0, 1.0)

      renderer = self.renderer # self.planeWidget[0].GetDefaultRenderer()
      for i in range(len(self.buttonWidgets)):
        buttonRepresentation = self.buttonWidgets[i].GetRepresentation()

        bds = [0]*6
        sz = 40.0
        bds[0] = upperRight.GetComputedDisplayValue(renderer)[0] - (i+1)*sz
        bds[1] = bds[0] + sz
        bds[2] = upperRight.GetComputedDisplayValue(renderer)[1] - sz
        bds[3] = bds[2] + sz
        bds[4] = bds[5] = 0.0
      
        # Scale to 1, default is .5
        buttonRepresentation.SetPlaceFactor(1)
        buttonRepresentation.PlaceWidget(bds)
    
class Viewer2D(QFrame):
  def __init__(self, parent, iDim=0):
    super(Viewer2D, self).__init__(parent)
    interactor = QVTKRenderWindowInteractor(self) # This is a QWidget
    self.edgeActor = None # Actor for contours
    self.iDim = iDim      # Slice dimensions
    self.lastSize = (0,0) # Used for corner button
    self.buttonWidget = None 
    layout = QHBoxLayout(self)
    layout.addWidget(interactor)
    layout.setContentsMargins(0, 0, 0, 0)
    self.setLayout(layout)

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
  def Enable(self):
    self.viewer.GetRenderer().ResetCamera()
    self.viewer.GetInteractor().EnableRenderOn()
  def resizeCallback(self, widget, event):
    """
    Callback for repositioning button. Only observe this if
    a button is added
    """
    curSize = widget.GetSize()
    if (curSize != self.lastSize):
      self.lastSize = curSize
    
      upperRight = vtk.vtkCoordinate()
      upperRight.SetCoordinateSystemToNormalizedDisplay()
      upperRight.SetValue(1.0, 1.0)

      renderer = self.viewer.GetRenderer()
      buttonRepresentation = self.buttonWidget.GetRepresentation()

      bds = [0]*6
      sz = 40.0
      bds[0] = upperRight.GetComputedDisplayValue(renderer)[0] - sz
      bds[1] = bds[0] + sz
      bds[2] = upperRight.GetComputedDisplayValue(renderer)[1] - sz
      bds[3] = bds[2] + sz
      bds[4] = bds[5] = 0.0
      
      # Scale to 1, default is .5
      buttonRepresentation.SetPlaceFactor(1)
      buttonRepresentation.PlaceWidget(bds)
    
  def AddCornerButton(self, texture, cb = None):
    """
    Add corner button. TODO: Support callback argument
    """

    # Render to ensure viewport has the right size (it has not)
    buttonRepresentation = vtk.vtkTexturedButtonRepresentation2D()
    buttonRepresentation.SetNumberOfStates(1)
    buttonRepresentation.SetButtonTexture(0, texture)
    self.buttonWidget = vtk.vtkButtonWidget()
    self.buttonWidget.SetInteractor(self.viewer.GetInteractor())
    self.buttonWidget.SetRepresentation(buttonRepresentation)

    self.buttonWidget.On()

    renWin = self.viewer.GetRenderWindow()
    renWin.AddObserver('ModifiedEvent', self.resizeCallback)

  def SetInputData(self, data):
    self.viewer.SetInputData(data)
    # Corner annotation, can use <slice>, <slice_pos>, <window_level>
    cornerAnnotation = vtk.vtkCornerAnnotation()
    cornerAnnotation.SetLinearFontScaleFactor(2)
    cornerAnnotation.SetNonlinearFontScaleFactor(1)
    cornerAnnotation.SetMaximumFontSize(20)
    cornerAnnotation.SetText(vtk.vtkCornerAnnotation.UpperLeft, {2:'Axial',
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
    cutEdges.SetInputConnection(data.GetOutputPort())#main_window.vesselNormals.GetOutputPort())
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
    
  def Start(self):
    self.interactor.Initialize()
    self.interactor.Start()

from PyQt5.QtWidgets import QStackedWidget
    
class Viewer2DStacked(QStackedWidget):
  resliceAxesChanged = pyqtSignal()
  def __init__(self, parent=None, axes=[0,1,2]):
    super(Viewer2DStacked, self).__init__(parent)
    # Create signal
    print(axes)
    #planesModified = pyEvent()
    for i in range(len(axes)):
      widget = Viewer2D(self, axes[i])
      self.addWidget(widget)

    # Add corner buttons
    fileName = ['./S00.png', './C00.png', './A00.png']
    for i in range(self.count()):
      reader = vtk.vtkPNGReader()
      reader.SetFileName(fileName[(axes[i] + 1) % 3])
      reader.Update()
      texture = reader.GetOutput()
      self.widget(i).AddCornerButton(texture)

    # TODO: Add function to 2D view to assign a callback for button
    for i in range(self.count()):
      self.widget(i).buttonWidget.AddObserver(vtk.vtkCommand.StateChangedEvent, self.btnClicked)
    
    # Make all views share the same cursor object
    for i in range(self.count()):
      self.widget(i).viewer.SetResliceCursor(self.widget(0).viewer.GetResliceCursor())

    # Cursor representation (anti-alias)
    for i in range(self.count()):
      for j in range(3):
        prop = self.widget(i).viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(j)
        renderLinesAsTubes(prop)
    for i in range(self.count()):
      color = [0.0, 0.0, 0.0]
      color[axes[i]] = 1
      for j in range(3):
        color[j] = color[j] / 4.0
      self.widget(i).viewer.GetRenderer().SetBackground(color)
      self.widget(i).interactor.Disable()

    # Make them all share the same color map.
    for i in range(self.count()):
      self.widget(i).viewer.SetLookupTable(self.widget(0).viewer.GetLookupTable())
  def close(self):
    for i in range(self.count()):
      self.widget(i).interactor.close()
  def dataValid(self):
    return self.widget(0).viewer.GetInput() is not None
      
  def ShowWidgetHideData(self):
    # Show widgets but hide non-existing data (MOVE TO Stack)
    for i in range(self.count()):
      self.widget(i).show()
      self.widget(i).viewer.GetImageActor().SetVisibility(False)
      
    # Establish callbacks
  def btnClicked(self, widget, event):
    index = self.currentIndex()
    index = index + 1
    index = index % 3
    self.setCurrentIndex(index)
    # Hide other actors
    #if (self.dataValid()):
    #  for i in range(3):
    #    self.widget(i).viewer.GetImageActor().SetVisibility((lambda x: True if x == index else False)(i))
  def Initialize(self):
    for i in range(self.count()):
      self.widget(i).Start()

  def EnableRenderOff(self):
    for i in range(self.count()):
      self.widget(i).viewer.GetInteractor().EnableRenderOff()

  def SetInputData(self, data):
    for i in range(self.count()):
      self.widget(i).SetInputData(data)

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
    
