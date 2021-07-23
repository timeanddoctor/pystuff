# TODO: Save image


import os
import socket
import vtk
import numpy as np

# TODO: Look in reslice.py and compute location of origin in 2D coordinates

from vtkUtils import CreateCross

def CreateSurface9076():
  # Coordinate transformations

  # Return cached value if present
  if CreateSurface9076.output is not None:
    print('reused STL surface')
    return CreateSurface9076.output
  
  # Sensor from STL
  sensorFromSTL = vtk.vtkTransform()
  sensorFromSTL.PostMultiply()
  sensorFromSTL.RotateZ(180.0)
  sensorFromSTL.Translate(109.27152 + 29.7296 - 5.41,
                        29.69371 - 2.2,
                        75.52397 - 2.144)
  sensorFromSTL.Modified()
  sensorFromSTL.Inverse()
  sensorFromSTL.Update()

  # Array actual from Array nominal  
  actFromNom = vtk.vtkTransform() 
  actFromNom.PostMultiply()
  actFromNom.RotateZ(np.rad2deg(-0.04712388))
  actFromNom.RotateY(np.rad2deg(0.00942477))
  actFromNom.Identity() # Not used since ideal probe
  actFromNom.Update()

  # Array nominal from probe reference  
  nomFromRef = vtk.vtkTransform()
  nomFromRef.PostMultiply()
  nomFromRef.RotateY(np.rad2deg(-0.05061454))
  nomFromRef.Translate(19.35, -0.62, -46.09)
  nomFromRef.Update()

  # Probe reference from sensor nominal  
  refFromSensor = vtk.vtkTransform() 
  refFromSensor.PostMultiply()
  refFromSensor.Translate(-3.33, 1.59, 1.7) # original
  refFromSensor.Translate(0.0, -3.86, 0.0) # Shifted half-height of xdx + enclosing
  refFromSensor.Inverse()
  refFromSensor.Update()
  
  # Actual array from sensor nominal
  actFromSensor = vtk.vtkTransform()
  actFromSensor.Identity()
  actFromSensor.Concatenate(refFromSensor)
  actFromSensor.Concatenate(nomFromRef)
  actFromSensor.Concatenate(actFromNom)
  actFromSensor.Update()
  
  # To Ultrasound from Array actual (based on ProbeCenterY value from
  # OEM "QUERY:B_TRANS_IMAGE_CALIB;").
  usFromActual = vtk.vtkTransform()
  usFromActual.PostMultiply()
  usFromActual.Translate(-47.8225, 0.0, 0.0) # original
  usFromActual.Translate(0.0, 0.0, 45.0) # JEM offset fra OEM (must be)
  usFromActual.Update()

  # Final transformation from STL to XZ-plane
  finalTransform = vtk.vtkTransform()
  finalTransform.PostMultiply()
  finalTransform.Identity()
  finalTransform.Concatenate(sensorFromSTL)
  finalTransform.Concatenate(actFromSensor)
  finalTransform.Concatenate(usFromActual)

  # Rotate around X 
  finalTransform.RotateX(-90)
  finalTransform.Translate(0.0, 50.006, 0.0)
  
  reader = vtk.vtkSTLReader()
  file_name = './9076.vtp'
  reader = vtk.vtkXMLPolyDataReader()
  reader.SetFileName(file_name)
  reader.Update()

  tfpoly = vtk.vtkTransformPolyDataFilter()
  tfpoly.SetInputConnection(reader.GetOutputPort())
  tfpoly.SetTransform(finalTransform)
  tfpoly.Update()
  CreateSurface9076.output = tfpoly.GetOutput()
  return CreateSurface9076.output
CreateSurface9076.output = None

def CreateAssembly9076():
  if CreateAssembly9076.output is not None:
    return CreateAssembly9076.output
  
  outline = CreateOutline9076()

  # Works - convert lines to polygons
  cutPoly = vtk.vtkPolyData()
  cutPoly.SetPoints(outline.GetPoints())
  cutPoly.SetPolys(outline.GetLines())

  # Triangle filter is robust enough to ignore the duplicate point at
  # the beginning and end of the polygons and triangulate them.
  cutTriangles = vtk.vtkTriangleFilter()
  cutTriangles.SetInputData(cutPoly)
  cutMapper = vtk.vtkPolyDataMapper()

  cutMapper.SetInputConnection(cutTriangles.GetOutputPort())

  cutActor = vtk.vtkActor()
  cutActor.SetMapper(cutMapper)
  cutActor.GetProperty().SetColor(peacock) # Intersecting plane
  cutActor.GetProperty().SetOpacity(.3)

  probeSurface = CreateSurface9076()

  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputData(probeSurface)

  probeActor = vtk.vtkActor()
  probeActor.SetMapper(mapper)
  if vtk.VTK_VERSION > '9.0.0':
    prop = probeActor.GetProperty()
    prop.SetInterpolationToPBR()
    prop.SetMetallic(0.5)
    prop.SetRoughness(0.4)

  mapper0 = vtk.vtkPolyDataMapper()
  mapper0.SetInputData(outline)

  outLineActor = vtk.vtkActor()
  outLineActor.SetMapper(mapper0)
  outLineActor.GetProperty().SetLineWidth(4)

    
  assemblyActor = vtk.vtkAssembly()
  assemblyActor.AddPart(cutActor)
  assemblyActor.AddPart(probeActor)
  assemblyActor.AddPart(outLineActor)
  CreateAssembly9076.output = assemblyActor
  return CreateAssembly9076.output
CreateAssembly9076.output = None  

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
#volName =  'VesselVolume.mhd'
volName =  'VesselVolumeUncompressed.mhd'
#volName = 'CT-Abdomen.mhd'
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
  #prop.SetColor( .2, .8, 0.1 )
  renderLinesAsTubes(prop)
  prop = planeWidget.GetHandleProperty()
  #prop.SetColor(0, .4, .7 )
  #prop.SetLineWidth( 1.5 )#//Set plane lineweight
  renderLinesAsTubes(prop)

  planeWidget.Modified()
  planeWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent, Callback, 1.0)

  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputData(outline)
  actor0 = vtk.vtkActor()
  actor0.SetMapper(mapper)

  # Origin used for book-keeping
  #center = (0.0, 0.0, 0.5*(bounds[4]+ bounds[5]))
  center = (0.0, 0.5*(bounds[2]+ bounds[3]), 0.0)

  prop = actor0.GetProperty()
  prop.SetLineWidth(4)
  renderLinesAsTubes(prop)


  probeSurface = CreateSurface9076()
  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputData(probeSurface)

  probeActor = vtk.vtkActor()
  probeActor.SetMapper(mapper)
  if vtk.VTK_VERSION > '9.0.0':
    prop = probeActor.GetProperty()
    prop.SetInterpolationToPBR()
    prop.SetMetallic(0.5)
    prop.SetRoughness(0.4)

  #actor = actor0


  
  assemblyActor = vtk.vtkAssembly()
  #assemblyActor.AddPart(cutActor)
  assemblyActor.AddPart(probeActor)
  #assemblyActor.AddPart(outLineActor)
  assemblyActor.AddPart(actor0)

  if initialMovement and transform is not None:
    assemblyActor.SetUserTransform(transform)
    center = transform.TransformPoint(center)
  assemblyActor.SetOrigin(center)
  
  return assemblyActor, planeWidget, outline

def Callback(obj, ev):
  global renderWindow
  global lastNormal
  global lastAxis1
  global outlineActor
  global originActor
  global origin2DActor

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

  # Show where (0,0,0) in global coordinates
  transformedOrigin = outlineActor.GetUserTransform().TransformPoint(0,0,0)

  if 0:
    roiStencil.SetInformationInput(reslice.GetOutput())
    roiStencil.Update()

    stencil.SetInputConnection(reslice.GetOutputPort())
    stencil.SetBackgroundValue(0.0)
    stencil.SetStencilConnection(roiStencil.GetOutputPort())

  renderWindow.Render()

fileName = os.path.join(fileDir, surfName)
actor, com = loadSurface(fileName)

renderer0 = vtk.vtkRenderer()
renderer0.SetViewport(0., 0., 0.5, 1.)


renderer1 = vtk.vtkRenderer()
renderer1.SetViewport(0.5, 0., 1., 1.)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(CreateCross(20.0))
global _Cross
_Cross = vtk.vtkActor()
_Cross.GetProperty().SetLineWidth(5)
_Cross.SetPosition(0.0, 50.006, 0.0)
_Cross.SetMapper(mapper)

global renderWindow
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

outlineActor, planeWidget, outline = CreateOutline(depth=80.0, transform=cutTransform)

planeWidget.SetInteractor(renderWindowInteractor)

renderer0.AddActor(outlineActor)

planeWidget.Modified()
planeWidget.On()

global originActor
ss = vtk.vtkSphereSource()
ss.SetRadius(3.0)
ss.SetThetaResolution(10)
ss.SetPhiResolution(10)
ss.SetCenter(0.0, 50.006, 0.0)
ss.Modified()
ssm = vtk.vtkPolyDataMapper()
ssm.SetInputConnection(ss.GetOutputPort())
originActor = vtk.vtkActor()
originActor.SetMapper(ssm)
originActor.SetUserTransform(cutTransform)
renderer0.AddActor(originActor)

lastNormal = planeWidget.GetNormal()
lastAxis1 = vtk.vtkVector3d()

vtk.vtkMath.Subtract(planeWidget.GetPoint1(),
                     planeWidget.GetOrigin(),
                     lastAxis1)

camera.SetViewUp(0.0, -1.0, 0.0)
renderer0.SetActiveCamera(camera)
renderer0.ResetCamera()

camera1 = vtk.vtkCamera()
camera1.SetViewUp(0.0, -1.0, 0.0)
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
reslice.SetAutoCropOutput(True)

testPoints = vtk.vtkPoints()
testPoints.DeepCopy(outline.GetPoints())

# TEST
bounds = testPoints.GetBounds()
dxy = 0.25
ny = int((np.ceil(bounds[3]) - np.floor(bounds[2])) / dxy)
nx = int((np.ceil(bounds[1]) - np.floor(bounds[0])) / dxy)
x0 = np.floor(bounds[0])
y0 = np.floor(bounds[2])
reslice.SetOutputExtent(0, nx, 0, ny, 0, 0)
reslice.SetOutputSpacing(dxy, dxy, dxy)
reslice.SetOutputOrigin(x0, y0, 0.0)

reslice.Update()

# Needed to provide spacing, origin, and whole extent
reslice.GetOutput()

# Create a greyscale lookup table
table = vtk.vtkLookupTable()
table.SetRange(0, 100) # image intensity range
table.SetValueRange(0.0, 1.0) # from black to white
table.SetSaturationRange(0.0, 0.0) # no color saturation
table.SetRampToLinear()
table.Build()

# Map the image through the lookup table
color = vtk.vtkImageMapToColors()
color.SetLookupTable(table)
color.SetInputConnection(reslice.GetOutputPort())

roiStencil = vtk.vtkLassoStencilSource()
roiStencil.SetShapeToPolygon()
roiStencil.SetPoints(testPoints)
roiStencil.SetInformationInput(reslice.GetOutput())
roiStencil.Update()

stencil = vtk.vtkImageStencil()
stencil.SetInputConnection(reslice.GetOutputPort())
stencil.SetBackgroundValue(0.0)
stencil.SetStencilConnection(roiStencil.GetOutputPort())
stencil.ReverseStencilOff()
stencil.Update()

# Create a greyscale lookup table
table1 = vtk.vtkLookupTable()
table1.SetRange(0, 200) # image intensity range
table1.SetValueRange(0.0, 1.0) # from black to white
table1.SetSaturationRange(0.0, 0.0) # no color saturation
table1.SetRampToLinear()
table1.Build()

# Map the image through the lookup table
color1 = vtk.vtkImageMapToColors()
color1.SetLookupTable(table1)
color1.SetInputConnection(stencil.GetOutputPort())

imageActor7 = vtk.vtkImageActor()
imageActor7.GetMapper().SetInputConnection(color1.GetOutputPort())

# Display the sliced image
imActor = vtk.vtkImageActor()
imActor.GetMapper().SetInputConnection(color.GetOutputPort())

#renderer1.AddActor(imActor)

# TESTME
renderer1.AddActor(imageActor7) # Works but no updates

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


def cbCameraModifiedEvt(obj, ev):
  print('camera')
  # Synchronize camera for overlay (renderer2) and renderer1
  global camera2
  camera2.ShallowCopy(obj)

#

renderer2 = vtk.vtkRenderer()
renderWindow.SetNumberOfLayers(2)
renderer2.SetViewport(0.5, 0., 1., 1.)
renderer2.SetLayer(1)
renderer2.SetInteractive(0)
renderWindow.AddRenderer(renderer2)

global camera2
camera2 = renderer2.GetActiveCamera()
camera2.ShallowCopy(renderer1.GetActiveCamera())

renderer2.AddActor(_Cross)


cam = renderer1.GetActiveCamera()
cam.AddObserver("ModifiedEvent", cbCameraModifiedEvt)


renderWindow.Render()



renderWindowInteractor.Start()
