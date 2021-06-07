import vtk
import os

from probe import CreateOutline9076

fileDir = 'c:/github/fis/data/Abdomen'

surfName = 'Liver_3D_Fast_Marching_Closed.vtp'
volName =  'VesselVolumeUncompressed.mhd'

def hexCol(s):
  if isinstance(s,str):
    if "#" in s:
      s = s.lstrip("#")
    return tuple(int(s[i : i + 2], 16)/255.0 for i in (0, 2, 4))
  return None

def loadSurface(fname):
  reader = vtk.vtkXMLPolyDataReader()
  reader.SetFileName(fileName)
  reader.Update()

  # Take the largest connected component
  connectFilter = vtk.vtkPolyDataConnectivityFilter()
  connectFilter.SetInputConnection(reader.GetOutputPort())
  connectFilter.SetExtractionModeToLargestRegion()
  connectFilter.Update()

  normals = vtk.vtkPolyDataNormals()
  normals.SetInputConnection(connectFilter.GetOutputPort())
  normals.Update()

  pd = normals.GetOutput()
  com = vtk.vtkCenterOfMass()
  com.SetInputData(pd)
  com.SetUseScalarsAsWeights(False)
  com.Update()
  center = com.GetCenter()
  
  # Mapper
  mapper = vtk.vtkPolyDataMapper()
  mapper.SetInputConnection(normals.GetOutputPort())

  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  prop = actor.GetProperty()
  prop.SetColor(vtk.vtkColor3d(hexCol("#873927")))

  # Assign actor to the renderer
  prop.SetOpacity(0.35)
  return actor, center

def Callback(obj, ev):
  print('hello')
  global lastNormal
  global lastAxis1
  global axes
  if 0:
    # TODO: Move a sector outline
    normal0 = lastNormal
    first0  = lastAxis1
    origin0 = axes.GetOrigin()
    
    normal1 = np.array(obj.GetNormal())
    first1 = np.array(obj.GetPoint1()) - np.array(obj.GetOrigin())
    origin1 = obj.GetCenter()
    
    trans = AxesToTransform(normal0, first0, origin0,
                            normal1, first1, origin1)
    
    if axes.GetUserTransform() is not None:
      axes.GetUserTransform().Concatenate(trans)
    else:
      transform = vtk.vtkTransform()
      transform.SetMatrix(trans)
      transform.PostMultiply()
      axes.SetUserTransform(transform)
    
    # Only for book keeping
    axes.SetOrigin(obj.GetCenter()) # Not modified by SetUserTransform
    axes.Modified()
    
    # Update last axes
    lastAxis1[0] = first1[0]
    lastAxis1[1] = first1[1]
    lastAxis1[2] = first1[2]
    
    lastNormal = (normal1[0], normal1[1], normal1[2])
  
fileName = os.path.join(fileDir, surfName)
actor, com = loadSurface(fileName)


renderer0 = vtk.vtkRenderer()
renderer0.SetViewport(0.,0., 0.5, 1.)


renderer1 = vtk.vtkRenderer()
renderer1.SetViewport(0.5,0., 1., 1.)


camera = vtk.vtkCamera()

renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer1)
renderWindow.AddRenderer(renderer0)
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

renderer0.SetBackground(.1, .2, .3)
renderer1.SetBackground(.1, .2, .3)

renderer0.AddActor(actor)

planeWidget = vtk.vtkPlaneWidget()
planeWidget.SetInteractor(renderWindowInteractor)
planeWidget.SetOrigin(com[0], com[1], com[2])
planeWidget.SetPoint1(com[0]+30.0, com[1], com[2])
planeWidget.SetPoint2(com[0], com[1]+30.0, com[2])
planeWidget.AddObserver(vtk.vtkCommand.EndInteractionEvent, Callback, 1.0)

prop = planeWidget.GetPlaneProperty()
prop.SetColor( .2, .8, 0.1 )
prop = planeWidget.GetHandleProperty()
prop.SetColor(0, .4, .7 )
prop.SetLineWidth( 1.5 )#//Set plane lineweight


planeWidget.Modified()
planeWidget.On()


renderer0.SetActiveCamera(camera)
renderer1.SetActiveCamera(camera)
renderer1.ResetCamera()

renderWindow.Render()
renderWindowInteractor.Start()
