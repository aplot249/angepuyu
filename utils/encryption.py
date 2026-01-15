import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from django.conf import settings


# 在 settings.py 中定义:
# AES_SECRET_KEY = '1234567890123456'  # 必须是 16, 24 或 32 字节长度
# 注意：生产环境中，建议密钥不要硬编码，或者每个用户登录后分配独立的 SessionKey

class AESCipher:
    # key ， mode ,bs
    def __init__(self):
        self.key = getattr(settings, 'AES_SECRET_KEY', '').encode('utf-8')
        if len(self.key) not in (16, 24, 32):
            raise ValueError("AES key must be either 16, 24, or 32 bytes long")
        self.mode = AES.MODE_CBC
        self.bs = AES.block_size  # 通常是 16

    def encrypt(self, text):
        """
        加密: 生成随机 IV -> 加密 -> 拼接 IV 和密文 -> Base64 编码
        """
        if isinstance(text, str):
            text = text.encode('utf-8')

        # 1. 生成随机 IV (16字节)
        cipher = AES.new(self.key, self.mode)
        iv = cipher.iv

        # 2. 填充并加密
        encrypted_bytes = cipher.encrypt(pad(text, self.bs))

        # 3. 拼接 IV + 密文 并转为 Base64
        return base64.b64encode(iv + encrypted_bytes).decode('utf-8')

    def decrypt(self, text):
        """
        解密: Base64 解码 -> 提取 IV -> 解密 -> 去除填充
        """
        if not text:
            return None

        try:
            # 1. Base64 解码
            decoded_data = base64.b64decode(text)

            # 2. 提取 IV (前16字节) 和 密文
            iv = decoded_data[:16]
            encrypted_bytes = decoded_data[16:]

            # 3. 解密
            cipher = AES.new(self.key, self.mode, iv)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), self.bs)

            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            # 生产环境建议 log 错误，返回 None 或抛出特定异常
            print(f"Decryption error: {e}")
            return None


encryptor = AESCipher()
