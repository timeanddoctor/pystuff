import sys
import numpy as np

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import (QtWidgets, QtGui, uic)
from PyQt5.QtCore import qDebug, QObject, Qt, QItemSelectionModel

from transform import (TransformModel, TransformDelegate, TreeItem, TreeModel)

ui, QMainWindow = uic.loadUiType('Trans_app_Qt_VTK.ui')

class ViewersApp(QMainWindow, ui):
  def __init__(self):
    #Parent constructor
    super(ViewersApp, self).__init__()
    self.vtk_widget = None
    self.setup()

  def setup(self):
    self.setupUi(self)

    self.vtk_widget = QMeshViewer(self.vtk_panel)

    # add a layout to let the vtk panel grow/shrink with window resize
    self.vtk_layout = QtWidgets.QHBoxLayout()
    self.vtk_layout.addWidget(self.vtk_widget)
    self.vtk_layout.setContentsMargins(0,0,0,0)
    self.vtk_panel.setLayout(self.vtk_layout)

    # transformation matrix
    data = [[1, 0, 0 , 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]]
    self.affineTransform = TransformModel(data)

    self.tblTransform.setModel(self.affineTransform)
    self.tblTransform.horizontalHeader().hide()
    self.tblTransform.verticalHeader().hide()
    self.tblTransform.setVisible(False)
    #self.tblTransform.resizeColumnsToContents()
    #self.tblTransform.resizeRowsToContents()

    # Set delegates (if any)
    self.tblTransform.setVisible(True)

    self.delegate = TransformDelegate(self)
    self.tblTransform.setItemDelegate(self.delegate)

    headers = ("Title", "Description")

    self.treeModel = TreeModel(headers)
    self.treeView.setModel(self.treeModel)

    # connects slots and signals
    self.btnAddFrame.clicked.connect(self.onAddFrameClicked)

    self.insertRowAction.triggered.connect(self.insertRow)
    self.insertColumnAction.triggered.connect(self.insertColumn)
    self.removeRowAction.triggered.connect(self.removeRow)
    self.removeColumnAction.triggered.connect(self.removeColumn)
    self.treeView.selectionModel().selectionChanged.connect(self.updateActions)
    self.insertChildAction.triggered.connect(self.insertChild)

  def insertChild(self):
    index = self.treeView.selectionModel().currentIndex()
    model = self.treeView.model()

    if model.columnCount(index) == 0:
        if not model.insertColumn(0, index):
            return

    if not model.insertRow(0, index):
        return

    for column in range(model.columnCount(index)):
        child = model.index(0, column, index)
        model.setData(child, "[No data]", Qt.EditRole)
        if model.headerData(column, Qt.Horizontal) is None:
            model.setHeaderData(column, Qt.Horizontal, "[No header]",
                    Qt.EditRole)

    self.treeView.selectionModel().setCurrentIndex(model.index(0, 0, index),
            QItemSelectionModel.ClearAndSelect)
    self.updateActions()

  def insertColumn(self):
      model = self.treeView.model()
      column = self.treeView.selectionModel().currentIndex().column()

      changed = model.insertColumn(column + 1)
      if changed:
          model.setHeaderData(column + 1, Qt.Horizontal, "[No header]",
                  Qt.EditRole)

      self.updateActions()

      return changed

  def insertRow(self):
      index = self.treeView.selectionModel().currentIndex()
      model = self.treeView.model()

      if not model.insertRow(index.row()+1, index.parent()):
          return

      self.updateActions()

      for column in range(model.columnCount(index.parent())):
          child = model.index(index.row()+1, column, index.parent())
          model.setData(child, "[No data]", Qt.EditRole)

  def removeColumn(self):
      model = self.treeView.model()
      column = self.treeView.selectionModel().currentIndex().column()

      changed = model.removeColumn(column)
      if changed:
          self.updateActions()

      return changed

  def removeRow(self):
      index = self.treeView.selectionModel().currentIndex()
      model = self.treeView.model()

      if (model.removeRow(index.row(), index.parent())):
          self.updateActions()

  def updateActions(self):
      hasSelection = not self.treeView.selectionModel().selection().isEmpty()
      self.removeRowAction.setEnabled(hasSelection)
      self.removeColumnAction.setEnabled(hasSelection)

      hasCurrent = self.treeView.selectionModel().currentIndex().isValid()
      self.insertRowAction.setEnabled(hasCurrent)
      self.insertColumnAction.setEnabled(hasCurrent)

      if hasCurrent:
          self.treeView.closePersistentEditor(self.treeView.selectionModel().currentIndex())

          row = self.treeView.selectionModel().currentIndex().row()
          column = self.treeView.selectionModel().currentIndex().column()
          if self.treeView.selectionModel().currentIndex().parent().isValid():
              self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
          else:
              self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))

  def initialize(self):
    self.vtk_widget.start()

  def onAddFrameClicked(self):
    row = self.treeView.selectionModel().currentIndex().row()
    column = self.treeView.selectionModel().currentIndex().column()
    print("(%d, %d)" % (row, column))

    bum = self.affineTransform.getData()

    self.vtk_widget.addAxes(bum)

colors = vtk.vtkNamedColors()

# Not working
class MouseInteractorHighLightTwoActors(vtk.vtkInteractorStyleTrackballCamera):

  def __init__(self, parent=None):
    self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)

    self.firstActor = None
    self.secondActor = None
    self.firstProperty = vtk.vtkProperty()
    self.secondProperty = vtk.vtkProperty()
    self.nPicked = 0

  def leftButtonPressEvent(self, obj, event):
    self.NewPickedActor = None
    if 0:
      clickPos = self.GetInteractor().GetEventPosition()
      print(clickPos)
      picker = vtk.vtkPropPicker()
      picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())
      # Get the new actor (not working)
      self.NewPickedActor = picker.GetActor()
    elif 0:
      # World-point picker - gives coordinates
      self.GetInteractor().GetPicker().Pick(self.GetInteractor().GetEventPosition()[0],
                                            self.GetInteractor().GetEventPosition()[1],
                                            0,
                                            self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer())
      picked = self.GetInteractor().GetPicker().GetPickPosition()
      print(picked)

      picker = vtk.vtkPropPicker()
      picker.Pick(self.GetInteractor().GetEventPosition()[0],
                  self.GetInteractor().GetEventPosition()[1],
                  0,
                  self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer())
      self.NewPickedActor = picker.GetActor()
    else:
      # Cell-picker
      self.GetInteractor().GetPicker().Pick(self.GetInteractor().GetEventPosition()[0],
                                            self.GetInteractor().GetEventPosition()[1],
                                            0,
                                            self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer())
      self.NewPickedActor = self.GetInteractor().GetPicker().GetActor()
      print(self.NewPickedActor)


    # If something was selected
    if self.NewPickedActor is not None:
      print("actor is picked")
      if self.NewPickedActor == self.firstActor:
        self.firstActor.GetXAxisShaftProperty().DeepCopy(self.firstProperty)
        self.nPicked = self.nPicked - 1
        self.firstActor = None
      elif self.NewPickedActor == self.secondActor:
        self.secondActor.GetXAxisShaftProperty().DeepCopy(self.secondProperty)
        self.nPicked = self.nPicked - 1
        self.secondActor = None
      else:
        if (self.nPicked == 1):
          self.secondProperty.DeepCopy(self.NewPickedActor.GetXAxisShaftProperty())
          self.NewPickedActor.GetXAxisShaftProperty().SetColor(colors.GetColor3d('Black'))
          self.secondActor = self.NewPickedActor
          self.nPicked = self.nPicked + 1
        elif (self.nPicked == 0):
          self.firstProperty.DeepCopy(self.NewPickedActor.GetXAxisShaftProperty())
          self.NewPickedActor.GetXAxisShaftProperty().SetColor(colors.GetColor3d('Gray'))
          self.firstActor = self.NewPickedActor
          self.nPicked = self.nPicked + 1

    self.OnLeftButtonDown()
    return


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
    #self.clickPositionZ:float = 0.0

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

    self.style = MouseInteractorHighLightTwoActors()
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

    #self.worldPointPicker = vtk.vtkWorldPointPicker()
    #self.interactor.SetPicker(self.worldPointPicker)
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

  def initAxes(self):
    # #* Axes
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
    self.renderer.AddActor(axes)

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


  def initSceneOld(self):
    qDebug('initSceneOld()')

    # set up my VTK Visualization pipeline
    # cut-and-paste from https://lorensen.github.io/VTKExamples/site/Python/GeometricObjects/Sphere/

    # Create a sphere
    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetCenter(0.0,0.0,0.0)
    sphereSource.SetRadius(5.0)
    # Make the surface smooth
    sphereSource.SetPhiResolution(100)
    sphereSource.SetThetaResolution(100)

    # Create a mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphereSource.GetOutputPort())

    # Create an actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d("Cornsilk"))
    actor.GetProperty().SetRepresentation(0)
    actor.GetProperty().SetDiffuseColor(colors.GetColor3d("Cornsilk"))
    actor.GetProperty().SetDiffuse(0.8)
    actor.GetProperty().SetSpecular(0.5)
    actor.GetProperty().SetSpecularColor(1.,1.,1.)
    actor.GetProperty().SetSpecularPower(30.)

    renderer =  vtk.vtkOpenGLRenderer()
    render_window = self.interactor.GetRenderWindow()
    render_window.AddRenderer(renderer)

    # TEST
    # interactor.SetRenderWindow(render_window)
    #render_window.SetInteractor(interactor)

    renderer.AddActor(actor)
    renderer.SetBackground(colors.GetColor3d("DarkGreen"))

    self.render_window = render_window
    self.renderer = renderer
    self.sphere = sphereSource
    self.actor = actor

  def start(self):
    self.interactor.Initialize()
    # If a big Qt application call app.exec instead
    self.interactor.Start()

  def addAxes(self, aff):
    self.interactor.Disable()

    # #* Axes
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

    transform = vtk.vtkTransform()
    mat = vtk.vtkMatrix4x4()
    for i in range(4):
      for j in range(4):
        mat.SetElement(i,j,aff[i,j])
    transform.SetMatrix(mat)
    axes.SetUserTransform(transform)

    self.renderer.AddActor(axes)
    self.interactor.Enable()
    self.render_window.Render()

  def Switch_Mode(self, new_value):
    self.actor.GetProperty().SetRepresentation(new_value)
    self.render_window.Render()

  def button_event(self, new_value):
    if new_value:
      print("Button was clicked")

  def set_Resolution(self, new_value):
    self.sphere.SetPhiResolution(new_value)
    self.sphere.SetThetaResolution(new_value)
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
