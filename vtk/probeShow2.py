import vtk

from ProbeView import CreateOutline9076, CreateSurface9076

outline = CreateOutline9076()
mesh = CreateSurface9076()

mapper0 = vtk.vtkPolyDataMapper()
mapper0.SetInputData(outline)

actor0 = vtk.vtkActor()
actor0.SetMapper(mapper0)
actor0.GetProperty().SetLineWidth(4)

mapper1 = vtk.vtkPolyDataMapper()
mapper1.SetInputData(mesh)

actor1 = vtk.vtkActor()
actor1.SetMapper(mapper1)

# TODO: Make a utility function
from vtk.util.colors import red, blue, black, yellow

cubeAxesActor = vtk.vtkCubeAxesActor()
cubeAxesActor.SetUseTextActor3D(1)
bounds0 = outline.GetBounds()
bounds1 = mesh.GetBounds()
bounds = (min(bounds0[0],bounds1[0]),
          max(bounds0[1],bounds1[1]),
          min(bounds0[2],bounds1[2]),
          max(bounds0[3],bounds1[3]),
          min(bounds0[4],bounds1[4]),
          max(bounds0[5],bounds1[5]))
cubeAxesActor.SetBounds(bounds)
cubeAxesActor.XAxisMinorTickVisibilityOff()
cubeAxesActor.YAxisMinorTickVisibilityOff()
cubeAxesActor.ZAxisMinorTickVisibilityOff()
cubeAxesActor.SetFlyModeToStaticEdges()
for i in range(3):
  cubeAxesActor.GetLabelTextProperty(i).SetColor(black)
  cubeAxesActor.GetTitleTextProperty(i).SetColor(black)
cubeAxesActor.GetXAxesLinesProperty().SetColor(black)
cubeAxesActor.GetYAxesLinesProperty().SetColor(black)
cubeAxesActor.GetZAxesLinesProperty().SetColor(black)

cubeAxesActor.GetProperty().SetColor(black)

namedColors = vtk.vtkNamedColors()

renderer = vtk.vtkRenderer()
cubeAxesActor.SetCamera(renderer.GetActiveCamera())
renderer.AddActor(cubeAxesActor)
renderer.AddActor(actor0)
renderer.AddActor(actor1)
renderer.SetBackground(namedColors.GetColor3d("SlateGray"))

renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("9076")
renderWindow.SetSize(600, 600)
renderWindow.AddRenderer(renderer)

camera = renderer.GetActiveCamera()
camera.ParallelProjectionOn()



interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renderWindow)

renderWindow.Render()
interactor.Start()
