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
import zlib
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup

# Benzaiten packages
from webscraper_modules.scraper_baseclass import BaseScraperClass


HEADER_ = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.116 Safari/537.36'}
STORY_PAGE_CONSTANT = 'https://archiveofourown.org{url}?view_adult=true">Proceed'
STORY_INDEX_CONSTANT = "https://archiveofourown.org{url}/navigate"
SEARCHPAGE_CONSTANT = 'https://archiveofourown.org/tags/Harry%20Potter%20-%20J*d*%20K*d*%20Rowling/works?page={}'
VIEW_ALL_CONSTANT ="https://archiveofourown.org{url}?view_adult=true&view_full_work=true" #MIGHT THROW AN ERROR WITH MATURE CONTENT

COOKIES_CONSTANT = {'domain': 'archiveofourown.org', 'httpOnly': False, 'name': 'view_adult', 'path': '/', 'secure': False, 'value': 'true'}

DRIVER_PATH = env_object.chrome_driver_path
INGESTED_LOG = env_object.ingested_log_path


class ArchiveOOO(BaseScraperClass):

    def __init__(self, url, goto=None, delay=9,
                 search_page_constant=SEARCHPAGE_CONSTANT,
                 debug_mode=False, data_base_class=None,
                 add_single_to_db=False, target_col=None):
        """
        will be given root starting page of a archive our our own index page, will go to the next page from there
        :param url: str: the root index page
        """
        print("Starting Ingest Class..")
        self.debug_mode = debug_mode
        self.ingested_log = self.open_ingested_log()
        self.data_base = data_base_class
        self.add_singles = add_single_to_db
        self.target_col = target_col

        self.search_page_constant = search_page_constant
        self.restarted_attempted = False
        self.delay = delay
        self.root_url = url
        self.root = self.get_page(self.root_url)
        self.root_soup = BeautifulSoup(self.root.content, 'html.parser')
        self.limt = goto
        self.start_browser()

    def start_browser(self):
        if self.debug_mode:
            print("******: starting headles chrom browser")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        #chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--window-size=1024x1400")
        s=Service(DRIVER_PATH)
        if self.debug_mode:
            print("******: created browser options")

        if self.debug_mode:
            print("******: starting driver")
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        time.sleep(self.delay)
        page = self.driver.get('https://archiveofourown.org/works/29832528?view_full_work=true') #know link for triggering adult contant

        wait = WebDriverWait(self.driver, 10)
        if self.debug_mode:
            print("******: auto completeing page")
        time.sleep(5) #box takes a second or 2 to appear

        I_agree = wait.until(EC.presence_of_element_located((By.ID, 'tos_agree')))
        I_agree.click()

        I_agree_button = wait.until(EC.presence_of_element_located((By.ID, 'accept_tos')))
        I_agree_button.click()

        proceed = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Proceed")))
        proceed.click()
        # now we can query any page without derailing the entire script

    def ingest(self, search_page_to_ingest):
        """
        assume root is popoulated and also grab the current page  and decides how far we go
        This one might be moved to the scraper class so we can add to the DB

        THIS IS REDUNDANT

        :return:
        """
        urlsplit = self.root_url.split('=')
        try:
            current_page = int(urlsplit[-1])
        except TypeError:
            print("Unexpected Url format")
            return None

        pageMax = self.get_browse_page_lenght(self.root_soup)

        if self.limt == None:
            limt = pageMax
        else:
            limt = self.limt


        if limt < current_page:
            print("Cant ingest with a limt smaller than the start page, set a limt that is the page number to stop on.")

        print("--- Ingesting up to page {}".format(limt))

        for page in range(limt):
            print("ingesting page {} of {}".format(current_page,limt))
            self.ingest_searchpage(current_page)
            print("finished ingesting page {}".format(current_page))
            current_page =+ 1

    def ingest_searchpage(self, pagenum):
        """
        This is where we wil iterate across the seach pages
        :param pagenum: the current page number we are on
        :return:
        """
        story_Batch = []
        if self.debug_mode:
            print("******: LOOKING AT SEARCH PAGE")

        searchpage_url = self.search_page_constant.format(pagenum)
        searcpage = self.get_page(searchpage_url)

        searcpage_soup = BeautifulSoup(searcpage.content, 'html.parser')
        if self.debug_mode:
            print("******: making search page soup")
        story_list = searcpage_soup.find_all(role='article')

        def estimate(chapters):
            """
            Not used any more used to estimate how long it would take to ingest a story based on the number of chapters
            :param chapters:
            :return:
            """
            try:
                chapters_num = int(chapters)
            except ValueError:
                return "Dont know"

            estimate = (self.delay * chapters_num)
            if estimate >= 60:
                return "{} Minute(s)".format(estimate/60)
            else:
                return "{} Seconds".format(estimate)



        for count, story in enumerate(story_list):
            if self.debug_mode:
                print("******: in search page iteration loop")
            story_object = {}
            story_metadata = self.get_Story_meta_data(story)
            story_object['MetaData'] = story_metadata

            if story_metadata == '<_STORY NOT IN ENGLISH_>':
                print("\n-------------------------------------------")
                print("story is not in English, moving onto next one")
                print("\n-------------------------------------------")
                continue

            metadata_log = self.check_ingested_log(story_metadata)

            if metadata_log == False:
                print("\n-------------------------------------------")
                print("Story has already been Ingested, skipping")
                print("\n-------------------------------------------")
                continue

            Time_to_complete = estimate(story_metadata['Chapters'])
            print(Time_to_complete)
            print("Starting ingest of {title}, it has {ch} chapters".format(title=story_metadata['Title'].encode('utf-8'),
                                                                            ch=story_metadata['Chapters'],))
            print("Ingesting story {} of {} in current batch".format(count, len(story_list)))
            is_single_chapter = int(story_metadata['Chapters']) == 1
            story_content = self.ingest_story(story_metadata['Link'], story_metadata['Title'],ingest_single=is_single_chapter)
            print("----------Finished Ingest----------------")
            story_object['Content'] = story_content

            if self.add_singles and self.data_base:
                self.data_base.add_to_database(itemToAdd=story_object,
                                               targetCollection=self.target_col,
                                               print_IDs=True)
            else:
                story_Batch.append(story_object)

        for story in story_Batch:
            print("\n--------------\n")

        return story_Batch

    def get_page(self, url):
        """
        gets the static html of a webpage then wait for 10 seconds
        :param url:
        :return:
        """
        if self.debug_mode:
            print("******: getting url: {}".format(url))

        page = requests.get(url, headers=HEADER_)
        time.sleep(self.delay)
        return page

    def get_dynamic_page(self, url):
        """
        gets dynamic web page source insluding javascript elements then waits 10 seconds
        :param url:
        :return:
        """

        if self.debug_mode:
            print("******: getting a dynamic page")
        time.sleep(self.delay)
        try:
            page = self.driver.get(url)
        except selenium.common.exceptions.TimeoutException as timeout_error:
            print("Got time out error, Restarting browser.")
            if not self.restarted_attempted:
                self.start_browser()
                self.restarted_attempted = True
                return self.get_dynamic_page(url)

            
        if self.restarted_attempted:
            self.restarted_attempted = False
        #print(driver.page_source)
        return self.driver.page_source

    def get_browse_page_lenght(self):
        """
        Gets the amount of pages within the given search
        :return:
        """
        if self.debug_mode:
            print("******: getting the lenght of the browse page")

        navigation_bar = self.root_soup.find_all(title='pagination')[0]
        buttons = navigation_bar.find_all('a')
        page_nums =[]
        for button in buttons:
            #print(button.attrs)
            url = button['href']
            urls_split = url.split("=")
            try:
                pagenum = int(urls_split[-1])
                page_nums.append(pagenum)
            except:
                print("could not get page num from {} URL, trying text instead".format(url))
                button_text = str(button.get_text())
                if button_text.isnumeric():
                    page_nums.append(int(button_text))
                else:
                    print("Could not get page num from button")

        return max(page_nums)

    def get_Story_meta_data(self, article_card):
        """
        Makes a metadata object that will cotian useful info about the story like its title chapter numbers and a link to the story
        :param article_card:
        :return:
        """
        if self.debug_mode:
            print("******: finding the story metadata")

        story_metaData_Object = {}
        story_metaData_Object["SOURCE"] = "ArchiveOfOurOwn"

        title = article_card.find_all(class_='heading')
        for entry in title:
            if 'Fandoms:' not in entry.get_text():
                try:
                    lines = entry.find_all('a')
                    story_metaData_Object["Link"] = (lines[0])['href']
                except IndexError:
                    #no link here
                    continue

                try:
                    split_title = entry.get_text().split("\n")
                    story_metaData_Object["Title"] = split_title[1]
                    story_metaData_Object["Author"] = split_title[5]
                except IndexError:
                    #Not the title header
                    continue

        if self.debug_mode:
            print("******: getting the static metadata tags")

        Tags = article_card.find_all(class_='tag')
        story_metaData_Object["Tags"] = [tag.get_text() for tag in Tags]

        Summary = article_card.find_all(class_='userstuff summary')
        story_metaData_Object["Story Summary"] = [paragraph.get_text() + "\n \n" for paragraph in Summary]

        #stats
        story_Language = article_card.find_all('dd', class_='language')[0].get_text()
        chapters = article_card.find_all('dd', class_='chapters')[0].get_text()

        if story_Language != 'English':
            return "<_STORY NOT IN ENGLISH_>"

        current_chapters = chapters.split("/")[0]
        if self.debug_mode:
            print("******: buiulding finial metadata")

        story_metaData_Object["Language"] = story_Language
        story_metaData_Object["Chapters"] = current_chapters


        return story_metaData_Object

    def Story_index(self, link):
        """
        Gets the index page for the given story
        :param link:
        :return: a lst of link to chapters for that story
        """
        if self.debug_mode:
            print("******: getting index of a story")

        chapter_link_lst = []

        index_page = self.get_page(STORY_INDEX_CONSTANT.format(url=link))
        index_soup = BeautifulSoup(index_page.content, 'html.parser')

        chapter_index = index_soup.find(class_= 'chapter index group')

        for chapter in chapter_index:
            try:
                chapter_link_lst.append(chapter.find('a')['href'])
            except TypeError:
                pass
        return chapter_link_lst

    def ingest_chapter(self, link):
        """
        expects to be given a link to a chpater will return a lst of string for the phapgraphs of that story
        :param link:
        :return:
        """
        if self.debug_mode:
            print("******: ingesting a single chapter")

        chapterlink = STORY_PAGE_CONSTANT.format(url=link)
        chapter_page = self.get_dynamic_page(chapterlink)

        chapter_soup = BeautifulSoup(chapter_page, 'html.parser')

        chapter_text = chapter_soup.find('div', class_='userstuff').next_element.get_text()

        return {"1": chapter_text}

    def ingest_full_story(self, link):
        if self.debug_mode:
            print("******: ingesting a story")
        chapters = {}

        full_story_link = VIEW_ALL_CONSTANT.format(url=link)
        print(full_story_link)
        full_story_page = self.get_dynamic_page(full_story_link)

        story_soup = BeautifulSoup(full_story_page, 'html.parser')
        #print(story_soup)
        chapters_lst = story_soup.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['chapter'])
        # ^ will explicitly match a div that has the class name chapter not just chapter in its name

        count = 1
        print("Chapter lst len: ", len(chapters_lst))
        for chapter in chapters_lst:
            if self.debug_mode:
                print("******: getting all the chapters")

            chapter_contents = []

            chapter_num = count
            heading = "Chapter {}".format(chapter_num)
            chapter_contents.append(heading)
            text = chapter.get_text()

            if len(text) > 90:
                if self.debug_mode:
                    print("******: printning a chapter sample from a full story")
                print("sample")
                text_sample = text.encode(encoding='utf-8')
                print(text_sample[0:120])


            print("Size of text uncompressed........: {}".format(sys.getsizeof(text)))

            # compressed = zlib.compress(text.encode()) #basic string compression
            # print("Size of text compressed: {}".format(sys.getsizeof(compressed)))

            chapter_contents.append(text)
            chapters[str(chapter_num)] = text
            count += 1


        return chapters

    def ingest_story(self, link, name, ingest_single=False):
        """
        give a link from metadata object, will get a lst of chpater link and get the strings of the chapters
        returns a dict with int as keys for the chpater number. starting at 1
        :param link:
        :return:
        """

        print("----------------------------------------------")
        print("Starting ingest of {} and its chapters".format(name.encode(encoding='utf-8')))
        if ingest_single:
            chapters =self.ingest_chapter(link)
        else:
            chapters = self.ingest_full_story(link)
        print("Finished ingest of {} and its chapters".format(name.encode(encoding='utf-8')))

        return chapters

# from Benzaiten_Common.DataBase import Database_Class
#
# databaseclass = Database_Class("FF_Data_Cluster")
# scarper_class = ArchiveOOO("https://archiveofourown.org/tags/Fate*s*Grand Order/works?page=1",
#                            search_page_constant="https://archiveofourown.org/tags/Fate*s*Grand Order/works?page={}",
#                            goto=2,
#                            data_base_class=databaseclass,add_single_to_db=True,target_col='test_data')
#
# scarper_class.ingest_searchpage("https://archiveofourown.org/tags/Fate*s*Grand Order/works?page=1")
