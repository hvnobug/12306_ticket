from rich.table import Table
import config
from core import browser

_ticket_info_headers = [
    '车次', '时间', '地点', '历时', '类型', '余票'
]

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


def get_seat_type_index_value(seat_type):
    if seat_type == '商务座':
        seat_type_index = 1
        seat_type_value = 9
    elif seat_type == '一等座':
        seat_type_index = 2
        seat_type_value = 'M'
    elif seat_type == '二等座':
        seat_type_index = 3
        seat_type_value = 0
    elif seat_type == '高级软卧':
        seat_type_index = 4
        seat_type_value = 6
    elif seat_type == '软卧':
        seat_type_index = 5
        seat_type_value = 4
    elif seat_type == '动卧':
        seat_type_index = 6
        seat_type_value = 'F'
    elif seat_type == '硬卧':
        seat_type_index = 7
        seat_type_value = 3
    elif seat_type == '软座':
        seat_type_index = 8
        seat_type_value = 2
    elif seat_type == '硬座':
        seat_type_index = 9
        seat_type_value = 1
    elif seat_type == '无座':
        seat_type_index = 10
        seat_type_value = 1
    elif seat_type == '其他':
        seat_type_index = 11
        seat_type_value = 1
    else:
        seat_type_index = 7
        seat_type_value = 3
    return seat_type_index, seat_type_value


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


def get_train_info(index):
    """
    获取列车信息
    :param index: 表格索引
    """
    train_num_id = '#train_num_' + str(index)
    cds = train_num_id + ' > div.cds'
    cdz = train_num_id + ' > div.cdz'

    def text_el(prefix, number):
        return f"{prefix}  > strong:nth-child({number})"

    ss = browser.find_el_if_exist(text_el(cdz, 1)).text
    es = browser.find_el_if_exist(text_el(cdz, 2)).text
    st = browser.find_el_if_exist(text_el(cds, 1)).text
    et = browser.find_el_if_exist(text_el(cds, 2)).text
    du = browser.find_el_if_exist(train_num_id + '> div.ls > strong').text
    return ss, es, st, et, du
