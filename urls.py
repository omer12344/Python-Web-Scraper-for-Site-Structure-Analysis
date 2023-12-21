from __future__ import annotations  # makes type hinting a str not a type for readability

from enum import Enum


class UrlType(Enum):
    pdf = ".pdf"
    jpg = ".jpg"
    png = ".png"
    gif = ".gif"
    html = ".html"
    mp3 = ".mp3"
    mp4 = ".mp4"
    doc = ".doc"
    docx = ".docx"
    xls = ".xls"
    xlsx = ".xlsx"
    ppt = ".ppt"
    pptx = ".pptx"
    txt = ".txt"
    zip = ".zip"
    csv = ".csv"
    json = ".json"
    xml = ".xml"
    unknown_type = "unknown url type"

    @classmethod
    def val_to_type(cls, url):
        for ty in cls:
            if ty.value in url:
                return ty
        return cls.unknown_type


class Url:

    def __init__(self, url_type: UrlType, super_url: Url, url: str, internal_urls: list[Url]):
        self.url_type = url_type
        self.super_url = super_url
        self.url = url
        self.internal_urls = internal_urls
        self._already_checked = False

    def __str__(self):
        if self.super_url:
            st = (f"url: {self.url} is a sub url of {self.super_url.url}, its type is {self.url_type.value},"
                  f" checked: {self._already_checked}")
        else:
            st = (f"url: {self.url} is the super url of all urls scraped, its type is {self.url_type.value},"
                  f" checked: {self._already_checked}")
        st += ", its internal urls:\n "
        for url in self.internal_urls:
            st += url.url
            st += '\n'
        return st


