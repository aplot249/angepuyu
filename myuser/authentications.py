import time
import platform
import jwt
from django.contrib.auth import get_user_model
from jwt.exceptions import ExpiredSignatureError
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from tantansiyu.settings import SECRET_KEY

User = get_user_model()


def generate_jwt(user):
    if platform.system() in ["Windows", "Darwin"]:
        # EXPIREDTIME = time.time() + 60 * 60 * 5 # 1小时
        # EXPIREDTIME = time.time() + 60  # 1分钟
        EXPIREDTIME = time.time() + 60 * 60 * 2  # 2小时
    else:
        # EXPIREDTIME = time.time() + 60 * 60 * 24 * 1  # 7天
        EXPIREDTIME = time.time() + 60 * 60 * 12 * 1  # 7天
    # expire_time = time.time() + 60 * 60 * 24 * 7
    expire_time = EXPIREDTIME
    return jwt.encode({"userid": user.pk, "exp": expire_time}, key=SECRET_KEY)


class JWTAuthentication(BaseAuthentication):
    keyword = 'JWT'

    def authenticate(self, request):
        print(request)
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = "不可用的JWT请求头！"
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = '不可用的JWT请求头！JWT Token中间不应该有空格！'
            raise exceptions.AuthenticationFailed(msg)
        try:
            jwt_token = auth[1]
            jwt_info = jwt.decode(jwt_token, SECRET_KEY, algorithms='HS256')
            userid = jwt_info.get('userid')
            try:
                # 绑定当前user到request对象上
                user = User.objects.get(pk=userid)
                return user, jwt_token
            except:
                msg = '用户不存在！'
                raise exceptions.AuthenticationFailed(msg)
        except ExpiredSignatureError:
            msg = "JWT Token已过期！"
            raise exceptions.AuthenticationFailed(msg)
