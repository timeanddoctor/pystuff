import vtk
import numpy as np
import sys

global lastNormal
global lastAxis1
global axes

from vtkUtils import AxesToTransform


def MyFunc2(obj, ev):
  global lastNormal
  global lastAxis1
  global axes

  normal0 = lastNormal
  first0  = lastAxis1
  origin0 = axes.GetOrigin()

  normal1 = np.array(obj.GetNormal())
  first1 = np.array(obj.GetPoint1()) - np.array(obj.GetOrigin())
  origin1 = obj.GetCenter()

  trans = AxesToTransform(normal0, first0, origin0,
                          normal1, first1, origin1)

  if axes.GetUserTransform() is not None:
    axes.GetUserTransform().Concatenate(trans)
  else:
    transform = vtk.vtkTransform()
    transform.SetMatrix(trans)
    transform.PostMultiply()
    axes.SetUserTransform(transform)

  # Only for book keeping
  axes.SetOrigin(obj.GetCenter()) # Not modified by SetUserTransform
  axes.Modified()

  # Update last axes
  lastAxis1[0] = first1[0]
  lastAxis1[1] = first1[1]
  lastAxis1[2] = first1[2]

  lastNormal = (normal1[0], normal1[1], normal1[2])

def MyFunc(obj, ev):
  global lastNormal
  global lastAxis1
  global axes

  saxis = np.array(obj.GetPoint1()) - np.array(obj.GetOrigin())
  axis = np.array(obj.GetNormal())

  vec = vtk.vtkVector3d() # Axis of rotation
  vtk.vtkMath.Cross(lastNormal, axis, vec)
  costheta = vtk.vtkMath.Dot(axis, lastNormal)
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
  rot0 = np.ones((3,3),dtype=np.float)
  vtk.vtkMath.QuaternionToMatrix3x3(quat0, rot0)

  if 1:
    newAxis1 = vtk.vtkVector3d()
    vtk.vtkMath.Multiply3x3(rot0, lastAxis1, newAxis1)

    # Rotate newAxis1 into saxis
    vec = vtk.vtkVector3d() # Axis of rotation
    vtk.vtkMath.Cross(newAxis1, saxis, vec)
    costheta = vtk.vtkMath.Dot(saxis, newAxis1)
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
    rot1 = np.ones((3,3),dtype=np.float)
    vtk.vtkMath.QuaternionToMatrix3x3(quat1, rot1)

    # Concatenate rotations
    rot = np.dot(rot1, rot0)

    # Rotate rot1 * rot0 (0, ix, jy, kz) rot0^-1 rot1^-1 = rot1*rot0 (0,x,y,z) (rot1*rot0)^-1
    #rot2 = np.ones((3,3),dtype=np.float)
    #quat2 = vtk.vtkQuaterniond()
    #vtk.vtkMath.MultiplyQuaternion(quat1, quat0, quat2)
    #vtk.vtkMath.QuaternionToMatrix3x3(quat2, rot2)

  mat = np.zeros((4,4), dtype=np.float)
  mat[:3,:3] = rot
  mat[3,3] = 1.0

  tmp = vtk.vtkVector3d()
  vtk.vtkMath.Multiply3x3(rot, axes.GetOrigin(), tmp)
  mat[:3,3] = np.array(obj.GetCenter()) - np.array(tmp)

  # Construct 4x4 matrix
  trans = vtk.vtkMatrix4x4()
  trans.DeepCopy(mat.flatten().tolist())

  if axes.GetUserTransform() is not None:
    axes.GetUserTransform().Concatenate(trans)
  else:
    transform = vtk.vtkTransform()
    transform.SetMatrix(trans)
    transform.PostMultiply()
    axes.SetUserTransform(transform)

  # Only for book keeping
  axes.SetOrigin(obj.GetCenter()) # Not modified by SetUserTransform
  axes.Modified()

  # Update last axes
  lastAxis1[0] = saxis[0]
  lastAxis1[1] = saxis[1]
  lastAxis1[2] = saxis[2]

  lastNormal = (axis[0], axis[1], axis[2])


renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("Test")
renderWindow.SetSize(600, 600)

renderWindow.AddRenderer(renderer);
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

planeWidget = vtk.vtkPlaneWidget()
planeWidget.SetInteractor(renderWindowInteractor)
#planeWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent, MyFunc, 1.0)
planeWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent, MyFunc2, 1.0)

initialMovement = True

if initialMovement:
  planeWidget.SetOrigin(1.5, 0.5, 2)
  planeWidget.SetPoint1(2.5, 0.5, 2)
  planeWidget.SetPoint2(1.5, 1.5, 2)

planeWidget.Modified()
planeWidget.On()

lastNormal = planeWidget.GetNormal()
lastAxis1 = vtk.vtkVector3d()

vtk.vtkMath.Subtract(planeWidget.GetPoint1(),
                     planeWidget.GetOrigin(),
                     lastAxis1)

renderWindowInteractor.Initialize()

renderer.ResetCamera()

# Crazy behavior for origin
axes = vtk.vtkAxesActor()
if initialMovement:
  tf = vtk.vtkTransform()

  rot = np.diag(np.ones(3, dtype=np.float))
  mat = np.zeros((4,4), dtype=np.float)
  mat[:3,:3] = rot
  mat[3,3] = 1.0
  tmp = vtk.vtkVector3d()
  vtk.vtkMath.Multiply3x3(rot, axes.GetOrigin(), tmp)
  mat[:3,3] = np.array(planeWidget.GetCenter()) - np.array(tmp)

  # Construct 4x4 matrix
  tfm = vtk.vtkMatrix4x4()
  tfm.DeepCopy(mat.flatten().tolist())
  tfm.Modified()
  tf.SetMatrix(tfm)
  tf.PostMultiply()
  tf.Update()
  axes.SetUserTransform(tf)
  axes.SetOrigin(planeWidget.GetCenter())
  axes.Modified()

renderer.AddActor(axes)

renderWindow.Render()
renderWindowInteractor.Start()
