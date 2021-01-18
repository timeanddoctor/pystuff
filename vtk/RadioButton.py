import vtk


def CreateButtonOff(image):
    white = [255, 255, 255]
    CreateImage(image, white, white)


def CreateButtonOn(image):
    white = [255, 255, 255]
    blue = [0, 0, 255]
    CreateImage(image, white, blue)


def CreateImage(image, color1, color2):
    size = 12
    dims = [size, size, 1]
    lim = size / 3.0

    # Specify the size of the image data
    image.SetDimensions(dims[0], dims[1], dims[2])
    # image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 3)
    arr = vtk.vtkUnsignedCharArray()
    arr.SetNumberOfComponents(3)
    arr.SetNumberOfTuples(dims[0] * dims[1])
    arr.SetName('scalars')

    # Fill the image with
    for y in range(dims[1]):
        for x in range(dims[0]):
            if x >= lim and x < 2 * lim and y >= lim and y < 2 * lim:
                arr.SetTuple3(y*size + x, color2[0], color2[1], color2[2])
            else:
                arr.SetTuple3(y*size + x, color1[0], color1[1], color1[2])

    image.GetPointData().AddArray(arr)
    image.GetPointData().SetActiveScalars('scalars')


# Create some geometry
sphereSource = vtk.vtkSphereSource()
sphereSource.Update()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(sphereSource.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)

# A renderer and render window
renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

# An interactor
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

# Create two images for texture
image1 = vtk.vtkImageData()
image2 = vtk.vtkImageData()
CreateButtonOff(image1)
CreateButtonOn(image2)

# Create the widget and its representation
buttonRepresentation = vtk.vtkTexturedButtonRepresentation2D()
buttonRepresentation.SetNumberOfStates(2)
buttonRepresentation.SetButtonTexture(0, image1)
buttonRepresentation.SetButtonTexture(1, image2)

buttonWidget = vtk.vtkButtonWidget()
buttonWidget.SetInteractor(renderWindowInteractor)
buttonWidget.SetRepresentation(buttonRepresentation)


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


buttonWidget.AddObserver(vtk.vtkCommand.StateChangedEvent, _the_callback)

balloonRep = vtk.vtkBalloonRepresentation()
balloonRep.SetBalloonLayoutToImageRight()

balloonWidget = vtk.vtkBalloonWidget()
balloonWidget.SetInteractor(renderWindowInteractor)
balloonWidget.SetRepresentation(balloonRep)
balloonWidget.AddBalloon(actor, "This is a sphere", None)

# Add the actors to the scene
renderer.AddActor(actor)
renderer.SetBackground(.1, .2, .5)

renderWindow.SetSize(640, 480)
renderWindow.Render()
balloonWidget.EnabledOn()


# Place the widget. Must be done after a render so that the
# viewport is defined.
# Here the widget placement is in normalized display coordinates
upperRight = vtk.vtkCoordinate()
upperRight.SetCoordinateSystemToNormalizedDisplay()
upperRight.SetValue(1.0, 1.0)

bds = [0]*6
sz = 50.0
bds[0] = upperRight.GetComputedDisplayValue(renderer)[0] - sz
bds[1] = bds[0] + sz
bds[2] = upperRight.GetComputedDisplayValue(renderer)[1] - sz
bds[3] = bds[2] + sz
bds[4] = bds[5] = 0.0

# Scale to 1, default is .5
buttonRepresentation.SetPlaceFactor(1)
buttonRepresentation.PlaceWidget(bds)
buttonWidget.On()

# Begin mouse interaction
renderWindowInteractor.Start()