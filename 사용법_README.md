# 🚀 Post Service 사용법

## 📦 받은 파일들
- `post-service-image.tar` - 도커 이미지 파일 (약 48MB)
- `run-post-service.bat` - Windows 실행 스크립트
- `run-post-service.sh` - Linux/Mac 실행 스크립트
- `사용법_README.md` - 이 파일

## 🐳 사전 준비사항

### Windows 사용자
1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드
2. 설치 후 재부팅
3. Docker Desktop 실행

### Linux/Mac 사용자
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io

# macOS
brew install docker
```

## 🚀 간단 실행 방법

### Windows 사용자
1. `run-post-service.bat` 파일을 **더블클릭**
2. 자동으로 모든 과정이 진행됩니다!

### Linux/Mac 사용자
```bash
# 실행 권한 부여
chmod +x run-post-service.sh

# 스크립트 실행
./run-post-service.sh
```

## 🔧 수동 실행 방법

### 1단계: 이미지 로드
```bash
docker load -i post-service-image.tar
```

### 2단계: 컨테이너 실행
```bash
docker run -d --name post-service-app -p 5000:5000 post-service--app:latest
```

### 3단계: 상태 확인
```bash
docker ps
```

## 🌐 웹페이지 접속

서비스가 실행되면 브라우저에서 다음 주소로 접속:

- **메인 페이지**: http://localhost:5000
- **글쓰기**: http://localhost:5000/write
- **게시글 상세**: http://localhost:5000/post
- **API 문서**: http://localhost:5000/api/docs

## 📱 API 테스트

### 헬스체크
```bash
curl http://localhost:5000/health
```

### 카테고리 목록
```bash
curl http://localhost:5000/api/v1/categories
```

### 게시글 목록
```bash
curl http://localhost:5000/api/v1/posts
```

## ⚙️ 서비스 관리

### 서비스 중지
```bash
docker stop post-service-app
```

### 서비스 시작
```bash
docker start post-service-app
```

### 서비스 제거
```bash
docker rm post-service-app
```

### 로그 확인
```bash
docker logs post-service-app
```

## 🎯 주요 기능

- ✅ **카테고리 시스템**: 7개 기본 카테고리 제공
- ✅ **게시글 관리**: CRUD 기능 완비
- ✅ **SQLite 데이터베이스**: 별도 설치 불필요
- ✅ **반응형 웹**: 모바일/데스크톱 지원
- ✅ **API 문서**: Swagger UI 제공

## 🆘 문제 해결

### 포트 5000이 이미 사용 중인 경우
```bash
# 다른 포트로 실행
docker run -d --name post-service-app -p 5001:5000 post-service--app:latest
# http://localhost:5001 로 접속
```

### 도커 권한 문제 (Linux)
```bash
sudo usermod -aG docker $USER
# 재로그인 필요
```

### 이미지 로드 실패
```bash
# 도커 상태 확인
docker info
# 도커 재시작
```

## 📞 지원

문제가 발생하면 다음 정보와 함께 문의해주세요:
- 운영체제 버전
- 도커 버전 (`docker --version`)
- 오류 메시지
- 실행한 명령어

---

**🎉 이제 Post Service를 즐겨보세요!**
