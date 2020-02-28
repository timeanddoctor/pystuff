import sys
import numpy as np

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import (QtWidgets, QtGui, uic)
from PyQt5.QtCore import qDebug, QObject, Qt, QItemSelectionModel

from transform import (TransformModel, TransformDelegate, TreeItem, TreeModel)

from FloatSlider import QFloatSlider
ui, QMainWindow = uic.loadUiType('Trans_app_Qt_VTK.ui')

colors = vtk.vtkNamedColors()

class ViewersApp(QMainWindow, ui):
  def __init__(self):
    #Parent constructor
    super(ViewersApp, self).__init__()
    self.vtk_widget = None
    self.setup()

  def setup(self):
    self.setupUi(self)

    # replace widgets
    nSliders = self.verticalSliderLayout.count()
    index = nSliders - 1
    while (index >=0):
      myWidget = self.verticalSliderLayout.itemAt(index).widget()
      myWidget.setParent(None)
      myWidget.close()
      index = index - 1

    self.floatSlider = []
    for index in range(nSliders):
      tmp = QFloatSlider(self, Qt.Horizontal)
      self.floatSlider.append(tmp)
      self.verticalSliderLayout.addWidget(tmp)

    self.vtk_widget = QMeshViewer(self.vtk_panel)

    # Add a layout to let the vtk panel grow/shrink with window resize
    self.vtk_layout = QtWidgets.QHBoxLayout()
    self.vtk_layout.addWidget(self.vtk_widget)
    self.vtk_layout.setContentsMargins(0,0,0,0)
    self.vtk_panel.setLayout(self.vtk_layout)

    # Initialize model for transformations
    data = np.diag(np.ones(4))
    self.affineTransform = TransformModel(data)

    self.tblTransform.setModel(self.affineTransform)
    self.tblTransform.horizontalHeader().hide()
    self.tblTransform.verticalHeader().hide()
    self.tblTransform.setVisible(False)

    header = self.tblTransform.horizontalHeader()
    header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
    header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
    header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
    header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

    header = self.tblTransform.verticalHeader()
    header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
    header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
    header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
    header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)

    # Set delegates (if any)
    self.delegate = TransformDelegate(self)
    self.tblTransform.setItemDelegate(self.delegate)
    self.tblTransform.setVisible(True)

    # Tree view model
    headers = ("Title", "Description", "Source", "Dest")
    self.treeModel = TreeModel(headers, self.vtk_widget.axes)
    self.treeView.setModel(self.treeModel)
    self.treeView.selectionModel().selectionChanged.connect(self.updateActions)
    self.treeModel.dataChanged.connect(self.updateFrames)

    self.treeView.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
    self.treeView.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

    # Connects slots and signals
    self.btnUpdate.clicked.connect(self.onUpdateClicked)
    self.insertRowAction.triggered.connect(self.insertRow)
    self.removeRowAction.triggered.connect(self.removeRow)
    self.insertChildAction.triggered.connect(self.insertChild)

  def insertChild(self):
    index = self.treeView.selectionModel().currentIndex()
    model = self.treeView.model()

    if model.columnCount(index) == 0:
      if not model.insertColumn(0, index):
        return

    if not model.insertRow(0, index):
      return

    # Update data for new entry (4 visible columns and 1 hidden = user data)
    for column in range(model.columnCount(index)):
      child = model.index(0, column, index)
      if column < 2:
        # Name and description
        model.setData(child, "[No name]", Qt.EditRole)
      elif column < 4:
        # Source or destination check-boxes
        model.setData(child, Qt.Unchecked, Qt.CheckStateRole)
      else:
        # User data
        axes = self.vtk_widget.createNewActor()
        self.vtk_widget.addActor(axes)
        model.setData(child, axes, Qt.UserRole)
      if model.headerData(column, Qt.Horizontal) is None:
        model.setHeaderData(column, Qt.Horizontal, "[No header]",
                            Qt.EditRole)

    self.treeView.selectionModel().setCurrentIndex(model.index(0, 0, index),
                                                   QItemSelectionModel.ClearAndSelect)
    self.updateActions()

  def insertRow(self):
    index = self.treeView.selectionModel().currentIndex()
    model = self.treeView.model()

    if not model.insertRow(index.row()+1, index.parent()):
      return

    self.updateActions()

    for column in range(model.columnCount(index.parent())):
      child = model.index(index.row()+1, column, index.parent())
      if column < 2:
        model.setData(child, "[No name]", Qt.EditRole)
      elif column < 4:
        model.setData(child, Qt.Unchecked, Qt.CheckStateRole)
      else:
        axes = self.vtk_widget.createNewActor()
        self.vtk_widget.addActor(axes)
        model.setData(child, axes, Qt.UserRole)

  def removeRow(self):
      index = self.treeView.selectionModel().currentIndex()
      model = self.treeView.model()
      item = model.getItem(index)
      if (model.removeRow(index.row(), index.parent())):
        actor = item.itemData[4]
        self.vtk_widget.removeActor(actor)
        self.updateActions()

  def updateGlyph(self, item):
    self.vtk_widget.interactor.Disable()
    axes = item.itemData[4]
    if axes is not None:
      if item.isSource():
        newColorX = colors.GetColor3d('darkslategray')
        newColorY = colors.GetColor3d('darkslategray')
        newColorZ = colors.GetColor3d('darkslategray')
      elif item.isDest():
        newColorX = colors.GetColor3d('lightslategray')
        newColorY = colors.GetColor3d('lightslategray')
        newColorZ = colors.GetColor3d('lightslategray')
      else:
        newColorX = vtk.vtkColor3d(1.0,0.0,0.0)
        newColorY = vtk.vtkColor3d(0.0,1.0,0.0)
        newColorZ = vtk.vtkColor3d(0.0,0.0,1.0)

      axes.GetXAxisShaftProperty().SetColor(newColorX)
      axes.GetYAxisShaftProperty().SetColor(newColorY)
      axes.GetZAxisShaftProperty().SetColor(newColorZ)
      axes.GetXAxisTipProperty().SetColor(newColorX)
      axes.GetYAxisTipProperty().SetColor(newColorY)
      axes.GetZAxisTipProperty().SetColor(newColorZ)

      self.vtk_widget.interactor.Enable()
      self.vtk_widget.render_window.Render()

  def updateFrames(self, topLeft, bottomRight, role):
    if topLeft == bottomRight:
      index = topLeft
      if index.isValid():
        if len(role) > 0:
          if role[0] == Qt.CheckStateRole:
            index = topLeft
            model = self.treeView.model()
            item  = model.getItem(index)
            self.updateGlyph(item)


  def updateActions(self):
      hasSelection = not self.treeView.selectionModel().selection().isEmpty()
      self.removeRowAction.setEnabled(hasSelection)
      #self.removeColumnAction.setEnabled(hasSelection)

      hasCurrent = self.treeView.selectionModel().currentIndex().isValid()
      self.insertRowAction.setEnabled(hasCurrent)
      #self.insertColumnAction.setEnabled(hasCurrent)

      if hasCurrent:
          self.treeView.closePersistentEditor(self.treeView.selectionModel().currentIndex())

          row = self.treeView.selectionModel().currentIndex().row()
          column = self.treeView.selectionModel().currentIndex().column()
          if self.treeView.selectionModel().currentIndex().parent().isValid():
              self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
          else:
              self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))
          model = self.treeView.model()
          index = self.treeView.selectionModel().currentIndex()
          item = model.getItem(index)
          if item is not None:
            self.updateTable(item)

  def updateTable(self, item):
    axes = item.itemData[4]
    arr = np.diag(np.ones(4))
    transform = axes.GetUserTransform()
    if transform is not None:
      mat = transform.GetMatrix()
      for i in range(4):
        for j in range(4):
          arr[i,j] = mat.GetElement(i,j)
    self.affineTransform.setAllData(arr)
  def initialize(self):
    self.vtk_widget.start()

  def onUpdateClicked(self):
    index = self.treeView.selectionModel().currentIndex()
    if index.isValid():
      item = self.treeModel.getItem(index)
      aff = self.affineTransform.getData()
      axes = item.itemData[4]
      self.vtk_widget.moveAxes(axes, aff)

class QMeshViewer(QtWidgets.QFrame):
  def __init__(self, parent):
    super(QMeshViewer,self).__init__(parent)

    self.platformModel:vtk.vtkCubeSource = None
    self.platformGrid:vtk.vtkPolyData = None
    self.platformModelActor:vtk.vtkActor = None
    self.platformGridActor:vtk.vtkActor = None

    self.platformWidth:float = 200.0
    self.platformDepth:float = 200.0
    self.platformThickness:float = 2.0
    self.gridBottomHeight:float = 0.15
    self.gridSize:np.uint16 = 10

    # Make the actual QtWidget a child so that it can be re_parented
    self.interactor = QVTKRenderWindowInteractor(self)
    self.layout = QtWidgets.QHBoxLayout()
    self.layout.addWidget(self.interactor)
    self.layout.setContentsMargins(0,0,0,0)
    self.setLayout(self.layout)

    self.initScene()
    self.initPlatform()
    self.initAxes()
    self.resetCamera()

    self.style = vtk.vtkInteractorStyleTrackballCamera()
    self.style.SetDefaultRenderer(self.renderer)
    self.interactor.SetInteractorStyle(self.style)

  def resetCamera(self):
    m_camPositionX = -237.885
    m_camPositionY = -392.348
    m_camPositionZ = 369.477
    self.renderer.GetActiveCamera().SetPosition(m_camPositionX, m_camPositionY, m_camPositionZ)
    self.renderer.GetActiveCamera().SetFocalPoint(0.0, 0.0, 0.0)
    self.renderer.GetActiveCamera().SetViewUp(0.0, 0.0, 1.0)
    self.renderer.ResetCameraClippingRange()

  def initScene(self):
    qDebug('initScene()')
    self.renderer =  vtk.vtkOpenGLRenderer()
    self.render_window = self.interactor.GetRenderWindow()
    self.render_window.AddRenderer(self.renderer)

    self.cellPicker = vtk.vtkCellPicker()
    self.cellPicker.SetTolerance(30.0)
    self.interactor.SetPicker(self.cellPicker)

    #* Top background color
    bg_t = np.ones(3)*245.0/255.0

    #* Bottom background color
    bg_b = np.ones(3)*170.0/255.0

    self.renderer.SetBackground(bg_t)
    self.renderer.SetBackground2(bg_b)
    self.renderer.GradientBackgroundOn()

  def createNewActor(self):
    axes = vtk.vtkAxesActor()
    axes_length = 50.0
    axes_label_font_size = np.int16(20)
    axes.SetTotalLength(axes_length, axes_length, axes_length)
    axes.SetCylinderRadius(0.01)
    axes.SetShaftTypeToCylinder()
    axes.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
    axes.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
    axes.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
    axes.GetXAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
    axes.GetYAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
    axes.GetZAxisCaptionActor2D().GetCaptionTextProperty().SetFontSize(axes_label_font_size)
    axes.PickableOn()
    return axes

  def initAxes(self):
    # #* Axes
    axes = self.createNewActor()
    self.axes = axes
    self.renderer.AddActor(self.axes)

  def initPlatform(self):
    qDebug('initPlatform()')

    #* Platform Model
    platformModelMapper = vtk.vtkPolyDataMapper()

    self.platformModel = vtk.vtkCubeSource()
    platformModelMapper.SetInputConnection(self.platformModel.GetOutputPort())

    self.platformModelActor = vtk.vtkActor()
    self.platformModelActor.SetMapper(platformModelMapper)
    self.platformModelActor.GetProperty().SetColor(1, 1, 1)
    self.platformModelActor.GetProperty().LightingOn()
    self.platformModelActor.GetProperty().SetOpacity(1)
    self.platformModelActor.GetProperty().SetAmbient(0.45)
    self.platformModelActor.GetProperty().SetDiffuse(0.4)

    self.platformModelActor.PickableOff()
    self.renderer.AddActor(self.platformModelActor)

    #* Platform Grid
    self.platformGrid = vtk.vtkPolyData()

    platformGridMapper = vtk.vtkPolyDataMapper()
    platformGridMapper.SetInputData(self.platformGrid)

    self.platformGridActor = vtk.vtkActor()
    self.platformGridActor.SetMapper(platformGridMapper)
    self.platformGridActor.GetProperty().LightingOff()
    self.platformGridActor.GetProperty().SetColor(0.45, 0.45, 0.45)
    self.platformGridActor.GetProperty().SetOpacity(1)
    self.platformGridActor.PickableOff()
    self.renderer.AddActor(self.platformGridActor)
    self.updatePlatform()

  def updatePlatform(self):
    qDebug('updatePlatform()')

    #* Platform Model
    if self.platformModel:
      self.platformModel.SetXLength(self.platformWidth)
      self.platformModel.SetYLength(self.platformDepth)
      self.platformModel.SetZLength(self.platformThickness)
      self.platformModel.SetCenter(0.0, 0.0, -self.platformThickness / 2)

    #* Platform Grid
    gridPoints = vtk.vtkPoints()
    gridCells = vtk.vtkCellArray()

    i = -self.platformWidth / 2
    while i <= self.platformWidth / 2:
      self.createLine(i, -self.platformDepth / 2, self.gridBottomHeight, i, self.platformDepth / 2, self.gridBottomHeight, gridPoints, gridCells)
      i += self.gridSize

    i = -self.platformDepth / 2
    while i <= self.platformDepth / 2:
      self.createLine(-self.platformWidth / 2, i, self.gridBottomHeight, self.platformWidth / 2, i, self.gridBottomHeight, gridPoints, gridCells)
      i += self.gridSize

    self.platformGrid.SetPoints(gridPoints)
    self.platformGrid.SetLines(gridCells)

  def createLine(self, x1:float, y1:float, z1:float, x2:float, y2:float, z2:float, points:vtk.vtkPoints, cells:vtk.vtkCellArray):
    line = vtk.vtkPolyLine()
    line.GetPointIds().SetNumberOfIds(2)

    id_1 = points.InsertNextPoint(x1, y1, z1) # vtkIdType
    id_2 = points.InsertNextPoint(x2, y2, z2) # vtkIdType

    line.GetPointIds().SetId(0, id_1)
    line.GetPointIds().SetId(1, id_2)
    cells.InsertNextCell(line)

  def start(self):
    self.interactor.Initialize()
    # If a big Qt application, call app.exec instead of having two GUI threads
    self.interactor.Start()

  def moveAxes(self, axes, aff):
    self.interactor.Disable()

    # Axes
    transform = vtk.vtkTransform()
    mat = vtk.vtkMatrix4x4()
    for i in range(4):
      for j in range(4):
        mat.SetElement(i,j,aff[i,j])
    transform.SetMatrix(mat)
    axes.SetUserTransform(transform)
    self.interactor.Enable()
    self.render_window.Render()

  def removeActor(self, actor):
    self.interactor.Disable()
    self.renderer.RemoveActor(actor)
    self.interactor.Enable()
    self.render_window.Render()

  def addActor(self, actor):
    self.interactor.Disable()
    self.renderer.AddActor(actor)
    self.interactor.Enable()
    self.render_window.Render()

if __name__ == '__main__':
  app = QtWidgets.QApplication(["Trans-App"])
  main_window = ViewersApp()
  main_window.show()
  main_window.initialize()
  app.exec_()

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
