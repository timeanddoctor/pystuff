import vtk

cone = vtk.vtkConeSource()
cone.SetCenter(150, 150, 0)
cone.SetHeight(100)
cone.SetRadius(50)
cone.Update()
coneMapper = vtk.vtkPolyDataMapper()
coneMapper.SetInputData(cone.GetOutput())
coneMapper.Update()
coneActor = vtk.vtkActor()
coneActor.SetMapper(coneMapper)

ren = vtk.vtkRenderer()
ren.AddActor(coneActor)
ren.SetBackground(0.1, 0.2, 0.4)


renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(400, 400)

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

renWin.Render()
X = 100
Y = 100
picker = vtk.vtkPropPicker()
picker.Pick(X, Y, 0, ren)
pickerWorld = picker.GetPickPosition()
print('world point from vtkPropPicker: ', pickerWorld)

coordinate = vtk.vtkCoordinate()
coordinate.SetCoordinateSystemToDisplay()
coordinate.SetValue(X, Y)
coorWorld = coordinate.GetComputedWorldValue(ren)
print('world point from vtkCoordinate: ', coorWorld)

from vedo import *
show(coneActor,
     Point(pickerWorld, c='green'),
     Point(coorWorld, c='red'),
     axes=1,
)
