import sys
from PyQt5.QtWidgets import *

class View2DStacked(QStackWidget):
  def __init__(self, parent):
    

if __name__ == "__main__":
  app = QApplication([])
  w = QWidget()
  w.setWindowTitle("Musketeers")

  btn1 = QPushButton("Athos")

  hbox = QHBoxLayout(w)

  hbox.addWidget(btn1)

  w.show()

  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
  
