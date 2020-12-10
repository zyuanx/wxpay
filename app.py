from wxpay import *
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify({'code': 0, 'msg': 'success'})


@app.route('/wxpay/pay')
def create_pay():
    """
    请求支付
    https://pay.weixin.qq.com/wiki/doc/api/wxa/wxa_api.php?chapter=9_1&index=1
    :return:
    """
    pay_data = {
        'body': '支付-测试',  # 商品描述
        'attach': '附加数据',  # 附加数据
        'total_fee': '1',  # 订单总金额，单位为分
        'openid': request.args.get('openid') or "o0wGL5cdilBxYCYc_VPKqvJypB1M"

    }
    wxpay = WxPay(pay_data)
    pay_info = wxpay.get_pay_info()
    if pay_info:
        return jsonify(pay_info)
    return jsonify({'code': 40001, 'msg': '请求支付失败'})


@app.route('/wxpay/notify', methods=['POST'])
def notify():
    """
    支付回调通知
    :return:
    """
    if request.method == 'POST':
        result_data = {
            'return_code': 'SUCCESS',
            'return_msg': 'OK'
        }
        return dict_to_order_xml(result_data), {'Content-Type': 'application/xml'}
    else:
        return 'error'


if __name__ == '__main__':
    app.run(debug=True)
