import vtk

class MouseInteractorStyle5(vtk.vtkInteractorStyleTrackballActor):
  def __init__(self, parent=None):
    super(MouseInteractorStyle5,self).__init__()
    self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
    self.cube = None
    self.Sphere = None
  def leftButtonPressEvent(self, obj, event):
    clickPos = self.GetInteractor().GetEventPosition()

    picker = vtk.vtkPropPicker()
    picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())

    # get the new
    self.NewPickedActor = picker.GetActor()

    # If something was selected
    if self.NewPickedActor:
      if self.NewPickedActor == self.cube:
        print("Picked cube")
      elif self.NewPickedActor == self.sphere:
        print("Picked sphere.")
    self.OnLeftButtonDown()
    return
def main():
  # Create a cube
  cubeSource = vtk.vtkCubeSource()
  cubeSource.Update()

  cubeMapper = vtk.vtkPolyDataMapper()
  cubeMapper.SetInputConnection(cubeSource.GetOutputPort())

  cubeActor = vtk.vtkActor()
  cubeActor.SetMapper(cubeMapper)

  # Create a sphere
  sphereSource = vtk.vtkSphereSource()
  sphereSource.SetCenter(5,0,0)
  sphereSource.Update()

  # Create a mapper
  sphereMapper = vtk.vtkPolyDataMapper()
  sphereMapper.SetInputConnection(sphereSource.GetOutputPort())

  # Create an actor
  sphereActor = vtk.vtkActor()
  sphereActor.SetMapper(sphereMapper)

  # A renderer and render window
  renderer = vtk.vtkRenderer()
  renderWindow = vtk.vtkRenderWindow()
  renderWindow.AddRenderer(renderer)

  # An interactor
  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  renderWindowInteractor.SetRenderWindow(renderWindow)

  # Set the custom stype to use for interaction.
  style = MouseInteractorStyle5()
  style.SetDefaultRenderer(renderer)
  style.cube = cubeActor
  style.sphere = sphereActor

  renderWindowInteractor.SetInteractorStyle(style)

  renderer.AddActor(cubeActor)
  renderer.AddActor(sphereActor)
  renderer.SetBackground(0,0,1)

  # Render and interact
  renderWindowInteractor.Initialize()
  renderWindow.Render()
  renderWindowInteractor.Start()

if __name__ == "__main__":
  main()

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
