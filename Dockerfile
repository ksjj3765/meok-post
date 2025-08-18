# Post Service Docker Image
# MSA 환경에서 Post 서비스를 컨테이너화하기 위한 이미지

FROM python:3.9-slim

LABEL maintainer="Post Service Team"
LABEL description="Post Service for MSA Architecture"
LABEL version="1.0.0"

WORKDIR /app

# MySQL 클라이언트 라이브러리 설치 (데이터베이스 연결용)
RUN apt-get update && apt-get install -y \
    gcc \
    libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 업로드 폴더 생성 (이미지 저장용)
RUN mkdir -p uploads && chmod 755 uploads

EXPOSE 5000

# 환경 변수 설정
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Gunicorn으로 프로덕션 서버 실행 (Flask 개발 서버 대신)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "app:app"]


