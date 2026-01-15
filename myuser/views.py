from datetime import timedelta
import hashlib
import requests
from django.conf import settings
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import requests
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from django.views.decorators.csrf import csrf_exempt

from rest_framework import status  # 导入状态
from rest_framework.filters import SearchFilter
from rest_framework.mixins import UpdateModelMixin, CreateModelMixin
from rest_framework.parsers import MultiPartParser  # 文件上传解析
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response  # 返回响应
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin, \
    ListModelMixin
from .authentications import JWTAuthentication
from .authentications import generate_jwt
from .models import *
from .serializers import *

from django.http.response import JsonResponse
from django.http import HttpResponse
from django.conf import settings
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import requests
import base64
import hashlib
from datetime import datetime, timedelta, timezone
import random
import time
import json
import string
from web.models import Sublingyu
# from django.utils.timezone import now
from django.utils import timezone


# 微信授权登录
class OpenIDLogin(APIView):
    def post(self, request):
        url = "https://api.weixin.qq.com/sns/jscode2session?appid={0}&secret={1}&js_code={2}&grant_type=authorization_code" \
            .format(settings.APP_ID, settings.APP_KEY, request.data['code'])
        r = requests.get(url, verify=False)
        # r = requests.get(url, verify=True)
        openid = r.json()['openid']
        # avatarUrl = request.data.get('avatarUrl')  # 获取前端口传来的头像
        # gender = request.data.get('gender')
        # nickname = openid[-5:] if request.data.get('nickName') == '微信用户' else request.data.get('nickName')
        user, created = UserProfile.objects.update_or_create(openid=openid, defaults={
            # "avatarUrl": avatarUrl,
            # "nickname": openid[-5:],
            "username": openid,
            "password": openid
        })

        exists = UserLoginRecordModel.objects.filter(user__nickname=user,
                                                     login_day=timezone.localtime(timezone.now()).date()).exists()
        print('.exists', exists, 'login_day', timezone.localtime(timezone.now()).date())
        # 每次登录做一下记录
        UserLoginRecordModel.objects.create(user=user)
        if created:
            data = Sublingyu.objects.filter(isTiku=True)
            # 默认分配
            [MyFavoritCat.objects.update_or_create(user=user, sublingyu=i, favAllItem=True, defaults={}) for i in data]
            # [MyFavoritCat.objects.create(user=user, sublingyu=i,favAllItem=True) for i in data]
        todayFirstLogin = True
        # 非会员，并且是当天的第一次登录
        if not user.isvip and not exists:  # 如果没有 买 过会员，加上判断日期，每天只能领取一次的逻辑，一天多次登录，后面登录的次数不给分配，只给当天第一次分配
            count = UserLoginRecordModel.objects.filter(user__nickname=user).count()
            if count >= 2:
                user.points = 30  # 如果没有买过就只给50
            elif count < 2:
                user.points = 100  # 如果没有买过就只给50
            user.save()
        # print("user：", user.avatarUrl, created)
        serializer = UserProfileSerializer(user)
        token = generate_jwt(user)
        return Response(
            {"user": serializer.data, "token": token, 'created': created, 'status': status.HTTP_202_ACCEPTED})


class SetUser(APIView):
    def get(self, request):
        UserProfile.objects.filter(points__gt=5000).update(isvip=True)
        return Response({'status': status.HTTP_202_ACCEPTED})


# 编辑个人资料的接口
class EditInfo(GenericViewSet, UpdateModelMixin):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer

    def get_parsers(self):
        print("self.request.POST:", self.request.POST)
        # 如果用户名在传来的键里
        if 'username' in dict(self.request.POST).keys():
            self.parser_classes = (MultiPartParser,)
        return super(EditInfo, self).get_parsers()

    # def create(self, request, *args, **kwargs):
    #     return super(EditInfo, self).partial_update(request, *args, **kwargs)

    # def update(self, request, *args, **kwargs):
    #     # print(request.data,dict(request.data).keys())
    #     partial = kwargs.pop('partial', False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     # print("serializer.validated_data：", serializer.validated_data)
    #     if request.data['type'] == 'openid':
    #         code = request.data['code']
    #         url = "https://api.weixin.qq.com/sns/jscode2session?appid={0}&secret={1}&js_code={2}&grant_type=authorization_code" \
    #             .format(settings.APP_ID, settings.APP_KEY, code)
    #         r = requests.get(url, verify=False)
    #         openid = r.json()['openid']
    #         print("openid", openid)
    #         user = request.user
    #         user.openid = openid
    #         user.save()
    #     else:
    #         self.perform_update(serializer)
    #     if getattr(instance, '_prefetched_objects_cache', None):
    #         instance._prefetched_objects_cache = {}
    #     return Response(serializer.data)

    def get_object(self):
        return self.request.user


class CustomSearchFilter(SearchFilter):
    def get_search_fields(self, view, request):
        print("request.query_params", request.query_params)
        return super(CustomSearchFilter, self).get_search_fields(view, request)


class Valid(APIView):
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        # 解析参数
        data = request.GET
        # Flask	from flask import request
        # data = request.args
        if len(data) == 0:
            return HttpResponse(content="hello, this is WeChat view")
        signature = data.get(key='signature', default='')
        timestamp = data.get(key='timestamp', default='')
        nonce = data.get(key='nonce', default='')
        echostr = data.get(key='echostr', default='')
        # 请按照公众平台官网\基本配置中信息填写
        token = "qwertyuiop123"

        list_para = [token, timestamp, nonce]
        list_para.sort()
        list_str = ''.join(list_para).encode('utf-8')

        sha1 = hashlib.sha1()
        sha1.update(list_str)
        # map(sha1.update, list_para)
        # 加密
        hashcode = sha1.hexdigest()
        print("/GET func: hashcode: {0}, signature: {1}".format(hashcode, signature))

        if hashcode == signature:
            return HttpResponse(content=echostr)
        else:
            return HttpResponse(content='验证失败')


class PriceListView(GenericViewSet, ListModelMixin):
    # authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAuthenticated,)
    serializer_class = HuiYuanTypeSerializer
    queryset = HuiYuanType.objects.all()


# 示例辅助函数
def generate_nonce_str(length=32):
    """生成随机字符串[citation:2]"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_signature(sign_string):
    """使用商户私钥对字符串进行签名[citation:2]"""
    private_key_path = settings.WECHAT_PAY['KEY_PATH']
    with open(private_key_path, 'rb') as f:
        private_key_data = f.read()
    private_key = serialization.load_pem_private_key(private_key_data, password=None)
    signature = private_key.sign(sign_string.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode('utf-8')


# def get_user_info(code):
#     """使用 code 获取用户 openid[citation:1]"""
#     req_params = {
#         'appid': settings.WECHAT_PAY['APPID'],
#         'secret': settings.WECHAT_PAY['APPSECRET'],
#         'js_code': code,
#         'grant_type': 'authorization_code',
#     }
#     user_info = requests.get('https://api.weixin.qq.com/sns/jscode2session', params=req_params, timeout=3, verify=False)
#     return user_info.json()


# 支付视图
class createPayOrder(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        price = request.data["price"]
        title = request.data["title"]

        openid = request.user.openid
        # 生成商户订单号（根据自己业务需要生成）
        order_id = str(int(time.time()))

        # 构造请求参数（V3接口）[citation:2]
        url = "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"
        wechat_config = settings.WECHAT_PAY
        timestamp = str(int(time.time()))
        nonce_str = generate_nonce_str()

        params = {
            "appid": wechat_config["APPID"],
            "mchid": wechat_config['MCHID'],
            "out_trade_no": order_id,
            "description": '无限积分，永久使用' if int(title.split("#")[-1]) > 10000 else title,
            "notify_url": wechat_config['NOTIFY_URL'],
            "amount": {
                "total": price * 100,  # 金额，单位：分
                "currency": "CNY"
            },
            "payer": {
                "openid": openid
            }
        }

        params_str = json.dumps(params, separators=(',', ':'))

        # 构造签名（示例，具体格式请严格参照微信官方文档）[citation:2]
        sign_str = f"POST\n/v3/pay/transactions/jsapi\n{timestamp}\n{nonce_str}\n{params_str}\n"
        signature = generate_signature(sign_str)

        # 生成请求头 Authorization
        authorization_header = f'WECHATPAY2-SHA256-RSA2048 mchid="{wechat_config["MCHID"]}",nonce_str="{nonce_str}",signature="{signature}",serial_no="{wechat_config["CERT_SERIAL"]}",timestamp="{timestamp}"'
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": authorization_header,
        }

        # 调用微信统一下单接口[citation:2]
        response = requests.post(url, data=params_str, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and 'prepay_id' in response_data:
            prepay_id = response_data['prepay_id']

            transcation, created = TranscationManage.objects.update_or_create(out_trade_no=params["out_trade_no"],
                                                                              defaults={
                                                                                  "user": request.user,
                                                                                  "title": title,
                                                                                  "price": price,
                                                                                  "prepay_id": prepay_id
                                                                              })
            print(transcation, created)
            # request.user.points = request.user.points + points
            # request.user.save()
            # 构造小程序端所需支付参数
            pay_params = {
                "timeStamp": timestamp,
                "nonceStr": nonce_str,
                "prepay_id": prepay_id,
                "package": f"prepay_id={prepay_id}",
                "signType": "RSA",
            }
            # 对支付参数再次签名（小程序端调起支付时使用）[citation:2]
            pay_sign_str = f"{wechat_config['APPID']}\n{timestamp}\n{nonce_str}\n{pay_params['package']}\n"
            pay_params['paySign'] = generate_signature(pay_sign_str)
            # return HttpResponse(json.dumps({"code": 0, "payment": pay_params}))
            return Response({"code": 0, "payment": pay_params})
        else:
            # return HttpResponse(json.dumps({"code": -1, "message": "支付订单创建失败", "error": response_data}))
            return Response({"code": -1, "message": "支付订单创建失败", "error": response_data})


@method_decorator(csrf_exempt, name='dispatch')
class PaymentNotifyView(View):
    """处理微信支付 V3 API 的异步通知"""

    def post(self, request):
        try:
            # 1. 验证签名 (省略：生产环境中需严格验证 request.headers 中的 Wechatpay-Signature)
            # 在生产环境中，您需要获取微信平台证书，并用证书公钥验证签名。
            # 为简化示例，这里跳过签名验证，但在实际应用中这是**强制要求**的安全步骤。
            print("注意：此处跳过了微信通知签名验证，请在生产环境中使用官方SDK或完整代码进行验证！")

            # 2. 解析通知数据
            notify_data = json.loads(request.body.decode('utf-8'))
            # print(notify_data)
            resource_data = notify_data.get('resource', {})
            # print(resource_data)

            # 3. 解密数据
            nonce = resource_data.get('nonce')
            ciphertext = resource_data.get('ciphertext')
            associated_data = resource_data.get('associated_data')

            if not all([nonce, ciphertext, associated_data]):
                return self.error_response('通知数据格式错误')

            # print(nonce, ciphertext, associated_data)
            # decrypted_data_json = decrypt_notification_resource(
            #     nonce, ciphertext, associated_data
            # )
            wechat_config = settings.WECHAT_PAY

            key = wechat_config['API_V3_KEY']
            key_bytes = str.encode(key)
            nonce_bytes = str.encode(nonce)
            ad_bytes = str.encode(associated_data)
            data = base64.b64decode(ciphertext)
            aesgcm = AESGCM(key_bytes)

            plaintext = aesgcm.decrypt(nonce_bytes, data, ad_bytes)
            decrypted_data_json = plaintext
            if not decrypted_data_json:
                return self.error_response('解密通知数据失败')

            transaction = json.loads(decrypted_data_json)
            print(transaction)
            # 4. 处理业务逻辑
            trade_state = transaction.get('trade_state')
            out_trade_no = transaction.get('out_trade_no')
            transaction_id = transaction.get('transaction_id')
            total_fee = transaction.get('amount', {}).get('total')
            print(f"微信交易号: {transaction_id}")

            TranscationManage.objects.filter(out_trade_no=out_trade_no).update(status='1',
                                                                               transaction_id=transaction_id)
            print(f"=== 收到订单通知 ===")
            print(f"商户订单号: {out_trade_no}")
            print(f"微信交易号: {transaction_id}")
            print(f"支付状态: {trade_state}")
            print(f"支付金额: {total_fee / 100} 元")

            # 5. 根据支付状态更新数据库中的订单
            if trade_state == 'SUCCESS':
                # 实际业务中：
                # 检查订单是否存在
                # 检查金额是否匹配 (total_fee == 订单金额)
                # 检查订单状态是否为未支付
                # 更新订单状态为已支付
                # 发放商品/服务等
                print(f"订单 {out_trade_no} 支付成功，已更新数据库状态。")

                # 6. 返回成功响应
                return self.success_response()

            # 如果是其他状态（如 REFUND、NOTPAY 等，根据业务决定是否处理）
            print(f"订单状态非成功: {trade_state}")
            return self.success_response()  # 非成功状态也要返回成功，避免微信重发

        except json.JSONDecodeError:
            return self.error_response('请求体解析错误')
        except Exception as e:
            print(f"处理通知请求时发生错误: {e}")
            return self.error_response(f'服务器处理错误: {e}')

    def success_response(self):
        """返回给微信的成功响应 (HTTP 200 OK)"""
        return JsonResponse({
            'code': 'SUCCESS',
            'message': '成功'
        }, status=200)
        # return Response({
        #     'code': 'SUCCESS',
        #     'message': '成功'
        # })

    def error_response(self, message):
        """返回给微信的失败响应 (HTTP 500)"""
        print(f"通知处理失败，返回错误码: {message}")
        return JsonResponse({
            'code': 'FAIL',
            'message': message
        }, status=500)
        # return Response({
        #     'code': 'FAIL',
        #     'message': message
        # })


class TranscationView(GenericViewSet, RetrieveModelMixin):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = TranscationManage.objects.all()
    serializer_class = TranscationManageSerializer
    lookup_field = 'prepay_id'


class ScoreRecordView(GenericViewSet, CreateModelMixin):
    queryset = ScoreRecordModel.objects.all()
    serializer_class = ScoreRecordSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# 这是给会员用户调整积分的方法
class UpdatePoints(APIView):
    def get(self, request):
        UserProfile.objects.filter(isvip=True).update(points=999999)
        return Response({'status': 'ok'})
