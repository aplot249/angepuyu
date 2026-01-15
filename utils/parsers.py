import json
from rest_framework.parsers import JSONParser,MultiPartParser
from rest_framework.exceptions import ParseError
from .encryption import encryptor


class DecryptJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        try:
            request_body = stream.read().decode('utf-8')
            data_obj = json.loads(request_body)

            # 获取密文
            encrypted_payload = data_obj.get('payload')

            if encrypted_payload:
                # 解密
                decrypted_json_str = encryptor.decrypt(encrypted_payload)
                if decrypted_json_str is None:
                    raise ParseError("Invalid encrypted data")
                return json.loads(decrypted_json_str)

            # 如果没有 payload 字段，尝试按普通 JSON 解析（兼容非加密请求）
            return data_obj

        except Exception as e:
            raise ParseError(f"Decryption failed: {str(e)}")


class DecryptMultiPartParser(MultiPartParser):
    """
    用于 multipart/form-data 文件上传请求
    只解密 formData 中的 payload 字段，文件保持原样
    """

    def parse(self, stream, media_type=None, parser_context=None):
        # 1. 调用父类解析文件和表单
        result = super().parse(stream, media_type, parser_context)

        # result.data 是 QueryDict (不可变)，需要拷贝一份
        data = result.data.copy()

        # 2. 检查并解密 payload 字段
        encrypted_payload = data.get('payload')
        if encrypted_payload:
            try:
                decrypted_json_str = encryptor.decrypt(encrypted_payload)
                if decrypted_json_str:
                    decrypted_data = json.loads(decrypted_json_str)
                    # 将解密出来的字段合并回 data
                    data.update(decrypted_data)
                    # 可选：删除 payload 字段
                    # del data['payload']
            except Exception as e:
                raise ParseError(f"Form data decryption failed: {str(e)}")

        return DataAndFiles(data, result.files)
