import vtk

source = vtk.vtkSphereSource()
source.Update()

# Extract the polydata
polydata = vtk.vtkPolyData()
polydata.ShallowCopy(source.GetOutput())

location = vtk.vtkDoubleArray()

# Create the data to store (here we just use (0,0,0))
locationValue = (1.0, 0.0, 0.0)

location.SetNumberOfComponents(3)
location.SetName("MyDoubleArray")
location.InsertNextTuple(locationValue)
# The data is added to FIELD data (rather than POINT data as usual)
polydata.GetFieldData().AddArray(location)

intValue = vtk.vtkIntArray()
intValue.SetNumberOfComponents(1)
intValue.SetName("MyIntValue")
intValue.InsertNextValue(5)

polydata.GetFieldData().AddArray(intValue)

# Get the data back out
retrievedArray = polydata.GetFieldData().GetAbstractArray("MyIntValue")

print(retrievedArray.GetValue(0))

retrievedArray = polydata.GetFieldData().GetAbstractArray("MyDoubleArray")

print(retrievedArray.GetValue(0))


# Use vtkTransformFilter to demonstrate this
