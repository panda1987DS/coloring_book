import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import logging.config
from dataclasses import dataclass, field
import yaml
from marshmallow_dataclass import class_schema
from marshmallow import ValidationError

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)
DEFAULT_PATH_TO_CONFIG = 'scraper_config.yaml'


@dataclass()
class ScraperParams:
    url: str
    path_l1: str
    class_l1: str
    class_l2: str
    class_l3: str
    group_name_l1: str
    save_to_file: bool
    filename: str
    dir_to_pict:str


ScraperParamsSchema = class_schema(ScraperParams)


def read_scraper_params(path: str) -> ScraperParams:
    try:
        with open(path, "r") as input_stream:
            schema = ScraperParamsSchema()
            return schema.load(yaml.safe_load(input_stream))
    except FileNotFoundError:
        logger.error(f"Can't load training parameters. File not found:{path}")
    except ValidationError as err:
        logger.error(f"Can't load training parameters. {err}")


def scraper(scraper_params):
    response = requests.get(scraper_params.url + scraper_params.path_l1)
    soup = BeautifulSoup(response.text, 'lxml')
    quotes = soup.find_all('ul', class_=scraper_params.class_l1)
    result = []
    for q in quotes:
        for content in q.contents:
            result = result + (
                mini_pict_scraper(q.previous, content.contents[0].text, content.contents[0].attrs['href'],
                                  scraper_params))
    return result


def mini_pict_scraper(group_name, subgroup_name, url, scraper_params):
    try:
        response = requests.get(url)
    except requests.exceptions.MissingSchema:
        response = requests.get(scraper_params.url[:-1] + url)
    soup = BeautifulSoup(response.text, 'lxml')
    quotes = soup.find_all('ul', class_=scraper_params.class_l2)
    result = []
    for content in quotes[0].contents:
        url_pict = get_url_pict(content.contents[0].attrs['href'], scraper_params)
        if not url_pict is None:
            result.append([group_name, subgroup_name, content.contents[0].text,
                           scraper_params.url[:-1]  + url_pict])
    return result


def get_url_pict(url, scraper_params):
    try:
        response = requests.get(url)
    except requests.exceptions.MissingSchema:
        response = requests.get(scraper_params.url[:-1] + url)
    soup = BeautifulSoup(response.text, 'lxml')
    quotes = soup.find_all('a', class_=scraper_params.class_l3)
    # quotes = soup.find_all('a',attrs={'data-fancybox': "images"})
    if len(quotes) > 0:
        return quotes[0].attrs['href']
    else:
        logger.warning("Can't load "+url)


def save_pict(col, scraper_params):
    filename = scraper_params.dir_to_pict + col['name'][col['name'].rfind('/')+1:] + ".jpg"
    img = col['href'].replace('/raskraski/barbie/',scraper_params.url)
    if os.path.exists(filename):
        logger.warning(f'{filename} already exists')
    else:
        # session = get_session()
        try:
            p = requests.get(img, timeout=5)
        except:
            p = requests.get(scraper_params.url[:-1] + img, timeout=5)
        try:
            out = open(filename, "wb")
            out.write(p.content)
            out.close()
            logger.info(f"Load {filename}")
        except:
            logger.warning(f"Can't load {filename}")


# def get_session():
#     # создать HTTP‑сеанс
#     session = requests.Session()
#     # выбираем один случайный прокси
#     proxy = PROXIES.sample().values[0]
#     session.proxies = {"http": proxy, "https": proxy}
#     return session

# Press the green button in the gutter to run the script.
def main():
    scraper_params = read_scraper_params(DEFAULT_PATH_TO_CONFIG)
    if scraper_params is None:
        logger.error(f'Can not load params from file {DEFAULT_PATH_TO_CONFIG}')
        return 0

    if scraper_params.save_to_file:
        result = scraper(scraper_params)
        # print(result)
        df = pd.DataFrame(result)
        df.columns = ["group","subgroup","name","href"]
        df.to_csv(scraper_params.filename)
    else:
        df = pd.read_csv(scraper_params.filename, index_col=0, )
        df.apply(save_pict, scraper_params=scraper_params, axis=1)


if __name__ == '__main__':
    main()

    # with open('important', 'wb') as file:
    #     dump(result,file)
    # t = mini_pict_scraper('https://deti-online.com/raskraski/aladdin-2019/')
    # print(t)
    # save_pict('https://deti-online.com/img/raskraski/aladdin-2019/aladdin-i-zhasmin.jpg')
    # get_url_pict('https://deti-online.com/raskraski/aladdin-2019/aladdin-i-zhasmin/')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
