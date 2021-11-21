# -*- coding: utf-8 -*-
#site packages
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
from bs4 import BeautifulSoup

#buildt in
import time


HEADER_ = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.116 Safari/537.36'}
STORY_PAGE_CONSTANT = 'https://archiveofourown.org{url}?view_adult=true">Proceed'
STORY_INDEX_CONSTANT = "https://archiveofourown.org{url}/navigate"
SEARCHPAGE_CONSTANT = 'https://archiveofourown.org/tags/Shingeki no Kyojin | Attack on Titan/works?page={}'

DRIVER_PATH = 'E:\\Python\\Benzaiten_mrk4\\chromedriver.exe' #the path where you have "chromedriver" file.



#.encode('utf-8')

class root_page(object):

    def __init__(self, url, goto=None, delay=9):
        """
        will be given root starting page of a archive our our own index page, will go to the next page from there
        :param url: str: the root index page
        """
        self.delay = delay
        self.root_url = url
        self.root = self.get_page(self.root_url)
        self.root_soup = BeautifulSoup(self.root.content, 'html.parser')
        self.limt = goto

    def ingest(self, search_page_to_ingest):
        """
        assume root is popoulated and also grab the current page  and decides how far we go
        This one might be moved to the scraper class so we can add to the DB
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

        searchpage_url = SEARCHPAGE_CONSTANT.format(pagenum)
        searcpage = self.get_page(searchpage_url)

        searcpage_soup = BeautifulSoup(searcpage.content, 'html.parser')
        story_list = searcpage_soup.find_all(role='article')

        def estimate(chapters):
            try:
                chapters_num = int(chapters)
            except ValueError:
                return "Dont know"

            estimate = (self.delay * chapters_num)
            if estimate >= 60:
                return "{} Minute(s)".format(estimate/60)
            else:
                return "{} Seconds".format(estimate)



        for story in story_list:
            story_object = {}
            story_metadata = self.get_Story_meta_data(story)
            story_object['MetaData'] = story_metadata

            print(story_metadata)

            if story_metadata == '<_STORY NOT IN ENGLISH_>':
                print("story is not in English, moving onto next one")
                continue

            Time_to_complete = estimate(story_metadata['Chapters'])
            print(Time_to_complete)
            print("Starting ingest of {title}, it has {ch} chapters, estimated to take {time}".format(title=story_metadata['Title'],
                                                                                                            ch=story_metadata['Chapters'],
                                                                                                            time=Time_to_complete))
            story_content = self.ingest_story(story_metadata['Link'])
            print("----------Finished Ingest----------------")
            story_object['Content'] = story_content

            story_Batch.append(story_object)

        for story in story_Batch:
            print("\n--------------\n",story)

        return story_Batch





    def get_page(self, url):
        """
        gets the static html of a webpage then wait for 10 seconds
        :param url:
        :return:
        """
        page = requests.get(url, headers=HEADER_)
        time.sleep(self.delay)
        return page

    def get_dynamic_page(self, url):
        """
        gets dynamic web page source insluding javascript elements then waits 10 seconds
        :param url:
        :return:
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        #chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--window-size=1024x1400")
        s=Service(DRIVER_PATH)

        driver = webdriver.Chrome(options=chrome_options, service=s)
        time.sleep(self.delay)
        page = driver.get(url)
        #print(driver.page_source)
        return driver.page_source

    def get_browse_page_lenght(self):
        """
        Gets the amount of pages within the given search
        :return:
        """
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
                print("could not get page num from {}".format(url))
        return max(page_nums)

    def get_Story_meta_data(self, article_card):
        """
        Makes a metadata object that will cotian useful info about the story like its title chapter numbers and a link to the story
        :param article_card:
        :return:
        """
        story_metaData_Object = {}

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

        Tags = article_card.find_all(class_='tag')
        story_metaData_Object["Tags"] = [tag.get_text() for tag in Tags]

        Summary = article_card.find_all(class_='userstuff summary')
        story_metaData_Object["Story Summary"] = [paragraph.get_text() + "\n \n" for paragraph in Summary]

        #stats
        story_Language = article_card.find_all('dd', class_='language')[0].get_text()
        chapters = article_card.find_all('dd', class_='chapters')[0].get_text()

        if story_Language != 'English':
            return "<_STORY NOT IN ENGLISH_>"

        current_chapters = int(chapters.split("/")[0])

        story_metaData_Object["Language"] = story_Language
        story_metaData_Object["Chapters"] = current_chapters

        return story_metaData_Object

    def Story_index(self, link):
        """
        Gets the index page for the given story
        :param link:
        :return: a lst of link to chapters for that story
        """
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
        chapter_contents = []

        chapterlink = STORY_PAGE_CONSTANT.format(url=link)
        chapter_page = self.get_dynamic_page(chapterlink)

        chapter_soup = BeautifulSoup(chapter_page, 'html.parser')

        chpaters_group = chapter_soup.find_all('div', class_='chapter')[0]
        chapters = chpaters_group.find_all(role='article')

        for phargraph in chapters:
            text = phargraph.get_text()
            if len(text) > 35:
                print("sample")
                print(text[0:34])
            chapter_contents.append(text)
        return chapter_contents

    def ingest_story(self, link):
        """
        give a link from metadata object, will get a lst of chpater link and get the strings of the chapters
        returns a dict with int as keys for the chpater number. starting at 1
        :param link:
        :return:
        """
        chapters = {}
        chapter_index = self.Story_index(link)

        count = 1
        for chapter in chapter_index:
            print("----------------------------------------------")
            print("Starting ingest of chapter {}".format(count))
            chapters[count] = self.ingest_chapter(chapter)
            print("Finished ingest of chapter {}".format(count))
            count += 1


        return chapters

