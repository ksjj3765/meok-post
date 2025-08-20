# Post Service API

MSA 아키텍처에서 게시글 관리만을 담당하는 독립적인 서비스입니다.

## 🚀 주요 기능

- **게시글 관리**: CRUD 작업, 검색, 필터링, 페이지네이션
- **태그 시스템**: 게시글 태그 관리
- **미디어 관리**: 이미지 업로드/삭제 (로컬/S3)
- **반응 시스템**: 좋아요/싫어요 기능
- **MSA 연동**: User 서비스, Notification 서비스와의 통신
- **이벤트 발행**: Outbox 패턴을 통한 이벤트 스트림

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │    │  Post Service   │    │   Database      │
│                 │◄──►│                 │◄──►│   (MySQL)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Outbox        │
                       │   Events        │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   CDC/DMS       │
                       │   (Event Stream)│
                       └─────────────────┘
```

## 🛠️ 기술 스택

- **Backend**: Flask 3.1.1
- **Database**: MySQL + SQLAlchemy
- **API Documentation**: Swagger/OpenAPI
- **Testing**: pytest
- **Code Quality**: flake8, black, isort

## 📦 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
export DATABASE_URL="mysql+pymysql://username:password@localhost:3307/postdb?charset=utf8mb4"
export SECRET_KEY="your-secret-key"
export USER_SERVICE_URL="http://localhost:8081"
export NOTIFICATION_SERVICE_URL="http://localhost:8082"
export ENVIRONMENT="development"
```

### 3. 데이터베이스 설정

```bash
# MySQL 데이터베이스 생성
mysql -u root -p
CREATE DATABASE postdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 데이터베이스 마이그레이션
flask db init
flask db migrate
flask db upgrade
```

### 4. 서버 실행

```bash
python app.py
```

서버가 `http://localhost:5000`에서 실행됩니다.

## 📚 API 문서

### Swagger UI

API 문서는 `/api/docs`에서 확인할 수 있습니다.

### 주요 엔드포인트

#### 게시글 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/posts` | 게시글 목록 조회 |
| POST | `/api/v1/posts` | 게시글 생성 |
| GET | `/api/v1/posts/{id}` | 게시글 상세 조회 |
| PUT | `/api/v1/posts/{id}` | 게시글 전체 수정 |
| PATCH | `/api/v1/posts/{id}` | 게시글 부분 수정 |
| DELETE | `/api/v1/posts/{id}` | 게시글 삭제 |

#### 태그 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tags` | 태그 목록 조회 |
| POST | `/api/v1/tags` | 태그 생성 |

#### 미디어 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/posts/{id}/images` | 게시글 이미지 목록 |
| POST | `/api/v1/posts/{id}/images` | 이미지 업로드 |
| DELETE | `/api/v1/posts/{id}/images/{media_id}` | 이미지 삭제 |

#### 반응 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/posts/{id}/reaction` | 게시글 반응 (좋아요/싫어요) |

### API 응답 형식

모든 API는 표준화된 응답 형식을 사용합니다:

```json
{
  "success": true,
  "message": "작업이 성공적으로 완료되었습니다",
  "data": {
    // 실제 데이터
  },
  "meta": {
    // 페이지네이션 정보 (해당하는 경우)
  }
}
```

에러 응답:

```json
{
  "success": false,
  "message": "에러 메시지",
  "error": {
    "code": 400,
    "details": "상세 에러 정보"
  }
}
```

## 🧪 테스트

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=post

# 특정 테스트 파일 실행
pytest tests/test_api.py
```

### 테스트 환경

- SQLite 인메모리 데이터베이스 사용
- 각 테스트마다 독립적인 데이터베이스 컨텍스트
- Fixture를 통한 테스트 데이터 관리

## 🔧 개발 도구

### 코드 포맷팅

```bash
# Black으로 코드 포맷팅
black post/ tests/

# isort로 import 정렬
isort post/ tests/
```

### 코드 품질 검사

```bash
# flake8으로 코드 품질 검사
flake8 post/ tests/

# 타입 힌트 검사 (mypy 설치 시)
mypy post/
```

## 📁 프로젝트 구조

```
post-service/
├── app.py                 # 메인 애플리케이션
├── config.py             # 설정 파일
├── requirements.txt      # Python 의존성
├── post/                # Post 서비스 모듈
│   ├── __init__.py
│   ├── models.py        # 데이터베이스 모델
│   ├── routes.py        # API 라우트
│   ├── services.py      # 비즈니스 로직
│   ├── validators.py    # 데이터 검증
│   └── schemas.py       # API 스키마
├── static/              # 정적 파일
│   └── swagger.json     # Swagger 문서
├── tests/               # 테스트 코드
│   ├── __init__.py
│   └── test_api.py      # API 테스트
├── uploads/             # 업로드된 파일 (개발 환경)
└── README.md            # 프로젝트 문서
```

## 🔒 보안

- 입력 데이터 검증 및 sanitization
- SQL 인젝션 방지 (SQLAlchemy ORM 사용)
- 파일 업로드 보안 (확장자, 크기 제한)
- 환경 변수를 통한 민감 정보 관리

## 🚀 배포

### Docker 사용

```bash
# Docker 이미지 빌드
docker build -t post-service .

# Docker 컨테이너 실행
docker run -p 5000:5000 post-service
```

### Docker Compose 사용

```bash
# 전체 서비스 실행
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

## 🤝 기여

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

---

**Post Service API** - MSA 환경에서 게시글 관리를 위한 강력하고 확장 가능한 서비스


