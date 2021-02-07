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

    
def Clicked():
  state = pb.property("state")
  if state == 0:
    step = 1
  else:
    if state == 2:
      step = -1
    else:
      step = pb.property("state-step")
  pb.setProperty("state", state + step)
  pb.setProperty("state-step", step) # update in case it changed

  # Changing the property is not enough to choose a new style from the
  # stylesheet, it is necessary to force a re-evaluation
  pb.style().unpolish(pb)
  pb.style().polish(pb)
  return
  
  #step = 
if __name__ == "__main__":
  app = QApplication([])
  w = QWidget()
  w.setWindowTitle("Musketeers")

  hbox = QHBoxLayout(w)

  #stack = View2DStacked()
  pb = QPushButton("Tristate")
  pb.setProperty("state", 0)
  pb.setProperty("state-step", 1)
  pb.setStyleSheet("QPushButton[state=\"0\"] {background: red; }"
                   "QPushButton[state=\"1\"] {background: grey; }"
                   "QPushButton[state=\"2\"] {background: blue; }")
  pb.clicked.connect(Clicked)

  

  pb1 = QPushButton("A")
  pb1.setCheckable(True)
  pb1.setStyleSheet("QPushButton{background-color:gray;}"
                    "QPushButton:checked{background-color:red;}")
  
  pb0 = QPushButton()
  style = QCommonStyle()
  pb0.setIcon(style.standardIcon(QStyle.SP_ArrowBack))
  hbox.addWidget(pb)
  hbox.addWidget(pb0)
  hbox.addWidget(pb1)
  w.show()

  sys.exit(app.exec_())

# Local variables: #
# tab-width: 2 #
# python-indent: 2 #
# indent-tabs-mode: nil #
# End: #
  
