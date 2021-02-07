import vtk

namedColors = vtk.vtkNamedColors()

# Create a sphere
sphereSource = vtk.vtkSphereSource()
sphereSource.Update()

sphereMapper = vtk.vtkPolyDataMapper()
sphereMapper.SetInputConnection(sphereSource.GetOutputPort())
sphereActor = vtk.vtkActor()
sphereActor.SetMapper(sphereMapper)
sphereActor.GetProperty().SetColor(namedColors.GetColor3d("Banana"))


# Create a cube
cubeSource = vtk.vtkCubeSource()
cubeSource.SetCenter(5.0, 0.0, 0.0)
cubeSource.Update()

cubeMapper = vtk.vtkPolyDataMapper()
cubeMapper.SetInputConnection(cubeSource.GetOutputPort())
cubeActor = vtk.vtkActor()
cubeActor.SetMapper(cubeMapper)
cubeActor.GetProperty().SetColor(namedColors.GetColor3d("Tomato"))
cubeActor.Modified()
# Combine the sphere and cube into an assembly
assembly = vtk.vtkAssembly()
assembly.AddPart(sphereActor)
assembly.AddPart(cubeActor)

# Apply a transform to the whole assembly
transform = vtk.vtkTransform()
transform.PostMultiply() #this is the key line
transform.Translate(5.0, 0, 0)

assembly.SetUserTransform(transform)

# Extract each actor from the assembly and change its opacity
collection = vtk.vtkPropCollection()

assembly.GetActors(collection)
collection.InitTraversal()
for i in range(collection.GetNumberOfItems()):
  actor = collection.GetNextProp()
  actor.GetProperty().SetOpacity(0.5)

# Visualization
renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

renderer.AddActor(assembly)
renderer.SetBackground(namedColors.GetColor3d("SlateGray"))

renderer.ResetCamera()
renderWindow.Render()

renderWindowInteractor.Start()

