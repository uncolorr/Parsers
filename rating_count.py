import json
import requests
import ssl
import pymysql


class SuggestNewsItem:
    def __init__(self, rating, news_id):
        self.__rating = rating
        self.__news_id = news_id

    def get_rating(self) -> int:
        return self.__rating

    def get_news_id(self) -> int:
        return self.__news_id

    def set_news_id(self, news_id):
        self.__news_id = news_id

    def set_rating(self, rating):
        self.__rating = rating


def get_token():
    c.execute("SELECT * FROM vk_config")
    items = c.fetchall()
    print(len(items))
    record = items[0]
    access_token = record[1]
    return access_token



ssl._create_default_https_context = ssl._create_unverified_context

conn = pymysql.connect(host='127.0.0.1', user='root', passwd='1234567890', db='lentach_app', use_unicode=True, charset="utf8")
c = conn.cursor()


list_suggests_news = []
dict_suggests_news = {}



access_token = get_token()
c.execute("SELECT * FROM suggests_news")
suggests_news = c.fetchall()

post_ids = []

for news_item in suggests_news:

    post_url = news_item[5]
    news_id = news_item[0]
    index_start = post_url.rindex("-")
    post_id = post_url[index_start:]
    print(post_id)
    data = requests.get("https://api.vk.com/method/wall.getById?posts=" + post_id + "&access_token=" + access_token + "&v=5.68")
    json_object = json.loads(data.text)
    response = json_object["response"]
    response_item = response[0]
    comments = response_item["comments"]
    comments_count = int(comments["count"])
    likes = response_item["likes"]
    likes_count = int(likes["count"])
    reposts = response_item["reposts"]
    reposts_count = int(reposts["count"])

    rating = int((likes_count + 20 * comments_count + 25 * reposts_count) / 5000)
    list_suggests_news.append(SuggestNewsItem(rating, news_id))
    dict_suggests_news[news_id] = rating
    print("Rating: ", rating)
   # c.execute("SELECT * FROM user_news WHERE news_id = %s", str(news_id))
    c.execute("SELECT * FROM user_news")
    user_news_items = c.fetchall()
    for user_news_item in user_news_items:
       # print("news_id = ", news_id)
       # print("user_news_item_id = ", user_news_item[1])
        if news_id == user_news_item[1]:

            print("YES")
            user_id = user_news_item[0]
            # c.execute("UPDATE users SET rating = '99' WHERE id = %s", str(user_id))
            c.execute("SELECT * FROM user_news WHERE user_id = %s", str(user_id))
            news_items = c.fetchall()
            result_rating = 0
            for n in news_items:
                if n[1] in dict_suggests_news:
                    result_rating += dict_suggests_news[n[1]]
            print("Result rating is: ", result_rating)
            c.execute("UPDATE users SET rating = '" + str(result_rating) + "' WHERE id = %s", str(user_id))


conn.commit()
conn.close()














