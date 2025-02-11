# 배포 가이드

## 1. 시스템 요구사항

### 1.1 하드웨어 요구사항
- CPU: 2코어 이상
- RAM: 4GB 이상
- 디스크: 20GB 이상

### 1.2 소프트웨어 요구사항
- Ubuntu 20.04 LTS 이상
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Nginx 1.18+
- Gunicorn 20+

## 2. 설치 절차

### 2.1 시스템 패키지 설치
```bash
# 시스템 업데이트
sudo apt update
sudo apt upgrade -y

# 필요한 패키지 설치
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx redis-server
```

### 2.2 PostgreSQL 설정
```bash
# PostgreSQL 사용자 생성
sudo -u postgres createuser --interactive

# 데이터베이스 생성
sudo -u postgres createdb cielopet_db
```

### 2.3 프로젝트 설정
```bash
# 프로젝트 디렉토리 생성
mkdir /var/www/cielopet
cd /var/www/cielopet

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 수정
```

### 2.4 Gunicorn 설정
```bash
# Gunicorn 설정 파일 생성
sudo nano /etc/systemd/system/gunicorn.service

[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/cielopet
ExecStart=/var/www/cielopet/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/var/www/cielopet/cielopet.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 2.5 Nginx 설정
```bash
# Nginx 설정 파일 생성
sudo nano /etc/nginx/sites-available/cielopet

server {
    listen 80;
    server_name your_domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/cielopet;
    }

    location /media/ {
        root /var/www/cielopet;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/cielopet/cielopet.sock;
    }
}

# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/cielopet /etc/nginx/sites-enabled
```

### 2.6 SSL 설정 (Let's Encrypt)
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d your_domain.com
```

## 3. 배포 절차

### 3.1 코드 배포
```bash
# 소스 코드 업데이트
git pull origin main

# 의존성 업데이트
pip install -r requirements.txt

# 정적 파일 수집
python manage.py collectstatic

# 데이터베이스 마이그레이션
python manage.py migrate
```

### 3.2 서비스 재시작
```bash
# Gunicorn 재시작
sudo systemctl restart gunicorn

# Nginx 재시작
sudo systemctl restart nginx
```

## 4. 모니터링 설정

### 4.1 Sentry 설정
```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

### 4.2 Prometheus & Grafana 설정
```bash
# Prometheus 설치
sudo apt-get install -y prometheus

# Grafana 설치
sudo apt-get install -y grafana
```

## 5. 백업 설정

### 5.1 데이터베이스 백업
```bash
# 백업 스크립트 생성
#!/bin/bash
BACKUP_DIR="/var/backups/cielopet"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump cielopet_db > $BACKUP_DIR/backup_$DATE.sql
```

### 5.2 미디어 파일 백업
```bash
# 미디어 파일 백업
rsync -av /var/www/cielopet/media/ /var/backups/cielopet/media/
```

## 6. 문제 해결

### 6.1 로그 확인
```bash
# Nginx 에러 로그
sudo tail -f /var/log/nginx/error.log

# Gunicorn 로그
sudo journalctl -u gunicorn
```

### 6.2 일반적인 문제 해결
- 502 Bad Gateway: Gunicorn 프로세스 확인
- 500 Internal Server Error: Django 에러 로그 확인
- 정적 파일 404: collectstatic 실행 여부 확인

## 7. 성능 최적화

### 7.1 캐시 설정
```python
# Redis 캐시 설정
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 7.2 데이터베이스 최적화
```bash
# PostgreSQL 설정 최적화
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 768MB
work_mem = 4MB
maintenance_work_mem = 64MB
``` 