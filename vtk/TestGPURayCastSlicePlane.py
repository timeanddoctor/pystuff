import vtk

data = vtk.vtkRTAnalyticSource()
data.SetWholeExtent(-100, 100, -100, 100, -100, 100)
data.Update()

mapper = vtk.vtkOpenGLGPUVolumeRayCastMapper()
mapper.SetInputConnection(data.GetOutputPort())
mapper.AutoAdjustSampleDistancesOff()
mapper.SetSampleDistance(0.5)
mapper.SetBlendModeToSlice()

# we also test if slicing works with cropping
mapper.SetCroppingRegionPlanes(0, 100, -100, 100, -100, 100)
mapper.CroppingOn()

colorTransferFunction = vtk.vtkColorTransferFunction()
colorTransferFunction.RemoveAllPoints()
colorTransferFunction.AddRGBPoint(220.0, 0.0, 1.0, 0.0)
colorTransferFunction.AddRGBPoint(150.0, 1.0, 1.0, 1.0)
colorTransferFunction.AddRGBPoint(190.0, 0.0, 1.0, 1.0)

scalarOpacity = vtk.vtkPiecewiseFunction()
scalarOpacity.AddPoint(220.0, 1.0)
scalarOpacity.AddPoint(150.0, 0.2)
scalarOpacity.AddPoint(190.0, 0.6)

slice0 = vtk.vtkPlane()
slice0.SetOrigin(1.0, 0.0, 0.0)
slice0.SetNormal(0.707107, 0.0, 0.707107)

volumeProperty0 = vtk.vtkVolumeProperty()
volumeProperty0.SetInterpolationTypeToLinear()
volumeProperty0.SetColor(colorTransferFunction)
volumeProperty0.SetScalarOpacity(scalarOpacity)
volumeProperty0.SetSliceFunction(slice0)

volume0 = vtk.vtkVolume()
volume0.SetMapper(mapper)
volume0.SetProperty(volumeProperty0)

renderer = vtk.vtkRenderer()
renderer.AddVolume(volume0)

if 1:
    # Add a new volume (view)
    slice1 = vtk.vtkPlane()
    slice1.SetOrigin(1.0, 0.0, 0.0)
    slice1.SetNormal(-0.707107, 0.0, 0.707107)
    
    volumeProperty1 = vtk.vtkVolumeProperty()
    volumeProperty1.SetInterpolationTypeToLinear()
    volumeProperty1.SetColor(colorTransferFunction)
    volumeProperty1.SetScalarOpacity(scalarOpacity)
    volumeProperty1.SetSliceFunction(slice1)
    
    volume1 = vtk.vtkVolume()
    volume1.SetMapper(mapper)
    volume1.SetProperty(volumeProperty1)
    
    renderer.AddVolume(volume1)

renderer.SetBackground(0.0, 0.0, 0.0)
renderer.ResetCamera()

renderWindow = vtk.vtkRenderWindow()
renderWindow.SetSize(600, 600)
renderWindow.AddRenderer(renderer)

style = vtk.vtkInteractorStyleTrackballCamera()

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.SetInteractorStyle(style)

renderWindow.Render()
renderWindowInteractor.Start()

