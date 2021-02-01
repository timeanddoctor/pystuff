import vtk
from vtk.util import numpy_support

reader = vtk.vtkPNGReader()
reader.SetFileName('./test.png')

viewer = vtk.vtkImageViewer2()
interactor = vtk.vtkRenderWindowInteractor()
viewer.SetupInteractor(interactor)


import numpy as np
arr = np.zeros((40,40,3),dtype=np.uint8)
arr[:,:,0] = 255

image = vtk.vtkImageData()
image.SetDimensions(40,40,1)

def try_callback(func, *args):
    """Wrap a given callback in a try statement."""
    import logging
    try:
        func(*args)
    except Exception as e:
        logging.warning('Encountered issue in callback: {}'.format(e))
    return


def callback(val):
    print("Button pressed!")


def _the_callback(widget, event):
    value = widget.GetRepresentation().GetState()
    if hasattr(callback, '__call__'):
        try_callback(callback, value)
    return

def Create2DImage(dims, rgba):
  image = vtk.vtkImageData()
  image.SetDimensions(dims[0],dims[1],1)
  arr = np.zeros((dims[0],dims[1],4),dtype=np.uint8)
  arr[:,:,:] = rgba
  # HACK
  #arr[20,:,:]
  colors = numpy_support.numpy_to_vtk(arr.ravel(), deep=False,
                                      array_type=vtk.VTK_UNSIGNED_CHAR)
  colors.SetNumberOfComponents(len(rgba))
  colors.SetNumberOfTuples(image.GetNumberOfPoints())
  image.GetPointData().SetScalars(colors)
  return image

def CreateCornerButtonImage(letter):
  freeType = vtk.vtkFreeTypeTools.GetInstance()
  textProperty = vtk.vtkTextProperty()
  textProperty.SetColor(1.0, 0.0, 0.0) # red
  textProperty.SetFontSize(16)
  #textProperty.SetVerticalJustificationToCentered()
  #textProperty.SetJustificationToCentered()
  textProperty.BoldOn()
  textProperty.Modified()
  
  textImage = vtk.vtkImageData()
  #textImage.SetNumberOfComponents(4)
  textImage.SetDimensions(40,40,1)
  dpi = 200
  sz = [0, 0]
  freeType.RenderString(textProperty, letter, dpi, textImage, sz)
  #textImage.SetExtent(0, sz[0], 0, sz[1], 0, 0)
  return textImage

viewer.SetInputConnection(reader.GetOutputPort())
#viewer.SetInputData(image)
viewer.GetRenderWindow().SetSize(640, 480)

viewer.Render()

buttonRepresentation = vtk.vtkTexturedButtonRepresentation2D()
buttonRepresentation.SetNumberOfStates(3)
#buttonRepresentation.SetButtonTexture(0, Create2DImage([40,40], [255,0,0,255]))

reader = vtk.vtkPNGReader()
reader.SetFileName('./S.png')
reader.Update()
img0 = reader.GetOutput()
buttonRepresentation.SetButtonTexture(0,img0)
reader = vtk.vtkPNGReader()
reader.SetFileName('./C.png')
reader.Update()
img1 = reader.GetOutput()
buttonRepresentation.SetButtonTexture(1, img1)
reader = vtk.vtkPNGReader()
reader.SetFileName('./A.png')
reader.Update()
img2 = reader.GetOutput()
buttonRepresentation.SetButtonTexture(2, img2)

buttonWidget = vtk.vtkButtonWidget()
buttonWidget.SetInteractor(interactor)
buttonWidget.SetRepresentation(buttonRepresentation)
buttonWidget.AddObserver(vtk.vtkCommand.StateChangedEvent, _the_callback)

upperRight = vtk.vtkCoordinate()
upperRight.SetCoordinateSystemToNormalizedDisplay()
upperRight.SetValue(1.0, 1.0)

renderer = viewer.GetRenderer()
bds = [0]*6
sz = 40.0
bds[0] = upperRight.GetComputedDisplayValue(renderer)[0] - sz
bds[1] = bds[0] + sz
bds[2] = upperRight.GetComputedDisplayValue(renderer)[1] - sz
bds[3] = bds[2] + sz
bds[4] = bds[5] = 0.0

# Alignment of text

# Scale to 1, default is .5
buttonRepresentation.SetPlaceFactor(1)
buttonRepresentation.PlaceWidget(bds)
buttonWidget.On()


interactor.Initialize()
interactor.Start()

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
