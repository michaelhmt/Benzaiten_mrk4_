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

        self.ingested_log = None

    def open_ingested_log(self):
        # make the log if it does'nt exist
        if not os.path.exists(INGESTED_LOG):
            if self.debug_mode:
                print("******: making log")
            with open(INGESTED_LOG, 'a+') as i_log:
                blank_log ={"Author":[],
                            "Link": [],
                            "Title": []}
                json.dump(blank_log, i_log, indent=4)

        # get the log data
        with open(INGESTED_LOG) as log_file:
            data = json.load(log_file)

        return data


    def check_ingested_log(self, metadata):
        if self.debug_mode:
            print("******: checking ingested log")

        try:
            if metadata['Title'] in self.ingested_log['Title'] and metadata['Link'] in self.ingested_log['Link']:
                #if thease vals exist in our log already we must have ingested this tory already
                return False
            else:
                if metadata['Link'] == None:
                    #This is bad metadata
                    print("Bad metadata retrived, not adding to log")
                    return False

                metadata_to_submit = []

                metadata_to_submit.append(metadata['Author'])
                metadata_to_submit.append(metadata['Link'])
                metadata_to_submit.append(metadata['Title'])

                self.add_to_ingested_log(metadata_to_submit)
                return True


        except IndexError as e:
            print('could open the meta data dict or maybe the log dict got {}'.format(e))

    def add_to_ingested_log(self, metadata_to_add):
        """
        give this function a list with with [Author, link, Title]
        :param metadata_to_add:
        :return:
        """
        if self.debug_mode:
            print("******: addign story to ingested log")


        with open(INGESTED_LOG, 'r+' ) as i_log:
            current_data = json.load(i_log)
            current_data['Author'].append(metadata_to_add[0])
            current_data['Link'].append(metadata_to_add[1])
            current_data['Title'].append(metadata_to_add[2])
            i_log.seek(0)
            json.dump(current_data, i_log, indent=4)


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