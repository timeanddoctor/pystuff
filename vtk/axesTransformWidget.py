import vtk

renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer);

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

ss = vtk.vtkSphereSource()
ss.SetCenter(100,250,500)
ss.Update()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(ss.GetOutputPort())
actor = vtk.vtkActor()
actor.SetMapper(mapper)

rep = vtk.vtkAxesTransformRepresentation()
axes = vtk.vtkAxesTransformWidget()
axes.SetInteractor(renderWindowInteractor)
axes.SetRepresentation(rep)

print(rep)
print(axes)

renderer.AddActor(actor)
renderer.SetBackground(0.1,0.2,0.4)
renderWindow.SetSize(300,300)

renderer.ResetCamera()

renderWindowInteractor.Initialize()
renderWindow.Render()
axes.On()
renderWindow.Render()

renderWindowInteractor.Start()
