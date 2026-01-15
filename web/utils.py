# utils.py
import requests
import json
from django.conf import settings


# 1. 获取 Access Token (建议存入 Redis 或缓存，避免频繁调用)
def get_wechat_access_token():
    appid = settings.APP_ID
    secret = settings.APP_KEY
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"

    response = requests.get(url)
    data = response.json()

    if "access_token" in data:
        return data["access_token"]
    else:
        # 记录日志，处理错误
        print(f"获取 Access Token 失败: {data}")
        return None


# 2. 调用内容安全接口 v2.0
def check_content_safety(openid, content):
    """
    检查文本是否违规
    :param openid: 用户的 openid (必须，v2版本要求)
    :param content: 需要检测的文本
    :return: True (安全), False (违规)
    """
    access_token = get_wechat_access_token()
    if not access_token:
        return False  # 如果拿不到 token，为了安全起见，默认拦截或报错

    url = f"https://api.weixin.qq.com/wxa/msg_sec_check?access_token={access_token}"

    payload = {
        "version": 2,
        "openid": openid,
        "scene": 1,  # 场景值：1-资料 2-评论 3-论坛 4-社交日志
        "content": content
    }

    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        res_data = response.json()

        # 打印日志方便调试
        print(f"微信安全检测结果: {res_data}")

        # 检查 errcode
        if res_data.get("errcode") != 0:
            # 调用出错（如 token 过期等）
            print(f"接口调用出错: {res_data}")
            return False

            # 核心判断逻辑：检查 result.suggest
        # suggest: "pass" (通过), "risky" (有风险), "review" (需人工复审)
        # 审核要求严格，除 "pass" 外一律视为违规
        result = res_data.get("result", {})
        if result.get("suggest") == "pass":
            return True
        else:
            return False

    except Exception as e:
        print(f"检测异常: {e}")
        return False