import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.colors import black

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame

from vtkUtils import renderLinesAsTubes

# TODO: Add text on plane widgets
#       Update titles on 2D widgets
#       Corner cube

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

class Viewer3D(QFrame):
  def __init__(self, parent, iDim=0, showOrientation=True, showPlaneTextActors=True):
    super(Viewer3D, self).__init__(parent)
    self.showOrientation = showOrientation
    self.showPlaneTextActors = showPlaneTextActors
    self.buttonSize = 40.0
    self.interactor = QVTKRenderWindowInteractor(self)
    self.renderer = vtk.vtkRenderer()
    self.renderer.SetBackground(245.0/255.0,
                                245.0/255.0,
                                245.0/255.0)
    self.renderer.SetBackground2(170.0/255.0,
                                 170.0/255.0,
                                 170.0/255.0)
    self.renderer.GradientBackgroundOn()
    
    self.interactor.GetRenderWindow().AddRenderer(self.renderer)

    self.planeWidgets = []
    self.SetupPlaneWidgets()

    layout = QHBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(self.interactor)
    self.setLayout(layout)
    self.buttonWidgets = []
    self.planeTextActors = []
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

    if self.showOrientation:
      self.AddOrientationWidget(version=1)

    if self.showPlaneTextActors:
      # Add plane text actors
      spacing = reader.GetOutput().GetSpacing()
      imageSize = (spacing[0]*imageDims[0],
                   spacing[1]*imageDims[1],
                   spacing[2]*imageDims[2])
      self.planeTextActors = self.AddTextToPlanes(imageSize,scale0=imageSize[0]/30.0)
      
      ren = self.planeWidgets[0].GetDefaultRenderer()
      for i in range(len(self.planeTextActors)):
        self.planeTextActors[i].SetUserMatrix(self.planeWidgets[i % 3].GetResliceAxes())
        ren.AddViewProp(self.planeTextActors[i])

  def AddOrientationWidget(self, version=0):
    # Corner widget
    if version == 0:
      axesActor = vtk.vtkAxesActor()
      self.axes = vtk.vtkOrientationMarkerWidget()
      self.axes.SetOrientationMarker( axesActor)
      self.axes.SetInteractor( self.interactor )
      self.axes.SetViewport( 0.8, 0.0, 1.0, 0.2)
      self.axes.EnabledOn()
      self.axes.InteractiveOn()
    else:
      colors = vtk.vtkNamedColors()
      xyzLabels = ['X', 'Y', 'Z']
      scale = (1.5, 1.5, 1.5)
      axes2 = MakeCubeActor(scale, xyzLabels, colors)
      self.om2 = vtk.vtkOrientationMarkerWidget()
      self.om2.SetOrientationMarker(axes2)
      # Position lower right in the viewport.
      self.om2.SetInteractor(self.interactor)
      self.om2.SetViewport(0.75, 0, 1.0, 0.25)
      self.om2.EnabledOn()
      self.om2.InteractiveOn()
      
  def AddTextToPlanes(self, imageSize, scale0=15.0):
    # Size is in [mm]
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
    bounds = textActor5.GetBounds()
    # possible bug here, why not 3 - 2 and imageSize[2]
    print(bounds)
    textActor5.AddPosition(-margin+imageSize[0]+bounds[1], bounds[3]-bounds[2], -0.5)
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
    bounds = textActor6.GetBounds()
    textActor6.AddPosition(-margin+imageSize[0]+bounds[1], bounds[3]-bounds[2], -0.5) # Last is out of plane
    textActors.append(textActor6)
    
    return textActors
    
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
          if len(self.planeWidgets) > 0:
            self.planeTextActors[index].SetVisibility(False)
            self.planeTextActors[(index+3) % 6].SetVisibility(False)
          self.planeWidgets[index].Off()
        else:
          self.planeWidgets[index].On()
          if len(self.planeWidgets) > 0:
            self.planeTextActors[index].SetVisibility(True)
            self.planeTextActors[(index+3) % 6].SetVisibility(True)
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
        
