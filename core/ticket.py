import re
import sys
import time
from datetime import datetime

from selenium.common.exceptions import ElementClickInterceptedException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support import wait
from selenium.webdriver.support.select import Select

import config
from core import browser, tk, ticket_url, pay_order_url
from core.login import has_login
from utils import console
from utils.message import send_mail, send_server_chan


class Ticket:
    def __init__(self):
        self._ticket_info = None
        self._running = True
        self._init()

    def _init(self):
        fs, ts = tk.look_up_station()
        self.fs, self.ts = fs, ts

        def to_unicode(s):
            """
            字符串转 unicode
            """
            return s.encode('unicode_escape').decode()

        # 将出发站,目的地,出发时间 加入到 cookie 中。
        js_save_fs = to_unicode(config.from_station).upper().replace('\\U', '%u') + '%2C' + fs
        js_save_ts = to_unicode(config.to_station).upper().replace('\\U', '%u') + '%2C' + ts
        cookie_domain = 'kyfw.12306.cn'
        browser.add_cookie({
            "name": "_jc_save_fromStation", "value": js_save_fs,
            "path": "/", "domain": cookie_domain
        })
        browser.add_cookie({
            "name": "_jc_save_toStation", "value": js_save_ts,
            "path": "/", "domain": cookie_domain
        })
        browser.add_cookie({
            "name": "_jc_save_fromDate", "value": config.from_time,
            "path": "/", "domain": cookie_domain
        })
        # 设置完 cookie 后,表单会自动根据 cookie 信息填充
        time.sleep(0.5)
        browser.get(ticket_url)

    def check(self):
        count = 0
        last_refresh_time = datetime.now().timestamp()
        time.sleep(1)
        while self._running:
            # 检查时候登录失效, 判断是否存在登出按钮
            if not has_login():
                return
            # 检查是否出错
            browser.check_error_page()
            # 随机休眠 0.3-1 秒
            # random_time = random.randint(300, 1000) / 1000
            # time.sleep(random_time)
            now = datetime.now().strftime('%H:%M:%S')
            # 判断是否在预约时间内
            if config.start_time <= now <= config.end_time:
                try:
                    wait.WebDriverWait(browser, 5).until(ec.element_to_be_clickable((By.ID, 'query_ticket'))).click()
                except ElementClickInterceptedException:
                    continue
                time.sleep(0.5)
                count += 1
                console.print(":raccoon:", f'第 [red]{count}[/red] 次点击查询 . . .')
                self._check_ticket()
            else:
                # 为了防止长时间不操作,session 失效
                now_timestamp = datetime.now().timestamp()
                if last_refresh_time - now_timestamp >= 180:
                    last_refresh_time = now_timestamp
                    console.print(":raccoon:", f'[{now}] 刷新浏览器')
                    browser.refresh()
        # 创建订单
        self._create_order()
        message = "恭喜您，抢到票了，请及时前往12306支付订单！"
        console.print(f":smiley: {message}")
        # 发送通知邮件
        if config.email['enable'] is True:
            send_mail(tk.html_ticket_info(self._ticket_info), html=True)
        # 发送 server 酱通知
        if config.server_chan['enable'] is True:
            send_server_chan(tk.md_ticket_info(self._ticket_info))
        sys.exit(0)

    def _create_order(self):
        """
        创建订单
        """
        time.sleep(1)
        passenger_list = browser.find_els_if_exist('#normal_passenger_id > li')
        # 选择乘坐人
        passenger_index = 1
        self._ticket_info['passengers'] = []
        # 检查余票数量
        ticket_value = self._ticket_info['value']
        surplus_ticket_number = int(ticket_value) if ticket_value != '有' else 9999
        for passenger in config.passengers[:surplus_ticket_number]:
            for passenger_li in passenger_list:
                passenger_input = passenger_li.find_element_by_tag_name('input')
                if passenger_li.find_element_by_tag_name('label').text == passenger:
                    console.print(f"选择乘坐人 [{passenger}] . . .")
                    self._ticket_info['passengers'].append(passenger)
                    passenger_input.click()
                    warning_alert = browser.find_el_if_exist('content_defaultwarningAlert_id', by=By.ID)
                    if warning_alert:
                        warning_alert.find_element_by_id('qd_closeDefaultWarningWindowDialog_id').click()
                        time.sleep(0.5)
                    # 选择席座
                    console.print(f"开始选择席座 [{self._ticket_info['seat_type']}] . . .")
                    seat_select = browser.find_element_by_id(f"seatType_{str(passenger_index)}")
                    seat_type = tk.seat_type_dict[self._ticket_info['seat_type']]
                    if not seat_type:
                        console.print(f"未找到坐席类型 :[red] {seat_type} [/red]")
                        sys.exit(-1)
                    seat_type_value = seat_type['value']
                    if seat_type_value != '0':
                        Select(seat_select).select_by_value(seat_type_value)
                    passenger_index += 1
                    time.sleep(0.5)
        if passenger_index == 1:
            console.print("未找到乘客信息 ... 无法选择乘客和坐席", style="bold red")
        print('正在提交订单 . . .')
        wait.WebDriverWait(browser, 5).until(ec.element_to_be_clickable((By.ID, 'submitOrder_id'))).click()
        time.sleep(1)
        # 通知对话框
        notice_el = browser.find_el_if_exist('content_transforNotice_id', by=By.ID)
        if notice_el and notice_el.is_displayed():
            notice_content = browser.find_element_by_css_selector('#orderResultInfo_id > div > span').text
            console.print("确认订单失败:", notice_content, style="bold yellow")
            sys.exit(-1)
        try:
            # 确认提交订单
            print('正在确认订单 . . .')
            wait.WebDriverWait(browser, 5).until(ec.element_to_be_clickable((By.ID, 'qr_submit_id'))).click()
            # 等待跳转到支付页面, 如果超时未跳转, 说明订单生成失败
            wait.WebDriverWait(browser, 10).until(lambda driver: driver.current_url.startswith(pay_order_url))
        except WebDriverException:
            # 核信息对话框,当确认订单按钮不可用
            check_el = browser.find_el_if_exist('content_checkticketinfo_id', by=By.ID)
            if check_el and check_el.is_displayed():
                check_text = check_el.find_element_by_id('sy_ticket_num_id').text
                console.print(check_text, style="bold red")
                sys.exit(-1)
            # 订单提交失败会出现提示框
            notice_el = browser.find_el_if_exist('content_transforNotice_id', by=By.ID)
            if notice_el and notice_el.is_displayed():
                title = browser.find_element_by_css_selector('#orderResultInfo_id > div > span').text
                content = notice_el.find_element_by_tag_name('p').text
                console.print(f'[red]{title}[/red]', content)
                sys.exit(-1)
        # 截取屏幕,订单信息页
        print('预订成功,正在截取屏幕 . . .')
        browser.screenshot(
            f'{self.fs}_{self.ts}_{config.from_time.replace("-", "")}_{self._ticket_info["train"].lower()}.png'
        )

    def _try_submit(self, index, left_tr, train_name):
        """
        尝试提交
        :param index: 表格索引
        :param left_tr: 列车信息行
        :param train_name: 列车车次名称
        """
        left_tr_id = left_tr.get_attribute('id')
        submit_btn = browser.find_el_if_exist('#' + left_tr_id + ' > td.no-br > a')
        if submit_btn:
            ss, es, st, et, du = tk.get_train_info(index)
            if str.startswith(left_tr_id, 'ticket_'):
                serial_num = left_tr_id[len('ticket_'):].split('_')[0]
                # 座位类型是否匹配
                for seat_type in config.seat_types:
                    if tk.seat_type_dict[seat_type]:
                        seat_selector = '#' + tk.seat_type_dict[seat_type]["code"] + '_' + serial_num
                        seat = left_tr.find_element_by_css_selector(seat_selector)
                        if seat:
                            ticket_info = {
                                "address": f"{ss} - {es}", "time": f"{st} - {et}", "duration": du,
                                'train': train_name
                            }

                            # 判断是否有余票,如果有余票就尝试提交
                            def try_submit(seat_el):
                                seat_text = seat_el.text
                                if seat_text == '有' or re.match("^\\d+$", seat_text):
                                    self._running = False
                                    ticket_info['seat_type'] = seat_type
                                    ticket_info['value'] = seat_text
                                    self._ticket_info = ticket_info
                                    console.print(tk.table_ticket_info(ticket_info))
                                    submit_btn.click()
                                    return True
                                return False

                            seat_div = browser.find_el_if_exist(seat_selector + ' > div')
                            if try_submit(seat_div if seat_div else seat):
                                return True
                    else:
                        console.print(f"未找到坐席类型 :[red] {seat_type} [/red]")
                        sys.exit(-1)
                    console.print(f":vampire: {config.from_time} - {train_name} - {seat_type}", "[red]暂无余票[/red]")
        else:
            console.print(f":vampire: {config.from_time} - {train_name}", "[red]暂无余票[/red]")
        return False

    def _check_ticket(self):
        """
        检查是否有余票
        """
        exist_train = False
        left_tr_list = browser.find_els_if_exist('#queryLeftTable > tr')
        # 真实的列车信息行索引
        train_row_index = 0
        for index in range(len(left_tr_list)):
            # 跳过空行
            if index % 2 == 0:
                left_tr = left_tr_list[index]
                train_tr = left_tr_list[index + 1]
                train_name = train_tr.get_attribute('datatran')
                for t in config.trains:
                    if t == train_name:
                        exist_train = True
                        if self._try_submit(train_row_index, left_tr, train_name):
                            return
                train_row_index += 1
        if not exist_train:
            console.print(
                ':raccoon: [yellow]未查询到车次信息[/yellow]: ',
                config.from_time, f"[{str.join(',', config.trains)}]"
            )
