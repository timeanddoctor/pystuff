#include <vtkSmartPointer.h>

#include <vtkXMLPolyDataReader.h>
#include <vtkSphereSource.h>
#include <vtkClipPolyData.h>
#include <vtkPlane.h>

#include <vtkCommand.h>
#include <vtkImplicitPlaneWidget2.h>
#include <vtkImplicitPlaneRepresentation.h>
 
#include <vtkPolyDataMapper.h>
#include <vtkProperty.h>
#include <vtkActor.h>
#include <vtkRenderWindow.h>
#include <vtkRenderer.h>
#include <vtkRenderWindowInteractor.h>
import vtk
import sys

class callback(object):
    def onExecute(self, caller, ev):
        planeWidget = caller
        rep = planeWidget.GetRepresentation()
        rep.GetPlane(self.Plane)
        
if __name__ == "__main__":
  sphereSource = vtk.vtkSphereSource()
  sphereSource.SetRadius(10.0)
  
  reader = vtk.vtkXMLPolyDataReader()
  
  #  Setup a visualization pipeline
  plane = vtk.vtkPlane()
  clipper = vtk.vtkClipPolyData()
  clipper.SetClipFunction(plane)
  clipper.InsideOutOn()
  if len(sys.argv) < 2:
      clipper.SetInputConnection(sphereSource.GetOutputPort())
  else:
      reader.SetFileName(sys.argv[1])
      clipper.SetInputConnection(reader.GetOutputPort())
  
  #  Create a mapper and actor
  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputConnection(clipper.GetOutputPort())
  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  
  backFaces = vtk.vtkProperty()
  backFaces.SetDiffuseColor(.8, .8, .4)
  
  actor.SetBackfaceProperty(backFaces)
   
  #  A renderer and render window
  renderer = vtk.vtkRenderer()
  renderWindow =vtk.vtkRenderWindow()
  renderWindow.AddRenderer(renderer)
  renderer.AddActor(actor)
   
  #  An interactor
  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  renderWindowInteractor.SetRenderWindow(renderWindow)
   
  renderWindow.Render()
  
  #  The callback will do the work
  #vtk.vtkIPWCallback> myCallback = vtk.vtkIPWCallback()
  #myCallback.Plane = plane
  #myCallback.Actor = actor
  
  rep = vtk.vtkImplicitPlaneRepresentation()
  rep.SetPlaceFactor(1.25) #  This must be set prior to placing the widget
  rep.PlaceWidget(actor.GetBounds())
  rep.SetNormal(plane.GetNormal())
  
  planeWidget = vtk.vtkImplicitPlaneWidget2()
  planeWidget.SetInteractor(renderWindowInteractor)
  planeWidget.SetRepresentation(rep)
  myCallback = callback()
  myCallback.Plane = plane
  myCallback.Actor = actor
  planeWidget.AddObserver(vtk.vtkCommand.InteractionEvent, myCallback.onExecute)
  
  #  Render
  renderWindowInteractor.Initialize()
  renderWindow.Render()
  planeWidget.On()
   
  #  Begin mouse interaction
  renderWindowInteractor.Start()

