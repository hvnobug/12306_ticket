import smtplib
import socket
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
import requests
from core.browser import get_random_ua
from utils import console


def send_mail(content, html=False):
    """
    邮件通知
    :param content:str email content
    :param html:boolean 是否为 html 格式
    :return:
    """
    try:
        sender = config.email['sender']
        receivers = config.email["receivers"]
        subject = '恭喜，您已订票成功!'
        username = config.email["username"]
        password = config.email["password"]
        host = config.email["host"]
        if html:
            msg = MIMEMultipart()
            msg.attach(MIMEText(content, 'html', 'utf-8'))
        else:
            msg = MIMEText(content, 'plain', 'utf-8')  # 中文需参数 utf-8，单字节字符不需要
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender
        msg['To'] = ",".join(receivers)
        try:
            smtp = smtplib.SMTP_SSL(host)
            smtp.connect(host)
        except socket.error:
            smtp = smtplib.SMTP()
            smtp.connect(host)
        smtp.connect(host)
        smtp.login(username, password)
        smtp.sendmail(sender, receivers, msg.as_string())
        smtp.quit()
        console.print(u"邮件已通知, 请查收", style="bold green")
    except Exception as e:
        console.print(u"邮件配置有误{}".format(e), style="bold red")


def send_server_chan(content):
    url = f'http://sc.ftqq.com/{config.server_chan["secret"]}.send'
    headers = {
        'User-Agent': get_random_ua()
    }
    payload = {"text": "抢票成功!", "desp": content}
    requests.get(url, params=payload, headers=headers)
