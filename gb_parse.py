import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from time import sleep
from db import SessionMaker
import models as models

class GBParse:

    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0',
    }

    _page_num = 1

    def __init__(self, start_url):
        self.start_url = start_url
        self._url = urlparse(start_url)

    def _get_soup(self, url):
        response = requests.get(url, headers=self._headers)
        return BeautifulSoup(response.text, 'lxml')

    def parse(self):

        page_num = self._page_num
        soup = self._get_soup(self.start_url)
        while soup.find('div', attrs={'class': 'post-items-wrapper'}).text:
            posts = soup.find('div', attrs={'class': 'post-items-wrapper'})
            list_posts = posts.findChildren('a', attrs={'class': 'post-item__title h3 search_text'})

            for post in list_posts:
                post_url = f'{self._url.scheme}://{self._url.hostname}{post.attrs.get("href")}'
                output_data = self.post_parse(post_url)
                sleep(1)
                self.save_to(output_data)

            self._page_num += 1
            url_page = f'{self.start_url}?page={str(page_num)}'
            soup = self._get_soup(url_page)

    def post_parse(self, post_url):

        soup_page = self._get_soup(post_url)

        post_template = {
            'post_url': post_url,
            'post_title': soup_page.find('article', attrs={'class': 'col-sm-6 col-md-8 blogpost__article-wrapper'}).h1.text,
            'date_time': soup_page.find('div', attrs={'class': 'blogpost-date-views'}).time['datetime'],
            'author': soup_page.find('div', attrs={'itemprop': 'author'}).text,
            'author_url': self.start_url[:-6] + soup_page.findChild('div', attrs={'class':'col-md-5 col-sm-12 col-lg-8 col-xs-12 padder-v'}).a['href'],
        }

        try:
            post_template['image_url'] = soup_page.find('div', attrs={'class': 'blogpost-content content_text content js-mediator-article'}).img['src']

            post_template['tags'] = soup_page.findAll('a', attrs={'class': 'small'})

            for tag in post_template['tags']:
                tag_name = getattr(tag, 'text')
                tag_url = f'{self._url.scheme}://{self._url.hostname}{tag.attrs["href"]}'

        except Exception:

            post_template['image_url'] = None

        return post_template

    @staticmethod
    def save_to(output_data):

        db = SessionMaker()

        writer = models.Writer(name=output_data['author'], url=output_data['author_url'])
        db_writer_check = db.query(models.Writer).filter(models.Writer.url == writer.url).first()
        if db_writer_check:
            writer = db_writer_check
        db.add(writer)

        post = models.Post(header=output_data['post_title'], post_date=output_data['date_time'],
                           url=output_data['post_url'], img_url=output_data['img_url'], writer=writer)
        db.add(post)

        for element in output_data['tags']:
            tag = models.Tag(name=element[0], url=element[1], posts=[post])
            db_tag_check = db.query(models.Tag).filter(models.Tag.url == tag.url).first()
            if db_tag_check:
                tag = db_tag_check
            db.add(tag)
            post.tag.append(tag)

        db.commit()
        db.close()


if __name__ == '__main__':
    url = 'https://geekbrains.ru/posts'
    parser = GBParse(url)
    parser.parse()