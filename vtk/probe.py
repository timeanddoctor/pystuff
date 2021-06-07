import vtk
import numpy as np

def CreateOutline9076(color = (255, 99, 71), depth = 80.0):
  """
  Create outline for the 9076 probe. The outline is contained in the XZ-plane
  """

  # Avoid multiple generations
  if CreateOutline9076.output is not None and  CreateOutline9076.depth == depth:
    print("reused outline")
    return CreateOutline9076.output

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

  # Create first arc
  arc0 = vtk.vtkArcSource()
  arc0.SetCenter(0, 0, -azR)
  arc0.SetPoint1(azR*np.sin(az0), 0, azR*np.cos(az0) - azR)
  arc0.SetPoint2(azR*np.sin(azN), 0, azR*np.cos(azN) - azR)
  arc0.SetResolution( 10 )
  arc0.Update()

  arcData0 = arc0.GetOutput()

  # Create second arc
  arc1 = vtk.vtkArcSource()
  arc1.SetCenter(0, 0, -azR)
  arc1.SetPoint1((azR+depth)*np.sin(azN), 0, (azR+depth)*np.cos(azN) - azR)
  arc1.SetPoint2((azR+depth)*np.sin(az0), 0, (azR+depth)*np.cos(az0) - azR)
  arc1.SetResolution( 10 )
  arc1.Update()

  arcData1 = arc1.GetOutput()

  # Resulting poly data
  linesPolyData = vtk.vtkPolyData()
  lines = vtk.vtkCellArray()
  points = vtk.vtkPoints()

  # Iterate through points and and create new lines
  arcData0.GetLines().InitTraversal()
  idList = vtk.vtkIdList()
  while arcData0.GetLines().GetNextCell(idList):
    pointId = idList.GetId(0)
    points.InsertNextPoint(arcData0.GetPoint(pointId))
    for i in range(1, idList.GetNumberOfIds()):
      pointId = idList.GetId(i)
      points.InsertNextPoint(arcData0.GetPoint(pointId))
      line = vtk.vtkLine()
      line.GetPointIds().SetId(0,i-1)
      line.GetPointIds().SetId(1,i)
      lines.InsertNextCell(line)

  arcData1.GetLines().InitTraversal()
  idList = vtk.vtkIdList()
  while arcData1.GetLines().GetNextCell(idList):
    pointId = idList.GetId(0)
    points.InsertNextPoint(arcData1.GetPoint(pointId))
    for j in range(1, idList.GetNumberOfIds()):
      pointId = idList.GetId(j)
      points.InsertNextPoint(arcData1.GetPoint(pointId))
      line = vtk.vtkLine()
      line.GetPointIds().SetId(0,i+j-1)
      line.GetPointIds().SetId(1,i+j)
      lines.InsertNextCell(line)

  # Insert two extra lines joining the two arcs
  line = vtk.vtkLine()
  line.GetPointIds().SetId(0,i+j)
  line.GetPointIds().SetId(1,0)
  lines.InsertNextCell(line)

  line = vtk.vtkLine()
  line.GetPointIds().SetId(0,i)
  line.GetPointIds().SetId(1,i+1)
  lines.InsertNextCell(line)


  linesPolyData.SetPoints(points)
  linesPolyData.SetLines(lines)

  # Create polyline(s) from line segments. There will be
  # two due to the the ordering
  cutStrips = vtk.vtkStripper()
  cutStrips.SetInputData(linesPolyData)
  cutStrips.Update()

  # Transform points forward such arcs have center in (0,0,0)
  transform = vtk.vtkTransform()
  transform.Translate(0.0, 0.0, roc)
  transform.Update()

  transformPolyDataFilter = vtk.vtkTransformPolyDataFilter()
  transformPolyDataFilter.SetInputConnection(cutStrips.GetOutputPort())
  transformPolyDataFilter.SetTransform(transform)
  transformPolyDataFilter.Update()
  outline = transformPolyDataFilter.GetOutput()

  # Color the lines
  colors = vtk.vtkUnsignedCharArray()
  colors.SetNumberOfComponents(3)
  for i in range(outline.GetNumberOfCells()):
    colors.InsertNextTypedTuple(color)

  outline.GetCellData().SetScalars(colors)
  CreateOutline9076.depth = depth
  CreateOutline9076.output = outline
  return CreateOutline9076.output
CreateOutline9076.output = None
CreateOutline9076.depth = 0.0
