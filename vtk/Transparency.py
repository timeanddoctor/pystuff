import vtk

reader = vtk.vtkPNGReader()
reader.SetFileName('./fixed.png')
reader.Update()

image = reader.GetOutput()

# Create a mask - half of the image should be transparent and the other half opaque
maskImage = vtk.vtkImageData()
extent = image.GetExtent()
maskImage.SetExtent(extent)

maskImage.AllocateScalars(vtk.VTK_DOUBLE,1)
for y in range(extent[2], extent[3]):
  for x in range(extent[0], extent[1]):
    if (y > (extent[3]-extent[2])/2.0):
      maskImage.SetScalarComponentFromDouble(x,y,0,0,0.0)
    else:
      maskImage.SetScalarComponentFromDouble(x,y,0,0,1.0)

lookupTable = vtk.vtkLookupTable()
lookupTable.SetNumberOfTableValues(2)
lookupTable.SetRange(0.0,1.0)
lookupTable.SetTableValue( 0, 0.0, 0.0, 0.0, 0.0 ) #label 0 is transparent
lookupTable.SetTableValue( 1, 0.0, 1.0, 0.0, 1.0 ) #label 1 is opaque and green
lookupTable.Build()

mapTransparency = vtk.vtkImageMapToColors()
mapTransparency.SetLookupTable(lookupTable)
mapTransparency.PassAlphaToOutputOn()
mapTransparency.SetInputData(maskImage)

  # Create actors
imageActor = vtk.vtkImageActor()
imageActor.GetMapper().SetInputData(image)

maskActor = vtk.vtkImageActor()
maskActor.GetMapper().SetInputConnection(mapTransparency.GetOutputPort())

# Visualize
renderer = vtk.vtkRenderer()
renderer.AddActor(imageActor)
renderer.AddActor(maskActor)
renderer.ResetCamera()

renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
style = vtk.vtkInteractorStyleImage()

renderWindowInteractor.SetInteractorStyle(style)

renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.Initialize()
renderWindowInteractor.Start()
