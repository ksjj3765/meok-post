# 🚀 커뮤니티 포스트 서비스

Flask 기반의 현대적인 커뮤니티 게시판 서비스입니다. 이미지 업로드, 좋아요/싫어요, 태그 관리 등 풍부한 기능을 제공합니다.

## ✨ 주요 기능

- 📝 **게시글 관리**: CRUD, 공개 설정, 상태 관리
- 🖼️ **이미지 업로드**: 다중 이미지, 드래그 앤 드롭
- 👍 **리액션 시스템**: 좋아요/싫어요 기능
- 🏷️ **태그 시스템**: 태그 생성 및 관리
- 🔍 **검색 기능**: FULLTEXT 검색 지원
- 📱 **반응형 UI**: Bootstrap 5 기반 모던 디자인
- 🗄️ **MSA 구조**: userdb와 postdb 분리

## 🛠️ 기술 스택

### Backend
- **Flask 3.1.1** - 웹 프레임워크
- **Flask-SQLAlchemy 3.1.1** - ORM
- **Flask-Migrate 4.1.0** - 데이터베이스 마이그레이션
- **PyMySQL 1.1.1** - MySQL 드라이버
- **Pillow** - 이미지 처리

### Frontend
- **HTML5 + CSS3** - 마크업 및 스타일링
- **Vanilla JavaScript** - 순수 자바스크립트
- **Bootstrap 5** - UI 프레임워크
- **Font Awesome 6** - 아이콘

### Database
- **MySQL 8.0+** - 메인 데이터베이스
- **MSA 구조** - userdb, postdb 분리

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/post-service.git
cd post-service
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 설정
```bash
# .env 파일 생성
cp .env.example .env

# 환경 변수 설정
export DATABASE_URL="mysql+pymysql://username:password@localhost:3306/postdb"
export SECRET_KEY="your-secret-key"
```

### 5. 데이터베이스 설정
```bash
# MySQL에서 데이터베이스 생성
CREATE DATABASE postdb CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE DATABASE userdb CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

# 마이그레이션 실행
flask db upgrade
```

### 6. 애플리케이션 실행
```bash
python app.py
```

브라우저에서 `http://127.0.0.1:5000`으로 접속하세요!

## 📁 프로젝트 구조

```
post-service/
├── app.py                 # Flask 애플리케이션 진입점
├── config.py              # 설정 파일
├── requirements.txt       # Python 의존성
├── .env.example          # 환경 변수 예시
├── .gitignore            # Git 무시 파일
├── README.md             # 프로젝트 문서
├── post/                 # 포스트 모듈
│   ├── __init__.py
│   ├── models.py         # 데이터베이스 모델
│   └── routes.py         # API 엔드포인트
├── static/               # 정적 파일
│   ├── style.css         # 커스텀 스타일
│   └── script.js         # 프론트엔드 로직
├── templates/            # HTML 템플릿
│   └── index.html        # 메인 페이지
├── uploads/              # 이미지 업로드 폴더
└── migrations/           # 데이터베이스 마이그레이션
```

## 🔧 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DATABASE_URL` | 데이터베이스 연결 문자열 | `mysql+pymysql://root:1234@localhost:3307/postdb` |
| `SECRET_KEY` | Flask 시크릿 키 | `dev-secret-key` |
| `AWS_ACCESS_KEY_ID` | AWS S3 액세스 키 | - |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 시크릿 키 | - |
| `S3_BUCKET_NAME` | S3 버킷 이름 | `post-service-images` |

## 📚 API 문서

### 게시글 API
- `GET /posts` - 게시글 목록 조회
- `POST /posts` - 게시글 생성
- `GET /posts/{id}` - 게시글 상세 조회
- `PUT /posts/{id}` - 게시글 전체 수정
- `PATCH /posts/{id}` - 게시글 부분 수정
- `DELETE /posts/{id}` - 게시글 삭제 (소프트 삭제)

### 이미지 API
- `POST /posts/{id}/images` - 이미지 업로드
- `GET /posts/{id}/images` - 이미지 목록 조회
- `DELETE /posts/{id}/images/{image_id}` - 이미지 삭제

### 리액션 API
- `POST /posts/{id}/reaction` - 좋아요/싫어요

### 태그 API
- `GET /tags` - 태그 목록 조회
- `POST /tags` - 태그 생성

## 🚀 배포

### AWS 배포 (권장)
1. **RDS**: MySQL 데이터베이스
2. **S3**: 이미지 저장소
3. **EC2/ECS**: 애플리케이션 서버
4. **CloudFront**: CDN

### Docker 배포
```bash
# Docker 이미지 빌드
docker build -t post-service .

# 컨테이너 실행
docker run -p 5000:5000 post-service
```

## 🧪 테스트

```bash
# API 테스트
python test_api.py

# 이미지 업로드 테스트
python test_image_upload.py
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 [Issues](https://github.com/yourusername/post-service/issues)를 통해 연락해주세요.

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요!


