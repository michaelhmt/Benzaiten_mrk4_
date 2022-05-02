DATABASE_ADRESS = 'mongodb+srv://{userName}:{password}@cluster0.wn9uy.mongodb.net/myFirstDatabase?retryWrites=true&w=majority'

HEADER_ = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.116 Safari/537.36'}
STORY_PAGE_CONSTANT = 'https://archiveofourown.org{url}?view_adult=true">Proceed'
STORY_INDEX_CONSTANT = "https://archiveofourown.org{url}/navigate"
SEARCHPAGE_CONSTANT = 'https://archiveofourown.org/tags/{Fandom_Source}/works?page={}'

VIEW_ALL_CONSTANT ="https://archiveofourown.org{url}?view_adult=true&view_full_work=true" #MIGHT THROW AN ERROR WITH MATURE CONTENT

COOKIES_CONSTANT = {'domain': 'archiveofourown.org', 'httpOnly': False, 'name': 'view_adult', 'path': '/', 'secure': False, 'value': 'true'}

DRIVER_PATH = 'E:\\Python\\Benzaiten_mrk4\\chromedriver.exe' #the path where you have "chromedriver" file.
INGESTED_LOG = 'E:\\Python\\Benzaiten_mrk4\\venv\\Benzaiten_Common\\Ingested_Log_{Fandom_Name}.json'
