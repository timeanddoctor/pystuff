import sys
import vtk
import numpy as np

def renderLinesAsTubes(prop):
  prop.SetEdgeVisibility(1)
  prop.SetPointSize(4)
  prop.SetLineWidth(3)
  prop.SetRenderLinesAsTubes(1)
  return prop

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
