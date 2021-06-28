import vtk
import sys

def CreateCross(sz):
  # Create a vtkPoints object and store the points in it
  pts = vtk.vtkPoints()
  pts.InsertNextPoint(-sz / 2, 0, 0)
  pts.InsertNextPoint(sz / 2, 0, 0)
  pts.InsertNextPoint(0, -sz / 2, 0)
  pts.InsertNextPoint(0, sz / 2, 0)

  # Setup the colors array
  color = [ 255, 128, 0 ]
  colors = vtk.vtkUnsignedCharArray()
  colors.SetNumberOfComponents(3)
  colors.SetName("Colors")

  # Add the colors we created to the colors array
  colors.InsertNextValue(color[0])
  colors.InsertNextValue(color[1])
  colors.InsertNextValue(color[2])

  colors.InsertNextValue(color[0])
  colors.InsertNextValue(color[1])
  colors.InsertNextValue(color[2])

  # Create the first line
  line0 = vtk.vtkLine()
  line0.GetPointIds().SetId(0, 0)
  line0.GetPointIds().SetId(1, 1)

  # Create the second line
  line1 = vtk.vtkLine()
  line1.GetPointIds().SetId(0, 2)
  line1.GetPointIds().SetId(1, 3)

  # Create a cell array to store the lines in and add the lines to it
  lines = vtk.vtkCellArray()
  lines.InsertNextCell(line0)
  lines.InsertNextCell(line1)

  # Create a polydata to store everything in
  linesPolyData = vtk.vtkPolyData()
  # Add the points to the dataset
  linesPolyData.SetPoints(pts)
  # Add the lines to the dataset
  linesPolyData.SetLines(lines)
  # Color the lines
  linesPolyData.GetCellData().SetScalars(colors)
  return linesPolyData


reader = vtk.vtkPNGReader()
fileName = './fullhead15.png'
if not reader.CanReadFile(fileName):
  sys.exit(-1)
reader.SetFileName(fileName)
reader.Update()
imageData = reader.GetOutput()

# Stupid cross as overlay
bounds = imageData.GetBounds()
imageSz = (bounds[1] - bounds[0], bounds[3] - bounds[2])
imageCenter = imageData.GetCenter()
_max = max(imageSz[0], imageSz[1])
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(CreateCross(_max / 10.0))
global _Cross
_Cross = vtk.vtkActor()
_Cross.GetProperty().SetLineWidth(5)
_Cross.SetPosition(imageCenter[0], imageCenter[1], imageCenter[2])
_Cross.SetMapper(mapper)


# Create a greyscale lookup table
table = vtk.vtkLookupTable()
table.SetRange(0, 2000) # image intensity range
table.SetValueRange(0.0, 1.0) # from black to white
table.SetSaturationRange(0.0, 0.0) # no color saturation
table.SetRampToLinear()
table.Build()

# Map the image through the lookup table
color = vtk.vtkImageMapToColors()
color.SetLookupTable(table)
color.SetInputConnection(reader.GetOutputPort())


global renderWindow
renderWindow = vtk.vtkRenderWindow()
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

global renderer
renderer = vtk.vtkRenderer()
renderWindow.AddRenderer(renderer)

imageActor = vtk.vtkImageActor()
imageActor.GetMapper().SetInputConnection(color.GetOutputPort())

renderer.SetBackground(0.2, 0.3, 0.4)
renderer.AddActor(imageActor)
renderer.ResetCamera()

def cbLeftButtonPressEvt(obj, ev):
  # Won't work
  global renderWindow
  global renderer
  global _Cross
  print('left button')
  if type(obj) == vtk.vtkInteractorStyleImage:
    mousePosition = obj.GetInteractor().GetLastEventPosition()
    _picker = vtk.vtkWorldPointPicker()
    _picker.Pick(mousePosition[0], mousePosition[1], 0.0, renderer)

    pickPosition = _picker.GetPickPosition()
    _Cross.SetPosition(pickPosition[0],
                       pickPosition[1],
                       pickPosition[2])
    renderWindow.Render()

def cbCameraModifiedEvt(obj, ev):
  global _CameraOverlay
  print('camera modified')
  _CameraOverlay.ShallowCopy(obj)


interactorStyleImage = vtk.vtkInteractorStyleImage()
renderWindow.GetInteractor().SetInteractorStyle(interactorStyleImage)
interactorStyleImage.SetDefaultRenderer(renderer)
interactorStyleImage.AddObserver("LeftButtonPressEvent", cbLeftButtonPressEvt)

renderWindow.SetNumberOfLayers(2)
renderOverlay = vtk.vtkRenderer()
renderOverlay.SetLayer(1)
renderOverlay.SetInteractive(0)
renderWindow.AddRenderer(renderOverlay)
renderOverlay.AddActor(_Cross)
global _CameraOverlay
_CameraOverlay = renderOverlay.GetActiveCamera()
_CameraOverlay.ShallowCopy(renderer.GetActiveCamera())

cam = renderer.GetActiveCamera()
cam.AddObserver("ModifiedEvent", cbCameraModifiedEvt)

renderWindow.Render()
renderWindowInteractor.Start()
