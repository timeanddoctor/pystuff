import vtk

from vtkUtils import polyInfo

colors = vtk.vtkNamedColors()

def get_program_parameters():
  import argparse
  description = 'Clip polydata interactively.'
  epilogue = ''''''
  parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('filename', help='vessels.vtp')

  args = parser.parse_args()
  return args.filename

ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.SetWindowName("Test")

renWin.AddRenderer(ren);
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

#filename = get_program_parameters()
filename = 'e:/github/fis/data/Abdomen/CT-Abdomen.mhd'

reader = vtk.vtkMetaImageReader()
reader.SetFileName(filename)
reader.Update()

imageData = reader.GetOutput()

volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
volumeMapper.SetInputConnection(reader.GetOutputPort())

colortrans = [[-1024.0,144.0,203.0,255],
              [109.0,255,0,0],
              [144,255,154,73],
              [392,255,255,255],
              [1504,0,0,0]]


alphatrans = [[-1024,0],
              [-724,0],
              [82,1],
              [177,85],
              [543,1],
              [449,2],
              [1504,0]]

volumeColor = vtk.vtkColorTransferFunction()
for i in range(len(colortrans)):
  volumeColor.AddRGBPoint(colortrans[i][0],
                          float(colortrans[i][1])/255.0,
                          float(colortrans[i][2])/255.0,
                          float(colortrans[i][3])/255.0)

volumeScalarOpacity = vtk.vtkPiecewiseFunction()
for i in range(len(alphatrans)):
  volumeScalarOpacity.AddPoint(alphatrans[i][0],
                               alphatrans[i][1]/255.0)

volumeGradientOpacity = vtk.vtkPiecewiseFunction()
volumeGradientOpacity.AddPoint(0, 0.0)
volumeGradientOpacity.AddPoint(90, 0.5)
volumeGradientOpacity.AddPoint(100, 1.0)

volumeProperty = vtk.vtkVolumeProperty()
#transferFunc = vtk.vtkImageData()
#property.SetTransfer2D(transferFunc)
#property.SetTransferMode(property.TF_2D)

volumeProperty.SetColor(volumeColor)
volumeProperty.SetScalarOpacity(volumeScalarOpacity)
#volumeProperty.SetGradientOpacity(volumeGradientOpacity)
volumeProperty.SetInterpolationTypeToLinear()
volumeProperty.ShadeOn()
volumeProperty.SetAmbient(0.2)
volumeProperty.SetDiffuse(0.54)
volumeProperty.SetSpecular(0.72)
volumeProperty.SetSpecularPower(15.0)


volume = vtk.vtkVolume()
volume.SetMapper(volumeMapper)
volume.SetProperty(volumeProperty)


#polyInfo(normals)

#normals.GetOutput().GetPointData().GetArray("Normals")

boxWidget = vtk.vtkBoxWidget2()
boxWidget.SetInteractor(iren)
boxWidget.GetRepresentation().PlaceWidget(imageData.GetBounds())
boxWidget.ScalingEnabledOn()
boxWidget.TranslationEnabledOn()
boxWidget.Modified()
useFunctionCallback = False

class CropObserver(object):
  def __init__(self):
    self.active = True
  def __call__(self, caller, ev):
    # Call crop traget

    pd = vtk.vtkPolyData()
    caller.GetRepresentation().GetPolyData(pd)
    p = pd.GetPoint(0)
    print("P: %f %f %f" % (p[0],p[1],p[2]))

def CropTargetDo():
  print('hello')

def CropTarget(caller, ev):
  print(caller.GetClassName(), "Event Id:", ev)
  CropTargetDo()

if (useFunctionCallback):
  boxWidget.AddObserver('EndInteractionEvent', CropTarget)
else:
  boxWidget.AddObserver('EndInteractionEvent', CropObserver())

# TODO: Add TranslateAction and SelectAction
boxWidget.On()

ren.AddViewProp(volume)
ren.SetBackground(colors.GetColor3d("BkgColor"))

ren.ResetCamera()

iren.Start()
