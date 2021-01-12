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
from core.browser import find_el_if_exist
from core.login import has_login
from utils import console
from utils.message import send_mail, send_server_chan
from utils.time import datetime_format_str, time_format_str, date_format_str


def check_alert():
    alert_el = browser.find_el_if_exist('content_defaultwarningAlert_id', by=By.ID)
    if alert_el and alert_el.is_enabled():
        btn = browser.find_el_if_exist('qd_closeDefaultWarningWindowDialog_id', by=By.ID)
        if btn and btn.is_enabled():
            btn.click()


def show_alert_info(text=None, split='  '):
    """
    @param text 添加到打印信息头部
    @param split 打印信息分隔符
    打印通知警告信息
    """
    print_info = []
    if text:
        print_info.append(text)

    # 对话框
    check_el = browser.find_el_if_exist('content_checkticketinfo_id', by=By.ID)
    if check_el and check_el.is_displayed():
        check_text = check_el.find_element_by_id('sy_ticket_num_id').text
        console.print(check_text, style="bold red")
    # 提示框
    notice_el = browser.find_el_if_exist('content_transforNotice_id', by=By.ID)
    if notice_el and notice_el.is_displayed():
        el = browser.find_el_if_exist('#orderResultInfo_id > div > span')
        if el:
            print_info.append(f'[red]{el.text}[/red]')
        el = find_el_if_exist(notice_el, 'p', by=By.TAG_NAME)
        if el:
            print_info.append(el.text)
    console.print(split.join(print_info))


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

    def check(self):
        browser.get(ticket_url)
        time.sleep(1)
        check_alert()
        count = 0
        while self._running:
            # 检查时候登录失效, 判断是否存在登出按钮
            if not has_login():
                return
            # 检查是否出错
            browser.check_error()

            # 随机休眠 0.3-1 秒
            # random_time = random.randint(300, 1000) / 1000
            # time.sleep(random_time)

            # 把开始时间,结束时间字符串转换为日期
            now = datetime.now()

            def convert_time_to_datetime(time_str):
                now_date_str = now.strftime(date_format_str)
                return datetime.strptime(f"{now_date_str} {time_str}", datetime_format_str)
            start_ts = convert_time_to_datetime(config.start_time).timestamp()
            end_ts = convert_time_to_datetime(config.end_time).timestamp()
            now_ts = now.timestamp()
            # 判断是否在预约时间内
            if (start_ts - 120) <= now_ts <= end_ts:
                try:
                    wait.WebDriverWait(browser, 5).until(ec.element_to_be_clickable((By.ID, 'query_ticket'))).click()
                except ElementClickInterceptedException:
                    continue
                time.sleep(0.5)
                count += 1
                console.print(":raccoon:", f'第 [red]{count}[/red] 次点击查询 . . .')
                self._check_ticket()
                # 每查询 1000 次刷新一次浏览器
                if count % 1000 == 0:
                    browser.refresh()
                    time.sleep(1)
                    # 检测是否出现提醒框
                    check_alert()
            else:
                # 使用睡眠方案,提前两分钟唤醒,登录超时会自动登录
                now_time_str = now.strftime(time_format_str)
                # 取今天日期 当前时间小于开始抢票时间
                if now_time_str < config.start_time:
                    date_str = now.strftime(date_format_str)
                # 取明天的日期
                else:
                    tomorrow = datetime.fromtimestamp(now.timestamp() + 60 * 60 * 24)
                    date_str = tomorrow.strftime(date_format_str)
                next_run_datetime = datetime.strptime(f"{date_str} {config.start_time}", datetime_format_str)
                sleep_second = next_run_datetime.timestamp() - now.timestamp() - 120
                console.print("未到达开始开放抢票时间,程序即将休眠 ... ", style="bold yellow")
                console.print(f"程序将于 [{next_run_datetime.strftime(datetime_format_str)}] 重新启动 !", style="bold green")
                time.sleep(sleep_second)
        # 创建订单
        if self._create_order():
            message = "恭喜您，抢到票了，请及时前往12306支付订单！"
            console.print(f":smiley: {message}")
            # 发送通知邮件
            if config.email['enable'] is True:
                send_mail(tk.html_ticket_info(self._ticket_info), html=True)
            # 发送 server 酱通知
            if config.server_chan['enable'] is True:
                send_server_chan(tk.md_ticket_info(self._ticket_info))
            sys.exit(0)
        self.check()

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
        try:
            print('正在提交订单 . . .')
            wait.WebDriverWait(browser, 10).until(ec.element_to_be_clickable((By.ID, 'submitOrder_id'))).click()
            time.sleep(1)
            # 确认提交订单
            print('正在确认订单 . . .')
            wait.WebDriverWait(browser, 10).until(ec.element_to_be_clickable((By.ID, 'qr_submit_id'))).click()
            # 等待跳转到支付页面, 如果超时未跳转, 说明订单生成失败
            wait.WebDriverWait(browser, 10).until(lambda driver: driver.current_url.startswith(pay_order_url))
            submit_btn = browser.find_el_if_exist('qr_submit_id', by=By.ID)
            if not submit_btn or not submit_btn.is_displayed():
                console.print(f'该车次无法提交[{self._ticket_info["train"]}]。', style="bold yellow")
                config.trains.remove(self._ticket_info["train"])
                show_alert_info('该车次无法提交[{self._ticket_info["train"]}]。', '\n')
                return False
        except WebDriverException as e:
            browser.screenshot(f'{datetime.now().strftime(datetime_format_str)}-error.png')
            show_alert_info('提交订单失败:\n')
            raise e
        # 截取屏幕,订单信息页
        print('预订成功,正在截取屏幕 . . .')
        browser.screenshot(
            f'{self.fs}_{self.ts}_{config.from_time.replace("-", "")}_{self._ticket_info["train"].lower()}.png'
        )
        return True

    def _try_submit(self, train_trs):
        """
        尝试提交
        :param train_trs: 列车车次名称
        """
        for train_tr in train_trs:
            submit_btn = find_el_if_exist(train_tr, 'td.no-br > a')
            ss, es, st, et, du, tn = tk.get_train_info(train_tr)
            if submit_btn and submit_btn:
                left_tr_id = train_tr.get_attribute('id')
                serial_num = left_tr_id[len('ticket_'):].split('_')[0]
                # 座位类型是否匹配
                for seat_type in config.seat_types:
                    if tk.seat_type_dict[seat_type]:
                        seat_type_id = tk.seat_type_dict[seat_type]["code"] + '_' + serial_num
                        seat = train_tr.find_element_by_id(seat_type_id)
                        if seat:
                            ticket_info = {
                                "address": f"{ss} - {es}", "time": f"{st} - {et}", "duration": du,
                                'train': tn
                            }
                            # 判断是否有余票,如果有余票就尝试提交
                            seat_text = seat.text
                            if seat_text == '有' or re.match("^\\d+$", seat_text):
                                self._running = False
                                ticket_info['seat_type'] = seat_type
                                ticket_info['value'] = seat_text
                                self._ticket_info = ticket_info
                                console.print(tk.table_ticket_info(ticket_info))
                                submit_btn.click()
                                return True
                        else:
                            console.print(f"未找到坐席类型 :[red] {seat_type} [/red]")
                            console.print("请按照要求配置坐席类型:", ",".join(tk.seat_type_dict.keys()))
                            sys.exit(-1)
                    console.print(f":vampire: {config.from_time} - {tn} - {seat_type}", "[red]暂无余票[/red]")
            else:
                console.print(f":vampire: {config.from_time} - {tn}", "[red]暂无余票[/red]")
        return False

    def _check_ticket(self):
        """
        检查是否有余票
        """
        train_trs = tk.find_train_info_trs()
        if len(train_trs) == 0:
            console.print(
                ':raccoon: [yellow]未查询到车次信息[/yellow]: ',
                config.from_time, f"[{str.join(',', config.trains)}]"
            )
        else:
            self._try_submit(train_trs)
