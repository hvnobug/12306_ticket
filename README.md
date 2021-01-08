## Selenium 12306 自动抢票

### Python版本支持
  - [x] 3.6 - 3.8
  - [ ] 2.7.x

### 特性
  - [x] 自动打码
  - [x] 自动登录
  - [x] 准点预售和捡漏
  - [ ] 智能候补
  - [x] 邮件通知
  - [x] server酱通知
  
### 安装

> 目前只测试过 `windows`,`linux`和`macos`没有测试过


#### ChromeDriver

`ChromeDriver`[下载地址](https://npm.taobao.org/mirrors/chromedriver/)

> 跟 `Chrome` 大版本保持一致即可

#### pip依赖

```bash
pip install -r requirement.txt
```

#### 修改配置文件

> 将 config_example.py 复制为 config.py

```python
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
chrome_path = 'D:\\chromedriver.exe'
```

#### 运行 main.py

```bash
python main.py
```

### 打码服务器

> 默认使用 [12306_code_server](https://github.com/YinAoXiong/12306_code_server) 提供的云打码服务器

也可以自建打码服务器,可以使用 `docker` 或 `docker-compose` 方式部署:

#### Docker 部署

```bash
docker run -d -p 8080:80 --name 12306 yinaoxiong/12306_code_server
```

#### docker-compose 部署

```yaml
version: "3"

services:
  code_12306:
    image: yinaoxiong/12306_code_server
    ports:
      - 5002:80 #可以根据需要修改端口
    environment:
      - WORKERS=1 #gunicorn works 默认为1可以根据服务器配置自行调整
    restart: always
```

然后修改 `config.py` 的 `code_server` 配置项

### 运行截图

![](https://github.com/hvnobug/12306_ticket/blob/master/images/12306_ticket_screenshot.png?raw=true)

### 鸣谢

* [12306](https://github.com/gzldc/12306): 12306抢票脚本
* [12306_code_server](https://github.com/YinAoXiong/12306_code_server): 自托管的12306验证码识别服务

### License

[MIT](https://github.com/hvnobug/12306_ticket/blob/master/LICENSE)