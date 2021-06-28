import sys
import vtk
import numpy as np

from vtk.util.numpy_support import vtk_to_numpy

""" 
impostor technique to make wide lines look like tubes to the
lighting and depth buffer. For spheres it takes square point sprites
and makes them look like spheres to the lighting and depth buffers. Be
aware that for large meshes, rendering a 12*12 point sprite per vertex
can result in a lot of pixels being drawn when the entire mesh is
shown, so use this power judiciously.
"""

def NumpyToVTK4x4(npArr, vtkMat):
  """
  Hard-coded to 4x4 matrix
  """
  arr = vtk.vtkDoubleArray()
  arr.SetNumberOfValues(16)
  arr.SetVoidArray(vtkMat.GetData(), 16, 4)
  assert(np.shape == (4,4) and np.dtype == np.float64)
  destArr = vtk_to_numpy(arr)
  src = npArr.flatten()
  destArr[:] = src[:]
  

def CloudMeanDist(source, target):
  # Source contains few points, target contains many
  locator = vtk.vtkCellLocator()
  locator.SetDataSet(target)
  locator.SetNumberOfCellsPerBucket(1)
  locator.BuildLocator()

  nPoints = source.GetNumberOfPoints()
  closestp = vtk.vtkPoints()
  closestp.SetNumberOfPoints(nPoints)

  subId = vtk.reference(0)
  dist2 = vtk.reference(0.0)
  cellId = vtk.reference(0) # mutable <-> reference
  outPoint = [0.0, 0.0, 0.0]

  for i in range(nPoints):
    locator.FindClosestPoint(source.GetPoint(i),
                             outPoint,
                             cellId,
                             subId,
                             dist2)
    closestp.SetPoint(i, outPoint)

  totaldist = 0.0
  p1 = [0.0, 0.0, 0.0]
  p2 = [0.0, 0.0, 0.0]

  for i in range(nPoints):
    # RMS
    totaldist = totaldist +\
      vtk.vtkMath.Distance2BetweenPoints(source.GetPoint(i),
                                         closestp.GetPoint(i))
  return np.sqrt(totaldist / nPoints)


def numpyTypeToVTKType(dtype):
  if dtype == np.int8:
    #define VTK_CHAR            2
    return 2
  elif dtype == np.uint8:
    #define VTK_UNSIGNED_CHAR   3
    return 3
  elif dtype == np.int16:
    #define VTK_SHORT           4
    return 4
  elif dtype == np.uint16:
    #define VTK_UNSIGNED_SHORT  5
    return 5
  elif dtype == np.int32:
    #define VTK_INT             6
    return 6
  elif dtype == np.uint32:
    #define VTK_UNSIGNED_INT    7
    return 7
  elif dtype == np.int64:
    #define VTK_LONG            8
    return 8
  elif dtype == np.uint64:
    #define VTK_UNSIGNED_LONG   9
    return 9
  elif dtype == np.float32:
    #define VTK_FLOAT          10
    return 10
  elif dtype == np.float64:
    #define VTK_DOUBLE         11
    return 11
  else:
    raise RuntimeError("type conversion not implemented...")

def toVtkImageData(a):    
  importer = vtk.vtkImageImport()

  #FIXME
  #In all cases I have seen, it is needed to reverse the shape here
  #Does that hold universally, and do we understand why?
  reverseShape = True
   
  importer.SetDataScalarType(numpyTypeToVTKType(a.dtype))
  if reverseShape:
    importer.SetDataExtent(0,a.shape[2]-1,0,a.shape[1]-1,0,a.shape[0]-1)
    importer.SetWholeExtent(0,a.shape[2]-1,0,a.shape[1]-1,0,a.shape[0]-1)
  else:
    importer.SetDataExtent(0,a.shape[0]-1,0,a.shape[1]-1,0,a.shape[2]-1)
    importer.SetWholeExtent(0,a.shape[0]-1,0,a.shape[1]-1,0,a.shape[2]-1)
  importer.SetImportVoidPointer(a)
  importer.Update()
  return importer.GetOutput()
  
def hexCol(s):
  if isinstance(s,str):
    if "#" in s:
      s = s.lstrip("#")
    return tuple(int(s[i : i + 2], 16)/255.0 for i in (0, 2, 4))
  return None

def renderLinesAsTubes(prop):
  prop.SetEdgeVisibility(1)
  prop.SetPointSize(4) # Should be larger than line width
  prop.SetLineWidth(3)
  prop.SetRenderLinesAsTubes(1)
  return prop

def renderPointsAsSpheres(prop):
  # Remember to set VertexColor and EdgeColor
  prop.SetEdgeVisibility(1)
  prop.SetPointSize(6)
  prop.SetLineWidth(3)
  prop.RenderPointsAsSpheres(1)
  prop.SetVertexVisibility(1)

def renderPointsAndLinesAsTubesAndSpheres(prop):
  renderLinesAsTubes(prop)
  renderLinesAsSpheres(prop)

def rotationFromHomogeneous(mat4):
  mat3 = vtk.vtkMatrix3x3()
  for i in range(3):
    for j in range(3):
      mat3.SetElement(i,j,mat4.GetElement(i,j))
  return mat3

def polyInfo(filter):
  """
  Debug information about output from vtkPolyData producing filters
  """
  filter.Update()
  output = filter.GetOutput()
  print("Polydata after: %s" % (filter.GetClassName()))
  print("\tLines: %d" % (output.GetNumberOfLines()))
  print("\tPoints: %d" % (output.GetNumberOfPoints()))
  print("\tCells: %d" % (output.GetNumberOfCells()))
  print("\tPieces: %d" % (output.GetNumberOfPieces()))
  print("\tStrips: %d" % (output.GetNumberOfStrips()))
  print("\tPolys: %d" % (output.GetNumberOfPolys()))
  print("\tVerts: %d" % (output.GetNumberOfVerts()))
  # Do we have normals?
  # .GetOutput().GetPointData().GetArray("Normals")
  # .GetNormals()
  # .GetVectors()

def vtkRotationMovie(renderWindow, filename='c:/test.avi'):
  global degrees
  degrees = 0

  windowToImageFilter = vtk.vtkWindowToImageFilter()
  windowToImageFilter.SetInput(renderWindow)
  windowToImageFilter.SetInputBufferTypeToRGB()
  windowToImageFilter.ReadFrontBufferOff()
  windowToImageFilter.Update()

  #writer = vtk.vtkOggTheoraWriter()
  writer = vtk.vtkAVIWriter()
  writer.SetInputConnection(windowToImageFilter.GetOutputPort())
  writer.SetRate(10) # Not needed for Ogg

  try:
    os.remove(filename)
  except OSError:
    pass
  writer.SetFileName(filename)
  writer.Start()

  timerId = renderWindow.GetInteractor().CreateRepeatingTimer(50)
  def cb(interactor, event):
    global degrees
    step = 5
    if (degrees > 359):
      interactor.DestroyTimer(timerId)
      writer.End()
      return
    interactor.GetRenderWindow().Render()
    cam = interactor.GetRenderWindow().GetRenderers().GetFirstRenderer().GetActiveCamera()
    cam.Azimuth(step)
    cam.OrthogonalizeViewUp()
    windowToImageFilter.Modified()
    writer.Write()
    degrees = degrees + step
  renderWindow.GetInteractor().AddObserver('TimerEvent', cb)
  renderWindow.GetInteractor().Start()

def vtkSubfigs(nrows=1, ncols=1, sharecamera=False):
  renderWindow = vtk.vtkRenderWindow()
  renderers = []
  camera = None
  if sharecamera:
    camera = vtk.vtkCamera()
  for irow in range(nrows):
    for icol in range(ncols):
      renderer = vtk.vtkRenderer()
      renderer.SetViewport(0.0 + icol*1.0/ncols,0.0 + irow*1.0/nrows,
                           (icol+1)*1.0/ncols,(irow+1)*1.0/nrows)
      if camera is not None:
        renderer.SetActiveCamera(camera)
      renderWindow.AddRenderer(renderer)
      renderers.append(renderer)
  return renderWindow, renderers

def hexCol(s):
  if isinstance(s,str):
    if "#" in s:  # hex to rgb
      h = s.lstrip("#")
      rgb255 = list(int(h[i : i + 2], 16) for i in (0, 2, 4))
      rgbh = np.array(rgb255) / 255.0
      return tuple(rgbh)

def AxesToTransform(normal0, first0, origin0,
                    normal1, first1, origin1):
  """
  Generate homegenous transform transforming origin and positive orientation defined by
  (normal0, first0, origin0) into (normal1, first1, origin1)
  """

  vec = vtk.vtkVector3d() # Axis of rotation
  vtk.vtkMath.Cross(normal0, normal1, vec)
  costheta = vtk.vtkMath.Dot(normal1, normal0)
  sintheta = vtk.vtkMath.Norm(vec)
  theta = np.arctan2(sintheta, costheta)

  if sintheta != 0.0:
    vec[0] = vec[0]/sintheta
    vec[1] = vec[1]/sintheta
    vec[2] = vec[2]/sintheta

  # Convert to Quaternion
  costheta = np.cos(0.5*theta)
  sintheta = np.sin(0.5*theta)
  quat0 = vtk.vtkQuaterniond(costheta, vec[0]*sintheta, vec[1]*sintheta, vec[2]*sintheta)

  newFirst = vtk.vtkVector3d()

  rot0 = np.ones((3,3),dtype=np.float)
  vtk.vtkMath.QuaternionToMatrix3x3(quat0, rot0)

  if 1:
    # Can be performed using quaternions
    vtk.vtkMath.Multiply3x3(rot0, first0, newFirst)
  else:
    # Quaternion equivalent of the above line
    quatAxis0 = vtk.vtkQuaterniond(0.0, first0[0],
                                   first0[1],
                                   first0[2])
    quatAxisTmp = vtk.vtkQuaterniond()
    quatAxis1 = vtk.vtkQuaterniond()
    vtk.vtkMath.MultiplyQuaternion(quat0, quatAxis0, quatAxisTmp)
    vtk.vtkMath.MultiplyQuaternion(quatAxisTmp, quat0.Inverse(), quatAxis1)
    newFirst[0] = quatAxis1[1]
    newFirst[1] = quatAxis1[2]
    newFirst[2] = quatAxis1[3]

  # Rotate newFirst into first1
  vec = vtk.vtkVector3d() # Axis of rotation
  vtk.vtkMath.Cross(newFirst, first1, vec)
  costheta = vtk.vtkMath.Dot(first1, newFirst)
  sintheta = vtk.vtkMath.Norm(vec)
  theta = np.arctan2(sintheta, costheta)
  if sintheta != 0.0:
    vec[0] = vec[0]/sintheta
    vec[1] = vec[1]/sintheta
    vec[2] = vec[2]/sintheta

  # Convert to Quaternion
  costheta = np.cos(0.5*theta)
  sintheta = np.sin(0.5*theta)
  quat1 = vtk.vtkQuaterniond(costheta, vec[0]*sintheta, vec[1]*sintheta, vec[2]*sintheta)
  if 0:
    rot1 = np.ones((3,3),dtype=np.float)
    vtk.vtkMath.QuaternionToMatrix3x3(quat1, rot1)
    rot = np.dot(rot1, rot0)
  else:
    # Quaternion equivalent of the above
    rot = np.ones((3,3),dtype=np.float)
    quat2 = vtk.vtkQuaterniond()
    vtk.vtkMath.MultiplyQuaternion(quat1, quat0, quat2)
    vtk.vtkMath.QuaternionToMatrix3x3(quat2, rot)

  # Rotation
  mat = np.zeros((4,4), dtype=np.float)
  mat[:3,:3] = rot
  mat[3,3] = 1.0

  # Translation
  tmp = vtk.vtkVector3d()
  vtk.vtkMath.Multiply3x3(rot, origin0, tmp)
  mat[:3,3] = np.array(origin1) - np.array(tmp)

  # Construct 4x4 matrix
  trans = vtk.vtkMatrix4x4()
  trans.DeepCopy(mat.flatten().tolist())

  return trans

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
