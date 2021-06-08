def extractBoundaryIds(source):
    idFilter = vtk.vtkIdFilter()
    idFilter.SetInputConnection(source.GetOutputPort())
    idFilter.SetIdsArrayName("ids")
    idFilter.SetPointIds(True)
    idFilter.SetCellIds(False)
    # Available for vtk>=8.3:
    #idFilter.SetPointIdsArrayName(arrayName)
    #idFilter.SetCellIdsArrayName(arrayName)
    idFilter.Update()

    edges = vtk.vtkFeatureEdges()
    edges.SetInputConnection(idFilter.GetOutputPort())
    edges.BoundaryEdgesOn()
    edges.ManifoldEdgesOff()
    edges.NonManifoldEdgesOff()
    edges.FeatureEdgesOff()
    edges.Update()

    array = edges.GetOutput().GetPointData().GetArray("ids")
    n = edges.GetOutput().GetNumberOfPoints()
    boundaryIds = []
    for i in range(n):
        boundaryIds.append(array.GetValue(i))
    return boundaryIds
