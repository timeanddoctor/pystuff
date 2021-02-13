from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
import time
import sys
import threading

#def logthread(caller):
#    print('%-25s: %s, %s' % (caller, QtCore.QThread.currentThread(), int(QtCore.QThread.currentThreadId()))


def logthread(caller):
    print('%-25s: %s, %s,' % (caller, QtCore.QThread.currentThread(), int(QtCore.QThread.currentThreadId())))
    print('%-25s: %s, %s,' % (caller, threading.current_thread().name, threading.current_thread().ident))


class Worker(QtCore.QObject):
    done = pyqtSignal()

    def __init__(self, parent=None):
        logthread('worker.__init__')
        super().__init__(parent)

    def run(self, m=10):
        logthread('worker.run')
        for x in range(m):
            y = x + 2
            time.sleep(0.001)
        logthread('worker.run finished')

        self.done.emit()


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        logthread('mainwin.__init__')
        super().__init__(parent)

        self.worker = Worker()
        self.workerThread = None

        self.btn = QtWidgets.QPushButton('Start worker in thread')
        self.btn2 = QtWidgets.QPushButton('Run worker here')
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.btn)
        layout.addWidget(self.btn2)

        self.run()

    def run(self):
        logthread('mainwin.run')

        self.workerThread = QtCore.QThread()
        self.worker.moveToThread(self.workerThread)
        self.worker.done.connect(self.workerDone)
        self.btn.clicked.connect(self.worker.run)
        self.btn2.clicked.connect(self.runWorkerHere)

        self.workerThread.start()
        self.show()

    def workerDone(self):
        logthread('mainwin.workerDone')

    def runWorkerHere(self):
        logthread('mainwin.runWorkerHere')
        self.worker.run()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    logthread('main')

    window = MainWindow()
    sys.exit(app.exec_())
