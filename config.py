"""
Post Service Configuration
MSA 환경에서 Post 서비스의 설정을 관리합니다.
"""

import os

class Config:
    # 보안 키 (운영 환경에서는 반드시 환경 변수로 설정)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 데이터베이스 연결 (개발: localhost:3307, 운영: RDS 엔드포인트)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:1234@localhost:3307/postdb?charset=utf8mb4'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MSA 서비스 URL (User, Notification 서비스 연동용)
    USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://localhost:8081')
    NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://localhost:8082')
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    
    # 데이터베이스 연결 풀 설정 (성능 최적화)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

