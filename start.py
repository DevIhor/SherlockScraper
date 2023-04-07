import csv
import os

from scrapy.crawler import CrawlerProcess

from sherlock.spiders.code_block_spider import CodeBlockSpider, LOGS_FOLDER, SELENIUM_LOGGER_FILENAME

crawler_settings = {
    'LOG_LEVEL': 'CUSTOM_PRINT_LOG_LEVEL',
    'RETRY_ENABLED': False,
    'AJAXCRAWL_ENABLED': True,
}


def prepare_data_files():
    output_filename = "output.csv"
    output_filename_txt = "output.txt"
    result_filename = "query_output.csv"
    result_filename_txt = "query_output.txt"

    # Remove old data files
    if os.path.isfile(output_filename):
        os.remove(output_filename)
    if os.path.isfile(output_filename_txt):
        os.remove(output_filename_txt)
    if os.path.isfile(result_filename):
        os.remove(result_filename)
    if os.path.isfile(result_filename_txt):
        os.remove(result_filename_txt)

    # Clean logs file
    if not os.path.exists(LOGS_FOLDER):
        os.makedirs(LOGS_FOLDER)
    if os.path.getsize(CodeBlockSpider.LOGS_FILENAME) < 5 * 1024 * 1024:
        os.remove(CodeBlockSpider.LOGS_FILENAME)
    if os.path.getsize(SELENIUM_LOGGER_FILENAME) < 5 * 1024 * 1024:
        os.remove(SELENIUM_LOGGER_FILENAME)
    
    # Add headers to csv files
    with open(output_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Deep Level"])
    with open(result_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Base URL", "Search Query"])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="URL scraper", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-u", "--start_point", 
                        default='https://bigmir.net',
                        help="start url")
    parser.add_argument("-d", "--domain_zone", 
                        default='any',
                        help="domain zones to scrape")
    parser.add_argument("-q", "--query", 
                        default='analytics.js',
                        help="query to search for on sites")
    parser.add_argument("--links_per_url",
                        type=int,
                        default=10000,
                        help="number of links to extract from web-page")
    parser.add_argument("--scraping_deep_level",
                        type=int,
                        default=1000000,
                        help="deep level of scraping urls")
    parser.add_argument("--concurrency",
                        type=int,
                        default=100,
                        help="number of concurrent requests")
    args = parser.parse_args()
    crawler_settings["CONCURRENT_REQUESTS"] = args.concurrency

    prepare_data_files()

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
