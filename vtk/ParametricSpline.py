import vtk

colors = vtk.vtkNamedColors()

# Create three points. We will join (Origin and P0) with a red line and
# (Origin and P1) with a green line
origin = [0.0, 0.0, 0.0]
p0 = [1.0, 0.0, 0.0]
p1 = [0.0, 1.0, 0.0]
p2 = [0.0, 1.0, 2.0]
p3 = [1.0, 2.0, 3.0]

# Create a vtkPoints object and store the points in it
points = vtk.vtkPoints()
points.InsertNextPoint(origin)
points.InsertNextPoint(p0)
points.InsertNextPoint(p1)
points.InsertNextPoint(p2)
points.InsertNextPoint(p3)

spline = vtk.vtkParametricSpline()
spline.SetPoints(points)

functionSource = vtk.vtkParametricFunctionSource()
functionSource.SetParametricFunction(spline)
functionSource.Update()

sphere = vtk.vtkSphereSource()
sphere.SetPhiResolution(21)
sphere.SetThetaResolution(21)
sphere.SetRadius(0.1)

# Setup actor and mapper
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(functionSource.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetColor(colors.GetColor3d("DarkSlateGrey"))
actor.GetProperty().SetLineWidth(3.0)

# Create a polydata to store everything in
polyData = vtk.vtkPolyData()
polyData.SetPoints(points)

pointMapper = vtk.vtkGlyph3DMapper()
pointMapper.SetInputData(polyData)
pointMapper.SetSourceConnection(sphere.GetOutputPort())

pointActor = vtk.vtkActor()
pointActor.SetMapper(pointMapper)
pointActor.GetProperty().SetColor(colors.GetColor3d("Peacock"))

# Setup render window, renderer, and interactor
renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)
renderWindow.SetWindowName("ParametricSpline")

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)
renderer.AddActor(actor)
renderer.AddActor(pointActor)
renderer.SetBackground(colors.GetColor3d("Silver"))

renderWindow.Render()
renderWindowInteractor.Start()
