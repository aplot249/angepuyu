"""tongchengQyApi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import re_path, path

from .views import *

urlpatterns = [
    re_path("^openid/$", OpenIDLogin.as_view()),  # 微信授权登录的
    re_path("^userinfo/$", EditInfo.as_view({'post': 'partial_update'})),  # 用户更改密码，和订阅通知时，获取到openID并入库
    re_path("^setuser/$", SetUser.as_view()),  # 微信授权登录的
    path('price/', PriceListView.as_view({'get': 'list'})),
    path('pay/', createPayOrder.as_view(), name='create_pay_order'),  # 支付订单
    path('pay/notify/', PaymentNotifyView.as_view(), name='pay_notify'),  # 订单回调通知地址，只有微信调用
    re_path('transcation/(?P<prepay_id>.*)/$', TranscationView.as_view({'get': 'retrieve'}), name='transcation'),
    path('scorerecord/', ScoreRecordView.as_view({'post': 'create'})),
    path('updatepoints/', UpdatePoints.as_view()),
]
