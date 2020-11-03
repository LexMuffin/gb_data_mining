import scrapy
from ..loaders import HHVacancyLoader, HHCompanyLoader

class HHSpider(scrapy.Spider):
    name = 'hh'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    xpath = {
        'vacancy': '//div[@class="vacancy-serp"]//a[contains(@class, "HH-LinkModifier")]/@href',
        'pagination': '//div[@data-qa="pager-block"]//a[contains(@class, "HH-pager-Controls-Next")]/@href',
        'company': '//div[@class="vacancy-company-name-wrapper"]/a/@href',
        'company_vacancies': '//div[@class="employer-sidebar-content"]/div[@class="employer-sidebar-block"]/a/@href',
    }

    def parse(self, response, **kwargs):

        for url in response.xpath(self.xpath['pagination']):
            yield response.follow(url, callback=self.parse)

        for url in response.xpath(self.xpath['vacancy']):
            yield response.follow(url, callback=self.vacancy_parse)

    def vacancy_parse(self, response, **kwargs):
        loader = HHVacancyLoader(response=response)

        loader.add_value('url', response.url)
        loader.add_xpath('title', '//div[@class="vacancy-title"]//h1/text()')
        loader.add_xpath('salary', '//div[@class="vacancy-title"]//p[@class="vacancy-salary"]//text()')
        loader.add_xpath('description', '//div[@class="vacancy-section"]/div[contains(@class, "g-user-content")]//text()')
        loader.add_xpath('skills', '//div[contains(@class, "bloko-tag-list")]//text()')
        loader.add_xpath('hh_company_url', self.xpath['company'])
        yield loader.load_item()

        for url in response.xpath(self.xpath['company']):
            yield response.follow(url, callback=self.company_parse)

    def company_parse(self, response, **kwargs):
        loader = HHCompanyLoader(response=response)

        loader.add_value('url', response.url)
        loader.add_xpath('company_name', '//div[@class="company-header"]//span/text()')
        loader.add_xpath('company_url', '//div[contains(@class, "employer-sidebar-content")]/a/@href')
        loader.add_xpath('field_of_activities', '//div[@class="employer-sidebar-block"]//p/text()')
        loader.add_xpath('desc_company', '//div[@class="g-user-content"]//p/text()')
        yield loader.load_item()

        for url in response.xpath(self.xpath['company_vacancies']):
            yield response.follow(url, callback=self.parse)