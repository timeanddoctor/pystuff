import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPalette

class View2DStacked(QStackedWidget):
  def __init__(self, parent=None):
    super(View2DStacked, self).__init__(parent)
    for i in range(3):
      widget = QWidget(self)
      widget.setGeometry(0,0,400,300)
      tColor0 = {0:"red", 1:"green", 2:"blue"}[i]
      tColor1 = {0:"red", 1:"green", 2:"blue"}[(i+1) % 3]
      widget.setStyleSheet("background-color:" + tColor0 + ";")
      pb = QPushButton(tColor1)
      pb.clicked.connect(self.buttonClicked)
      hbox = QHBoxLayout(widget)
      hbox.addWidget(pb)
      self.addWidget(widget)
  def buttonClicked(self):
    index = self.currentIndex()
    index = index + 1
    index = index % 3
    self.setCurrentIndex(index)
    
if __name__ == "__main__":
  app = QApplication([])
  w = QWidget()
  w.setWindowTitle("Musketeers")

  btn1 = QPushButton("Athos")

  hbox = QHBoxLayout(w)

  stack = View2DStacked()
  
  hbox.addWidget(stack)

  w.show()

  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
  
