import sys
import os

EXAMPLE_URL = "https://archiveofourown.org//tags//-------//works?page={}"

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
from PyQt5 import uic
from Benzaiten_Common.Scrpaer import iterate
from PyQt5 import QtGui,QtCore
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap


class configured_collect_data(data_ui):
    def __init__(self, mainwindow):
        super(configured_collect_data, self).__init__()
        self.setupUi(mainwindow)
        self.connect_signials()
        self.initui()

    def connect_signials(self):
        self.start_collection.clicked.connect(self.start_collection_function)

    def initui(self):
        self.process = QtCore.QProcess(self)
        self.process.readyRead.connect(self.write_to_console)
        self.process.started.connect(lambda: self.start_collection.setEnabled(False))
        self.process.finished.connect(lambda: self.start_collection.setEnabled(True))

    def write_to_console(self):
        self.console_output.insertPlainText(self.process.readAll().data().decode())

    def start_collection_function(self):
        self.process.start('python',['-u', 'Test.py',])

    #def get_ui_state(self):



def launch_ui():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = configured_collect_data(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    status = launch_ui()