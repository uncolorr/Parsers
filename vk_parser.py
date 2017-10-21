from __future__ import print_function

import json
import requests
import urllib.request
import re
import ssl
from breadability.readable import Article
import pymysql


class NewsItem:
    def __init__(self, title, description, url, text_from_site):
        self.__title = title
        self.__description = description
        self.__url = url
        self.__text_from_site = text_from_site

    def get_title(self) -> str:
        return self.__title

    def get_description(self) -> str:
        return self.__description

    def get_url(self) -> str:
        return self.__url

    def get_text_from_site(self) -> str:
        return self.__text_from_site

    def set_title(self, title):
        self.__title = title

    def set_description(self, description):
        self.__description = description

    def set_link(self, link):
        self.__link = link

    def set_text(self, text):
        self.__text = text


ssl._create_default_https_context = ssl._create_unverified_context
conn = pymysql.connect(host='127.0.0.1', user='root', passwd='1234567890', db='lentach_app', use_unicode=True, charset="utf8")
c = conn.cursor()


# https://api.vk.com/method/METHOD_NAME?PARAMETERS&access_token=ACCESS_TOKEN&v=V
def wall_get(owner_id, access_token):
    response = requests.get(
        "https://api.vk.com/method/wall.get?owner_id=-" + owner_id + "&count=10&access_token=" + access_token + "&v=5.68")
    return json.loads(response.text)


def get_token():
    c.execute("SELECT * FROM vk_config")
    items = c.fetchall()
    print(len(items))
    record = items[0]
    access_token = record[1]
    return access_token


def clean_html(raw_html):
    clean_r = re.compile('<.*?>')
    clean_text = re.sub(clean_r, '', raw_html)
    clean_r = re.compile('\n')
    clean_text = re.sub(clean_r, '', clean_text)
    clean_text = re.sub(' +', ' ', clean_text)
    return clean_text


def is_record_exists(news, record):
    booleans = []
    result = False
    for news_item in news:
        if record.get_description():
            booleans.append(news_item[1] == record.get_description())
        if record.get_title():
            booleans.append(news_item[2] == record.get_title())
        if record.get_url():
            booleans.append(news_item[3] == record.get_url())
        if record.get_text_from_site():
            booleans.append(news_item[4] == record.get_text_from_site())

        for b in booleans:
            result = result or b

        if result:
            print(True)
            return result

    print(False)
    return False


access_token = get_token()

c.execute("SELECT * FROM vk_news")
news = c.fetchall()
print(len(news))

publics_indexes = []
c.execute("SELECT * FROM vk_publics")
result = c.fetchall()
items = result
for item in items:
    index = item[0]
    publics_indexes.append(index)

c.execute("SELECT * FROM vk_publics")
publics = c.fetchall()


for public in publics:
    owner_id = public[1]
    values = wall_get(owner_id, access_token)
    response = values["response"]
    items = response["items"]
    for item in items:
        description = item["text"]
        url = ""
        title = ""
        text_from_site = ""

        if 'attachments' in item:
            attachments = item['attachments']
            attachment = attachments[0]
            if attachment["type"] == "link":
                link = attachment["link"]
                url = link["url"]
                title = link["title"]
                resp = urllib.request.urlopen(url)
                xml_resp = resp.read()
                encode = resp.headers.get_content_charset("utf-8")
                d = xml_resp.decode(encode)
                document = Article(d, url=url)
                text_from_site = clean_html(document.readable)
                print(text_from_site)

        if not text_from_site:
            text_from_site = description
        news_item = NewsItem(title, description, url, text_from_site)

        if not is_record_exists(news, news_item):
            c.execute("INSERT INTO vk_news (description, text_from_site, title, url) VALUES(%s, %s, %s, %s)",
                      (news_item.get_description(), news_item.get_text_from_site(), news_item.get_title(),
                       news_item.get_url()))
            c.execute("SELECT * FROM vk_news WHERE ID = (SELECT MAX(ID) FROM vk_news)")
            res = c.fetchall()
            itms = res
            news_index = 0
            for itm in itms:
                news_index = itm[0]
                c.execute("INSERT INTO vk_publics_news (publics_id, news_id) VALUES(%s, %s)",
                          (public[0], news_index))


conn.commit()
conn.close()
