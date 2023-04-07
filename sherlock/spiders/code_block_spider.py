import csv
import logging
import scrapy

from urllib.parse import urljoin, urlparse

from scrapy.http import HtmlResponse
from scrapy.utils.python import to_bytes
from scrapy.spiders import CrawlSpider
# from scrapy.linkextractors import LinkExtractor
from scrapy.utils.log import configure_logging

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait

from twisted.internet.error import DNSLookupError

CUSTOM_PRINT_LOG_LEVEL = 60
logging.addLevelName(CUSTOM_PRINT_LOG_LEVEL, 'CUSTOM_PRINT_LOG_LEVEL')

logging.getLogger('selenium').setLevel(CUSTOM_PRINT_LOG_LEVEL)


class CodeBlockSpider(CrawlSpider):
    name = 'code_block_spider'
    retry_enabled = False

    def __init__(self, start_point, domain_zone, query, parsed_links_limit_per_url, max_url_deep_level):
        configure_logging(install_root_handler=False)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--incognito')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(10)

        self.start_urls = [start_point]
        self.domain_zone = "" if domain_zone.lower() in ("any", "*") else domain_zone
        self.query = query
        self.PARSED_LINKS_LIMIT_PER_URL = parsed_links_limit_per_url
        self.MAXIMUM_URL_DEEP_LEVEL = max_url_deep_level

        # Prepare data files
        self.output_filename = "output.csv"
        self.output_filename_txt = "output.txt"
        self.result_filename = "query_output.csv"
        self.result_filename_txt = "query_output.txt"

    def close(self, reason):
        self.driver.close()

    def parse_error(self, failure):
        if failure.check(DNSLookupError):
            return

    def parse(self, response, url_deep_level):
        try:
            self.driver.get(response.url)
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            return
        body = to_bytes(self.driver.page_source)
        selenium_response = HtmlResponse(response.url, body=body, encoding='utf-8')

        if 0 < self.MAXIMUM_URL_DEEP_LEVEL < url_deep_level:
            return
        
        # Extract all links from the response
        links = selenium_response.css('a::attr(href)').getall() \
            + selenium_response.css('link[rel="stylesheet"]::attr(href)').getall() \
            + selenium_response.css('script::attr(src)').getall() \
            + selenium_response.css('link[rel="alternate"][hreflang="en"]::attr(href)').getall()

        # Extract the URLs from the og:url meta tag
        og_url = selenium_response.css('meta[property="og:url"]::attr(content)').get()

        # Add the meta tag URLs to the list of links
        if og_url:
            links.append(og_url)

        # Preprocess links (convert to absolute url and remove all protocols except http/https)
        links = [urljoin(response.url, link) for link in links]
        links = [link for link in links if link.startswith("http")]

        result_links = []

        # Write the result URL and it's searched term url
        with open(self.result_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            for link in links:
                if self.query in link and link not in result_links:
                    result_links.append(link)
                    writer.writerow([response.url, link])

        # Write the result searched URL
        with open(self.result_filename_txt, mode='a', newline='') as file:
            if result_links:
                file.write(f"{response.url}\n")

        # Filter out already processed links to prevent infinite loops from all sources
        new_links = [link for link in links
                     if urlparse(link).netloc.endswith(self.domain_zone) and (link not in self.processed_links)]

        # or Filter out from the body of response
        # new_links = [link.url for link in LinkExtractor().extract_links(response)
        #              if (self.domain_zone in link.url) and (link.url not in self.processed_links)]

        if self.PARSED_LINKS_LIMIT_PER_URL > 0:
            new_links = new_links[:self.PARSED_LINKS_LIMIT_PER_URL]

        self.processed_links.append(response.url)

        # Write the current URL and deep level to the output file
        with open(self.output_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([response.url, url_deep_level])

        # Write the current URL to the output txt file
        with open(self.output_filename_txt, mode='a', newline='') as file:
            file.write(f"{response.url}\n")

        # Add new links to the queue
        if self.MAXIMUM_URL_DEEP_LEVEL > 0 and url_deep_level + 1 <= self.MAXIMUM_URL_DEEP_LEVEL:
            for link in new_links:
                self.crawler.engine.crawl(
                    scrapy.Request(
                        url=link, 
                        callback=self.parse, 
                        errback=self.parse_error,
                        cb_kwargs={'url_deep_level': url_deep_level + 1}
                    )
                )

        logging.log(CUSTOM_PRINT_LOG_LEVEL, 
                    f"Processed - {len(self.processed_links)} links. "
                    f"In Queue - {len(self.crawler.engine.slot.scheduler)} links. "
                    f"Current url deep level - {url_deep_level}. ")

    def start_requests(self):
        self.processed_links = []

        # Start the spider by visiting the start URL
        yield scrapy.Request(
            url=self.start_urls[0], 
            callback=self.parse, 
            errback=self.parse_error,
            cb_kwargs={'url_deep_level': 0}
        )

