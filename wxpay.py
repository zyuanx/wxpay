import uuid
import hashlib
import xml.etree.ElementTree as ET
import requests


def get_nonce_str():
    '''
    获取随机字符串
    :return:
    '''
    return str(uuid.uuid4()).replace('-', '')


def dict_to_xml(dict_data):
    '''
    dict to xml
    :param dict_data:
    :return:
    '''
    xml = ["<xml>"]
    for k, v in dict_data.items():
        xml.append("<{0}>{1}</{0}>".format(k, v))
    xml.append("</xml>")
    return "".join(xml)


def xml_to_dict(xml_data):
    '''
    xml to dict
    :param xml_data:
    :return:
    '''
    xml_dict = {}
    root = ET.fromstring(xml_data)
    for child in root:
        xml_dict[child.tag] = child.text
    return xml_dict


class WxPay(object):

    def __init__(self, merchant_key, kwargs):
        self.url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
        self.merchant_key = merchant_key
        self.pay_data = kwargs

    def create_sign(self, pay_data):
        '''
        生成签名
        :return:
        '''
        '''生成签名'''
        stringA = ''
        # ks = sorted(pay_data.keys())
        # 参数排序
        # for k in ks:
        #     stringA += (k + '=' + pay_data[k] + '&')
        # # 拼接商户KEY
        # stringSignTemp = stringA + "key=" + self.merchant_key
        # md5加密，也可以用其他方式
        # hash_md5 = hashlib.md5(stringSignTemp.encode('utf8'))
        # sign = hash_md5.hexdigest().upper()
        # return sign

        stringA = '&'.join(["{0}={1}".format(k, pay_data.get(k)) for k in sorted(pay_data)])
        stringSignTemp = '{0}&key={1}'.format(stringA, self.merchant_key).encode('utf-8')
        sign = hashlib.md5(stringSignTemp).hexdigest()
        return sign.upper()

    def get_pay_info(self):
        '''
        获取支付信息
        :param xml_data:
        :return:
        '''
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
