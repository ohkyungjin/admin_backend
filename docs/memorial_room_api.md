# 추모실 API 명세서

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

### 1. MemorialRoom (추모실 정보)
```json
{
    "name": {
        "type": "string",
        "required": true,
        "max_length": 100,
        "description": "추모실 이름"
    },
    "capacity": {
        "type": "integer",
        "required": false,
        "default": 10,
        "description": "수용 인원"
    },
    "description": {
        "type": "string",
        "required": false,
        "description": "설명"
    },
    "is_active": {
        "type": "boolean",
        "required": false,
        "default": true,
        "description": "활성화 여부"
    },
    "operating_hours": {
        "type": "object",
        "required": true,
        "description": "운영 시간",
        "properties": {
            "start_time": {
                "type": "string",
                "format": "HH:MM",
                "description": "운영 시작 시간"
            },
            "end_time": {
                "type": "string",
                "format": "HH:MM",
                "description": "운영 종료 시간"
            }
        }
    },
    "current_status": {
        "type": "string",
        "required": false,
        "choices": ["available", "in_use", "reserved"],
        "default": "available",
        "description": "현재 상태"
    }
}
```

## API 엔드포인트

### 1. 추모실 목록 조회
```
GET /memorial-rooms/rooms/

[Query Parameters]
- is_active (boolean, optional):
    - 활성화 여부로 필터링
    - 값: true/false
- current_status (string, optional):
    - 현재 상태로 필터링
    - 값: available/in_use/reserved

[Response 200]
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "추모실 1",
            "capacity": 10,
            "description": "1층 위치",
            "is_active": true,
            "current_status": "available",
            "created_at": "2024-03-15T14:30:00+09:00",
            "updated_at": "2024-03-15T14:30:00+09:00"
        }
    ]
}
```

### 2. 추모실 상세 조회
```
GET /memorial-rooms/rooms/{id}/

[Response 200]
{
    "id": 1,
    "name": "추모실 1",
    "capacity": 10,
    "description": "1층 위치",
    "is_active": true,
    "current_status": "available",
    "created_at": "2024-03-15T14:30:00+09:00",
    "updated_at": "2024-03-15T14:30:00+09:00"
}
```

### 3. 추모실 생성
```
POST /memorial-rooms/rooms/

[Request Body]
{
    "name": "추모실 1",
    "capacity": 10,
    "description": "1층 위치",
    "is_active": true,
    "operating_hours": {
        "start_time": "09:00",
        "end_time": "18:00"
    }
}

[Response 201]
{
    "id": 1,
    "name": "추모실 1",
    "capacity": 10,
    "description": "1층 위치",
    "is_active": true,
    "operating_hours": {
        "start_time": "09:00",
        "end_time": "18:00"
    },
    "current_status": "available",
    "created_at": "2024-03-15T14:30:00+09:00",
    "updated_at": "2024-03-15T14:30:00+09:00"
}
```

### 4. 추모실 수정
```
PUT /memorial-rooms/rooms/{id}/

[Request Body]
{
    "name": "추모실 1",
    "capacity": 15,
    "description": "1층 위치 (리모델링)",
    "is_active": true,
    "operating_hours": {
        "start_time": "09:00",
        "end_time": "18:00"
    }
}

[Response 200]
{
    "id": 1,
    "name": "추모실 1",
    "capacity": 15,
    "description": "1층 위치 (리모델링)",
    "is_active": true,
    "operating_hours": {
        "start_time": "09:00",
        "end_time": "18:00"
    },
    "current_status": "available",
    "created_at": "2024-03-15T14:30:00+09:00",
    "updated_at": "2024-03-15T14:35:00+09:00"
}
```

### 5. 추모실 삭제
```
DELETE /memorial-rooms/rooms/{id}/

[Response 204]
No Content
```

### 6. 추모실 상태 변경
```
POST /memorial-rooms/rooms/{id}/change-status/

[Request Body]
{
    "current_status": "in_use"
}

[Response 200]
{
    "id": 1,
    "name": "추모실 1",
    "current_status": "in_use",
    "updated_at": "2024-03-15T14:35:00+09:00"
}
```

## 상태 코드 정의

### 추모실 상태 (current_status)
```
available: 사용가능
in_use: 사용중
reserved: 예약중
```

## 에러 코드 정의

```json
{
    "error_codes": {
        "ROOM_NOT_FOUND": {
            "code": "M001",
            "message": "존재하지 않는 추모실입니다",
            "status": 404
        },
        "DUPLICATE_ROOM_NAME": {
            "code": "M002",
            "message": "이미 존재하는 추모실 이름입니다",
            "status": 400
        },
        "INVALID_STATUS": {
            "code": "M003",
            "message": "올바르지 않은 상태값입니다",
            "status": 400
        },
        "ROOM_IN_USE": {
            "code": "M004",
            "message": "사용중인 추모실은 삭제할 수 없습니다",
            "status": 400
        }
    }
}
```

## 자동 상태 변경

1. 예약 시간이 되면 자동으로 'in_use' 상태로 변경됩니다.
2. 예약 완료 후 자동으로 'available' 상태로 변경됩니다.
3. 새로운 예약이 생성되면 'reserved' 상태로 변경됩니다. 