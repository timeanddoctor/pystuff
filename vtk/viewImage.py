# TODO: View simple image,
import vtk

# Read the source file.
reader = vtk.vtkPNGReader()
reader.SetFileName("oIu8j.png")
reader.Update()

# Display the image
actor = vtk.vtkImageActor()
actor.GetMapper().SetInputConnection(reader.GetOutputPort())

renderer = vtk.vtkRenderer()
renderer.AddActor(actor)

window = vtk.vtkRenderWindow()
window.AddRenderer(renderer)

# Set up the interaction
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(window)
interactor.Initialize()
interactor.Start()
