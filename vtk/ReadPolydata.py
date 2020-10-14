# Convert vtkPolyData to o3d files with vertices

import sys

import vtk

import numpy as np

from mpl_toolkits.mplot3d import art3d
import matplotlib.colors as colors
import matplotlib.cm as cm
import matplotlib.pyplot as plt

sys.path.append('/home/jmh/github/registration/python')

import addpaths

plt.ion()

def get2Dvessels():
  #filename = './2D_old.vtp'
  filename = './2D.vtp'

  # Read all the data from the file
  reader = vtk.vtkXMLPolyDataReader()
  reader.SetFileName(filename)
  reader.Update()

  mesh = reader.GetOutput()

  points = mesh.GetPoints() # vtkPoints

  dataArray = points.GetData() # vtkDataArray

  faceIndex = vtk.vtkIdList()

  nFaces = mesh.GetNumberOfCells()

  npoints = 0
  for i in range(nFaces):
    mesh.GetCellPoints(i, faceIndex)
    npoints = npoints + faceIndex.GetNumberOfIds()

  points = np.zeros((npoints,3), dtype=np.float)

  k = 0
  for i in range(nFaces):
    mesh.GetCellPoints(i, faceIndex)
    npoints = faceIndex.GetNumberOfIds()
    for j in range(npoints):
      vertexIndex = faceIndex.GetId(j)
      points[k,0] = dataArray.GetComponent(vertexIndex, 0)
      points[k,1] = dataArray.GetComponent(vertexIndex, 1)
      points[k,2] = dataArray.GetComponent(vertexIndex, 2)
      k = k + 1
  return points

def get3Dvessels():
  #filename = './3D.vtp'
  filename = './Connected.vtp'

  # Read all the data from the file
  reader = vtk.vtkXMLPolyDataReader()
  reader.SetFileName(filename)
  reader.Update()

  mesh = reader.GetOutput()

  points = mesh.GetPoints() # vtkPoints

  dataArray = points.GetData() # vtkDataArray

  nFaces = mesh.GetNumberOfCells()

  faceIndex = vtk.vtkIdList()

  vertexArray = np.zeros((nFaces,3,3))


  # Anticipates this is triangles!!!
  for i in range(nFaces):
    mesh.GetCellPoints(i, faceIndex)
    vertexIndex = faceIndex.GetId(0)
    vertexArray[i,0,0] = dataArray.GetComponent(vertexIndex, 0)
    vertexArray[i,0,1] = dataArray.GetComponent(vertexIndex, 1)
    vertexArray[i,0,2] = dataArray.GetComponent(vertexIndex, 2)
    vertexIndex = faceIndex.GetId(1)
    vertexArray[i,1,0] = dataArray.GetComponent(vertexIndex, 0)
    vertexArray[i,1,1] = dataArray.GetComponent(vertexIndex, 1)
    vertexArray[i,1,2] = dataArray.GetComponent(vertexIndex, 2)
    vertexIndex = faceIndex.GetId(2)
    vertexArray[i,2,0] = dataArray.GetComponent(vertexIndex, 0)
    vertexArray[i,2,1] = dataArray.GetComponent(vertexIndex, 1)
    vertexArray[i,2,2] = dataArray.GetComponent(vertexIndex, 2)

  data = vertexArray.reshape((nFaces*3,3))

  return data

vesselTree = get3Dvessels()
vesselPlane = get2Dvessels()

nDecimate = 1
vesselTree = vesselTree[::nDecimate,:]

# Save to open3d
import open3d as o3d

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(vesselTree)
o3d.io.write_point_cloud("./vesseltree.pcd", pcd)

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(vesselPlane)
o3d.io.write_point_cloud("./vesselplane.pcd", pcd)


if 1:
  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')

  ax.plot(vesselTree[:,0],
          vesselTree[:,1],
          vesselTree[:,2], 'k+')

  ax.plot(vesselPlane[:,0],
          vesselPlane[:,1],
          vesselPlane[:,2], 'ro')
if 0:
  import swig_registration as registration

  from rigid import (rigid, normalize)

  X = vesselTree
  Y = vesselPlane

  # 80% outliers
  show = True
  T, TF = rigid(X, Y, normalize=False, show=show, scale=False, w=0.9, tol=1e-6, maxIter=3)
