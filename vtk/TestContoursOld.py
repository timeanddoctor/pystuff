#TODO: Reduce number of points using vtkSmoothPolyDataFilter

# Pass it through a vtkDecimatePolylineFilter. It should reduce the
# number of points. You can initialize the contour with those control
# points then.

# Kent Williams from nitrc.org brainstracer. pulling out a node 1 by
# one and determining the change in area of the filled polygon caused
# by node removal.
import vtk
import sys
import os
import math

global ContourWidget
global minArea


def IdsMinusThisPoint(ids, PointCount, i):
  k = 0

  for j in range(PointCount):
    if ( j != i ):
      ids.SetId(k, int(j))
      k = k + 1
  # leaving off first point? 1 is index of first point
  # in the reduced polygon
  print("Number of IDs")
  print(ids.GetNumberOfIds())
  print(k)
  if i == 0:
    ids.SetId(k, int(1))
  else:
    ids.SetId(k, int(0))

def ConvertPointSequenceToPolyData(inPts,
                                   closed):
  npts = inPts.GetNumberOfPoints()

  if ( npts < 2 ):
    return

  p0 = inPts.GetPoint(0)
  p1 = inPts.GetPoint( npts - 1)

  if ( p0[0] == p1[0] and p0[1] == p1[1] and p0[2] == p1[2] and closed == 1):
    npts = npts - 1

  temp = vtk.vtkPoints()
  temp.SetNumberOfPoints( npts )
  for i in range(npts):
    temp.SetPoint( i, inPts.GetPoint( i ) )

  cells = vtk.vtkCellArray()
  cells.Allocate( cells.EstimateSize( npts + closed, 2 ) )
  cells.InsertNextCell( npts + closed )

  for i in range(npts):
    cells.InsertCellPoint( i )

  if (closed == 1):
    cells.InsertCellPoint( 0 )

  outPoly = vtk.vtkPolyData()
  outPoly.SetPoints( temp )
  temp = None #.Delete()
  outPoly.SetLines( cells )
  cells = None #.Delete()
  return outPoly

def PolyDataArea(pd):
  assert(pd.GetNumberOfLines() == 1)
  idList = vtk.vtkIdList()
  pd.GetLines().InitTraversal()
  pd.GetLines().GetNextCell(idList)
  npts = idList.GetNumberOfIds()
  normal = [0.0, 0.0, 0.0]
  return vtk.vtkPolygon.ComputeArea(pd.GetPoints(),
                                    npts,
                                    idList,
                                    normal)

def PointsArea(points):
  numPoints = points.GetNumberOfPoints()

  ids = vtk.vtkIdList()
  ids.SetNumberOfIds(numPoints + 1)

  for i in range(numPoints):
    ids.SetId(i, int(i))

  ids.SetId(numPoints, int(0))
  normal = [0.0, 0.0, 0.0]
  rval = vtk.vtkPolygon.ComputeArea(points, numPoints, ids, normal)
  return rval


def callback(obj, ev):
  if obj.GetWidgetState() == vtk.vtkContourWidget.Manipulate:
    # Get contours from widget
    pd = ContourWidget.GetContourRepresentation().GetContourRepresentationAsPolyData()

    # TODO: Initialize using pd3
    pd3 = vtk.vtkPolyData()
    if ( pd.GetPoints().GetNumberOfPoints() > 0 ):
      print('lort')
      pts = pd.GetPoints()
      zPos = 0.0#origin[2] + iSlice * spacing[2]
      for j in range(pd.GetNumberOfPoints()):
        point = pts.GetPoint(j)
        point = (point[0], point[1], zPos)
        pts.SetPoint(j, point)

      lines = pd.GetLines()
      points = vtk.vtkIdList()
      pd.GetLines().InitTraversal()
      while lines.GetNextCell(points):
        numPoints = points.GetNumberOfIds()
        print("Line has " + str(numPoints) + " points.")
        tmpPoints = vtk.vtkPoints()
        for j in range(numPoints):
          point = pts.GetPoint(points.GetId(j))
          tmpPoints.InsertNextPoint(point)
        if ( PointsArea(tmpPoints) < minArea ):
          tmpPoints = None
          continue
        pd2 = vtk.vtkPolyData()
        pd2 = ConvertPointSequenceToPolyData(tmpPoints, 1)
        #Cull(pd2, pd3)
    print(pd.GetNumberOfPoints())
    print(pd3.GetNumberOfPoints())

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
    v16 = vtk.vtkMetaImageReader()
    v16.SetFileName("/home/jmh/github/fis/data/Abdomen/CT-Abdomen.mhd")
    v16.Update()
  elif 0:
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
  elif 1:
    v16 = vtk.vtkMetaImageReader()
    v16.SetFileName("e:/analogic/fis/data/Abdomen/CT-Abdomen.mhd")
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

  global minArea
  spacing = v16.GetOutput().GetSpacing()
  minArea = ( spacing[0] * spacing[1] ) / 0.1

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

  # Contour representation - responsible for placement of points, calculation of lines and contour manipulation
  global rep
  rep = vtk.vtkOrientedGlyphContourRepresentation()
  # vtkContourRepresentation has GetActiveNodeWorldPostion/Orientation
  rep.GetProperty().SetOpacity(0) #1
  prop = rep.GetLinesProperty()
  from vtkUtils import renderLinesAsTubes
  from vtk.util.colors import red, green, pink, yellow
  renderLinesAsTubes(prop)
  prop.SetColor(yellow)
  propActive = rep.GetActiveProperty()
  #propActive.SetOpacity(0) # 2
  
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

  # Use vtkContourTriangulator to fill contours

  # Point placer
  imageActorPointPlacer = vtk.vtkImageActorPointPlacer()
  imageActorPointPlacer.SetImageActor(ImageViewer.GetImageActor())
  rep.SetPointPlacer(imageActorPointPlacer)

  global ContourWidget
  # Contour widget - has a  vtkWidgetEventTranslator which translate events to vtkContourWidget events
  ContourWidget = vtk.vtkContourWidget()
  ContourWidget.SetRepresentation(rep)
  ContourWidget.SetInteractor(iren)
  ContourWidget.SetEnabled(True)
  ContourWidget.ProcessEventsOn()
  ContourWidget.ContinuousDrawOn()

  # Can be Initialize() using polydata

  # Override methods that returns display position to get an overlay
  # (display postions) instead of computing it from world position and
  # the method BuildLines to interpolate using display positions
  # instead of world positions

  # Thinning of contour control points
  # AddFinalPointAction
  ContourWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent, callback)



  if 0:
    # TODO: Make interior transparent
    contour = ContourWidget.GetContourRepresentation().GetContourRepresentationAsPolyData()
    tc = vtk.vtkContourTriangulator()
    tc.SetInputData(contour)
    tc.Update()

    # Extrusion towards camera
    extruder = vtk.vtkLinearExtrusionFilter()
    extruder.CappingOn()
    extruder.SetScalaFactor(1.0)
    extruder.SetInputData(tc.GetOutput())
    extruder.SetVector(0,0,1.0)
    extruder.SetExtrusionTypeToNormalExtrusion()
    
    polyMapper = vtk.vtkPolyMapper()
    polyMapper.SetInputConnection(extruder.GetOutputPort())
    polyMapper.ScalarVisibilityOn()
    polyMapper.Update()
    polyActor = vtk.vtkActor()
    polyActor.SetMapper(polyMapper)
    prop = polyActor.GetProperty()
    prop.SetColor(0,1,0)
    #prop.SetRepresentationToWireframe()
    renderer.AddActor(polyActor)
    renderer.GetRenderWindow().Render()
  


  iren.Start()

if __name__ == '__main__':
  global rep
  main(sys.argv)
  
# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
