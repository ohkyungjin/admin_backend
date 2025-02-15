# 대시보드 API 명세서

## Base URL
```
http://localhost:8000/api/v1
```

## 공통 헤더
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

## 공통 쿼리 파라미터
```
date: YYYY-MM-DD (조회할 날짜, 기본값: 오늘)
```

## 응답 데이터 포맷

### 1. ReservationStats (예약 통계)
```json
{
    "today_total": {
        "type": "integer",
        "description": "오늘 총 예약 수"
    },
    "today_completed": {
        "type": "integer",
        "description": "오늘 완료된 예약 수"
    },
    "today_pending": {
        "type": "integer",
        "description": "오늘 대기 중인 예약 수"
    },
    "today_confirmed": {
        "type": "integer",
        "description": "오늘 확정된 예약 수"
    },
    "today_in_progress": {
        "type": "integer",
        "description": "오늘 진행 중인 예약 수"
    },
    "today_cancelled": {
        "type": "integer",
        "description": "오늘 취소된 예약 수"
    },
    "emergency_count": {
        "type": "integer",
        "description": "오늘의 긴급 예약 수"
    },
    "weekly_stats": {
        "type": "object",
        "description": "최근 7일간 일별 예약 통계",
        "properties": {
            "YYYY-MM-DD": {
                "type": "integer",
                "description": "해당 일자의 예약 수"
            }
        }
    },
    "monthly_stats": {
        "type": "object",
        "description": "이번 달 일별 예약 통계",
        "properties": {
            "YYYY-MM-DD": {
                "type": "integer",
                "description": "해당 일자의 예약 수"
            }
        }
    }
}
```

### 2. MemorialRoomStatus (추모실 현황)
```json
{
    "room_id": {
        "type": "integer",
        "description": "추모실 ID"
    },
    "room_name": {
        "type": "string",
        "description": "추모실 이름"
    },
    "current_status": {
        "type": "string",
        "enum": ["available", "in_use", "reserved"],
        "description": "현재 상태 (사용가능/사용중/예약중)"
    },
    "next_reservation": {
        "type": "object",
        "description": "다음 예약 정보",
        "nullable": true,
        "properties": {
            "id": "integer",
            "customer": {
                "id": "integer",
                "name": "string",
                "phone": "string",
                "email": "string",
                "address": "string"
            },
            "pet": {
                "id": "integer",
                "name": "string",
                "species": "string",
                "breed": "string"
            },
            "scheduled_at": "datetime",
            "status": "string",
            "is_emergency": "boolean"
        }
    },
    "today_reservation_count": {
        "type": "integer",
        "description": "오늘 예약 건수"
    }
}
```

### 3. StaffWorkload (직원 배정 현황)
```json
{
    "staff_id": {
        "type": "integer",
        "description": "직원 ID"
    },
    "staff_name": {
        "type": "string",
        "description": "직원 이름"
    },
    "assigned_count": {
        "type": "integer",
        "description": "배정된 예약 수"
    },
    "today_assignments": {
        "type": "array",
        "description": "오늘의 배정 목록",
        "items": {
            "id": "integer",
            "scheduled_at": "datetime",
            "status": "string",
            "customer": {
                "name": "string",
                "phone": "string"
            },
            "pet": {
                "name": "string",
                "species": "string"
            }
        }
    }
}
```

## API 엔드포인트

### 1. 대시보드 전체 데이터 조회
```
GET /dashboard/

Query Parameters:
- date: YYYY-MM-DD (선택, 기본값: 오늘)

Response 200:
{
    "reservation_stats": {...},
    "memorial_room_status": [...],
    "recent_reservations": [...],
    "staff_workload": [...]
}
```

### 2. 예약 통계 데이터 조회
```
GET /dashboard/reservation_stats/

Query Parameters:
- date: YYYY-MM-DD (선택, 기본값: 오늘)

Response 200:
{
    "today_total": 15,
    "today_completed": 5,
    "today_pending": 4,
    "today_confirmed": 4,
    "today_in_progress": 2,
    "today_cancelled": 0,
    "emergency_count": 2,
    "weekly_stats": {...},
    "monthly_stats": {...}
}
```

### 3. 추모실 현황 데이터 조회
```
GET /dashboard/memorial_room_status/

Query Parameters:
- date: YYYY-MM-DD (선택, 기본값: 오늘)

Response 200:
[
    {
        "room_id": 1,
        "room_name": "추모실 1",
        "current_status": "in_use",
        "next_reservation": {...},
        "today_reservation_count": 3
    }
]
```

### 4. 직원 배정 현황 데이터 조회
```
GET /dashboard/staff_workload/

Query Parameters:
- date: YYYY-MM-DD (선택, 기본값: 오늘)

Response 200:
[
    {
        "staff_id": 1,
        "staff_name": "홍길동",
        "assigned_count": 3,
        "today_assignments": [...]
    }
]
```

## 상태 코드 정의

### 추모실 상태 (current_status)
```
available: 사용가능
in_use: 사용중
reserved: 예약중
```

### 예약 상태 (status)
```
pending: 대기중
confirmed: 확정
in_progress: 진행중
completed: 완료
cancelled: 취소
```

## 에러 응답

```json
{
    "error": {
        "code": "string",
        "message": "string"
    }
}
```

### 에러 코드
```
401 Unauthorized: 인증되지 않은 요청
403 Forbidden: 권한 없음
404 Not Found: 리소스를 찾을 수 없음
500 Internal Server Error: 서버 내부 오류
```

## 자동 업데이트
- 10분마다 예약 상태와 추모실 상태가 자동으로 업데이트됩니다.
- 예약 시간이 되면 자동으로 '진행중' 상태로 변경됩니다.
- 예약 시작 2시간 후 자동으로 '완료' 상태로 변경됩니다.
- 모든 상태 변경은 이력이 기록됩니다. 