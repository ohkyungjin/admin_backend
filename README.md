# CIELO PET 관리자 도구 백엔드

CIELO PET의 관리자 도구를 위한 Django 기반 백엔드 API 서버입니다.

## 기능

- 사용자 관리 (계정, 권한)
- 재고 관리
  - 카테고리
  - 공급업체
  - 재고 항목
  - 재고 이동
  - 발주 관리

## 기술 스택

- Python 3.x
- Django
- Django REST Framework
- Simple JWT (인증)
- SQLite (개발용 DB)

## 설치 방법

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

4. 개발 서버 실행
```bash
python manage.py runserver
```

## API 문서

주요 API 엔드포인트:

### 인증
- POST /api/v1/accounts/token/: 로그인 (토큰 발급)
- POST /api/v1/accounts/token/refresh/: 토큰 갱신
- POST /api/v1/accounts/token/verify/: 토큰 검증

### 사용자 관리
- GET /api/v1/accounts/users/: 사용자 목록
- POST /api/v1/accounts/users/: 사용자 생성
- GET /api/v1/accounts/users/{id}/: 사용자 상세
- PUT /api/v1/accounts/users/{id}/: 사용자 수정
- DELETE /api/v1/accounts/users/{id}/: 사용자 삭제
- POST /api/v1/accounts/users/{id}/change-password/: 비밀번호 변경

### 재고 관리
- GET /api/v1/inventory/items/: 재고 항목 목록
- GET /api/v1/inventory/items/low-stock/: 최소 재고 이하 항목
- POST /api/v1/inventory/items/{id}/adjust-stock/: 재고 수량 조정

### 발주 관리
- GET /api/v1/inventory/orders/: 발주서 목록
- POST /api/v1/inventory/orders/{id}/approve/: 발주서 승인
- POST /api/v1/inventory/orders/{id}/receive/: 발주 입고 처리
- POST /api/v1/inventory/orders/{id}/cancel/: 발주서 취소
