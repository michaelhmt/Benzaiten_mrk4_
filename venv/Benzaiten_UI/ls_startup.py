from collect_data import Ui_MainWindow as data_ui
from PyQt5 import QtCore, QtGui, QtWidgets

class configured_collect_data(data_ui):
    def __init__(self, mainwindow):
        self.setupUi(mainwindow)
        super(configured_collect_data, self).__init__()

    def test(self):
        print("rewteegd")


def launch_ui():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = configured_collect_data(MainWindow)
    #ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    status = launch_ui()