import vtk

plane_source = vtk.vtkPlaneSource()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(plane_source.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)

renderer0 = vtk.vtkRenderer()
renderer1 = vtk.vtkRenderer()
renderer0.SetLayer(0)
renderer1.SetLayer(1)
render_window = vtk.vtkRenderWindow()
render_window.SetNumberOfLayers(2)
if 0:
    render_window.AddRenderer(renderer0)

    # The following line triggers rendering problems
    render_window.AddRenderer(renderer1)
else:
    render_window.AddRenderer(renderer1)
    render_window.AddRenderer(renderer0) # The active renderer
camera = vtk.vtkCamera()
renderer0.SetActiveCamera(camera)
renderer1.SetActiveCamera(camera)

renderer0.AddActor(actor)
renderer0.ResetCamera()

render_window_interactor = vtk.vtkRenderWindowInteractor()
trackball_style = vtk.vtkInteractorStyleTrackballCamera()

render_window_interactor.SetRenderWindow(render_window)
render_window_interactor.SetInteractorStyle(trackball_style)

render_window.Render()
render_window_interactor.Start()
