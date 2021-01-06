import time
import config
import random
from core import browser
from utils import console
from rich.table import Table
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import wait
from utils.message import send_mail, send_ftqq
from selenium.webdriver.support import expected_conditions as ec

seat_type_dict = {
    "商务座": "SWZ",
    "一等座": "ZY",
    "二等座": "ZE",
    "高级软卧": "GR",
    "软卧": "RW",
    "动卧": "SRRB",
    "硬卧": "YW",
    "软座": "RZ",
    "硬座": "YZ",
    "无座": "WZ",
    "其他": "QT"
}
ticket_url = 'https://kyfw.12306.cn/otn/leftTicket/init'


def _look_up_station():
    """
    读取车站信息
    :return:
    """
    # 文件来自 https://kyfw.12306.cn/otn/resources/js/framework/favorite_name.js
    import os
    path = os.path.join(os.path.dirname(__file__), '../favorite_name.js')
    try:
        with open(path, encoding="utf-8") as result:
            info = result.read().split('=')[1].strip("'").split('@')
    except Exception as e:
        print(e)
        with open(path) as result:
            info = result.read().split('=')[1].strip("'").split('@')
    del info[0]
    station_name = {}
    for i in range(0, len(info)):
        n_info = info[i].split('|')
        station_name[n_info[1]] = n_info[2]
    try:
        fs = station_name[config.from_station.encode("utf8")]
        ts = station_name[config.to_station.encode("utf8")]
    except KeyError:
        fs = station_name[config.from_station]
        ts = station_name[config.to_station]
    return fs, ts


_ticket_info_headers = [
    '车次', '时间', '地点', '历时', '类型', '余票'
]


def _train_color(train):
    if train.startswith('K'):
        train_color = 'white'
    elif train.startswith('T'):
        train_color = 'green'
    elif train.startswith('Z'):
        train_color = 'rgb(0,255,0)'
    elif train.startswith('D'):
        train_color = 'rgb(255,215,0)'
    elif train.startswith('G'):
        train_color = 'red'
    else:
        train_color = 'magenta'
    return train_color


def _value_color(value):
    if value == '有':
        value_color = 'green'
    elif value == '候补':
        value_color = 'yellow'
    else:
        value_color = 'magenta'
    return value_color


def _md_ticket_info(ti):
    """
    将列车信息转成 markdown
    """
    # train = ti['train']
    # value = ti['value']
    # row = [
    #     f'<span style="color={_train_color(train)};">{train}</span>',
    #     ti['time'], ti['address'], ti['duration'], ti['seat_type'],
    #     f'<span style="color={_value_color(value)};">{value}</span>'
    # ]
    # r1 = str.join('|', [f' {header} ' for header in _ticket_info_headers])
    # r2 = str.join('|', [' :---: ' for _ in range(len(_ticket_info_headers))])
    # r3 = str.join('|', [f' {item} ' for item in row])
    # return f'{r1}\n{r2}\n{r3}'
    headers = _ticket_info_headers
    return str.join('\n', [
        f'* **{headers[0]}:** {ti["train"]}',
        f'* **{headers[1]}:** {ti["time"]}',
        f'* **{headers[2]}:** {ti["address"]}',
        f'* **{headers[3]}:** {ti["seat_type"]}',
        f'* **{headers[4]}:** {ti["value"]}'
    ])


def _table_ticket_info(ti):
    """
    将列车信息转成表格
    """
    table = Table(show_header=True, header_style="bold")
    for header in _ticket_info_headers:
        table.add_column(header, justify="center")
    train = ti['train']
    value = ti['value']
    value_color = _value_color(value)
    train_color = _train_color(train)
    table.add_row(
        f"[{train_color}]{train}[/{train_color}]",
        ti['time'],
        ti['address'],
        ti['duration'],
        ti['seat_type'],
        f"[{value_color}]{value}[/{value_color}]"
    )
    table.highlight = True
    return table


def _get_train_info(index):
    """
    获取列车信息
    :param index: 表格索引
    """
    train_num_id = '#train_num_' + str(index)
    cds = train_num_id + ' > div.cds'
    cdz = train_num_id + ' > div.cdz'
    ss = browser.find_el_if_exist(cdz + ' > strong.start-s').text
    es = browser.find_el_if_exist(cdz + ' > strong.end-s').text
    st = browser.find_el_if_exist(cds + ' > strong.start-t').text
    et = browser.find_el_if_exist(cds + ' > strong.color999').text
    du = browser.find_el_if_exist(train_num_id + '> div.ls > strong').text
    return ss, es, st, et, du


class Ticket:
    def __init__(self):
        self._ticket_info = None
        self._running = True
        self._init()

    def _init(self):
        fs, ts = _look_up_station()
        self.fs, self.ts = fs, ts
        time.sleep(0.5)
        browser.get(ticket_url)

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
        # 刷新浏览器,表单会自动根据 cookie 信息填充
        browser.refresh()
        time.sleep(0.5)

    def check(self):
        count = 0
        sleep_time = 0
        while self._running:
            random_time = random.randint(300, 1000) / 1000
            time.sleep(random_time)
            now = datetime.now().strftime('%H:%M:%S')
            # 判断是否在预约时间内
            if config.start_time <= now <= config.end_time:
                count += 1
                browser.find_element_by_id('query_ticket').click()
                time.sleep(0.5)
                console.print(f':vampire: 第 [red]{count}[/red] 次点击查询 . . .')
                self._check_ticket()
            else:
                sleep_time += 1
                # 为了防止长时间不操作,session 失效
                if sleep_time >= 60:
                    sleep_time = 0
                    console.print(f':raccoon: [{now}] 刷新浏览器')
                    browser.refresh()
        self._create_order()
        message = "恭喜您，抢到票了，请及时前往12306支付订单！"
        console.print(f":smiley: {message}")
        if config.mail['enable'] is True:
            send_mail(message)
        if config.ftqq_server['enable'] is True:
            send_ftqq(_md_ticket_info(self._ticket_info))

    def _create_order(self):
        """
        创建订单
        """
        time.sleep(0.5)
        passenger_list = browser.find_els_if_exist('#normal_passenger_id > li')
        for passenger in config.passengers:
            for passenger_li in passenger_list:
                passenger_input = passenger_li.find_element_by_tag_name('input')
                if passenger_li.find_element_by_tag_name('label').text == passenger \
                        and not passenger_input.is_selected():
                    passenger_input.click()
        wait.WebDriverWait(browser, 5).until(ec.element_to_be_clickable((By.ID, 'submitOrder_id'))).click()
        wait.WebDriverWait(browser, 5).until(ec.element_to_be_clickable((By.ID, 'qr_submit_id'))).click()
        # 截取屏幕,订单信息页
        browser.screenshot(
            f'{self.fs}_{self.ts}_{config.from_time.replace("-", "")}_{self._ticket_info["train"].lower()}.png'
        )
        time.sleep(60)

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
            ss, es, st, et, du = _get_train_info(index)
            if str.startswith(left_tr_id, 'ticket_'):
                serial_num = left_tr_id[len('ticket_'):].split('_')[0]
                # 座位类型是否匹配
                for seat_type in config.seat_types:
                    if seat_type_dict[seat_type]:
                        seat_selector = '#' + seat_type_dict[seat_type] + '_' + serial_num
                        seat = left_tr.find_element_by_css_selector(seat_selector)
                        if seat:
                            ticket_info = {
                                "address": f"{ss} - {es}", "time": f"{st} - {et}", "duration": du,
                                'train': train_name
                            }

                            # 判断是否有余票,如果有余票就尝试提交
                            def try_submit(seat_el):
                                if seat_el.text and seat_el.text is not '无' \
                                        and seat_el.text is not '--':
                                    self._running = False
                                    ticket_info['seat_type'] = seat_type
                                    ticket_info['value'] = seat_el.text
                                    self._ticket_info = ticket_info
                                    console.print(_table_ticket_info(ticket_info))
                                    print(_md_ticket_info(ticket_info))
                                    submit_btn.click()
                                    return True
                                return False

                            seat_div = browser.find_el_if_exist(seat_selector + ' > div')
                            if try_submit(seat_div if seat_div else seat):
                                return True
                            console.print(":vampire:", f"{config.from_time} - {seat_type}", "[red]暂无余票[/red]")
        return False

    def _check_ticket(self):
        """
        检查是否有余票
        """
        left_tr_list = browser.find_els_if_exist('#queryLeftTable > tr')
        for index in range(len(left_tr_list)):
            # 跳过空表格行
            if index % 2 == 0:
                left_tr = left_tr_list[index]
                train_tr = left_tr_list[index + 1]
                train_name = train_tr.get_attribute('datatran')
                for t in config.trains:
                    if t == train_name:
                        if self._try_submit(index, left_tr, train_name):
                            return
