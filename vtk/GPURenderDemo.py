# Basically, once the vtkPlane and vtkClipVolume created, calling the
# AddClippingPlane(plane) method of the vtkVolumeRayCastMapper object
# made the trick.

#I finally used the vtkImplicitPlaneWidget class, and made the
#vtkClipVolume object's output be its input.


# See GPURenderDemo
import vtk
import sys

VTI_FILETYPE = 1
MHA_FILETYPE = 2

class vtkBoxWidgetCallback(object):
  def __init__(self):
    self.Mapper = None
  def onExecute(self, caller, ev):
    widget = caller
    if self.Mapper is not None:
      planes = vtk.vtkPlanes()
      widget.GetPlanes(planes)
      self.Mapper.SetClippingPlanes(planes)
  def SetMapper(self, mapper):
    self.Mapper = mapper

def PrintUsage():
  print("Usage: ")
  print("  GPURenderDemo <options>")
  print("where options may include: ")
  print("  -DICOM <directory>")
  print("  -VTI <filename>")
  print("  -MHA <filename>")
  print("  -DependentComponents")
  print("  -Clip")
  print("  -MIP <window> <level>")
  print("  -CompositeRamp <window> <level>")
  print("  -CompositeShadeRamp <window> <level>")
  print("  -CT_Skin")
  print("  -CT_Bone")
  print("  -CT_Muscle")
  print("  -FrameRate <rate>")
  print("  -DataReduction <factor>")
  print("")
  sys.stdout.write("You must use either the -DICOM option to specify the directory where")
  sys.stdout.write("the data is located or the -VTI or -MHA option to specify the path of a .vti file."
      )
  sys.stdout.write("By default, the program assumes that the file has independent components,\n")
  sys.stdout.write("use -DependentComponents to specify that the file has dependent components.\n")
  sys.stdout.write("Use the -Clip option to display a cube widget for clipping the volume.\n")
  sys.stdout.write("Use the -FrameRate option with a desired frame rate (in frames per second)\n")
  sys.stdout.write("which will control the interactive rendering rate.\n")
  sys.stdout.write("Use the -DataReduction option with a reduction factor (greater than zero and\n")
  sys.stdout.write("less than one) to reduce the data before rendering.\n")
  sys.stdout.write("Use one of the remaining options to specify the blend function\n")
  sys.stdout.write("and transfer functions. The -MIP option utilizes a maximum intensity\n")
  sys.stdout.write("projection method, while the others utilize compositing. The\n")
  sys.stdout.write("-CompositeRamp option is unshaded compositing, while the other\n")
  sys.stdout.write("compositing options employ shading.\n")
  sys.stdout.write("Note: MIP, CompositeRamp, CompositeShadeRamp, CT_Skin, CT_Bone,\n")
  sys.stdout.write("and CT_Muscle are appropriate for DICOM data. MIP, CompositeRamp,\n")
  sys.stdout.write("and RGB_Composite are appropriate for RGB data.\n")
  sys.stdout.write("Example: GPURenderDemo -DICOM CTNeck -MIP 4096 1024\n")
  sys.stdout.write("\n")

def main():
  count = 1
  dirname = None
  opacityWindow = 4096.0
  opacityLevel = 2048.0
  blendType = 0
  clip = 0
  reductionFactor = 1.0
  frameRate = 10.0
  fileName = None
  fileType = 0

  independentComponents = True

  while (count < len(sys.argv)):
    if (sys.argv[count] == "?"):
      PrintUsage()
      sys.exit(0)
    elif (sys.argv[count] == "-DICOM"):
      dirname = sys.argv[count+1]
      count += 2
    elif (sys.argv[count] == "-VTI"):
      fileType = VTI_FILETYPE
      fileName = sys.argv[count+1]
      count += 2
    elif (sys.argv[count] == "-MHA"):
      fileType = MHA_FILETYPE
      fileName = sys.argv[count+1]
      count += 2
    elif (sys.argv[count] == "-Clip"):
      clip = 1
      count += 1
    elif (sys.argv[count] == "-MIP"):
      opacityWindow = float(sys.argv[count + 1])
      opacityLevel = float(sys.argv[count + 2])
      blendType = 0
      count += 3
    elif (sys.argv[count] == "-CompositeRamp"):
      opacityWindow = float(sys.argv[count + 1])
      opacityLevel = float(sys.argv[count + 2])
      blendType = 1
      count += 3
    elif (sys.argv[count] == "-CompositeShadeRamp"):
      opacityWindow = float(sys.argv[count + 1])
      opacityLevel = float(sys.argv[count + 2])
      blendType = 2
      count += 3
    elif (sys.argv[count] == "-CT_Skin"):
      blendType = 3
      count += 1
    elif (sys.argv[count] == "-CT_Bone"):
      blendType = 4
      count += 1
    elif (sys.argv[count] == "-CT_Muscle"):
      blendType = 5
      count += 1
    elif (sys.argv[count] == "-RGB_Composite"):
      blendType = 6
      count += 1
    elif (sys.argv[count] == "-FrameRate"):
      frameRate = float(sys.argv[count + 1])
      if (frameRate < 0.01 or frameRate > 60.0):
        print("Invalid frame rate - use a number between 0.01 and 60.0")
        print("Using default frame rate of 10 frames per second.")
        frameRate = 10.0
      count += 2
    elif (sys.argv[count] == "-ReductionFactor"):
      reductionFactor = float(sys.argv[count + 1])
      if (reductionFactor <= 0.0 or reductionFactor >= 1.0):
        print("Invalid reduction factor - use a number between 0 and 1 (exclusive)")
        print("Using the default of no reduction.")
        reductionFactor = 1.0
      count += 2
    elif (sys.argv[count] == "-DependentComponents"):
      independentComponents = false
      count += 1
    else:
      print("Unrecognized option: %s\n" % (sys.argv[count]))
      PrintUsage()
      sys.exit(-1)
  if (dirname is None and fileName is None):
    print("Error: you must specify a directory of DICOM data or a .vti file or a .mha!")
    PrintUsage()
    sys.exit(-1)

  # Create the renderer, render window and interactor
  renderer = vtk.vtkRenderer()
  renWin = vtk.vtkRenderWindow()
  renWin.AddRenderer(renderer)

  # Connect it all. Note that funny arithematic on the
  # SetDesiredUpdateRate - the vtkRenderWindow divides it
  # allocated time across all renderers, and the renderer
  # divides it time across all props. If clip is
  # true then there are two props
  iren = vtk.vtkRenderWindowInteractor()
  iren.SetRenderWindow(renWin)
  iren.SetDesiredUpdateRate(frameRate / (1.0 + clip))

  iren.GetInteractorStyle().SetDefaultRenderer(renderer)

  # Read the data
  reader = None
  _input = None
  if (dirname):
    dicomReader = vtk.vtkDICOMImageReader()
    dicomReader.SetDirectoryName(dirname)
    dicomReader.Update()
    _input = dicomReader.GetOutput()
    reader = dicomReader
  elif (fileType == VTI_FILETYPE):
    xmlReader = vtk.vtkXMLImageDataReader()
    xmlReader.SetFileName(fileName)
    xmlReader.Update()
    _input = xmlReader.GetOutput()
    reader = xmlReader
  elif (fileType == MHA_FILETYPE):
    metaReader = vtk.vtkMetaImageReader()
    metaReader.SetFileName(fileName)
    metaReader.Update()
    _input = metaReader.GetOutput()
    reader = metaReader
  else:
    print("Error! Not VTI or MHA!")
    exit(-1)

  # Verify that we actually have a volume
  dim = _input.GetDimensions()
  if (dim[0] < 2 or dim[1] < 2 or dim[2] < 2):
    print("Error loading data!")
    sys.exit(-1)

  resample = vtk.vtkImageResample()
  if (reductionFactor < 1.0):
    resample.SetInputConnection(reader.GetOutputPort())
    resample.SetAxisMagnificationFactor(0, reductionFactor)
    resample.SetAxisMagnificationFactor(1, reductionFactor)
    resample.SetAxisMagnificationFactor(2, reductionFactor)

  # Create our volume and mapper
  volume = vtk.vtkVolume()
  mapper = vtk.vtkSmartVolumeMapper()

  # Add a box widget if the clip option was selected
  box = vtk.vtkBoxWidget()
  if (clip):
    box.SetInteractor(iren)
    box.SetPlaceFactor(1.01)
    if (reductionFactor < 1.0):
      box.SetInputConnection(resample.GetOutputPort())
    else:
      box.SetInputData(_input)

    box.SetDefaultRenderer(renderer)
    box.InsideOutOn()
    box.PlaceWidget()
    callback = vtkBoxWidgetCallback()
    callback.SetMapper(mapper)
    box.AddObserver(vtk.vtkCommand.InteractionEvent, callback.onExecute)
    box.EnabledOn()
    box.GetSelectedFaceProperty().SetOpacity(0.0)

  if (reductionFactor < 1.0):
    mapper.SetInputConnection(resample.GetOutputPort())
  else:
    mapper.SetInputConnection(reader.GetOutputPort())

  # Set the sample distance on the ray to be 1/2 the average spacing
  spacing = None
  if (reductionFactor < 1.0):
    spacing = resample.GetOutput().GetSpacing()
  else:
    spacing = _input.GetSpacing()

  #  mapper.SetSampleDistance( (spacing[0]+spacing[1]+spacing[2])/6.0 )
  #  mapper.SetMaximumImageSampleDistance(10.0)

  # Create our transfer function
  colorFun = vtk.vtkColorTransferFunction()
  opacityFun = vtk.vtkPiecewiseFunction()

  # Create the property and attach the transfer functions
  _property = vtk.vtkVolumeProperty()
  _property.SetIndependentComponents(independentComponents)
  _property.SetColor(colorFun)
  _property.SetScalarOpacity(opacityFun)
  _property.SetInterpolationTypeToLinear()

  # connect up the volume to the property and the mapper
  volume.SetProperty(_property)
  volume.SetMapper(mapper)

  # Depending on the blend type selected as a command line option,
  # adjust the transfer function
  if (blendType == 0):
    # MIP
    # Create an opacity ramp from the window and level values.
    # Color is white. Blending is MIP.
    colorFun.AddRGBSegment(0.0, 1.0, 1.0, 1.0, 255.0, 1.0, 1.0, 1.0)
    opacityFun.AddSegment(
        opacityLevel - 0.5 * opacityWindow, 0.0, opacityLevel + 0.5 * opacityWindow, 1.0)
    mapper.SetBlendModeToMaximumIntensity()
  elif blendType == 1:
    # CompositeRamp
    # Create a ramp from the window and level values. Use compositing
    # without shading. Color is a ramp from black to white.
    colorFun.AddRGBSegment(opacityLevel - 0.5 * opacityWindow, 0.0, 0.0, 0.0,
      opacityLevel + 0.5 * opacityWindow, 1.0, 1.0, 1.0)
    opacityFun.AddSegment(
      opacityLevel - 0.5 * opacityWindow, 0.0, opacityLevel + 0.5 * opacityWindow, 1.0)
    mapper.SetBlendModeToComposite()
    _property.ShadeOff()
  elif blendType == 2:
    # CompositeShadeRamp
    # Create a ramp from the window and level values. Use compositing
    # with shading. Color is white.
    colorFun.AddRGBSegment(0.0, 1.0, 1.0, 1.0, 255.0, 1.0, 1.0, 1.0)
    opacityFun.AddSegment(
      opacityLevel - 0.5 * opacityWindow, 0.0, opacityLevel + 0.5 * opacityWindow, 1.0)
    mapper.SetBlendModeToComposite()
    _property.ShadeOn()

  elif blendType == 3:
    # CT_Skin
    # Use compositing and functions set to highlight skin in CT data
    # Not for use on RGB data
    colorFun.AddRGBPoint(-3024, 0, 0, 0, 0.5, 0.0)
    colorFun.AddRGBPoint(-1000, .62, .36, .18, 0.5, 0.0)
    colorFun.AddRGBPoint(-500, .88, .60, .29, 0.33, 0.45)
    colorFun.AddRGBPoint(3071, .83, .66, 1, 0.5, 0.0)

    opacityFun.AddPoint(-3024, 0, 0.5, 0.0)
    opacityFun.AddPoint(-1000, 0, 0.5, 0.0)
    opacityFun.AddPoint(-500, 1.0, 0.33, 0.45)
    opacityFun.AddPoint(3071, 1.0, 0.5, 0.0)

    mapper.SetBlendModeToComposite()
    _property.ShadeOn()
    _property.SetAmbient(0.1)
    _property.SetDiffuse(0.9)
    _property.SetSpecular(0.2)
    _property.SetSpecularPower(10.0)
    _property.SetScalarOpacityUnitDistance(0.8919)

  elif blendType == 4:
    # CT_Bone
    # Use compositing and functions set to highlight bone in CT data
    # Not for use on RGB data
    colorFun.AddRGBPoint(-3024, 0, 0, 0, 0.5, 0.0)
    colorFun.AddRGBPoint(-16, 0.73, 0.25, 0.30, 0.49, .61)
    colorFun.AddRGBPoint(641, .90, .82, .56, .5, 0.0)
    colorFun.AddRGBPoint(3071, 1, 1, 1, .5, 0.0)

    opacityFun.AddPoint(-3024, 0, 0.5, 0.0)
    opacityFun.AddPoint(-16, 0, .49, .61)
    opacityFun.AddPoint(641, .72, .5, 0.0)
    opacityFun.AddPoint(3071, .71, 0.5, 0.0)

    mapper.SetBlendModeToComposite()
    _property.ShadeOn()
    _property.SetAmbient(0.1)
    _property.SetDiffuse(0.9)
    _property.SetSpecular(0.2)
    _property.SetSpecularPower(10.0)
    _property.SetScalarOpacityUnitDistance(0.8919)

  elif blendType == 5:
    # CT_Muscle
    # Use compositing and functions set to highlight muscle in CT data
    # Not for use on RGB data
    colorFun.AddRGBPoint(-3024, 0, 0, 0, 0.5, 0.0)
    colorFun.AddRGBPoint(-155, .55, .25, .15, 0.5, .92)
    colorFun.AddRGBPoint(217, .88, .60, .29, 0.33, 0.45)
    colorFun.AddRGBPoint(420, 1, .94, .95, 0.5, 0.0)
    colorFun.AddRGBPoint(3071, .83, .66, 1, 0.5, 0.0)

    opacityFun.AddPoint(-3024, 0, 0.5, 0.0)
    opacityFun.AddPoint(-155, 0, 0.5, 0.92)
    opacityFun.AddPoint(217, .68, 0.33, 0.45)
    opacityFun.AddPoint(420, .83, 0.5, 0.0)
    opacityFun.AddPoint(3071, .80, 0.5, 0.0)

    mapper.SetBlendModeToComposite()
    _property.ShadeOn()
    _property.SetAmbient(0.1)
    _property.SetDiffuse(0.9)
    _property.SetSpecular(0.2)
    _property.SetSpecularPower(10.0)
    _property.SetScalarOpacityUnitDistance(0.8919)
  elif blendType == 6:
    # RGB_Composite
    # Use compositing and functions set to highlight red/green/blue regions
    # in RGB data. Not for use on single component data
    opacityFun.AddPoint(0, 0.0)
    opacityFun.AddPoint(5.0, 0.0)
    opacityFun.AddPoint(30.0, 0.05)
    opacityFun.AddPoint(31.0, 0.0)
    opacityFun.AddPoint(90.0, 0.0)
    opacityFun.AddPoint(100.0, 0.3)
    opacityFun.AddPoint(110.0, 0.0)
    opacityFun.AddPoint(190.0, 0.0)
    opacityFun.AddPoint(200.0, 0.4)
    opacityFun.AddPoint(210.0, 0.0)
    opacityFun.AddPoint(245.0, 0.0)
    opacityFun.AddPoint(255.0, 0.5)

    mapper.SetBlendModeToComposite()
    _property.ShadeOff()
    _property.SetScalarOpacityUnitDistance(1.0)
  else:
    print("Unknown blend type.")

  # Set the default window size
  renWin.SetSize(600, 600)
  renWin.Render()

  # Add the volume to the scene
  renderer.AddVolume(volume)

  renderer.ResetCamera()

  # interact with data
  renWin.Render()

  iren.Start()

  return 0
    
if __name__ == "__main__":
  main()
