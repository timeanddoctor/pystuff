from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

import vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

# This is for demonstration only. For the production code, we will do
# something radically different
from skimage.segmentation import (morphological_chan_vese,
                                  checkerboard_level_set)

class SegmentationTask(QObject):
  done = pyqtSignal('PyQt_PyObject')
  def __init__(self, parent = None):
    super().__init__(parent)

  @pyqtSlot('PyQt_PyObject', 'PyQt_PyObject')    
  def execute(self, arg, trans):
    # Number of Chan-Vese iterations
    nIter = 20
    std = 1.5 # [mm], original
    squareSize = 1.5 # [mm]
    
    saveMetaImage = False
    savePNGImage = False
    # Actual work - now done using SciPy

    # Gaussian smoothing
    dx, dy, dz = arg.GetSpacing()
    sx, sy = std / dx, std / dy
    smoother = vtk.vtkImageGaussianSmooth()
    smoother.SetStandardDeviations(sx, sy)
    smoother.SetDimensionality(2)
    smoother.SetInputData(arg)
    smoother.Update()

    if savePNGImage:
      writer = vtk.vtkPNGWriter()
      writer.SetFileName('./output.png')
      writer.SetInputConnection(smoother.GetOutputPort())
      writer.Write()
    
    if saveMetaImage:
      # Save to disk
      writer = vtk.vtkMetaImageWriter()
      writer.SetFileName('./output.mhd')
      writer.SetInputConnection(smoother.GetOutputPort())
      writer.Write()

    smoothedData = smoother.GetOutput()
    
    # Convert VTK to NumPy image
    dims = arg.GetDimensions()
    vtk_array = smoothedData.GetPointData().GetScalars()
    nComponents = vtk_array.GetNumberOfComponents()
    npData = vtk_to_numpy(vtk_array).reshape(dims[2], dims[1], dims[0], nComponents)[:,:,:,0].reshape(dims[1], dims[0])

    # Seed for active contours
    iSquareSize = int(squareSize / dx)
    init_ls = checkerboard_level_set(npData.shape, iSquareSize)

    contours = morphological_chan_vese(npData, nIter,
                                       init_level_set=init_ls, smoothing=2)
    # Add singleton to get 3-dimensional data
    data = contours[None, :]

    # Convert Numpy to VTK data
    importer = vtk.vtkImageImport()
    importer.SetDataScalarType(vtk.VTK_SIGNED_CHAR)
    importer.SetDataExtent(0,data.shape[2]-1,
                           0,data.shape[1]-1,
                           0,data.shape[0]-1)
    importer.SetWholeExtent(0,data.shape[2]-1,
                            0,data.shape[1]-1,
                            0,data.shape[0]-1)
    importer.SetImportVoidPointer(data.data)
    importer.Update()
    vtkData = importer.GetOutput()
    vtkData.SetSpacing(smoothedData.GetSpacing())
    vtkData.SetOrigin(0,0,0)
    
    # Contour filter
    contourFilter = vtk.vtkContourFilter()
    iso_value = 0.5
    contourFilter.SetInputData(vtkData)
    contourFilter.SetValue(0, iso_value)
    contourFilter.Update()
    contourFilter.ReleaseDataFlagOn()

    # Compute normals
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(contourFilter.GetOutputPort())
    normals.SetFeatureAngle(60.0)
    normals.ReleaseDataFlagOn()

    # Join line segments
    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(normals.GetOutputPort())
    stripper.ReleaseDataFlagOn()
    stripper.Update()

    # Transform data from scaled screen to world coordinates
    transformFilter = vtk.vtkTransformPolyDataFilter()
    transformFilter.SetInputConnection(stripper.GetOutputPort())
    transformFilter.SetTransform(trans)
    transformFilter.Update()
    result = transformFilter.GetOutput()
    
    # Emit done with output
    self.done.emit(result)

class SegmentationService(QObject):
  # Signal to emit to perform segmentation
  execute = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')

  # Signal emitted when segmentation is ready
  ready = pyqtSignal('PyQt_PyObject')

  def __init__(self, parent = None):
    super(SegmentationService, self).__init__(parent)
    self.workerThread = QThread(self)
    self.worker = SegmentationTask()
    self.worker.moveToThread(self.workerThread)
    self.execute.connect(self.worker.execute)
    self.worker.done.connect(self.workerDone)
    self.workerThread.finished.connect(self.worker.deleteLater)
    self.workerThread.start()
    if parent is not None:
        parent.destroyed.connect(self.cleanUp)

  @pyqtSlot('PyQt_PyObject')
  def workerDone(self,arg):
    # Worker attaches to this slot
    self.ready.emit(arg)
        
  def cleanUp(self):
    # TODO: Call this when parent is destroyed
    self.worker.deleteLater()
    self.worker = None
    self.workerThread.quit()
    self.workerThread.wait()
    self.workerThread = None


# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
