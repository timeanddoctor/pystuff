from qt import Signal, Property

from qtpy.QtCore import QObject, QUrl, qDebug, qCritical, Slot, Qt, QFileInfo, QSettings
from qtpy.QtQml import QQmlApplicationEngine, qmlRegisterType, QQmlEngine
from qtpy.QtWidgets import QApplication

from qtpy.QtGui import QIcon

import qtpy.QtGui as QtGui

import qtpy.QtCharts

from QVTKFramebufferObjectItem import FboItem

def defaultFormat(stereo_capable):
  """ Po prostu skopiowałem to z https://github.com/Kitware/VTK/blob/master/GUISupport/Qt/QVTKRenderWindowAdapter.cxx
     i działa poprawnie bufor głębokości
  """
  fmt = QtGui.QSurfaceFormat()
  fmt.setRenderableType(QtGui.QSurfaceFormat.OpenGL)
  fmt.setVersion(3, 2)
  fmt.setProfile(QtGui.QSurfaceFormat.CoreProfile)
  fmt.setSwapBehavior(QtGui.QSurfaceFormat.DoubleBuffer)
  fmt.setRedBufferSize(8)
  fmt.setGreenBufferSize(8)
  fmt.setBlueBufferSize(8)
  fmt.setDepthBufferSize(8)
  fmt.setAlphaBufferSize(8)
  fmt.setStencilBufferSize(0)
  fmt.setStereo(stereo_capable)
  fmt.setSamples(0)

  return fmt

class ChartDataProvider(QObject):
  def __init__(self, parent=None):
    super(ChartDataProvider, self).__init__(parent)

  @Slot(qtpy.QtCore.QObject)
  def fillData(self, series):
    print(series)
    series.append(0.1,0.23)
    series.append(0.4,0.3)
    series.append(0.7,0.75)
    series.append(0.85,0.65)
    series.setName("Czy to ładny przebieg?")

class CanvasHandler(QObject):
  DEFAULT_MODEL_DIR_KEY = "default_model_dir"
  def __init__(self, sys_argv):
    super().__init__()
    self.__m_vtkFboItem = None
    #sys_argv += ['--style', 'Material'] #! MUST HAVE
    #sys_argv += ['--style', 'Fusion'] #! MUST HAVE
    sys_argv += ['--style', 'Windows'] #! MUST HAVE


    QApplication.setAttribute( Qt.AA_UseDesktopOpenGL )
    QtGui.QSurfaceFormat.setDefaultFormat(defaultFormat(False)) # from vtk 8.2.0
    app = QApplication(sys_argv)
    app.setApplicationName("QtQuickVTK");
    app.setWindowIcon(QIcon(":/resources/bq.ico"));
    app.setOrganizationName("Sexy Soft");
    app.setOrganizationDomain("www.sexysoft.com");

    engine = QQmlApplicationEngine()
    app.setApplicationName('QtVTK-Py')

    # Register QML Types
    qmlRegisterType(FboItem, 'QtVTK', 1, 0, 'VtkFboItem')

    # Expose/Bind Python classes (QObject) to QML
    ctxt = engine.rootContext() # returns QQmlContext
    ctxt.setContextProperty('canvasHandler', self)
    self.dataProvider = ChartDataProvider()
    ctxt.setContextProperty('chartDataProvider', self.dataProvider)

    # Load main QML file
    engine.load(QUrl.fromLocalFile('resources/main.qml'))

    # Get reference to the QVTKFramebufferObjectItem in QML
    rootObject = engine.rootObjects()[0] # returns QObject
    self.__m_vtkFboItem = rootObject.findChild(FboItem, 'vtkFboItem')

    # Give the vtkFboItem reference to the CanvasHandler
    if (self.__m_vtkFboItem):
      qDebug('CanvasHandler::CanvasHandler: setting vtkFboItem to CanvasHandler')
      self.__m_vtkFboItem.rendererInitialized.connect(self.startApplication)
    else:
      qCritical('CanvasHandler::CanvasHandler: Unable to get vtkFboItem instance')
      return

    MySettings = QSettings()

    print("load Settings")

    self.fileDialog = rootObject.findChild(QObject, "myFileDialog")
    if (self.fileDialog is not None):
      tmp = MySettings.value(CanvasHandler.DEFAULT_MODEL_DIR_KEY)
      print(tmp)
      self.fileDialog.setProperty("folder", QUrl.fromLocalFile(tmp))


    rc = app.exec_()
    qDebug(f'CanvasHandler::CanvasHandler: Execution finished with return code: {rc}')

  @Slot(str)
  def openModel(self, fileName):
    print(f'Otwieram: {fileName}')
    self.__m_vtkFboItem.addModel(fileName)

    localFilePath = QUrl(fileName).toLocalFile()

    currentDir = QFileInfo(localFilePath).absoluteDir()
    currentPath = currentDir.absolutePath()

    MySettings = QSettings()
    MySettings.setValue(CanvasHandler.DEFAULT_MODEL_DIR_KEY, currentPath);
    print(currentPath)

  @Slot(int,int,int)
  def mousePressEvent(self, button:int, screenX:int, screenY:int):
    qDebug('CanvasHandler::mousePressEvent()')

  @Slot(int,int,int)
  def mouseMoveEvent(self, button:int, screenX:int, screenY:int):
    qDebug('CanvasHandler::mouseMoveEvent()')


  @Slot(int,int,int)
  def mouseReleaseEvent(self, button:int, screenX:int, screenY:int):
    qDebug('CanvasHandler::mouseReleaseEvent()')


  def startApplication(self):
    qDebug('CanvasHandler::startApplication()')
    self.__m_vtkFboItem.rendererInitialized.disconnect(self.startApplication)

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
