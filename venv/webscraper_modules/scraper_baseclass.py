# -*- coding: utf-8 -*-
# coding=utf8

#buildt in
import os
import sys
import json
import time

# env settings
def set_env():
    env_dir = os.path.dirname(os.getcwd())
    sys.path.append(env_dir)
    print("this is env dir: ", env_dir)
set_env()
import Site_custom
env_object = Site_custom.env()

#site packages

INGESTED_LOG = env_object.ingested_log_path

#.encode('utf-8')


class BaseScraperClass(object):

    def __init__(self, url, goto=None, delay=9,
                 search_page_constant="Not given",
                 debug_mode=False, data_base_class=None,
                 add_single_to_db=False):
        """
        will be given root starting page of a archive our our own index page, will go to the next page from there
        :param url: str: the root index page
        """
        print("Starting Ingest Class..")
        self.debug_mode = debug_mode
        self.data_base = data_base_class
        self.add_singles = add_single_to_db

        self.search_page_constant = search_page_constant
        self.delay = delay
        self.root_url = url
        self.limt = goto




    def get_browse_page_lenght(self):
        """
        Used to detrmin how many potential pages we will need to to iterate over,
         us to set the lenght of the for loop
        :return:
        """
        raise NotImplementedError("Get browser page lenght has not been implemented")

    def ingest_searchpage(self, search_page_to_ingest):
        """
        Called by the main scraper script this function should manage reterving a scraped story
        and adding that story to the database

        :param search_page_to_ingest: The url of the search page or general
        the page where we have a collection of links to the storyies
        :return:
        """
        raise NotImplementedError("Ingest search page has not been implemented")