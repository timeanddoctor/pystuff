import vtk
import numpy as np
import sys

global lastNormal
global lastAxis1
global axes

from vtkUtils import AxesToTransform

# TODO: Only axes actors with user transforms depend on transforms

# Works without initial rotation
class vtkAxesTransformWidget2(vtk.vtkObject):
  """
  No internal renderer, so you need to explicit add the axes
  member to the renderer used
  """
  def __init__(self, transform = None):
    self.planeWidget = vtk.vtkPlaneWidget()
    self.axes = vtk.vtkAxesActor()
    pOrigin = vtk.vtkVector3d(np.r_[0, 0, 0])
    pPoint1 = vtk.vtkVector3d(np.r_[1, 0, 0])
    pPoint2 = vtk.vtkVector3d(np.r_[0, 1, 0])

    if transform is not None:
      self.axes.SetUserTransform(transform)
      pOrigin = transform.TransformPoint(pOrigin)
      pPoint1 = transform.TransformPoint(pPoint1)
      pPoint2 = transform.TransformPoint(pPoint2)

    self.planeWidget.SetOrigin(pOrigin)
    self.planeWidget.SetPoint1(pPoint1)
    self.planeWidget.SetPoint2(pPoint2)

    self.planeWidget.Modified()

    self.lastNormal = self.planeWidget.GetNormal()
    self.lastAxis1 = vtk.vtkVector3d()

    vtk.vtkMath.Subtract(self.planeWidget.GetPoint1(),
                         self.planeWidget.GetOrigin(),
                         self.lastAxis1)
    print(self.lastNormal)
    print(self.lastAxis1)

    self.axes.SetOrigin(self.planeWidget.GetOrigin())

    self.axes.Modified()

    self.planeWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent,
                                 self.SynchronizeAxes, 1.0)
    # TODO: Create update button to align all widgets with their axes

  def SetInteractor(self, iren):
    self.planeWidget.SetInteractor(iren)

  def GetOrigin(self):
    return self.planeWidget.GetOrigin()

  def SetOrigin(self, pOrigin):
    self.planeWidget.SetOrigin(pOrigin)

  def SetPoint1(self, pPoint1):
    self.planeWidget.SetPoint1(pPoint1)

  def SetPoint2(self, pPoint2):
    self.planeWidget.SetPoint2(pPoint2)

  def Modified(self):
    self.planeWidget.Modified()

  def On(self):
    self.planeWidget.On()

  def GetNormal(self):
    return self.planeWidget.GetNormal()

  def GetPoint1(self):
    return self.planeWidget.GetPoint1()

  def GetPoint2(self):
    return self.planeWidget.GetPoint2()

  def GetCenter(self):
    return self.planeWidget.GetCenter()

  def UpdatePlane(self):
    origin = vtk.vtkVector3d(np.r_[0, 0, 0])
    point1 = vtk.vtkVector3d(np.r_[1, 0, 0])
    point2 = vtk.vtkVector3d(np.r_[0, 1, 0])
    self.planeWidget.SetOrigin(self.axes.GetUserTransform().TransformPoint(origin))
    self.planeWidget.SetPoint1(self.axes.GetUserTransform().TransformPoint(point1))
    self.planeWidget.SetPoint2(self.axes.GetUserTransform().TransformPoint(point2))
    self.planeWidget.Modified()
    # Consider transforming points
  def SynchronizeAxes(self, obj, ev):

    # Old coordinate system
    normal0 = self.lastNormal
    first0  = self.lastAxis1
    origin0 = self.axes.GetOrigin() # Way to store origin

    # New coordinate system
    normal1 = obj.GetNormal()
    first1  = vtk.vtkVector3d()
    vtk.vtkMath.Subtract(obj.GetPoint1(), obj.GetOrigin(), first1)
    # Normalize (not needed - but we do this anyway)
    #first1.Normalize()
    #origin1 = obj.GetCenter() # Original
    origin1 = obj.GetOrigin()

    # Transform
    trans = AxesToTransform(normal0, first0, origin0,
                            normal1, first1, origin1)


    if self.axes.GetUserTransform() is not None:
      self.axes.GetUserTransform().Concatenate(trans)
    else:
      transform = vtk.vtkTransform()
      transform.PostMultiply()
      transform.SetMatrix(trans)
      self.axes.SetUserTransform(transform)

    self.axes.GetUserTransform().Update()

    # Center moved to origin of axes
    self.axes.SetOrigin(obj.GetOrigin())
    self.axes.Modified()

    # Update last axes
    self.lastAxis1 = first1
    self.lastNormal = normal1
    print(self.__repr__)
    print('done sync')


renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("Test")
renderWindow.SetSize(600, 600)

renderWindow.AddRenderer(renderer);
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)



tf0 = vtk.vtkTransform()
tf0.PostMultiply()
tf0.Update()

tf1 = vtk.vtkTransform()
tf1.PostMultiply()
tf1.Translate(0,0,0.7)
tf1.Update()

tf2 = vtk.vtkTransform()
tf2.PostMultiply()
tf2.Concatenate(tf0)
tf2.Concatenate(tf1)
tf2.Update()


planeWidget = vtkAxesTransformWidget2(transform=tf0)
planeWidget.SetInteractor(renderWindowInteractor)

# Bind KeyPressEvent and KeyReleaseEvent
def Bum(obj, ev):
  if obj.GetShiftKey():
    extrinsic = True

renderWindowInteractor.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, Bum, 1.0)


planeWidget.Modified()


renderWindowInteractor.Initialize()

planeWidget.On()

renderer.AddActor(planeWidget.axes)

pw = vtkAxesTransformWidget2(transform=tf2)
pw.SetInteractor(renderWindowInteractor)
pw.On()
renderer.AddActor(pw.axes)

renderer.ResetCamera()

renderWindow.Render()

def bla(obj, ev):
  key = obj.GetKeySym()
  if key == 'u':
    planeWidget.UpdatePlane()
    pw.UpdatePlane()
    renderWindow.Render()

renderWindowInteractor.AddObserver(vtk.vtkCommand.KeyPressEvent, bla)


renderWindowInteractor.Start()
