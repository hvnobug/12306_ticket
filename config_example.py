# 打码服务器配置
code_server = {
    'host': '12306.yinaoxiong.cn',
    'scheme': 'https',
    'path': '/verify/base64/'
}

#  邮箱配置，如果抢票成功，将通过邮件配置通知给您
#  列举163
#  "sender": "xxx@163.com"
#  "receivers": ["123@qq.com"]
#  "username": "xxx"
#  "password": "xxx
#  "host": "smtp.163.com"
#  列举qq  , qq设置比较复杂，需要在邮箱-->账户-->开启smtp服务，取得授权码 == 邮箱登录密码
#  "sender": "xxx@qq.com"
#  "receivers": ["123@qq.com"]
#  "username": "xxx"
#  "password": "授权码"
#  "host": "smtp.qq.com"

email = {
    # 是否开启邮箱通知
    "enable": False,
    "sender": "xx@qq.com",
    "receivers": ["xx@136.com"],
    "username": "xxx",
    "password": "xxx",
    "host": "smtp.qq.com"
}

# Server酱 使用前需要前往 http://sc.ftqq.com/3.version 扫码绑定获取 SECRET 并关注获得抢票结果通知的公众号
server_chan = {
    # 是否开启 server酱 微信提醒
    "enable": False,
    "secret": ""
}

# 出发时间
from_time = '2021-01-22'
# 选择车次
trains = ['G412']
# 选择座位
seat_types = ["一等座", "二等座"]
# 选择乘坐人
passengers = ['张三']
# 12306 用户名
username = '131xxx12345'
# 12306 密码
password = '123456'
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
