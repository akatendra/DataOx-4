import aiohttp
import asyncio
import time
from datetime import datetime
import scraper
import database
import logging.config

headers = {
    "user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}

"""fix yelling at me error"""
# Monkey Patch:
# https://pythonalgos.com/runtimeerror-event-loop-is-closed-asyncio-fix/
from functools import wraps

from asyncio.proactor_events import _ProactorBasePipeTransport


def silence_event_loop_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except RuntimeError as e:
            if str(e) != 'Event loop is closed':
                raise

    return wrapper


_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(
    _ProactorBasePipeTransport.__del__)
"""fix yelling at me error end"""


def spent_time():
    global start_time
    sec_all = time.time() - start_time
    if sec_all > 60:
        minutes = sec_all // 60
        sec = sec_all % 60
        time_str = f'| {int(minutes)} min {round(sec, 1)} sec'
    else:
        time_str = f'| {round(sec_all, 1)} sec'
    start_time = time.time()
    return time_str


async def fetch(session, page_number, url):
    try:
        async with session.get(url) as response:
            logger.debug(f'page_number: {page_number} | url: {url}')
            logger.debug(f'Status: {response.status}')
            logger.debug(
                f'Content-type: {response.headers["content-type"]}')
            current_url = response.url
            logger.debug(f'current_url: {current_url}')
            html = await response.text()
            return page_number, html
    except Exception as error:
        logger.debug(f'{str(error)}')


async def main():
    global urls
    tasks = []

    # Start sessions
    async with aiohttp.ClientSession(headers=headers) as session:
        for url in urls:
            tasks.append(fetch(session, url[0], url[1]))
        htmls = await asyncio.gather(*tasks)
    return htmls


async def find_pagination_end(start_page, session):
    logger.debug(f'Hi from find_pagination_end func!')
    page = start_page
    new_page = page + 1
    processed_url = make_url_for_page_number(start_page)
    while new_page > page:
        page = new_page
        logger.debug(
            f'page: {page} | new_page: {new_page} | processed_url: {processed_url}')
        result = await fetch(session, page, processed_url)
        html = result[1]
        new_page = scraper.parse_pages_count(html)
        logger.debug(f'new_page: {new_page}')
        processed_url = make_url_for_page_number(new_page)
        logger.debug(f'processed_url: {processed_url}')
    return page


async def find_near_to_end_page_number(session):
    logger.debug(f'Hi from find_near_to_end_page_number func!')
    page_number = 999
    page_url = make_url_for_page_number(page_number)
    async with session.get(page_url) as response:
        logger.debug(
            f'page_number: {page_number} | page_url: {page_url}')
        logger.debug(f'Status: {response.status}')
        logger.debug(
            f'Content-type: {response.headers["content-type"]}')
        current_url = response.url
        logger.debug(f'current_url: {current_url}')
        url_str = str(current_url)
        url_list = url_str.split('/')
        logger.debug(f'url_list: {url_list}')
        for element in url_list:
            if 'page-' in element:
                page = int(element.replace('page-', ''))
        logger.debug(f'page: {page}')
    return page


async def find_pages_count():
    async with aiohttp.ClientSession(headers=headers) as session:
        logger.debug(f'Hi from find_pages_count!')
        page = await find_near_to_end_page_number(session)
        page = await find_pagination_end(page, session)
    return page


def make_url_for_page_number(page_number):
    if page_number == 1:
        page_url = url1 + url2
    else:
        page_url = f'{url1}page-{page_number}/{url2}'
    return page_url


if __name__ == "__main__":
    # Set up logging
    logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
    logger = logging.getLogger(__name__)

    # Set the variables values
    time_begin = start_time = time.time()
    url = 'https://www.kijiji.ca/b-apartments-condos/city-of-toronto/c37l1700273'
    url1 = 'https://www.kijiji.ca/b-apartments-condos/city-of-toronto/'
    url2 = 'c37l1700273'
    output_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # End of variables values setting

    logger.info('Start...')

    # Get pagination last page
    max_page = asyncio.run(find_pages_count())
    logger.debug(f'Found max_page: {max_page}')

    # Getting urls
    urls = []
    for page_number in range(1, max_page + 1):
        logger.debug(f'Take in work page: {page_number}')
        if page_number == 1:
            page_url = url1 + url2
        else:
            page_url = f'{url1}page-{page_number}/{url2}'
        logger.debug(f'page_url: {page_url}')
        urls.append((page_number, page_url))
    logger.debug(f'urls count: {len(urls)}')

    htmls = asyncio.run(main())

    # Storing the raw HTML data.
    for html in htmls:
        if html is not None:
            output_data = scraper.parse_html(html)
            database.write_to_db(database.metadata, database.engine,
                                 output_data)
        else:
            continue

    time_end = time.time()
    elapsed_time = time_end - time_begin
    if elapsed_time > 60:
        elapsed_minutes = elapsed_time // 60
        elapsed_sec = elapsed_time % 60
        elapsed_time_str = f'| {int(elapsed_minutes)} min {round(elapsed_sec, 1)} sec'
    else:
        elapsed_time_str = f'| {round(elapsed_time, 1)} sec'
    logger.info(
        f'Elapsed run time: {elapsed_time_str} seconds | Page_counter: {scraper.page_counter} | htmls count: {len(htmls)} | New items: {scraper.counter} | feature: {scraper.feature_counter} | regular: {scraper.regular_counter} | feature + regular: {scraper.feature_counter + scraper.regular_counter}')

