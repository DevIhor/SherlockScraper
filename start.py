import os
from urllib.parse import urlparse

from scrapy.crawler import CrawlerProcess

from sherlock.spiders.code_block_spider import CodeBlockSpider

crawler_settings = {
    'LOG_LEVEL': 'INFO',
    'LOG_FILE_APPEND': False,
    'LOG_FORMAT': "%(asctime)s :%(levelname)s : %(name)s :%(message)s",
    'RETRY_ENABLED': False,
    'ROBOTSTXT_OBEY': False,
    'AJAXCRAWL_ENABLED': True,
}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="URL scraper", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-u", "--start_point", 
                        default='https://bigmir.net',
                        help="start url")
    parser.add_argument("-d", "--domain_zone", 
                        default='any',
                        help="domain zones to scrape")
    parser.add_argument('-q', '--query',
                        default='analytics.js',
                        help="query to search for on sites")
    parser.add_argument('--links_per_url',
                        type=int,
                        default=10000,
                        help="number of links to extract from web-page")
    parser.add_argument('--scraping_deep_level',
                        type=int,
                        default=1000000,
                        help="deep level of scraping urls")
    parser.add_argument('--concurrency',
                        type=int,
                        default=100,
                        help="number of concurrent requests")
    args = parser.parse_args()
    crawler_settings['CONCURRENT_REQUESTS'] = args.concurrency
    crawler_settings['LOG_FILE'] = os.path.join(
        CodeBlockSpider.LOGS_FOLDER,
        f"{str(urlparse(args.start_point).netloc).replace('.', '_')}.log"
    )

    process = CrawlerProcess(crawler_settings)
    process.crawl(
        CodeBlockSpider, 
        start_point=args.start_point, 
        domain_zone=args.domain_zone, 
        query=args.query, 
        parsed_links_limit_per_url=args.links_per_url, 
        max_url_deep_level=args.scraping_deep_level
    )
    process.start()
