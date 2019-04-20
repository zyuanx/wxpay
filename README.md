# wxpay
写在前面：因为要做一个可以报名、缴费与打印准考证的小程序，所以花了两个下午和两个晚上完成了后端的编写与部署（菜鸡一个），生成准考证的代码在末尾开源链接。

一、准备工作
1、商户号：一串数字、需要自行申请，需要一些证明材料

2、小程序ID：已经认证并且加入支付功能，需提前发布以便商户审核通过

3、商户KEY：在商户平台自己设置，MD5 32位加密即可

4、一些参数

    data = {
        'appid': appid,  # 小程序id
        'mch_id': mch_id,  # 商户号
        'attach': attach,  # 附加数据 非必需
        'nonce_str': get_nonce_str(),  # 获取随机字符串
        'body': 'JSAPI-Pay',  # 商品描述
        'out_trade_no': str(int(time.time())),  # 商户订单号
        'total_fee': total_fee,  # 商品价格 以分为单位 整数
        'spbill_create_ip': spbill_create_ip,  # 终端ip 通过 socket 获取
        'notify_url': notify_url,  # 支付结果通知地址
        'trade_type': trade_type,  # 交易类型 小程序为 JSAPI
        'openid': request.args.get('openid')  # 获取请求参数中的用户openid JSAPI支付必须传
    }



 二、签名算法（备注为另一种算法）
官方文档：https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=4_3 

1、首先将所要发送的参数进行 ASCII 码从小到大排序，拼接成url参数形式，如：stringA="appid=wxd930ea5d5a258f4f&body=test&device_info=1000&mch_id=10000100&nonce_str=ibuaiVcKdpRxkhJA"

2、将商户32位key拼接 stringSignTemp=stringA+"&key=192006250b4c09247ec02edce69f6a2d" 

3、MD5加密，并转化为大写

 代码如下
```
def create_sign(self, pay_data):
    stringA = '&'.join(["{0}={1}".format(k, pay_data.get(k)) for k in sorted(pay_data)])
    stringSignTemp = '{0}&key={1}'.format(stringA, self.merchant_key).encode('utf-8')
    sign = hashlib.md5(stringSignTemp).hexdigest()
    return sign.upper()
```
三、拼接XML
```
def dict_to_xml(dict_data):
    xml = ["<xml>"]
    for k, v in dict_data.iteritems():
        xml.append("<{0}>{1}</{0}>".format(k, v))
    xml.append("</xml>")
    return "".join(xml)

xml_data = dict_to_xml(self.pay_data)
response = request(url=self.url, data=xml_data)
```
在使用上述代码进行xml拼接的时候，prepay_id 返回数据为空。通过搜索，发现一种原因是终端 ip 的原因，所以修改为 socket  获取终端 ip ，但是返回数据仍然为空，然后我就猜想是 xml 拼接的问题，索性就用笨方法字符串拼接，然后 format 对 xml字符串中的标识进行值的修改，返回数据成功。
```
def get_pay_info(self):
    # 调用签名函数
    sign = self.create_sign(self.pay_data)
    self.pay_data['sign'] = sign
    # 拼接 XMl
    xmlstr = '<xml>' \
             '<appid>wxbcdbe97d7b353c80</appid>' \
             '<attach>test</attach>' \
             '<body>JSAPI-Pay</body>' \
             '<mch_id>1526671931</mch_id>' \
             '<nonce_str>{nonce_str}</nonce_str>' \
             '<notify_url>https://file.cumtlee.cn/wxpay/notify</notify_url>' \
             '<openid>{openid}</openid>' \
             '<out_trade_no>{out_trade_no}</out_trade_no>' \
             '<spbill_create_ip>{spbill_create_ip}</spbill_create_ip>' \
             '<total_fee>5000</total_fee>' \
             '<trade_type>JSAPI</trade_type>' \
             '<sign>{sign}</sign>' \
             '</xml>'
    xml = xmlstr.format(nonce_str=self.pay_data['nonce_str'],
                        openid=self.pay_data['openid'],
                        out_trade_no=self.pay_data['out_trade_no'],
                        spbill_create_ip=self.pay_data['spbill_create_ip'],
                        sign=self.pay_data['sign'])
    # 统一下单接口请求
    r = requests.post(self.url, data=xml.encode("utf-8"))
    prepay_id = xml_to_dict(r.text).get('prepay_id')
    # 对返回的 xml 解析
    paySign_data = {
        'appId': self.pay_data.get('appid'),
        'timeStamp': self.pay_data.get('out_trade_no'),
        'nonceStr': self.pay_data.get('nonce_str'),
        'package': 'prepay_id={0}'.format(prepay_id),
        'signType': 'MD5'
    }
    # 再次对返回的数据签名
    paySign = self.create_sign(paySign_data)
    paySign_data.pop('appId')
    paySign_data['paySign'] = paySign
    return paySign_data
```
基于开源代码 https://github.com/ilyq/wxpay 进行了适当的修改，在此感谢。

 四、flask服务器部署
 环境配置（宝塔面板为 python2，安装下列环境的时候均改为 pip3 install XXX）

Nginx

VirtualEnv

uwsgi

flask

安装Nginx
pip3 install nginx

安装VirtualEnv
pip3 install virtualenv

 安装完VirtualEnv后，进入自己的项目目录，通过 virtualenv venv（venv可改为任意名字） 建立一个虚拟目录 venv，然后 source venv/bin/activate 进入虚拟环境 SSH终端开始多了  (venv)

安装 uWSGI
pip3 install uwsgi

安装 Flask 
pip3 install flask

 项目文件（例子）
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello World!"

# 文件名 app.py
配置uwsgi
touch uwsgi.ini 新建一个 ini 文件

 配置文件内容

[uwsgi]
master = true
# venv 虚拟目录
home = /www/wwwroot/www.blackcode.club/sql/venv
# 项目文件
wsgi-file = app.py
# 应用的名字 app
callable = app
socket = 127.0.0.1:3000
stats = 127.0.0.1:9191
# 进程信息 进程数量
processes = 4
# 线程信息  线程数量
threads = 4
buffer-size=32768
# 存进程id的文件
pidfile=uwsgi.pid
# 日志文件
daemonize=uwsgi.log
uwsgi --ini uwsgi.ini 启动，会发现目录内生成了 uwsgi.pid 与 wsgi.log 两个文件

可以通过 lsof -i:3000 查看 端口所对应的进程 id ，kill uwsgi.pid 就可以结束相应的进程

 配置Nginx
server {
        charset      utf-8;
        listen       80;
        server_name  119.29.224.165;
        root         /www/wwwroot/www.blackcode.club/sql;

        location / {
				include   uwsgi_params;
           		uwsgi_pass   127.0.0.1:3000;
           		uwsgi_param UWSGI_PYHOME /www/wwwroot/www.blackcode.club/sql/venv;
           		uwsgi_param UWSGI_CHDIR  /www/wwwroot/www.blackcode.club/sql;
        }
}
重载 Nginx 配置、启动 uwsgi 进程
打开 119.29.224.165 就可以发现显示的 hello world。

我的开源 https://github.com/flylzy/wxpay

参考引用 配置搭建阿里云服务器nginx+uwsgi (python) 、wxpay
