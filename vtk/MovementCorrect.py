import vtk
import numpy as np
import sys

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

  # Can be performed using quaternions
  vtk.vtkMath.Multiply3x3(rot0, first0, newFirst)

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

  rot1 = np.ones((3,3),dtype=np.float)
  vtk.vtkMath.QuaternionToMatrix3x3(quat1, rot1)
  rot = np.dot(rot1, rot0)

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

def createAxesActor(length=20.0):
  """
  Create axes actor with variable lengths of axes. The actor is made
  pickable. If a prop picker is used the axes(this prop) can be picked
  """
  axes = vtk.vtkAxesActor()
  axes_length = length
  axes_label_font_size = np.int16(14)
  axes.SetTotalLength(axes_length, axes_length, axes_length)
  axes.SetCylinderRadius(0.01)
  axes.SetShaftTypeToCylinder()
  axes.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
  axes.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
  axes.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
  axes.GetXAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
  axes.GetYAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
  axes.GetZAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
  prop = axes.GetXAxisShaftProperty()
  renderLinesAsTubes(prop)
  prop.SetEdgeColor(0.9,0.0,0.0)
  prop = axes.GetYAxisShaftProperty()
  renderLinesAsTubes(prop)
  prop.SetEdgeColor(0.0,0.9,0.0)
  prop = axes.GetZAxisShaftProperty()
  renderLinesAsTubes(prop)
  prop.SetEdgeColor(0.0,0.0,0.9)
  axes.PickableOn()
  return axes


class vtkAxesTransformWidget2(vtk.vtkObject):
  """
  Simple composiste widget, which allow the movement of an axes actor.

  After movement, the user must press 'u' to update.

  TODO: Consider calling UpdatePlane when axes actor is modified due
  any inputs
  """
  def __init__(self, transform = None):
    self.planeWidget = vtk.vtkPlaneWidget()
    self.planeWidget.SetHandleSize(0.02)
    self.axes = createAxesActor(length=0.5)

    pOrigin = vtk.vtkVector3d(np.r_[-0.5, -0.5, 0])
    pPoint1 = vtk.vtkVector3d(np.r_[0.5, -0.5, 0])
    pPoint2 = vtk.vtkVector3d(np.r_[-0.5, 0.5, 0])

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

    self.axes.SetOrigin(self.planeWidget.GetCenter())
    self.axes.Modified()

    self.planeWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent,
                                 self.SynchronizePlaneCallback, 1.0)
    self.extrinsicHandle = 0
    self.updateHandle = 0

    self.extrinsic = False

  def SetInteractor(self, iren):
    self.planeWidget.SetInteractor(iren)
    if self.extrinsicHandle == 0:
      self.extrinsicHandle = iren.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent, self.Extrinsic, 1.0)
    if self.updateHandle == 0:
      self.updateHandle = iren.AddObserver(vtk.vtkCommand.KeyPressEvent, self.UpdatePlaneCallback, 1.0)

    # TODO: Throw error if impossible to add axes actor to a renderer
    # Correct way is to associate a renderer to THIS widget
    renderer = iren.GetRenderWindow().GetRenderers().GetFirstRenderer()
    renderer.AddActor(self.axes)

  def UpdatePlaneCallback(self, obj, ev):
    key = obj.GetKeySym()
    if key == 'u':
      self.UpdatePlane()
      self.planeWidget.GetInteractor().GetRenderWindow().Render()

  def Extrinsic(self, obj, ev):
    if obj.GetShiftKey():
      self.extrinsic = True
      print('Last transformation was extrinsic')

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

  def UpdatePlane(self):
    origin = vtk.vtkVector3d(np.r_[-0.5, -0.5, 0])
    point1 = vtk.vtkVector3d(np.r_[ 0.5, -0.5, 0])
    point2 = vtk.vtkVector3d(np.r_[-0.5,  0.5, 0])
    self.planeWidget.SetOrigin(self.axes.GetUserTransform().TransformPoint(origin))
    self.planeWidget.SetPoint1(self.axes.GetUserTransform().TransformPoint(point1))
    self.planeWidget.SetPoint2(self.axes.GetUserTransform().TransformPoint(point2))
    self.planeWidget.Modified()

    # We have used the last position of the plane widget to store last point.
    # This must be updated when updated indrectly
    self.lastNormal = self.planeWidget.GetNormal()
    vtk.vtkMath.Subtract(self.planeWidget.GetPoint1(), self.planeWidget.GetOrigin(), self.lastAxis1)
    self.axes.SetOrigin(self.planeWidget.GetCenter())

  def SynchronizePlaneCallback(self, obj, ev):
    # If not updated using 'u', things get out of order
    # Consider update these parameters when the axes actor has been updated
    normal0 = self.lastNormal
    first0  = self.lastAxis1
    origin0 = self.axes.GetOrigin() # Way to store origin

    # New coordinate system
    normal1 = obj.GetNormal()
    first1  = vtk.vtkVector3d()
    vtk.vtkMath.Subtract(obj.GetPoint1(), obj.GetOrigin(), first1)
    first1.Normalize()

    origin1 = obj.GetCenter()

    # Transform
    trans = AxesToTransform(normal0, first0, origin0,
                            normal1, first1, origin1)

    if self.axes.GetUserTransform() is not None:
      if self.extrinsic:
        self.axes.GetUserTransform().PreMultiply()
      self.axes.GetUserTransform().Concatenate(trans)
    else:
      transform = vtk.vtkTransform()
      transform.PostMultiply()
      transform.SetMatrix(trans)
      self.axes.SetUserTransform(transform)

    self.axes.GetUserTransform().Update()

    if self.extrinsic:
      self.axes.GetUserTransform().PostMultiply()
      self.extrinsic = False

    # Center moved to origin of axes
    self.axes.SetOrigin(obj.GetCenter())
    self.axes.Modified()

    # Update last axes
    self.lastAxis1 = first1
    self.lastNormal = normal1


renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("Test")
renderWindow.SetSize(600, 600)

renderWindow.AddRenderer(renderer);
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)


# Some transforms
tf0 = vtk.vtkTransform()
tf0.PostMultiply()
tf0.Update()

objTransform1 = vtk.vtkTransform()
objTransform1.PostMultiply()
objTransform1.Concatenate(tf0)
objTransform1.Translate(0,0,0.7)
objTransform1.Update()

objTransform2 = vtk.vtkTransform()
objTransform2.PostMultiply()
objTransform2.SetInput(objTransform1)
objTransform2.Translate(0.2, 0.0, 0.1)

renderWindowInteractor.Initialize()

pw0 = vtkAxesTransformWidget2(transform=tf0)
pw0.SetInteractor(renderWindowInteractor)
pw0.On()

pw1 = vtkAxesTransformWidget2(transform=objTransform1)
pw1.SetInteractor(renderWindowInteractor)
pw1.On()

pw2 = vtkAxesTransformWidget2(transform=objTransform2)
pw2.SetInteractor(renderWindowInteractor)
pw2.On()


renderer.ResetCamera()
renderWindow.Render()

renderWindowInteractor.Start()
