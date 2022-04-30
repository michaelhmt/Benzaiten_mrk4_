# coding=utf8
#project imports
from FFWebscraper import root_page
from DataBase import Database_Class

SEARCHPAGE_CONSTANT = 'https://archiveofourown.org/tags/Harry%20Potter%20-%20J*d*%20K*d*%20Rowling/works?page={}'


def ingest(search_page_to_ingest, add_to_db=True):
    starturl = SEARCHPAGE_CONSTANT.format(search_page_to_ingest)

    ingestor = root_page(starturl, delay=17)
    database = Database_Class('HP_ff_data')

    story_batch = ingestor.ingest_searchpage(search_page_to_ingest)
    if add_to_db:
        print("-----story Batch: ", story_batch)
        if len(story_batch) <= 0:
            print("*** story batch is empty, skipping to next page ***")
            return

        database.add_to_database(story_batch, 'collectedData') #cannot add an empty batch to the DB, which we might do with the logging feature, fix this bug

def iterate(page_to_start_with, limt=None, add_to_db = True):
    print("starting up.....")
    print("checking {}".format(SEARCHPAGE_CONSTANT.format(1)))
    ingestor_check = root_page(SEARCHPAGE_CONSTANT.format(1)) #used to check how many pages we have as we always know we will have page 1

    page_max = ingestor_check.get_browse_page_lenght()

    if limt == None:
        end_page = page_max
    else:
        end_page = limt

    if limt < page_to_start_with:
        print("Cant ingest with a limt smaller than the start page, set a limt that is the page number to stop on.")

    print("--- Ingesting up to page {}".format(limt))

    current_page = page_to_start_with

    for page in range(limt):
        print("ingesting page {} of {}".format(current_page, limt))
        ingest(current_page,add_to_db= add_to_db)
        print("----------------------------------------------------")
        print("finished ingesting page {}".format(current_page))
        print("----------------------------------------------------")
        current_page += 1


#iterate(20,limt=40, add_to_db=True)

