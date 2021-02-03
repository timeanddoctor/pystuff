#!/usr/bin/env python

# In this example vtkClipPolyData is used to cut a polygonal model
# of a cow in half. In addition, the open clip is closed by triangulating
# the resulting complex polygons.
import os
import vtk
from vtk.util.colors import peacock, tomato, red, black
#VTK_DATA_ROOT = vtkGetDataRoot()
VTK_DATA_ROOT = '/home/jmh/git/VTKExamples/src/Testing'

# First start by reading a cow model. We also generate surface normals for
# prettier rendering.
cow = vtk.vtkBYUReader()
if os.name == 'nt':
  cow.SetGeometryFileName("./cow.g")
else:
  cow.SetGeometryFileName(VTK_DATA_ROOT + "/Data/cow.g")
cowNormals = vtk.vtkPolyDataNormals()
cowNormals.SetInputConnection(cow.GetOutputPort())

# We clip with an implicit function. Here we use a plane positioned near
# the center of the cow model and oriented at an arbitrary angle.
plane = vtk.vtkPlane()
plane.SetOrigin(0.25, 0, 0)
plane.SetNormal(-1, -1, 0)

# vtkClipPolyData requires an implicit function to define what it is to
# clip with. Any implicit function, including complex boolean combinations
# can be used. Notice that we can specify the value of the implicit function
# with the SetValue method.
clipper = vtk.vtkClipPolyData()
clipper.SetInputConnection(cowNormals.GetOutputPort())
clipper.SetClipFunction(plane)
clipper.GenerateClipScalarsOn()
clipper.GenerateClippedOutputOn()
clipper.SetValue(0.5)
clipMapper = vtk.vtkPolyDataMapper()
clipMapper.SetInputConnection(clipper.GetOutputPort())
clipMapper.ScalarVisibilityOff()
#clipMapper.ScalarVisibilityOn()
backProp = vtk.vtkProperty()
backProp.SetDiffuseColor(tomato)
clipActor = vtk.vtkActor()
clipActor.SetMapper(clipMapper)
clipActor.GetProperty().SetColor(peacock) # surface of rest of cow
clipActor.SetBackfaceProperty(backProp)

# Here we are cutting the cow. Cutting creates lines where the cut
# function intersects the model. (Clipping removes a portion of the
# model but the dimension of the data does not change.)
#
# The reason we are cutting is to generate a closed polygon at the
# boundary of the clipping process. The cutter generates line
# segments, the stripper then puts them together into polylines. We
# then pull a trick and define polygons using the closed line
# segments that the stripper created.
cutEdges = vtk.vtkCutter()
cutEdges.SetInputConnection(cowNormals.GetOutputPort())
cutEdges.SetCutFunction(plane)
#cutEdges.GenerateCutScalarsOn()
cutEdges.GenerateCutScalarsOff()
cutEdges.SetValue(0, 0.5)
cutStrips = vtk.vtkStripper()
cutStrips.SetInputConnection(cutEdges.GetOutputPort())
cutStrips.Update()
cutPoly = vtk.vtkPolyData()
cutPoly.SetPoints(cutStrips.GetOutput().GetPoints())
cutPoly.SetPolys(cutStrips.GetOutput().GetLines())

# Triangle filter is robust enough to ignore the duplicate point at
# the beginning and end of the polygons and triangulate them.
cutTriangles = vtk.vtkTriangleFilter()
cutTriangles.SetInputData(cutPoly)
cutMapper = vtk.vtkPolyDataMapper()

# Only one of these are needed
#cutMapper.SetInputData(cutPoly)
cutMapper.SetInputConnection(cutTriangles.GetOutputPort())

cutActor = vtk.vtkActor()
cutActor.SetMapper(cutMapper)
cutActor.GetProperty().SetColor(peacock) # Intersecting plane

testMe = False

tubes = vtk.vtkTubeFilter()

if testMe:
  tubes.SetInputData(cutPoly) # does not work
else:
  tubes.SetInputConnection(cutStrips.GetOutputPort()) # works

tubes.CappingOn() # Was off
tubes.SidesShareVerticesOff()
tubes.SetNumberOfSides(12)
tubes.SetRadius(0.0125)
if testMe:
  tubes.Update()

edgeMapper = vtk.vtkPolyDataMapper()
edgeMapper.ScalarVisibilityOff()

if testMe:
  edgeMapper.SetInputData(tubes.GetOutput())
else:
  # edgeMapper.SetInputData(cutPoly) # alone gives surface
  edgeMapper.SetInputConnection(tubes.GetOutputPort()) # Ignores InputData
  #edgeMapper.SetInputConnection(cutStrips.GetOutputPort())
  
edgeActor = vtk.vtkActor()
edgeActor.SetMapper(edgeMapper)
edgeActor.GetProperty().SetColor(red)
edgeActor.GetProperty().SetLineWidth(3)

transform = vtk.vtkTransform()
transform.Translate(+0.1, +0.1, 0)
edgeActor.SetUserTransform(transform)



# The clipped part of the cow is rendered wireframe.
restMapper = vtk.vtkPolyDataMapper()
restMapper.SetInputConnection(clipper.GetClippedOutputPort())
restMapper.ScalarVisibilityOff()
restActor = vtk.vtkActor()
restActor.SetMapper(restMapper)
restActor.GetProperty().SetRepresentationToWireframe()
# restActor.GetProperty().SetColor(red) # rest of wireframe

# Create graphics stuff
ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)


# Add the actors to the renderer, set the background and size
ren.AddActor(clipActor)
ren.AddActor(cutActor)
ren.AddActor(restActor)
ren.AddActor(edgeActor) # What we want

ren.SetBackground(1, 1, 1)
ren.ResetCamera()
ren.GetActiveCamera().Azimuth(30)
ren.GetActiveCamera().Elevation(30)
ren.GetActiveCamera().Dolly(1.5)
ren.ResetCameraClippingRange()

renWin.SetSize(300, 300)
iren.Initialize()

# Lets you move the cut plane back and forth by invoking the function
# Cut with the appropriate plane value (essentially a distance from
# the original plane).  This is not used in this code but should give
# you an idea of how to define a function to do this.
def Cut(v):
    clipper.SetValue(v)
    cutEdges.SetValue(0, v)
    cutStrips.Update()
    cutPoly.SetPoints(cutStrips.GetOutput().GetPoints())
    cutPoly.SetPolys(cutStrips.GetOutput().GetLines())
    cutMapper.Update()
    renWin.Render()

renWin.Render()
iren.Start()
