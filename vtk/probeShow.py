# txUS.input = [ probe9076.txUA, probe9076.txAS_3129501 ]
# txHU.input = [ probe9076.txHS, txUS.inverse ]
import vtk
from vtk.util.colors import red, blue, black, yellow
import numpy as np

nElements = 144
pitch = 0.2101
roc = 50.006
depth = 80.0
height = 5.0

azR = roc
azArcLength = pitch * (nElements - 1.0)
azSegment = azArcLength / azR
dAz = azSegment / (nElements - 1.0)

az = dAz * (np.r_[0:nElements] - 0.5*(nElements - 1.0))

az0 = az[0] - 0.5*dAz
azN = az[nElements-1] + 0.5*dAz

namedColors = vtk.vtkNamedColors()

appendFilter = vtk.vtkAppendPolyData()

# Create 2 arcs
arc0 = vtk.vtkArcSource()
arc0.SetCenter(0, 0, -azR)
arc0.SetPoint1(azR*np.sin(az0), 0, azR*np.cos(az0) - azR)
arc0.SetPoint2(azR*np.sin(azN), 0, azR*np.cos(azN) - azR)
arc0.SetResolution( 10 )
arc0.Update()

appendFilter.AddInputData(arc0.GetOutput())
appendFilter.Update()

arc1 = vtk.vtkArcSource()
arc1.SetCenter(0, 0, -azR)
arc1.SetPoint1((azR+depth)*np.sin(az0), 0, (azR+depth)*np.cos(az0) - azR)
arc1.SetPoint2((azR+depth)*np.sin(azN), 0, (azR+depth)*np.cos(azN) - azR)
arc1.SetResolution( 10 )
arc1.Update()

appendFilter.AddInputData(arc1.GetOutput())
appendFilter.Update()

# Create lines
linesPolyData = vtk.vtkPolyData()

pts = vtk.vtkPoints()
pts.InsertNextPoint((azR*np.sin(az0), 0, azR*np.cos(az0) - azR))
pts.InsertNextPoint(((azR+depth)*np.sin(az0), 0, (azR+depth)*np.cos(az0) - azR))
pts.InsertNextPoint((azR*np.sin(azN), 0, azR*np.cos(azN) - azR))
pts.InsertNextPoint(((azR+depth)*np.sin(azN), 0, (azR+depth)*np.cos(azN) - azR))

linesPolyData.SetPoints(pts)

line0 = vtk.vtkLine()
line0.GetPointIds().SetId(0, 0)
line0.GetPointIds().SetId(1, 1)

line1 = vtk.vtkLine()
line1.GetPointIds().SetId(0, 2)
line1.GetPointIds().SetId(1, 3)

# Create a vtkCellArray container and store the lines in it
lines = vtk.vtkCellArray()
lines.InsertNextCell(line0)
lines.InsertNextCell(line1)

linesPolyData.SetLines(lines)

appendFilter.AddInputData(linesPolyData)
appendFilter.Update()

outline = appendFilter.GetOutput()

colors = vtk.vtkUnsignedCharArray()
colors.SetNumberOfComponents(3)
for i in range(outline.GetNumberOfCells()):
  colors.InsertNextTypedTuple((255, 99, 71))

outline.GetCellData().SetScalars(colors)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(outline)

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetLineWidth(4)
actor.GetProperty().SetLineWidth(4)

# The probe
radPerDegree = np.pi / 180.0

# Sensor from STL
sensorFromSTL = vtk.vtkTransform()
sensorFromSTL.PostMultiply()
sensorFromSTL.RotateZ(180.0)
sensorFromSTL.Translate(109.27152 + 29.7296 - 5.41,
                        29.69371 - 2.2,
                        75.52397 - 2.144)
sensorFromSTL.Modified()
sensorFromSTL.Inverse()
sensorFromSTL.Update()

actFromNom = vtk.vtkTransform() # Array actual from Array nominal
actFromNom.PostMultiply()
actFromNom.RotateZ(-0.04712388 / radPerDegree)
actFromNom.RotateY(0.00942477 / radPerDegree)
actFromNom.Identity() # Not used since ideal probe
actFromNom.Update()

nomFromRef = vtk.vtkTransform() # Array nominal from probe reference
nomFromRef.PostMultiply()
nomFromRef.RotateY(-0.05061454 / radPerDegree) # 3 degrees
nomFromRef.Translate(19.35, -0.62, -46.09)
nomFromRef.Update()

refFromSensor = vtk.vtkTransform() # Probe reference from sensor nominal
refFromSensor.PostMultiply()
refFromSensor.Translate(-3.33, 1.59, 1.7) # original
refFromSensor.Translate(0.0, -3.86, 0.0) # Half height of xdx

refFromSensor.Inverse()
refFromSensor.Update()

# actual array from sensor nominal
actFromSensor = vtk.vtkTransform()
actFromSensor.Identity()
actFromSensor.Concatenate(refFromSensor)
actFromSensor.Concatenate(nomFromRef)
actFromSensor.Concatenate(actFromNom)
actFromSensor.Update()

# To Ultrasound from Array actual (based on ProbeCenterY value from OEM "QUERY:B_TRANS_IMAGE_CALIB;"). Not needed since our origin is at the sole
usFromActual = vtk.vtkTransform()
usFromActual.PostMultiply()
usFromActual.Translate(-47.8225, 0.0, 0.0) # original
usFromActual.Translate(0.0, 0.0, 45.0) # JEM offset fra OEM
usFromActual.Update()

finalTransform = vtk.vtkTransform()
finalTransform.PostMultiply()
finalTransform.Identity()
finalTransform.Concatenate(sensorFromSTL)
finalTransform.Concatenate(actFromSensor)
finalTransform.Concatenate(usFromActual)


#file_name = './9076.STL'
reader = vtk.vtkSTLReader()
file_name = './9076.vtp'
reader = vtk.vtkXMLPolyDataReader()
reader.SetFileName(file_name)
reader.Update()

#finalTransform = sensorFromSTL
#finalTransform.Inverse()


tfpoly = vtk.vtkTransformPolyDataFilter()
tfpoly.SetInputConnection(reader.GetOutputPort())
tfpoly.SetTransform(finalTransform)
tfpoly.Update()

mapper2 = vtk.vtkPolyDataMapper()
mapper2.SetInputConnection(tfpoly.GetOutputPort())

actor2 = vtk.vtkActor()
actor2.SetMapper(mapper2)

# TODO: Make a utility function
cubeAxesActor = vtk.vtkCubeAxesActor()
cubeAxesActor.SetUseTextActor3D(1)
bounds0 = outline.GetBounds()
bounds1 = tfpoly.GetOutput().GetBounds()
bounds = (min(bounds0[0],bounds1[0]),
          max(bounds0[1],bounds1[1]),
          min(bounds0[2],bounds1[2]),
          max(bounds0[3],bounds1[3]),
          min(bounds0[4],bounds1[4]),
          max(bounds0[5],bounds1[5]))
cubeAxesActor.SetBounds(bounds)
cubeAxesActor.XAxisMinorTickVisibilityOff()
cubeAxesActor.YAxisMinorTickVisibilityOff()
cubeAxesActor.ZAxisMinorTickVisibilityOff()
cubeAxesActor.SetFlyModeToStaticEdges()
for i in range(3):
  cubeAxesActor.GetLabelTextProperty(i).SetColor(black)
  cubeAxesActor.GetTitleTextProperty(i).SetColor(black)
cubeAxesActor.GetXAxesLinesProperty().SetColor(black)
cubeAxesActor.GetYAxesLinesProperty().SetColor(black)
cubeAxesActor.GetZAxesLinesProperty().SetColor(black)

cubeAxesActor.GetProperty().SetColor(black)

          


renderer = vtk.vtkRenderer()
cubeAxesActor.SetCamera(renderer.GetActiveCamera())
renderer.AddActor(cubeAxesActor)
renderer.AddActor(actor)
renderer.AddActor(actor2)
renderer.SetBackground(namedColors.GetColor3d("SlateGray"))
                       
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetWindowName("9076")
renderWindow.SetSize(600, 600)
renderWindow.AddRenderer(renderer)

camera = renderer.GetActiveCamera()
camera.ParallelProjectionOn()



interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renderWindow)

renderWindow.Render()
interactor.Start()

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
