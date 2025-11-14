# -*- coding: utf-8 -*-
# coding=utf8

"""
FanfictionNet web scraper with browser management and logging
"""

# built-in
import os
import sys
import json
import time
import re
import datetime
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
from bs4 import BeautifulSoup

# Benzaiten packages
from webscraper_modules.scraper_baseclass import BaseScraperClass
from Benzaiten_Common.browser_manager import BrowserManager
from Benzaiten_Common.logging_config import get_logger

logger = get_logger(__name__)

# Constants
INGESTED_LOG = env_object.ingested_log_path
DRIVER_PATH = env_object.chrome_driver_path
SEARCHPAGE_CONSTANT = "https://www.fanfiction.net/anime/Digimon/?&srt=1&r=103&p={}"
METADATA_SKIP = ['Rated:', "Reviews:", "Favs:", "Follows:", "Updated:", "Published:"]
METADATA_TAGS = ['Rated:', "Chapters:", "Words:", "Reviews:", "Favs:", "Follows:", "Updated:", "Published:"]
URL_CONSTANT = "https://www.fanfiction.net"


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


class FanfictionNetScraper(BaseScraperClass):
    """FanfictionNet scraper with improved error handling and logging"""

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

        logger.info(f"Initializing FanfictionNetScraper with URL: {url}")

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

        # Initialize browser manager
        self.browser_manager = BrowserManager(
            headless=scraper_config.get('headless', False),
            use_undetected=True,
            driver_path=DRIVER_PATH
        )
        self.browser_manager.start_browser()

        logger.info("FanfictionNetScraper initialized successfully")

    def get_page(self, url: str) -> str:
        """
        Get page HTML with automatic retry logic

        Args:
            url: URL to fetch

        Returns:
            Page HTML source
        """
        logger.debug(f"Fetching page: {url}")
        return self.browser_manager.get_page(url, delay=self.delay)

    def get_browse_page_length(self) -> int:
        """
        Get the highest page number from the search

        Returns:
            Maximum page number
        """
        logger.info("Determining browse page length")

        try:
            root_page = self.get_page(self.root_url.format(" "))
            root_page_soup = BeautifulSoup(root_page, 'html.parser')

            page_bar = root_page_soup.find_all('center', style='margin-top:5px;margin-bottom:5px;')

            if not page_bar:
                logger.warning("Could not find page navigation bar")
                return 1

            page_bar = page_bar[0]

            # Iterate across the page navigation bar and find the URL extract the target page number
            page_nums = []
            for page in page_bar:
                try:
                    page_num = int(page.get('href').split("=")[-1])
                    page_nums.append(page_num)
                except (AttributeError, ValueError):
                    continue

            if not page_nums:
                logger.warning("No page numbers found")
                return 1

            max_page = max(page_nums)
            logger.info(f"Maximum page number: {max_page}")
            return max_page

        except Exception as e:
            logger.error(f"Error determining page length: {e}", exc_info=True)
            return 1

    def get_story_metadata(self, story) -> Dict:
        """
        Extract metadata from story element

        Args:
            story: BeautifulSoup story element

        Returns:
            Dictionary of metadata
        """
        story_metadata_object = {}

        try:
            # Extract title and link
            title = story.find_all('a', class_='stitle')[0]
            story_metadata_object['Title'] = title.get_text()
            story_metadata_object["Link"] = title['href']

            # Extract author
            all_links = story.find_all('a')
            for link in all_links:
                link_text = link.get_text()
                if link_text and link_text != title and link_text != 'reviews':
                    story_metadata_object['Author'] = link_text
                    break

            # Extract summary
            summary = story.find('div', class_='z-indent z-padtop').next_element
            story_metadata_object["Story Summary"] = summary.get_text()

            # Extract story data
            story_data = story.find('div', class_='z-padtop2 xgray').next_element.get_text()

            # Extract metadata elements
            metadata_elements = story_data.split("-")
            story_not_in_english = True

            for data in metadata_elements:
                if 'English' in data:
                    logger.debug("Story is in English")
                    story_not_in_english = False
                if "Chapters:" in data:
                    chapter_number = int(data.replace("Chapters: ", ""))
                    story_metadata_object['Chapters'] = chapter_number
                if "Words:" in data:
                    wordcount = data.replace("Words: ", "").replace(",", "")
                    story_metadata_object['word count'] = int(wordcount)

            if story_not_in_english:
                return {"error": "<_STORY NOT IN ENGLISH_>"}

            # Extract genre
            genre_candidate = metadata_elements[2] if len(metadata_elements) > 2 else ""
            is_genre = True
            for tag in METADATA_TAGS:
                if tag in genre_candidate or tag == 'English':
                    is_genre = False
                    break

            if is_genre:
                story_metadata_object['genre'] = genre_candidate
            else:
                story_metadata_object['genre'] = "No genre given"

            # Extract tags
            full_summary = story.find_all('div', class_='z-indent z-padtop')[0].get_text()
            story_tags = full_summary.split("-")[-1]

            is_u_tags = True
            for tag in METADATA_SKIP:
                if tag in story_tags:
                    is_u_tags = False
                    break

            if is_u_tags:
                split_tags = re.split('[?,]', story_tags)
                clean_tags = [tag.replace("[", "").replace("]", "") for tag in split_tags]
                story_metadata_object['Tags'] = clean_tags
            else:
                story_metadata_object['Tags'] = "NONE GIVEN"

            # Add source
            story_metadata_object['SOURCE'] = 'FanFictionNet'

            return story_metadata_object

        except Exception as e:
            logger.error(f"Error extracting metadata: {e}", exc_info=True)
            return {"error": f"Failed to extract metadata: {e}"}

    def collect_story(self, metadata: Dict) -> Dict:
        """
        Collect all chapters of a story

        Args:
            metadata: Story metadata dictionary

        Returns:
            Dictionary of chapter contents
        """
        story_object = {}

        try:
            url_split = metadata['Link'].split("/")
            story_chapter_amount = metadata['Chapters']

            url_elements = [URL_CONSTANT, "s", url_split[2], "{}"]
            story_url = "/".join(url_elements)

            estimated_time = self.estimate_collection_time(story_chapter_amount)
            logger.info(f"Starting collection, estimated time: {estimated_time}")

            for chapter in range(story_chapter_amount):
                chapter_num = chapter + 1
                chapter_url = story_url.format(chapter_num)

                chapter_soup = BeautifulSoup(self.get_page(chapter_url), 'html.parser')
                chapter_content_element = chapter_soup.find_all('div', class_="storytext xcontrast_txt nocopy")

                if not chapter_content_element:
                    logger.warning(f"No content found for chapter {chapter_num}")
                    continue

                chapter_content = chapter_content_element[0].get_text()
                story_object[str(chapter_num)] = chapter_content
                logger.info(f"Collected chapter {chapter_num} of {story_chapter_amount}")

            return story_object

        except Exception as e:
            logger.error(f"Error collecting story: {e}", exc_info=True)
            return {}

    def estimate_collection_time(self, chapter_amount: int) -> str:
        """
        Estimate time to collect story

        Args:
            chapter_amount: Number of chapters

        Returns:
            Formatted time string
        """
        estimate_seconds = ((self.delay + 15) * chapter_amount)
        return str(datetime.timedelta(seconds=estimate_seconds))

    def ingest_searchpage(self, search_page: int) -> List[Dict]:
        """
        Ingest all stories from a search page

        Args:
            search_page: Page number to ingest

        Returns:
            List of story dictionaries
        """
        story_batch = []
        logger.info(f"Ingesting search page {search_page}")

        try:
            search_page_soup = BeautifulSoup(
                self.get_page(self.root_url.format(search_page)),
                'html.parser'
            )

            stories = search_page_soup.find_all('div', style="min-height:77px;border-bottom:1px #cdcdcd solid;")
            logger.info(f"Found {len(stories)} stories on page {search_page}")

            for index, story in enumerate(stories):
                story_object = {}
                story_metadata = self.get_story_metadata(story)

                # Check for errors
                if 'error' in story_metadata:
                    if story_metadata['error'] == '<_STORY NOT IN ENGLISH_>':
                        logger.info("Skipping non-English story")
                    else:
                        logger.warning(f"Metadata extraction failed: {story_metadata['error']}")
                    continue

                # Check if already ingested
                if not self.check_ingested_log(story_metadata):
                    logger.info("Story already ingested, skipping")
                    continue

                story_object['MetaData'] = story_metadata

                logger.info(f"Starting ingest of '{story_metadata['Title']}', {story_metadata['Chapters']} chapters")
                story_content = self.collect_story(story_metadata)
                story_object['Content'] = story_content
                logger.info(f"Ingesting story {index + 1} of {len(stories)} in current batch")

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

            logger.info(f"Completed ingesting page {search_page}")
            return story_batch

        except Exception as e:
            logger.error(f"Error ingesting search page {search_page}: {e}", exc_info=True)
            return story_batch

    def close(self):
        """Close browser and cleanup resources"""
        logger.info("Closing FanfictionNetScraper")
        if self.browser_manager:
            self.browser_manager.close()

    def __del__(self):
        """Destructor - ensure cleanup"""
        try:
            self.close()
        except:
            pass
