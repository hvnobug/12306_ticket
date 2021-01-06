# 打码服务器配置
code_server = {
    'host': '12306.yinaoxiong.cn',
    'scheme': 'https',
    'path': '/verify/base64/'
}

# 邮箱配置 暂不支持
mail = {
    "enable": False
}

# Server酱 http://sc.ftqq.com/3.version
ftqq_server = {
    "enable": False,
    "sckey": ""
}

# 出发时间
from_time = '2021-01-22'
# 选择车次
trains = ['G412']
# 选择座位
seat_types = ["一等座", "二等座"]
# 选择乘坐人
passengers = ['XXX']
# 12306 用户名
username = '131xxx12345'
# 12306 密码
password = 'abc123'
# 出发地
from_station = '上海'
# 目的地
to_station = '北京'

# 开始售票时间
start_time = '05:00:00'
# 停止售票时间
end_time = '23:00:00'
# ChromeDriver 运行路径
CHROME_PATH = 'D:\\chromedriver.exe'
