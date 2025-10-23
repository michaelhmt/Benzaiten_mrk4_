# -*- coding: utf-8 -*-
# coding=utf8

"""
Base scraper class with common functionality for all scrapers
"""

# built-in
import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List

# env settings
def set_env():
    env_dir = os.path.dirname(os.getcwd())
    sys.path.append(env_dir)
set_env()

import Site_custom
env_object = Site_custom.env()

# Benzaiten imports
from benzaiten_common.logging_config import get_logger

logger = get_logger(__name__)

# Constants
INGESTED_LOG = env_object.ingested_log_path


class BaseScraperClass(object):
    """Base class for all web scrapers with common functionality"""

    def __init__(self,
                 url: str,
                 goto: Optional[int] = None,
                 delay: Optional[int] = None,
                 search_page_constant: str = "Not given",
                 debug_mode: bool = False,
                 data_base_class=None,
                 add_single_to_db: bool = False,
                 target_col: Optional[str] = None):
        """
        Initialize base scraper

        Args:
            url: Root URL for search pages
            goto: Page number limit (None for no limit)
            delay: Delay between requests
            search_page_constant: URL template for search pages
            debug_mode: Enable debug logging
            data_base_class: Database instance for storage
            add_single_to_db: Add stories individually vs batching
            target_col: Target collection name
        """
        logger.info("Initializing scraper base class")

        self.debug_mode = debug_mode
        self.data_base = data_base_class
        self.add_singles = add_single_to_db
        self.target_col = target_col

        self.search_page_constant = search_page_constant
        self.delay = delay or 9
        self.root_url = url
        self.limit = goto

        self.ingested_log = None

    def open_ingested_log(self) -> Dict:
        """
        Open or create ingested log file

        Returns:
            Dictionary of ingested stories
        """
        # Create log if it doesn't exist
        if not os.path.exists(INGESTED_LOG):
            logger.info("Creating new ingested log file")
            with open(INGESTED_LOG, 'a+') as i_log:
                blank_log = {
                    "Author": [],
                    "Link": [],
                    "Title": []
                }
                json.dump(blank_log, i_log, indent=4)

        # Load log data
        try:
            with open(INGESTED_LOG) as log_file:
                data = json.load(log_file)
            logger.debug(f"Loaded ingested log with {len(data.get('Title', []))} entries")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Error reading ingested log: {e}")
            return {"Author": [], "Link": [], "Title": []}

    def check_ingested_log(self, metadata: Dict) -> bool:
        """
        Check if story has already been ingested

        Args:
            metadata: Story metadata dictionary

        Returns:
            True if story should be ingested, False if already ingested
        """
        logger.debug(f"Checking ingested log for '{metadata.get('Title', 'Unknown')}'")

        try:
            title = metadata.get('Title')
            link = metadata.get('Link')

            if not link:
                logger.warning("Bad metadata: missing link")
                return False

            # Check if already ingested
            if title in self.ingested_log.get('Title', []) and link in self.ingested_log.get('Link', []):
                logger.info(f"Story '{title}' already ingested")
                return False

            # Add to ingested log
            metadata_to_submit = [
                metadata.get('Author', 'Unknown'),
                link,
                title
            ]
            self.add_to_ingested_log(metadata_to_submit)
            return True

        except (KeyError, IndexError) as e:
            logger.error(f"Error checking ingested log: {e}", exc_info=True)
            return False

    def add_to_ingested_log(self, metadata_to_add: List[str]):
        """
        Add story to ingested log

        Args:
            metadata_to_add: List with [Author, Link, Title]
        """
        logger.debug(f"Adding to ingested log: {metadata_to_add[2]}")

        try:
            with open(INGESTED_LOG, 'r+') as i_log:
                current_data = json.load(i_log)
                current_data['Author'].append(metadata_to_add[0])
                current_data['Link'].append(metadata_to_add[1])
                current_data['Title'].append(metadata_to_add[2])
                i_log.seek(0)
                i_log.truncate()  # Clear file before writing
                json.dump(current_data, i_log, indent=4)

            logger.info(f"Added '{metadata_to_add[2]}' to ingested log")

        except Exception as e:
            logger.error(f"Error adding to ingested log: {e}", exc_info=True)

    def get_browse_page_length(self) -> int:
        """
        Get the maximum page number from search results
        (Must be implemented by subclasses)

        Returns:
            Maximum page number
        """
        raise NotImplementedError("get_browse_page_length has not been implemented")

    def ingest_searchpage(self, search_page_to_ingest: int) -> List[Dict]:
        """
        Ingest all stories from a search page
        (Must be implemented by subclasses)

        Args:
            search_page_to_ingest: Page number to ingest

        Returns:
            List of story dictionaries
        """
        raise NotImplementedError("ingest_searchpage has not been implemented")
