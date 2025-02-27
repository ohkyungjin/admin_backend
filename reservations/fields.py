from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64

class EncryptedField:
    """
    Django 모델 필드를 위한 암호화 Mixin
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # settings.py에서 ENCRYPTION_KEY를 가져옵니다.
        # 키가 없으면 새로 생성합니다.
        if not hasattr(settings, 'ENCRYPTION_KEY'):
            key = Fernet.generate_key()
            setattr(settings, 'ENCRYPTION_KEY', key)
        self.fernet = Fernet(settings.ENCRYPTION_KEY)

    def get_prep_value(self, value):
        # 데이터베이스에 저장하기 전에 암호화
        if value is None:
            return value
        value = super().get_prep_value(value)
        encrypted = self.fernet.encrypt(str(value).encode())
        return base64.b64encode(encrypted).decode()

    def from_db_value(self, value, expression, connection):
        # 데이터베이스에서 읽을 때 복호화
        if value is None:
            return value
        try:
            decrypted = self.fernet.decrypt(base64.b64decode(value))
            return decrypted.decode()
        except Exception:
            return None

class EncryptedCharField(EncryptedField, models.CharField):
    pass

class EncryptedTextField(EncryptedField, models.TextField):
    pass

class EncryptedEmailField(EncryptedField, models.EmailField):
    pass 