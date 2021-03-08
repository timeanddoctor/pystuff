import sys
import vtk

# Define interaction style
class InteractorStyleMoveGlyph(vtk.vtkInteractorStyleTrackballActor):
#  static InteractorStyleMoveGlyph* New()
#  vtk.vtkTypeMacro(InteractorStyleMoveGlyph,vtk.vtkInteractorStyleTrackballActor)
  def __init__(self, parent=None):
    super(InteractorStyleMoveGlyph,self).__init__()
    self.InteractionPicker = vtk.vtkCellPicker()
    self.InteractionPicker.SetTolerance(0.001)

    self.AddObserver(vtk.vtkCommand.MouseMoveEvent,
                     lambda obj, ev: self.OnMouseMove(obj, ev))

    self.AddObserver(vtk.vtkCommand.MiddleButtonPressEvent,
                     lambda obj, ev: self.OnMiddleButtonDown(obj, ev))

    self.AddObserver(vtk.vtkCommand.MiddleButtonReleaseEvent,
                     lambda obj, ev: self.OnMiddleButtonUp(obj, ev))

    self.AddObserver(vtk.vtkCommand.LeftButtonPressEvent,
                     lambda obj, ev: self.OnLeftButtonDown(obj, ev))

    self.AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent,
                     lambda obj, ev: self.OnLeftButtonUp(obj, ev))

    self.CurrentRenderer = None # Only in python
    self.InteractionProp = None
    self.Data = None
    self.GlyphData = None

    self.MoveMapper = None
    self.MoveActor = None
    self.MoveSphereSource = None

    self.SelectedPoint = None

    self.MoveSphereSource = vtk.vtkSphereSource()
    self.MoveSphereSource.SetRadius(.1)
    self.MoveSphereSource.Update()

    self.MoveMapper = vtk.vtkPolyDataMapper()
    self.MoveMapper.SetInputConnection(self.MoveSphereSource.GetOutputPort())

    self.MoveActor = vtk.vtkActor()
    self.MoveActor.SetMapper(self.MoveMapper)
    #self.MoveActor.VisibilityOff()

    # Issue must be shared by parent to make same behaviour as in C++
    #self.EventCallbackCommand = vtk.vtkCallbackCommand()
    self.Move = False
  def OnLeftButtonDown(self, ob, ev):
    x = self.GetInteractor().GetEventPosition()[0]
    y = self.GetInteractor().GetEventPosition()[1];

    if (self.InteractionProp == self.MoveActor):
      print('equals move actor')

    self.FindPokedRenderer(x, y)
    prop = self.FindPickedActor(x, y)
    if not self.Move:
      if (prop is not None):
        self.InteractionProp = prop
      else:
        self.InteractionProp = None
    else:
      if (prop is None):
        self.InteractionProp = None

    if self.CurrentRenderer is None or self.InteractionProp is None:
      return

    #self.GrabFocus(self.EventCallbackCommand);

    if self.GetInteractor().GetShiftKey():
      self.StartPan()
    elif self.GetInteractor().GetControlKey():
      self.StartSpin()
    else:
      self.StartRotate()

  def Pan(self):
    if self.CurrentRenderer is None or self.InteractionProp is None:
      return

    rwi = self.GetInteractor()

    # Use initial center as the origin from which to pan

    obj_center = self.InteractionProp.GetCenter()

    disp_obj_center = [0.0, 0.0, 0.0]
    new_pick_point = [0.0, 0.0, 0.0, 0.0]
    old_pick_point = [0.0, 0.0, 0.0, 0.0]
    motion_vector =  [0.0, 0.0, 0.0]

    self.ComputeWorldToDisplay(self.CurrentRenderer,
                               obj_center[0], obj_center[1], obj_center[2],
                               disp_obj_center)

    self.ComputeDisplayToWorld(self.CurrentRenderer,
                               rwi.GetEventPosition()[0],
                               rwi.GetEventPosition()[1],
                               disp_obj_center[2],
                               new_pick_point)

    self.ComputeDisplayToWorld(self.CurrentRenderer,
                               rwi.GetLastEventPosition()[0],
                               rwi.GetLastEventPosition()[1],
                               disp_obj_center[2],
                               old_pick_point)

    motion_vector[0] = new_pick_point[0] - old_pick_point[0]
    motion_vector[1] = new_pick_point[1] - old_pick_point[1]
    motion_vector[2] = new_pick_point[2] - old_pick_point[2]

    if (self.InteractionProp.GetUserMatrix() is not None):
      t = vtk.vtkTransform()
      t.PostMultiply()
      t.SetMatrix(self.InteractionProp.GetUserMatrix())
      t.Translate(motion_vector[0], motion_vector[1], motion_vector[2])
      self.InteractionProp.GetUserMatrix().DeepCopy(t.GetMatrix())
      t.Delete()
    else:
      self.InteractionProp.AddPosition(motion_vector[0],
                                       motion_vector[1],
                                       motion_vector[2])

    if (self.GetAutoAdjustCameraClippingRange()):
      self.CurrentRenderer.ResetCameraClippingRange()

    rwi.Render()


  def OnLeftButtonUp(self, ob, ev):
    state = self.GetState()
    if state == vtk.VTKIS_PAN:
      self.EndPan()
    elif state == vtk.VTKIS_SPIN:
      self.EndSpin()
    elif state == vtk.VTKIS_ROTATE:
      self.EndRotate()

    if self.GetInteractor() is not None:
      self.ReleaseFocus()
  def SetRenderer(self, renderer):
    self.CurrentRenderer = renderer

  def FindPickedActor(self, x, y):
    self.InteractionPicker.Pick(x, y, 0.0, self.CurrentRenderer)
    prop = self.InteractionPicker.GetViewProp()
    return prop

  def OnMouseMove(self, ob, ev):
    # Was not self.Move to be able to make dragged move (not in python)
    #if not self.Move:
    #  return
    self.SuperOnMouseMove()
    #vtk.vtkInteractorStyleTrackballActor.OnMouseMove(self)
  def SuperOnMouseMove(self):
    x = self.GetInteractor().GetEventPosition()[0]
    y = self.GetInteractor().GetEventPosition()[1]

    state = self.GetState()
    if state == vtk.VTKIS_ROTATE:
      self.FindPokedRenderer(x, y)
      self.Rotate()
      self.InvokeEvent(vtk.vtkCommand.InteractionEvent, None)
    elif state == vtk.VTKIS_PAN:
      self.FindPokedRenderer(x, y)
      self.Pan()
      self.InvokeEvent(vtk.vtkCommand.InteractionEvent, None)
    elif state == vtk.VTKIS_DOLLY:
      self.FindPokedRenderer(x, y)
      self.Dolly()
      self.InvokeEvent(vtk.vtkCommand.InteractionEvent, None)
    elif state == vtk.VTKIS_SPIN:
      self.FindPokedRenderer(x, y)
      self.Spin()
      self.InvokeEvent(vtk.vtkCommand.InteractionEvent, None)
    elif state == vtk.VTKIS_USCALE:
       self.FindPokedRenderer(x, y)
       self.UniformScale()
       self.InvokeEvent(vtk.vtkCommand.InteractionEvent, None)

  def SuperOnMiddleButtonUp(self):
    state = self.GetState()
    if state == vtk.VTKIS_DOLLY:
      self.EndDolly()
    elif state == vtk.VTKIS_PAN:
      self.EndPan()

    if self.GetInteractor() is not None:
      self.ReleaseFocus()

  def OnMiddleButtonUp(self, ob, ev):
    # Forward events
    print('middle button up')
    #vtk.vtkInteractorStyleTrackballActor.OnMiddleButtonUp(self)
    self.SuperOnMiddleButtonUp()

    # was false to skip OnMouseMove
    #self.Move = False
    self.MoveActor.VisibilityOff()

    if self.SelectedPoint is not None:
      self.Data.GetPoints().SetPoint(self.SelectedPoint, self.MoveActor.GetPosition())
      self.Data.Modified()
      self.GetCurrentRenderer().Render()
      self.GetCurrentRenderer().GetRenderWindow().Render()

  def SuperOnMiddleButtonDown(self):
    #vtk.vtkInteractorStyleTrackballActor.OnMiddleButtonDown(self)
    x = self.GetInteractor().GetEventPosition()[0]
    y = self.GetInteractor().GetEventPosition()[1]
    self.FindPokedRenderer(x, y)

    prop = self.FindPickedActor(x, y)
    if prop is not None:
      self.InteractionProp = prop

    if self.InteractionProp is None:
      print('no prop hit')
      self.Move = False

    if self.CurrentRenderer is None or self.InteractionProp is None:
      return

    #self.GrabFocus(self.EventCallbackCommand)
    if (self.GetInteractor().GetControlKey()):
      self.StartDolly()
    else:
      self.StartPan()

  def OnMiddleButtonDown(self, ob, ev):
    print('middle button down')
    # Forward events - not possible to get InteractionPicker in python
    #vtk.vtkInteractorStyleTrackballActor.OnMiddleButtonDown(self)
    self.SuperOnMiddleButtonDown()

    self.MoveActor.VisibilityOn()

    if (self.InteractionPicker.GetPointId() >= 0):
      id  = self.GlyphData.GetPointData().GetArray("InputPointIds").GetValue(self.InteractionPicker.GetPointId())
      print("Id:" + str(id))
      self.Move = True
      self.SelectedPoint = id

      p = self.Data.GetPoint(id)
      self.MoveActor.SetPosition(p)

    self.GetCurrentRenderer().AddActor(self.MoveActor)
    # Used in parent class - important
    self.InteractionProp = self.MoveActor


def main():
  points = vtk.vtkPoints()
  points.InsertNextPoint(0,0,0)
  points.InsertNextPoint(1,0,0)
  points.InsertNextPoint(2,0,0)

  input0 = vtk.vtkPolyData()
  input0.SetPoints(points)

  glyphSource = vtk.vtkSphereSource()
  glyphSource.SetRadius(.1)
  glyphSource.Update()

  glyph3D = vtk.vtkGlyph3D()
  glyph3D.GeneratePointIdsOn()
  glyph3D.SetSourceConnection(glyphSource.GetOutputPort())
  glyph3D.SetInputData(input0)
  glyph3D.SetScaleModeToDataScalingOff()
  glyph3D.Update()

  # Create a mapper and actor
  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputConnection(glyph3D.GetOutputPort())

  actor = vtk.vtkActor()
  actor.SetMapper(mapper)

  # Visualize
  renderer = vtk.vtkRenderer()
  renderWindow = vtk.vtkRenderWindow()
  renderWindow.AddRenderer(renderer)

  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  renderWindowInteractor.SetRenderWindow(renderWindow)

  renderer.AddActor(actor)
  #renderer.SetBackground(1,1,1) # Background color white

  renderWindow.Render()

  style = InteractorStyleMoveGlyph()
  style.SetRenderer(renderer)
  renderWindowInteractor.SetInteractorStyle( style )
  style.Data = input0
  style.GlyphData = glyph3D.GetOutput()

  renderWindowInteractor.Start()


if __name__ == '__main__':
    main()

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
