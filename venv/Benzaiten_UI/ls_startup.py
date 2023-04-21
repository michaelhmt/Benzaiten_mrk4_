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

import Benzaiten_Common.utils as b_utils
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
from data_tools.collection_class import Collection_data
from DataBase import Database_Class
from Benzaiten_UI.ui_widgets.author_info import AuthorInfo
from Benzaiten_UI.ui_widgets.story_info import StoryInfo
from Benzaiten_UI.ui_widgets.tag_info import TagInfo



# this needs to match whats at the top of Scraper.py
# really should be in a Json they both share
config_path = env_object.config_path

with open(config_path, "r") as config_file:
    config = json.load(config_file)


class CollectionTreeChildItem(QTreeWidgetItem):
    item_type = "No Type"



class CollectionTreeItem(QTreeWidgetItem):
    item_type = "Story"

    def __init__(self, data_item):
        super(CollectionTreeItem, self).__init__()
        self.data = data_item

    def populate_children(self):
        author_item = self.make_tree_item(self.data['MetaData'].get('Author', "No Author"), 'author.png', "author")
        icon_folder = self.make_tree_item('Tags', 'tag_folder.png', "tag_folder")

        # make tag Items
        for tag in self.data['MetaData']['Tags']:
            tag_item = self.make_tree_item(tag, "tag_icon.png", "tag")
            icon_folder.addChild(tag_item)

        self.addChild(author_item)
        self.addChild(icon_folder)

    def make_tree_item(self, name,  icon, type):
        _tree_item = CollectionTreeChildItem()
        _tree_item.item_type = type
        _tree_item.setText(0, name)
        item_icon = QtGui.QIcon(os.path.join(env_object.icons_folder, icon))
        _tree_item.setIcon(0, item_icon)

        return _tree_item


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        print(layout.itemAt(i))
        layout.removeItem(layout.itemAt(i))


class configured_collect_data(data_ui):
    def __init__(self, mainwindow):
        super(configured_collect_data, self).__init__()
        self.setupUi(mainwindow)
        self.connect_signials()
        self.initui()

        self.temp_file =  os.path.join(os.getcwd(), 'temp.json')
        self.console_output_scroll_bar = self.console_output.verticalScrollBar()
        self.console_output.installEventFilter(self)
        self.u_response = None
        self.stop_launch = False

    def connect_signials(self):
        self.start_collection.clicked.connect(self.start_collection_function)
        self.clear_output.clicked.connect(lambda: self.console_output.clear())
        self.btn_load_collection.clicked.connect(self.retrive_collection)

        self.collection_display.currentItemChanged.connect(self.populated_selected_item_info)
        self.btn_deliver_data.clicked.connect(self.deliver_collection)
        self.btn_start_analysis.clicked.connect(self.analyse_current_collection)

    def make_sub_widget(self, widget_class):
        base_widget = QtWidgets.QWidget(parent=self)
        sub_widget = widget_class()
        sub_widget.setupUi(base_widget)
        base_widget.show()
        sub_widget.show()
        return sub_widget

    def populated_selected_item_info(self):
        selected_item = self.collection_display.currentItem()
        if not selected_item:
            print("Nothing selected")
            return
        clear_layout(self.Info_layout)

        print("This is selected_item.item_type: ", selected_item.item_type)

        if selected_item.item_type is "Story":
            print("Adding a story_info widget")
            story_info_widget = self.make_sub_widget(StoryInfo)
            story_info_widget.label_2.setText(str(b_utils.word_count_of_story(selected_item.data)))
            self.Info_layout.addWidget(story_info_widget)


    def initui(self):
        # if you get an error here make sure data_ui inherits from QtWidgets.QMainWindow
        self.process = QtCore.QProcess(self)

        self.process.readyRead.connect(self.write_to_console)
        self.process.started.connect(lambda: self.start_collection.setEnabled(False))
        self.process.finished.connect(lambda: self.start_collection.setEnabled(True))

        self.populate_ui()

        for website in config['web_scrapers'].keys():
            self.Ingest_mode.addItem(website)

    def populate_ui(self):
        self.populate_collections()

    def populate_collections(self):
        self.database = Database_Class('FF_Data_Cluster')
        if not self.database.collections:
            self.collections = config['database_collections']
        else:
            self.collections = self.database.collections

        self.cmbx_collections.addItems(self.collections)

    # Web collection tab
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

        if self.stop_launch:
            return

        log_path = str(self.temp_file)
        log_path = log_path.replace("\\", "/")
        self.write_to_log(script_launch_args)

        print("sending the following: ", "import Launch_helper; Launch_helper.launch_scraper_via_ui('{}')".format(log_path))
        self.process.start('python',['-u',
                                     '-c',
                                     "import Launch_helper; Launch_helper.launch_scraper_via_ui('{}');".format(log_path)])

    def get_ui_state(self):
        self.stop_launch = False
        target_url = self.query_search_page()
        if not target_url:
            print("Given Url is Invalid, ending")
            self.console_output.insertPlainText("Given Url is Invalid, ending\n")
            self.stop_launch = True



        page_limt = self.number_to_collect.value()
        add_to_db = self.add_to_data_base.checkState()
        page_to_start_at = self.spinBox.value()
        debug_mode = self.chkbx_debug_mode.checkState()
        website_mode = self.Ingest_mode.currentText()

        if add_to_db:
            user_col = self.target_db_col.text()
            if user_col != "":
                target_col_valid = self.check_collection(user_col)
                if target_col_valid:
                    target_collection = str(user_col)
                    self.add_to_col_list(user_col)
                else:
                    print("stopping collection")
                    self.stop_launch = True
                    return False
            else:
                print("No collection given")
                self.stop_launch = True
                return False


        print("This is target col: ", target_collection)

        state_dict ={"target_url": target_url,
                     "page_limt": page_limt,
                     "add_to_db": add_to_db,
                     "page_to_start": page_to_start_at,
                     "debug": debug_mode,
                     "website_mode": website_mode,
                     "target_col": target_collection}

        print("Thhis is state_dict: ", state_dict)
        return state_dict

    def add_to_col_list(self, col_name):
        collections_lst = config['database_collections']
        if col_name not in collections_lst:
            collections_lst.append(col_name)
            with open(config_path, "w") as coonfig_file:
                config['database_collections'] = collections_lst
                json.dump(config, coonfig_file, indent=4)

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
        elif col_to_check in collections_lst:
            return True

    def response(self, i):
        self.u_response = i.text()

    # Data tools Tab

    def deliver_collection(self):

        collection_name = self.cmbx_collections.currentText()
        print("starting Download of: {}".format(collection_name))
        self.collection = Collection_data(collection_name)
        print("downloaded {}".format(collection_name))



    def retrive_collection(self):
        self.collection_display.clear()
        collection_name = self.cmbx_collections.currentText()
        self.collection = Collection_data(collection_name)
        self.disk_data = self.collection.get_collection_data()

        #progress window
        progress_win = QtWidgets.QProgressDialog("generating",'', 0, 10000, self)
        progress_win.setLabelText("computing Data.")
        progress_win.setWindowModality(Qt.WindowModal)
        progress_win.setCancelButton( None)
        progress_win.setMaximum(10000)
        progress_win.setMinimum(0)
        progress_win.setValue(0)

        word_count = 0

        if not self.disk_data:
            m_box = QtWidgets.QMessageBox()
            msg = "{} has not been downloaded to this machine, press \"deliver Data Collection\" to retrieve it.".format(collection_name)
            m_box.setText(msg)
            m_box.setWindowTitle("Collection not on disk")
            m_box.exec()
            return

        entry_number = len(self.disk_data)
        step_size = (10000 / entry_number) + 0.9
        progress = 0
        self.lcdnum_entries.display(entry_number)
        progress_win.show()

        for entry in self.disk_data:

            word_count +=  self.word_count_of_entry(entry)
            story_item = CollectionTreeItem(entry)
            story_item.setText(0, entry['MetaData'].get('Title', "No Title"))
            story_icon = QtGui.QIcon(os.path.join(env_object.icons_folder, 'story_icon.png'))
            story_item.setIcon(0, story_icon)
            self.collection_display.insertTopLevelItem(0, story_item)
            story_item.populate_children()

            progress = progress + step_size
            progress_win.setValue(int(progress))

        print("This is word count: ", word_count)
        self.lcdnum_word_count.display(int(word_count))
        progress_win.close()

    def analyse_current_collection(self):
        if self.collection:
            self.collection.deliver_data()
            self.collection.deliver_top_author_anyalsis()

    def word_count_of_entry(self, entry):
        count = 0
        for _, chapter in entry['Content'].items():
            count += len(chapter)
        return count









def launch_ui():
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = configured_collect_data(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    status = launch_ui()