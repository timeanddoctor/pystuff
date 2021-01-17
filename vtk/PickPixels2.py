import vtk
import sys

class vtkImageInteractionCallback(object):
  def __init__(self):
    self.Viewer = None
    self.Picker = None
    self.Annotation = None
  def SetPicker(self, picker):
    self.Picker = picker
  def SetAnnotation(self, annotation):
    self.Annotation = annotation
  def SetViewer(self, viewer):
    self.Viewer = viewer
  def Execute(self, obj, event):
    del obj, event
    interactor = self.Viewer.GetRenderWindow().GetInteractor()
    renderer = self.Viewer.GetRenderer()
    actor = self.Viewer.GetImageActor()
    image = self.Viewer.GetInput()
    style = interactor.GetInteractorStyle()
    self.Picker.Pick(interactor.GetEventPosition()[0],
                     interactor.GetEventPosition()[1], 0.0, renderer)
    path = self.Picker.GetPath() # Get iterator
    validPick = False
    if path is not None:
      # TODO: Use pythonic iteration, need to get iterator for vtkAssemblePath
      path.InitTraversal()
      for i in range(path.GetNumberOfItems()):
        node = path.GetNextNode()
        if actor == node.GetViewProp():
          validPick = True
          break
    if not validPick:
      self.Annotation.SetText(0, "Off Image")
      interactor.Render()
      style.OnMouseMove()
      return
    pos = self.Picker.GetPickPosition()
    axis = self.Viewer.GetSliceOrientation()
    image_coordinates = [0, 0, 0]
    if axis == vtk.vtkImageViewer2.SLICE_ORIENTATION_XZ:
      image_coordinates[0] = int(vtk.vtkMath.Round(pos[0]))
      image_coordinates[1] = int(self.Viewer.GetSlice())
      image_coordinates[2] = int(vtk.vtkMath.Round(pos[2]))
    elif axis == vtk.vtkImageViewer2.SLICE_ORIENTATION_YZ:
      image_coordinates[0] = int(self.Viewer.GetSlice())
      image_coordinates[1] = int(vtk.vtkMath.Round(pos[0]))
      image_coordinates[2] = int(vtk.vtkMath.Round(pos[1]))
    else:
      image_coordinates[0] = int(vtk.vtkMath.Round(pos[0]))
      image_coordinates[1] = int(vtk.vtkMath.Round(pos[1]))
      image_coordinates[2] = int(self.Viewer.GetSlice())
    message = "Location: ( "
    message = message + vtk.vtkVariant(image_coordinates[0]).ToString()
    message = message + ", "
    message = message + vtk.vtkVariant(image_coordinates[1]).ToString()
    message = message + ", "
    message = message + vtk.vtkVariant(image_coordinates[2]).ToString()
    message = message + " )\nValue: ( "

    # We convert everything to float
    message = valueMessage(image, image_coordinates, message)

    self.Annotation.SetText(0, message)
    interactor.Render()
    style.OnMouseMove()

def valueMessage(image, pos, message):
  nComponents = image.GetNumberOfScalarComponents()
  for i in range(nComponents):
    message = message + str(image.GetScalarComponentAsFloat(pos[0], pos[1], pos[2], i))
    if i < nComponents - 1:
      message = message + ", "
  message = message + " )"
  return message

def main(argv):
  imageViewer = vtk.vtkImageViewer2()
  if len(argv) < 2:
    noiseSource = vtk.vtkImageNoiseSource()
    noiseSource.SetWholeExtent(0, 512, 0, 512, 0, 0)
    noiseSource.SetMinimum(0.0)
    noiseSource.SetMaximum(65535.0)

    # cast noise image to unsigned short
    imageCast = vtk.vtkImageCast()
    imageCast.SetInputConnection(noiseSource.GetOutputPort())
    imageCast.SetOutputScalarTypeToUnsignedShort()
    imageCast.Update()
    # connect to image viewer pipeline
    imageViewer.SetInputConnection(imageCast.GetOutputPort())
  else:
    # Parse input argument
    inputFilename = str(argv[1])

    # Read the image
    tiffReader = vtk.vtkTIFFReader()
    if not tiffReader.CanReadFile(inputFilename):
      return
    tiffReader.SetFileName(inputFilename)

    # connect to image viewer pipeline
    imageViewer.SetInputConnection(tiffReader.GetOutputPort())

  # Picker to pick pixels
  propPicker = vtk.vtkPropPicker()
  propPicker.PickFromListOn()

  # Give the picker a prop to pick
  imageActor = imageViewer.GetImageActor()
  propPicker.AddPickList(imageActor)

  # disable interpolation, so we can see each pixel
  imageActor.InterpolateOff()

  # Visualize
  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  imageViewer.SetupInteractor(renderWindowInteractor)
  imageViewer.SetSize(600, 600)

  renderer = imageViewer.GetRenderer()
  renderer.ResetCamera()
  renderer.GradientBackgroundOn()
  renderer.SetBackground(0.6, 0.6, 0.5)
  renderer.SetBackground2(0.3, 0.3, 0.2)

  # Annotate the image with window/level and mouse over pixel
  # information
  cornerAnnotation = vtk.vtkCornerAnnotation()
  cornerAnnotation.SetLinearFontScaleFactor(2)
  cornerAnnotation.SetNonlinearFontScaleFactor(1)
  cornerAnnotation.SetMaximumFontSize(20)
  cornerAnnotation.SetText(0, "Off Image")
  cornerAnnotation.SetText(3, "<window>\n<level>")
  cornerAnnotation.GetTextProperty().SetColor(1, 0, 0)

  imageViewer.GetRenderer().AddViewProp(cornerAnnotation)


  # Callback listens to MouseMoveEvents invoked by the interactor's style
  callback = vtkImageInteractionCallback()
  callback.SetViewer(imageViewer)
  callback.SetAnnotation(cornerAnnotation)
  callback.SetPicker(propPicker)

  # InteractorStyleImage allows for the following controls:
  # 1) middle mouse + move = camera pan
  # 2) left mouse + move = window/level
  # 3) right mouse + move = camera zoom
  # 4) middle mouse wheel scroll = zoom
  # 5) 'r' = reset window/level
  # 6) shift + 'r' = reset camera
  imageStyle = imageViewer.GetInteractorStyle()
  imageStyle.AddObserver('MouseMoveEvent', callback.Execute)

  if len(argv) > 1:
    imageViewer.GetImageActor().GetMapper().SetInputConnection(tiffReader.GetOutputPort())

  renderWindowInteractor.Initialize()
  renderWindowInteractor.Start()

if __name__ == '__main__':
  main(sys.argv)
