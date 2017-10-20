from __future__ import print_function
import ssl
import urllib.request
from xml.etree.ElementTree import fromstring
from breadability.readable import Article
import sqlite3
import re
import pymysql


# класс одной новости
class NewsItem:
    def __init__(self, title, description, link, text):
        self.__title = title
        self.__description = description
        self.__link = link
        self.__text = text

    def get_title(self) -> str:
        return self.__title

    def get_description(self) -> str:
        return self.__description

    def get_link(self):
        return self.__link

    def get_text(self) -> str:
        return self.__text

    def set_title(self, title):
        self.__title = title

    def set_description(self, description):
        self.__description = description

    def set_link(self, link):
        self.__link = link

    def set_text(self, text):
        self.__text = text


# класс источника
class Source:
    def __init__(self, name, url_main, url_rss, charset):
        self.__name = name
        self.__url_main = url_main
        self.__url_rss = url_rss
        self.__charset = charset
        self.__news = []

    def get_name(self) -> str:
        return self.__name

    def set_name(self, name):
        self.__name = name

    def get_url_main(self) -> str:
        return self.__url_main

    def set_url_main(self, url_main):
        self.__url_main = url_main

    def set_charset(self, charset):
        self.__charset = charset

    def get_charset(self) -> str:
        return self.__charset

    def get_url_rss(self) -> str:
        return self.__url_rss

    def set_url_rss(self, url_rss):
        self.__url_rss = url_rss

    def add_news(self, news_item):
        self.__news.append(news_item)

    def get_news(self):
        return self.__news


def clean_html(raw_html):
    clean_r = re.compile('<.*?>')
    clean_text = re.sub(clean_r, '', raw_html)
    clean_r = re.compile('\n')
    clean_text = re.sub(clean_r, '', clean_text)
    clean_text = re.sub(' +', ' ', clean_text)
    return clean_text


def is_record_exists(news, record):
    for news_item in news:
        if (news_item[1] == record.get_title()) and (news_item[2] == record.get_description()):
            return True

    return False


ssl._create_default_https_context = ssl._create_unverified_context  # для соеднения, опять какая то херня с сертификатом
sources = []
sources_indexes = []
# conn = sqlite3.connect('lentach_app.db')
conn = pymysql.connect(host='127.0.0.1', user='root', passwd='1234567890', db='lentach_app', use_unicode=True, charset="utf8")
c = conn.cursor()
c.execute("SELECT * FROM rss_sources")
result = c.fetchall()
items = result
for item in items:
    index = item[0]
    name = item[1]
    url_main = item[2]
    url_rss = item[3]
    charset = item[4]
    source = Source(name, url_main, url_rss, charset)
    sources.append(source)
    sources_indexes.append(index)

c.execute("SELECT * FROM rss_news")
news = c.fetchall()

for source in sources:
    response = urllib.request.urlopen(source.get_url_rss())
    xml_response = response.read()
    print(xml_response)
    encoding = response.headers.get_content_charset(source.get_charset())
    data = xml_response.decode(encoding)
    print(type(fromstring(data)))
    root = fromstring(data)
    for item in root.getchildren()[0].findall('item'):  # парсинг
        title = str(item.find('title').text)
        description = str(item.find('description').text)
        link = str(item.find('link').text)
        print(link)
        resp = urllib.request.urlopen(link)
        xml_resp = resp.read()
        encode = response.headers.get_content_charset(source.get_charset())
        d = xml_resp.decode(encode)
        document = Article(d, url=link)
        text = clean_html(document.readable)
        print(text)
        source.add_news(NewsItem(title, description, link, text))

c.execute("SELECT * FROM rss_sources")
result = c.fetchall()
items = result
for item in items:
    index = item[0]
    sources_indexes.append(index)

source_id = 0
for source in sources:
    for news_item in source.get_news():
        if not is_record_exists(news, news_item):
            c.execute("INSERT INTO rss_news (title, description, text) VALUES(%s, %s, %s)",
                      (news_item.get_title(), news_item.get_description(), news_item.get_text()))
            c.execute("SELECT * FROM rss_news WHERE ID = (SELECT MAX(ID) FROM rss_news)")
            res = c.fetchall()
            itms = res
            news_index = 0
            for itm in itms:
                news_index = itm[0]
                c.execute("INSERT INTO rss_sources_news (source_id, news_id) VALUES(%s, %s)",
                          (sources_indexes[source_id], news_index))

    source_id += 1

conn.commit()
conn.close()

# (news_item.get_title().encode('utf-8'), news_item.get_description().encode('utf-8'), news_item.get_text().encode('utf-8'))