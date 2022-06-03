#buildt in
import os
import sys
import json
import time
import copy
import re
from pprint import pprint

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
from selenium_stealth import stealth
from bs4 import BeautifulSoup

# Benzaiten packages
from scraper_baseclass import BaseScraperClass

SEARCHPAGE_CONSTANT = "https://www.fanfiction.net/anime/Digimon/?&srt=1&r=103&p={}"
DRIVER_PATH = env_object.chrome_driver_path
METADATA_SKIP = ['Rated:', "Reviews:", "Favs:", "Follows:", "Updated:", "Published:"]
METADATA_TAGS = ['Rated:',"Chapters:", "Words:" , "Reviews:", "Favs:", "Follows:", "Updated:", "Published:"]

class FanfictionNetScraper(BaseScraperClass):

    def __init__(self,
                 url,
                 goto=None,
                 delay=9,
                 search_page_constant=SEARCHPAGE_CONSTANT,
                 debug_mode=False, data_base_class=None,
                 add_single_to_db=False):

        super().__init__(url)

        self.root_url = url
        self.limt = goto
        self.delay = delay
        self.search_page_constant = search_page_constant
        self.debug_mode = debug_mode
        self.data_base = data_base_class
        self.add_singles = add_single_to_db


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

        page = self.driver.get(url)
        time.sleep(self.delay)

        return self.driver.page_source

    def start_browser(self):
        if self.debug_mode:
            print("******: starting headles chrom browser")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        #chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--window-size=10x10")
        s=Service(DRIVER_PATH)
        if self.debug_mode:
            print("******: created browser options")

        if self.debug_mode:
            print("******: starting driver")
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

        # make us able to get past Cloudflare whilie in Headless mode
        stealth(self.driver,
                platform="Win32",
                fix_hairline=True)

        return True

    def ingest_searchpage(self, search_page):
        pass
        search_page_soup = BeautifulSoup(self.get_page(self.root_url.format(search_page)), 'html.parser')

        stories = search_page_soup.find_all('div', style="min-height:77px;border-bottom:1px #cdcdcd solid;")

        for index, story in enumerate(stories):
            story_object = {}
            story_meta_data = self.get_story_metadata(story)
            print(story_meta_data)



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
        for data in metadata_elements:
            story_not_in_english = True

            if data in METADATA_SKIP:
                continue
            if data == ' English ':
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





scraper = FanfictionNetScraper("https://www.fanfiction.net/anime/Digimon/?&srt=1&r=103&p={}",
                               goto=2,
                               delay=15,
                               search_page_constant=SEARCHPAGE_CONSTANT,
                               debug_mode=True,
                               data_base_class=None,
                               add_single_to_db=False)