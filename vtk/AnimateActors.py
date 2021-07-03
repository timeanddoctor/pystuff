import vtk
import sys

class ActorAnimator(object):
  def __init__(self):
    self.Actor = None
    self.StartPosition = vtk.vtkVector3d(.0, .0, .0)
    self.EndPosition = vtk.vtkVector3d(.0, .0, .0)

  def SetActor(self, actor):
    self.Actor = actor
  def SetEndPosition(self, position):
    self.EndPosition = position
  def SetStartPosition(self, position):
    self.StartPosition = position
  def AddObserversToCue(self, cue):
    cue.AddObserver(vtk.vtkCommand.StartAnimationCueEvent, self.Start)
    cue.AddObserver(vtk.vtkCommand.EndAnimationCueEvent, self.End)
    cue.AddObserver(vtk.vtkCommand.AnimationCueTickEvent, self.Tick)
  def Start(self, obj, ev):
    self.Actor.SetPosition(self.StartPosition)

  def Tick(self, obj, ev):
    position = vtk.vtkVector3d()
    if (type(obj) == vtk.vtkAnimationCue):
      ac = obj
      t = (ac.GetAnimationTime() - ac.GetStartTime()) / (ac.GetEndTime() - ac.GetStartTime())
      delta = vtk.vtkVector3d()
      vtk.vtkMath.Subtract(self.EndPosition, self.StartPosition, delta)
      vtk.vtkMath.MultiplyScalar(delta, t)
      position = vtk.vtkVector3d()
      vtk.vtkMath.Add(self.StartPosition, delta, position)
      self.Actor.SetPosition(position)
  def End(self, obj, ev):
    self.Actor.SetPosition(self.EndPosition)

global renWin
renWin = None

def RenderCallback(obj, ev):
  global renWin
  renWin.Render()

def main(argv):
  # Sinleton
  vtk.vtkLogger.Init()

  colors = vtk.vtkNamedColors()
  coneColor = colors.GetColor3d("Tomato")
  sphereColor = colors.GetColor3d("Banana")
  backgroundColor = colors.GetColor3d("Peacock")

  # Create the graphics structure. The renderer renders into the
  # render window.
  iren = vtk.vtkRenderWindowInteractor()
  ren1 = vtk.vtkRenderer()
  ren1.SetBackground(backgroundColor)

  global renWin
  renWin = vtk.vtkRenderWindow()
  iren.SetRenderWindow(renWin)
  renWin.AddRenderer(ren1)

  # Generate a sphere
  sphereSource = vtk.vtkSphereSource()
  sphereSource.SetPhiResolution(31)
  sphereSource.SetThetaResolution(31)

  sphereMapper = vtk.vtkPolyDataMapper()
  sphereMapper.SetInputConnection(sphereSource.GetOutputPort())
  sphere = vtk.vtkActor()
  sphere.SetMapper(sphereMapper)
  sphere.GetProperty().SetDiffuseColor(sphereColor)
  sphere.GetProperty().SetDiffuse(.7)
  sphere.GetProperty().SetSpecular(.3)
  sphere.GetProperty().SetSpecularPower(30.0)

  ren1.AddActor(sphere)

  # Generate a cone
  coneSource = vtk.vtkConeSource()
  coneSource.SetResolution(31)

  coneMapper = vtk.vtkPolyDataMapper()
  coneMapper.SetInputConnection(coneSource.GetOutputPort())
  cone = vtk.vtkActor()
  cone.SetMapper(coneMapper)
  cone.GetProperty().SetDiffuseColor(coneColor)

  ren1.AddActor(cone)

  # Create an Animation Scene
  scene = vtk.vtkAnimationScene()
  if (len(sys.argv) >= 2 and argv[1] == "-real"):
      #vtkLogF(INFO, "real-time mode")
      scene.SetModeToRealTime()
  else:
      #vtkLogF(INFO, "sequence mode")
      scene.SetModeToSequence()
  scene.SetLoop(0)
  scene.SetFrameRate(5)
  scene.SetStartTime(0)
  scene.SetEndTime(20)
  scene.AddObserver("AnimationCueTickEvent", RenderCallback)

  # Create an Animation Cue for each actor
  cue1 = vtk.vtkAnimationCue()
  cue1.SetStartTime(5)
  cue1.SetEndTime(23)
  scene.AddCue(cue1)

  cue2 = vtk.vtkAnimationCue()
  cue2.SetStartTime(1)
  cue2.SetEndTime(10)
  scene.AddCue(cue2)

  # Create an ActorAnimator for each actor
  animateSphere = ActorAnimator()
  animateSphere.SetActor(sphere)
  animateSphere.AddObserversToCue(cue1)

  animateCone = ActorAnimator()
  animateCone.SetEndPosition(vtk.vtkVector3d(-1, -1, -1))
  animateCone.SetActor(cone)
  animateCone.AddObserversToCue(cue2)

  renWin.SetWindowName("AnimateActors")

  renWin.Render()
  ren1.ResetCamera()
  ren1.GetActiveCamera().Dolly(.5)
  ren1.ResetCameraClippingRange()

  # Create Cue observer.
  scene.Play()
  scene.Stop()

  iren.Start()

if __name__ == "__main__":
    main(sys.argv)
