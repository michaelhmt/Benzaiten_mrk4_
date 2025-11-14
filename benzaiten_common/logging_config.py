# -*- coding: utf-8 -*-
# coding=utf8

"""
Centralized logging configuration for Benzaiten
"""

import logging
import os
import sys
import json
from pathlib import Path


def get_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


def setup_logging(name=None, log_file=None, level=None):
    """
    Set up logging with both file and console handlers

    Args:
        name: Logger name (defaults to module name)
        log_file: Path to log file (defaults to config value)
        level: Logging level (defaults to config value)

    Returns:
        logging.Logger instance
    """
    config = get_config()
    log_config = config.get('logging', {})

    # Get logger
    logger = logging.getLogger(name or __name__)

    # Set level
    log_level = level or log_config.get('level', 'INFO')
    logger.setLevel(getattr(logging, log_level))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(log_format)

    # Console handler
    if log_config.get('console_output', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    log_file_path = log_file or log_config.get('file', 'benzaiten.log')
    if not os.path.isabs(log_file_path):
        log_file_path = Path(__file__).parent.parent / log_file_path

    try:
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not create log file handler: {e}")

    return logger


def get_logger(name):
    """
    Get or create a logger with the given name

    Args:
        name: Logger name

    Returns:
        logging.Logger instance
    """
    return setup_logging(name)
