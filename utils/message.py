import config
import requests
from core.browser import get_random_ua


def send_mail(content):
    # TODO
    print(content)


def send_ftqq(content):
    url = f'http://sc.ftqq.com/{config.ftqq_server["sckey"]}.send'
    headers = {
        'User-Agent': get_random_ua()
    }
    payload = {"text": "抢票成功!", "desp": content}
    requests.get(url, params=payload, headers=headers)
