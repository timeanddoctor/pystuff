from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

import vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

# This is for demonstration only. For the production code, we will do
# something radically different
from skimage.segmentation import (morphological_chan_vese,
                                  checkerboard_level_set)

class SegmentationTask(QObject):
  done = pyqtSignal()
  def __init__(self, parent = None):
    super().__init__(parent)

  @pyqtSlot('PyQt_PyObject')    
  def execute(self, arg):
    # Actual work - now done using SciPy
    print("running")
    return

    smoother = vtk.vtkImageGaussianSmooth()
    smoother.SetStandardDeviations(2.0, 2.0)
    smoother.SetDimensionality(2)
    smoother.SetInputData(arg)
    smoother.Update()
    
    # Save to disk
    writer = vtk.vtkMetaImageWriter()
    writer.SetFileName('./output.mhd')
    writer.SetInputConnection(smoother.GetOutputPort())
    writer.Write()

    # Convert VTK to NumPy image
    dims = arg.GetDimensions()
    vtk_array = arg.GetPointData().GetScalars()
    nComponents = vtk_array.GetNumberOfComponents()
    temp = vtk_to_numpy(vtk_array).reshape(dims[2], dims[1], dims[0], nComponents)
    npData = temp[:,:,:,0].reshape(dims[1], dims[0])

    # Segment using SciPy
    init_ls = checkerboard_level_set(npData.shape, 6) # was 6
    contours0 = morphological_chan_vese(npData, 8, init_level_set=init_ls, smoothing=2)
    data = 255*contours0[None,:]
    #vtkData = toVtkImageData(data)

    
    
    self.done.emit()

class SegmentationService(QObject):
  # Signal to emit to perform segmentation
  execute = pyqtSignal('PyQt_PyObject')
  # Consider argument 
  def __init__(self, parent = None):
    super(SegmentationService, self).__init__(parent)
    self.workerThread = QThread(self)
    self.worker = SegmentationTask()
    self.worker.moveToThread(self.workerThread)
    self.execute.connect(self.worker.execute)
    self.workerThread.finished.connect(self.worker.deleteLater)
    self.workerThread.start()
    if parent is not None:
        parent.destroyed.connect(self.cleanUp)
  def cleanUp(self):
    # TODO: Call this when parent is destroyed
    print("clean up")
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
