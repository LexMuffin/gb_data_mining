from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
from pymongo import MongoClient
import datetime

months_to_digit = {
    'сентября': 9,
    'октября': 10,
    'ноября': 11,
    'декабря': 11,
    'января': 1,
    'февраля': 2,
    'марта': 3,
    'апреля': 4,
    'мая': 5,
    'июня': 6,
    'июля': 7,
    'августа': 8,
}

class Magnit_Parser:

    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0',
    }

    _params = {
        'geo': 'moskva',
    }

    def __init__(self, start_url):
        self.start_url = start_url
        self._url = urlparse(start_url)
        mongo_client = MongoClient('mongodb://localhost:27017')
        self.db = mongo_client['magnit_parse']

    def _get_soup(self, url:str):
        response = requests.get(url, headers=self._headers)
        return BeautifulSoup(response.text, 'lxml')

    def parse(self):
        soup = self._get_soup(self.start_url)
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})
        products = catalog.findChildren('a', attrs={'class': 'card-sale'})
        for product in products:
            if len(product.attrs.get('class')) > 2 or product.attrs.get('href')[0] != '/':
                continue
            product_url = f'{self._url.scheme}://{self._url.hostname}{product.attrs.get("href")}'
            product_soup = self._get_soup(product_url)
            product_data = self.get_product_structure(product_soup, product_url)
            self.save_to(product_data)

    def get_product_structure(self, product_soup, url):

        product_template = {
            'promo_name': ('div', 'action__name', 'text'),
            'product_name': ('div', 'action__title', 'text'),
            'old_price': ('div', 'label__price label__price_old', 'text'),
            'new_price': ('div', 'label__price label__price_new', 'text'),
            'image_url': ('img', 'action__image', 'data-src'),
            'date_from': ('div', 'action__date-label', 'text'),
            'date_to': ('div', 'action__date-label', 'text'),
        }

        product = {'url': url, }

        for key, value in product_template.items():
            try:
                if key == 'image_url':
                    product[key] = product_soup.find(value[0], attrs={'class': value[1]})[value[2]]
                elif key == 'new_price':
                    product_parent = product_soup.findChild('div', attrs={'class': 'action__footer'})
                    product[key] = getattr(product_parent.find(value[0], attrs={'class': value[1]}), value[2])
                else:
                    product[key] = getattr(product_soup.find(value[0], attrs={'class': value[1]}), value[2])
            except Exception:
                product[key] = None

        product['promo_name'] = ''.join((product['promo_name'].split('\n')))
        if product['old_price'] != None:
            product['old_price'] = int(''.join((product['old_price']).split('\n'))) / 100
        if product['new_price'] != None:
            product['new_price'] = int(''.join((product['new_price']).split('\n'))) / 100
        product['image_url'] = f'{urlparse(url).scheme}://{urlparse(url).hostname}{product["image_url"]}'
        product['date_from'] = datetime.datetime(year=2020,
                                        month=(months_to_digit[(product['date_from']).split(' ')[2]]),
                                        day=int((product['date_from']).split(' ')[1]))
        product['date_to'] = datetime.datetime(year=2020,
                                                 month=(months_to_digit[(product['date_to']).split(' ')[5]]),
                                                 day=int((product['date_to']).split(' ')[4]))


        return product

    def save_to(self, product_data: dict):
        collection = self.db['magnit_hw_2']
        collection.insert_one(product_data)
        print(1)


if __name__ == '__main__':
    url = 'https://magnit.ru/promo/?geo=moskva'
    parser = Magnit_Parser(url)
    parser.parse()