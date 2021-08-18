import vtk
import numpy as np

# This is an ad-hoc implementation of an outline for the 9076 to be
# shown on an overlay as well as a 3D representation extracted from
# STL. The coordinate transformations needed for aligning the STL with
# the outline is taken from

# http://gitlab.bkmedical.com/FeasibilitySoftware/QuickVtk/blob/master/res/qml/BKApp/ProbeLiver.qml


def CreateOutline9076(color = (255, 99, 71), depth = 80.0):
  """
  Create outline for the 9076 probe. The outline is contained in the XZ-plane
  """
  # Default color for the outline is "Tomato"
  nElements = 144
  pitch = 0.2101
  roc = 50.006
  height = 5.0
  
  azR = roc
  azArcLength = pitch * (nElements - 1.0)
  azSegment = azArcLength / azR
  dAz = azSegment / (nElements - 1.0)
  
  az = dAz * (np.r_[0:nElements] - 0.5*(nElements - 1.0))
  
  az0 = az[0] - 0.5*dAz
  azN = az[nElements-1] + 0.5*dAz

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
    colors.InsertNextTypedTuple(color)
  
  outline.GetCellData().SetScalars(colors)
  return outline

def CreateSurface9076():
  # Coordinate transformations
  
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

  # Array actual from Array nominal  
  actFromNom = vtk.vtkTransform() 
  actFromNom.PostMultiply()
  actFromNom.RotateZ(np.rad2deg(-0.04712388))
  actFromNom.RotateY(np.rad2deg(0.00942477))
  actFromNom.Identity() # Not used since ideal probe
  actFromNom.Update()

  # Array nominal from probe reference  
  nomFromRef = vtk.vtkTransform()
  nomFromRef.PostMultiply()
  nomFromRef.RotateY(np.rad2deg(-0.05061454))
  nomFromRef.Translate(19.35, -0.62, -46.09)
  nomFromRef.Update()

  # Probe reference from sensor nominal  
  refFromSensor = vtk.vtkTransform() 
  refFromSensor.PostMultiply()
  refFromSensor.Translate(-3.33, 1.59, 1.7) # original
  refFromSensor.Translate(0.0, -3.86, 0.0) # Shifted half-height of xdx + enclosing
  refFromSensor.Inverse()
  refFromSensor.Update()
  
  # Actual array from sensor nominal
  actFromSensor = vtk.vtkTransform()
  actFromSensor.Identity()
  actFromSensor.Concatenate(refFromSensor)
  actFromSensor.Concatenate(nomFromRef)
  actFromSensor.Concatenate(actFromNom)
  actFromSensor.Update()
  
  # To Ultrasound from Array actual (based on ProbeCenterY value from
  # OEM "QUERY:B_TRANS_IMAGE_CALIB;").
  usFromActual = vtk.vtkTransform()
  usFromActual.PostMultiply()
  usFromActual.Translate(-47.8225, 0.0, 0.0) # original
  usFromActual.Translate(0.0, 0.0, 45.0) # JEM offset fra OEM (must be)
  usFromActual.Update()

  # Final transformation from STL to XZ-plane
  finalTransform = vtk.vtkTransform()
  finalTransform.PostMultiply()
  finalTransform.Identity()
  finalTransform.Concatenate(sensorFromSTL)
  finalTransform.Concatenate(actFromSensor)
  finalTransform.Concatenate(usFromActual)

  reader = vtk.vtkSTLReader()
  file_name = './9076.vtp'
  reader = vtk.vtkXMLPolyDataReader()
  reader.SetFileName(file_name)
  reader.Update()

  tfpoly = vtk.vtkTransformPolyDataFilter()
  tfpoly.SetInputConnection(reader.GetOutputPort())
  tfpoly.SetTransform(finalTransform)
  tfpoly.Update()
  return tfpoly.GetOutput()

  
# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
