import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support import wait

import config
from core import browser, index_page, ticket_url, login_page
from core.captcha import Captcha, slider_captcha
from utils import console


def _init():
    # 跳转到登录页
    browser.get(login_page)
    time.sleep(1)
    if browser.find_el_if_exist('ERROR', by=By.ID) is not None:
        console.print('[red]12306请求过于频繁,请稍等重试 . . . [/red]')
        browser.wait_unblock()
    # 等待用户密码登录按钮可以点击,切换到用户密码登录 Tab
    wait.WebDriverWait(browser, 5).until(
        ec.element_to_be_clickable((By.CLASS_NAME, 'login-hd-account'))).click()
    time.sleep(1)


def has_login():
    """
    判断用户是否登录
    """
    url = browser.current_url
    if url.startswith(index_page):
        return browser.find_el_if_exist('#J-header-logout > a.logout') is not None
    if url.startswith(ticket_url):
        return browser.find_el_if_exist('#J-header-logout > a:nth-child(3)') is not None
    return False


class Login:

    def __init__(self):
        self.captcha = Captcha()

    def login(self):
        # 初始化
        _init()
        # 自动打码
        self.captcha.code_captcha()
        # 开始登陆
        browser.find_element_by_id('J-userName').send_keys(config.username)
        browser.find_element_by_id('J-password').send_keys(config.password)
        browser.find_element_by_id('J-login').click()
        time.sleep(0.5)
        # 验证滑块验证码
        slider_captcha()
        try:
            # 等待跳转到首页
            wait.WebDriverWait(browser, 10).until(lambda driver: driver.current_url.startswith(index_page))
        except TimeoutException:
            console.print("登录失败,请稍后重试 . . .", style="bold red")
            browser.wait_unblock()
