import vtk

# Sphere 1
sphereSource1 = vtk.vtkSphereSource()
sphereSource1.SetCenter(0.0, 0.0, 0.0)
sphereSource1.SetRadius(4.0)
sphereSource1.Update()

mapper1 = vtk.vtkPolyDataMapper()
mapper1.SetInputConnection(sphereSource1.GetOutputPort())

actor1 = vtk.vtkActor()
actor1.SetMapper(mapper1)

# Sphere 2
sphereSource2 = vtk.vtkSphereSource()
sphereSource2.SetCenter(10.0, 0.0, 0.0)
sphereSource2.SetRadius(3.0)
sphereSource2.Update()

# Create a mapper
mapper2 = vtk.vtkPolyDataMapper()
mapper2.SetInputConnection(sphereSource2.GetOutputPort())

# Create an actor
actor2 = vtk.vtkActor()
actor2.SetMapper(mapper2)

# A renderer and render window
renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

# An interactor
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

# Add the actors to the scene
renderer.AddActor(actor1)
renderer.AddActor(actor2)
renderer.SetBackground(1,1,1) # Background color white

# Render an image (lights and cameras are created automatically)
renderWindow.Render()

style = vtk.vtkInteractorStyleTrackballActor()

renderWindowInteractor.SetInteractorStyle( style )

# Begin mouse interaction
renderWindowInteractor.Start()
