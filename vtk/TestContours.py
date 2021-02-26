import vtk
import sys
import os

class vtkSliderCallback(object):
  def __init__(self):
    self._viewer = None
  def SetImageViewer(self,viewer):
    self._viewer = viewer
  def Execute(self, caller, event):
    slider = caller
    sliderRepres = slider.GetRepresentation()
    pos = int(sliderRepres.GetValue())
    self._viewer.SetSlice(pos)

    
def main(argv):
  if os.name == 'nt':
    VTK_DATA_ROOT = "c:/VTK82/build_Release/ExternalData/Testing/"
  else:
    VTK_DATA_ROOT = "/home/jmh/"

  if 0:
    fname = os.path.join(VTK_DATA_ROOT, "Data/headsq/quarter")
    
    v16 = vtk.vtkVolume16Reader()
    v16.SetDataDimensions(64, 64)
    v16.SetDataByteOrderToLittleEndian()
    v16.SetImageRange(1, 93)
    v16.SetDataSpacing(3.2, 3.2, 1.5)
    v16.SetFilePrefix(fname)
    v16.ReleaseDataFlagOn()
    v16.SetDataMask(0x7fff)
    v16.Update()
  else:
    v16 = vtk.vtkMetaImageReader()
    v16.SetFileName("c:/github/fis/data/Abdomen/CT-Abdomen.mhd")
    v16.Update()

  rng = v16.GetOutput().GetScalarRange()

  shifter = vtk.vtkImageShiftScale()
  shifter.SetShift(-1.0*rng[0])
  shifter.SetScale(255.0/(rng[1]-rng[0]))
  shifter.SetOutputScalarTypeToUnsignedChar()
  shifter.SetInputConnection(v16.GetOutputPort())
  shifter.ReleaseDataFlagOff()
  shifter.Update()

 
  ImageViewer = vtk.vtkImageViewer2()
  ImageViewer.SetInputData(shifter.GetOutput())
  ImageViewer.SetColorLevel(127)
  ImageViewer.SetColorWindow(255)

  iren = vtk.vtkRenderWindowInteractor()
  ImageViewer.SetupInteractor(iren)

  ImageViewer.Render()
  ImageViewer.GetRenderer().ResetCamera()

  ImageViewer.Render()    
 
  dims = v16.GetOutput().GetDimensions()

  # Slider screen representation
  SliderRepres = vtk.vtkSliderRepresentation2D()
  _min = ImageViewer.GetSliceMin()
  _max = ImageViewer.GetSliceMax()
  SliderRepres.SetMinimumValue(_min)
  SliderRepres.SetMaximumValue(_max)
  SliderRepres.SetValue(int((_min + _max) / 2))
  SliderRepres.SetTitleText("Slice")
  SliderRepres.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
  SliderRepres.GetPoint1Coordinate().SetValue(0.3, 0.05)
  SliderRepres.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
  SliderRepres.GetPoint2Coordinate().SetValue(0.7, 0.05)
  SliderRepres.SetSliderLength(0.02)
  SliderRepres.SetSliderWidth(0.03)
  SliderRepres.SetEndCapLength(0.01)
  SliderRepres.SetEndCapWidth(0.03)
  SliderRepres.SetTubeWidth(0.005)
  SliderRepres.SetLabelFormat("%3.0lf")
  SliderRepres.SetTitleHeight(0.02)
  SliderRepres.SetLabelHeight(0.02)

  # Slider widget
  SliderWidget = vtk.vtkSliderWidget()
  SliderWidget.SetInteractor(iren)
  SliderWidget.SetRepresentation(SliderRepres)
  SliderWidget.KeyPressActivationOff()
  SliderWidget.SetAnimationModeToAnimate()
  SliderWidget.SetEnabled(True)
 
  SliderCb = vtkSliderCallback()
  SliderCb.SetImageViewer(ImageViewer)
  SliderWidget.AddObserver(vtk.vtkCommand.InteractionEvent, SliderCb.Execute)  

  ImageViewer.SetSlice(int(SliderRepres.GetValue()))

  # Contour representation
  rep = vtk.vtkOrientedGlyphContourRepresentation()
  prop = rep.GetLinesProperty()
  from vtkUtils import renderLinesAsTubes
  from vtk.util.colors import red, green, pink, yellow
  renderLinesAsTubes(prop)
  prop.SetColor(yellow)
  propActive = rep.GetActiveProperty()

  renderLinesAsTubes(propActive)

  propActive.SetColor(green)
  shapeActive = rep.GetActiveCursorShape()

  warp = vtk.vtkWarpVector()
  warp.SetInputData(shapeActive)
  warp.SetInputArrayToProcess(0, 0, 0,
                              vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS,
                              vtk.vtkDataSetAttributes.NORMALS)
  scale = 0.4
  warp.SetScaleFactor(scale)
  warp.Update()
  rep.SetActiveCursorShape(warp.GetOutput())
  
  # Point placer
  imageActorPointPlacer = vtk.vtkImageActorPointPlacer()
  imageActorPointPlacer.SetImageActor(ImageViewer.GetImageActor())
  rep.SetPointPlacer(imageActorPointPlacer)

  # Contour widget
  ContourWidget = vtk.vtkContourWidget()
  ContourWidget.SetRepresentation(rep)
  ContourWidget.SetInteractor(iren)
  ContourWidget.SetEnabled(True)
  ContourWidget.ProcessEventsOn()

  iren.Start()

if __name__ == '__main__':
  main(sys.argv)
  
# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
