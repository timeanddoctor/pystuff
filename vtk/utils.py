import vtk
import numpy as np

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


def renderLinesAsTubes(prop):
  prop.SetEdgeVisibility(1)
  prop.SetPointSize(4) # Should be larger than line width
  prop.SetLineWidth(3)
  prop.SetRenderLinesAsTubes(1)
  return prop
