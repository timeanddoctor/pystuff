import os
import vtk

from vtkUtils import polyInfo

filedir = os.path.dirname(os.path.realpath(__file__))

def get_program_parameters():
  import argparse
  description = 'Clip polydata interactively.'
  epilogue = ''''''
  parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('filename', help='vessels.vtp')

  args = parser.parse_args()
  return args.filename

renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("Test")

renderWindow.AddRenderer(renderer);
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

#filename = get_program_parameters()
filename = os.path.join(filedir, '../../fis/data/Abdomen/ProperlyClosed.vtp')

reader = vtk.vtkXMLPolyDataReader()
reader.SetFileName(filename)
reader.Update()

global polydata
polydata = reader.GetOutput()

global normals
normals = vtk.vtkPolyDataNormals()
normals.SetInputConnection(reader.GetOutputPort())

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(normals.GetOutputPort())

global lastActor
lastActor = vtk.vtkActor()
lastActor.SetMapper(mapper)
colors = vtk.vtkNamedColors()
prop = lastActor.GetProperty()
prop.SetColor(colors.GetColor3d("Red"))

#polyInfo(normals)

#normals.GetOutput().GetPointData().GetArray("Normals")
bounds = polydata.GetBounds()
center = polydata.GetCenter()

# Implicit function for clipping
plane = vtk.vtkPlane()
plane.SetOrigin(bounds[0], bounds[2], center[2])
plane.SetNormal(0, 0, 1)
plane.Modified()

def BeginInteraction(obj,ev):
  print('Begin Interaction')

def EndInteraction(obj,ev):
  print('End Interaction')

planeWidget = vtk.vtkPlaneWidget()
planeWidget.SetInputData(polydata)
planeWidget.NormalToZAxisOn()
planeWidget.SetInteractor(renderWindow.GetInteractor())
planeWidget.AddObserver("EnableEvent", BeginInteraction)
planeWidget.AddObserver("StartInteractionEvent", BeginInteraction)
planeWidget.AddObserver("InteractionEvent", EndInteraction)

planeWidget.SetEnabled(0)
planeWidget.SetOrigin(bounds[0], bounds[2], center[2])
planeWidget.SetPoint1(bounds[0], bounds[3], center[2])
planeWidget.SetPoint2(bounds[1], bounds[2], center[2])
planeWidget.Modified()
prop = planeWidget.GetPlaneProperty()
prop.SetColor( .2, .8, 0.1 )
#prop.SetOpacity( 0.5 )#//Set transparency
prop = planeWidget.GetHandleProperty()
prop.SetColor(0, .4, .7 )
prop.SetLineWidth( 1.5 )#//Set plane lineweight

planeWidget.PlaceWidget() # Lay the plane
planeWidget.SetCenter(center)
planeWidget.Modified()
planeWidget.SetEnabled(1)
planeWidget.On() # Display plane

renderer.AddActor(lastActor)
renderer.SetBackground(1,1,1) # Background color white
renderer.ResetCamera()

def KeyPress(obj, ev):
  global normals, lastActor
  key = obj.GetKeySym()
  if key == 'r':
    if (lastActor is not None):
      renderer.RemoveActor(lastActor)
      lastActor = None

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(reader.GetOutputPort())

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(colors.GetColor3d("Red"))
    prop.SetInterpolationToFlat()
    renderer.AddActor(actor)
    lastActor = actor
    # TODO: Update normals
    renderWindowInteractor.Enable()
    renderWindow.Render()
  if key == 'p':
    # Reset plane position
    planeWidget.SetEnabled(0)
    planeWidget.SetOrigin(bounds[0], bounds[2], center[2])
    planeWidget.SetPoint1(bounds[0], bounds[3], center[2])
    planeWidget.SetPoint2(bounds[1], bounds[2], center[2])
    planeWidget.Modified()
    planeWidget.SetEnabled(1)
    return
  if key == 'c':
    # Implicit function for clipping
    plane = vtk.vtkPlane()
    plane.SetOrigin(planeWidget.GetOrigin())
    plane.SetNormal(planeWidget.GetNormal())
    plane.Modified()

    clipper = vtk.vtkClipPolyData()
    clipper.SetInputConnection(normals.GetOutputPort())
    clipper.SetClipFunction(plane)
    clipper.SetValue(0)
    clipper.Update()

    clipPoly = clipper.GetOutput()

    boundaryEdges = vtk.vtkFeatureEdges()
    boundaryEdges.SetInputData(clipPoly)
    boundaryEdges.BoundaryEdgesOn()
    boundaryEdges.FeatureEdgesOff()
    boundaryEdges.NonManifoldEdgesOff()
    boundaryEdges.ManifoldEdgesOff()

    boundaryStrips = vtk.vtkStripper()
    boundaryStrips.SetInputConnection(boundaryEdges.GetOutputPort())
    boundaryStrips.Update()

    # Change the polylines into polygons
    boundaryPoly = vtk.vtkPolyData()
    boundaryPoly.SetPoints(boundaryStrips.GetOutput().GetPoints())
    boundaryPoly.SetPolys(boundaryStrips.GetOutput().GetLines())

    append = vtk.vtkAppendPolyData()
    append.AddInputData(boundaryPoly)
    append.AddInputData(clipPoly)
    cleanFilter = vtk.vtkCleanPolyData()
    cleanFilter.SetInputConnection(append.GetOutputPort())
    cleanFilter.Update()

    renderWindowInteractor.Disable()
    if (lastActor is not None):
      renderer.RemoveActor(lastActor)
      lastActor = None

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(cleanFilter.GetOutputPort())

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(colors.GetColor3d("Red"))
    prop.SetInterpolationToFlat()
    renderer.AddActor(actor)
    lastActor = actor
    # TODO: Update normals
    renderWindowInteractor.Enable()
    renderWindow.Render()



#Render and interact
renderWindow.Render()

renderWindowInteractor.AddObserver('KeyPressEvent', KeyPress, 1.0)
renderWindowInteractor.Start()
