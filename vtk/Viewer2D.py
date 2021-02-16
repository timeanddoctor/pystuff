# Clean-up
# Stack with 2 views
# World coordinates of click
# Transformation
# Registration

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import red, yellow

from collections import deque

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame
from PyQt5.QtCore import pyqtSignal

from vtkUtils import renderLinesAsTubes, AxesToTransform

import math

    
class Viewer2D(QFrame):
  def __init__(self, parent, iDim=0):
    super(Viewer2D, self).__init__(parent)
    interactor = QVTKRenderWindowInteractor(self) # This is a QWidget
    self.contourActor = None # Actor for contours
    self.overlay   = None    # Actor for segmentation contours
    self.wrongContourActor = None
    self.iDim = iDim      # Slice dimensions
    self.lastSize = (0,0) # Used for corner button
    self.buttonWidget = None
    self.cornerAnnotation = None
    self.buttonSize = 40.0
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

  def AddOverlay(self, polyData):
    # TODO: Add node to position in 3D
    self.viewer.GetRenderWindow().GetInteractor().Disable()
    if self.overlay is not None:
      self.viewer.GetRenderer().RemoveActor(self.overlay)
      self.overlay = None
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polyData)
    self.overlay = vtk.vtkActor()
    self.overlay.SetMapper(mapper)
    prop = self.overlay.GetProperty()
    renderLinesAsTubes(prop)
    prop.SetColor(yellow)
    self.viewer.GetRenderer().AddActor(self.overlay)
    self.viewer.GetRenderWindow().GetInteractor().Enable()
  def RemoveOverlay(self):
    if self.overlay is not None:
      self.viewer.GetRenderWindow().GetInteractor().Disable()
      self.viewer.GetRenderer().RemoveActor(self.overlay)
      self.overlay = None
      self.viewer.GetRenderWindow().GetInteractor().Enable()
      
  def ShowHideCursor(self, visible=False):
    for i in range(3):
      prop = self.viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(i)
      if visible:
        prop.SetOpacity(1.0)
      else:
        prop.SetOpacity(0.0)
  def GetScreenTransform(self):
    """
    Get transform from origin to window slice plane
    """
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
    
    # Get distance from plane to screen
    cursor = self.viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursor()
    normal = cursor.GetPlane(self.iDim).GetNormal()
    origin = cursor.GetPlane(self.iDim).GetOrigin()

    PQ = vtk.vtkVector3d()
    vtk.vtkMath.Subtract(origin, lowerLeft, PQ)
    dist = vtk.vtkMath.Dot(normal, PQ)

    trans = vtk.vtkTransform()
    trans.Translate(dist*normal[0],dist*normal[1],dist*normal[2])
    origin1 = trans.TransformPoint(lowerLeft)

    normal0 = (0.0,0.0,1.0)
    first0 =  (1.0,0.0,0.0)
    origin0 = (0.0,0.0,0.0)
    
    transMat = AxesToTransform(normal0, first0, origin0,
                               normal1, first1, origin1)
    
    return transMat
    
  def GetScreenImage(self, useOffScreenBuffer=True):
    image = None
    if useOffScreenBuffer:
      image = self.readOffScrenBuffer()
      image.SetOrigin(0,0,0)
    else:
      image = self.readOnScreenBuffer()

    renderer = self.viewer.GetRenderer()      
    coordinate = vtk.vtkCoordinate()
    coordinate.SetCoordinateSystemToNormalizedDisplay()

    dims = image.GetDimensions()
    coordinate.SetValue(1.0, 0.0) # Lower right
    lowerRight = coordinate.GetComputedWorldValue(renderer)
    coordinate.SetValue(0.0, 0.0) # Lower left
    lowerLeft = coordinate.GetComputedWorldValue(renderer)
    dx = vtk.vtkMath.Distance2BetweenPoints(
      lowerRight,
      lowerLeft)
    dx = math.sqrt(dx) / dims[0]
    
    coordinate.SetValue(0.0, 1.0) # Upper left
    dy = vtk.vtkMath.Distance2BetweenPoints(
      coordinate.GetComputedWorldValue(renderer),
      lowerLeft)
    dy = math.sqrt(dy) / dims[1]
    image.SetSpacing(dx,dy,0.0)
    image.Modified()
  
    # Adjust origin
    cursor = self.viewer.GetResliceCursor()
    normal = cursor.GetPlane(self.iDim).GetNormal()
    origin = cursor.GetPlane(self.iDim).GetOrigin()
    PQ = vtk.vtkVector3d()
    vtk.vtkMath.Subtract(origin, lowerLeft, PQ)
    # Signed distance to plane
    dist = vtk.vtkMath.Dot(normal, PQ)

    # If VTK 9.0 add origin and orientation
    trans = vtk.vtkTransform()
    trans.Translate(dist*normal[0],dist*normal[1],dist*normal[2])
    image.SetOrigin(trans.TransformPoint(lowerLeft))
    image.Modified()
    # TODO: Compute orientation for VTK 9.0
    # image.SetOrientation(mat)
    return image
      
  # Get transformation to screen view
  def readOffScrenBuffer(self, hideCursor=True,
                         hideContours=True,
                         hideAnnotations=True):
    renderWindow = self.viewer.GetRenderWindow()
    if not renderWindow.SetUseOffScreenBuffers(True):
      glRenderWindow.DebugOn()
      glRenderWindow.SetUseOffScreenBuffers(True)
      glRenderWindow.DebugOff()
      print("Unable create a hardware frame buffer, the graphic board or driver can be too old")
      sys.exit(-1)

    # Hide cursor
    if hideCursor:
      self.ShowHideCursor(False)
    if hideAnnotations:
      self.ShowHideAnnotations(False)
    if hideContours:
      self.ShowHideContours(False)

    windowToImageFilter = vtk.vtkWindowToImageFilter()
    windowToImageFilter.SetInput(renderWindow)
    windowToImageFilter.Update() # Issues a render call
  
    renderWindow.SetUseOffScreenBuffers(False)

    self.ShowHideCursor(True)
    self.ShowHideAnnotations(True)
    self.ShowHideContours(True)
    return windowToImageFilter.GetOutput()
        
  def readOnScreenBuffer(self, hideCursor=True,
                         hideContours=True,
                         hideAnnotations=True):
    # Read on-screen buffer
    renderWindow = self.viewer.GetRenderWindow()

    oldSB = renderWindow.GetSwapBuffers()
    renderWindow.SwapBuffersOff()
    
    if hideCursor:
      self.ShowHideCursor(False)
    if hideAnnotations:
      self.ShowHideAnnotations(False)
    if hideContours:
      self.ShowHideContours(False)
    
    windowToImageFilter = vtk.vtkWindowToImageFilter()
    windowToImageFilter.SetInput(renderWindow)

    windowToImageFilter.SetScale(1)
    windowToImageFilter.SetInputBufferTypeToRGBA()
    
    windowToImageFilter.ReadFrontBufferOff()
    windowToImageFilter.Update() # Issues a render on input
    
    renderWindow.SetSwapBuffers(oldSB)
    renderWindow.SwapBuffersOn()

    self.ShowHideCursor(True)
    self.ShowHideAnnotations(True)
    self.ShowHideContours(True)
    return windowToImageFilter.GetOutput()

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
      sz = self.buttonSize
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

  def ShowHideAnnotations(self, show=True):
    if self.cornerAnnotation is not None:
      self.cornerAnnotation.SetVisibility(show)
  def SetInputData(self, data):
    self.viewer.SetInputData(data)
    # Corner annotation, can use <slice>, <slice_pos>, <window_level>
    self.cornerAnnotation = vtk.vtkCornerAnnotation()
    self.cornerAnnotation.SetLinearFontScaleFactor(2)
    self.cornerAnnotation.SetNonlinearFontScaleFactor(1)
    self.cornerAnnotation.SetMaximumFontSize(20)
    self.cornerAnnotation.SetText(vtk.vtkCornerAnnotation.UpperLeft, {2:'Axial',
                                                                 0:'Sagittal',
                                                                 1:'Coronal'}[self.iDim])
    prop = self.cornerAnnotation.GetTextProperty()
    prop.BoldOn()
    color = deque((1,0,0))
    color.rotate(self.iDim)
    self.cornerAnnotation.GetTextProperty().SetColor(tuple(color))
    self.cornerAnnotation.SetImageActor(self.viewer.GetImageActor())
    
    self.cornerAnnotation.SetWindowLevel(self.viewer.GetWindowLevel())
    self.viewer.GetRenderer().AddViewProp(self.cornerAnnotation)

  def InitializeContours(self, data, color=yellow):
    # Disable interactor
    self.viewer.GetRenderWindow().GetInteractor().Disable()

    if self.contourActor is not None:
      self.viewer.GetRenderer().RemoveActor(self.contourActor)
      self.contourActor = None

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
          
    self.contourActor = vtk.vtkActor()
    self.contourActor.SetMapper(edgeMapper)
    prop = self.contourActor.GetProperty()
    renderLinesAsTubes(prop)
    prop.SetColor(color) # If Scalars are extracted - they turn green

    # Move in front of image
    transform = vtk.vtkTransform()
    transform.Translate(normal)
    self.contourActor.SetUserTransform(transform)

    # Add actor to renderer
    self.viewer.GetRenderer().AddViewProp(self.contourActor)

    # Enable interactor again
    self.viewer.GetRenderWindow().GetInteractor().Enable()

  def ShowHideContours(self, show):
    if self.contourActor is not None:
      self.contourActor.SetVisibility(show)
  def SetResliceCursor(self, cursor):
    self.viewer.SetResliceCursor(cursor)

  def GetResliceCursor(self):
    return self.viewer.GetResliceCursor()

  def UpdateContours(self, transform=None):
    if self.contourActor is not None:
      RCW = self.viewer.GetResliceCursorWidget()    
      ps = RCW.GetResliceCursorRepresentation().GetPlaneSource()
      normal = ps.GetNormal()
      origin = ps.GetOrigin()
      # If transform -> modify origin and normal

      self.plane.SetOrigin(origin)
      self.plane.SetNormal(normal)

      # if transform apply inverse transform to contours
      
      # Move in front of image (z-buffer)
      transform = vtk.vtkTransform()
      transform.Translate(normal) # TODO: Add 'EndEvent' on transform filter
      self.contourActor.SetUserTransform(transform)
    
  def Start(self):
    self.interactor.Initialize()
    self.interactor.Start()

from PyQt5.QtWidgets import QStackedWidget
    
class Viewer2DStacked(QStackedWidget):
  resliceAxesChanged = pyqtSignal()
  def __init__(self, parent=None, axes=[0,1,2]):
    super(Viewer2DStacked, self).__init__(parent)
    # Create signal
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
      self.widget(i).buttonWidget.AddObserver(vtk.vtkCommand.StateChangedEvent, self.btnViewChangeClicked)
    
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
  def btnViewChangeClicked(self, widget, event):
    index = self.currentIndex()
    index = index + 1
    index = index % 3
    self.setCurrentIndex(index)
    # TODO: Consider hiding other actors
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
    
