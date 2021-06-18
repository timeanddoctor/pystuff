import vtk
import numpy as np
import sys

global lastNormal
global lastAxis1
global axes

from vtkUtils import AxesToTransform




def SynchronizeAxes(obj, ev):
  global lastNormal
  global lastAxis1
  global axes
  global extrinsic
  
  print('sync')
  normal0 = lastNormal
  first0  = lastAxis1
  origin0 = axes.GetOrigin()

  normal1 = np.array(obj.GetNormal())
  first1 = np.array(obj.GetPoint1()) - np.array(obj.GetOrigin())

  # Normalize (not needed)
  l = np.sqrt(np.sum(first1**2))
  first1 = 1/l * first1
  
  origin1 = obj.GetCenter()

  trans = AxesToTransform(normal0, first0, origin0,
                          normal1, first1, origin1)

  if axes.GetUserTransform() is not None:
    axes.GetUserTransform().Concatenate(trans)
  else:
    transform = vtk.vtkTransform()
    transform.PostMultiply()
    transform.SetMatrix(trans)
    axes.SetUserTransform(transform)

  # Center moved to origin of axes
  axes.SetOrigin(obj.GetCenter()) # Not modified by SetUserTransform
  axes.Modified()

  # Update last axes
  lastAxis1[0] = first1[0]
  lastAxis1[1] = first1[1]
  lastAxis1[2] = first1[2]

  lastNormal = (normal1[0], normal1[1], normal1[2])


renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("Test")
renderWindow.SetSize(600, 600)

renderWindow.AddRenderer(renderer);
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

planeWidget = vtk.vtkPlaneWidget()
planeWidget.SetInteractor(renderWindowInteractor)
planeWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent, SynchronizeAxes, 1.0)

# Bind KeyPressEvent and KeyReleaseEvent
def Bum(obj, ev):
  if obj.GetShiftKey():
    extrinsic = True

renderWindowInteractor.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, Bum, 1.0)

# Make some initial movement 
planeWidget.SetOrigin(1.5, 0.5, 2)
planeWidget.SetPoint1(2.5, 0.5, 2)
planeWidget.SetPoint2(1.5, 1.5, 2)

# TODO: Test a rotation

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


# Move the axes-actor corresponding to the initial movement
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

tf = vtk.vtkTransform()
tf.SetMatrix(tfm)
tf.PostMultiply()
tf.Update()

# Apply the initial movement as a user transform
axes.SetUserTransform(tf)
axes.SetOrigin(planeWidget.GetCenter())
axes.Modified()

renderer.AddActor(axes)
renderWindow.Render()

renderWindowInteractor.Start()
