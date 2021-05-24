import vtk

global transform
transform = vtk.vtkTransform()
global source

def callback(ob, ev):
  global transform
  if ob is not None:
    print(ob.GetClassName())
    print(ev)
    if ob.GetClassName() == 'vtkSphereSource':
      if ev == 'StartEvent':
        print('start - changing transform')
        transform.Scale(1.0,1.0,1.0)
        transform.Update()
    #source.Update() # Infinite - triggers new StartEvent

transform.Scale(1.0,2.0,3.0)
transform.Update()


source = vtk.vtkSphereSource()
source.AddObserver(vtk.vtkCommand.AnyEvent, callback)
source.SetThetaResolution(10)
source.SetPhiResolution(10)
source.SetRadius(1.0)
source.Update()


filt = vtk.vtkTransformPolyDataFilter()
filt.AddObserver(vtk.vtkCommand.AnyEvent, callback)
filt.SetTransform(transform)
filt.SetInputConnection(source.GetOutputPort())
filt.Update()

# Can I use StartEvent
# ProgressEvent has a pointer to a value [0,1]
# TimerEvent return an int representing a timerId
output = filt.GetOutput()
