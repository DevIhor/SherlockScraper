# SherlockScraper
Scrapy bot, that scrapes urls in a deep and tries to find some file (url) by query

## SetUp
Clone project and go to bot directory
```bash
git clone https://github.com/DevIhor/SherlockScraper.git
cd SherlockScraper
```

### Basic
Create virtual environment and activate it
(you need to activate it before running scrapper)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install python requirements
```bash
pip install -r requirements.txt
```

### OR using pipenv
Install pipenv
```bash
python3.10 -m pip install -U pipenv
```

Create virtual environment and install python requirements
```bash
python3.10 -m pipenv install --deploy --dev --ignore-pipfile
```

Activate virtual environment
```bash
pipenv shell
```

## Run
Enter virtual environment
```bash
source .venv/bin/activate
```

Run scrapper
```bash
python start.py --help
```

After finish working with bot, you need to deactivate virtual environment
```bash
deactivate
```

## Description
### Flags
- `--help` - shows all information;
- `--start_point ...` - set start url to scrape;
- `--domain_zone ...` - set domain zone for urls to scrape;
- `--query ...` - set query to search for on all scraped web-pages;
- `--full_search` - enable searching for query also inside `.js` files;
- `--links_per_url ...` - set amount of urls to extract, and scrape in deep, per web-page;
- `--scraping_deep_level ...` - set the level of deep to scrape web-pages;
- `--concurrency ...` - set amount of concurrent requests;

## Example
Run unlimited scrapper 
```bash
python start.py --start_point="https://ukr.net" --domain_zone=".net" --query="analytics.js"
```

Run limited scrapper 
```bash
python start.py --start_point="https://ukr.net" --domain_zone=".net" --query="analytics.js" --links_per_url=10 --scraping_deep_level=4 --full_search
```

## Results
`output.txt` - list of scrapped urls

`query_output.txt` - list of web-pages urls that have query string

`output.csv` - list of scrapped urls + url deep level

`query_output.csv` - list of web-pages urls that have query string + url with query string