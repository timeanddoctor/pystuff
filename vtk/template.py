import vtk

renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

# Contain triangle-strips
ss = vtk.vtkSectorSource()
ss.SetRadialResolution(10)
ss.SetCircumferentialResolution(10)
ss.SetInnerRadius(10)
ss.SetOuterRadius(50)
ss.SetStartAngle(-10)
ss.SetEndAngle(10.0)
ss.ReleaseDataFlagOn()
ss.Update()

loopData = ss.GetOutput()

# TODO: Use IdFilter instead
contours = vtk.vtkFeatureEdges()
contours.SetInputData(loopData)
contours.BoundaryEdgesOn()
contours.FeatureEdgesOff()
contours.ManifoldEdgesOff()
contours.NonManifoldEdgesOff()
contours.Update()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(contours.GetOutputPort())
#mapper.SetInputConnection(contours.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetColor(1.0,0.0,0.0)

renderer.AddActor(actor)


renderer.ResetCamera()
renderWindow.Render()
renderWindowInteractor.Start()
