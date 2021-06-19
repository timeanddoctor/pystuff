import vtk
import numpy as np
import math

colors = vtk.vtkNamedColors()

from probe import CreateOutline9076
from utils import renderLinesAsTubes, AxesToTransform

def GetAxis(transform, index):
  """
  Get any axis from transformation
  """
  mat = transform.GetMatrix()
  return (mat.GetElement(0,index), mat.GetElement(1,index), mat.GetElement(2,index))

def createPerpendicular(vector3d):
  """
  Create vector in 3D that is perpendicular to input
  """
  values = np.fabs(np.r_[vector3d[0],vector3d[1],vector3d[2]])
  inx = values.argsort()
  tmp = vtk.vtkVector3d()

  # Swap the two largest component and add a sign
  tmp[inx[-1]] = -vector3d[inx[-2]]
  tmp[inx[-2]] =  vector3d[inx[-1]]
  tmp[inx[-3]] =  vector3d[inx[-3]]

  # Cross-product with the input
  result = vtk.vtkVector3d()
  vtk.vtkMath.Cross(vector3d, tmp, result)

  # Return unit vector
  norm = result.Normalize()
  return result

def addOrientationWidget(iren):
  """
  Add orientation widget to the interactor iren
  """
  # Orientation widget
  axesActor = vtk.vtkAxesActor()
  axes = vtk.vtkOrientationMarkerWidget()
  axes.SetOrientationMarker( axesActor)
  axes.SetInteractor( iren )
  axes.SetViewport( 0.8, 0.0, 1.0, 0.2)
  axes.EnabledOn()
  axes.InteractiveOn()

def createAxesActor(length=20.0):
  """
  Create axes actor with variable lengths of axes. The actor is made
  pickable. If a prop picker is used the axes(this prop) can be picked
  """
  axes = vtk.vtkAxesActor()
  axes_length = length
  axes_label_font_size = np.int16(12)
  axes.SetTotalLength(axes_length, axes_length, axes_length)
  axes.SetCylinderRadius(0.01)
  axes.SetShaftTypeToCylinder()
  axes.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
  axes.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
  axes.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
  axes.GetXAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
  axes.GetYAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
  axes.GetZAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
  prop = axes.GetXAxisShaftProperty()
  renderLinesAsTubes(prop)
  prop.SetEdgeColor(0.9,0.0,0.0)
  prop = axes.GetYAxisShaftProperty()
  renderLinesAsTubes(prop)
  prop.SetEdgeColor(0.0,0.9,0.0)
  prop = axes.GetZAxisShaftProperty()
  renderLinesAsTubes(prop)
  prop.SetEdgeColor(0.0,0.0,0.9)

  axes.PickableOn()
  return axes

def createOutline(depth=80.0, transform=None):
  """
  Create outline of 9076. The coordinates are such that
  the z-direction is into tissue and the center-of-curvature
  is at (0,0,0)

  Dimensions are given in [mm]
  """
  outline = CreateOutline9076(depth=depth)
  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputData(outline)
  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  if transform is not None:
    actor.SetUserTransform(transform)
  prop = actor.GetProperty()
  prop.SetLineWidth(4)
  renderLinesAsTubes(prop)
  return actor

def createNeedle(length=30.0, transform=vtk.vtkTransform()):
  """
  Create a needle with a given length. The needle is pointing from (0,0,0)
  into the z-direction.

  Return an actor for the needle and a filter, which can be used for
  retrieveing the transformed data to be used for e.g. an intersection
  """
  lineSource = vtk.vtkLineSource()
  lineSource.SetPoint1(0.0,0.0,0.0)
  lineSource.SetPoint2(0.0,0.0,length)
  lineSource.SetResolution(100)
  lineSource.Update()

  filt = vtk.vtkTransformPolyDataFilter()
  filt.SetInputConnection(lineSource.GetOutputPort())
  filt.SetTransform(transform)
  filt.Update()
  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputConnection(filt.GetOutputPort())

  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  prop = actor.GetProperty()
  prop.SetLineWidth(6)
  prop.SetColor(colors.GetColor3d("Peacock"))
  renderLinesAsTubes(prop)
  return actor, filt

def createNeedleReference(trans,
                          imgX=0.0,
                          imgZ=70.00,
                          angleZenith=0.0,
                          angleAz=0.0,
                          distance=50.0):
  """
  Create a need intersection the scan plane

  Input:
    transat: array nominal from world-coordinates. Array nominal has origin at center of curvature
    imgX: x-coordinate of intersection
    imgZ: z-coordinate of intersection
    angleZenith: angle from normal incidence. 0 means normal incidence
    angleAz: azimuthal angle.
  """
  print("imgX: " + str(imgX))
  print("imgZ: " + str(imgZ))
  trans.Update()

  worldFromNominal = trans

  intersection = vtk.vtkVector3d()
  intersection[0] = imgX
  intersection[1] = 0.0
  intersection[2] = imgZ

  origin0 = vtk.vtkVector3d()
  origin0[0] = imgX
  origin0[1] = distance
  origin0[2] = imgZ

  worldOrigin = worldFromNominal.TransformPoint(origin0)
  print("world origin (before rotation): " + str(worldOrigin))

  worldIntersection = worldFromNominal.TransformPoint(intersection)
  print("world intersection: " + str(worldIntersection))

  worldCOC = worldFromNominal.TransformPoint((0.0, 0.0, 0.0))

  # Rotate zenith angle - rotate around |COC-Intersection| x |Origin - Intersection|
  worldInt2Coc = vtk.vtkVector3d()
  vtk.vtkMath.Subtract(worldCOC, worldIntersection, worldInt2Coc)
  norm = worldInt2Coc.Normalize()

  worldInt2Origin = vtk.vtkVector3d()
  vtk.vtkMath.Subtract(worldOrigin, worldIntersection, worldInt2Origin)
  norm = worldInt2Origin.Normalize()

  # Axis of rotation for zenith
  zenithRotAxis = vtk.vtkVector3d()
  vtk.vtkMath.Cross(worldInt2Origin, worldInt2Coc, zenithRotAxis)

  # Axis of rotation for azimuth - equal normal to plane
  azimuthRotAxis = worldInt2Origin

  # Create rotation tranform
  zenithAzimuthRot = vtk.vtkTransform()
  zenithAzimuthRot.PostMultiply()
  zenithAzimuthRot.Translate(-worldIntersection[0],
                             -worldIntersection[1],
                             -worldIntersection[2])
  zenithAzimuthRot.RotateWXYZ(angleZenith, zenithRotAxis[0], zenithRotAxis[1], zenithRotAxis[2])
  zenithAzimuthRot.RotateWXYZ(angleAz, azimuthRotAxis[0], azimuthRotAxis[1], azimuthRotAxis[2])
  zenithAzimuthRot.Translate(worldIntersection[0],
                             worldIntersection[1],
                             worldIntersection[2])
  zenithAzimuthRot.Update()

  # Transform origin of needle
  worldOriginRotated = zenithAzimuthRot.TransformPoint(worldOrigin)
  print("world origin (after rotation): " + str(worldOriginRotated))

  # Normal vector for the needle
  worldNormal = vtk.vtkVector3d()
  vtk.vtkMath.Subtract(worldIntersection, worldOriginRotated, worldNormal)
  norm = worldNormal.Normalize()
  print("world normal (after rotation): " + str(worldNormal))

  # Find any vector perpendicular to worldNormal
  first1 = createPerpendicular(worldNormal)
  print("perpendicular vector: " + str(first1))

  # Compute transformation from standard coordinates to needle.
  normal0 = (0.0,0.0,1.0)
  first0  = (1.0,0.0,0.0)
  origin0 = (0.0,0.0,0.0)
  needleFromWorld = vtk.vtkTransform()
  needleFromWorld.PostMultiply()
  mat = AxesToTransform(normal0, first0, origin0,
                        worldNormal, first1, worldOriginRotated)
  needleFromWorld.SetMatrix(mat)

  return needleFromWorld

# Compute intersection with plane containing outline
def ComputeIntersection(needleTransform, cocTransform, distance=50.0):
  """
  Array nominal axes is cocTransform, needleTransform is the transform of the needle (not the clamp)

  distance is the length of the needle

  """
  needleActor, lineFilter = createNeedle(length=distance+20.0, transform=needleTransform)

  # Get position from cocTransform
  # Normal from z-axis

  # Test intersection
  plane = vtk.vtkPlane()
  plane.SetOrigin(cocTransform.GetPosition())
  plane.SetNormal(GetAxis(cocTransform,1))

  cutter = vtk.vtkCutter()
  cutter.SetCutFunction(plane)
  cutter.SetInputData(lineFilter.GetOutput())
  cutter.Update()
  cutterout = cutter.GetOutput()

  intcpActor = None
  if (cutterout.GetNumberOfPoints() > 0):
    print(cutterout.GetPoint(0))
    pointSource = vtk.vtkSphereSource()
    pointSource.SetCenter(cutterout.GetPoint(0))
    pointSource.SetRadius(1.0)
    pointSource.SetPhiResolution(10)
    pointSource.SetThetaResolution(10)
    pointSource.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(pointSource.GetOutputPort())

    intcpActor = vtk.vtkActor()
    intcpActor.SetMapper(mapper)
    intcpActor.GetProperty().SetColor(colors.GetColor3d('Yellow'))
    intcpActor.GetProperty().SetPointSize(5)

  return needleActor, intcpActor

# Create window and renderer
ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
iren.Initialize()
renWin.SetSize(600, 600)


###################################################
# Coordinate transforms
###################################################

# Field generator from world
fgFromWorld = vtk.vtkTransform()
fgFromWorld.PostMultiply()
fgFromWorld.Identity()
fgFromWorld.Update()

# Show field generateor
fgAxes = createAxesActor()
fgAxes.SetUserTransform(fgFromWorld)
fgAxes.SetZAxisLabelText('Zfg')
fgAxes.Modified()

# Box for the Field generator
box = vtk.vtkCubeSource()
box.SetBounds(-40,40,-40,40,-10,10)
box.Update()
boxMapper = vtk.vtkPolyDataMapper()
boxMapper.SetInputConnection(box.GetOutputPort())
boxActor = vtk.vtkActor()
boxActor.SetMapper(boxMapper)
boxActor.SetUserTransform(fgFromWorld)
ren.AddActor(boxActor)


# Probe sensor from Field Generator (move probe)
psFromFg = vtk.vtkTransform()
psFromFg.PostMultiply()
#psFromFg.RotateZ(90)
#psFromFg.RotateX(-90)
psFromFg.Translate(0.0, 0.0, 100.0)
psFromFg.Update()

# Probe reference from probe sensor
refFromSensor = vtk.vtkTransform()
refFromSensor.PostMultiply()
refFromSensor.Translate(3.33, -1.59, -1.7) # original
refFromSensor.Update()

# Array nominal from probe reference
nomFromRef = vtk.vtkTransform()
nomFromRef.PostMultiply()
# Equivalent to q=(0.999680, 0.0, 0.025305, 0.0)
nomFromRef.RotateY(np.rad2deg(-0.05061454))
nomFromRef.Translate(19.35, -0.63, -46.09)
nomFromRef.Update()

# Needle base from clamp
needBaseFromClamp = vtk.vtkTransform()
needBaseFromClamp.PostMultiply()
needBaseFromClamp.Translate(8.38,0.97, 5.33)
needBaseFromClamp.Update()

# Array nominal from world coordinate
nomFromWorld = vtk.vtkTransform()
nomFromWorld.PostMultiply()
nomFromWorld.Identity()
nomFromWorld.Concatenate(fgFromWorld)
nomFromWorld.Concatenate(psFromFg)
nomFromWorld.Concatenate(refFromSensor)
nomFromWorld.Concatenate(nomFromRef)
nomFromWorld.Update()

# Probe sensor from world
sensorFromWorld = vtk.vtkTransform()
sensorFromWorld.PostMultiply()
sensorFromWorld.Identity()
sensorFromWorld.Concatenate(fgFromWorld)
sensorFromWorld.Concatenate(psFromFg)
sensorFromWorld.Update()

addOrientationWidget(iren)

# Orientation widget
axesActor = vtk.vtkAxesActor()
axes = vtk.vtkOrientationMarkerWidget()
axes.SetOrientationMarker( axesActor)
axes.SetInteractor( iren )
axes.SetViewport( 0.8, 0.0, 1.0, 0.2)
axes.EnabledOn()
axes.InteractiveOn()

# Create sector outline
sectorActor = createOutline()
sectorActor.SetUserTransform(nomFromWorld)

# Array nominal axes
nomAxes = createAxesActor()
nomAxes.SetZAxisLabelText('Zcoc')
nomAxes.SetUserTransform(nomFromWorld)
ren.AddActor(nomAxes)

# Probe sensor
probeSensorAxes = createAxesActor()
probeSensorAxes.SetZAxisLabelText('Zpsn')
probeSensorAxes.SetUserTransform(sensorFromWorld)
ren.AddActor(probeSensorAxes)

# Angling increases distance!!!!

# Create needle tip
worldToNeedle = createNeedleReference(nomFromWorld,
                                      imgX=00.0,
                                      imgZ=80.0+50.006,
                                      angleZenith=20.0,
                                      angleAz=30.0,
                                      distance=20.0)

needleAxes = createAxesActor()
needleAxes.SetZAxisLabelText('Znb')
needleAxes.SetUserTransform(worldToNeedle)
needleAxes.Modified()
ren.AddActor(needleAxes)

ren.AddActor(fgAxes)
ren.AddActor(sectorActor)

# Copute the field-generator to needle clamp transformation. We assume that
# the Field generator from world is identity

needBaseFromWorld = vtk.vtkTransform()
needBaseFromWorld.PostMultiply()
needBaseFromWorld.Concatenate(worldToNeedle)
needBaseFromWorld.Concatenate(needBaseFromClamp.GetInverse())
needBaseFromWorld.Update()


needleClampAxes = createAxesActor()
needleClampAxes.SetZAxisLabelText('Znc')
needleClampAxes.SetUserTransform(needBaseFromWorld)
needleClampAxes.Modified()
ren.AddActor(needleClampAxes)


# Print the matrix transform from world to needle clamp
print(needBaseFromWorld.GetMatrix())

# Compute and show intersection
needleActor0, intcpActor = ComputeIntersection(worldToNeedle, nomFromWorld, distance=50.0)

ren.AddActor(needleActor0)
if intcpActor is not None:
  ren.AddActor(intcpActor)

renWin.Render()
iren.Start()



#if __name__ == "__main__":
