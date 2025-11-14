# -*- coding: utf-8 -*-
# coding=utf8

"""
Archive of Our Own web scraper with browser management and logging
"""

# built-in
import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, List

# env settings
def set_env():
    env_dir = os.path.dirname(os.getcwd())
    sys.path.append(env_dir)
set_env()

import Site_custom
env_object = Site_custom.env()

# site packages
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

# Benzaiten packages
from webscraper_modules.scraper_baseclass import BaseScraperClass
from benzaiten_common.browser_manager import BrowserManager
from benzaiten_common.logging_config import get_logger

logger = get_logger(__name__)

# Constants
HEADER_ = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.116 Safari/537.36'}
STORY_PAGE_CONSTANT = 'https://archiveofourown.org{url}?view_adult=true">Proceed'
STORY_INDEX_CONSTANT = "https://archiveofourown.org{url}/navigate"
SEARCHPAGE_CONSTANT = 'https://archiveofourown.org/tags/Harry%20Potter%20-%20J*d*%20K*d*%20Rowling/works?page={}'
VIEW_ALL_CONSTANT = "https://archiveofourown.org{url}?view_adult=true&view_full_work=true"

DRIVER_PATH = env_object.chrome_driver_path
INGESTED_LOG = env_object.ingested_log_path


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


class ArchiveOfOurOwnScraper(BaseScraperClass):
    """Archive of Our Own scraper with improved error handling and logging"""

    def __init__(self,
                 url: str,
                 goto: Optional[int] = None,
                 delay: Optional[int] = None,
                 search_page_constant: str = SEARCHPAGE_CONSTANT,
                 debug_mode: bool = False,
                 data_base_class=None,
                 add_single_to_db: bool = False,
                 target_col: Optional[str] = None):
        """
        Initialize scraper

        Args:
            url: Base URL for search pages
            goto: Page number limit (None for no limit)
            delay: Delay between requests (defaults to config)
            search_page_constant: URL template for search pages
            debug_mode: Enable debug logging
            data_base_class: Database instance for storage
            add_single_to_db: Add stories individually vs batching
            target_col: Target collection name
        """
        super().__init__(url, goto, delay, search_page_constant, debug_mode, data_base_class, add_single_to_db, target_col)

        logger.info(f"Initializing ArchiveOfOurOwnScraper with URL: {url}")

        self.config = load_config()
        scraper_config = self.config.get('scraper_settings', {})

        self.root_url = url
        self.limit = goto
        self.delay = delay or scraper_config.get('default_delay', 9)
        self.search_page_constant = search_page_constant
        self.debug_mode = debug_mode
        self.data_base = data_base_class
        self.add_singles = add_single_to_db
        self.target_col = target_col

        self.ingested_log = self.open_ingested_log()

        # Get initial page info with static request
        logger.info("Fetching initial page with requests library")
        self.root = requests.get(self.root_url, headers=HEADER_)
        time.sleep(self.delay)
        self.root_soup = BeautifulSoup(self.root.content, 'html.parser')

        # Initialize browser manager for dynamic content
        self.browser_manager = BrowserManager(
            headless=scraper_config.get('headless', True),
            use_undetected=False,
            driver_path=DRIVER_PATH
        )
        self.browser_manager.start_browser()

        # Handle adult content warning on AO3
        self._handle_adult_content_warning()

        logger.info("ArchiveOfOurOwnScraper initialized successfully")

    def _handle_adult_content_warning(self):
        """Navigate through Archive of Our Own's adult content warning"""
        try:
            logger.info("Handling AO3 adult content warning")
            test_url = 'https://archiveofourown.org/works/29832528?view_full_work=true'
            self.browser_manager.driver.get(test_url)

            wait = WebDriverWait(self.browser_manager.driver, 10)
            time.sleep(5)  # Wait for warning box to appear

            # Accept terms of service
            logger.debug("Clicking TOS agreement")
            tos_agree = wait.until(EC.presence_of_element_located((By.ID, 'tos_agree')))
            tos_agree.click()

            tos_button = wait.until(EC.presence_of_element_located((By.ID, 'accept_tos')))
            tos_button.click()

            # Click proceed button
            proceed = wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Proceed")))
            proceed.click()

            logger.info("Successfully handled adult content warning")

        except TimeoutException:
            logger.warning("Timeout waiting for adult content warning elements (may already be accepted)")
        except Exception as e:
            logger.error(f"Error handling adult content warning: {e}", exc_info=True)

    def get_page(self, url: str) -> requests.Response:
        """
        Get static page with requests library

        Args:
            url: URL to fetch

        Returns:
            requests.Response object
        """
        logger.debug(f"Fetching static page: {url}")
        page = requests.get(url, headers=HEADER_)
        time.sleep(self.delay)
        return page

    def get_dynamic_page(self, url: str) -> str:
        """
        Get dynamic page with browser (for JavaScript-rendered content)

        Args:
            url: URL to fetch

        Returns:
            Page source HTML
        """
        logger.debug(f"Fetching dynamic page: {url}")
        return self.browser_manager.get_page(url, delay=self.delay)

    def get_browse_page_length(self) -> int:
        """
        Get the maximum page number from search results

        Returns:
            Maximum page number
        """
        logger.info("Determining browse page length")

        try:
            navigation_bar = self.root_soup.find_all(title='pagination')
            if not navigation_bar:
                logger.warning("No pagination found")
                return 1

            navigation_bar = navigation_bar[0]
            buttons = navigation_bar.find_all('a')
            page_nums = []

            for button in buttons:
                url = button.get('href', '')
                urls_split = url.split("=")
                try:
                    pagenum = int(urls_split[-1])
                    page_nums.append(pagenum)
                except (ValueError, IndexError):
                    logger.debug(f"Could not extract page number from URL: {url}, trying button text")
                    button_text = str(button.get_text())
                    if button_text.isnumeric():
                        page_nums.append(int(button_text))

            if not page_nums:
                logger.warning("No page numbers found")
                return 1

            max_page = max(page_nums)
            logger.info(f"Maximum page number: {max_page}")
            return max_page

        except Exception as e:
            logger.error(f"Error determining page length: {e}", exc_info=True)
            return 1

    def get_story_metadata(self, article_card) -> Dict:
        """
        Extract metadata from story article element

        Args:
            article_card: BeautifulSoup article element

        Returns:
            Dictionary of metadata
        """
        story_metadata_object = {}
        story_metadata_object["SOURCE"] = "ArchiveOfOurOwn"

        try:
            # Extract title and author
            title_elements = article_card.find_all(class_='heading')
            for entry in title_elements:
                if 'Fandoms:' not in entry.get_text():
                    try:
                        lines = entry.find_all('a')
                        story_metadata_object["Link"] = lines[0]['href']
                    except (IndexError, KeyError):
                        continue

                    try:
                        split_title = entry.get_text().split("\n")
                        story_metadata_object["Title"] = split_title[1]
                        story_metadata_object["Author"] = split_title[5]
                    except IndexError:
                        continue

            # Extract tags
            tags = article_card.find_all(class_='tag')
            story_metadata_object["Tags"] = [tag.get_text() for tag in tags]

            # Extract summary
            summary = article_card.find_all(class_='userstuff summary')
            story_metadata_object["Story Summary"] = [paragraph.get_text() + "\n \n" for paragraph in summary]

            # Extract language and chapters
            language_element = article_card.find_all('dd', class_='language')
            chapters_element = article_card.find_all('dd', class_='chapters')

            if not language_element or not chapters_element:
                logger.warning("Missing language or chapters metadata")
                return {"error": "Missing required metadata"}

            story_language = language_element[0].get_text()
            chapters = chapters_element[0].get_text()

            if story_language != 'English':
                return {"error": "<_STORY NOT IN ENGLISH_>"}

            current_chapters = chapters.split("/")[0]
            story_metadata_object["Language"] = story_language
            story_metadata_object["Chapters"] = current_chapters

            return story_metadata_object

        except Exception as e:
            logger.error(f"Error extracting metadata: {e}", exc_info=True)
            return {"error": f"Failed to extract metadata: {e}"}

    def ingest_chapter(self, link: str) -> Dict:
        """
        Ingest a single chapter story

        Args:
            link: Story link

        Returns:
            Dictionary with chapter text
        """
        logger.info(f"Ingesting single chapter: {link}")

        try:
            chapter_text = []
            chapter_link = STORY_PAGE_CONSTANT.format(url=link)
            chapter_page = self.get_dynamic_page(chapter_link)
            chapter_soup = BeautifulSoup(chapter_page, 'html.parser')

            chapter_group = chapter_soup.find('div', class_='userstuff module')

            if chapter_group:
                for tag in chapter_group:
                    text = tag.get_text() if hasattr(tag, 'get_text') else str(tag)
                    if text.strip():
                        chapter_text.append(text)
            else:
                # Fallback to simpler search
                userstuff = chapter_soup.find('div', class_='userstuff')
                if userstuff:
                    chapter_text.append(userstuff.get_text())

            joined_text = ' '.join(chapter_text)
            logger.info(f"Collected single chapter, length: {len(chapter_text)} elements")
            return {"1": joined_text}

        except Exception as e:
            logger.error(f"Error ingesting chapter: {e}", exc_info=True)
            return {"1": ""}

    def ingest_full_story(self, link: str) -> Dict:
        """
        Ingest a multi-chapter story

        Args:
            link: Story link

        Returns:
            Dictionary of chapters
        """
        logger.info(f"Ingesting full story: {link}")

        chapters = {}

        try:
            full_story_link = VIEW_ALL_CONSTANT.format(url=link)
            logger.debug(f"Full story URL: {full_story_link}")
            full_story_page = self.get_dynamic_page(full_story_link)

            story_soup = BeautifulSoup(full_story_page, 'html.parser')
            chapters_lst = story_soup.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['chapter'])

            logger.info(f"Found {len(chapters_lst)} chapters")

            for count, chapter in enumerate(chapters_lst, start=1):
                chapter_num = count
                text = chapter.get_text()

                if len(text) > 90:
                    logger.debug(f"Chapter {chapter_num} sample: {text[:120]}")

                logger.debug(f"Chapter {chapter_num} size: {sys.getsizeof(text)} bytes")
                chapters[str(chapter_num)] = text

            logger.info(f"Successfully ingested {len(chapters)} chapters")
            return chapters

        except Exception as e:
            logger.error(f"Error ingesting full story: {e}", exc_info=True)
            return {}

    def ingest_story(self, link: str, name: str, ingest_single: bool = False) -> Dict:
        """
        Ingest a story (single chapter or multi-chapter)

        Args:
            link: Story link
            name: Story name
            ingest_single: Whether this is a single chapter story

        Returns:
            Dictionary of chapters
        """
        logger.info(f"Starting ingest of '{name}' (single_chapter={ingest_single})")

        try:
            if ingest_single:
                chapters = self.ingest_chapter(link)
            else:
                chapters = self.ingest_full_story(link)

            logger.info(f"Finished ingesting '{name}'")
            return chapters

        except Exception as e:
            logger.error(f"Error ingesting story '{name}': {e}", exc_info=True)
            return {}

    def ingest_searchpage(self, pagenum: int) -> List[Dict]:
        """
        Ingest all stories from a search page

        Args:
            pagenum: Page number to ingest

        Returns:
            List of story dictionaries
        """
        story_batch = []
        logger.info(f"Ingesting search page {pagenum}")

        try:
            searchpage_url = self.search_page_constant.format(pagenum)
            searchpage = self.get_page(searchpage_url)
            searchpage_soup = BeautifulSoup(searchpage.content, 'html.parser')
            story_list = searchpage_soup.find_all(role='article')

            logger.info(f"Found {len(story_list)} stories on page {pagenum}")

            for count, story in enumerate(story_list):
                story_object = {}
                story_metadata = self.get_story_metadata(story)

                # Check for errors
                if 'error' in story_metadata:
                    if story_metadata['error'] == '<_STORY NOT IN ENGLISH_>':
                        logger.info("Skipping non-English story")
                    else:
                        logger.warning(f"Metadata extraction failed: {story_metadata['error']}")
                    continue

                story_object['MetaData'] = story_metadata

                # Check if already ingested
                if not self.check_ingested_log(story_metadata):
                    logger.info("Story already ingested, skipping")
                    continue

                is_single_chapter = int(story_metadata['Chapters']) == 1
                logger.info(f"Starting ingest of '{story_metadata['Title']}', {story_metadata['Chapters']} chapters")
                story_content = self.ingest_story(story_metadata['Link'], story_metadata['Title'], ingest_single=is_single_chapter)
                story_object['Content'] = story_content
                logger.info(f"Ingesting story {count + 1} of {len(story_list)} in current batch")

                # Add to database if configured
                if self.add_singles and self.data_base:
                    logger.info(f"Adding '{story_metadata['Title']}' to database collection '{self.target_col}'")
                    self.data_base.add_to_database(
                        itemToAdd=story_object,
                        targetCollection=self.target_col,
                        print_IDs=True
                    )
                else:
                    story_batch.append(story_object)

            logger.info(f"Completed ingesting page {pagenum}")
            return story_batch

        except Exception as e:
            logger.error(f"Error ingesting search page {pagenum}: {e}", exc_info=True)
            return story_batch

    def close(self):
        """Close browser and cleanup resources"""
        logger.info("Closing ArchiveOfOurOwnScraper")
        if self.browser_manager:
            self.browser_manager.close()

    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.close()
        except:
            pass


# Keep backward compatibility with old class name
ArchiveOOO = ArchiveOfOurOwnScraper
