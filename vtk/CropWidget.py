import vtk

#filename = '/home/jmh/bkmedical/data/CT/Connected.vtp'
filename = '/home/jmh/bkmedical/data/CT/CT-Abdomen.mhd'
reader = vtk.vtkMetaImageReader()
reader.SetFileName(filename)
reader.Update()


mapper = vtk.vtkFixedPointVolumeRayCastMapper()
mapper.SetInputConnection(reader.GetOutputPort())
actor = vtk.vtkActor()
actor.SetMapper(mapper)

colors = vtk.vtkNamedColors()

prop = actor.GetProperty()
prop.SetColor(colors.GetColor3d("Red"))

renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("Test")
renderWindow.SetSize(600, 600)

renderWindow.AddRenderer(renderer);
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

cropWidget = vtk.vtkImageCroppingRegionsWidget()
cropWidget.SetInteractor(renderWindowInteractor)
cropWidget.SetVolumeMapper(mapper)
cropWidget.Modified()
cropWidget.On()

renderWindowInteractor.Initialize()

renderer.SetBackground(.1,.2,.3)
renderer.ResetCamera()


renderWindow.Render()
renderWindowInteractor.Start()
