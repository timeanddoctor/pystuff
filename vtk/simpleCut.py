import os
import socket
import vtk
import numpy as np

# TODO: Look in reslice.py and compute location of origin in 2D coordinates

def CreateOutline9076(color = (255, 99, 71), depth = 80.0, resolution=10):
  """
  Create outline for the 9076 probe. The outline is contained in the XZ-plane
  """

  # Avoid multiple generations
  if CreateOutline9076.output is not None and  CreateOutline9076.depth == depth:
    print("reused outline")
    return CreateOutline9076.output

  nElements = 144
  pitch = 0.2101
  roc = 50.006
  height = 5.0

  azR = roc
  azArcLength = pitch * (nElements - 1.0)
  azSegment = azArcLength / azR
  dAz = azSegment / (nElements - 1.0)

  az = dAz * (np.r_[0:nElements] - 0.5*(nElements - 1.0))

  az0 = az[0] - 0.5*dAz
  azN = az[nElements-1] + 0.5*dAz

  # Create first arc
  arc0 = vtk.vtkArcSource()
  arc0.SetCenter(0, -azR, 0)
  arc0.SetPoint1(azR*np.sin(az0), azR*np.cos(az0) - azR,0)
  arc0.SetPoint2(azR*np.sin(azN), azR*np.cos(azN) - azR,0)
  arc0.SetResolution( resolution )
  arc0.Update()

  arcData0 = arc0.GetOutput()

  # Create second arc
  arc1 = vtk.vtkArcSource()
  arc1.SetCenter(0, -azR, 0)
  arc1.SetPoint1((azR+depth)*np.sin(azN), (azR+depth)*np.cos(azN) - azR, 0)
  arc1.SetPoint2((azR+depth)*np.sin(az0), (azR+depth)*np.cos(az0) - azR, 0)
  arc1.SetResolution( resolution )
  arc1.Update()

  arcData1 = arc1.GetOutput()

  # Resulting poly data
  linesPolyData = vtk.vtkPolyData()
  lines = vtk.vtkCellArray()
  points = vtk.vtkPoints()

  # Iterate through points and and create new lines
  arcData0.GetLines().InitTraversal()
  idList = vtk.vtkIdList()
  while arcData0.GetLines().GetNextCell(idList):
    pointId = idList.GetId(0)
    points.InsertNextPoint(arcData0.GetPoint(pointId))
    for i in range(1, idList.GetNumberOfIds()):
      pointId = idList.GetId(i)
      points.InsertNextPoint(arcData0.GetPoint(pointId))
      line = vtk.vtkLine()
      line.GetPointIds().SetId(0,i-1)
      line.GetPointIds().SetId(1,i) # last i value is 10=resolution
      lines.InsertNextCell(line)

  # i = resolution
  arcData1.GetLines().InitTraversal()
  idList = vtk.vtkIdList()
  while arcData1.GetLines().GetNextCell(idList):
    pointId = idList.GetId(0)
    points.InsertNextPoint(arcData1.GetPoint(pointId))
    # Line from 1st arc to second arc
    line = vtk.vtkLine()
    line.GetPointIds().SetId(0,i)
    j = 0
    line.GetPointIds().SetId(1, i+1+j)
    lines.InsertNextCell(line)
    for j in range(1, idList.GetNumberOfIds()):
      pointId = idList.GetId(j)
      points.InsertNextPoint(arcData1.GetPoint(pointId))
      line = vtk.vtkLine()
      line.GetPointIds().SetId(0,i+j-1+1)
      line.GetPointIds().SetId(1,i+j+1)
      lines.InsertNextCell(line)

  # Insert one extra line joining the two arcs
  line = vtk.vtkLine()
  line.GetPointIds().SetId(0,i+j+1)
  line.GetPointIds().SetId(1,0)
  lines.InsertNextCell(line)

  linesPolyData.SetPoints(points)
  linesPolyData.SetLines(lines)

  # Create polyline(s) from line segments. There will be
  # two due to the the ordering
  cutStrips = vtk.vtkStripper()
  cutStrips.SetInputData(linesPolyData)
  cutStrips.Update()

  # Transform points forward such arcs have center in (0,0,0)
  transform = vtk.vtkTransform()
  transform.PostMultiply()
  transform.Translate(0.0, roc, 0.0)
  transform.Update()

  transformPolyDataFilter = vtk.vtkTransformPolyDataFilter()
  transformPolyDataFilter.SetInputConnection(cutStrips.GetOutputPort())
  transformPolyDataFilter.SetTransform(transform)
  transformPolyDataFilter.Update()
  outline = transformPolyDataFilter.GetOutput()

  # Color the lines
  colors = vtk.vtkUnsignedCharArray()
  colors.SetNumberOfComponents(3)
  for i in range(outline.GetNumberOfCells()):
    colors.InsertNextTypedTuple(color)

  outline.GetCellData().SetScalars(colors)
  CreateOutline9076.depth = depth
  CreateOutline9076.output = outline
  return CreateOutline9076.output
CreateOutline9076.output = None
CreateOutline9076.depth = 0.0

from vtkUtils import renderLinesAsTubes, AxesToTransform

global lastNormal
global lastAxis1
global outlineActor

if os.name == 'posix':
  fileDir = "/home/jmh/github/fis/data/Abdomen"
elif socket.gethostname() == 's1551':
  fileDir = "e:/analogic/fis/data/Abdomen"
else:
  fileDir = "c:/github/fis/data/Abdomen"

surfName = 'Liver_3D_Fast_Marching_Closed.vtp'
volName =  'VesselVolume.mhd'

def hexCol(s):
  if isinstance(s,str):
    if "#" in s:
      s = s.lstrip("#")
    return tuple(int(s[i : i + 2], 16)/255.0 for i in (0, 2, 4))
  return None

initialMovement = True

def loadSurface(fname):
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
  normals.Update()

  pd = normals.GetOutput()
  com = vtk.vtkCenterOfMass()
  com.SetInputData(pd)
  com.SetUseScalarsAsWeights(False)
  com.Update()
  center = com.GetCenter()

  # Mapper
  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputConnection(normals.GetOutputPort())

  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  prop = actor.GetProperty()
  prop.SetColor(vtk.vtkColor3d(hexCol("#873927")))

  # Assign actor to the renderer
  prop.SetOpacity(0.35)
  return actor, center

def CreateOutline(depth=80.0, transform=None):
  # Create planeWidget aligned with sector outline
  outline = CreateOutline9076(depth=depth)

  bounds = outline.GetBounds()
  planeWidget = vtk.vtkPlaneWidget()

  origin = (bounds[0], bounds[2], 0.0)
  point1 = (bounds[1], bounds[2], 0.0)
  point2 = (bounds[0], bounds[3], 0.0)

  if initialMovement and transform is not None:
    origin = transform.TransformPoint(origin)
    point1 = transform.TransformPoint(point1)
    point2 = transform.TransformPoint(point2)

  planeWidget.SetOrigin(origin)
  planeWidget.SetPoint1(point1)
  planeWidget.SetPoint2(point2)
  prop = planeWidget.GetPlaneProperty()
  prop.SetColor( .2, .8, 0.1 )
  renderLinesAsTubes(prop)
  prop = planeWidget.GetHandleProperty()
  prop.SetColor(0, .4, .7 )
  prop.SetLineWidth( 1.5 )#//Set plane lineweight
  renderLinesAsTubes(prop)

  planeWidget.Modified()
  planeWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent, Callback, 1.0)

  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputData(outline)
  actor = vtk.vtkActor()
  actor.SetMapper(mapper)

  # Origin used for book-keeping
  #center = (0.0, 0.0, 0.5*(bounds[4]+ bounds[5]))
  center = (0.0, 0.5*(bounds[2]+ bounds[3]), 0.0)

  if initialMovement and transform is not None:
    actor.SetUserTransform(transform)
    center = transform.TransformPoint(center)
  actor.SetOrigin(center)

  prop = actor.GetProperty()
  prop.SetLineWidth(4)
  renderLinesAsTubes(prop)
  return actor, planeWidget

def Callback(obj, ev):
  global lastNormal
  global lastAxis1
  global outlineActor

  normal0 = lastNormal
  first0  = lastAxis1
  origin0 = outlineActor.GetOrigin()

  # New values
  normal1 = np.array(obj.GetNormal())
  first1 = np.array(obj.GetPoint1()) - np.array(obj.GetOrigin())
  origin1 = obj.GetCenter()

  trans = AxesToTransform(normal0, first0, origin0,
                          normal1, first1, origin1)
  if outlineActor.GetUserTransform() is not None:
    outlineActor.GetUserTransform().Concatenate(trans)
  else:
    transform = vtk.vtkTransform()
    transform.SetMatrix(trans)
    transform.PostMultiply()
    outlineActor.SetUserTransform(transform)

  # Only for book keeping
  outlineActor.SetOrigin(obj.GetCenter()) # Not modified by SetUserTransform
  outlineActor.Modified()
  # Update last axes
  lastAxis1[0] = first1[0]
  lastAxis1[1] = first1[1]
  lastAxis1[2] = first1[2]

  lastNormal = (normal1[0], normal1[1], normal1[2])


fileName = os.path.join(fileDir, surfName)
actor, com = loadSurface(fileName)

renderer0 = vtk.vtkRenderer()
renderer0.SetViewport(0., 0., 0.5, 1.)


renderer1 = vtk.vtkRenderer()
renderer1.SetViewport(0.5, 0., 1., 1.)

renderWindow = vtk.vtkRenderWindow()
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

camera = vtk.vtkCamera()

renderWindow.AddRenderer(renderer1)
renderWindow.AddRenderer(renderer0) # This the active renderer


imageStyle = vtk.vtkInteractorStyleImage()
imageStyle.SetDefaultRenderer(renderer1)

switchStyle = vtk.vtkInteractorStyleSwitch()
switchStyle.SetDefaultRenderer(renderer0)

renderWindowInteractor.SetInteractorStyle(switchStyle)

def MouseMoveCallback(obj, event):
  pos = obj.GetEventPosition()
  bla = renderWindowInteractor.FindPokedRenderer(pos[0], pos[1])
  if (bla == renderer0):
    if (renderWindowInteractor.GetInteractorStyle() != switchStyle):
      renderWindowInteractor.SetInteractorStyle(switchStyle)
      print('updated')
  else:
    if (renderWindowInteractor.GetInteractorStyle() != imageStyle):
      renderWindowInteractor.SetInteractorStyle(imageStyle)
      print('updated')

renderWindowInteractor.AddObserver("MouseMoveEvent", MouseMoveCallback)
#switchStyle.AddObserver("MouseMoveEvent", MouseMoveCallback)


renderer0.SetBackground(.9, 0.9, 0.9)
renderer1.SetBackground(.9, 0.9, 0.9)

renderer0.AddActor(actor)

cutTransform = vtk.vtkTransform()
cutTransform.PostMultiply()
cutTransform.Translate(com[0], com[1], com[2])
cutTransform.Update()

outlineActor, planeWidget = CreateOutline(depth=80.0, transform=cutTransform)

planeWidget.SetInteractor(renderWindowInteractor)

renderer0.AddActor(outlineActor)

planeWidget.Modified()
planeWidget.On()

lastNormal = planeWidget.GetNormal()
lastAxis1 = vtk.vtkVector3d()

vtk.vtkMath.Subtract(planeWidget.GetPoint1(),
                     planeWidget.GetOrigin(),
                     lastAxis1)

renderer0.SetActiveCamera(camera)
renderer0.ResetCamera()

camera1 = vtk.vtkCamera()

renderer1.SetActiveCamera(camera1)
renderer1.ResetCamera()

# Image slice data
fileName = os.path.join(fileDir, volName)
reader = vtk.vtkMetaImageReader()
reader.SetFileName(fileName)
reader.Update()

reslice = vtk.vtkImageReslice()
reslice.SetInputConnection(reader.GetOutputPort())
reslice.SetOutputDimensionality(2)
reslice.SetResliceAxes(cutTransform.GetMatrix())
reslice.SetInterpolationModeToLinear()
#reslice.SetAutoCropOutput(True)
#reslice.SetOutputExtent(-10, 10, -10, 10, 0, 0)


# Create a greyscale lookup table
table = vtk.vtkLookupTable()
table.SetRange(0, 1000) # image intensity range
table.SetValueRange(0.0, 1.0) # from black to white
table.SetSaturationRange(0.0, 0.0) # no color saturation
table.SetRampToLinear()
table.Build()

# Map the image through the lookup table
color = vtk.vtkImageMapToColors()
color.SetLookupTable(table)
color.SetInputConnection(reslice.GetOutputPort())

# Display the image
imActor = vtk.vtkImageActor()
imActor.GetMapper().SetInputConnection(color.GetOutputPort())

renderer1.AddActor(imActor)

renderer0.ResetCamera()
renderer1.ResetCamera()

# The one that is visible in TrialVTK/Registration/python
mat4x4 = np.array([[0.9824507428729312,   -0.028608856565971154, 0.1843151408713164, -221.425151769367],
                   [0.18431514087131629,   0.3004711475787132,  -0.935812491003576,  -325.6553959586223],
                   [-0.028608856565971223, 0.9533617481306448,   0.3004711475787133, -547.1574253306663],
                   [0,  0,      0,      1]])
sliceCenter = np.r_[-31.317285034663634,       -174.62449255285645,    -193.39018826551072]

# Show slice using vtkImageActor
# Use lasso stencil

# Two interactors
#https://discourse.vtk.org/t/possible-to-use-different-interaction-styles-across-viewports/1926




renderWindow.Render()
renderWindowInteractor.Start()
