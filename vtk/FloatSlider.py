#--- QT imports
from PyQt5 import QtGui
from PyQt5 import QtCore

from PyQt5.QtGui import *
from PyQt5.QtCore import *

from PyQt5.QtWidgets import QSlider

class QFloatSlider(QSlider):
  floatValueChanged = pyqtSignal(float)

  def __init__(self, orientation:Qt.Orientation, parent=None):
    super(QFloatSlider,self).__init__(orientation, parent)
    self.floatMin   = 0.0
    self.floatRange = 1.0
    self.setFloatValue(0.5)
    self.valueChanged.connect(self.notifyValueChanged)
    
  @pyqtSlot(int, name='notifyValueChanged')
  def notifyValueChanged(self,value):
    floatValue = self.getFloatValue()
    self.floatValueChanged.emit(floatValue)

  def getFloatValue(self):
    iRange = self.maximum() - self.minimum()
    if (iRange != 0):
      delta = self.floatRange / iRange
      floatValue = self.floatMin + delta * (self.value() - self.minimum())
    else:
      floatValue = self.floatMin
    return floatValue

  def setFloatValue(self,value):
    iRange = self.maximum() - self.minimum()
    iValue = int(iRange * (value - self.floatMin) / self.floatRange)
    super(QFloatSlider,self).setValue(iValue)
    
  def setRange(self,first,last,nValues):
    self.setMinimum(first)
    self.floatRange = (last-first)
    super(QFloatSlider,self).setRange(0,nValues-1)

  def setMinimum(self,value):
    self.floatMin = value
    pass

  def setMaximum(self,a):
    self.floatRange = a - self.floatMin
    pass

  def setSingleStep(self,step):
    """
    TODO: Increase resolution to match exactly and respect maximum
    """
    nStep = int(self.floatRange / step)
    super(QFloatSlider,self).setSingleStep(nStep)
    pass

  def setPageStep(self,step):
    """
    TODO: Increase resolution to match exactly and respect maximum
    """
    nStep = int(self.floatRange / step)
    super(QFloatSlider,self).setPageStep(nStep)
    pass
