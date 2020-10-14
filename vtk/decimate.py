from vtk import (vtkSphereSource, vtkPolyData, vtkDecimatePro)


def decimation():
    sphereS = vtkSphereSource()
    sphereS.Update()

    inputPoly = vtkPolyData()
    inputPoly.ShallowCopy(sphereS.GetOutput())

    print("Before decimation\n"
          "-----------------\n"
          "There are " + str(inputPoly.GetNumberOfPoints()) + "points.\n"
          "There are " + str(inputPoly.GetNumberOfPolys()) + "polygons.\n")

    decimate = vtkDecimatePro()
    decimate.SetInputData(inputPoly)
    decimate.SetTargetReduction(.10)
    decimate.Update()

    decimatedPoly = vtkPolyData()
    decimatedPoly.ShallowCopy(decimate.GetOutput())

    print("After decimation \n"
          "-----------------\n"
          "There are " + str(decimatedPoly.GetNumberOfPoints()) + "points.\n"
          "There are " + str(decimatedPoly.GetNumberOfPolys()) + "polygons.\n")


if __name__ == "__main__":
    decimation()
