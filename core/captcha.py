import sys
import time
import requests
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

import config
from core import browser
from utils import console


class Captcha:
    def _get_captcha(self):
        time.sleep(0.5)
        # 获取验证码图片
        self._code_img_ele = browser.find_element_by_id('J-loginImg')
        base64_img = self._code_img_ele.get_attribute('src')
        self._code_img = base64_img[len('data:image/jpg;base64,'):]

    def code_captcha(self):
        # 获取验证码图片
        self._get_captcha()
        # 获取打码坐标
        points = self._parse_captcha()
        # 开始打码
        self._verify_captcha(points)
        time.sleep(0.5)

    def _verify_captcha(self, points):
        # 遍历列表，使用动作链对每一个列表元素对应的x,y指定的位置进行点击操作
        for i in range(len(points) // 2):
            ActionChains(browser).move_to_element_with_offset(
                self._code_img_ele,
                float(points[i * 2]),
                float(points[i * 2 + 1])
            ).click().perform()
            time.sleep(1)

    def _parse_captcha(self):
        # 这里也可以使用自建打码服务器
        code_url = f'{config.code_server["scheme"]}://{config.code_server["host"]}{config.code_server["path"]}'
        data = {"imageFile": self._code_img}
        count = 0
        while count < 10:
            count += 1
            try:
                resp = requests.post(code_url, data=data)
                if resp.status_code is 200:
                    resp_json = resp.json()
                    if resp_json and resp_json.get("code") is 0:
                        return code_xy(resp_json.get("data")).split(',')
            except Exception as e:
                print(e)
                console.print(f'[red]打码失败[/red] - [{count}]')
                sys.exit(-1)


def code_xy(select):
    post = []
    offsets_x = 0  # 选择的答案的left值,通过浏览器点击8个小图的中点得到的,这样基本没问题
    offsets_y = 0  # 选择的答案的top值
    for offset in select:
        if offset == '1':
            offsets_y = 77
            offsets_x = 40
        elif offset == '2':
            offsets_y = 77
            offsets_x = 112
        elif offset == '3':
            offsets_y = 77
            offsets_x = 184
        elif offset == '4':
            offsets_y = 77
            offsets_x = 256
        elif offset == '5':
            offsets_y = 149
            offsets_x = 40
        elif offset == '6':
            offsets_y = 149
            offsets_x = 112
        elif offset == '7':
            offsets_y = 149
            offsets_x = 184
        elif offset == '8':
            offsets_y = 149
            offsets_x = 256
        else:
            pass
        post.append(offsets_x)
        post.append(offsets_y)
    rand_code = str(post).replace(']', '').replace('[', '').replace("'", '').replace(' ', '')
    console.print(f":thumbs_up: 验证码识别成功: [{rand_code}]")
    return rand_code


def slider_captcha():
    try_time = 1
    div = browser.find_el_if_exist('nc_1_n1z', by=By.ID)
    while div and div.is_displayed():
        if try_time > 10:
            console.print('滑块验证码验证失败 . . .', style='bold red')
            sys.exit(-1)
        # 动作链
        action = ActionChains(browser)
        # 点击长按指定的标签
        action.click_and_hold(div)
        # 处理滑动模块
        for i in range(5):
            # perform()立即执行动作链操作
            # move_by_offset(x,y):x水平方向 y竖直方向
            try:
                action.move_by_offset(350, 0).perform()  # 速度为30mm
            except WebDriverException:
                time.sleep(0.5)
        time.sleep(0.5)
        action.release()
        try_time += 1
        div = browser.find_el_if_exist('nc_1_n1z', by=By.ID)
