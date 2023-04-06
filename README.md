# SherlockScraper
Scrapy bot, that scrapes urls in a deep and tries to find some file (url) by query

## SetUp

Clone project and go to bot directory
```bash
git clone https://github.com/DevIhor/SherlockScraper.git
cd SherlockScraper
```

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

## Run

Enter venv
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

## Example

Run unlimited scrapper 
```bash
python start.py --start_point="https://ukr.net" --domain_zone=".net" --query="analytics.js"
```

Run limited scrapper 
```bash
python start.py --start_point="https://ukr.net" --domain_zone=".net" --query="analytics.js" --links_per_url=10 --scraping_deep_level=4
```

## Results

`output.txt` - list of scrapped urls

`query_output.txt` - list of web-pages urls that have query string

`output.csv` - list of scrapped urls + url deep level

`query_output.csv` - list of web-pages urls that have query string + url with query string