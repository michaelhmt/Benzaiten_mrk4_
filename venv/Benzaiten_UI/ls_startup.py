# -*- coding: utf-8 -*-
# coding=utf8

import sys
import os
import json
import time

EXAMPLE_URL = "https://archiveofourown.org//tags//-------//works?page={}"

def set_env():
    env_dir = os.path.dirname(os.getcwd())
    sys.path.append(env_dir)
    print("this is env dir: ", env_dir)
set_env()
import Site_custom
env_object = Site_custom.env()

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

from webscraper_modules.archive_of_our_own import ArchiveOOO
from webscraper_modules.fanfiction_net_scraper import FanfictionNetScraper

# this needs to match whats at the top of Scraper.py
# really should be in a Json they both share
conf_path = env_object.config_path

with open(conf_path, "r") as config_file:
    config = json.load(config_file)

class configured_collect_data(data_ui):
    def __init__(self, mainwindow):
        super(configured_collect_data, self).__init__()
        self.setupUi(mainwindow)
        self.connect_signials()
        self.initui()

        self.temp_file = temp_log_write_location = os.path.join(os.getcwd(), 'temp.json')
        self.console_output_scroll_bar = self.console_output.verticalScrollBar()
        self.console_output.installEventFilter(self)
        self.u_response = None

    def connect_signials(self):
        self.start_collection.clicked.connect(self.start_collection_function)
        self.clear_output.clicked.connect(lambda: self.console_output.clear())

    def initui(self):
        # if you get an error here make sure data_ui inherits from QtWidgets.QMainWindow
        self.process = QtCore.QProcess(self)

        self.process.readyRead.connect(self.write_to_console)
        self.process.started.connect(lambda: self.start_collection.setEnabled(False))
        self.process.finished.connect(lambda: self.start_collection.setEnabled(True))

        for website in config['web_scrapers'].keys():
            self.Ingest_mode.addItem(website)

    def write_to_console(self):
        self.console_output.insertPlainText(self.process.readAll().data().decode("cp850"))
        try:
            time.sleep(0.1)
            current_postion = self.console_output_scroll_bar.value()
            self.console_output_scroll_bar.setValue(current_postion + 100000)
        except:
            # encase we have'nt got a scroll bar yet
            pass

    def start_collection_function(self):
        script_launch_args = str(self.get_ui_state())

        if not self.get_ui_state():
            return

        log_path = str(self.temp_file)
        log_path = log_path.replace("\\", "/")
        self.write_to_log(script_launch_args)

        print("sending the following: ", "import Launch_helper; Launch_helper.launch_scraper_via_ui('{}')".format(log_path))
        self.process.start('python',['-u',
                                     '-c',
                                     "import Launch_helper; Launch_helper.launch_scraper_via_ui('{}');".format(log_path)])

    def get_ui_state(self):
        target_url = self.query_search_page()
        if not target_url:
            print("Given Url is Invalid, ending")
            self.console_output.insertPlainText("Given Url is Invalid, ending\n")
            return



        page_limt = self.number_to_collect.value()
        add_to_db = self.add_to_data_base.checkState()
        page_to_start_at = self.spinBox.value()
        debug_mode = self.chkbx_debug_mode.checkState()
        website_mode = self.Ingest_mode.currentText()

        if add_to_db:
            if self.target_db_col.text() != "":
                target_col_valid = self.check_collection(self.target_db_col.text())
                if target_col_valid:
                    target_collection = str(self.target_db_col.text())
                else:
                    print("stopping collection")
                    return False
            else:
                print("No collection given")
                return False


        state_dict ={"target_url": target_url,
                     "page_limt": page_limt,
                     "add_to_db": add_to_db,
                     "page_to_start": page_to_start_at,
                     "debug": debug_mode,
                     "website_mode": website_mode,
                     "target_col": target_collection}

        print("Thhis is state_dict: ", state_dict)
        return state_dict

    def write_to_log(self, var_to_write):
        if not os.path.exists(self.temp_file):
            with open(self.temp_file, 'a+'):
                pass

        with open(self.temp_file, "w+") as temp_file:
            json.dump(var_to_write, temp_file, indent=6)

    def query_search_page(self):
        current_text = self.target_url.text()
        if self.ignore_name_check:
            # For if we have a custom group of tags that we want to collect
            # ideally make sure this ends in &page= so we can add the .fomrat
            # make sure &page= is ideally not anywhere else in the url

            if "&page=" not in current_text:
                print("Not page url found, I hope you know what your doing!")
            return current_text + "{}"

        else:
            start_constant = 'https://archiveofourown.org/tags/'
            end_constant = '/works'

            print("Start is good: ", current_text.startswith(start_constant),
                  "end is good: ",current_text.endswith(end_constant))
            if current_text.startswith(start_constant) and current_text.endswith(end_constant):
                print("Url passed check")
                return current_text + "?page={}"

    def check_collection(self, col_to_check):
        collections_lst = config['database_collections']
        if col_to_check not in collections_lst:
            dialouge_window = QtWidgets.QMessageBox()

            dialouge_window.setIcon(QMessageBox.Information)
            dialouge_window.setText("The target collection does not yet exists in the DataBase.\n"
                                    "Do you want to add it?")
            dialouge_window.setInformativeText("This is the collection you are trying to add {} \n"
                                               "Thease are the collections that already exist: \n {}".format(col_to_check,
                                                                                                             "\n".join(collections_lst)))
            dialouge_window.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            dialouge_window.buttonClicked.connect(self.response)

            retval = dialouge_window.exec_()

            if self.u_response == 'OK':
                print("proceeding")
                return True
            elif self.u_response == 'Cancel':
                return False


    def response(self, i):
        self.u_response = i.text()






def launch_ui():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = configured_collect_data(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    status = launch_ui()