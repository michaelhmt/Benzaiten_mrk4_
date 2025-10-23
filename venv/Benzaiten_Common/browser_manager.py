# -*- coding: utf-8 -*-
# coding=utf8

"""
Browser manager with context manager support and proper resource cleanup
"""

import time
import json
from pathlib import Path
from typing import Optional
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc

from logging_config import get_logger

logger = get_logger(__name__)


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


class BrowserManager:
    """
    Context manager for browser instances with automatic cleanup
    and retry logic for page loads
    """

    def __init__(self, headless=None, use_undetected=True, driver_path=None):
        """
        Initialize browser manager

        Args:
            headless: Run browser in headless mode (defaults to config)
            use_undetected: Use undetected_chromedriver (for bypassing detection)
            driver_path: Path to chromedriver executable
        """
        self.config = load_config()
        self.scraper_config = self.config.get('scraper_settings', {})

        self.headless = headless if headless is not None else self.scraper_config.get('headless', True)
        self.use_undetected = use_undetected
        self.driver_path = driver_path
        self.driver: Optional[webdriver.Chrome] = None
        self.retry_count = 0
        self.max_retries = self.scraper_config.get('max_retries', 3)

        logger.info(f"BrowserManager initialized (headless={self.headless}, undetected={use_undetected})")

    def __enter__(self):
        """Context manager entry - start browser"""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser"""
        self.close()
        return False  # Don't suppress exceptions

    def start_browser(self):
        """Start the browser instance"""
        if self.driver:
            logger.warning("Browser already started, closing previous instance")
            self.close()

        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")

            window_size = self.scraper_config.get('window_size', '1024x1400')
            chrome_options.add_argument(f"--window-size={window_size}")

            # Set page load timeout
            timeout = self.scraper_config.get('page_load_timeout', 30)

            if self.use_undetected:
                logger.info("Starting undetected Chrome driver")
                self.driver = uc.Chrome(use_subprocess=True, options=chrome_options)
            else:
                logger.info("Starting standard Chrome driver")
                if self.driver_path:
                    service = Service(self.driver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    self.driver = webdriver.Chrome(options=chrome_options)

            self.driver.set_page_load_timeout(timeout)
            logger.info(f"Browser started successfully (timeout={timeout}s)")

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    def get_page(self, url: str, delay: Optional[float] = None) -> str:
        """
        Get a page with automatic retry on timeout

        Args:
            url: URL to fetch
            delay: Delay after successful load (defaults to config)

        Returns:
            Page source HTML

        Raises:
            RuntimeError: If max retries exceeded
        """
        if not self.driver:
            raise RuntimeError("Browser not started. Use 'with BrowserManager()' or call start_browser()")

        delay = delay or self.scraper_config.get('default_delay', 9)
        backoff_base = self.scraper_config.get('retry_backoff_base', 2)

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Loading page: {url} (attempt {attempt + 1}/{self.max_retries})")
                self.driver.get(url)
                time.sleep(delay)
                logger.debug(f"Page loaded successfully: {url}")
                return self.driver.page_source

            except selenium.common.exceptions.TimeoutException as e:
                logger.warning(f"Timeout loading {url} (attempt {attempt + 1}/{self.max_retries})")

                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff
                    wait_time = delay * (backoff_base ** attempt)
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

                    # Try restarting browser on last retry
                    if attempt == self.max_retries - 2:
                        logger.warning("Restarting browser before final attempt")
                        self.restart_browser()
                else:
                    logger.error(f"Max retries exceeded for {url}")
                    raise RuntimeError(f"Failed to load {url} after {self.max_retries} attempts") from e

            except Exception as e:
                logger.error(f"Unexpected error loading {url}: {e}")
                raise

    def restart_browser(self):
        """Restart the browser instance"""
        logger.info("Restarting browser...")
        self.close()
        time.sleep(2)  # Brief pause before restart
        self.start_browser()

    def close(self):
        """Close the browser and cleanup resources"""
        if self.driver:
            try:
                logger.info("Closing browser...")
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self.driver = None

    def __del__(self):
        """Destructor - ensure browser is closed"""
        self.close()


class RetryablePageLoader:
    """
    Decorator for adding retry logic to page loading functions
    """

    def __init__(self, max_retries=3, backoff_base=2, delay=1):
        """
        Initialize retry decorator

        Args:
            max_retries: Maximum number of retry attempts
            backoff_base: Base for exponential backoff calculation
            delay: Initial delay between retries
        """
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.delay = delay

    def __call__(self, func):
        """Apply retry logic to function"""

        def wrapper(*args, **kwargs):
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except (selenium.common.exceptions.TimeoutException,
                        selenium.common.exceptions.WebDriverException) as e:
                    if attempt < self.max_retries - 1:
                        wait_time = self.delay * (self.backoff_base ** attempt)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{self.max_retries}), "
                            f"retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {self.max_retries} attempts")
                        raise

        return wrapper
