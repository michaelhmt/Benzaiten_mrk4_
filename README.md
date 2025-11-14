# Benzaiten mrk4

A powerful web scraping tool for collecting fanfiction stories from FanFiction.Net and Archive of Our Own (AO3), with data analysis and visualization capabilities.

## Features

- **Multi-Site Scraping**: Support for FanFiction.Net and Archive of Our Own
- **Browser Automation**: Uses undetected-chromedriver to bypass bot detection
- **Data Storage**: MongoDB integration for efficient story storage
- **PyQt5 GUI**: User-friendly interface for managing scraping operations
- **Data Analysis**: Built-in tools for analyzing collected stories
- **Visualization**: Word clouds, tag distributions, and statistical charts
- **Robust Error Handling**: Automatic retries with exponential backoff
- **Comprehensive Logging**: Centralized logging system for debugging

## Project Structure

```
Benzaiten_mrk4_/
├── benzaiten_common/      # Core functionality
│   ├── browser_manager.py # Browser automation with context managers
│   ├── DataBase.py        # MongoDB interface
│   ├── logging_config.py  # Centralized logging
│   └── utils.py           # Utility functions
│
├── benzaiten_ui/          # PyQt5 GUI components
│   ├── ls_startup.py      # Main UI launcher
│   ├── collect_data.py    # Data collection interface
│   └── ui_widgets/        # Custom UI widgets
│
├── webscraper_modules/    # Web scraper implementations
│   ├── scraper_baseclass.py        # Base scraper class
│   ├── fanfiction_net_scraper.py   # FanFiction.Net scraper
│   └── archive_of_our_own.py       # AO3 scraper
│
├── data_tools/            # Data analysis tools
│   └── collection_class.py # Data processing and visualization
│
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
└── TEST_REPORT.md        # Comprehensive test results
```

## Requirements

- Python 3.9 or higher
- MongoDB (for data storage)
- Chrome/Chromium browser (for web scraping)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Benzaiten_mrk4_.git
cd Benzaiten_mrk4_
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB

Update `config.json` with your MongoDB connection details:

```json
{
  "database": {
    "connection_string": "mongodb://localhost:27017",
    "timeout_ms": 5000
  },
  "scraper_settings": {
    "default_delay": 9,
    "page_load_timeout": 30,
    "max_retries": 3,
    "retry_backoff_base": 2,
    "headless": true
  },
  "logging": {
    "level": "INFO",
    "file": "benzaiten.log"
  }
}
```

## Usage

### GUI Mode

Launch the graphical interface:

```bash
python benzaiten_ui/ls_startup.py
```

### Programmatic Usage

#### FanFiction.Net Scraper

```python
from webscraper_modules.fanfiction_net_scraper import FanfictionNetScraper
from benzaiten_common.DataBase import Database_Class

# Initialize database
db = Database_Class('fanfiction_data')

# Create scraper
url_template = "https://www.fanfiction.net/anime/Digimon/?&srt=1&r=103&p={}"
scraper = FanfictionNetScraper(
    url=url_template,
    goto=5,  # Scrape first 5 pages
    data_base_class=db,
    target_col='stories'
)

# Start scraping (this will use the browser manager automatically)
scraper.iterate()
```

#### Archive of Our Own Scraper

```python
from webscraper_modules.archive_of_our_own import ArchiveOfOurOwnScraper
from benzaiten_common.DataBase import Database_Class

# Initialize database
db = Database_Class('ao3_data')

# Create scraper
url_template = "https://archiveofourown.org/tags/Harry%20Potter/works?page={}"
scraper = ArchiveOfOurOwnScraper(
    url=url_template,
    goto=10,  # Scrape first 10 pages
    data_base_class=db,
    target_col='stories'
)

# Start scraping
scraper.iterate()
```

#### Data Analysis

```python
from data_tools.collection_class import Collection_data
from benzaiten_common.DataBase import Database_Class

# Connect to database
db = Database_Class('fanfiction_data')

# Analyze collection
collection = Collection_data(db, 'stories')

# Generate visualizations
collection.create_wordcloud()  # Word cloud from story summaries
collection.tag_breakdown()     # Tag distribution chart
collection.export_to_csv()     # Export data for further analysis
```

## Configuration

### Scraper Settings

- **default_delay**: Delay between page requests (seconds)
- **page_load_timeout**: Maximum time to wait for page load (seconds)
- **max_retries**: Number of retry attempts on failure
- **retry_backoff_base**: Exponential backoff base for retries
- **headless**: Run browser in headless mode (true/false)

### Logging

Logs are written to `benzaiten.log` by default. Adjust the logging level in `config.json`:

- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only

## Data Storage

Stories are stored in MongoDB with the following structure:

```json
{
  "MetaData": {
    "Title": "Story Title",
    "Author": "Author Name",
    "Words": 50000,
    "Chapters": 10,
    "Tags": ["Romance", "Adventure"],
    "Rating": "T",
    "Published": "2021-01-01",
    "Updated": "2021-12-31"
  },
  "Content": {
    "chapters": ["Chapter 1 text...", "Chapter 2 text..."]
  }
}
```

**Note**: Chapter content is stored as zlib-compressed strings. Decompress when retrieving:

```python
import zlib
decompressed = zlib.decompress(compressed_content.encode())
```

## Testing

Run the test suite to verify your installation:

```bash
python test_imports.py      # Test module imports
python test_ui.py           # Test UI components
python test_data_tools.py   # Test data analysis tools
python test_database.py     # Test database connectivity
```

See `TEST_REPORT.md` for detailed test results.

## Recent Refactoring (November 2024)

The project underwent a major refactoring to improve code quality and maintainability:

- ✅ Removed 539MB of site-packages from version control
- ✅ Implemented proper Python package structure
- ✅ Added centralized logging system
- ✅ Implemented browser manager with context managers and automatic cleanup
- ✅ Fixed infinite recursion bugs in retry logic
- ✅ Created comprehensive test suite
- ✅ Updated all import paths for consistency
- ✅ Created `requirements.txt` for easy dependency management

## Dependencies

### Core
- **selenium** (4.38.0+): Browser automation
- **beautifulsoup4** (4.14.2+): HTML parsing
- **undetected-chromedriver** (3.5.5+): Bypass bot detection
- **requests** (2.32.5+): HTTP requests
- **pymongo** (4.15.4+): MongoDB interface

### Data Analysis
- **pandas** (2.3.3+): Data manipulation
- **matplotlib** (3.10.7+): Visualization
- **wordcloud** (1.9.4+): Word cloud generation

### GUI
- **PyQt5** (5.15.11+): Graphical interface

See `requirements.txt` for complete dependency list.

## Troubleshooting

### Browser Issues

If you encounter browser-related errors:

1. Ensure Chrome/Chromium is installed
2. Try setting `headless: false` in `config.json` to see what's happening
3. Check ChromeDriver compatibility with your Chrome version

### Database Connection

If MongoDB connection fails:

1. Ensure MongoDB is running: `sudo systemctl start mongodb`
2. Verify connection string in `config.json`
3. Check firewall settings if connecting to remote MongoDB

### Import Errors

If you get import errors after cloning:

1. Ensure you're in the virtual environment: `source venv/bin/activate`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.9+)

## Contributing

This is a personal project, but suggestions and bug reports are welcome! Please open an issue on GitHub.

## License

See LICENSE file for details.

## Acknowledgments

- Originally written in Python 3.9 (November 2021)
- Major refactoring completed November 2024
- Uses various open-source libraries (see requirements.txt)

## Version History

- **v4.0** (Nov 2024): Major refactoring, improved structure, comprehensive testing
- **v3.0** (Nov 2021): Original implementation with GUI and data analysis tools

---

**Note**: This tool is for personal archival purposes only. Please respect the terms of service of FanFiction.Net and Archive of Our Own. Use reasonable delays between requests to avoid overloading servers.
