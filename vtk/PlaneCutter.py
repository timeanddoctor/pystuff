import vtk

fileName = './FullHead.mhd'
colors = vtk.vtkNamedColors()

renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("Test")

renderWindow.AddRenderer(renderer);
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

reader = vtk.vtkMetaImageReader()
reader.SetFileName(fileName)

imageData = reader.GetOutput()

volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
volumeMapper.SetInputConnection(reader.GetOutputPort())

volumeColor = vtk.vtkColorTransferFunction()
volumeColor.AddRGBPoint(0, 0.0, 0.0, 0.0)
volumeColor.AddRGBPoint(500, 1.0, 0.5, 0.3)
volumeColor.AddRGBPoint(1000, 1.0, 0.5, 0.3)
volumeColor.AddRGBPoint(1150, 1.0, 1.0, 0.9)

volumeScalarOpacity = vtk.vtkPiecewiseFunction()
volumeScalarOpacity.AddPoint(0, 0.00)
volumeScalarOpacity.AddPoint(500, 0.15)
volumeScalarOpacity.AddPoint(1000, 0.15)
volumeScalarOpacity.AddPoint(1150, 0.85)

volumeGradientOpacity = vtk.vtkPiecewiseFunction()
volumeGradientOpacity.AddPoint(0, 0.0)
volumeGradientOpacity.AddPoint(90, 0.5)
volumeGradientOpacity.AddPoint(100, 1.0)

volumeProperty = vtk.vtkVolumeProperty()
volumeProperty.SetColor(volumeColor)
volumeProperty.SetScalarOpacity(volumeScalarOpacity)
volumeProperty.SetGradientOpacity(volumeGradientOpacity)
volumeProperty.SetInterpolationTypeToLinear()
#volumeProperty.ShadeOn()
#volumeProperty.SetAmbient(0.4)
#volumeProperty.SetDiffuse(0.6)
#volumeProperty.SetSpecular(0.2)

volume = vtk.vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volumeProperty)

# Finally, add the volume to the renderer
renderer.AddViewProp(volume)

# Set up an initial view of the volume.  The focal point will be the
# center of the volume, and the camera position will be 400mm to the
# patient's left (which is our right).
camera = renderer.GetActiveCamera()
c = volume.GetCenter()
camera.SetViewUp(0, 0, -1)
camera.SetPosition(c[0], c[1] - 400, c[2])
camera.SetFocalPoint(c[0], c[1], c[2])
camera.Azimuth(30.0)
camera.Elevation(30.0)

planeWidget = vtk.vtkPlaneWidget()
planeWidget.SetInteractor(renderWindow.GetInteractor())
planeWidget.SetInputData(imageData)
planeWidget.SetResolution( 10 )#//That is, set the number of meshes
planeWidget.GetPlaneProperty().SetColor( .2, .8, 0.1 )#//Set color
planeWidget.GetPlaneProperty().SetOpacity( 0.5 )#//Set transparency
planeWidget.GetHandleProperty().SetColor( 0, .4, .7 )#//Set plane vertex color
planeWidget.GetHandleProperty().SetLineWidth( 1.5 )#//Set plane lineweight
planeWidget.NormalToZAxisOn()#//Initial normal direction parallel to Z axis
planeWidget.SetRepresentationToWireframe()#//Planes display as mesh properties
planeWidget.SetCenter( volume.GetCenter() )#//Set plane coordinates
planeWidget.PlaceWidget()#//Lay the plane
planeWidget.On()#//Display plane

# Set a background color for the renderer
renderer.SetBackground(colors.GetColor3d("BkgColor"))
renderWindow.SetSize(640, 480)

def KeyPress(obj, ev):
  key = obj.GetKeySym()
  if (key == 'c'):
    clippingPlane = vtk.vtkPlane()
    planeWidget.GetPlane(clippingPlane)
    volume.GetMapper().AddClippingPlane(clippingPlane)
    volume.Modified()
    renderWindow.Modified()
    renderWindow.Render()

renderWindowInteractor.AddObserver('KeyPressEvent', KeyPress, 1.0)

renderWindowInteractor.Start()

