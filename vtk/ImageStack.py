import vtk

def CreateColorImage(image, corner, channel):
  image.SetDimensions(10, 10, 1)
  image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 3)

  for x in range(10):
    for y in range(10):
      for rgb in range(3):
        image.SetScalarComponentFromDouble(x,y,0, rgb, 0.0)

  for x in range(corner, corner+3):
    for y in range(corner,corner+3):
      image.SetScalarComponentFromDouble(x,y,0, channel, 255.0)


# Image 1
image1 = vtk.vtkImageData()
CreateColorImage(image1, 1, 0);

imageSliceMapper1 = vtk.vtkImageSliceMapper()
imageSliceMapper1.SetInputData(image1)

imageSlice1 = vtk.vtkImageSlice()
imageSlice1.SetMapper(imageSliceMapper1)
imageSlice1.GetProperty().SetOpacity(.5)

# Image 2
image2 = vtk.vtkImageData()
CreateColorImage(image2, 4, 1)

imageSliceMapper2 = vtk.vtkImageSliceMapper()
imageSliceMapper2.SetInputData(image2)

imageSlice2 = vtk.vtkImageSlice()
imageSlice2.SetMapper(imageSliceMapper2)
imageSlice2.GetProperty().SetOpacity(.5)

# Stack
imageStack = vtk.vtkImageStack()
imageStack.AddImage(imageSlice1)
imageStack.AddImage(imageSlice2)
#imageStack.SetActiveLayer(1)

# Setup renderers
renderer = vtk.vtkRenderer()
renderer.AddViewProp(imageStack)
renderer.ResetCamera()

# Setup render window
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

# Setup render window interactor
renderWindowInteractor = vtk.vtkRenderWindowInteractor()

style = vtk.vtkInteractorStyleImage()

renderWindowInteractor.SetInteractorStyle(style)

# Render and start interaction
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindow.Render()
renderWindowInteractor.Initialize()

renderWindowInteractor.Start()
