import time
import config
from core import browser
from core.captcha import Captcha
from selenium.webdriver.common.by import By
from selenium.webdriver.support import wait
from selenium.webdriver.support import expected_conditions as ec

login_page = 'https://kyfw.12306.cn/otn/resources/login.html'


def _init():
    # 现在使用这个url地址
    browser.get(login_page)
    # 等待用户密码登录按钮可以点击,切换到用户密码登录 Tab
    wait.WebDriverWait(browser, 5).until(
        ec.element_to_be_clickable((By.CLASS_NAME, 'login-hd-account'))).click()
    time.sleep(1)


class Login:

    def __init__(self):
        self.captcha = Captcha(browser)

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
        self.captcha.slider_captcha()
        time.sleep(1)
