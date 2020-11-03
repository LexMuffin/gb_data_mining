from itemloaders.processors import TakeFirst, MapCompose
from scrapy.loader import ItemLoader
from scrapy import Selector
from .items import HHCompanyItem, HHVacancyItem

def eraser_symbols(itm):
    result = itm.replace('\xa0', '')
    return result


def list_concat(itm):
    result = ' '.join(itm)
    return eraser_symbols(result)


def create_hh_company_url(itm):
    result = f'https://hh.ru{itm[0]}'
    return result


class HHVacancyLoader(ItemLoader):
    default_item_class = HHVacancyItem

    url_out = TakeFirst()
    title_out = TakeFirst()
    salary_in = list_concat
    salary_out = TakeFirst()
    description_in = list_concat
    description_out = TakeFirst()
    skills_out = MapCompose(eraser_symbols)
    hh_company_url_in = create_hh_company_url
    hh_company_url_out = TakeFirst()

class HHCompanyLoader(ItemLoader):
    default_item_class = HHCompanyItem

    url_out = TakeFirst()
    company_name_in = list_concat
    company_name_out = TakeFirst()
    company_url_out = TakeFirst()
    field_of_activities_out = MapCompose(eraser_symbols)
    desc_company_in = list_concat
    desc_company_out = TakeFirst()