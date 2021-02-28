from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

import vtk

from vtkUtils import CloudMeanDist

# This is for demonstration only. For the production code, we will use
# a non-linear version of ICP and compute absolute RMSE.

class RegistrationTask(QObject):
  done = pyqtSignal(float, 'PyQt_PyObject', 'PyQt_PyObject')
  def __init__(self, parent = None):
    super().__init__(parent)

  @pyqtSlot('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject')    
  def execute(self, contour, alignment, surfaceFilter):
    """
    Contour: Result from US segmentation (world coordinates).
    Alignment: Pseudo transform applied to CT surface for misalignment
    SurfaceFilter: Filter, which output surface with normals
    """
    surface = surfaceFilter.GetOutput()

    # Invert transform, such that the misalignment can be applied to US data
    inverse = vtk.vtkTransform()
    inverse.DeepCopy(alignment)
    inverse.PostMultiply()
    inverse.Inverse()

    # We do not want to move CT data, so we apply the inverse to US
    transformPolyDataFilter0 = vtk.vtkTransformPolyDataFilter()
    transformPolyDataFilter0.SetInputData(contour)
    transformPolyDataFilter0.SetTransform(inverse)
    transformPolyDataFilter0.Update()
    wrongContours = transformPolyDataFilter0.GetOutput()

    icp = vtk.vtkIterativeClosestPointTransform()
    icp.SetSource(wrongContours) # US contour
    icp.SetTarget(surface)       # CT surface
    icp.GetLandmarkTransform().SetModeToRigidBody()
    icp.DebugOn()
    icp.SetMaximumNumberOfIterations(10)
    icp.StartByMatchingCentroidsOff() # Must be off
    icp.SetMeanDistanceModeToRMS()
    icp.Modified()
    icp.Update()

    # Transform US to find RMSE
    transformPolyDataFilter1 = vtk.vtkTransformPolyDataFilter()
    transformPolyDataFilter1.SetInputData(wrongContours)
    transformPolyDataFilter1.SetTransform(icp)
    transformPolyDataFilter1.Update()

    # Compute RMSE
    correctedContours = transformPolyDataFilter1.GetOutput()
    rmse = CloudMeanDist(correctedContours, surface)

    # We cannot call Inverse on transform, since it is an ICP and will
    # issue a registration where source and target are interchanged
    mat = vtk.vtkMatrix4x4()
    mat.DeepCopy(icp.GetMatrix())
    
    # Emit done with output
    self.done.emit(rmse, mat, correctedContours)

class RegistrationService(QObject):
  # Signal to emit to perform registration
  execute = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject')

  # Signal emitted when registration is ready
  ready = pyqtSignal(float, 'PyQt_PyObject', 'PyQt_PyObject')

  def __init__(self, parent = None):
    super(RegistrationService, self).__init__(parent)
    self.workerThread = QThread(self)
    self.worker = RegistrationTask()
    self.worker.moveToThread(self.workerThread)
    self.execute.connect(self.worker.execute)
    self.worker.done.connect(self.workerDone)
    self.workerThread.finished.connect(self.worker.deleteLater)
    self.workerThread.start()
    if parent is not None:
        parent.destroyed.connect(self.cleanUp)

  @pyqtSlot(float, 'PyQt_PyObject', 'PyQt_PyObject')
  def workerDone(self,rmse, transform, corrected):
    # Worker attaches to this slot
    self.ready.emit(rmse, transform, corrected)
        
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
