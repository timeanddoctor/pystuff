import vtk
import sys

origin = [0.0, 0.0, 0.0]
p0 = [1.0, 0.0, 0.0]
p1 = [0.0, 1.0, 0.0]
p2 = [0.0, 1.0, 2.0]
p3 = [1.0, 2.0, 3.0]

# Create a vtkPoints object and store the points in it
points = vtk.vtkPoints()
points.InsertNextPoint(origin)
points.InsertNextPoint(p0)
points.InsertNextPoint(p1)
points.InsertNextPoint(p2)
points.InsertNextPoint(p3)

# Create a cell array to store the lines in and add the lines to it
lines = vtk.vtkCellArray()

# Create four lines
for i in range(4):
  line = vtk.vtkLine()
  line.GetPointIds().SetId(0,i)
  line.GetPointIds().SetId(1,i+1)
  lines.InsertNextCell(line)

# Create a polydata to store everything in
linesPolyData = vtk.vtkPolyData()

# Add the points to the dataset
linesPolyData.SetPoints(points)

# Add the lines to the dataset
linesPolyData.SetLines(lines)

print("There are " + str(linesPolyData.GetNumberOfLines()) + " lines.")

dataArray = linesPolyData.GetPoints().GetData()


linesPolyData.GetLines().InitTraversal()
idList = vtk.vtkIdList()
while linesPolyData.GetLines().GetNextCell(idList):
  print("Line has " + str(idList.GetNumberOfIds()) + " points.")
  for pointId in range(idList.GetNumberOfIds()):
    sys.stdout.write(str(idList.GetId(pointId))+ ": ")
    # First x-coordinate
    x = dataArray.GetComponent(idList.GetId(pointId),0)
    y = dataArray.GetComponent(idList.GetId(pointId),1)
    z = dataArray.GetComponent(idList.GetId(pointId),2)
    sys.stdout.write("x: " + str(x) + " y: " + str(y) + " z: " + str(z))
    sys.stdout.write("\n")
  print("")
