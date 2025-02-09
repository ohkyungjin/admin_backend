# 예약 관리 API 명세서

## Base URL
```
http://localhost:8000/api/v1
```

## 공통 헤더
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

## 요청 파라미터 포맷

### 1. Customer (고객 정보)
```json
{
    "name": {
        "type": "string",
        "required": true,
        "max_length": 100,
        "description": "고객명"
    },
    "phone": {
        "type": "string",
        "required": true,
        "max_length": 20,
        "format": "000-0000-0000",
        "description": "전화번호"
    },
    "email": {
        "type": "string",
        "required": false,
        "max_length": 254,
        "format": "email",
        "description": "이메일"
    },
    "address": {
        "type": "string",
        "required": false,
        "description": "주소"
    }
}
```

### 2. Pet (반려동물 정보)
```json
{
    "name": {
        "type": "string",
        "required": true,
        "max_length": 100,
        "description": "반려동물명"
    },
    "species": {
        "type": "string",
        "required": false,
        "max_length": 50,
        "description": "종"
    },
    "breed": {
        "type": "string",
        "required": false,
        "max_length": 100,
        "description": "품종"
    },
    "age": {
        "type": "integer",
        "required": false,
        "min": 0,
        "description": "나이"
    },
    "weight": {
        "type": "decimal",
        "required": false,
        "max_digits": 5,
        "decimal_places": 2,
        "description": "체중 (kg)"
    },
    "gender": {
        "type": "string",
        "required": false,
        "choices": ["male", "female"],
        "description": "성별"
    },
    "is_neutered": {
        "type": "boolean",
        "required": false,
        "default": false,
        "description": "중성화 여부"
    },
    "death_date": {
        "type": "datetime",
        "required": false,
        "format": "YYYY-MM-DDThh:mm:ss±hh:mm",
        "description": "사망일시"
    },
    "death_reason": {
        "type": "string",
        "required": false,
        "choices": ["natural", "disease", "accident", "euthanasia", "other"],
        "description": "사망사유"
    },
    "special_notes": {
        "type": "string",
        "required": false,
        "description": "특이사항"
    }
}
```

### 3. Reservation (예약 정보)
```json
{
    "customer": {
        "type": "object",
        "required": true,
        "description": "고객 정보",
        "properties": "Customer 객체 참조"
    },
    "pet": {
        "type": "object",
        "required": true,
        "description": "반려동물 정보",
        "properties": "Pet 객체 참조"
    },
    "memorial_room_id": {
        "type": "integer",
        "required": false,
        "description": "추모실 ID"
    },
    "package_id": {
        "type": "integer",
        "required": false,
        "description": "장례 패키지 ID"
    },
    "assigned_staff_id": {
        "type": "integer",
        "required": false,
        "description": "담당 직원 ID"
    },
    "scheduled_at": {
        "type": "datetime",
        "required": false,
        "format": "YYYY-MM-DDThh:mm:ss±hh:mm",
        "description": "예약 일시"
    },
    "is_emergency": {
        "type": "boolean",
        "required": false,
        "default": false,
        "description": "긴급여부"
    },
    "visit_route": {
        "type": "string",
        "required": false,
        "choices": ["internet", "blog", "hospital", "referral"],
        "description": "방문경로"
    },
    "referral_hospital": {
        "type": "string",
        "required": false,
        "max_length": 100,
        "description": "의뢰 병원명"
    },
    "need_death_certificate": {
        "type": "boolean",
        "required": false,
        "default": false,
        "description": "사망확인서 필요여부"
    },
    "custom_requests": {
        "type": "string",
        "required": false,
        "description": "요청사항"
    }
}
```

### 4. Status Change (상태 변경)
```json
{
    "status": {
        "type": "string",
        "required": true,
        "choices": ["pending", "confirmed", "in_progress", "completed", "cancelled"],
        "description": "변경할 상태"
    },
    "notes": {
        "type": "string",
        "required": false,
        "description": "상태 변경 사유"
    }
}
```

### 5. Reschedule (일정 변경)
```json
{
    "scheduled_at": {
        "type": "datetime",
        "required": true,
        "format": "YYYY-MM-DDThh:mm:ss±hh:mm",
        "description": "변경할 예약 일시"
    },
    "memorial_room_id": {
        "type": "integer",
        "required": false,
        "description": "변경할 추모실 ID"
    }
}
```

## API 엔드포인트

### 1. 예약 목록 조회
```
GET /reservations/reservations/

[Query Parameters]
- status (string, optional): 
    - 예약 상태 필터링
    - 값: pending/confirmed/in_progress/completed/cancelled
- is_emergency (boolean, optional):
    - 긴급여부 필터링
    - 값: true/false
- assigned_staff (integer, optional):
    - 담당 직원 ID 필터링
- start_date (string, optional):
    - 시작일
    - 형식: YYYY-MM-DD
- end_date (string, optional):
    - 종료일
    - 형식: YYYY-MM-DD
- search (string, optional):
    - 검색어 (고객명, 반려동물명, 전화번호)
- page (integer, optional):
    - 페이지 번호
    - 기본값: 1
- page_size (integer, optional):
    - 페이지 크기
    - 기본값: 20
    - 최대값: 100
- memorial_room_id (integer, optional):
    - 추모실 ID로 필터링
- timezone (string, optional):
    - 클라이언트 타임존
    - 기본값: Asia/Seoul
    - 예: America/New_York, Europe/London

[Response 200]
{
    "count": 100,
    "next": "http://api/v1/reservations/reservations/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "customer": {
                "id": 1,
                "name": "홍길동",
                "phone": "010-1234-5678",
                "email": "hong@example.com"
            },
            "pet": {
                "id": 1,
                "name": "멍멍이",
                "species": "강아지",
                "breed": "말티즈",
                "age": 12,
                "death_reason_display": "자연사",
                "gender_display": "수컷"
            },
            "memorial_room_id": 1,
            "memorial_room_name": "추모실 1",
            "package_id": 1,
            "package_name": "BASIC예식",
            "package_price": 350000,
            "scheduled_at": "2024-03-16T10:00:00+09:00",
            "status": "pending",
            "status_display": "대기중",
            "is_emergency": false,
            "assigned_staff_id": 1,
            "assigned_staff_name": "김직원",
            "visit_route": "internet",
            "visit_route_display": "인터넷",
            "referral_hospital": "",
            "need_death_certificate": true,
            "created_at": "2024-03-15T14:30:00+09:00"
        }
    ]
}

[Error Responses]
- 400 Bad Request:
    - 잘못된 날짜 형식
    - 잘못된 타임존
- 401 Unauthorized:
    - 인증 토큰 없음 또는 만료
- 403 Forbidden:
    - 접근 권한 없음
```

### 2. 예약 가능 시간 조회
```
GET /reservations/reservations/available-times/

[Query Parameters]
- date (string, required):
    - 조회할 날짜
    - 형식: YYYY-MM-DD
- memorial_room_id (integer, optional):
    - 특정 추모실 ID
    - 미지정시 전체 추모실 조회

[Response 200]
{
    "date": "2024-03-20",
    "memorial_room_id": 1,
    "available_times": [
        {
            "start_time": "09:00:00",
            "end_time": "11:00:00"
        },
        {
            "start_time": "14:00:00",
            "end_time": "16:00:00"
        }
    ]
}

[Error Responses]
- 400 Bad Request:
    - 날짜 미지정
    - 과거 날짜 지정
    - 잘못된 날짜 형식
- 404 Not Found:
    - 존재하지 않는 추모실
```

### 3. 예약 중복 체크
```
POST /reservations/reservations/check-availability/

[Request Body]
{
    "memorial_room_id": 1,      // required, integer
    "scheduled_at": "2024-03-20T14:00:00+09:00",  // required, datetime
    "duration_hours": 2         // optional, integer, default: 2
}

[Response 200]
{
    "is_available": true,
    "conflicting_reservation": null
}

[Response 400 - 중복 예약 존재]
{
    "is_available": false,
    "conflicting_reservation": {
        "id": 123,
        "scheduled_at": "2024-03-20T13:00:00+09:00",
        "duration_hours": 2
    }
}

[Error Responses]
- 400 Bad Request:
    - 필수 파라미터 누락
    - 과거 시간 지정
    - 잘못된 시간 형식
- 404 Not Found:
    - 존재하지 않는 추모실
```

### 4. 일괄 상태 변경
```
POST /reservations/reservations/bulk-status-update/

[Request Body]
{
    "reservation_ids": [1, 2, 3],  // required, array of integers
    "status": "confirmed",         // required, string
    "notes": "일괄 확정 처리"       // optional, string
}

[Response 200]
{
    "success": true,
    "updated_count": 3,
    "failed_updates": []
}

[Response 200 - 부분 실패]
{
    "success": true,
    "updated_count": 1,
    "failed_updates": [
        {
            "id": 2,
            "error": "잘못된 상태 변경입니다."
        },
        {
            "id": 3,
            "error": "예약을 찾을 수 없습니다."
        }
    ]
}

[Error Responses]
- 400 Bad Request:
    - 필수 파라미터 누락
    - 잘못된 상태값
- 401 Unauthorized:
    - 인증 토큰 없음 또는 만료
- 403 Forbidden:
    - 접근 권한 없음
```

## 상태 코드 정의

### 예약 상태 (status)
```
pending: 대기중
confirmed: 확정
in_progress: 진행중
completed: 완료
cancelled: 취소
```

### 방문 경로 (visit_route)
```
internet: 인터넷
blog: 블로그
hospital: 병원
referral: 지인소개
```

### 사망 사유 (death_reason)
```
natural: 자연사
disease: 병사
accident: 사고사
euthanasia: 안락사
other: 기타
```

## 에러 코드 정의

```json
{
    "error_codes": {
        "DUPLICATE_RESERVATION": {
            "code": "E001",
            "message": "해당 시간에 이미 예약이 존재합니다",
            "status": 400
        },
        "INVALID_STATUS_TRANSITION": {
            "code": "E002",
            "message": "현재 상태에서 변경할 수 없는 상태입니다",
            "status": 400
        },
        "ROOM_NOT_AVAILABLE": {
            "code": "E003",
            "message": "해당 추모실은 현재 사용할 수 없습니다",
            "status": 400
        },
        "PAST_DATETIME": {
            "code": "E004",
            "message": "과거 시간으로 예약할 수 없습니다",
            "status": 400
        },
        "INVALID_DATETIME_FORMAT": {
            "code": "E005",
            "message": "잘못된 날짜/시간 형식입니다",
            "status": 400
        },
        "ROOM_NOT_FOUND": {
            "code": "E006",
            "message": "존재하지 않는 추모실입니다",
            "status": 404
        }
    }
}
```

## 시간대 처리

모든 날짜/시간 데이터는 다음 규칙을 따릅니다:

1. 서버 저장: UTC 기준으로 저장
2. API 응답: ISO 8601 형식의 타임스탬프 (기본: KST, +09:00)
3. 클라이언트 요청: 
   - timezone 파라미터로 클라이언트 시간대 지정 가능
   - 지정하지 않을 경우 KST(Asia/Seoul) 기준으로 처리
4. 날짜 범위 검색:
   - start_date, end_date는 클라이언트 시간대 기준으로 처리
   - 예: start_date=2024-03-20, timezone=Asia/Seoul인 경우
     2024-03-20 00:00:00 KST ~ 2024-03-20 23:59:59 KST 범위로 검색