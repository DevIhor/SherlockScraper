import csv
import logging
import os.path
from collections.abc import Generator
from typing import Any

import scrapy

from urllib.parse import urljoin, urlparse

from scrapy.http import HtmlResponse
from scrapy.utils.python import to_bytes
from scrapy.spiders import CrawlSpider
# from scrapy.linkextractors import LinkExtractor

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.support.wait import WebDriverWait

from twisted.internet.error import DNSLookupError

CUSTOM_PRINT_LOG_LEVEL = 60
logging.addLevelName(CUSTOM_PRINT_LOG_LEVEL, 'CUSTOM_PRINT_LOG_LEVEL')

console = logging.StreamHandler()
console.setLevel(CUSTOM_PRINT_LOG_LEVEL)
logging.getLogger('').addHandler(console)


class CodeBlockSpider(CrawlSpider):
    name = 'code_block_spider'
    LOGS_FOLDER = '.logs'
    RESULTS_FOLDER = 'results'
    retry_enabled = False

    # Data files
    SCRAPED_URLS_FILEPATH = os.path.join(RESULTS_FOLDER, "scraped_urls.csv")
    SCRAPED_URLS_FILEPATH_TXT = os.path.join(RESULTS_FOLDER, "scraped_urls.txt")
    RESULT_FILEPATH = os.path.join(RESULTS_FOLDER, "result.csv")
    RESULT_FILEPATH_TXT = os.path.join(RESULTS_FOLDER, "result.txt")

    def __init__(
            self,
            start_point: str,
            domain_zone: str,
            query: str,
            parsed_links_limit_per_url: int,
            max_url_deep_level: int,
            full_search: bool,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.start_urls = [start_point]
        self.domain_zone = "" if domain_zone.lower() in ("any", "*") else domain_zone
        self.query = query
        self.PARSED_LINKS_LIMIT_PER_URL = parsed_links_limit_per_url
        self.MAXIMUM_URL_DEEP_LEVEL = max_url_deep_level
        self.enable_full_search = full_search
        self.processed_links = []

        self.selenium_driver = None
        self.configure_selenium_driver()

    def configure_selenium_driver(
            self
    ) -> None:
        """Configure Selenium driver"""
        import browsers

        available_browsers = {item['browser_type'] for item in browsers.browsers()}

        if {"chrome", "chromium"} & available_browsers:
            browser_options = ChromeOptions()
            browser_options.add_argument('--headless')
            browser_options.add_argument('--ignore-certificate-errors')
            browser_options.add_argument('--incognito')
            self.selenium_driver = webdriver.Chrome(options=browser_options)
        elif {"firefox"} & available_browsers:
            browser_options = FirefoxOptions()
            browser_options.add_argument('-headless')
            self.selenium_driver = webdriver.Firefox(options=browser_options)
        elif {"msedge"} & available_browsers:
            browser_options = EdgeOptions()
            browser_options.add_argument('--headless')
            browser_options.add_argument('--ignore-certificate-errors')
            browser_options.add_argument('--incognito')
            self.selenium_driver = webdriver.Edge(options=browser_options)
        elif {"safari"} & available_browsers:
            browser_options = SafariOptions()
            self.selenium_driver = webdriver.Safari(options=browser_options)

        self.selenium_driver.set_page_load_timeout(10)

    def get_start_url_repr(
            self
    ) -> str:
        """Get the start URL representation"""
        return str(urlparse(self.start_urls[0]).netloc).replace(".", "_")

    @staticmethod
    def prepare_env() -> None:
        """Prepare the environment for the spider"""

        # Create .logs folder if missing
        if not os.path.exists(CodeBlockSpider.LOGS_FOLDER):
            os.makedirs(CodeBlockSpider.LOGS_FOLDER)

        # Create results folder if missing
        if not os.path.exists(CodeBlockSpider.RESULTS_FOLDER):
            os.makedirs(CodeBlockSpider.RESULTS_FOLDER)

        # Remove old data files
        if os.path.isfile(CodeBlockSpider.SCRAPED_URLS_FILEPATH):
            os.remove(CodeBlockSpider.SCRAPED_URLS_FILEPATH)
        if os.path.isfile(CodeBlockSpider.SCRAPED_URLS_FILEPATH_TXT):
            os.remove(CodeBlockSpider.SCRAPED_URLS_FILEPATH_TXT)
        if os.path.isfile(CodeBlockSpider.RESULT_FILEPATH):
            os.remove(CodeBlockSpider.RESULT_FILEPATH)
        if os.path.isfile(CodeBlockSpider.RESULT_FILEPATH_TXT):
            os.remove(CodeBlockSpider.RESULT_FILEPATH_TXT)

        # Add headers to csv files
        with open(CodeBlockSpider.SCRAPED_URLS_FILEPATH, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["URL", "Deep Level"])
        with open(CodeBlockSpider.RESULT_FILEPATH, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Base URL", "Search Query"])

    def start_requests(
            self
    ) -> Generator[scrapy.Request, None, None]:
        """Start the spider by visiting the start URL"""
        yield scrapy.Request(
            url=self.start_urls[0],
            callback=self.parse,
            errback=self.parse_error,
            cb_kwargs={'url_deep_level': 0}
        )

    def close(
            self,
            reason: Any
    ) -> None:
        """Close the spider"""
        self.selenium_driver.close()

    def parse_error(
            self,
            failure
    ) -> None:
        """Check for timeout errors and dns lookup errors.
        If any of these errors occur, the spider will retry the request.
        """
        if failure.check(TimeoutException) or failure.check(DNSLookupError):
            logging.log(CUSTOM_PRINT_LOG_LEVEL, repr(failure))

    def parse(self, response, *args, **kwargs):
        logging.log(logging.INFO, f"Started processing {response.url}")

        url_deep_level = kwargs.get('url_deep_level', 0)

        # Extract SPA content
        try:
            self.selenium_driver.get(response.url)
            WebDriverWait(self.selenium_driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            return
        body = to_bytes(self.selenium_driver.page_source)
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
        result_links = set()

        # Write the result URL and it's searched term url
        with open(self.RESULT_FILEPATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            if self.enable_full_search and self.query in self.selenium_driver.page_source:
                writer.writerow([response.url, self.query])
            else:
                result_links = {link for link in links if self.query in link}
                for link in result_links:
                    writer.writerow([response.url, link])

        # Write the result searched URL
        with open(self.RESULT_FILEPATH_TXT, mode='a', newline='') as file:
            if (self.enable_full_search and self.query in self.selenium_driver.page_source) or result_links:
                file.write(f"{response.url}\n")

        links = [link for link in links if link.startswith("http")]

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
        with open(self.SCRAPED_URLS_FILEPATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([response.url, url_deep_level])

        # Write the current URL to the output txt file
        with open(self.SCRAPED_URLS_FILEPATH_TXT, mode='a', newline='') as file:
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
