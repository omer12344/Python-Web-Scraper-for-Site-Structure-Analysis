from __future__ import annotations
from bs4 import *
from requests import *
from urls import Url, UrlType
from time import time
import json
from datetime import datetime
import os
import random


def time_it_took(func):
    """
    :param func: function to check
    :return: the time it took to execute the function
    """
    def wrapper(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        print("checked url in {} secounds".format(str(time() - t1)[0:6]))
        return result
    return wrapper


@time_it_took
def investigate_url(url: Url, base_domain: str) -> list[Url]:
    """
    :param url: url to investigate
    :param base_domain: base domain of the url
    :return: list of all discovered urls inside param url (each sub url is checked if valid)
    """
    # List of user agents to rotate
    user_agents = [  # dated to around the end of 2023, may expire if executed later...
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/"
        "605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 "
        "(KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/13.1.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/77.0.3865.90 Mobile Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/77.0.3865.90 Safari/537.36"
    ]
    headers = {'User-Agent': random.choice(user_agents)}  # Randomly select a user-agent
    try:
        response = get(url=url.url, headers=headers, timeout=3).content
    except HTTPError as e:
        print("cannot scrape website {}, {}".format(url.url, e))
        return []
    except Exception as unexpected:
        print("unexpected error scraping {}, {}".format(url.url, unexpected))
        return []
    url._already_checked = True
    soup = BeautifulSoup(response, 'html.parser')
    tags = soup('a')
    internal_urls = []
    for tag in tags:
        turl = str(tag.get('href', None))
        if turl:
            internal_urls.append(Url(UrlType.val_to_type(turl), url, turl, []))
    print("found {} urls inside of {}".format(len(internal_urls), url.url))
    internal_urls = filter_url_list(internal_urls, base_domain)
    for u in internal_urls:
        print(Url.__str__(u))
    return internal_urls


def merge_lists(current_list, new_list) -> list[Url]:
    """
    :param current_list: current list of existing urls
    :param new_list: new list of urls just created and found
    :return: new list combining them without duplicates
    """
    for url in new_list:
        if url not in current_list:
            current_list.append(url)
    return current_list


def filter_url_list(url_list: list[Url], base_domain: str) -> list[Url]:
    """
    Filters the URL list to include only URLs that are related to the base domain and not in restricted areas.

    :param url_list: List of URLs to filter.
    :param base_domain: The base domain to check against.
    :return: Filtered list of URLs.
    """
    restricted_areas = [
        "google", "bing", "yahoo", "facebook", "twitter", "linkedin", "youtube",
        "instagram", "pinterest", "tumblr", "reddit", "amazon", "ebay", "wikipedia",
        "about", "quora", "blogspot", "wordpress", "ads", "cookie", "policy",
        "terms", "faq", "support", "login", "signup", "account"
    ]

    def is_url_valid(url: str) -> bool:
        """
        Checks if the URL is valid (not in restricted areas and belongs to the base domain).
        """
        if any(area in url for area in restricted_areas):
            return False
        return base_domain in url

    return [url for url in url_list if is_url_valid(url.url)]


def fix_urls(url_list, base_url) -> list[Url]:
    for i, turl in enumerate(url_list):
        if "http" not in turl.url:
            turl.url = base_url + turl.url
            url_list[i] = turl
    return url_list


@time_it_took
def main() -> dict:
    """
    :return: scraped database of the given url
    """
    global url_to_scrape
    print("Scrapper running....")
    url_to_scrape = "https://www.themarker.com/"
    url_to_scrape = Url(UrlType.val_to_type(url_to_scrape), None, url_to_scrape, [])
    database_dict = {}  # Key: URL string, Value: Dict of URL details

    to_investigate = [url_to_scrape]
    checked_urls = set()

    rcount = 0
    while to_investigate:
        rcount += 1
        print(f"Starting round {rcount}")

        new_urls = []
        for url in to_investigate:
            if url.url not in checked_urls:
                print(f"Investigating: {url.url}")
                internal_urls = investigate_url(url, base_domain=url_to_scrape.url)
                internal_urls = fix_urls(internal_urls, url_to_scrape.url)  # Fix relative URLs
                database_dict[url.url] = {
                    'type': url.url_type.value,
                    'internal_urls': [u.url for u in internal_urls],
                    'checked': url._already_checked
                }
                new_urls.extend(internal_urls)
                checked_urls.add(url.url)

        to_investigate = new_urls
        print(f"Finished round {rcount}")
        print_database(database_dict)
    return database_dict


"""
database and file handling functions
"""


def print_database(database_dict: dict) -> None:
    """
    :param database_dict:
    :return:
    """
    for url, details in database_dict.items():
        print(f"URL: {url}, Type: {details['type']}, Checked: {details['checked']}")
        for internal_url in details['internal_urls']:
            print(f"  - Internal URL: {internal_url}")


def format_filename(base_url: str, extension: str) -> str:
    """
    :param base_url: base url to the filename
    :param extension: file extension
    :return: file name to assemble
    """
    # Extract the base name from the URL
    base_name = base_url.split("//")[-1].split("/")[0]
    # Format the date
    date_str = datetime.now().strftime("%Y-%m-%d")
    # Create the filename
    filename = f"{base_name} {date_str}.{extension}"
    return filename


def export_to_json(database_dict: dict, base_url: str, directory='D:\\cyber_projects\\Webscraper\\outputs') -> None:
    """
    :param database_dict: the actual data of the dictionary
    :param base_url: the base url
    :param directory: directory to copy the file to
    :return:
    """
    filename = format_filename(base_url, 'json')
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w') as file:
        json.dump(database_dict, file, indent=4)


if __name__ == "__main__":
    data_base = main()
    # export database to file
    export_to_json(data_base, url_to_scrape.url)
