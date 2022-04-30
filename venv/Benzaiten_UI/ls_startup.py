import sys
import os

def set_env():
    current_location = os.getcwd()
    package_folder = os.path.dirname(current_location)
    common_folder = os.path.join(package_folder, "Benzaiten_Common")
    sys.path.append("E:\\Python\\Benzaiten_mrk4\\venv\\Lib\\site-packages")
    sys.path.append(package_folder)
    sys.path.append(common_folder)

set_env()

from collect_data import Ui_MainWindow as data_ui
from PyQt5 import QtCore, QtGui, QtWidgets
from Benzaiten_Common.Scrpaer import iterate


class configured_collect_data(data_ui):
    def __init__(self, mainwindow):
        self.setupUi(mainwindow)
        self.connect_signials()

    def connect_signials(self):
        self.start_collection.clicked.connect(self.start_collection_function)

    def start_collection_function(self):
        print("Hello")



def launch_ui():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = configured_collect_data(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    status = launch_ui()