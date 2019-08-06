import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re
import asyncio
import concurrent.futures
import time
import codecs
import abc


class Scraper(abc.ABC):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.titles = []
        self.descriptions = []
        self.links = []

    @staticmethod
    def get_response(url):

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.01)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session.get(url)

    @staticmethod
    async def _get_responses(links):
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=128)

        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor,
                Scraper.get_response,
                url
            )
            for url in links
        ]
        list_of_responses = []
        print(str(len(links)) + ' responses to get')

        for response in await asyncio.gather(*futures):
            list_of_responses.append(response)

        return list_of_responses

    @staticmethod
    def get_responses(links):
        loop = asyncio.get_event_loop()
        start = time.time()
        responses = loop.run_until_complete(Scraper._get_responses(links))
        end = time.time()
        print('time getting responses: %.2f' % (end - start) + 's')

        return responses

    def scrape_all(self, responses, urls):
        new_urls = []
        start = time.time()
        print('scraping from %d links for a first batch' % len(responses))
        for response, url in zip(responses, urls):
            temp_list = self.scrape(response, url=url, more_pages=True)

            for link in temp_list:
                new_urls.append(link)
        end = time.time()
        print('scraping first batch time: %.2f' % (end - start) + 's\n')

        new_responses = Scraper.get_responses(new_urls)
        print('scraping %d links for a second batch...' % len(new_responses))
        start = time.time()

        for response, url in zip(new_responses, new_urls):
            self.scrape(response)

        end = time.time()
        print('scraping second batch time: %.2f' % (end - start) + 's\n')

    def clear(self):
        self.titles.clear()
        self.descriptions.clear()
        self.links.clear()

    def write_to_file(self, filename, append=False):
        if append:
            file = codecs.open(filename, 'a+', encoding='latin-1')
        else:
            file = codecs.open(filename, 'w+', encoding='latin-1')

        array = []
        for title, description, link in zip(self.titles, self.descriptions, self.links):
            array.append((title, description, link))
        array.sort(key=lambda offer: offer[0])
        self.titles = []
        self.descriptions = []
        self.links = []
        for offer in array:
            self.titles.append(offer[0])
            self.descriptions.append(offer[1])
            self.links.append(offer[2])

        for title, description, link in zip(self.titles, self.descriptions, self.links):
            file.write(title + '|' + description + '|' + link + '\n')

        file.close()

    @abc.abstractmethod
    def scrape(self, response, url=None, more_pages=False):
        pass

    @abc.abstractmethod
    def get_urls(self, tag_list, town, intern=False):
        pass


class PracujplScraper(Scraper):

    def scrape(self, response, url=None, more_pages=False):

        soup = BeautifulSoup(response.text, 'lxml')

        offers = soup.find_all(type='application/ld+json')

        for offer in offers:
            offer = offer.get_text()
            offer = offer[: offer.find('...')]
            offer = offer.replace('{"@context":"http://schema.org/","@type":"JobPosting","title":', '') \
                .replace('|', '/')
            offer = offer[offer.find('"'):].replace('\n', '').replace('"', '')
            title = offer[: offer.find(',description:')]
            description = offer[offer.find(',description:') + len(',description: '):]

            self.titles.append(title)
            self.descriptions.append(description)

        scripts = soup.findAll('script')
        promoted_offers = soup.find(class_='results results--promoted')
        promoted_count = 0
        if promoted_offers:
            promoted_count = len(promoted_offers.findAll(class_="offer__click"))

        for script in scripts:
            script = str(script)
            indices = [index.end() for index in re.finditer('"offerUrl":', script)]
            if len(indices) == 0:
                continue

            if promoted_count > 0:
                temp_list = indices[len(indices) - promoted_count:]
                temp_list.extend(indices[: len(indices) - promoted_count])
                indices = temp_list
                if promoted_count > 1:
                    temp = indices[0]
                    indices[0] = indices[1]
                    indices[1] = temp

            for index in indices:
                temp_script = script[index:]
                url_position = re.search('"(.*?)"', temp_script)

                temp_link = temp_script[1: url_position.end()-1]
                link = 'https://www.pracuj.pl' + temp_link
                self.links.append(link)

        if more_pages and url:
            number_of_pages = soup.find(class_="pagination_label--max")
            if not number_of_pages:
                return []

            number_of_pages = number_of_pages.get_text().replace('/ ', '')
            number_of_pages = int(number_of_pages)

            list_of_urls = []
            count = 2
            while count <= number_of_pages:
                list_of_urls.append((url + 'pn=' + str(count) + '&'))
                count += 1
            return list_of_urls

    def get_urls(self, tag_list, town, intern=False):
        list_of_urls = []

        for tag in tag_list:
            list_of_urls.append(PracujplScraper.make_link(tag, town, intern_only=intern))

        list_of_urls = [url.replace(' ', '%20') for url in list_of_urls]
        return list_of_urls

    @staticmethod
    def make_link(tag, town, intern_only=True):
        link = 'https://www.pracuj.pl/praca/'
        # between_tags = '-x44-'
        end_of_tags = ';kw/'
        end_of_towns = ';wp?'
        intern_end = 'et=1&'

        link += tag.name

        link += end_of_tags
        link += town
        link += end_of_towns
        if intern_only:
            link += intern_end

        return link
