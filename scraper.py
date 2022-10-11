from datetime import timedelta, datetime
from bs4 import BeautifulSoup
import logging
import logging.config

import database

# Global variables
counter = 0
page_counter = 0
feature_counter = 0
regular_counter = 0
BASE = 'https://www.kijiji.ca'
# End Global variables

# Set up logging
logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
# Remove from output to the log information from Firefox, where a lot
# of space is taken up by the server response with the html content
# of the entire page. Outputting this information to the log greatly increases
# the size of the log file.
logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(
    logging.WARNING)


def splitlines(string):
    line_list = string.splitlines()
    logger.debug(f'line_list: {line_list}')
    new_string = ''
    for line in line_list:
        new_string += line.strip() + ' '
    return new_string


def convert_date(date):
    if 'sec' in date:
        date_list = date.split()
        sec_str = date_list[1]
        if sec_str.isdigit():
            sec = int(date_list[1])
            converted_date = datetime.now() - timedelta(seconds=sec)
        else:
            converted_date = None
    elif 'min' in date:
        date_list = date.split()
        minutes_str = date_list[1]
        if minutes_str.isdigit():
            minutes = int(date_list[1])
            converted_date = datetime.now() - timedelta(minutes=minutes)
        else:
            converted_date = None
    elif 'hour' in date:
        date_list = date.split()
        hours_str = date_list[1]
        if hours_str.isdigit():
            hours = int(date_list[1])
            converted_date = datetime.now() - timedelta(hours=hours)
        else:
            converted_date = None
    elif 'Yesterday' in date:
        converted_date = datetime.now() - timedelta(days=1)
    elif 'day' in date:
        date_list = date.split()
        days_str = date_list[1]
        if days_str.isdigit():
            days = int(date_list[1])
            converted_date = datetime.now() - timedelta(days=days)
        else:
            converted_date = None
    elif 'week' in date:
        date_list = date.split()
        weeks_str = date_list[1]
        if weeks_str.isdigit():
            weeks = int(date_list[1])
            converted_date = datetime.now() - timedelta(weeks=weeks)
        else:
            converted_date = None
    elif 'month' in date:
        date_list = date.split()
        month_str = date_list[0]
        if month_str.isdigit():
            month = int(date_list[0])
            converted_date = datetime.now() - timedelta(days=30 * month)
        else:
            converted_date = None
    else:
        converted_date = None
    return converted_date


def parse_pages_count(data):
    soup = BeautifulSoup(data, 'lxml')
    # pagination = soup.select_one('div[class="pagination"]')
    pagination_links = soup.select('div[class="pagination"] a')
    logger.debug(f'pagination_links: {pagination_links}')
    page = 1
    link_page = 1
    for link in pagination_links:
        logger.debug(f'link: {link}')
        link_text = link.text
        if link_text.isdigit():
            link_page = int(link_text)
        logger.debug(f'link_page: {link_page}')
        if link_page >= page:
            page = link_page
    return page



def get_items(page_number, data):
    page_number = page_number
    soup = BeautifulSoup(data, 'lxml')
    items = soup.select('div[class*="search-item"]')
    logger.debug('###############################################')
    logger.debug(
        f'Number of items founded on page {page_number}: {len(items)}')
    logger.debug('###############################################')
    return items


def featured_regular_counter(item):
    global feature_counter, regular_counter
    logger.debug(f"item['class']: {item['class']}")
    if 'top-feature' in item['class']:
        feature_counter += 1
    else:
        regular_counter += 1


def get_item_a(item):
    # Working with a title.
    try:
        item_a = item.select_one('a[class="title"]')
        logger.debug(f'item_a:  {item_a}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_a = None
    return item_a


def get_item_url(item_a):
    # Getting an item url.
    try:
        item_url = BASE + item_a['href']
        logger.debug(f'item_url | len: {len(item_url)} | {item_url}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_url = None
    return item_url


def get_item_title(item_a):
    # Getting an item title.
    try:
        item_title = item_a.text.strip()
        logger.debug(f'item_title: {item_title}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_title = None
    return item_title


def get_item_image_url(item):
    item_image_url = None
    try:
        # Getting an image url.
        item_image_url = item.select_one('img')['data-src']
        logger.debug(
            f'item_image_url | len: {len(item_image_url)} | {item_image_url}')
    except KeyError as key_error:
        if str(key_error) == 'data-src':
            item_image_url = None
            logging.exception(
                f"Exception KeyError: 'data-src' occurred and fixed! | {key_error}")
    except UnboundLocalError as unb_loc_Error:
        item_image_url = None
        logging.exception(
            f"Exception UnboundLocalError: item_image_url not referenced! | {unb_loc_Error}")
    return item_image_url


def get_item_description_min(item):
    # Getting a description_min.
    try:
        item_description_min = item.select_one(
            'div[class="description"]').text
        logger.debug(
            f'item_description_min original | len: {len(item_description_min)} | {item_description_min}')
        if '...' in item_description_min:
            item_description_min = item_description_min.split('...')[0] + '...'
        logger.debug(
            f'item_description_min before space strip | len: {len(item_description_min)} | {item_description_min}')
        item_description_min = splitlines(item_description_min)

        logger.debug(
            f'item_description_min | len: {len(item_description_min)} | {item_description_min}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_description_min = None
    return item_description_min


def get_item_description_tagline(item):
    # Getting a description tagline.
    try:
        item_description_tagline = item.select_one(
            'div[class="tagline"]')
        if item_description_tagline:
            item_description_tagline = item_description_tagline.text.strip()
            item_description_tagline_len = len(
                item_description_tagline)
        else:
            item_description_tagline = None
            item_description_tagline_len = None
        logger.debug(
            f'item_description_tagline | len: {item_description_tagline_len} | {item_description_tagline}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_description_tagline = None
    return item_description_tagline


def get_item_price_currency(item):
    # Getting an item price.
    try:
        item_price_str = item.select_one('div[class="price"]').text.strip()
        logger.debug(f'item_price_str: {item_price_str}')

        # Getting an item price currency.
        if item_price_str[0] == '$':
            item_currency = '$'
        else:
            item_currency = None
            item_price = None
        logger.debug(f'item_currency:  {item_currency}')

        if item_currency is not None:
            item_price_str = item_price_str.split('.')[0]
            logger.debug(f'item_price_str: {item_price_str}')
            item_price = int(
                ''.join(
                    char for char in item_price_str if
                    char.isdecimal()))
        logger.debug(f'item_price: {item_price}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_price = None
        item_currency = None
    return item_price, item_currency


def get_nearest_intersection(item):
    # Getting an item the nearest intersection.
    try:
        item_intersections = item.select_one(
            'span[class="nearest-intersection"]')
        if item_intersections:
            item_intersections_list = item_intersections.select(
                'span[class="intersection"]')
            logger.debug(
                f'item_intersections_list: {item_intersections_list}')
            item_intersections = item_intersections_list[
                                     0].text + ' / ' + \
                                 item_intersections_list[1].text
            item_intersections_len = len(item_intersections)
        else:
            item_intersections = None
            item_intersections_len = None
        logger.debug(
            f'item_intersections | len: {item_intersections_len} | {item_intersections}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_intersections = None
    return item_intersections


def get_item_beds(item):
    # Getting beds.
    try:
        item_beds = item.select_one(
            'span[class="bedrooms"]').text.strip()
        logger.debug(f'item_beds:  {item_beds}')
        item_beds = item_beds.replace('Beds:', '').strip()
        logger.debug(f'item_beds final: {item_beds}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_beds = None
    return item_beds


def get_item_city(item):
    # Getting an item city.
    try:
        item_city_publish_date = item.select_one(
            'div[class="location"]')
        logger.debug(
            f'item_city_publish_date: {item_city_publish_date}')
        if item_city_publish_date:
            item_city = item_city_publish_date.find('span').text
            item_city = item_city.replace('\n', '').strip()
        else:
            item_city = None
        logger.debug(f'item_city: {item_city}')
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_city = None
    return item_city


def get_item_publishing_date(item):
    # Getting an item publishing date.
    try:
        item_date_data = item.select_one(
            'span[class="date-posted"]').text
        if '/' in item_date_data:
            item_date_list = item_date_data.split('/')
            item_date = datetime(int(item_date_list[2]),
                                 int(item_date_list[1]),
                                 int(item_date_list[0]))
        else:
            # Convert '< 10 hours ago' or '< 52 minutes ago' in normal calendar date.
            item_date = convert_date(item_date_data)
        logger.debug(
            f'item_date:  {item_date.strftime("%d-%m-%Y %H:%M")}')
        item_add_date = datetime.now()
    except Exception as error:
        logging.exception(f'Exception occurred during parsing! | {error}')
        item_date = None
    return item_date, item_add_date


def parse_html(html):
    global counter, page_counter
    logger.info(f'Hi from parse_html func!')
    page_counter += 1
    page_number = html[0]
    items = get_items(page_number, html[1])
    data = {}
    # Get items_ids which are in database already
    data_listing_id_from_db = database.get_item_ids(database.engine)
    logger.debug(
        f'Number of item_ids are already exist in database: {len(data_listing_id_from_db)}')
    for item in items:
        data_listing_id = int(item['data-listing-id'])
        logger.debug('###############################################')
        logger.debug(f'Detected data_listing_id:  {data_listing_id}')
        if data_listing_id in data_listing_id_from_db:
            logger.debug(
                f'Detected data_listing_id is already exist in database: {data_listing_id} | Skipped...')
            logger.debug('###############################################')
            continue
        else:
            counter += 1
            logger.debug(f'counter: {counter}')
            logger.debug(
                f'Detected on page {page_number} data_listing_id is taken in work: {data_listing_id}')
            logger.debug('###############################################')
            featured_regular_counter(item)
            # Working with a title.
            item_a = get_item_a(item)
            # Getting an item url.
            item_url = get_item_url(item_a)
            # Getting an item title.
            item_title = get_item_title(item_a)
            # Getting an item image url.
            item_image_url = get_item_image_url(item)
            # Getting a description_min.
            item_description_min = get_item_description_min(item)
            # Getting a description tagline.
            item_description_tagline = get_item_description_tagline(item)
            # Getting a description.
            item_description = None
            # Getting an item price and an item price currency.
            item_price, item_currency = get_item_price_currency(item)
            # Getting an item the nearest intersection.
            item_intersections = get_nearest_intersection(item)
            # Getting beds.
            item_beds = get_item_beds(item)
            # Getting an item city.
            item_city = get_item_city(item)
            # Getting an item publishing date.
            item_date, item_add_date = get_item_publishing_date(item)
            # Data writing into a dictionary.
            item_dict = {'id': data_listing_id,
                         'data_vip_url': item_url,
                         'image_url': item_image_url,
                         'title': item_title,
                         'description_min': item_description_min,
                         'description_tagline': item_description_tagline,
                         'description': item_description,
                         'beds': item_beds,
                         'price': item_price,
                         'currency': item_currency,
                         'city': item_city,
                         'intersections': item_intersections,
                         'rental_type': 'Long Term Rentals',
                         'publish_date': item_date,
                         'add_date': item_add_date
                         }
            # Put data dictionary as 'value' in new dictionary
            # with item_id as 'key'.
            data[data_listing_id] = item_dict
    logger.debug('###############################################')
    logger.debug(f'New items detected during parse: {len(data)}')
    logger.debug('###############################################')
    return data
