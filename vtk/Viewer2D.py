# TODO: 1. Viewer2DStacked
#       2. Main using it and 3D (hack)
#       3. 3D widget
#       4. Buttons on stacked widget
#       5. Buttons on 3D widget

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from collections import deque

from PyQt5.QtWidgets import QHBoxLayout, QFrame

from vtkUtils import renderLinesAsTubes

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
    
  def Start(self):
    self.interactor.Initialize()
    self.interactor.Start()

from PyQt5.QtWidgets import QStackedWidget
    
def Viewer2DStacked(QStackedWidget):
  def __init__(self, parent=None):
    super(View2DStacked, self).__init__(parent)
    # Create signal
    #planesModified = pyEvent()
    
    for i in range(3):
      widget = Viewer2D(self, i)
      self.addWidget(widget)

    # Make all views share the same cursor object
    for i in range(3):
      self.widget(i).viewer.SetResliceCursor(self.widget(0).viewer.GetResliceCursor())

    # Cursor representation (anti-alias)
    for i in range(3):
      for j in range(3):
        prop = self.widgets(i).viewer.GetResliceCursorWidget().GetResliceCursorRepresentation().GetResliceCursorActor().GetCenterlineProperty(j)
        renderLinesAsTubes(prop)
    for i in range(3):
      color = [0.0, 0.0, 0.0]
      color[i] = 1
      for j in range(3):
        color[j] = color[j] / 4.0
      self.widget(i).viewer.GetRenderer().SetBackground(color)
      self.widget(i).interactor.Disable()

    # Callbacks
    
    
# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
    
