from django.core.management.base import BaseCommand
from django.conf import settings
from cryptography.fernet import Fernet
from reservations.models import Customer, Pet
import base64

'''
1. 먼저 새로운 암호화 키를 생성합니다:
  - python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
2. 기존 데이터를 새로운 키로 재암호화합니다:
  - python manage.py reencrypt_data --old-key [기존_키] --new-key [새로운_키]
3. .env 파일의 ENCRYPTION_KEY를 새로운 키로 업데이트합니다.
4. 서버를 재시작합니다.

주의사항:
1. 키 변경 전에 반드시 데이터베이스를 백업해두세요.
2. 키 변경 작업은 서비스 중단 시간에 수행하는 것이 좋습니다.
3. 기존 키는 재암호화가 완료될 때까지 안전하게 보관해야 합니다.
4. 재암호화 작업이 실패할 경우를 대비해 롤백 계획을 세워두세요.
'''
class Command(BaseCommand):
    help = '기존 데이터를 새로운 키로 재암호화합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--old-key', type=str, required=True, help='기존 암호화 키')
        parser.add_argument('--new-key', type=str, required=True, help='새로운 암호화 키')

    def handle(self, *args, **options):
        old_key = options['old_key'].encode()
        new_key = options['new_key'].encode()

        old_fernet = Fernet(old_key)
        new_fernet = Fernet(new_key)

        self.stdout.write('데이터 재암호화를 시작합니다...')

        # Customer 모델 데이터 재암호화
        for customer in Customer.objects.all():
            try:
                # 기존 암호화된 데이터 가져오기
                encrypted_name = base64.b64decode(customer.name)
                encrypted_phone = base64.b64decode(customer.phone)
                encrypted_email = base64.b64decode(customer.email) if customer.email else None
                encrypted_address = base64.b64decode(customer.address) if customer.address else None

                # 기존 키로 복호화
                name = old_fernet.decrypt(encrypted_name).decode()
                phone = old_fernet.decrypt(encrypted_phone).decode()
                email = old_fernet.decrypt(encrypted_email).decode() if encrypted_email else ''
                address = old_fernet.decrypt(encrypted_address).decode() if encrypted_address else ''

                # 새 키로 암호화
                customer.name = base64.b64encode(new_fernet.encrypt(name.encode())).decode()
                customer.phone = base64.b64encode(new_fernet.encrypt(phone.encode())).decode()
                if email:
                    customer.email = base64.b64encode(new_fernet.encrypt(email.encode())).decode()
                if address:
                    customer.address = base64.b64encode(new_fernet.encrypt(address.encode())).decode()

                customer.save()
                self.stdout.write(f'고객 ID {customer.id} 재암호화 완료')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'고객 ID {customer.id} 처리 중 오류: {str(e)}'))

        # Pet 모델 데이터 재암호화
        for pet in Pet.objects.all():
            try:
                # 기존 암호화된 데이터 가져오기
                encrypted_name = base64.b64decode(pet.name)
                encrypted_species = base64.b64decode(pet.species) if pet.species else None
                encrypted_breed = base64.b64decode(pet.breed) if pet.breed else None

                # 기존 키로 복호화
                name = old_fernet.decrypt(encrypted_name).decode()
                species = old_fernet.decrypt(encrypted_species).decode() if encrypted_species else ''
                breed = old_fernet.decrypt(encrypted_breed).decode() if encrypted_breed else ''

                # 새 키로 암호화
                pet.name = base64.b64encode(new_fernet.encrypt(name.encode())).decode()
                if species:
                    pet.species = base64.b64encode(new_fernet.encrypt(species.encode())).decode()
                if breed:
                    pet.breed = base64.b64encode(new_fernet.encrypt(breed.encode())).decode()

                pet.save()
                self.stdout.write(f'반려동물 ID {pet.id} 재암호화 완료')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'반려동물 ID {pet.id} 처리 중 오류: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('모든 데이터 재암호화가 완료되었습니다.')) 