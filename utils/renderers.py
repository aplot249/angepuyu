import json
from rest_framework.renderers import JSONRenderer
from .encryption import encryptor


class EncryptJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # 渲染原始数据为 JSON 字符串
        json_data = super().render(data, accepted_media_type, renderer_context)

        # 视情况决定是否加密（例如 debug 模式不加密，或只加密特定状态码）
        # 这里演示默认全部加密

        encrypted_data = encryptor.encrypt(json_data.decode('utf-8'))
        # print('1111111111111',json_data)
        # 包装统一格式
        response_data = {
            "payload": encrypted_data
        }

        return json.dumps(response_data).encode('utf-8')
