import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import black

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame

from vtkUtils import renderLinesAsTubes

class Viewer3D(QFrame):
  def __init__(self, parent, iDim=0):
    super(Viewer3D, self).__init__(parent)
    self.buttonSize = 40.0
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

    axesActor = vtk.vtkAxesActor()
    self.axes = vtk.vtkOrientationMarkerWidget()
    self.axes.SetOrientationMarker( axesActor)
    self.axes.SetInteractor( self.interactor )
    self.axes.SetViewport( 0.8, 0.0, 1.0, 0.2)
    #self.planeWidget[0].GetDefaultRenderer().AddActor(axesActor)
    self.axes.EnabledOn()
    self.axes.InteractiveOn()

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

      prop = pw.GetTextProperty()
      prop.SetColor(black)
      
      pw.Modified()
      self.planeWidgets.append(pw)

  def AddPlaneCornerButtons(self):
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

      renderer = self.renderer
      # Reposition buttons
      for i in range(len(self.buttonWidgets)):
        buttonRepresentation = self.buttonWidgets[i].GetRepresentation()
        bds = [0]*6
        sz = self.buttonSize
        bds[0] = upperRight.GetComputedDisplayValue(renderer)[0] - (i+1)*sz
        bds[1] = bds[0] + sz
        bds[2] = upperRight.GetComputedDisplayValue(renderer)[1] - sz
        bds[3] = bds[2] + sz
        bds[4] = bds[5] = 0.0
      
        # Scale to 1, default is .5
        buttonRepresentation.SetPlaceFactor(1)
        buttonRepresentation.PlaceWidget(bds)

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
        
