# CIELO PET 관리자 시스템

반려동물 장례 서비스 관리 시스템의 백엔드 API 서버입니다.

## 기술 스택

- Python 3.9+
- Django 5.1
- Django REST Framework
- SQLite3 (개발용)
- JWT Authentication
- CORS 지원

## 주요 기능

### 1. 예약 관리
- 장례 예약 생성/조회/수정/취소
- 예약 상태 관리 (대기/확정/진행중/완료/취소)
- 긴급 예약 처리
- 예약 이력 관리

### 2. 추모실 관리
- 추모실 현황 조회
- 예약 가능 시간 조회
- 추모실 배정 관리

### 3. 대시보드
- 실시간 예약 현황
- 추모실 사용 현황
- 직원 배정 현황
- 통계 데이터 제공

### 4. 직원 관리
- 직원 계정 관리
- 권한 관리
- 업무 배정 관리

## 설치 및 실행

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 수정
```

4. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

5. 개발 서버 실행
```bash
python manage.py runserver
```

## API 문서

### 예약 관리 API
- [예약 API 문서](docs/reservation_api.md)
- [추모실 API 문서](docs/memorial_room_api.md)

### 대시보드 API
- [대시보드 API 문서](docs/dashboard_api.md)

### 인증 API
- [인증 API 문서](docs/auth_api.md)

## 개발 가이드

### 코드 스타일
- PEP 8 준수
- Black 포맷터 사용
- isort로 import 정렬

### 브랜치 전략
- main: 프로덕션 브랜치
- develop: 개발 브랜치
- feature/*: 기능 개발
- hotfix/*: 긴급 수정

### 커밋 메시지 컨벤션
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드
chore: 기타 변경사항
```

## 테스트

```bash
# 전체 테스트 실행
python manage.py test

# 특정 앱 테스트
python manage.py test reservations

# 커버리지 리포트 생성
coverage run manage.py test
coverage report
```

## 배포

### 요구사항
- Python 3.9+
- PostgreSQL (프로덕션용)
- Redis (캐싱용)
- Nginx
- Gunicorn

### 배포 절차
1. 프로덕션 설정 적용
2. 정적 파일 수집
3. 데이터베이스 마이그레이션
4. Gunicorn 설정
5. Nginx 설정
6. SSL 인증서 설정

자세한 배포 가이드는 [deployment.md](docs/deployment.md)를 참조하세요.

## 모니터링

- Sentry: 에러 트래킹
- Prometheus: 메트릭 수집
- Grafana: 대시보드 시각화

## 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여 가이드

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 문의

- 이메일: support@cielopet.com
- 이슈 트래커: GitHub Issues
