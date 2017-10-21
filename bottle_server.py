from bottle import request, route, run, post, get
import pymysql
import requests
import json


def get_token():
    c.execute("SELECT * FROM vk_config")
    items = c.fetchall()
    print(len(items))
    record = items[0]
    access_token = record[1]
    return access_token


conn = pymysql.connect(host='127.0.0.1', user='root', passwd='1234567890', db='lentach_app', use_unicode=True, charset="utf8")
c = conn.cursor()
access_token = get_token()



@route('/hello')
def hello():
    return "Hello World!"


@route('/accept', method='POST')
def accept():
    data = request.json
    type = data["type"]
    if type == "wall_reply_new" or type == "wall_reply_edit" or type == "wall_reply_restore":
        object = data["object"]
        post_owner_id = object["post_owner_id"]
        post_id = object["post_id"]
        result_id = str(post_owner_id) + "_" + str(post_id)
        print(result_id)
        c.execute("SELECT * FROM suggests_news WHERE substring(post_url, 33) = '" + result_id + "'")
        a = c.fetchall()
        temp = a[0]
        news_id = temp[0]
        c.execute("SELECT * FROM user_news WHERE news_id = '%s'" % str(news_id))
        a = c.fetchall()
        temp = a[0]
        user_id = temp[0]

        data = requests.get("https://api.vk.com/method/wall.getById?posts=" + result_id + "&access_token=" + access_token + "&v=5.68")
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
        print(rating)
        c.execute("UPDATE users SET rating = rating + " + str(rating) + " WHERE id = %s", user_id)
        conn.commit()

    if type == "wall_reply_delete":
        pass


run(host='0.0.0.0', port=80, debug=True)
