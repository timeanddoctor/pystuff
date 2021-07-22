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

_slice = vtk.vtkPlane()
_slice.SetOrigin(1.0, 0.0, 0.0)
_slice.SetNormal(0.707107, 0.0, 0.707107)

volumeProperty = vtk.vtkVolumeProperty()
volumeProperty.SetInterpolationTypeToLinear()
volumeProperty.SetColor(colorTransferFunction)
volumeProperty.SetScalarOpacity(scalarOpacity)
volumeProperty.SetSliceFunction(_slice)

volume = vtk.vtkVolume()
volume.SetMapper(mapper)
volume.SetProperty(volumeProperty)

renderer = vtk.vtkRenderer()
renderer.AddVolume(volume)
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

