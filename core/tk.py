from rich.table import Table
from selenium.webdriver.common.by import By

import config
from core import browser

_ticket_info_headers = [
    '车次', '时间', '地点', '历时', '类型', '余票'
]

seat_type_dict = {
    "商务座": {
        "code": "SWZ",
        "index": 1,
        "value": "9"
    },
    "一等座": {
        "code": "ZY",
        "index": 2,
        "value": "M"
    },
    "二等座": {
        "code": "ZE",
        "index": 3,
        "value": "0"
    },
    "高级软卧": {
        "code": "GR",
        "index": 4,
        "value": "6"
    },
    "软卧": {
        "code": "RW",
        "index": 5,
        "value": "4"
    },
    "动卧": {
        "code": "SRRB",
        "index": 6,
        "value": "F"
    },
    "硬卧": {
        "code": "YW",
        "index": 7,
        "value": "3"
    },
    "软座": {
        "code": "RZ",
        "index": 8,
        "value": "2"
    },
    "硬座": {
        "code": "YZ",
        "index": 9,
        "value": "1"
    },
    "无座": {
        "code": "WZ",
        "index": 10,
        "value": "1"
    },
    "其他": {
        "code": "QT",
        "index": 11,
        "value": "1"
    }
}


def look_up_station():
    """
    读取车站信息
    :return:
    """
    import os
    path = os.path.join(os.path.dirname(__file__), '../station_names.js')
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


def md_ticket_info(ti):
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
        f'* **{headers[3]}:** {ti["duration"]}',
        f'* **{headers[4]}:** {ti["seat_type"]}',
        f'* **乘坐人:** {str.join(",", ti["passengers"])}',
    ])


def table_ticket_info(ti):
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


def html_ticket_info(ti):
    headers = _ticket_info_headers

    def render_li(k, v):
        return f'<li><strong style="margin-right:5px;">{k}:</strong>{v}</li>'

    return f"""
    <h3>抢票成功!</h3>
    <div>
        <ul>
            {render_li(headers[0], ti["train"])}
            {render_li(headers[1], ti["time"])}
            {render_li(headers[2], ti["address"])}
            {render_li(headers[3], ti["duration"])}
            {render_li(headers[4], ti["seat_type"])}
            {render_li('乘坐人', str.join(",", ti["passengers"]))}
        </ul>
    </div>
    """


def get_train_info(train_trs):
    """
    获取列车信息
    :param train_trs: 表格列
    """
    cds = 'div.cds'
    cdz = 'div.cdz'

    def text_el(prefix, number):
        return f"{prefix}  > strong:nth-child({number})"

    ss = train_trs.find_element_by_css_selector(text_el(cdz, 1)).text
    es = train_trs.find_element_by_css_selector(text_el(cdz, 2)).text
    st = train_trs.find_element_by_css_selector(text_el(cds, 1)).text
    et = train_trs.find_element_by_css_selector(text_el(cds, 2)).text
    du = train_trs.find_element_by_css_selector('div.ls > strong').text
    tn = train_trs.find_element_by_css_selector('.train .number').text
    return ss, es, st, et, du, tn


def find_train_info_trs():
    """查询表格中的车次信息"""
    trs = []
    for t in config.trains:
        # 可能会出现相同名称车次
        numbers = browser.find_els_if_exist(t, by=By.LINK_TEXT)
        if numbers is None or len(numbers) is 0:
            continue
        for number in numbers:
            trs.append(number.find_element_by_xpath('../../../../..'))
    return trs
