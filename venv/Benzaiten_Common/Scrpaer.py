# coding=utf8

# buildt in
import os
import sys
import json

# env settings
def set_env():
    env_dir = os.path.dirname(os.getcwd())
    sys.path.append(env_dir)
set_env()
import Site_custom
env_object = Site_custom.env()

print(sys.path)

#project imports
from FFWebscraper import root_page
from DataBase import Database_Class
from webscraper_modules.archive_of_our_own import ArchiveOOO
from webscraper_modules.fanfiction_net_scraper import FanfictionNetScraper

SEARCHPAGE_CONSTANT = 'https://archiveofourown.org/tags/Harry%20Potter%20-%20J*d*%20K*d*%20Rowling/works?page={}'
TEST_DUMP_FILE = os.path.join(os.getcwd(), "sample_log.json")

conf_path = env_object.config_path

with open(conf_path, "r") as config_file:
    config = json.load(config_file)



def ingest(search_page_to_ingest,
           scraper_object,
           add_to_db=True,
           searchPage_constant=SEARCHPAGE_CONSTANT,
           debug_mode=False):

    if debug_mode:
        print("******: starting iteration")
    starturl = searchPage_constant.format(search_page_to_ingest)

    if debug_mode:
        print("******: Ingest  and database classes created")

    story_batch = scraper_object.ingest_searchpage(search_page_to_ingest)
    if debug_mode:
        print("******: Writing story batch to a dump file")
        write_test_sample(story_batch)


def iterate(page_to_start_with,
            web_scraper,
            limt=None, add_to_db=True,
            using_UI=False,
            searchPage_constant=SEARCHPAGE_CONSTANT,
            debug_mode=False,
            col=None):

    print("starting up.....")
    print("checking {}".format(searchPage_constant.format(1)))
    web_scraper_class = globals()[config['web_scrapers'].get(web_scraper)]
    if not web_scraper_class:
        print("No valid scraper set or it is misconfigured")
        return

    database = Database_Class('FF_Data_Cluster')
    web_scraper_object = web_scraper_class(searchPage_constant.format(1),
                                           delay=25,
                                           search_page_constant=searchPage_constant,
                                           debug_mode=debug_mode,
                                           data_base_class=database,
                                           add_single_to_db=add_to_db,
                                           target_col=col) #used to check how many pages we have as we always know we will have page 1

    page_max = web_scraper_object.get_browse_page_lenght()

    if limt == None or 0:
        if debug_mode:
            print("******: Using the max page num: {}".format(page_max))
        end_page = page_max
    else:
        end_page = limt

    if limt < page_to_start_with:
        print("Cant ingest with a limt smaller than the start page, set a limt that is the page number to stop on.")

    print("--- Ingesting up to page {}".format(limt))

    current_page = page_to_start_with

    for page in range(limt):
        print("ingesting page {} of {}".format(current_page, limt))
        ingest(current_page, web_scraper_object,
               add_to_db= add_to_db,
               searchPage_constant=searchPage_constant,
               debug_mode=debug_mode)

        print("----------------------------------------------------")
        print("finished ingesting page {}".format(current_page))
        print("----------------------------------------------------")
        current_page += 1
    print("*"*50, "\nAll target data was collected!\n", "*"*50) # should maybe report any errors we caught here



def write_test_sample(story_batch):
    if not os.path.exists(TEST_DUMP_FILE):
        with open(TEST_DUMP_FILE, 'a+') as i_log:
            json.dump(story_batch, i_log, indent=4)



#iterate(20,limt=40, add_to_db=True)

