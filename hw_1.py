import json
import requests
import time
url = 'https://5ka.ru/api/v2/special_offers/'
cat_url = 'https://5ka.ru/api/v2/categories/'

class Parser5ka:

    __headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:81.0) Gecko/20100101 Firefox/81.0',
    }
    __params = {
        'records_per_page': 50,
        'categories': '',
    }
    __to_replace = (',', '-', '/', '\\', '.', '"', "'", '*', '#',)
    categories = []

    def __init__(self, start_url):
        self.start_url = start_url

    def download_category(self, url=None):
        if not url:
            url = cat_url
        response = requests.get(url, headers=self.__headers)
        self.categories = response.json()

    def replace_to_name(self, name):
        for itm in self.__to_replace:
            name = name.replace(itm, '')
        return ' '.join(name.split()).lower()

    def save_to_json_file(self):
        params = self.__params

        while url:
            for category in self.categories:
                params['categories'] = category['parent_group_code']
                response = requests.get(url, headers=self.__headers, params=params)
                data = response.json()
                with open(f'products/{self.replace_to_name(category["parent_group_name"])}.json', 'w', encoding='UTF-8') as file:
                    json.dump(data, file, ensure_ascii=False)
                params = {}
                time.sleep(0.5)

if __name__ == '__main__':
    parser = Parser5ka(url)
    parser.download_category()
    parser.save_to_json_file()