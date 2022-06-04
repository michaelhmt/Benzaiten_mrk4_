#buildt in
import os
import sys
import json
import time
import copy
import re
import datetime
from pprint import pprint

# env settings
import selenium.common.exceptions


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
from selenium_stealth import stealth
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

# Benzaiten packages
from webscraper_modules.scraper_baseclass import BaseScraperClass

INGESTED_LOG = env_object.ingested_log_path
DRIVER_PATH = env_object.chrome_driver_path

SEARCHPAGE_CONSTANT = "https://www.fanfiction.net/anime/Digimon/?&srt=1&r=103&p={}"
METADATA_SKIP = ['Rated:', "Reviews:", "Favs:", "Follows:", "Updated:", "Published:"]
METADATA_TAGS = ['Rated:',"Chapters:", "Words:" , "Reviews:", "Favs:", "Follows:", "Updated:", "Published:"]
URL_CONSTANT = "https://www.fanfiction.net"

class FanfictionNetScraper(BaseScraperClass):

    def __init__(self,
                 url,
                 goto=None,
                 delay=9,
                 search_page_constant=SEARCHPAGE_CONSTANT,
                 debug_mode=False, data_base_class=None,
                 add_single_to_db=False,
                 target_col=None):

        super().__init__(url)

        self.root_url = url
        self.limt = goto
        self.delay = delay
        self.search_page_constant = search_page_constant
        self.debug_mode = debug_mode
        self.data_base = data_base_class
        self.add_singles = add_single_to_db
        self.target_col = target_col
        self.restarted_attempted = False

        self.ingested_log = self.open_ingested_log()


        self.start_browser()
        #print(self.get_browse_page_lenght())
        self.ingest_searchpage(1)

    def get_page(self, url):
        """
        gets the static html of a webpage then wait for 10 seconds
        :param url:
        :return:
        """
        if self.debug_mode:
            print("******: getting url: {}".format(url))

        try:
            page = self.driver.get(url)
        except selenium.common.exceptions.TimeoutException as timeout_error:
            print("Got time out error, Restarting browser.")
            self.start_browser()
            self.restarted_attempted = True


        time.sleep(self.delay)

        return self.driver.page_source

    def time_out_holding_pattern(self, url):
        time.sleep(self.delay)
        count = 0

        while True:
            count += 1
            time.sleep(self.delay)
            print("attempting to get page, attempt number: {}".format(count))

            try:
                page = self.driver.get(url)

                if self.driver.page_source:
                    return self.driver.page_source

            except selenium.common.exceptions.TimeoutException as timeout_error:
                pass

    def start_browser(self):
        if self.debug_mode:
            print("******: starting headles chrome browser")
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        #chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--window-size=1024x1400")
        s=Service(DRIVER_PATH)
        if self.debug_mode:
            print("******: created browser options")

        if self.debug_mode:
            print("******: starting driver")
        #self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        self.driver = uc.Chrome(use_subprocess=True, options=chrome_options)
        # make us able to get past Cloudflare whilie in Headless mode
        # stealth(self.driver,
        #         platform="Win32",
        #         fix_hairline=True)

        # self.driver.get("https://www.fanfiction.net")
        #
        # wait = WebDriverWait(self.driver, 10)
        # if self.debug_mode:
        #     print("******: auto completeing page")
        # time.sleep(5) #box takes a second or 2 to appear
        #
        # cookie_agree_xpath = '//*[@id="cookie_notice"]/div/table/tbody/tr/td[2]/div'
        #
        # I_agree = wait.until(EC.presence_of_element_located((By.XPATH, cookie_agree_xpath)))
        # I_agree.click()

        return True

    def ingest_searchpage(self, search_page):
        story_Batch = []
        search_page_soup = BeautifulSoup(self.get_page(self.root_url.format(search_page)), 'html.parser')

        stories = search_page_soup.find_all('div', style="min-height:77px;border-bottom:1px #cdcdcd solid;")

        for index, story in enumerate(stories):
            story_object = {}
            story_metadata = self.get_story_metadata(story)

            if story_metadata == '<_STORY NOT IN ENGLISH_>':
                print("\n-------------------------------------------")
                print("story is not in English, moving onto next one")
                print("\n-------------------------------------------")
                continue



            if not self.check_ingested_log(story_metadata):
                print("\n-------------------------------------------")
                print("Story has already been Ingested, skipping")
                print("\n-------------------------------------------")
                continue

            story_object['MetaData'] = story_metadata

            print("Starting ingest of {title}, it has {ch} chapters".format(title=story_metadata['Title'].encode('utf-8'),
                                                                            ch=story_metadata['Chapters'],))
            story_content = self.collect_story(story_metadata)
            story_object['Content'] = story_content
            print("Ingesting story {} of {} in current batch".format(index, len(stories)))


            print("This is add_singles: ", self.add_singles)
            print("This is database Class: ", self.data_base)
            if self.add_singles and self.data_base:
                print("Adding {} to the data base in {} collection.".format(story_metadata['Title'].encode('utf-8'),
                                                                            self.target_col))
                self.data_base.add_to_database(itemToAdd=story_object,
                                               targetCollection=self.target_col,
                                               print_IDs=True)
            else:
                story_Batch.append(story_object)
        return story_Batch

    def get_browse_page_lenght(self):
        """
        Get the highest page number from the search so we know how far we can go
        :return: int, the number of the last page
        """
        root_page = self.get_page(self.root_url.format(" "))
        root_page_soup = BeautifulSoup(root_page, 'html.parser')

        page_bar = root_page_soup.find_all('center', style='margin-top:5px;margin-bottom:5px;')[0]

        # iterate across the page navigation bar and find the url extract the target page number
        page_nums = []
        for page in page_bar:
            try:
                page_num = int(page.get('href').split("=")[-1])
                page_nums.append(page_num)
            except AttributeError:
                continue

        # retunr the highest number
        return max(page_nums)

    def get_story_metadata(self, story):
        story_metadata_object = {}

        title = story.find_all('a', class_='stitle')[0]
        story_metadata_object['Title'] = title.get_text()
        story_metadata_object["Link"] = title['href']

        all_links = story.find_all('a')
        for link in all_links:
            link_text = link.get_text()
            if link_text and link_text != title and link_text != 'reviews':
                story_metadata_object['Author'] = link_text

        summary = story.find('div', class_='z-indent z-padtop').next_element
        story_metadata_object["Story Summary"] = summary.get_text()

        story_data = story.find('div', class_='z-padtop2 xgray').next_element.get_text()

        # extract all the meta data tags
        metadata_elements = story_data.split("-")
        story_not_in_english = True

        for data in metadata_elements:
            if data in METADATA_SKIP:
                continue
            if 'English' in data:
                print("story is in english")
                story_not_in_english = False
            if "Chapters:" in data:
                chapter_number = int(data.replace("Chapters: ", ""))
                story_metadata_object['Chapters'] = chapter_number
            if "Words:" in data:
                wordcount = data.replace("Words: ", "").replace(",", "")
                story_metadata_object['word count'] =  int(wordcount)

        if story_not_in_english:
            return "<_STORY NOT IN ENGLISH_>"

        # if the genere is'nt given another tag will be at this postion(normally languge or chapters)
        # lets look through and see if we have a genre in here and not another tag
        genre_candiate = metadata_elements[2]
        is_genre = True
        for tag in METADATA_TAGS:
            if tag in genre_candiate or tag == 'English':
                is_genre = False
        if is_genre:
            story_metadata_object['genre'] = genre_candiate
        else:
            story_metadata_object['genre'] = "No genre given"

        # the acutal tags are user typed and not seprated by any common chracter and not always present
        # so we have to get a bit hacky

        full_summary = story.find_all('div', class_= 'z-indent z-padtop')[0].get_text()
        story_tags = full_summary.split("-")[-1]

        is_u_tags= True
        for tag in METADATA_SKIP:
            if tag in story_tags:
                is_u_tags = False

        if is_u_tags:
            split_tags = re.split('[?,]', story_tags)
            clean_tags = []
            for tag in split_tags:
                tag = tag.replace("[", "")
                tag = tag.replace("]", "")
                clean_tags.append(tag)
            story_metadata_object['Tags'] = clean_tags
        else:
            story_metadata_object['Tags'] = "NONE GIVEN"

        return story_metadata_object

    def collect_story(self, metadata):
        # build url format string
        story_object = {}

        url_split = metadata['Link'].split("/")
        story_chapter_amount = metadata['Chapters']

        url_elements = [URL_CONSTANT, "s", url_split[2], "{}"]
        story_url = "/".join(url_elements)

        print("*"*30)
        print("Starting collection, estimated time is {}".format(self.estimate_collection_time(story_chapter_amount)))
        print("*" * 30)

        for chapter in range(story_chapter_amount):
            chapter_num = chapter+1
            chapter_url = story_url.format(chapter_num)

            chapter_soup = BeautifulSoup(self.get_page(chapter_url), 'html.parser')
            chapter_content = chapter_soup.find_all('div',class_="storytext xcontrast_txt nocopy")[0].get_text()
            story_object[str(chapter_num)] = chapter_content
            print("--collected chapter {} of  {}".format(chapter_num, story_chapter_amount))

        return story_object



    def estimate_collection_time(self, chapter_amount):
        estimate_seconds = ((self.delay + 15) * chapter_amount)
        return str(datetime.timedelta(seconds=estimate_seconds))
